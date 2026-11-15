using System;
using System.Collections.Generic;
using System.Linq;
using System.Numerics;

namespace SurvivorUnchained.Play;

/// <summary>
/// Spring plates that ride their piece's own skin (a skirt's lappets, a pauldron's lames: each a rigid island on one
/// spring link, SpringCarry's Island rule), the targets and the collider of a ClothChains run on them.
/// Targets: where ClothChains' own ride each link's parent bone rigidly (a lappet hinged on the pelvis, blind to the thigh
/// it lies on), here each particle's target is where the piece's own weights carry that point this frame (a link's head
/// and tail skinned with the weights of its plate's vertices near them) and each link's axes are the best rigid fit of a
/// few of its plate's points under those weights (its twist). With no swing the plate moves as its file was skinned; the
/// chains add only the swing about that.
/// Collider (ClothChains.Hook, every solver iteration): the plate itself, not its centre line, is held off the body's
/// skin. A few dozen of its own points (on its inner face, and spread over it for its rims) against a sparse set of the
/// body's vertices skinned as the body is (its weights and blend shapes; eased through the substeps as the targets are),
/// each point pushed out along the body's normal there: a link with a pinned head turns about it (a point too near the
/// head to clear by a turn is left), a link down a chain moves both its ends (its head is its parent link's tail).
/// All of it is chosen once at dress time (Build: the points, each point's body candidates, the anchors' weights); a
/// frame skins the few points (Update), fits, steps the chains and collides. Deterministic. Engine-free
/// (System.Numerics): View/PieceSprings runs it, the tests hold it.
/// </summary>
public sealed class PlateFollow
{
    /// <summary>An affine map as Godot's Transform3D has it: basis columns X, Y, Z and origin O.</summary>
    public readonly record struct Xf(Vector3 X, Vector3 Y, Vector3 Z, Vector3 O)
    {
        public static readonly Xf Identity = new(Vector3.UnitX, Vector3.UnitY, Vector3.UnitZ, Vector3.Zero);
        public Vector3 Basis(Vector3 v) => X * v.X + Y * v.Y + Z * v.Z;
        public Vector3 Apply(Vector3 v) => X * v.X + Y * v.Y + Z * v.Z + O;
        public static Xf operator *(Xf a, Xf b) => new(a.Basis(b.X), a.Basis(b.Y), a.Basis(b.Z), a.Apply(b.O));
        public Xf Inverse()
        {
            var c0 = Vector3.Cross(Y, Z); var c1 = Vector3.Cross(Z, X); var c2 = Vector3.Cross(X, Y);
            float id = 1f / Vector3.Dot(X, c0);
            var r = new Xf(new Vector3(c0.X, c1.X, c2.X) * id, new Vector3(c0.Y, c1.Y, c2.Y) * id, new Vector3(c0.Z, c1.Z, c2.Z) * id, Vector3.Zero);
            return r with { O = -r.Basis(O) };
        }
        public float Scale => X.Length();
    }

    /// <summary>Margin: how far off the skin a plate's points are held (skeleton units); Cell: the body's points' spacing;
    /// Near: how far (at the bind) a body point may lie from a plate point to be tried against it; Inner: points a link
    /// on its plate's inner face (its normal against the body's), Rim: spread over all of it; Fit: points a link its axes
    /// are fitted to; AnchorVerts: the plate vertices nearest a head or tail whose weights it takes; MinLever: the least
    /// share of a pinned link's length a point lies along it to turn it (nearer its head no turn clears it); MaxPush: the
    /// most one push moves a link's end (skeleton units); Slide: a point too near a pinned head to clear by a turn slides
    /// the whole plate out (its hinge with it; the hinge is pinned again each substep, so only the last frame's push shows).</summary>
    public readonly record struct Tuning(float Margin = 0.003f, float Cell = 0.012f, float Near = 0.1f, int Inner = 24, int Rim = 8,
        int Fit = 16, int AnchorVerts = 32, float MinLever = 0.2f, float MaxPush = 0.05f, float FaceDot = -0.2f, bool Slide = true)
    {
        public static readonly Tuning Plate = new(Margin: 0.003f);
    }

    /// <summary>A spring link: head and tail (skeleton rest), its parent link (index, -1: on the body).</summary>
    public readonly record struct Link(Vector3 Head, Vector3 Tail, int Parent);

    /// <summary>A skinned mesh at the bind (dress time): per vertex its rest place (its weights' blend of its binds'
    /// frames at the bind, skeleton rest), its normal there, its K influences (skeleton bone, -1 unused; weight), each
    /// influence's own rest place where the binds disagree (At, K a vertex; null: all at Place), its blend shapes'
    /// offsets at weight 1 (skeleton rest axes; channel ChannelBase + shape in Update's weights), and for a piece each
    /// vertex's link (-1: not carried).</summary>
    public sealed class MeshIn
    {
        public int K;
        public Vector3[] Place = Array.Empty<Vector3>();
        public Vector3[] Normal = Array.Empty<Vector3>();
        public int[] Bone = Array.Empty<int>();
        public float[] Weight = Array.Empty<float>();
        public Vector3[]? At;
        public int ChannelBase;
        public Vector3[]?[] ShapeD = Array.Empty<Vector3[]?>();
        public Vector3[]?[] ShapeDn = Array.Empty<Vector3[]?>();
        public int[]? Link;
        public int Count => Place.Length;
    }

    /// <summary>Points skinned to the skeleton as their mesh is (K influences, each its own rest place), blend shapes as
    /// offsets (channel, offset, normal offset), posed into the world each Update (the last frame's kept for easing).</summary>
    sealed class Cloud
    {
        public int N, K;
        public int[] Bone = Array.Empty<int>();
        public float[] W = Array.Empty<float>();
        public Vector3[] At = Array.Empty<Vector3>();
        public Vector3[] Nrm0 = Array.Empty<Vector3>();
        public int[] SStart = Array.Empty<int>();
        public int[] SCh = Array.Empty<int>();
        public Vector3[] SD = Array.Empty<Vector3>(), SDn = Array.Empty<Vector3>();
        public Vector3[] P = Array.Empty<Vector3>(), Nn = Array.Empty<Vector3>(), Pp = Array.Empty<Vector3>();
        public bool Has;

        public static Cloud Of(IReadOnlyList<(MeshIn M, int V)> pts, int k)
        {
            var c = new Cloud { N = pts.Count, K = k };
            c.Bone = new int[c.N * k]; Array.Fill(c.Bone, -1);
            c.W = new float[c.N * k]; c.At = new Vector3[c.N * k]; c.Nrm0 = new Vector3[c.N];
            var start = new List<int>(); var ch = new List<int>(); var sd = new List<Vector3>(); var sdn = new List<Vector3>();
            for (int i = 0; i < c.N; i++)
            {
                var (m, v) = pts[i];
                // (its influences, heaviest first, at most k)
                var inf = Enumerable.Range(0, m.K).Select(q => (q, b: m.Bone[v * m.K + q], w: m.Weight[v * m.K + q]))
                    .Where(x => x.b >= 0 && x.w > 0).OrderByDescending(x => x.w).ThenBy(x => x.q).Take(k).ToArray();
                float sum = inf.Sum(x => x.w);
                for (int j = 0; j < inf.Length; j++)
                {
                    c.Bone[i * k + j] = inf[j].b;
                    c.W[i * k + j] = sum > 0 ? inf[j].w / sum : 0;
                    c.At[i * k + j] = m.At != null ? m.At[v * m.K + inf[j].q] : m.Place[v];
                }
                c.Nrm0[i] = m.Normal.Length > v ? m.Normal[v] : Vector3.UnitY;
                start.Add(ch.Count);
                for (int s = 0; s < m.ShapeD.Length; s++)
                {
                    var d = m.ShapeD[s]; var dn = s < m.ShapeDn.Length ? m.ShapeDn[s] : null;
                    var dv = d != null ? d[v] : Vector3.Zero; var dnv = dn != null ? dn[v] : Vector3.Zero;
                    if (dv == Vector3.Zero && dnv == Vector3.Zero) continue;
                    ch.Add(m.ChannelBase + s); sd.Add(dv); sdn.Add(dnv);
                }
            }
            start.Add(ch.Count);
            c.SStart = start.ToArray(); c.SCh = ch.ToArray(); c.SD = sd.ToArray(); c.SDn = sdn.ToArray();
            c.P = new Vector3[c.N]; c.Nn = new Vector3[c.N]; c.Pp = new Vector3[c.N];
            return c;
        }

        /// <summary>A point with averaged weights (an anchor): its influences and rest place given.</summary>
        public static Cloud OfAnchors(IReadOnlyList<(Vector3 At, (int Bone, float W)[] Inf)> pts, int k)
        {
            var c = new Cloud { N = pts.Count, K = k };
            c.Bone = new int[c.N * k]; Array.Fill(c.Bone, -1);
            c.W = new float[c.N * k]; c.At = new Vector3[c.N * k]; c.Nrm0 = new Vector3[c.N];
            for (int i = 0; i < c.N; i++)
                for (int j = 0; j < Math.Min(k, pts[i].Inf.Length); j++)
                { c.Bone[i * k + j] = pts[i].Inf[j].Bone; c.W[i * k + j] = pts[i].Inf[j].W; c.At[i * k + j] = pts[i].At; }
            c.SStart = new int[c.N + 1];
            c.P = new Vector3[c.N]; c.Nn = new Vector3[c.N]; c.Pp = new Vector3[c.N];
            return c;
        }

        /// <summary>Posed by the bones' skinning maps m (bone's pose times its rest's inverse, into the target space).</summary>
        public void Skin(Xf[] m, float[]? ch, bool normals, bool keep)
        {
            if (keep && Has) Array.Copy(P, Pp, N);
            for (int i = 0; i < N; i++)
            {
                Vector3 off = Vector3.Zero, offN = Vector3.Zero;
                if (ch != null)
                    for (int s = SStart[i]; s < SStart[i + 1]; s++)
                    {
                        float w = SCh[s] < ch.Length ? ch[SCh[s]] : 0;
                        if (w == 0) continue;
                        off += SD[s] * w; offN += SDn[s] * w;
                    }
                Vector3 p = Vector3.Zero, n = Vector3.Zero;
                for (int j = 0; j < K; j++)
                {
                    float w = W[i * K + j];
                    int b = Bone[i * K + j];
                    if (w <= 0 || b < 0 || b >= m.Length) continue;
                    p += m[b].Apply(At[i * K + j] + off) * w;
                    if (normals) n += m[b].Basis(Nrm0[i] + offN) * w;
                }
                P[i] = p;
                if (normals) Nn[i] = n.LengthSquared() > 1e-20f ? Vector3.Normalize(n) : Vector3.UnitY;
            }
            if (!Has || !keep) Array.Copy(P, Pp, N);
            Has = true;
        }
    }

    readonly Link[] links;
    readonly int[] linkParticle, parent, headParticle, order;
    readonly Tuning tune;
    readonly Cloud anchors;           // per particle
    readonly Cloud fitPts;            // per link: [fitStart[k], fitStart[k+1])
    readonly int[] fitStart;
    readonly Vector3[] fitRest;
    readonly Vector3[] fitRestMid;
    readonly Quaternion[] fit;
    readonly int[] sampStart;         // per link: its plate's points
    readonly Vector3[] samp;          // rest places
    readonly Cloud? sampShapes;       // (their blend shape offsets: rest places at 0, only the offsets used)
    readonly int[] candStart, cand;   // per plate point: its body points
    readonly Cloud? body;
    Xf w = Xf.Identity, wInv = Xf.Identity;
    readonly Vector3[] sampOff;       // this frame's shape offsets per plate point
    bool fitted;
    // (the collider's working sets: the body's points eased to the call's a, once per a; for each plate point its nearest
    // body point on each of up to Parts body parts (a part: the points one bone leads), kept from call to call: when the
    // body has moved (and every 3rd call while it stays) each walks its part's neighbours to a nearer one until none is;
    // the nearest of them is the plate point's. A cut starts them again from the bind's nearest)
    const int NearNb = 8, Parts = 4;
    readonly int[] bodyNb;            // per body point: its NearNb nearest others of its part at the bind (-1: none)
    readonly int[] seed, near;        // per plate point and part: the bind's nearest, the nearest now (-1: none)
    readonly Vector3[] bodyAt;
    float bodyA = float.NaN;
    int still;
    Xf[] wsBuf = Array.Empty<Xf>();

    public int Links => links.Length;
    public int BodyPoints => body?.N ?? 0;
    public int PlatePoints => samp.Length;
    public int Candidates => cand.Length;
    /// <summary>Pushes this frame and the deepest a plate point was found before its push (skeleton units).</summary>
    public int Pushes;
    public float Deepest;

    PlateFollow(Link[] links, int[] linkParticle, int[] parent, Tuning tune, Cloud anchors, Cloud fitPts, int[] fitStart, Vector3[] fitRest,
        int[] sampStart, Vector3[] samp, Cloud? sampShapes, int[] candStart, int[] cand, Cloud? body, int[] bodyNb, int[] seed)
    {
        this.links = links; this.linkParticle = linkParticle; this.parent = parent; this.tune = tune;
        headParticle = linkParticle.Select(p => parent[p]).ToArray();
        order = Enumerable.Range(0, links.Length).OrderBy(i => linkParticle[i]).ToArray();
        this.anchors = anchors; this.fitPts = fitPts; this.fitStart = fitStart; this.fitRest = fitRest;
        fitRestMid = new Vector3[links.Length];
        for (int k = 0; k < links.Length; k++)
        {
            var c = Vector3.Zero; int n = fitStart[k + 1] - fitStart[k];
            for (int i = fitStart[k]; i < fitStart[k + 1]; i++) c += fitRest[i];
            fitRestMid[k] = n > 0 ? c / n : links[k].Head;
        }
        fit = Enumerable.Repeat(Quaternion.Identity, links.Length).ToArray();
        this.sampStart = sampStart; this.samp = samp; this.sampShapes = sampShapes; this.candStart = candStart; this.cand = cand; this.body = body;
        sampOff = new Vector3[samp.Length];
        this.bodyNb = bodyNb; this.seed = seed;
        near = (int[])seed.Clone();
        bodyAt = new Vector3[body?.N ?? 0];
    }

    /// <summary>The plates of a row's links (their particles as ClothChains.Order lays them: each link's tail particle,
    /// each particle's parent), from the piece's meshes (each vertex's link: the carry's) and the body's (null: no
    /// collider). Null when no link has a vertex.</summary>
    public static PlateFollow? Build(IReadOnlyList<Link> links, int[] linkParticle, int[] parent, IReadOnlyList<MeshIn> pieces, MeshIn? bodyMesh, Tuning tune)
    {
        int nl = links.Count;
        // (each link's plate: its vertices, thinned to a spacing of half the body's)
        var plate = Enumerable.Range(0, nl).Select(_ => new List<(MeshIn M, int V)>()).ToArray();
        foreach (var m in pieces)
        {
            if (m.Link == null) continue;
            var seen = new HashSet<(int, long)>();
            for (int v = 0; v < m.Count; v++)
            {
                int l = m.Link[v];
                if (l < 0 || l >= nl) continue;
                if (!seen.Add((l, Key(m.Place[v], tune.Cell * 0.5f)))) continue;
                plate[l].Add((m, v));
            }
        }
        if (plate.All(p => p.Count == 0)) return null;
        var all = plate.SelectMany(p => p).ToList();
        // (the anchors: each chain's root head and each link's tail, with the weights of the plate vertices near them,
        // its own plate's and its child links')
        var kids = Enumerable.Range(0, nl).Select(k => Enumerable.Range(0, nl).Where(c => links[c].Parent == k).ToList()).ToArray();
        var anchorPts = new (Vector3 At, (int Bone, float W)[] Inf)[parent.Length];
        for (int k = 0; k < nl; k++)
        {
            var pool = plate[k].Concat(kids[k].SelectMany(c => plate[c])).ToList();
            anchorPts[linkParticle[k]] = (links[k].Tail, Blend(pool.Count > 0 ? pool : all, links[k].Tail, tune.AnchorVerts));
            int hp = parent[linkParticle[k]];
            if (hp >= 0 && parent[hp] < 0)
                anchorPts[hp] = (links[k].Head, Blend(plate[k].Count > 0 ? plate[k] : all, links[k].Head, tune.AnchorVerts));
        }
        for (int p = 0; p < anchorPts.Length; p++) anchorPts[p].Inf ??= Array.Empty<(int, float)>();
        var anchors = Cloud.OfAnchors(anchorPts, 4);
        // (the fit points: spread over each plate)
        var fitList = new List<(MeshIn M, int V)>();
        var fitStart = new int[nl + 1];
        for (int k = 0; k < nl; k++)
        {
            fitStart[k] = fitList.Count;
            var pts = plate[k].Select(x => x.M.Place[x.V]).ToList();
            foreach (int i in Spread(pts, tune.Fit, Nearest(pts, links[k].Head))) fitList.Add(plate[k][i]);
        }
        fitStart[nl] = fitList.Count;
        var fitPts = Cloud.Of(fitList, 8);
        var fitRest = fitList.Select(x => x.M.Place[x.V]).ToArray();
        // (the body's points: its vertices thinned to one a cell, those near any plate)
        Cloud? body = null;
        var reps = new List<int>();
        var repGrid = new Dictionary<long, List<int>>();
        float gc = Math.Max(tune.Cell * 2, 0.02f);
        if (bodyMesh != null)
        {
            var best = new Dictionary<long, (int V, float D)>();
            float c = tune.Cell;
            var near = new HashSet<long>();
            foreach (var (m, v) in all) foreach (long kk in Around(m.Place[v], tune.Near, tune.Near)) near.Add(kk);
            for (int v = 0; v < bodyMesh.Count; v++)
            {
                var p = bodyMesh.Place[v];
                if (!near.Contains(Key(p, tune.Near))) continue;
                long key = Key(p, c);
                var centre = new Vector3(MathF.Floor(p.X / c) + 0.5f, MathF.Floor(p.Y / c) + 0.5f, MathF.Floor(p.Z / c) + 0.5f) * c;
                float d = Vector3.DistanceSquared(p, centre);
                if (!best.TryGetValue(key, out var b) || d < b.D) best[key] = (v, d);
            }
            reps = best.Values.Select(x => x.V).OrderBy(v => v).ToList();
            for (int i = 0; i < reps.Count; i++)
            {
                long key = Key(bodyMesh.Place[reps[i]], gc);
                if (!repGrid.TryGetValue(key, out var l)) repGrid[key] = l = new List<int>();
                l.Add(i);
            }
        }
        // (each plate's points: on its inner face (its normal against the nearest body point's), the nearest the body
        // first, then spread over all of it (its rims))
        var sampList = new List<(MeshIn M, int V)>();
        var sampStart = new int[nl + 1];
        for (int k = 0; k < nl; k++)
        {
            sampStart[k] = sampList.Count;
            var pts = plate[k].Select(x => x.M.Place[x.V]).ToList();
            if (pts.Count == 0) continue;
            var picked = new List<int>();
            if (bodyMesh != null && reps.Count > 0)
            {
                var inner = new List<int>(); float closest = float.MaxValue; int first = -1;
                for (int i = 0; i < pts.Count; i++)
                {
                    int r = NearestRep(repGrid, bodyMesh, reps, pts[i], gc, Math.Min(tune.Near, 0.05f));
                    if (r < 0) continue;
                    var bp = bodyMesh.Place[reps[r]]; var bn = bodyMesh.Normal[reps[r]];
                    var (m, v) = plate[k][i];
                    if (Vector3.Dot(m.Normal[v], bn) >= tune.FaceDot) continue;
                    inner.Add(i);
                    float d = Vector3.Dot(pts[i] - bp, bn);
                    if (d < closest) { closest = d; first = inner.Count - 1; }
                }
                if (inner.Count > 0)
                    foreach (int j in Spread(inner.Select(i => pts[i]).ToList(), tune.Inner, first)) picked.Add(inner[j]);
            }
            foreach (int i in Spread(pts, tune.Rim + Math.Max(0, tune.Inner - picked.Count), Farthest(pts, picked.Count > 0 ? pts[picked[0]] : links[k].Head)))
                if (!picked.Contains(i)) picked.Add(i);
            foreach (int i in picked) sampList.Add(plate[k][i]);
        }
        sampStart[nl] = sampList.Count;
        var samp = sampList.Select(x => x.M.Place[x.V]).ToArray();
        Cloud? sampShapes = sampList.Any(x => x.M.ShapeD.Length > 0) ? Cloud.Of(sampList, 1) : null;
        // (each plate point's body candidates: the body points within Near of it at the bind)
        var candStart = new int[samp.Length + 1];
        var cand = new List<int>();
        var used = new Dictionary<int, int>();
        var candRep = new List<int>();
        for (int s = 0; s < samp.Length; s++)
        {
            candStart[s] = cand.Count;
            if (bodyMesh == null) continue;
            var found = new List<int>();
            foreach (long kk in Around(samp[s], tune.Near, gc))
                if (repGrid.TryGetValue(kk, out var l))
                    foreach (int r in l)
                        if (Vector3.DistanceSquared(bodyMesh.Place[reps[r]], samp[s]) <= tune.Near * tune.Near) found.Add(r);
            found.Sort();
            foreach (int r in found)
            {
                if (!used.TryGetValue(r, out int ci)) { ci = candRep.Count; used[r] = ci; candRep.Add(r); }
                cand.Add(ci);
            }
        }
        candStart[samp.Length] = cand.Count;
        if (bodyMesh != null && candRep.Count > 0) body = Cloud.Of(candRep.Select(r => (bodyMesh, reps[r])).ToList(), Math.Min(8, bodyMesh.K));
        // (each body point's nearest others at the bind: the steps the collider walks)
        var bodyNb = Array.Empty<int>();
        var seed = new int[samp.Length * Parts];
        Array.Fill(seed, -1);
        if (body != null)
        {
            var rp = candRep.Select(r => bodyMesh!.Place[reps[r]]).ToArray();
            // (each body point's part: the bone with its most weight)
            var part = candRep.Select(r =>
            {
                int v = reps[r], best = -1; float bw = -1;
                for (int q = 0; q < bodyMesh!.K; q++) if (bodyMesh.Weight[v * bodyMesh.K + q] > bw) { bw = bodyMesh.Weight[v * bodyMesh.K + q]; best = bodyMesh.Bone[v * bodyMesh.K + q]; }
                return best;
            }).ToArray();
            for (int sp = 0; sp < samp.Length; sp++)
            {
                // (its nearest candidate on each part at the bind, the Parts nearest parts kept)
                var byPart = new Dictionary<int, (float D, int J)>();
                for (int c = candStart[sp]; c < candStart[sp + 1]; c++)
                {
                    int j = cand[c]; float d2 = Vector3.DistanceSquared(rp[j], samp[sp]);
                    if (!byPart.TryGetValue(part[j], out var have) || d2 < have.D) byPart[part[j]] = (d2, j);
                }
                int i = 0;
                foreach (var e in byPart.Values.OrderBy(e => e.D).ThenBy(e => e.J).Take(Parts)) seed[sp * Parts + i++] = e.J;
            }
            bodyNb = new int[rp.Length * NearNb];
            var nd = new float[NearNb];
            for (int j = 0; j < rp.Length; j++)
            {
                int o0 = j * NearNb;
                for (int m = 0; m < NearNb; m++) { bodyNb[o0 + m] = -1; nd[m] = float.MaxValue; }
                for (int o = 0; o < rp.Length; o++)
                {
                    if (o == j || part[o] != part[j]) continue;
                    float d2 = Vector3.DistanceSquared(rp[o], rp[j]);
                    if (d2 >= nd[NearNb - 1]) continue;
                    int m = NearNb - 1;
                    while (m > 0 && nd[m - 1] > d2) { nd[m] = nd[m - 1]; bodyNb[o0 + m] = bodyNb[o0 + m - 1]; m--; }
                    nd[m] = d2; bodyNb[o0 + m] = o;
                }
            }
        }
        return new PlateFollow(links.ToArray(), linkParticle, parent, tune, anchors, fitPts, fitStart, fitRest, sampStart, samp, sampShapes,
            candStart, cand.ToArray(), body, bodyNb, seed);
    }

    /// <summary>This frame: the bones' skinning maps (skeleton space: each bone's pose times its rest's inverse, by
    /// skeleton bone), the skeleton's world transform, the blend shape weights (by channel). Fills the particles'
    /// targets (world) and fits each link's axes; poses the body's points (the last frame's kept for the substeps).</summary>
    public void Update(Xf[] skin, Xf world, float[]? shapeWeights, Vector3[] targets)
    {
        w = world; wInv = world.Inverse();
        if (wsBuf.Length != skin.Length) wsBuf = new Xf[skin.Length];
        var ws = wsBuf;
        for (int b = 0; b < skin.Length; b++) ws[b] = world * skin[b];
        anchors.Skin(ws, null, false, false);
        for (int p = 0; p < targets.Length && p < anchors.N; p++) targets[p] = anchors.P[p];
        fitPts.Skin(skin, shapeWeights, false, false);
        for (int k = 0; k < links.Length; k++) fit[k] = Fit(k, fitted ? 6 : 30);
        fitted = true;
        if (sampShapes != null)
        {
            // (the plate points' blend shape offsets at this frame's weights, in their rest frame: the carried vertices keep theirs)
            for (int s = 0; s < samp.Length; s++)
            {
                var off = Vector3.Zero;
                for (int j = sampShapes.SStart[s]; j < sampShapes.SStart[s + 1]; j++)
                {
                    float wt = shapeWeights != null && sampShapes.SCh[j] < shapeWeights.Length ? shapeWeights[sampShapes.SCh[j]] : 0;
                    off += sampShapes.SD[j] * wt;
                }
                sampOff[s] = off;
            }
        }
        body?.Skin(ws, shapeWeights, true, true);
        Pushes = 0; Deepest = 0;
        bodyA = float.NaN;
    }

    /// <summary>A cut: the body's points start the next frame where they are now (no easing in from before it).</summary>
    public void Cut() { if (body != null) body.Has = false; Array.Copy(seed, near, seed.Length); }

    Quaternion Fit(int k, int iterations)
    {
        int a = fitStart[k], b = fitStart[k + 1];
        if (b - a < 3) return fit[k];
        var qm = Vector3.Zero;
        for (int i = a; i < b; i++) qm += fitPts.P[i];
        qm /= b - a;
        Vector3 c0 = Vector3.Zero, c1 = Vector3.Zero, c2 = Vector3.Zero;
        for (int i = a; i < b; i++)
        {
            var q = fitPts.P[i] - qm; var r = fitRest[i] - fitRestMid[k];
            c0 += q * r.X; c1 += q * r.Y; c2 += q * r.Z;
        }
        return Rotation(c0, c1, c2, fit[k], iterations);
    }

    /// <summary>The rotation part of the matrix with columns a0..a2 (Müller et al. 2016, "A Robust Method to Extract the
    /// Rotational Part of Deformations"), from the guess q.</summary>
    public static Quaternion Rotation(Vector3 a0, Vector3 a1, Vector3 a2, Quaternion q, int iterations)
    {
        for (int it = 0; it < iterations; it++)
        {
            var r0 = Vector3.Transform(Vector3.UnitX, q); var r1 = Vector3.Transform(Vector3.UnitY, q); var r2 = Vector3.Transform(Vector3.UnitZ, q);
            var om = (Vector3.Cross(r0, a0) + Vector3.Cross(r1, a1) + Vector3.Cross(r2, a2))
                * (1f / (MathF.Abs(Vector3.Dot(r0, a0) + Vector3.Dot(r1, a1) + Vector3.Dot(r2, a2)) + 1e-9f));
            float wl = om.Length();
            if (wl < 1e-7f) break;
            q = Quaternion.Normalize(Quaternion.CreateFromAxisAngle(om / wl, wl) * q);
        }
        return q;
    }

    /// <summary>The collider (ClothChains.Hook): each link's plate points held Margin off the body's points' planes, the
    /// body eased to a (0..1) through the frame.</summary>
    public void Collide(Vector3[] x, float a)
    {
        if (body == null) return;
        float scale = w.Scale, margin = tune.Margin * scale, maxPush = tune.MaxPush * scale;
        bool moved = a != bodyA;
        // (the body still, as through a reset's settle: the plates' own moves walked every 3rd call)
        still = moved ? 0 : still + 1;
        bool walk = moved || still % 3 == 0;
        if (moved)
        {
            for (int j = 0; j < bodyAt.Length; j++) bodyAt[j] = Vector3.Lerp(body.Pp[j], body.P[j], a);
            bodyA = a;
        }
        foreach (int k in order)
        {
            int ti = linkParticle[k], hi = headParticle[k];
            bool pinned = parent[hi] < 0;
            var chordRest = links[k].Tail - links[k].Head;
            var lin = fit[k];
            var chordT = w.Basis(Vector3.Transform(chordRest, lin));
            for (int s = sampStart[k]; s < sampStart[k + 1]; s++)
            {
                var h = x[hi]; var t = x[ti];
                var chord = t - h;
                float cl2 = chord.LengthSquared();
                if (cl2 < 1e-12f) break;
                var q = FromTo(chordT, chord);
                var p = h + Vector3.Transform(w.Basis(Vector3.Transform(samp[s] + sampOff[s] - links[k].Head, lin)), q);
                // (its nearest body point, and how far it stands off that point's plane)
                int bi = -1; float bd = float.MaxValue;
                for (int u = s * Parts; u < s * Parts + Parts; u++)
                {
                    int ci = near[u];
                    if (ci < 0) break;
                    var at0 = bodyAt[ci];
                    float ex = at0.X - p.X, ey = at0.Y - p.Y, ez = at0.Z - p.Z, cd = ex * ex + ey * ey + ez * ez;
                    if (walk)
                    {
                        // (from its last nearest on this part, step to the nearest of its neighbours while one is nearer)
                        for (int step = 0; step < 32; step++)
                        {
                            int best = -1, o0 = ci * NearNb;
                            for (int m = 0; m < NearNb; m++)
                            {
                                int o = bodyNb[o0 + m];
                                if (o < 0) break;
                                var at = bodyAt[o];
                                float dx = at.X - p.X, dy = at.Y - p.Y, dz = at.Z - p.Z, d2 = dx * dx + dy * dy + dz * dz;
                                if (d2 < cd) { cd = d2; best = o; }
                            }
                            if (best < 0) break;
                            ci = best;
                        }
                        near[u] = ci;
                    }
                    if (cd < bd) { bd = cd; bi = ci; }
                }
                if (bi < 0) continue;
                var bp = bodyAt[bi];
                var n = body.Nn[bi];
                float off = Vector3.Dot(p - bp, n);
                float push = margin - off;
                if (push <= 0) continue;
                Deepest = Math.Max(Deepest, -off / scale);
                float sgm = Vector3.Dot(p - h, chord) / cl2;
                if (pinned)
                {
                    if (sgm < tune.MinLever)
                    {
                        // (too near its head for a turn to clear it: the whole plate slid out, its hinge with it)
                        if (!tune.Slide) continue;
                        float m0 = Math.Min(push, maxPush);
                        x[hi] = h + n * m0; x[ti] = t + n * m0;
                    }
                    else x[ti] = t + n * Math.Min(push / Math.Min(sgm, 1f), maxPush);
                }
                else
                {
                    sgm = Math.Clamp(sgm, 0, 1);
                    float wsum = sgm * sgm + (1 - sgm) * (1 - sgm);
                    x[ti] = t + n * Math.Min(push * sgm / wsum, maxPush);
                    x[hi] = h + n * Math.Min(push * (1 - sgm) / wsum, maxPush);
                }
                Pushes++;
            }
        }
    }

    /// <summary>A link's turn from its rest (skeleton space) and its head (skeleton space), the chains' particles x as they
    /// are (world): its fitted axes turned so its tail points at its tail particle. The spring bone's global pose is
    /// (Basis(turn) times its rest's basis, head).</summary>
    public (Quaternion Turn, Vector3 Head) Pose(int k, IReadOnlyList<Vector3> x)
    {
        var hs = wInv.Apply(x[headParticle[k]]); var ts = wInv.Apply(x[linkParticle[k]]);
        var chordT = Vector3.Transform(links[k].Tail - links[k].Head, fit[k]);
        var q = FromTo(chordT, ts - hs);
        return (Quaternion.Normalize(q * fit[k]), hs);
    }

    /// <summary>A link's fitted axes this frame (skeleton space; its turn from the rest with no swing).</summary>
    public Quaternion Fitted(int k) => fit[k];

    static Quaternion FromTo(Vector3 a, Vector3 b)
    {
        float la = a.Length(), lb = b.Length();
        if (la < 1e-9f || lb < 1e-9f) return Quaternion.Identity;
        a /= la; b /= lb;
        float d = Vector3.Dot(a, b);
        if (d < -0.9999f)
        {
            var ax = Vector3.Cross(a, MathF.Abs(a.X) < 0.9f ? Vector3.UnitX : Vector3.UnitY);
            return Quaternion.CreateFromAxisAngle(Vector3.Normalize(ax), MathF.PI);
        }
        return Quaternion.Normalize(new Quaternion(Vector3.Cross(a, b), 1 + d));
    }

    /// <summary>The weights of the n plate vertices nearest p (by 1/(distance + 5 mm)), their four heaviest bones.</summary>
    static (int Bone, float W)[] Blend(List<(MeshIn M, int V)> pool, Vector3 p, int n)
    {
        var near = pool.Select((x, i) => (i, d: Vector3.Distance(x.M.Place[x.V], p))).OrderBy(x => x.d).ThenBy(x => x.i).Take(Math.Max(1, n)).ToList();
        var acc = new Dictionary<int, float>();
        foreach (var (i, d) in near)
        {
            var (m, v) = pool[i];
            float c = 1f / (d + 0.005f);
            for (int q = 0; q < m.K; q++)
            {
                int b = m.Bone[v * m.K + q]; float wq = m.Weight[v * m.K + q];
                if (b < 0 || wq <= 0) continue;
                acc[b] = (acc.TryGetValue(b, out var o) ? o : 0) + c * wq;
            }
        }
        var top = acc.OrderByDescending(x => x.Value).ThenBy(x => x.Key).Take(4).ToArray();
        float sum = top.Sum(x => x.Value);
        return top.Select(x => (x.Key, sum > 0 ? x.Value / sum : 0)).ToArray();
    }

    /// <summary>Farthest-point picks: n indices of pts, from first, each the farthest from those picked (ties: lower).</summary>
    public static List<int> Spread(IReadOnlyList<Vector3> pts, int n, int first)
    {
        var o = new List<int>();
        if (pts.Count == 0 || n <= 0) return o;
        var d = new float[pts.Count];
        Array.Fill(d, float.MaxValue);
        int cur = Math.Clamp(first, 0, pts.Count - 1);
        while (o.Count < Math.Min(n, pts.Count))
        {
            o.Add(cur);
            int next = -1; float far = -1;
            for (int i = 0; i < pts.Count; i++)
            {
                d[i] = Math.Min(d[i], Vector3.DistanceSquared(pts[i], pts[cur]));
                if (d[i] > far) { far = d[i]; next = i; }
            }
            if (far <= 0) break;
            cur = next;
        }
        return o;
    }

    static int Nearest(IReadOnlyList<Vector3> pts, Vector3 p)
    {
        int best = 0; float bd = float.MaxValue;
        for (int i = 0; i < pts.Count; i++) { float d = Vector3.DistanceSquared(pts[i], p); if (d < bd) { bd = d; best = i; } }
        return best;
    }

    static int Farthest(IReadOnlyList<Vector3> pts, Vector3 p)
    {
        int best = 0; float bd = -1;
        for (int i = 0; i < pts.Count; i++) { float d = Vector3.DistanceSquared(pts[i], p); if (d > bd) { bd = d; best = i; } }
        return best;
    }

    static int NearestRep(Dictionary<long, List<int>> grid, MeshIn body, List<int> reps, Vector3 p, float cell, float cap)
    {
        int best = -1; float bd = cap * cap;
        foreach (long k in Around(p, cap, cell))
            if (grid.TryGetValue(k, out var l))
                foreach (int r in l)
                {
                    float d = Vector3.DistanceSquared(body.Place[reps[r]], p);
                    if (d < bd) { bd = d; best = r; }
                }
        return best;
    }

    static long Key(Vector3 p, float c) => Key((int)MathF.Floor(p.X / c), (int)MathF.Floor(p.Y / c), (int)MathF.Floor(p.Z / c));
    static long Key(int x, int y, int z) => ((long)(x + (1 << 20)) << 42) | ((long)(y + (1 << 20)) << 21) | (long)(z + (1 << 20));

    static IEnumerable<long> Around(Vector3 p, float r, float c)
    {
        int x0 = (int)MathF.Floor((p.X - r) / c), x1 = (int)MathF.Floor((p.X + r) / c);
        int y0 = (int)MathF.Floor((p.Y - r) / c), y1 = (int)MathF.Floor((p.Y + r) / c);
        int z0 = (int)MathF.Floor((p.Z - r) / c), z1 = (int)MathF.Floor((p.Z + r) / c);
        for (int x = x0; x <= x1; x++) for (int y = y0; y <= y1; y++) for (int z = z0; z <= z1; z++) yield return Key(x, y, z);
    }
}
