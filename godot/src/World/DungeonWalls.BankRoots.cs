using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// The den banks' big roots (den round 9, lane BANKS, 15 Nov): geometry where the painted bank alone read as flat
/// cut-outs under a grey scrim (judge round 8). FROM den_room.png / den_boss.png: masses of huge roots 0.8-1.2 m thick in
/// long sweeping runs along the bank that arch over and dive into the earth, roots coming down off the bank and arching
/// onto the floor, and on the far (back) banks root columns climbing into the dark. Lit by the den rig (the key from the
/// upper left), so the lit tops, the shaded sides, the cast shadows and the dark hollows under the arches are real; the
/// painted bank (dungeon_wall.gdshader) is the dark tangle between them. View only: no physics body, the walkable field
/// and the generator untouched. Chunked by 32 m cells so the camera and the shadow pass cull them.
/// --den-roots2 0: the round-8 banks (no big roots, the old bank shading).
/// </summary>
public static partial class DungeonWalls
{
    static readonly bool BigRoots = Args.Num("den-roots2", 0f) > 0.5f;
    static readonly float Girth = Args.Num("den-root-girth", 1f);      // the big roots' thickness, x
    static readonly float RootGap = Args.Num("den-root-gap", 2.6f);    // metres of bank edge per station (the density's knob)
    const float BankRootKind = 0.8f, ChunkM = 32f, Ds = 0.3f;

    // The den bank's surface as its mesh has it (Place: BankY with the face's lumps), never under the floor.
    static float SurfAt(Ctx c, float x, float z) => Mathf.Max(c.BankY(x, z, c.S(x, z)), c.Floor(x, z));
    static Vector3 SurfN(Ctx c, float x, float z)
    {
        const float e = 0.3f;
        float hx = SurfAt(c, x + e, z) - SurfAt(c, x - e, z), hz = SurfAt(c, x, z + e) - SurfAt(c, x, z - e);
        return new Vector3(-hx, 2 * e, -hz).Normalized();
    }
    // Onto the line where the bank's outside distance is want (S is metres outside the walkable edge).
    static bool SnapS(Ctx c, ref Vector2 h, float want)
    {
        for (int it = 0; it < 4; it++) h += c.Grad(null, h.X, h.Y, true) * (want - c.S(h.X, h.Y));
        return Mathf.Abs(c.S(h.X, h.Y) - want) < 0.35f;
    }
    // Clear of the map's border and of the pits (a pit's rim is the pit lane's).
    static bool Clear(Ctx c, Vector2 h) => Mathf.Abs(h.X) < c.Half - 6 && Mathf.Abs(h.Y) < c.Half - 6 && c.Bil(c.Hf, h.X, h.Y) > 1.2f;

    static void BankRoots(Ctx c, float[] s, int n, Node3D parent, Material mat)
    {
        var bufs = new Dictionary<(int, int), Buf>();
        Buf B(Vector2 p)
        {
            var k = (Mathf.FloorToInt(p.X / ChunkM), Mathf.FloorToInt(p.Y / ChunkM));
            if (!bufs.TryGetValue(k, out var bb)) bufs[k] = bb = new Buf();
            return bb;
        }
        // Stations along the bank's foot, at least 0.8 RootGap apart (the contour's segments come in raster order, so
        // the running length alone would bunch them).
        var taken = new Dictionary<(int, int), List<Vector2>>();
        bool Near(Vector2 p, float d)
        {
            int ci = Mathf.FloorToInt(p.X / 4f), cj = Mathf.FloorToInt(p.Y / 4f);
            for (int dj = -1; dj <= 1; dj++)
                for (int di = -1; di <= 1; di++)
                    if (taken.TryGetValue((ci + di, cj + dj), out var l))
                        foreach (var q in l) if (q.DistanceSquaredTo(p) < d * d) return true;
            return false;
        }
        float acc = 0, next = 1f;
        int st = 0;
        foreach (var (a, e) in Contour(s, n, 0.3f, c.Half))
        {
            float len = a.DistanceTo(e), at = 0;
            while (acc + len - at >= next)
            {
                at += next - acc; acc = 0;
                var p = a.Lerp(e, len > 0 ? at / len : 0);
                int hx = Mathf.RoundToInt(p.X * 4), hz = Mathf.RoundToInt(p.Y * 4);
                next = 0.5f;
                if (!Clear(c, p) || Near(p, RootGap * (0.8f + 0.4f * Hash01(hx, hz, 5)))) continue;
                var key = (Mathf.FloorToInt(p.X / 4f), Mathf.FloorToInt(p.Y / 4f));
                if (!taken.TryGetValue(key, out var lst)) taken[key] = lst = new List<Vector2>();
                lst.Add(p);
                Station(c, B(p), p, hx, hz);
                st++;
            }
            acc += len - at;
        }
        int tris = 0;
        foreach (var (k, bb) in bufs)
        {
            if (bb.V.Count == 0) continue;
            var m = new ArrayMesh();
            bb.ToMesh(m);
            m.SurfaceSetMaterial(0, mat);
            tris += bb.I.Count / 3;
            parent.AddChild(new MeshInstance3D { Name = $"BankRoots_{k.Item1}_{k.Item2}", Mesh = m, CastShadow = GeometryInstance3D.ShadowCastingSetting.On });
        }
        GD.Print($"DungeonWalls den: {st} bank root stations, {tris} big-root tris in {bufs.Count} chunks");
    }

    // One station's roots: a big runner along the bank, a root down off the bank onto the floor, and on a back bank a
    // column climbing the far wall into the dark. Each by its own hash; the roots along a stretch lean one way.
    static void Station(Ctx c, Buf b, Vector2 p, int hx, int hz)
    {
        float H(int k) => Hash01(hx, hz, 300 + k);
        var g = c.Grad(null, p.X, p.Y, true);
        var t = new Vector2(-g.Y, g.X) * (N2(p.X * 0.07f + 3.3f, p.Y * 0.07f - 8.1f) < 0.5f ? -1 : 1);
        float sc = c.BankSc(p.X, p.Y), bk = c.Back(p.X, p.Y), fy = c.Floor(p.X, p.Y);
        float top = sc + Ctx.BackRun * bk;
        int sd = hx * 7919 + hz * 104729;

        // 1. A runner: along the bank, its outside distance wandering on a long wave between the foot and the crest (on
        // up the far wall), coming out of the earth, lifting off the bank in arches with dark hollows under them, now
        // and then diving under and out again, sinking at its end.
        if (H(1) < 0.85f)
        {
            float len = 5f + 4f * H(2), r0 = Girth * (0.36f + 0.2f * H(3));
            float lo = 0.35f + r0 * 0.5f, hi = Mathf.Max(lo + 0.3f, (bk > 0.5f ? top - 0.6f : sc + 0.2f));
            float s0 = Mathf.Lerp(lo, hi, 0.15f + 0.7f * H(4)), amp = 0.4f + 0.9f * H(5) * (hi - lo) * 0.5f;
            var q = p - t * (len * (0.3f + 0.3f * H(6)));
            if (SnapS(c, ref q, s0) && Clear(c, q))
            {
                var path = Run(c, q, t, s0, amp, 5f + 4f * H(7), 6.283f * H(8), len, lo, hi);
                var (r, up, dn) = Profile(path.Count);
                float L = (path.Count - 1) * Ds;
                int arches = H(9) < 0.75f ? 1 + (H(10) < 0.45f ? 1 : 0) : 0;
                bool dive = H(11) < 0.35f && L > 5.5f;
                for (int k = 0; k < path.Count; k++)
                {
                    float a = k * Ds, done = a / Mathf.Max(L, 0.01f);
                    r[k] = r0 * Knots(a, sd) * Mathf.Lerp(1f, 0.7f, Sm(0.6f, 1f, done)) * (1 + 0.2f * (1 - Sm(0f, 1.2f, a)));
                    dn[k] = 1.25f * (1 - Sm(0.1f, 1.1f, a)) + 1.4f * Sm(L - 1.2f, L - 0.1f, a);
                    if (dive) { float dc = L * (0.45f + 0.15f * H(12)); dn[k] += 1.5f * Bump(a, dc - 0.8f, dc + 0.8f); }
                    for (int i = 0; i < arches; i++)
                    {
                        float ac = L * (i == 0 ? 0.25f + 0.15f * H(13) : 0.68f + 0.12f * H(14)), aw = 1.4f + 1.2f * H(15 + i);
                        up[k] += (0.2f + 0.45f * H(17 + i)) * Bump(a, ac - aw * 0.5f, ac + aw * 0.5f);
                    }
                }
                Lay(c, b, path, r, up, dn, false, fy, H(19));
            }
        }

        // 2. A root down off the bank: from the crest (or partway up the far wall) down the face, slanting, bridging the
        // bank's foot in an arch onto the floor, out over it 1-2.5 m, tapering, its tip sunk.
        if (H(20) < 0.6f)
        {
            float r0 = Girth * (0.28f + 0.16f * H(21));
            float s0 = bk > 0.5f ? Mathf.Lerp(sc, top, 0.2f + 0.5f * H(22)) : sc * (0.75f + 0.3f * H(22));
            var q = p + t * (1.6f * (2 * H(23) - 1));
            if (SnapS(c, ref q, s0) && Clear(c, q))
            {
                var path = Down(c, q, t, 0.55f * (2 * H(24) - 1), -(1.1f + 1.5f * H(25)), sd + 5);
                Hang(c, b, path, r0, sd + 5, fy, H(26), 0.15f + 0.3f * H(27));
            }
        }

        // 3. On a back bank, a root column: from the top of the far wall down its face and out, thick, flaring at its
        // foot; the far wall's trunks (den_room.png's top).
        if (bk > 0.5f && H(30) < 0.55f)
        {
            float r0 = Girth * (0.42f + 0.22f * H(31));
            var q = p + t * (1.4f * (2 * H(32) - 1));
            if (SnapS(c, ref q, top + 0.4f) && Clear(c, q))
            {
                var path = Down(c, q, t, 0.3f * (2 * H(33) - 1), -(0.6f + 1.2f * H(34)), sd + 9);
                Hang(c, b, path, r0, sd + 9, fy, H(35), 0.1f + 0.25f * H(36));
            }
        }
    }

    static float Bump(float a, float a0, float a1) => a <= a0 || a >= a1 ? 0 : Mathf.Sin(Mathf.Pi * (a - a0) / (a1 - a0));
    static float Knots(float a, int sd) => (1 + 0.12f * (2 * N3(a * 1.1f, sd * 0.013f, 1.7f) - 1)) * (1 + 0.18f * Sm(0.68f, 0.86f, N3(a * 1.7f + 11f, sd * 0.017f, 3f)));
    static (List<float> R, List<float> Up, List<float> Dn) Profile(int n)
    {
        var r = new List<float>(n); var up = new List<float>(n); var dn = new List<float>(n);
        for (int k = 0; k < n; k++) { r.Add(0); up.Add(0); dn.Add(0); }
        return (r, up, dn);
    }

    // A runner's plan path: along t, s wandering on a sine of the given wave between lo and hi.
    static List<Vector2> Run(Ctx c, Vector2 h, Vector2 t, float s0, float amp, float wave, float ph, float len, float lo, float hi)
    {
        var pts = new List<Vector2> { h };
        float a = 0;
        while (a < len)
        {
            var g = c.Grad(null, h.X, h.Y, true);
            var nt = new Vector2(-g.Y, g.X);
            t = nt.Dot(t) < 0 ? -nt : nt;
            var prev = h;
            h += t * Ds;
            float want = Mathf.Clamp(s0 + amp * Mathf.Sin(Mathf.Tau * a / wave + ph) - amp * Mathf.Sin(ph), lo, hi);
            if (!SnapS(c, ref h, want) || !Clear(c, h)) break;
            // keep the steps even (the snap moves it across the bank as well)
            var d = h - prev;
            if (d.LengthSquared() > 1e-6f) h = prev + d.Normalized() * Ds;
            a += Ds;
            pts.Add(h);
        }
        return pts;
    }

    // A plan path down the bank (against S's gradient) turned slant radians toward t, wandering, until S < sEnd.
    static List<Vector2> Down(Ctx c, Vector2 h, Vector2 t, float slant, float sEnd, int seed)
    {
        var pts = new List<Vector2> { h };
        float ang = slant, fs = Hash01(seed, 7, 2) * 50f;
        for (int k = 1; k < 60; k++)
        {
            var g = c.Grad(null, h.X, h.Y, true);
            var nt = new Vector2(-g.Y, g.X);
            t = nt.Dot(t) < 0 ? -nt : nt;
            ang += (0.5f * (2 * N2(k * Ds * 0.45f + fs, fs * 0.37f) - 1) - 0.4f * (ang - slant)) * Ds;
            h += (-g * Mathf.Cos(ang) + t * Mathf.Sin(ang)) * Ds;
            if (!Clear(c, h)) break;
            pts.Add(h);
            if (c.S(h.X, h.Y) < sEnd) break;
        }
        return pts;
    }

    // A root hanging down a path from the bank onto the floor: sunk where it starts, bridging the bank's foot in an arch
    // (lift metres more at its top), tapering out over the floor to a tip sunk into it.
    static void Hang(Ctx c, Buf b, List<Vector2> path, float r0, int sd, float fy, float id, float lift)
    {
        if (path.Count < 4) return;
        var (r, up, dn) = Profile(path.Count);
        float L = (path.Count - 1) * Ds;
        for (int k = 0; k < path.Count; k++)
        {
            float a = k * Ds, done = a / L, sv = c.S(path[k].X, path[k].Y);
            r[k] = r0 * Knots(a, sd) * Mathf.Lerp(1f, 0.3f, Sm(0.3f, 1f, done)) * (1 + 0.25f * (1 - Sm(0f, 1f, a)));
            dn[k] = 1.2f * (1 - Sm(0.1f, 0.9f, a)) + 1.3f * Sm(L - 0.7f, L, a);
            // the arch over the foot: lifted most where the bank meets the floor
            up[k] = lift * Sm(-1.2f, -0.3f, sv) * (1 - Sm(0.3f, 1.4f, sv));
        }
        Lay(c, b, path, r, up, dn, true, fy, id);
    }

    // Lays one root on the bank from its plan path: centred 0.55 of its radius over the surface (along its normal), lifted
    // up metres (world up), sunk dn of its radius (along the normal). With bridge, the centre line spans the concave
    // corners (the bank's foot) as a taut root does, with a dark hollow under it.
    static void Lay(Ctx c, Buf b, List<Vector2> h, List<float> r, List<float> up, List<float> dn, bool bridge, float floorY, float id)
    {
        int n = h.Count;
        if (n < 3) return;
        var P = new Vector3[n]; var N = new Vector3[n]; var S = new float[n]; var y = new float[n];
        for (int k = 0; k < n; k++)
        {
            S[k] = c.S(h[k].X, h[k].Y);
            N[k] = SurfN(c, h[k].X, h[k].Y);
            P[k] = new Vector3(h[k].X, SurfAt(c, h[k].X, h[k].Y), h[k].Y) + N[k] * (0.55f * r[k]);
            y[k] = P[k].Y;
        }
        // (a sag per step bounds the bridge's reach: it spans the foot's tight corner, never the far wall's long climb,
        // which a taut string turned into poles leaning out from its top; b9a)
        if (bridge)
            for (int it = 0; it < 150; it++)
                for (int k = 1; k < n - 1; k++) y[k] = Mathf.Max(P[k].Y, 0.5f * (y[k - 1] + y[k + 1]) - 0.03f);
        var pts = new List<Vector3>(n); var rs = new List<float>(n); var ss = new List<float>(n); var lie = new List<Vector3>(n); var pr = new List<float>(n);
        for (int k = 0; k < n; k++)
        {
            pts.Add(new Vector3(P[k].X, y[k] + up[k], P[k].Z) - N[k] * (dn[k] * r[k]));
            rs.Add(r[k]); ss.Add(S[k]); lie.Add(N[k]); pr.Add(1f);
        }
        for (int it = 0; it < 2; it++)
            for (int k = 1; k < n - 1; k++) pts[k] = pts[k] * 0.5f + (pts[k - 1] + pts[k + 1]) * 0.25f;
        float rm = 0; foreach (var v in r) rm = Mathf.Max(rm, v);
        Tube(b, pts, rs, ss, lie, pr, floorY, BankRootKind, id, rm >= 0.3f ? 12 : rm >= 0.16f ? 10 : 8);
    }
}
