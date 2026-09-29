using System;
using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// Beasts, modelled and animated in code (the web game's render/creatures.ts).
///
/// The character packs have people and the dead, but no wolves, no boars and
/// no lamplings, and those are what the Thornhollow quests are about. So they
/// are built here, in a chunky faceted style:
///
///   - bodies are LOFTED: a handful of polygonal cross-sections along the
///     spine, skinned between two spine bones so the back flexes in a gallop;
///   - heads, jaws, legs, tails and ears are their own segments on their own
///     bones; fur is a ruff of little pyramids, because fur in low poly is a
///     silhouette, not a texture;
///   - colour is per face (flat, like painted palette blocks), graded from a
///     dark back to a pale belly;
///   - animation is a pose function per clip, sampled over its cycle: a
///     gallop is a phase offset per leg, not a mocap file.
///
/// What comes out is geometry (triangles, each vertex on one bone or blended
/// between two), bones, and clips; Vat bakes it into a crowd as it does the
/// people. Shapes are built as the web game builds them (three.js's winding:
/// counter-clockwise from outside) and turned for Godot when baked.
/// </summary>
public sealed class Creature
{
    public sealed class Bone
    {
        public required string Name;
        public int Parent = -1;
        public Vector3 Rest, RestWorld;
    }

    /// <summary>A bone's offset from rest: rotation (Euler XYZ, radians) and position.</summary>
    public readonly record struct BonePose(Vector3 R, Vector3 P);

    public sealed record Clip(double Duration, Func<double, Dictionary<string, BonePose>> Pose);

    /// <summary>Triangles (three vertices each), in model space, with a
    /// colour per vertex (linear), and each vertex on bone A, or blended
    /// toward bone B by W.</summary>
    public sealed class Part
    {
        public readonly List<Vector3> Pos = new();
        public readonly List<Color> Col = new();
        public readonly List<int> A = new(), B = new();
        public readonly List<float> W = new();
        public int Count => Pos.Count;
    }

    public readonly List<Bone> Bones = new();
    readonly Dictionary<string, int> byName = new();
    public readonly Part Body = new(), Glow = new();
    public Color GlowColor = Colors.Black;
    public readonly Dictionary<string, Clip> Clips = new();

    /* ------------------------------------------------------------ building -- */

    void AddBone(string name, string? parent, float x, float y, float z)
    {
        var b = new Bone { Name = name, Rest = new Vector3(x, y, z) };
        if (parent != null) { b.Parent = byName[parent]; b.RestWorld = Bones[b.Parent].RestWorld + b.Rest; }
        else b.RestWorld = b.Rest;
        byName[name] = Bones.Count;
        Bones.Add(b);
    }

    Vector3 BoneWorld(string name) => Bones[byName[name]].RestWorld;

    /// <summary>Skinned between two bones along an axis (0 x, 1 y, 2 z), from one value to another.</summary>
    sealed record Blend(string A, string B, int Axis, float From, float To);

    void Add(List<Vector3> tris, string bone, Func<Vector3, Vector3, Color> color, bool glow = false) => Add(tris, (object)bone, color, glow);
    void Add(List<Vector3> tris, Blend bone, Func<Vector3, Vector3, Color> color, bool glow = false) => Add(tris, (object)bone, color, glow);

    void Add(List<Vector3> tris, object bone, Func<Vector3, Vector3, Color> color, bool glow)
    {
        var part = glow ? Glow : Body;
        for (int f = 0; f < tris.Count; f += 3)
        {
            Vector3 a = tris[f], b = tris[f + 1], c = tris[f + 2];
            var n = (c - b).Cross(a - b).Normalized();
            var col = color((a + b + c) / 3, n);
            for (int k = 0; k < 3; k++)
            {
                var v = tris[f + k];
                part.Pos.Add(v);
                part.Col.Add(col);
                if (bone is string s) { part.A.Add(byName[s]); part.B.Add(-1); part.W.Add(0); }
                else
                {
                    var bl = (Blend)bone;
                    float t = Mathf.Clamp((v[bl.Axis] - bl.From) / (bl.To - bl.From), 0, 1);
                    part.A.Add(byName[bl.A]); part.B.Add(byName[bl.B]); part.W.Add(t * t * (3 - 2 * t));
                }
            }
        }
    }

    void AddClip(string name, double duration, Func<double, Dictionary<string, BonePose>> pose) => Clips[name] = new Clip(duration, pose);

    /* -------------------------------------------------------------- posing -- */

    /// <summary>Where every bone is (model space) in a clip at t seconds, and
    /// the matrix that takes a vertex from rest to there.</summary>
    public Transform3D[] Skinning(string clip, double t)
    {
        var c = Clips[clip];
        var pose = c.Pose(Math.Clamp(t / c.Duration, 0, 1));
        var world = new Transform3D[Bones.Count];
        var skin = new Transform3D[Bones.Count];
        for (int i = 0; i < Bones.Count; i++)
        {
            var b = Bones[i];
            pose.TryGetValue(b.Name, out var p);
            // Euler XYZ as three.js composes it: X, then Y, then Z, as matrices Rx·Ry·Rz.
            var basis = new Basis(Vector3.Right, p.R.X) * new Basis(Vector3.Up, p.R.Y) * new Basis(new Vector3(0, 0, 1), p.R.Z);
            var local = new Transform3D(basis, b.Rest + p.P);
            world[i] = b.Parent >= 0 ? world[b.Parent] * local : local;
            skin[i] = world[i] * new Transform3D(Basis.Identity, -b.RestWorld);
        }
        return skin;
    }

    /// <summary>A part's vertices, posed.</summary>
    public static void Pose(Part part, Transform3D[] skin, Span<Vector3> into)
    {
        for (int i = 0; i < part.Count; i++)
        {
            var v = part.Pos[i];
            var p = skin[part.A[i]] * v;
            if (part.B[i] >= 0) p = p.Lerp(skin[part.B[i]] * v, part.W[i]);
            into[i] = p;
        }
    }

    /* -------------------------------------------------------------- shapes -- */

    readonly record struct Ring(float Z, float Y, float W, float H, float X = 0);

    /// <summary>A loft: polygonal rings along +z, capped both ends.</summary>
    static List<Vector3> Loft(Ring[] rings, int sides = 7, float jitter = 0, Random? rng = null)
    {
        var pos = new List<Vector3>();
        var ring = new List<Vector3[]>();
        foreach (var r in rings)
        {
            var pts = new Vector3[sides];
            for (int i = 0; i < sides; i++)
            {
                float a = (float)i / sides * Mathf.Tau + Mathf.Pi / sides;
                float j = jitter > 0 && rng != null ? 1 + ((float)rng.NextDouble() - 0.5f) * jitter : 1;
                pts[i] = new Vector3(r.X + Mathf.Cos(a) * r.W * j, r.Y + Mathf.Sin(a) * r.H * j, r.Z);
            }
            ring.Add(pts);
        }
        void Tri(Vector3 a, Vector3 b, Vector3 c) { pos.Add(a); pos.Add(b); pos.Add(c); }
        for (int k = 0; k < ring.Count - 1; k++)
        {
            var A = ring[k]; var B = ring[k + 1];
            for (int i = 0; i < sides; i++)
            {
                int i2 = (i + 1) % sides;
                Tri(A[i], A[i2], B[i]);
                Tri(A[i2], B[i2], B[i]);
            }
        }
        void Cap(Vector3[] R, bool flip)
        {
            var c = Vector3.Zero;
            foreach (var p in R) c += p;
            c /= R.Length;
            for (int i = 0; i < sides; i++)
            {
                int i2 = (i + 1) % sides;
                if (flip) Tri(c, R[i2], R[i]); else Tri(c, R[i], R[i2]);
            }
        }
        Cap(ring[0], true);
        Cap(ring[^1], false);
        return pos;
    }

    /// <summary>A tapered cylinder along +Y, radius r0 at 0 and r1 at len
    /// (r1 = 0: a cone), turned to point along `dir` and moved to `at`.</summary>
    static List<Vector3> Cylinder(Vector3 at, Vector3 dir, float len, float r0, float r1, int sides)
    {
        var pos = new List<Vector3>();
        var q = Turn(dir);
        Vector3 P(float r, float y, int i) { float a = (float)i / sides * Mathf.Tau; return at + q * new Vector3(r * Mathf.Sin(a), y, r * Mathf.Cos(a)); }
        void Tri(Vector3 a, Vector3 b, Vector3 c) { pos.Add(a); pos.Add(b); pos.Add(c); }
        var bottom = at;
        var top = at + q * new Vector3(0, len, 0);
        for (int i = 0; i < sides; i++)
        {
            int j = i + 1;
            Vector3 bi = P(r0, 0, i), bj = P(r0, 0, j), ti = P(r1, len, i), tj = P(r1, len, j);
            Tri(bi, bj, ti);
            if (r1 > 0) Tri(bj, tj, ti);
            Tri(bottom, bj, bi);
            if (r1 > 0) Tri(top, ti, tj);
        }
        return pos;
    }

    static Quaternion Turn(Vector3 dir)
    {
        dir = dir.Normalized();
        if (dir.Dot(Vector3.Up) > 0.9999f) return Quaternion.Identity;
        if (dir.Dot(Vector3.Up) < -0.9999f) return new Quaternion(Vector3.Right, Mathf.Pi);
        return new Quaternion(Vector3.Up, dir);
    }

    /// <summary>A tapered limb from a to b.</summary>
    static List<Vector3> Limb(Vector3 a, Vector3 b, float r0, float r1, int sides = 5) => Cylinder(a, b - a, a.DistanceTo(b), r0, r1, sides);

    static List<Vector3> Cone(Vector3 at, Vector3 dir, float r, float h, int sides = 4) => Cylinder(at, dir, h, r, 0, sides);

    static readonly Vector3[] IcoV;
    static readonly int[] IcoF =
    {
        0, 11, 5, 0, 5, 1, 0, 1, 7, 0, 7, 10, 0, 10, 11, 1, 5, 9, 5, 11, 4, 11, 10, 2, 10, 7, 6, 7, 1, 8,
        3, 9, 4, 3, 4, 2, 3, 2, 6, 3, 6, 8, 3, 8, 9, 4, 9, 5, 2, 4, 11, 6, 2, 10, 8, 6, 7, 9, 8, 1,
    };

    static Creature()
    {
        float t = (1 + Mathf.Sqrt(5)) / 2;
        float[] v = { -1, t, 0, 1, t, 0, -1, -t, 0, 1, -t, 0, 0, -1, t, 0, 1, t, 0, -1, -t, 0, 1, -t, t, 0, -1, t, 0, 1, -t, 0, -1, -t, 0, 1 };
        IcoV = new Vector3[12];
        for (int i = 0; i < 12; i++) IcoV[i] = new Vector3(v[i * 3], v[i * 3 + 1], v[i * 3 + 2]).Normalized();
    }

    /// <summary>A lump: an icosahedron (once subdivided at detail 1), squashed and moved.</summary>
    static List<Vector3> Blob(Vector3 at, float r, float sx = 1, float sy = 1, float sz = 1, int detail = 0)
    {
        var tris = new List<Vector3>();
        for (int f = 0; f < IcoF.Length; f += 3)
        {
            Vector3 a = IcoV[IcoF[f]], b = IcoV[IcoF[f + 1]], c = IcoV[IcoF[f + 2]];
            if (detail == 0) { tris.Add(a); tris.Add(b); tris.Add(c); continue; }
            Vector3 ab = ((a + b) / 2).Normalized(), bc = ((b + c) / 2).Normalized(), ca = ((c + a) / 2).Normalized();
            tris.AddRange(new[] { a, ab, ca, ab, b, bc, ca, bc, c, ab, bc, ca });
        }
        var s = new Vector3(sx, sy, sz) * r;
        for (int i = 0; i < tris.Count; i++) tris[i] = at + tris[i] * s;
        return tris;
    }

    /* ------------------------------------------------------------- colour -- */

    static Color C(string hex) => new Color(hex).SrgbToLinear();
    static Color Mul(Color c, float k) => new(c.R * k, c.G * k, c.B * k);
    /// <summary>A small change of lightness (three.js's offsetHSL, near enough for these greys).</summary>
    static Color Lighter(Color c, float d) => new(Mathf.Max(0, c.R + d), Mathf.Max(0, c.G + d), Mathf.Max(0, c.B + d));
    static float Smooth(float x, float lo, float hi) { float t = Mathf.Clamp((x - lo) / (hi - lo), 0, 1); return t * t * (3 - 2 * t); }
    static Vector3 V(float x, float y, float z) => new(x, y, z);

    static BonePose Rot(double x, double y = 0, double z = 0) => new(V((float)x, (float)y, (float)z), Vector3.Zero);
    static BonePose At(double x, double y, double z) => new(Vector3.Zero, V((float)x, (float)y, (float)z));
    static BonePose Both(double rx, double ry, double rz, double px, double py, double pz) => new(V((float)rx, (float)ry, (float)rz), V((float)px, (float)py, (float)pz));

    /* -------------------------------------------------------------- wolves -- */

    public sealed record WolfLook(string Back, string Belly, string Muzzle, string Nose, string Eye, bool GlowEyes = false, float Ruff = 1, bool Sick = false);

    public static readonly Dictionary<string, WolfLook> WolfLooks = new()
    {
        ["wolf"] = new("#6b6a70", "#b9b3a4", "#d4cdbb", "#141416", "#e8c060"),
        ["wolf_alpha"] = new("#2e2d31", "#8d8a84", "#d9d4c8", "#0e0e10", "#ffd070", true, 1.5f),
        ["wolf_blighted"] = new("#3a3b33", "#6d6e58", "#8a8b70", "#161612", "#9dff6a", true, 1.1f, true),
        ["wolf_spirit"] = new("#a8c8ff", "#e8f4ff", "#ffffff", "#6a8ccc", "#ffffff", true, 1.2f),
    };

    public static Creature Wolf(WolfLook look, int seed)
    {
        var rng = new Random(seed);
        var B = new Creature();
        B.AddBone("root", null, 0, 0, 0);
        B.AddBone("hips", "root", 0, 0.62f, -0.32f);
        B.AddBone("chest", "hips", 0, 0.04f, 0.5f);
        B.AddBone("neck", "chest", 0, 0.12f, 0.2f);
        B.AddBone("head", "neck", 0, 0.14f, 0.14f);
        B.AddBone("jaw", "head", 0, -0.08f, 0.1f);
        B.AddBone("tail", "hips", 0, 0.06f, -0.2f);
        B.AddBone("tail2", "tail", 0, -0.05f, -0.24f);
        foreach (var (side, sx) in new[] { ("L", 1f), ("R", -1f) })
        {
            B.AddBone($"fu{side}", "chest", 0.15f * sx, -0.05f, 0.08f);
            B.AddBone($"fl{side}", $"fu{side}", 0, -0.28f, 0.02f);
            B.AddBone($"bu{side}", "hips", 0.15f * sx, -0.02f, -0.08f);
            B.AddBone($"bl{side}", $"bu{side}", 0, -0.3f, -0.04f);
        }

        Color back = C(look.Back), belly = C(look.Belly), muzzle = C(look.Muzzle), nose = C(look.Nose), sick = C("#7a8a3a");
        Color Shade(Vector3 c, Vector3 n)
        {
            // Dark along the back, pale underneath, with a little per-facet noise.
            float up = n.Y * 0.5f + 0.5f;
            float k = Smooth(c.Y, 0.45f, 0.75f) * 0.6f + up * 0.4f;
            var col = Lighter(belly.Lerp(back, k), Mathf.Sin(c.X * 41 + c.Z * 23 + c.Y * 17) * 0.5f * 0.04f);
            if (look.Sick && Mathf.Sin(c.X * 30 + c.Z * 12) > 0.75f) col = col.Lerp(sick, 0.6f);
            return col;
        }

        // Torso: rump to chest, deep chest, tucked waist.
        B.Add(Loft(new Ring[]
        {
            new(-0.62f, 0.64f, 0.1f, 0.1f), new(-0.5f, 0.66f, 0.2f, 0.18f), new(-0.22f, 0.64f, 0.21f, 0.17f), new(0.02f, 0.64f, 0.2f, 0.17f),
            new(0.2f, 0.63f, 0.24f, 0.24f), new(0.36f, 0.66f, 0.22f, 0.23f), new(0.46f, 0.72f, 0.14f, 0.14f),
        }, 7, 0.1f, rng), new Blend("hips", "chest", 2, -0.2f, 0.2f), Shade);

        // Neck ruff: fur in low poly is a silhouette.
        int ruffN = (int)Math.Round(9 * look.Ruff);
        for (int i = 0; i < ruffN; i++)
        {
            float a = (float)i / ruffN * Mathf.Tau;
            B.Add(Cone(V(Mathf.Cos(a) * 0.17f, 0.78f + Mathf.Sin(a) * 0.15f, 0.42f), V(Mathf.Cos(a), Mathf.Sin(a) + 0.2f, -0.9f), 0.07f, 0.2f + (float)rng.NextDouble() * 0.08f, 3),
                "neck", (c, n) => Mul(Shade(c, n), 0.92f));
        }

        // Neck and head.
        B.Add(Loft(new Ring[] { new(0.4f, 0.76f, 0.13f, 0.14f), new(0.56f, 0.86f, 0.11f, 0.12f) }, 6), "neck", Shade);
        Color HeadShade(Vector3 c, Vector3 n) => c.Z > 0.88f ? muzzle.Lerp(belly, 0.2f) : Shade(c, n).Lerp(muzzle, c.Y < 0.88f ? 0.35f : 0);
        B.Add(Loft(new Ring[] { new(0.56f, 0.92f, 0.14f, 0.13f), new(0.7f, 0.93f, 0.15f, 0.12f), new(0.82f, 0.9f, 0.1f, 0.08f), new(1.0f, 0.88f, 0.06f, 0.05f) }, 6), "head", HeadShade);
        B.Add(Blob(V(0, 0.9f, 1.02f), 0.035f, 1.2f, 0.8f, 1, 1), "head", (_, _) => nose);
        // Jaw.
        B.Add(Loft(new Ring[] { new(0.7f, 0.82f, 0.09f, 0.04f), new(0.97f, 0.83f, 0.05f, 0.03f) }, 5), "jaw", (_, _) => Mul(muzzle, 0.85f));
        // Ears and eyes.
        foreach (float sx in new[] { 1f, -1f })
            B.Add(Cone(V(0.08f * sx, 1.02f, 0.66f), V(0.25f * sx, 1, -0.2f), 0.055f, 0.16f, 3), "head", (c, n) => Mul(Shade(c, n), 0.8f));
        foreach (float sx in new[] { 1f, -1f })
            B.Add(Blob(V(0.1f * sx, 0.97f, 0.8f), 0.028f, 1, 0.7f, 1), "head", (_, _) => C(look.Eye), look.GlowEyes);

        // Legs.
        foreach (var (side, sx) in new[] { ("L", 1f), ("R", -1f) })
        {
            Vector3 fu = B.BoneWorld($"fu{side}"), fl = B.BoneWorld($"fl{side}");
            B.Add(Limb(fu + V(0, 0.05f, 0), fl, 0.075f, 0.055f), $"fu{side}", Shade);
            B.Add(Limb(fl, V(fl.X, 0.04f, fl.Z + 0.02f), 0.05f, 0.04f), $"fl{side}", Shade);
            B.Add(Blob(V(fl.X, 0.04f, fl.Z + 0.06f), 0.05f, 1, 0.6f, 1.4f), $"fl{side}", (_, _) => Mul(belly, 0.55f));
            Vector3 bu = B.BoneWorld($"bu{side}"), bl = B.BoneWorld($"bl{side}");
            B.Add(Blob(bu + V(0.02f * sx, -0.04f, 0.02f), 0.11f, 0.8f, 1.2f, 1.1f), $"bu{side}", Shade);
            B.Add(Limb(bu, bl, 0.08f, 0.05f), $"bu{side}", Shade);
            B.Add(Limb(bl, V(bl.X, 0.04f, bl.Z + 0.05f), 0.05f, 0.04f), $"bl{side}", Shade);
            B.Add(Blob(V(bl.X, 0.04f, bl.Z + 0.09f), 0.05f, 1, 0.6f, 1.4f), $"bl{side}", (_, _) => Mul(belly, 0.55f));
        }

        // Tail: bushy in the middle.
        B.Add(Loft(new Ring[] { new(-0.52f, 0.68f, 0.06f, 0.06f), new(-0.66f, 0.62f, 0.1f, 0.1f) }, 6), "tail", Shade);
        B.Add(Loft(new Ring[] { new(-0.66f, 0.62f, 0.1f, 0.1f), new(-0.86f, 0.5f, 0.09f, 0.09f), new(-1.0f, 0.42f, 0.03f, 0.03f) }, 6), "tail2", (c, n) => c.Z < -0.93f ? belly : Shade(c, n));
        B.GlowColor = C(look.Eye);

        B.AddClip("run", 0.56, t =>
        {
            double a = t * Math.Tau;
            double Leg(double ph, double amp) => Math.Sin(a + ph) * amp;
            return new()
            {
                ["hips"] = Both(Math.Sin(a) * 0.08, 0, 0, 0, Math.Abs(Math.Sin(a)) * 0.07, 0),
                ["chest"] = Rot(-Math.Sin(a) * 0.12),
                ["neck"] = Rot(Math.Sin(a + 0.6) * 0.1),
                ["head"] = Rot(-Math.Sin(a + 0.6) * 0.08),
                ["tail"] = Rot(0.25 + Math.Sin(a * 2) * 0.12, Math.Sin(a) * 0.2),
                ["tail2"] = Rot(0.1, Math.Sin(a + 1) * 0.25),
                ["fuL"] = Rot(Leg(0, 0.75)), ["flL"] = Rot(Math.Max(0, Leg(0.9, 0.9))),
                ["fuR"] = Rot(Leg(0.4, 0.75)), ["flR"] = Rot(Math.Max(0, Leg(1.3, 0.9))),
                ["buL"] = Rot(Leg(Math.PI, 0.7)), ["blL"] = Rot(-Math.Max(0, Leg(Math.PI + 0.9, 0.8))),
                ["buR"] = Rot(Leg(Math.PI + 0.4, 0.7)), ["blR"] = Rot(-Math.Max(0, Leg(Math.PI + 1.3, 0.8))),
                ["jaw"] = Rot(0.15 + Math.Sin(a) * 0.05),
            };
        });
        B.AddClip("idle", 2.4, t =>
        {
            double a = t * Math.Tau;
            return new()
            {
                ["chest"] = At(0, Math.Sin(a * 2) * 0.008, 0),
                ["neck"] = Rot(Math.Sin(a) * 0.05, Math.Sin(a * 0.5) * 0.25),
                ["head"] = Rot(0.05, Math.Sin(a) * 0.15),
                ["tail"] = Rot(0.35, Math.Sin(a * 3) * 0.35),
                ["tail2"] = Rot(0.2, Math.Sin(a * 3 + 1) * 0.3),
                ["jaw"] = Rot(0.05 + Math.Max(0, Math.Sin(a * 4)) * 0.12),
            };
        });
        B.AddClip("attack", 0.5, t =>
        {
            double k = Math.Sin(Math.Min(1, t * 1.6) * Math.PI);
            return new()
            {
                ["hips"] = Both(-0.15 * k, 0, 0, 0, -0.04 * k, 0.12 * k),
                ["chest"] = Rot(0.2 * k), ["neck"] = Rot(-0.35 * k), ["head"] = Rot(0.25 * k), ["jaw"] = Rot(0.6 * k),
                ["fuL"] = Rot(-0.8 * k), ["fuR"] = Rot(-0.7 * k), ["tail"] = Rot(0.1),
            };
        });
        B.AddClip("windup", 0.8, t =>
        {
            double a = t * Math.Tau;
            return new()
            {
                ["hips"] = Both(0.15, 0, 0, 0, -0.12, -0.05),
                ["chest"] = Rot(0.1), ["neck"] = Rot(0.35), ["head"] = Rot(-0.25),
                ["jaw"] = Rot(0.3 + Math.Sin(a * 6) * 0.08),
                ["tail"] = Rot(-0.2, Math.Sin(a * 4) * 0.08),
                ["buL"] = Rot(0.4), ["buR"] = Rot(0.4), ["blL"] = Rot(-0.6), ["blR"] = Rot(-0.6),
            };
        });
        B.AddClip("die", 0.9, t =>
        {
            double k = Math.Min(1, t * 1.5), e = 1 - (1 - k) * (1 - k);
            return new()
            {
                ["root"] = Both(0, 0, e * 1.45, 0, -0.05 * e, 0),
                ["hips"] = At(0, -0.35 * e, 0),
                ["neck"] = Rot(0.3 * e), ["head"] = Rot(0.2 * e), ["jaw"] = Rot(0.35 * e),
                ["fuL"] = Rot(-0.5 * e), ["fuR"] = Rot(0.3 * e), ["buL"] = Rot(0.4 * e), ["buR"] = Rot(-0.3 * e),
                ["tail"] = Rot(0.5 * e),
            };
        });
        B.AddClip("hit", 0.3, t =>
        {
            double k = Math.Sin(t * Math.PI);
            return new() { ["chest"] = Both(0, 0, 0.15 * k, 0, 0, -0.06 * k), ["head"] = Rot(-0.25 * k, 0.2 * k), ["neck"] = Rot(-0.2 * k) };
        });
        return B;
    }

    /* --------------------------------------------------------------- boars -- */

    public static Creature Boar()
    {
        var rng = new Random(17);
        var B = new Creature();
        B.AddBone("root", null, 0, 0, 0);
        B.AddBone("hips", "root", 0, 0.55f, -0.3f);
        B.AddBone("chest", "hips", 0, 0.05f, 0.5f);
        B.AddBone("head", "chest", 0, -0.02f, 0.28f);
        B.AddBone("tail", "hips", 0, 0.1f, -0.35f);
        foreach (var (side, sx) in new[] { ("L", 1f), ("R", -1f) })
        {
            B.AddBone($"fu{side}", "chest", 0.2f * sx, -0.15f, 0.05f);
            B.AddBone($"bu{side}", "hips", 0.2f * sx, -0.15f, -0.1f);
        }
        Color dark = C("#3b2a20"), mid = C("#6a4a33"), light = C("#8a6a4c"), bristle = C("#2a1d16");
        Color Shade(Vector3 c, Vector3 n)
        {
            float up = n.Y * 0.5f + 0.5f;
            var col = light.Lerp(mid, up).Lerp(dark, Smooth(c.Y, 0.7f, 0.9f) * 0.6f);
            return Lighter(col, Mathf.Sin(c.X * 33 + c.Z * 19) * 0.025f);
        }
        B.Add(Loft(new Ring[]
        {
            new(-0.7f, 0.58f, 0.14f, 0.14f), new(-0.55f, 0.62f, 0.3f, 0.28f), new(-0.2f, 0.66f, 0.34f, 0.32f), new(0.15f, 0.7f, 0.36f, 0.36f), new(0.35f, 0.66f, 0.3f, 0.31f),
        }, 8, 0.12f, rng), new Blend("hips", "chest", 2, -0.3f, 0.2f), Shade);
        // Bristle ridge along the spine.
        for (int i = 0; i < 9; i++)
        {
            float z = -0.5f + i * 0.1f;
            B.Add(Cone(V(0, 0.94f + Mathf.Sin(i * 0.6f) * 0.04f, z), V(0, 1, -0.35f), 0.05f, 0.18f + (float)rng.NextDouble() * 0.08f, 3), z > 0 ? "chest" : "hips", (_, _) => bristle);
        }
        // Head: a wedge ending in a flat snout, with tusks.
        B.Add(Loft(new Ring[] { new(0.36f, 0.68f, 0.26f, 0.26f), new(0.56f, 0.6f, 0.2f, 0.2f), new(0.78f, 0.5f, 0.12f, 0.12f), new(0.86f, 0.48f, 0.11f, 0.1f) }, 7),
            "head", (c, n) => c.Z > 0.84f ? C("#b08070") : Shade(c, n));
        foreach (float sx in new[] { 1f, -1f })
        {
            B.Add(Cone(V(0.1f * sx, 0.45f, 0.76f), V(0.3f * sx, 1, 0.5f), 0.03f, 0.2f, 4), "head", (_, _) => C("#e8e0c8"));
            B.Add(Cone(V(0.13f * sx, 0.84f, 0.46f), V(0.6f * sx, 0.8f, -0.3f), 0.06f, 0.14f, 3), "head", (_, _) => dark);
            B.Add(Blob(V(0.14f * sx, 0.72f, 0.62f), 0.025f), "head", (_, _) => C("#1a0e0a"));
        }
        foreach (var side in new[] { "L", "R" })
        {
            Vector3 f = B.BoneWorld($"fu{side}"), b = B.BoneWorld($"bu{side}");
            B.Add(Limb(f, V(f.X, 0.03f, f.Z + 0.03f), 0.09f, 0.06f), $"fu{side}", (_, _) => dark);
            B.Add(Limb(b, V(b.X, 0.03f, b.Z - 0.02f), 0.1f, 0.06f), $"bu{side}", (_, _) => dark);
        }
        B.Add(Cone(V(0, 0.66f, -0.68f), V(0, -0.5f, -1), 0.03f, 0.22f, 3), "tail", (_, _) => dark);

        B.AddClip("run", 0.5, t =>
        {
            double a = t * Math.Tau;
            return new()
            {
                ["hips"] = Both(Math.Sin(a) * 0.05, 0, 0, 0, Math.Abs(Math.Sin(a)) * 0.05, 0),
                ["chest"] = Rot(-Math.Sin(a) * 0.06), ["head"] = Rot(Math.Sin(a + 0.5) * 0.08),
                ["fuL"] = Rot(Math.Sin(a) * 0.7), ["fuR"] = Rot(Math.Sin(a + Math.PI) * 0.7),
                ["buL"] = Rot(Math.Sin(a + Math.PI) * 0.7), ["buR"] = Rot(Math.Sin(a) * 0.7),
                ["tail"] = Rot(Math.Sin(a * 2) * 0.3),
            };
        });
        B.AddClip("idle", 2, t =>
        {
            double a = t * Math.Tau;
            return new() { ["head"] = Rot(0.2 + Math.Max(0, Math.Sin(a * 2)) * 0.25, Math.Sin(a) * 0.2), ["tail"] = Rot(0, Math.Sin(a * 5) * 0.4), ["chest"] = At(0, Math.Sin(a * 2) * 0.01, 0) };
        });
        B.AddClip("windup", 0.6, t =>
        {
            double a = t * Math.Tau;
            // Pawing the ground.
            return new()
            {
                ["hips"] = Both(0.1, 0, 0, 0, -0.04, 0), ["head"] = Rot(0.35),
                ["fuL"] = Rot(-0.6 + Math.Max(0, Math.Sin(a * 2)) * 0.9), ["fuR"] = Rot(0.1),
                ["tail"] = Rot(-0.4, Math.Sin(a * 6) * 0.3),
            };
        });
        B.AddClip("attack", 0.45, t =>
        {
            double k = Math.Sin(t * Math.PI);
            return new() { ["head"] = Both(-0.5 * k, 0, 0, 0, 0.05 * k, 0.1 * k), ["chest"] = Rot(-0.1 * k), ["fuL"] = Rot(-0.4 * k), ["fuR"] = Rot(-0.4 * k) };
        });
        B.AddClip("die", 0.8, t =>
        {
            double e = 1 - Math.Pow(1 - Math.Min(1, t * 1.4), 2);
            return new() { ["root"] = Rot(0, 0, -1.5 * e), ["hips"] = At(0, -0.3 * e, 0), ["head"] = Rot(0.3 * e), ["fuL"] = Rot(0.6 * e), ["buR"] = Rot(-0.5 * e) };
        });
        B.AddClip("hit", 0.3, t => new() { ["chest"] = Rot(0, 0, 0.12 * Math.Sin(t * Math.PI)), ["head"] = Rot(-0.3 * Math.Sin(t * Math.PI)) });
        return B;
    }

    /* ----------------------------------------------------------- lamplings -- */

    public static Creature Lampling(bool sapper)
    {
        var B = new Creature();
        B.AddBone("root", null, 0, 0, 0);
        B.AddBone("body", "root", 0, 0.38f, 0);
        B.AddBone("head", "body", 0, 0.3f, 0.04f);
        B.AddBone("lamp", "head", 0, 0.22f, -0.05f);
        B.AddBone("armL", "body", 0.26f, 0.12f, 0.05f);
        B.AddBone("armR", "body", -0.26f, 0.12f, 0.05f);
        B.AddBone("legL", "body", 0.13f, -0.22f, 0);
        B.AddBone("legR", "body", -0.13f, -0.22f, 0);
        Color skin = C(sapper ? "#8a6a4a" : "#9a7e58"), dark = C("#5a4230"), belly = C("#c8ac80");
        Color Shade(Vector3 c, Vector3 n) => skin.Lerp(belly, Mathf.Max(0, n.Z) * 0.4f).Lerp(dark, Mathf.Max(0, -n.Y) * 0.4f);
        // A round body and a big round head: small, and certain everything is food.
        B.Add(Blob(V(0, 0.36f, 0), 0.25f, 1, 1.05f, 0.95f, 1), "body", Shade);
        B.Add(Blob(V(0, 0.7f, 0.04f), 0.22f, 1.1f, 0.95f, 1, 1), "head", Shade);
        // Snout, eyes, ears.
        B.Add(Blob(V(0, 0.66f, 0.25f), 0.08f, 1.3f, 0.8f, 1), "head", (_, _) => C("#d8a080"));
        foreach (float sx in new[] { 1f, -1f })
        {
            B.Add(Blob(V(0.09f * sx, 0.76f, 0.2f), 0.055f, 1, 1.2f, 0.6f, 1), "head", (_, _) => C("#1a1410"));
            B.Add(Blob(V(0.1f * sx, 0.78f, 0.23f), 0.018f), "head", (_, _) => C("#ffe8a0"), true);
            B.Add(Cone(V(0.17f * sx, 0.84f, 0), V(0.9f * sx, 0.6f, -0.2f), 0.06f, 0.16f, 3), "head", (_, _) => Mul(skin, 0.8f));
        }
        // The hard hat and its lamp: the lamp glows, which is what they dig toward.
        B.Add(Loft(new Ring[] { new(-0.02f, 0.86f, 0.24f, 0.02f), new(0.02f, 0.9f, 0.2f, 0.1f) }, 8), "head", (_, _) => C(sapper ? "#7a2a1a" : "#c8a030"));
        B.Add(Limb(V(0, 0.95f, -0.02f), V(0, 1.08f, -0.04f), 0.02f, 0.02f, 4), "lamp", (_, _) => C("#3a3a3a"));
        B.Add(Blob(V(0, 1.12f, -0.04f), 0.07f, 1, 1.1f, 1, 1), "lamp", (_, _) => C("#ffd070"), true);
        // Arms with digging claws; the sapper carries a satchel.
        foreach (var (side, sx) in new[] { ("L", 1f), ("R", -1f) })
        {
            B.Add(Limb(V(0.24f * sx, 0.5f, 0.05f), V(0.36f * sx, 0.3f, 0.12f), 0.06f, 0.05f), $"arm{side}", Shade);
            for (int k = 0; k < 3; k++)
                B.Add(Cone(V((0.36f + k * 0.015f) * sx, 0.28f, 0.12f + k * 0.03f), V(0.2f * sx, -1, 0.5f), 0.02f, 0.1f, 3), $"arm{side}", (_, _) => C("#e8dcc0"));
            B.Add(Limb(V(0.13f * sx, 0.18f, 0), V(0.14f * sx, 0.03f, 0.03f), 0.07f, 0.06f), $"leg{side}", (_, _) => dark);
            B.Add(Blob(V(0.14f * sx, 0.03f, 0.08f), 0.07f, 1, 0.5f, 1.4f), $"leg{side}", (_, _) => dark);
        }
        if (sapper)
        {
            B.Add(Blob(V(0, 0.4f, -0.26f), 0.14f, 1.1f, 1, 0.7f), "body", (_, _) => C("#5a3a22"));
            B.Add(Blob(V(0, 0.55f, -0.3f), 0.05f), "body", (_, _) => C("#ff7a30"), true);
        }
        B.GlowColor = C("#ffc860");

        B.AddClip("run", 0.42, t =>
        {
            double a = t * Math.Tau;
            return new()
            {
                ["body"] = Both(0.15, 0, Math.Sin(a) * 0.12, 0, Math.Abs(Math.Sin(a)) * 0.06, 0),
                ["head"] = Rot(-0.1, 0, -Math.Sin(a) * 0.1),
                ["lamp"] = Rot(Math.Sin(a + 1) * 0.3, 0, Math.Sin(a) * 0.3),
                ["armL"] = Rot(Math.Sin(a) * 0.9), ["armR"] = Rot(-Math.Sin(a) * 0.9),
                ["legL"] = Rot(-Math.Sin(a) * 0.8), ["legR"] = Rot(Math.Sin(a) * 0.8),
            };
        });
        B.AddClip("idle", 1.6, t =>
        {
            double a = t * Math.Tau;
            return new() { ["body"] = At(0, Math.Sin(a * 2) * 0.01, 0), ["head"] = Rot(0, Math.Sin(a) * 0.4), ["lamp"] = Rot(Math.Sin(a * 2) * 0.15), ["armL"] = Rot(0.2, 0, Math.Sin(a * 4) * 0.1) };
        });
        B.AddClip("attack", 0.45, t =>
        {
            double k = Math.Sin(t * Math.PI);
            return new() { ["body"] = Rot(0.35 * k), ["armL"] = Rot(-1.6 * k), ["armR"] = Rot(-1.2 * k), ["head"] = Rot(0.2 * k) };
        });
        B.AddClip("burrow", 0.5, t =>
        {
            double a = t * Math.Tau;
            return new() { ["body"] = Both(0.9, 0, 0, 0, -0.35, 0), ["armL"] = Rot(-1.2 + Math.Sin(a) * 0.8), ["armR"] = Rot(-1.2 - Math.Sin(a) * 0.8), ["lamp"] = Rot(Math.Sin(a * 2) * 0.4) };
        });
        B.AddClip("rise", 0.6, t =>
        {
            double e = Math.Min(1, t * 1.3);
            return new() { ["root"] = At(0, -0.6 * (1 - e), 0), ["body"] = Rot(0.6 * (1 - e)), ["armL"] = Rot(-2.2 * (1 - e)), ["armR"] = Rot(-2.2 * (1 - e)) };
        });
        B.AddClip("die", 0.8, t =>
        {
            double e = 1 - Math.Pow(1 - Math.Min(1, t * 1.4), 2);
            return new() { ["root"] = Both(-1.4 * e, 0, 0, 0, 0, -0.2 * e), ["head"] = Rot(0.3 * e), ["lamp"] = Rot(1.2 * e), ["armL"] = Rot(-1.5 * e, 0, 0.5 * e), ["armR"] = Rot(-1.2 * e, 0, -0.6 * e) };
        });
        B.AddClip("hit", 0.3, t => new() { ["body"] = Rot(-0.25 * Math.Sin(t * Math.PI)) });
        return B;
    }

    /* ------------------------------------------------------------- lookup -- */

    static readonly Dictionary<string, Creature> cache = new();

    /// <summary>The creature a visual names, made once.</summary>
    public static Creature? Of(string visual)
    {
        if (cache.TryGetValue(visual, out var c)) return c;
        c = visual switch
        {
            _ when WolfLooks.TryGetValue(visual, out var look) => Wolf(look, visual.Length * 7),
            "boar" => Boar(),
            "lampling" => Lampling(false),
            "lampling_sapper" => Lampling(true),
            _ => null,
        };
        if (c != null) cache[visual] = c;
        return c;
    }
}
