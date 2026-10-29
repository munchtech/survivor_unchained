using System;
using System.Collections.Generic;
using System.Numerics;

namespace SurvivorUnchained.Play;

/// <summary>
/// A garment's hanging chains (a cape's columns, a capelet's hem bones) as particles on rigid links, simulated in world
/// units: each chain's root rides its body bone (pinned), every other particle swings under gravity and is pulled toward
/// where its link would lie riding the body rigidly (its bind drape: a spring of angular frequency Stiff, stiffer at the
/// root than the tip), its motion relative to the body damped (Drag) with a little air drag (Air), its links kept their
/// length, and each link kept off the body's capsules (thighs, calves, pelvis, spine) and above the ground. A link never
/// comes closer to a capsule than it was at the bind or than the two radii touching, whichever is less (SetRest), so the
/// bind drape is always a valid state. Reset puts the chains at the rigid targets and settles them there (SettleSeconds
/// under the pose as it is), so the first frame of a shot after a cut shows a hang at rest, never a swing.
/// Engine-free (System.Numerics); View/PieceSprings runs it, the tests hold it.
/// </summary>
public sealed class ClothChains
{
    /// <summary>Stiff: angular frequency (1/s) of the pull toward the rigid drape, at a chain's root link and at its tip;
    /// Bend: of the pull keeping each link's bend on the link above as at the bind (the cloth swings as a whole, not a whip);
    /// Drag: damping (1/s) of the motion relative to the body, plus 2 Zeta times the particle's own spring frequency (its
    /// springs damped near critically: a stiff root link does not ring); Air: of the motion in the world; Gravity: m/s/s, world.</summary>
    public readonly record struct Tuning(float StiffRoot = 9f, float StiffTip = 1.5f, float Bend = 7f, float Drag = 4f, float Zeta = 0.9f, float Air = 0.3f,
        float Gravity = 9.8f, int Substeps = 4, int Iterations = 3, float SettleSeconds = 1.5f, float MaxSpeed = 14f)
    {
        /// <summary>The heavy soaked wool (new Tuning() is all zeros: a record struct's parameterless constructor).</summary>
        public static readonly Tuning Wool = new(StiffRoot: 9f);
    }

    public readonly record struct Capsule(Vector3 A, Vector3 B, float R);

    readonly int[] parent;
    readonly float[] radius, stiff;
    readonly Vector3[] x, xp, tPrev, tSub, tSubPrev, vel;
    Capsule[] colPrev = Array.Empty<Capsule>();
    float[,] limit = new float[0, 0];
    bool started;
    public Tuning Tune;

    /// <summary>Particles in order (a parent before its children); parent[i] &lt; 0 for a pinned chain root; radius[i]
    /// the link ending at i (world); stiffness[i] (1/s) overrides the root-to-tip ramp where &gt; 0.</summary>
    public ClothChains(int[] parent, float[] radius, Tuning tune, float[]? stiffness = null)
    {
        int n = parent.Length;
        for (int i = 0; i < n; i++)
            if (parent[i] >= i) throw new ArgumentException($"particle {i}: its parent {parent[i]} must come before it");
        this.parent = parent;
        this.radius = radius;
        Tune = tune;
        x = new Vector3[n]; xp = new Vector3[n]; tPrev = new Vector3[n]; tSub = new Vector3[n]; tSubPrev = new Vector3[n]; vel = new Vector3[n];
        // (each particle's depth down its chain, and its chain's longest depth: the stiffness ramp)
        var depth = new int[n];
        var rootOf = new int[n];
        for (int i = 0; i < n; i++) { depth[i] = parent[i] < 0 ? 0 : depth[parent[i]] + 1; rootOf[i] = parent[i] < 0 ? i : rootOf[parent[i]]; }
        var deepest = new Dictionary<int, int>();
        for (int i = 0; i < n; i++) deepest[rootOf[i]] = Math.Max(deepest.TryGetValue(rootOf[i], out var d) ? d : 0, depth[i]);
        stiff = new float[n];
        for (int i = 0; i < n; i++)
        {
            float u = deepest[rootOf[i]] <= 1 ? 0 : (depth[i] - 1) / (float)(deepest[rootOf[i]] - 1);
            stiff[i] = stiffness != null && stiffness[i] > 0 ? stiffness[i] : tune.StiffRoot + (tune.StiffTip - tune.StiffRoot) * Math.Clamp(u, 0, 1);
        }
    }

    public int Count => x.Length;
    public IReadOnlyList<Vector3> Positions => x;
    public int Parent(int i) => parent[i];
    public float Stiffness(int i) => stiff[i];

    /// <summary>The bind: each link's closest approach to each capsule there caps how close it may come (see the summary).</summary>
    public void SetRest(Vector3[] t, Capsule[] cols)
    {
        limit = new float[x.Length, cols.Length];
        for (int i = 0; i < x.Length; i++)
            for (int c = 0; c < cols.Length; c++)
            {
                if (parent[i] < 0) { limit[i, c] = 0; continue; }
                var (_, _, d) = Closest(t[parent[i]], t[i], cols[c].A, cols[c].B);
                limit[i, c] = Math.Max(0, Math.Min(radius[i] + cols[c].R, d));
            }
    }

    /// <summary>The chains at the rigid targets, settled there under the pose as it is (no motion carried in).</summary>
    public void Reset(Vector3[] t, Capsule[] cols, float? ground, Vector3 down)
    {
        if (limit.GetLength(1) != cols.Length) SetRest(t, cols);
        Array.Copy(t, x, x.Length); Array.Copy(t, xp, x.Length); Array.Copy(t, tPrev, x.Length);
        int steps = (int)MathF.Ceiling(Tune.SettleSeconds * 60);
        for (int k = 0; k < steps; k++) Sub(1f / 60, t, t, cols, ground, down);
        Array.Copy(x, xp, x.Length);
        colPrev = (Capsule[])cols.Clone();
        started = true;
    }

    /// <summary>One frame: the targets and capsules eased from last frame's to these over the substeps.</summary>
    public void Step(float dt, Vector3[] t, Capsule[] cols, float? ground, Vector3 down)
    {
        if (!started || colPrev.Length != cols.Length) { Reset(t, cols, ground, down); return; }
        int n = Math.Max(1, Tune.Substeps);
        float h = dt / n;
        var cs = new Capsule[cols.Length];
        Array.Copy(tPrev, tSub, x.Length);
        for (int s = 1; s <= n; s++)
        {
            float a = s / (float)n;
            Array.Copy(tSub, tSubPrev, x.Length);
            for (int i = 0; i < x.Length; i++) tSub[i] = Vector3.Lerp(tPrev[i], t[i], a);
            for (int c = 0; c < cols.Length; c++)
                cs[c] = new Capsule(Vector3.Lerp(colPrev[c].A, cols[c].A, a), Vector3.Lerp(colPrev[c].B, cols[c].B, a), cols[c].R);
            Sub(h, tSubPrev, tSub, cs, ground, down);
        }
        Array.Copy(t, tPrev, x.Length);
        colPrev = (Capsule[])cols.Clone();
    }

    void Sub(float h, Vector3[] t0, Vector3[] t, Capsule[] cols, float? ground, Vector3 down)
    {
        float air = MathF.Exp(-Tune.Air * h), vmax = Tune.MaxSpeed * h;
        var g = down * Tune.Gravity * h * h;
        for (int i = 0; i < x.Length; i++) vel[i] = parent[i] < 0 ? t[i] - t0[i] : x[i] - xp[i];
        for (int i = 0; i < x.Length; i++)
        {
            if (parent[i] < 0) { xp[i] = x[i]; x[i] = t[i]; continue; }
            int p = parent[i];
            bool bends = parent[p] >= 0;
            // (damped toward the body's own motion there (its shape spring's share), and toward its parent's (its bend's))
            var vt = t[i] - t0[i];
            var v = vt + (vel[i] - vt) * MathF.Exp(-(Tune.Drag + 2 * Tune.Zeta * stiff[i]) * h);
            if (bends) v = vel[p] + (v - vel[p]) * MathF.Exp(-2 * Tune.Zeta * Tune.Bend * h);
            v *= air;
            if (v.Length() > vmax) v *= vmax / v.Length();
            var rest = t[i] - t[p];
            var spring = (t[i] - x[i]) * (stiff[i] * stiff[i] * h * h);
            if (bends)
            {
                var bent = x[p] + Vector3.Transform(rest, FromTo(t[p] - t[parent[p]], x[p] - x[parent[p]]));
                spring += (bent - x[i]) * (Tune.Bend * Tune.Bend * h * h);
            }
            xp[i] = x[i];
            x[i] += v + g + spring;
        }
        for (int it = 0; it < Math.Max(1, Tune.Iterations); it++)
        {
            for (int i = 0; i < x.Length; i++)
            {
                if (parent[i] < 0) continue;
                int p = parent[i];
                float len = (t[i] - t[p]).Length();
                var d = x[i] - x[p];
                float dl = d.Length();
                x[i] = dl > 1e-6f ? x[p] + d * (len / dl) : x[p] + (t[i] - t[p]);
            }
            Collide(cols, ground);
        }
    }

    void Collide(Capsule[] cols, float? ground)
    {
        for (int i = 0; i < x.Length; i++)
        {
            if (parent[i] < 0) continue;
            int p = parent[i];
            bool pinned = parent[p] < 0;
            for (int c = 0; c < cols.Length; c++)
            {
                float lim = limit[i, c];
                if (lim <= 0) continue;
                var (s, q, d) = Closest(x[p], x[i], cols[c].A, cols[c].B);
                if (d >= lim) continue;
                var r = PointOnSegment(cols[c].A, cols[c].B, q);
                var nrm = q - r;
                float nl = nrm.Length();
                if (nl < 1e-6f) { nrm = Vector3.Normalize(Vector3.Cross(cols[c].B - cols[c].A, Vector3.UnitX)); if (float.IsNaN(nrm.X)) nrm = Vector3.UnitZ; }
                else nrm /= nl;
                float push = lim - d;
                // (the push shared between the link's ends by where it touches; a pinned end does not move)
                if (pinned) x[i] += nrm * push * Math.Min(1f / Math.Max(s, 1e-3f), 3f);
                else { float w = s * s + (1 - s) * (1 - s); x[i] += nrm * push * (s / w); x[p] += nrm * push * ((1 - s) / w); }
            }
            if (ground is float gy && x[i].Y < gy + radius[i]) x[i].Y = gy + radius[i];
        }
    }

    /// <summary>The deepest any link's centre line goes inside each capsule's body (its radius, not the contact
    /// distance), world units (0: clear).</summary>
    public float[] Penetration(Capsule[] cols)
    {
        var o = new float[cols.Length];
        for (int i = 0; i < x.Length; i++)
        {
            if (parent[i] < 0) continue;
            for (int c = 0; c < cols.Length; c++)
            {
                var (_, _, d) = Closest(x[parent[i]], x[i], cols[c].A, cols[c].B);
                o[c] = Math.Max(o[c], cols[c].R - d);
            }
        }
        return o;
    }

    /// <summary>The closest points of segments PQ and AB: the parameter on PQ, the point on PQ, the distance.</summary>
    public static (float S, Vector3 Q, float D) Closest(Vector3 p, Vector3 q, Vector3 a, Vector3 b)
    {
        var d1 = q - p; var d2 = b - a; var r = p - a;
        float aa = Vector3.Dot(d1, d1), e = Vector3.Dot(d2, d2), f = Vector3.Dot(d2, r);
        float s, t;
        if (aa <= 1e-12f && e <= 1e-12f) { s = t = 0; }
        else if (aa <= 1e-12f) { s = 0; t = Math.Clamp(f / e, 0, 1); }
        else
        {
            float c = Vector3.Dot(d1, r);
            if (e <= 1e-12f) { t = 0; s = Math.Clamp(-c / aa, 0, 1); }
            else
            {
                float bb = Vector3.Dot(d1, d2), den = aa * e - bb * bb;
                s = den > 1e-12f ? Math.Clamp((bb * f - c * e) / den, 0, 1) : 0;
                t = (bb * s + f) / e;
                if (t < 0) { t = 0; s = Math.Clamp(-c / aa, 0, 1); }
                else if (t > 1) { t = 1; s = Math.Clamp((bb - c) / aa, 0, 1); }
            }
        }
        var c1 = p + d1 * s; var c2 = a + d2 * t;
        return (s, c1, (c1 - c2).Length());
    }

    /// <summary>The shortest turn taking direction a to direction b.</summary>
    static Quaternion FromTo(Vector3 a, Vector3 b)
    {
        float la = a.Length(), lb = b.Length();
        if (la < 1e-9f || lb < 1e-9f) return Quaternion.Identity;
        a /= la; b /= lb;
        float d = Vector3.Dot(a, b);
        if (d < -0.9999f) return Quaternion.CreateFromAxisAngle(Math.Abs(a.X) < 0.9f ? Vector3.Normalize(Vector3.Cross(a, Vector3.UnitX)) : Vector3.UnitY, MathF.PI);
        var c = Vector3.Cross(a, b);
        return Quaternion.Normalize(new Quaternion(c, 1 + d));
    }

    static Vector3 PointOnSegment(Vector3 a, Vector3 b, Vector3 p)
    {
        var ab = b - a;
        float l = Vector3.Dot(ab, ab);
        return l <= 1e-12f ? a : a + ab * Math.Clamp(Vector3.Dot(p - a, ab) / l, 0, 1);
    }

    /// <summary>Particle order for named links (bone, parent): each chain from a link whose parent is not a link, down
    /// through the links parented to it. Returns, per link in the given order, its particle (the link's tail), and per
    /// particle its parent particle (-1: a chain's pinned root, one per chain, before its links).</summary>
    public static (int[] LinkParticle, int[] Parent, int[] RootLink) Order(IReadOnlyList<(string Bone, string Parent)> links)
    {
        var idx = new Dictionary<string, int>();
        for (int i = 0; i < links.Count; i++) idx[links[i].Bone] = i;
        var kids = new Dictionary<int, List<int>>();
        var roots = new List<int>();
        for (int i = 0; i < links.Count; i++)
            if (idx.TryGetValue(links[i].Parent, out int pi)) { if (!kids.TryGetValue(pi, out var l)) kids[pi] = l = new(); l.Add(i); }
            else roots.Add(i);
        var lp = new int[links.Count];
        Array.Fill(lp, -1);
        var par = new List<int>();
        var rootLink = new List<int>();
        void Walk(int link, int headParticle)
        {
            lp[link] = par.Count;
            par.Add(headParticle);
            rootLink.Add(-1);
            if (kids.TryGetValue(link, out var ks)) foreach (var k in ks) Walk(k, lp[link]);
        }
        foreach (var r in roots)
        {
            int head = par.Count;
            par.Add(-1);
            rootLink.Add(r);
            Walk(r, head);
        }
        return (lp, par.ToArray(), rootLink.ToArray());
    }

    /// <summary>A bone's forward pitch (degrees): its direction now against at rest, both seen side-on (about +X, the
    /// body's lateral axis; forward is +Z), positive as the top tips forward.</summary>
    public static float Pitch(Vector3 rest, Vector3 now)
    {
        var a = new Vector2(rest.Y, rest.Z); var b = new Vector2(now.Y, now.Z);
        float cross = a.X * b.Y - a.Y * b.X, dot = Vector2.Dot(a, b);
        return MathF.Atan2(cross, dot) * 180f / MathF.PI;
    }

    /// <summary>A corrective's weight: 0 at From degrees, 1 at To, smoothstep between.</summary>
    public static float Weight(float deg, float from, float to)
    {
        if (to == from) return deg >= to ? 1 : 0;
        float u = Math.Clamp((deg - from) / (to - from), 0, 1);
        return u * u * (3 - 2 * u);
    }
}
