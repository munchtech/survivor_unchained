using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Maps.Arenas;
using static SurvivorUnchained.View.Made;
using static SurvivorUnchained.View.Shapes;

namespace SurvivorUnchained.View;

/// <summary>
/// The Seventh Legion's hall (Maps/Arenas/Vault, Behind the Sealed Door), made in code to its plan:
/// its walls of ashlar laced with brick every fourth course, broken to the heights the centuries left
/// them; the piers between their bays and the dead in rows of niches in the bays; the door; the arch
/// of the stair's mouth in the north wall, its keystone cut with the seven-notch sigil, and the stair
/// going down under it toward the Morrow's light. And the fight's own pieces in it: the fallen roof
/// beams and opened sarcophagi it takes cover behind, and the Legion's standard.
/// Placed at the world's origin unturned, so its frame is the world's (its floor at y 0).
/// </summary>
public static partial class Pieces
{
    /// <summary>The ashlar's course (medieval_blocks_03: five to its 2.2 m), so the steps of a broken
    /// wall's top fall on its joints.</summary>
    const float Course = 0.44f;

    /// <summary>Every fourth course is brick, through the wall: the Legion's way of building.</summary>
    static bool BrickCourse(int k) => k % 4 == 3;

    sealed class HallKit
    {
        public readonly Build Stone = new(), Brick = new(), Core = new(), Turf = new(), Niche = new(), Urn = new(), Bone = new(),
            Step = new(), Sigil = new(), Haze = new();
    }

    static Vector3 V3(double x, double z, double y = 0) => new((float)x, (float)y, (float)z);

    static void Q(Build b, Vector3 p0, Vector3 p1, Vector3 p2, Vector3 p3, Vector3 n) => b.Quad(b.V(p0, n), b.V(p1, n), b.V(p2, n), b.V(p3, n));

    /// <summary>A six-faced block from its eight corners: one end's four in turn, then the other's in
    /// the same turn; each face shaded flat, facing out.</summary>
    static void Hex(Build b, Vector3[] v)
    {
        var c = Vector3.Zero;
        foreach (var p in v) c += p;
        c /= 8;
        void F(int i, int j, int k, int l)
        {
            var n = (v[k] - v[i]).Cross(v[j] - v[i]);
            n = n.LengthSquared() > 1e-12f ? n.Normalized() : Vector3.Up;
            if (n.Dot((v[i] + v[j] + v[k] + v[l]) / 4 - c) < 0) n = -n;
            Q(b, v[i], v[j], v[k], v[l], n);
        }
        F(0, 1, 2, 3); F(4, 5, 6, 7); F(0, 1, 5, 4); F(1, 2, 6, 5); F(2, 3, 7, 6); F(3, 0, 4, 7);
    }

    /// <summary>A box about c, its half-extents along three axes.</summary>
    static void Block(Build b, Vector3 c, Vector3 ax, Vector3 ay, Vector3 az) => Hex(b, new[]
    {
        c - ax - ay - az, c + ax - ay - az, c + ax - ay + az, c - ax - ay + az,
        c - ax + ay - az, c + ax + ay - az, c + ax + ay + az, c - ax + ay + az,
    });

    /// <summary>A wall's face from p (on the floor's level) along u for w, y0 to y1, facing n: ashlar,
    /// its brick courses brick.</summary>
    static void Coursed(HallKit k, Vector3 p, Vector3 u, float w, float y0, float y1, Vector3 n)
    {
        float y = y0;
        for (int guard = 0; y < y1 - 1e-4f && guard < 200; guard++)
        {
            bool Brick(float at) => at >= -1e-3f && BrickCourse(Mathf.FloorToInt(at / Course + 1e-3f));
            bool brick = Brick(y);
            float top = y;
            for (int g2 = 0; top < y1 - 1e-4f && Brick(top) == brick && g2 < 200; g2++)
                top = Mathf.Min(y1, top < -1e-3f ? 0 : (Mathf.FloorToInt(top / Course + 1e-3f) + 1) * Course);
            Q(brick ? k.Brick : k.Stone, p + Vector3.Up * y, p + u * w + Vector3.Up * y, p + u * w + Vector3.Up * top, p + Vector3.Up * top, n);
            y = top;
        }
    }

    /// <summary>A pier or any square mass on the floor: four coursed faces, its top the wall's core.</summary>
    static void Mass(HallKit k, Vector3 c, Vector3 u, Vector3 n, float hu, float hn, float h, float y0 = -0.3f)
    {
        Vector3 p0 = c - u * hu + n * hn, p1 = c + u * hu + n * hn, p2 = c + u * hu - n * hn, p3 = c - u * hu - n * hn;
        Coursed(k, p0, u, hu * 2, y0, h, n);
        Coursed(k, p1, -n, hn * 2, y0, h, u);
        Coursed(k, p2, -u, hu * 2, y0, h, -n);
        Coursed(k, p3, n, hn * 2, y0, h, -u);
        Q(k.Core, p0 + Vector3.Up * h, p1 + Vector3.Up * h, p2 + Vector3.Up * h, p3 + Vector3.Up * h, Vector3.Up);
    }

    static float H01(int a, int b) => Mathf.PosMod(Mathf.Sin(a * 12.9898f + b * 78.233f) * 43758.547f, 1f);

    static Node3D Hall()
    {
        var k = new HallKit();
        var rng = new RandomNumberGenerator { Seed = 7_0007 };
        var pierH = new Dictionary<int, float>();
        foreach (var r in Vault.Runs) HallRun(k, r, rng, pierH);
        for (int i = 0; i < Vault.Piers.Length; i++) HallPier(k, Vault.Piers[i], pierH.GetValueOrDefault(i, 4f), i);
        foreach (var (x, z, half, h) in Vault.Corners)
        {
            var c = V3(x, z);
            Mass(k, c, Vector3.Right, Vector3.Back, (float)half, (float)half, (float)h);
            Block(k.Stone, c + Vector3.Up * ((float)h + 0.12f), Vector3.Right * ((float)half + 0.14f), Vector3.Up * 0.12f, Vector3.Back * ((float)half + 0.14f));
        }
        StairMouth(k);
        Lintel(k);
        var haze = new StandardMaterial3D
        {
            ShadingMode = BaseMaterial3D.ShadingModeEnum.Unshaded, AlbedoTexture = Tex(Paint(4, 64, (u, v) =>
            {
                // The Morrow's light coming up the stair from far below: ember at the foot, gone by the arch.
                float t = Mathf.Pow(v, 2.2f);
                return new Color(0.9f * t, 0.32f * t, 0.1f * t);
            })),
        };
        return Hold((k.Stone.Mesh(true), Surface("medieval_blocks_03", 2.2f, "#7a7c80")),
            (k.Brick.Mesh(true), Surface("castle_brick_broken_06", 1.4f, "#9c8478")),
            (k.Core.Mesh(true), Surface("rabdentse_ruins_wall", 1.6f, "#b4aea4")),
            (k.Niche.Mesh(), Surface("rabdentse_ruins_wall", 0.9f, "#4a4640")),
            (k.Urn.Mesh(), Mat("#4e3022", 0, 0.75f)),
            (k.Bone.Mesh(), Mat("#a89c84", 0, 0.6f)),
            (k.Step.Mesh(true), Surface("sandstone_cracks", 1.6f, "#7e8288")),
            (k.Sigil.Mesh(), Glow("#8a5aff", 0.7f, "#2a1c40")),
            (k.Haze.Mesh(), haze));
    }

    /// <summary>A run of wall: its bays between piers cut into columns, each standing to its own
    /// height in courses, niches in rows in the bays, turf over its top in stretches.</summary>
    static void HallRun(HallKit k, Vault.Run r, RandomNumberGenerator rng, Dictionary<int, float> pierH)
    {
        var a = V3(r.Ax, r.Az);
        var e = V3(r.Bx, r.Bz);
        float L = a.DistanceTo(e), T = (float)Vault.Thick;
        var u = (e - a) / L;
        var n = V3(r.Nx, r.Nz);
        var o = -n;
        bool niches = r.Nz > -0.5;
        Vector3 At(float s, float d, float y) => a + u * s + o * d + Vector3.Up * y;
        float Stand(float s) => (float)Vault.Standing(r, s);

        // Its piers: their spans along it, and each one's height (above the wall by a few courses).
        var spans = new List<(float S0, float S1)>();
        for (int i = 0; i < Vault.Piers.Length; i++)
        {
            var p = Vault.Piers[i];
            if (Math.Abs(p.Nx - r.Nx) > 0.1 || Math.Abs(p.Nz - r.Nz) > 0.1) continue;
            var pc = V3(p.X, p.Z);
            float s = (pc - a).Dot(u), off = Mathf.Abs((pc - a).Dot(n));
            if (off > 0.05f || s < 0 || s > L) continue;
            spans.Add((s - (float)p.W / 2, s + (float)p.W / 2));
            pierH[i] = p.H > 0 ? (float)p.H : Stand(s) + Course * (2 + (int)(H01(r.Seed, i) * 2.99f));
        }
        spans.Sort();

        // The columns: niche, wall, niche... in a bay; plain wall elsewhere.
        var cols = new List<(float S0, float S1, bool Niche)>();
        void Plain(float b0, float b1)
        {
            int m = Math.Max(1, (int)Mathf.Round((b1 - b0) / 0.6f));
            for (int i = 0; i < m; i++) cols.Add((b0 + (b1 - b0) * i / m, b0 + (b1 - b0) * (i + 1) / m, false));
        }
        void Bay(float b0, float b1)
        {
            float len = b1 - b0;
            if (!niches || len < 2.2f) { Plain(b0, b1); return; }
            int m = (int)((len - 0.9f + 0.5f) / 1.05f);
            float total = m * 1.05f - 0.5f, at = b0 + (len - total) / 2;
            Plain(b0, at);
            for (int i = 0; i < m; i++)
            {
                cols.Add((at, at + 0.55f, true));
                if (i < m - 1) cols.Add((at + 0.55f, at + 1.05f, false));
                at += 1.05f;
            }
            Plain(at - 0.5f, b1);
        }
        float from = 0;
        foreach (var (s0, s1) in spans)
        {
            if (s0 > from + 0.05f) Bay(from, s0);
            from = Mathf.Max(from, s1);
        }
        if (from < L - 0.05f) Bay(from, L);

        // Each column's height: the run's broken line, a block knocked off its top here and there.
        var hs = cols.Select(c => (float)Vault.Top(r, (c.S0 + c.S1) / 2)).ToArray();

        float[] rows = { 0.55f, 2.15f, 3.75f, 5.35f };
        for (int i = 0; i < cols.Count; i++)
        {
            var (s0, s1, niche) = cols[i];
            float h = hs[i];
            // The inner face, holed by its niches.
            float y = -0.3f;
            if (niche)
                foreach (float r0 in rows)
                {
                    float r1 = r0 + 0.55f;
                    if (r1 + 0.5f > h) break;
                    Coursed(k, At(s0, 0, 0), u, s1 - s0, y, r0, n);
                    Niche(k, At, u, n, s0, s1, r0, r1, H01(r.Seed * 97 + i, (int)(r0 * 10)));
                    y = r1;
                }
            Coursed(k, At(s0, 0, 0), u, s1 - s0, y, h, n);
            // The outer face (the howe's earth stands against most of it).
            Coursed(k, At(s0, T, 0), u, s1 - s0, -0.3f, h, o);
            // The top: the wall's core of rubble in mortar, open to the sky.
            Q(k.Core, At(s0, 0, h), At(s1, 0, h), At(s1, T, h), At(s0, T, h), Vector3.Up);
            // Where its neighbour stands lower, the broken end shows.
            float hp = i > 0 && cols[i - 1].S1 >= s0 - 0.01f ? hs[i - 1] : -0.3f;
            float hn = i + 1 < cols.Count && cols[i + 1].S0 <= s1 + 0.01f ? hs[i + 1] : -0.3f;
            if (hp < h) Q(k.Core, At(s0, 0, hp), At(s0, T, hp), At(s0, T, h), At(s0, 0, h), -u);
            if (hn < h) Q(k.Core, At(s1, 0, hn), At(s1, T, hn), At(s1, T, h), At(s1, 0, h), u);
            // The core's rubble standing loose on the top, broken: a top is never a flat shelf.
            int lumps = 1 + (int)(H01(i, r.Seed) * 2.5f);
            for (int j = 0; j < lumps; j++)
                Lump(k.Core, At(s0 + (s1 - s0) * (0.2f + 0.6f * H01(i * 7 + j, 3)), 0.25f + (T - 0.5f) * H01(i * 5 + j, 4), h),
                    0.22f + 0.24f * H01(i * 3 + j, 5), rng);
        }
    }

    /// <summary>A niche: a recess in the wall's face, dark, and what the Legion laid in it: an urn of
    /// ashes, a skull, or nothing now.</summary>
    static void Niche(HallKit k, Func<float, float, float, Vector3> at, Vector3 u, Vector3 n, float s0, float s1, float y0, float y1, float roll)
    {
        const float D = 0.45f;
        Q(k.Niche, at(s0, D, y0), at(s1, D, y0), at(s1, D, y1), at(s0, D, y1), n);
        Q(k.Niche, at(s0, 0, y0), at(s0, D, y0), at(s0, D, y1), at(s0, 0, y1), u);
        Q(k.Niche, at(s1, 0, y0), at(s1, D, y0), at(s1, D, y1), at(s1, 0, y1), -u);
        Q(k.Niche, at(s0, 0, y1), at(s1, 0, y1), at(s1, D, y1), at(s0, D, y1), Vector3.Down);
        Q(k.Niche, at(s0, 0, y0), at(s1, 0, y0), at(s1, D, y0), at(s0, D, y0), Vector3.Up);
        var mid = at((s0 + s1) / 2, D * 0.55f, y0);
        if (roll < 0.5f)
            Lathe(k.Urn, Pts(0, 0, 0.08f, 0, 0.12f, 0.07f, 0.13f, 0.15f, 0.1f, 0.24f, 0.065f, 0.27f, 0.085f, 0.3f, 0, 0.3f), 10,
                new Transform3D(Basis.Identity.Scaled(Vector3.One * (0.85f + 0.3f * roll)), mid));
        else if (roll < 0.75f)
        {
            // A skull, looking out.
            Lathe(k.Bone, Pts(0, 0, 0.06f, 0.01f, 0.085f, 0.06f, 0.08f, 0.12f, 0.045f, 0.16f, 0, 0.17f), 9,
                new Transform3D(Basis.Identity.Scaled(new Vector3(0.9f, 0.85f, 1.1f)), mid + n * 0.04f));
        }
    }

    /// <summary>A pier standing out of its wall's face: coursed, capped where it kept its impost, its
    /// top broken in a step where it did not. The gate's piers carry the springing of the arch that
    /// crossed the hall, a few of its stones still reaching out.</summary>
    static void HallPier(HallKit k, Vault.Pier p, float h, int seed)
    {
        var n = V3(p.Nx, p.Nz);
        var u = new Vector3(-n.Z, 0, n.X);
        float T = (float)Vault.Thick, front = (float)p.Out, hw = (float)p.W / 2;
        var c = V3(p.X, p.Z) + n * (front - T - 0.05f) / 2;
        float hn = (front + T + 0.05f) / 2;
        Mass(k, c, u, n, hw, hn, h);
        bool gate = Math.Abs(p.Out - 0.75) < 0.01;
        bool kept = gate || p.H > 0 || H01(seed, 3) < 0.45f;
        if (kept) Block(k.Stone, c + Vector3.Up * (h + 0.11f), u * (hw + 0.1f), Vector3.Up * 0.11f, n * (hn + 0.1f));
        else Mass(k, c + u * hw * 0.45f - n * hn * 0.2f, u, n, hw * 0.55f, hn * 0.8f, h + Course, h);
        if (!gate) return;
        // The arch's springing: voussoirs from the impost, reaching up and in toward the other side.
        float R = Mathf.Abs((float)p.X) - front, cy = h + 0.22f, sx = Mathf.Sign((float)p.X);
        float zc = (float)p.Z, dz = hw * 0.75f;
        for (int i = 0; i < 4; i++)
        {
            float a0 = i * 0.058f, a1 = (i + 1) * 0.058f - 0.004f;
            // The last stone has slipped.
            float sag = i == 3 ? 0.06f : 0;
            Vector3 P(float ang, float rr, float z) => new(sx * rr * Mathf.Cos(ang), cy + rr * Mathf.Sin(ang) - sag, z);
            Hex(k.Stone, new[]
            {
                P(a0, R, zc - dz), P(a0, R + 0.8f, zc - dz), P(a1, R + 0.8f, zc - dz), P(a1, R, zc - dz),
                P(a0, R, zc + dz), P(a0, R + 0.8f, zc + dz), P(a1, R + 0.8f, zc + dz), P(a1, R, zc + dz),
            });
        }
    }

    /// <summary>The stair's mouth: its arch in the north wall, the keystone cut with the seven-notch
    /// sigil, the wall over it, and the stair going down under a barrel vault out of the moon into the
    /// light coming up from below.</summary>
    static void StairMouth(HallKit k)
    {
        float W = (float)Vault.StairHalf, zf = (float)Vault.NorthFace, T = (float)Vault.Thick, spring = 4.2f, ring = 0.75f;
        float zfront = zf + 0.35f, zback = zf - T, zend = zf - 10.4f;
        // The arch: thirteen voussoirs over the opening, the keystone standing proud.
        const int N = 13;
        for (int i = 0; i < N; i++)
        {
            float a0 = Mathf.Pi * i / N, a1 = Mathf.Pi * (i + 1) / N - 0.006f;
            float ro = W + ring + (i == N / 2 ? 0.18f : 0);
            Vector3 P(float ang, float rr, float z) => new(rr * Mathf.Cos(ang), spring + rr * Mathf.Sin(ang), z);
            Hex(k.Stone, new[]
            {
                P(a0, W, zfront), P(a0, ro, zfront), P(a1, ro, zfront), P(a1, W, zfront),
                P(a0, W, zback), P(a0, ro, zback), P(a1, ro, zback), P(a1, W, zback),
            });
        }
        // The sigil on the keystone's face: a ring, and seven notches cut into it (the binders' seven
        // keys), the Legion's mark; it keeps a little of the light the door woke with.
        var key = new Vector3(0, spring + W + ring * 0.5f + 0.05f, zfront + 0.012f);
        Tube(k.Sigil, Path(40, t => key + new Vector3(0.24f * Mathf.Cos(t * Mathf.Tau), 0.24f * Mathf.Sin(t * Mathf.Tau), 0), true), 0.016f, 5, true);
        for (int i = 0; i < 7; i++)
        {
            float a = Mathf.Pi / 2 + i * Mathf.Tau / 7;
            var d = new Vector3(Mathf.Cos(a), Mathf.Sin(a), 0);
            Tube(k.Sigil, new List<Vector3> { key + d * 0.13f, key + d * 0.31f }, 0.014f, 4);
        }
        // The wall over it, up to the north wall's broken line, in columns down to the arch's back.
        float top = 8.4f;
        for (float x0 = -W; x0 < W - 0.01f; x0 += 0.58f)
        {
            float x1 = Mathf.Min(W, x0 + 0.58f), far = Mathf.Max(Mathf.Abs(x0), Mathf.Abs(x1));
            float y0 = spring + Mathf.Sqrt(Mathf.Max(0, (W + ring) * (W + ring) - far * far)) - 0.05f;
            float h = top - (H01((int)(x0 * 10), 5) < 0.3f ? Course : 0) + (Mathf.Abs(x0) < 0.6f ? Course : 0);
            var c = new Vector3((x0 + x1) / 2, 0, zf - T / 2);
            Coursed(k, new Vector3(x0, 0, zf), Vector3.Right, x1 - x0, y0, h, Vector3.Back);
            Q(k.Core, new Vector3(x0, h, zf), new Vector3(x1, h, zf), new Vector3(x1, h, zback), new Vector3(x0, h, zback), Vector3.Up);
            Q(k.Core, new Vector3(x0, y0, zf), new Vector3(x1, y0, zf), new Vector3(x1, y0, zback), new Vector3(x0, y0, zback), Vector3.Down);
        }
        // The well's sides, and the barrel vault over the stair.
        foreach (int s in new[] { -1, 1 })
            Coursed(k, new Vector3(s * W, 0, zfront), Vector3.Forward, zfront - zend, -9.5f, spring, new Vector3(-s, 0, 0));
        const int VS = 14;
        for (int i = 0; i < VS; i++)
        {
            float a0 = Mathf.Pi * i / VS, a1 = Mathf.Pi * (i + 1) / VS;
            Vector3 P(float ang, float z) => new(W * Mathf.Cos(ang), spring + W * Mathf.Sin(ang), z);
            var nm = -new Vector3(Mathf.Cos((a0 + a1) / 2), Mathf.Sin((a0 + a1) / 2), 0);
            Q(k.Stone, P(a0, zback), P(a1, zback), P(a1, zend), P(a0, zend), nm);
            // Its back, under the howe's earth (seen only from far above).
            Vector3 O(float ang, float z) => new((W + ring) * Mathf.Cos(ang), spring + (W + ring) * Mathf.Sin(ang), z);
            Q(k.Core, O(a0, zback), O(a1, zback), O(a1, zend), O(a0, zend), -nm);
        }
        // The far end, where the stair goes on down out of sight.
        Q(k.Stone, new Vector3(-W - ring, -1f, zend), new Vector3(W + ring, -1f, zend), new Vector3(W + ring, spring, zend), new Vector3(-W - ring, spring, zend), Vector3.Back);
        // The stair: treads a long stride deep, worn, down to where the light comes from.
        float z = zf, y = 0;
        for (int i = 0; z > zend + 0.05f && i < 40; i++)
        {
            float z1 = z - 0.42f;
            Q(k.Step, new Vector3(-W, y, z), new Vector3(W, y, z), new Vector3(W, y, z1), new Vector3(-W, y, z1), Vector3.Up);
            Q(k.Step, new Vector3(-W, y - 0.25f, z1), new Vector3(W, y - 0.25f, z1), new Vector3(W, y, z1), new Vector3(-W, y, z1), Vector3.Back);
            z = z1;
            y -= 0.25f;
        }
        // Where it goes on down out of sight: the light it comes up in.
        k.Haze.Quad(k.Haze.V(new Vector3(-W, -9.5f, zend), Vector3.Back, new Vector2(0, 1)), k.Haze.V(new Vector3(W, -9.5f, zend), Vector3.Back, new Vector2(1, 1)),
            k.Haze.V(new Vector3(W, -1f, zend + 0.01f), Vector3.Back, new Vector2(1, 0)), k.Haze.V(new Vector3(-W, -1f, zend + 0.01f), Vector3.Back, new Vector2(0, 0)));
    }

    /// <summary>The door's lintel, one stone over its jambs: the way she came in, and will go out.</summary>
    static void Lintel(HallKit k)
    {
        float zf = (float)Vault.SouthFace, T = (float)Vault.Thick, w = (float)Vault.DoorHalf + 0.9f;
        Block(k.Stone, new Vector3(0, 4.15f, zf + (T - 0.25f) / 2), new Vector3(w, 0, 0), new Vector3(0, 0.3f, 0), new Vector3(0, 0, (T + 0.25f) / 2 + 0.02f));
    }

    /// <summary>A legionary's shield where it fell: the long curved scutum, its red gone to the brown of
    /// old blood, its bronze rim and boss green; lying on its face or its back, a little askew.</summary>
    static Node3D Scutum(int seed)
    {
        var face = new Build();
        var bronze = new Build();
        var rng = new RandomNumberGenerator { Seed = (ulong)(seed * 977 + 41) };
        const float H = 1.05f, Wd = 0.64f, R = 0.55f;
        float span = Wd / R, up = rng.Randf() < 0.5f ? 1 : -1;
        // The curve across its width: a section of a cylinder along its length (z).
        Vector3 P(float u, float v, float lift) =>
            new(R * Mathf.Sin(u) * (1 + lift), (R * (Mathf.Cos(u) - Mathf.Cos(span / 2)) * up + 0.04f) * (1 + lift), v);
        const int NU = 8;
        for (int i = 0; i < NU; i++)
        {
            float u0 = -span / 2 + span * i / NU, u1 = u0 + span / NU;
            var n = new Vector3(Mathf.Sin((u0 + u1) / 2), Mathf.Cos((u0 + u1) / 2) * up, 0);
            if (n.Y < 0) n = -n;
            Q(face, P(u0, -H / 2, 0), P(u1, -H / 2, 0), P(u1, H / 2, 0), P(u0, H / 2, 0), n);
        }
        // Its rim, and its boss.
        Tube(bronze, Path(NU, t => P(-span / 2 + span * t, -H / 2, 0.02f)), 0.02f, 4);
        Tube(bronze, Path(NU, t => P(-span / 2 + span * t, H / 2, 0.02f)), 0.02f, 4);
        Tube(bronze, new List<Vector3> { P(-span / 2, -H / 2, 0.02f), P(-span / 2, H / 2, 0.02f) }, 0.02f, 4);
        Tube(bronze, new List<Vector3> { P(span / 2, -H / 2, 0.02f), P(span / 2, H / 2, 0.02f) }, 0.02f, 4);
        if (up > 0) Lathe(bronze, Pts(0, 0, 0.12f, 0, 0.1f, 0.04f, 0.05f, 0.08f, 0, 0.09f), 10, new Transform3D(Basis.Identity, P(0, 0, 0.01f)));
        var root = Hold((face.Mesh(), Mat("#4a1c14", 0, 0.75f, true)), (bronze.Mesh(), Mat("#5e6c52", 0.55f, 0.5f)));
        root.Rotation = new Vector3(0.05f * (rng.Randf() - 0.5f), 0, 0.08f * (rng.Randf() - 0.5f));
        var holder = new Node3D();
        holder.AddChild(root);
        return holder;
    }

    /// <summary>Stones of the walls and the arches come down: a few blocks tumbled together, broken
    /// rubble round them. Lies where nobody fights (the corners, the gates' piers' feet).</summary>
    static Node3D Tumble(int seed)
    {
        var stone = new Build();
        var core = new Build();
        var rng = new RandomNumberGenerator { Seed = (ulong)(seed * 613 + 29) };
        int n = 3 + (int)(rng.Randi() % 3);
        for (int i = 0; i < n; i++)
        {
            float a = rng.Randf() * Mathf.Tau, r = 0.3f + 0.9f * rng.Randf();
            var b = new Basis(Vector3.Up, rng.Randf() * Mathf.Tau) * new Basis(Vector3.Right, (rng.Randf() - 0.5f) * 0.5f) * new Basis(Vector3.Back, (rng.Randf() - 0.5f) * 0.4f);
            var c = new Vector3(Mathf.Cos(a) * r, 0.18f + 0.1f * rng.Randf() + (i == n - 1 ? 0.3f : 0), Mathf.Sin(a) * r);
            Block(stone, c, b.X * (0.38f + 0.12f * rng.Randf()), b.Y * 0.22f, b.Z * (0.26f + 0.08f * rng.Randf()));
        }
        for (int i = 0; i < 10; i++)
        {
            float a = rng.Randf() * Mathf.Tau, r = 0.4f + 1.2f * rng.Randf();
            Lump(core, new Vector3(Mathf.Cos(a) * r, 0.02f, Mathf.Sin(a) * r), 0.15f + 0.2f * rng.Randf(), rng);
        }
        return Hold((stone.Mesh(true), Surface("rock_boulder_dry", 1.2f, "#6c6e72")), (core.Mesh(true), Surface("rabdentse_ruins_wall", 1.2f, "#a49e94")));
    }

    /* ---------------------------------------------------------- the fight's pieces -- */

    /// <summary>A fallen roof beam, as the fight's cover (4 m by 1.4, lying across the hall): the great
    /// tie-beam black with age, split at its end, a rafter come down across it, iron straps rusted on
    /// them and the roof's tiles broken round them. Under a metre high.</summary>
    static Node3D FallenBeam(int seed)
    {
        var wood = new Build();
        var iron = new Build();
        var tile = new Build();
        var rng = new RandomNumberGenerator { Seed = (ulong)(seed * 7717 + 3) };
        float s = seed % 2 == 0 ? 1 : -1;
        Beam(wood, new Vector3(-2.1f * s, 0.27f, -0.28f), new Vector3(2.15f * s, 0.3f, -0.22f), 0.6f);
        // The rafter across it, its foot on the floor, its head on the beam.
        Beam(wood, new Vector3(-1.5f * s, 0.18f, 0.42f), new Vector3(1.6f * s, 0.62f, 0.15f), 0.4f, 0.36f);
        // The beam's end split along its grain.
        for (int i = 0; i < 5; i++)
        {
            var at = new Vector3(2.12f * s, 0.12f + 0.32f * rng.Randf(), -0.5f + 0.5f * rng.Randf());
            Tube(wood, new List<Vector3> { at, at + new Vector3((0.25f + 0.35f * rng.Randf()) * s, 0.05f * rng.Randf(), (rng.Randf() - 0.5f) * 0.15f) }, t => 0.06f * (1 - t) + 0.01f, 4);
        }
        // Its straps.
        foreach (float x in new[] { -1.2f, 0.9f })
            Beam(iron, new Vector3(x * s, 0.27f, -0.25f) - Vector3.Right * 0.04f, new Vector3(x * s, 0.27f, -0.25f) + Vector3.Right * 0.04f, 0.64f, 0.64f);
        // Broken tiles round it and on it.
        for (int i = 0; i < 34; i++)
        {
            // Heaped against the beams' sides, a few on them.
            float x = (rng.Randf() - 0.5f) * 4.2f, side = rng.Randf() < 0.5f ? -1 : 1;
            float z = -0.25f + side * (0.36f + 0.45f * rng.Randf() * rng.Randf());
            bool on = rng.Randf() < 0.15f;
            if (on) z = -0.25f + (rng.Randf() - 0.5f) * 0.4f;
            float y = on ? 0.58f : 0.02f + 0.08f * (1 - Mathf.Abs(Mathf.Abs(z + 0.25f) - 0.36f) / 0.45f);
            var b = new Basis(Vector3.Up, rng.Randf() * Mathf.Tau) * new Basis(Vector3.Right, (rng.Randf() - 0.5f) * 0.5f);
            Block(tile, new Vector3(x, y + 0.02f, z), b.X * (0.08f + 0.08f * rng.Randf()), b.Y * 0.018f, b.Z * (0.07f + 0.06f * rng.Randf()));
        }
        return Hold((wood.Mesh(true), Surface("rough_wood", 1.1f, "#5e544a")), (iron.Mesh(), Mat("#2e2420", 0.6f, 0.7f)), (tile.Mesh(), Mat("#5a2e22", 0, 0.85f)));
    }

    /// <summary>A legionary's sarcophagus, as the fight's cover (2.6 m by 1.2): a limestone chest on
    /// its plinth, a panel for the name and a wreath either side of it, the gabled lid pushed half off
    /// from inside, one end down on the floor. Empty: he is up.</summary>
    static Node3D Sarcophagus(int seed)
    {
        var stone = new Build();
        var dark = new Build();
        float s = seed % 2 == 0 ? 1 : -1;
        const float L = 1.12f, Wd = 0.46f, H = 0.86f, t = 0.1f;
        // The plinth.
        Block(stone, new Vector3(0, 0.07f, 0), new Vector3(L + 0.07f, 0, 0), new Vector3(0, 0.07f, 0), new Vector3(0, 0, Wd + 0.07f));
        // The chest's four sides, hollow, and its floor inside, dark.
        Block(stone, new Vector3(0, 0.14f + H / 2, Wd - t / 2), new Vector3(L, 0, 0), new Vector3(0, H / 2, 0), new Vector3(0, 0, t / 2));
        Block(stone, new Vector3(0, 0.14f + H / 2, -Wd + t / 2), new Vector3(L, 0, 0), new Vector3(0, H / 2, 0), new Vector3(0, 0, t / 2));
        Block(stone, new Vector3(L - t / 2, 0.14f + H / 2, 0), new Vector3(t / 2, 0, 0), new Vector3(0, H / 2, 0), new Vector3(0, 0, Wd - t));
        Block(stone, new Vector3(-L + t / 2, 0.14f + H / 2, 0), new Vector3(t / 2, 0, 0), new Vector3(0, H / 2, 0), new Vector3(0, 0, Wd - t));
        Q(dark, new Vector3(-L + t, 0.3f, -Wd + t), new Vector3(L - t, 0.3f, -Wd + t), new Vector3(L - t, 0.3f, Wd - t), new Vector3(-L + t, 0.3f, Wd - t), Vector3.Up);
        // The panel and the wreaths, on both long sides.
        foreach (float side in new[] { -1f, 1f })
        {
            float zf = side * (Wd + 0.012f);
            Block(stone, new Vector3(0, 0.6f, zf), new Vector3(0.42f, 0, 0), new Vector3(0, 0.2f, 0), new Vector3(0, 0, 0.014f));
            foreach (float ex in new[] { -1f, 1f })
                Hex(stone, new[]
                {
                    new Vector3(ex * 0.42f, 0.5f, zf - 0.012f), new Vector3(ex * 0.42f, 0.7f, zf - 0.012f), new Vector3(ex * 0.53f, 0.66f, zf - 0.012f), new Vector3(ex * 0.53f, 0.54f, zf - 0.012f),
                    new Vector3(ex * 0.42f, 0.5f, zf + 0.012f), new Vector3(ex * 0.42f, 0.7f, zf + 0.012f), new Vector3(ex * 0.53f, 0.66f, zf + 0.012f), new Vector3(ex * 0.53f, 0.54f, zf + 0.012f),
                });
            foreach (float wx in new[] { -0.8f, 0.8f })
                Tube(stone, Path(18, a => new Vector3(wx + 0.13f * Mathf.Cos(a * Mathf.Tau), 0.6f + 0.13f * Mathf.Sin(a * Mathf.Tau), zf + side * 0.01f), true), 0.028f, 5, true);
        }
        // The lid, pushed off askew from inside: gabled, its corners raised, one end on the floor.
        var lid = new Build();
        const float LL = 1.2f, LW = 0.53f;
        Block(lid, new Vector3(0, 0.07f, 0), new Vector3(LL, 0, 0), new Vector3(0, 0.07f, 0), new Vector3(0, 0, LW));
        Hex(lid, new[]
        {
            new Vector3(-LL, 0.14f, -LW), new Vector3(-LL, 0.14f, LW), new Vector3(-LL, 0.34f, 0.05f), new Vector3(-LL, 0.34f, -0.05f),
            new Vector3(LL, 0.14f, -LW), new Vector3(LL, 0.14f, LW), new Vector3(LL, 0.34f, 0.05f), new Vector3(LL, 0.34f, -0.05f),
        });
        foreach (float ex in new[] { -1f, 1f })
            foreach (float ez in new[] { -1f, 1f })
                Block(lid, new Vector3(ex * (LL - 0.1f), 0.24f, ez * (LW - 0.1f)), new Vector3(0.1f, 0, 0), new Vector3(0, 0.1f, 0), new Vector3(0, 0, 0.1f));
        var lidAt = new Transform3D(new Basis(Vector3.Up, 0.2f * s) * new Basis(Vector3.Back, -0.3f * s), new Vector3(0.62f * s, 0.62f, -0.12f * s));
        stone.Append(lid, lidAt);
        return Hold((stone.Mesh(true), Surface("rock_boulder_dry", 1.1f, "#74726c")), (dark.Mesh(), Mat("#141210", 0, 0.95f)));
    }

    /// <summary>The Legion's standard, planted: a pole a man and a half high, the spear's head on top,
    /// its discs down the pole and the crescent under them, and from the crossbar the rag that was red
    /// once with VII on it; a cairn of stones at its foot. Its rag faces the camera.</summary>
    static Node3D Standard(int seed)
    {
        var wood = new Build();
        var bronze = new Build();
        var rag = new Build();
        var paint = new Build();
        var stone = new Build();
        var rng = new RandomNumberGenerator { Seed = (ulong)(seed * 131 + 17) };
        const float Top = 3.05f, Bar = 2.62f;
        Tube(wood, new List<Vector3> { new(0, -0.1f, 0), new(0, Top, 0) }, 0.04f, 7);
        Lathe(bronze, Pts(0, 0, 0.05f, 0.02f, 0.06f, 0.1f, 0.0f, 0.36f), 6, new Transform3D(Basis.Identity, new Vector3(0, Top, 0)));
        // The wreath under the point, and the crossbar with its finials.
        Tube(bronze, Path(16, a => new Vector3(0.12f * Mathf.Cos(a * Mathf.Tau), Top - 0.12f, 0.12f * Mathf.Sin(a * Mathf.Tau)), true), 0.02f, 5, true);
        Tube(wood, new List<Vector3> { new(-0.44f, Bar, 0.05f), new(0.44f, Bar, 0.05f) }, 0.024f, 6);
        foreach (float x in new[] { -0.46f, 0.46f }) Lathe(bronze, Pts(0, -0.04f, 0.04f, 0, 0, 0.04f), 6, new Transform3D(Basis.Identity, new Vector3(x, Bar, 0.05f)));
        // The discs, and the crescent.
        for (int i = 0; i < 4; i++)
            Lathe(bronze, Pts(0, 0, 0.115f, 0, 0.12f, 0.018f, 0.06f, 0.04f, 0, 0.042f), 14,
                new Transform3D(new Basis(Vector3.Right, Mathf.Pi / 2), new Vector3(0, 1.48f + i * 0.24f, 0.04f)));
        Extrude(bronze, Crescent(0.16f, 0.12f, 0.08f), 0.02f, 0, new Transform3D(Basis.Identity, new Vector3(0, 1.18f, 0.045f)));
        // The rag: hanging from the bar, tattered at its foot, a little stir in it.
        var outline = new List<Vector2> { new(-0.4f, 0), new(0.4f, 0) };
        for (int i = 8; i >= 0; i--)
        {
            float x = -0.4f + 0.8f * i / 8;
            outline.Add(new Vector2(x, -0.72f - 0.14f * rng.Randf() + (i % 2 == 0 ? 0.06f : 0)));
        }
        var ragAt = new Vector3(0, Bar - 0.03f, 0.08f);
        Sheet(rag, null, outline.Select(p => new Vector2(p.X, p.Y)).ToArray(), 0.05f, 0,
            p => ragAt + new Vector3(p.X, p.Y, 0.025f * Mathf.Sin(p.X * 7 + seed) * (-p.Y) + 0.04f * p.Y * p.Y));
        // VII, in what is left of the gilt.
        void Stroke(Vector2 a, Vector2 b)
        {
            foreach (float zs in new[] { 1f, -1f })
            {
                var pa = ragAt + new Vector3(a.X, a.Y, 0.025f * Mathf.Sin(a.X * 7 + seed) * (-a.Y) + 0.04f * a.Y * a.Y + zs * 0.006f);
                var pb = ragAt + new Vector3(b.X, b.Y, 0.025f * Mathf.Sin(b.X * 7 + seed) * (-b.Y) + 0.04f * b.Y * b.Y + zs * 0.006f);
                Tube(paint, new List<Vector3> { pa, pb }, 0.016f, 4);
            }
        }
        Stroke(new(-0.27f, -0.2f), new(-0.17f, -0.5f)); Stroke(new(-0.17f, -0.5f), new(-0.07f, -0.2f));
        Stroke(new(0.07f, -0.2f), new(0.07f, -0.5f)); Stroke(new(0.2f, -0.2f), new(0.2f, -0.5f));
        // The cairn it is planted in.
        for (int i = 0; i < 7; i++)
        {
            float a = i * Mathf.Tau / 7 + rng.Randf() * 0.4f, r = 0.22f + 0.12f * rng.Randf();
            Lump(stone, new Vector3(Mathf.Cos(a) * r, 0.04f, Mathf.Sin(a) * r), 0.22f + 0.1f * rng.Randf(), rng);
        }
        return Hold((wood.Mesh(), Mat("#2e2420", 0, 0.8f)), (bronze.Mesh(), Mat("#5e6c52", 0.55f, 0.45f)),
            (rag.Mesh(), Cloth("#5e1812", true, 3)), (paint.Mesh(), Mat("#a08656", 0.3f, 0.6f)), (stone.Mesh(), Surface("rock_boulder_dry", 0.8f, "#6c6a64")));
    }
}
