using System;
using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.View;

/// <summary>
/// Gore: what a blade and a fire do to the things they kill (the web game's
/// fx/gore.ts).
///
///   - sprays: a hit on anything that bleeds throws blood the way it was
///     struck; on the dead, bone chips;
///   - splats: blood on the ground (decals, so it lies on grass and stones as
///     much as earth), spattered by hits and pooled under the fallen: a pool
///     spreads for a few seconds, darkens and browns as it dries, and fades;
///   - gibs: a blow far bigger than what it killed bursts the body; meat,
///     bone and the odd skull are thrown with simple physics, bounce, settle,
///     bleed where they land, and sink into the ground in their time.
///
/// `Level` scales all of it (the Gore setting): 1 full, 0.35 reduced (a
/// little blood, nothing thrown), 0 none.
/// </summary>
public partial class Gore : Node3D
{
    public sealed record Blood(Color Spray, Color Pool);

    static readonly Blood Red = new(new Color("#8e0c0c"), new Color("#4a0404"));
    static readonly Blood Ichor = new(new Color("#3a4a10"), new Color("#1c240a"));
    /// <summary>The lamplings': thick and dark, from a long way under.</summary>
    static readonly Blood Deep = new(new Color("#6a1a0c"), new Color("#2c0906"));

    /// <summary>What a family bleeds (null: it does not).</summary>
    public static Blood? Of(Family? family, string def = "") => family switch
    {
        null or Family.Undead or Family.Elemental or Family.Construct => null,
        Family.Blighted => Ichor,
        Family.Lampling => Deep,
        _ when def.Contains("blight") => Ichor,
        _ => Red,
    };

    public float Level = 1;
    readonly Func<double, double, double> heightAt;
    readonly Sparks matter;
    readonly Hits hits;
    double time;
    static readonly Random rng = new(23);
    static float R() => (float)rng.NextDouble();

    public Gore(Func<double, double, double> heightAt, Sparks matter, Hits hits)
    {
        this.heightAt = heightAt;
        this.matter = matter;
        this.hits = hits;
        Name = "Gore";
    }

    public override void _Ready()
    {
        BuildSplats();
        BuildGibs();
    }

    float Ground(float x, float z) => (float)heightAt(x, z);

    /* ------------------------------------------------------------ splats -- */

    // Decals share the renderer's clustered budget with the lights: enough
    // for a field of the fallen, not the web game's 420.
    const int SplatMax = 180;

    sealed class Splat
    {
        public required Decal Decal;
        public double Born = -1e9, Life = 1;
        public bool Pool;
        public Color Color;
        public Vector2 Size;
        // What the decal was last given, so it is told only of a change: a new
        // size moves it in the renderer's culling, every frame, for each of 180.
        public bool Shown;
        public Vector3 SentSize;
        public Color SentColor;
    }

    readonly List<Splat> splats = new();
    int nextSplat;

    void BuildSplats()
    {
        var (albedo, orm) = SplatTextures();
        for (int i = 0; i < SplatMax; i++)
        {
            var d = new Decal
            {
                CullMask = 1, TextureAlbedo = albedo, TextureOrm = orm, Size = new Vector3(1, 1.2f, 1), Visible = false,
                UpperFade = 0.2f, LowerFade = 0.4f, AlbedoMix = 1, SortingOffset = i * 0.001f,
            };
            AddChild(d);
            splats.Add(new Splat { Decal = d });
        }
    }

    /// <summary>A ragged blot with droplets thrown round it; wet (smooth) where the blood is.</summary>
    static (ImageTexture Albedo, ImageTexture Orm) SplatTextures()
    {
        const int N = 256;
        var img = Image.CreateEmpty(N, N, true, Image.Format.Rgba8);
        var orm = Image.CreateEmpty(N, N, true, Image.Format.Rgba8);
        var noise = new FastNoiseLite { Seed = 9, Frequency = 0.03f, FractalOctaves = 4 };
        var r = new RandomNumberGenerator { Seed = 13 };
        var drops = new List<(Vector2 P, float R)>();
        for (int i = 0; i < 22; i++) { float a = r.Randf() * Mathf.Tau, d = 0.35f + r.Randf() * 0.55f; drops.Add((new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * d, 0.015f + r.Randf() * 0.04f)); }
        for (int y = 0; y < N; y++)
            for (int x = 0; x < N; x++)
            {
                var p = new Vector2(x, y) / N * 2 - Vector2.One;
                float rr = p.Length() + noise.GetNoise2D(x, y) * 0.45f;
                float a = 1 - Mathf.SmoothStep(0.32f, 0.42f, rr);
                foreach (var (dp, dr) in drops) a = Mathf.Max(a, 1 - Mathf.SmoothStep(dr * 0.6f, dr, (p - dp).Length()));
                // Darker and deeper at the middle, thinner at the rim.
                float wet = Mathf.Lerp(0.75f, 1.15f, Mathf.SmoothStep(0.05f, 0.4f, rr)) * (0.85f + 0.15f * noise.GetNoise2D(x * 3, y * 3));
                img.SetPixel(x, y, new Color(Mathf.Min(1, wet), Mathf.Min(1, wet), Mathf.Min(1, wet), a));
                orm.SetPixel(x, y, new Color(1, 0.3f, 0, a));
            }
        img.GenerateMipmaps();
        orm.GenerateMipmaps();
        return (ImageTexture.CreateFromImage(img), ImageTexture.CreateFromImage(orm));
    }

    /// <summary>Blood on the ground at `at` (its height is found here).</summary>
    public void Splash(float x, float z, float size, Blood blood, double life, bool pool = false)
    {
        var s = splats[nextSplat];
        nextSplat = (nextSplat + 1) % splats.Count;
        s.Born = time;
        s.Life = life;
        s.Pool = pool;
        s.Color = blood.Pool;
        s.Size = new Vector2(size, size * (0.8f + R() * 0.4f));
        s.Decal.Position = new Vector3(x, Ground(x, z) + 0.3f, z);
        s.Decal.Rotation = new Vector3(0, R() * Mathf.Tau, 0);
        if (!s.Shown) { s.Shown = true; s.Decal.Visible = true; }
        s.SentSize = new Vector3(-1, -1, -1);
        Shape(s);
    }

    void Shape(Splat s)
    {
        double age = time - s.Born;
        float k = (float)Math.Clamp(age / s.Life, 0, 1);
        // A pool spreads for a few seconds; a splat is there at once.
        float grow = s.Pool ? Mathf.SmoothStep(0, 4, (float)age) * 0.75f + 0.25f : 1;
        var size = new Vector3(s.Size.X * grow, 1.2f, s.Size.Y * grow);
        if (size != s.SentSize) { s.SentSize = size; s.Decal.Size = size; }
        // It dries brown, and in its time is gone.
        float dry = Mathf.SmoothStep(0.1f, 0.7f, k);
        var c = s.Color.Lerp(s.Color * new Color(0.8f, 0.62f, 0.55f), dry);
        c.A = 0.92f * (1 - Mathf.SmoothStep(0.75f, 1, k));
        if (c != s.SentColor) { s.SentColor = c; s.Decal.Modulate = c; }
        if (k >= 1) { s.Shown = false; s.Decal.Visible = false; }
    }

    /* -------------------------------------------------------------- gibs -- */

    enum Kind { Meat, Bone, Skull }

    sealed class Gib
    {
        public Kind Kind;
        public int Slot;
        public Vector3 P, V, Axis;
        public float Ang, Spin, R, Age, Life, Size, Settle;
        public bool Resting, Bled;
        // At rest, settled and placed there: nothing about it changes until it sinks.
        public bool Still;
        /// <summary>How it lay as it stopped, and how it comes to rest: a bone flat, a skull face up.</summary>
        public Quaternion From, Rest;
        public Blood? Blood;
    }

    /// <summary>One kind of piece: its MultiMesh and the floats behind it,
    /// changed here and handed over once a frame (a call into the engine for
    /// every piece in the air or on the ground, every frame, cost more).</summary>
    sealed class GibMeshes
    {
        public required MultiMesh Mesh;
        public required float[] Buffer;
        public required int Stride;
        public bool Dirty;

        public void Place(int slot, Transform3D t)
        {
            int o = slot * Stride;
            var b = t.Basis;
            var f = Buffer;
            f[o] = b.X.X; f[o + 1] = b.Y.X; f[o + 2] = b.Z.X; f[o + 3] = t.Origin.X;
            f[o + 4] = b.X.Y; f[o + 5] = b.Y.Y; f[o + 6] = b.Z.Y; f[o + 7] = t.Origin.Y;
            f[o + 8] = b.X.Z; f[o + 9] = b.Y.Z; f[o + 10] = b.Z.Z; f[o + 11] = t.Origin.Z;
            Dirty = true;
        }

        public void Tint(int slot, Color c)
        {
            if (Stride < 16) return;
            int o = slot * Stride + 12;
            Buffer[o] = c.R; Buffer[o + 1] = c.G; Buffer[o + 2] = c.B; Buffer[o + 3] = c.A;
            Dirty = true;
        }

        public void Flush()
        {
            if (!Dirty) return;
            Dirty = false;
            RenderingServer.MultimeshSetBuffer(Mesh.GetRid(), Buffer);
        }
    }

    readonly Dictionary<Kind, GibMeshes> meshes = new();
    readonly Dictionary<Kind, Stack<int>> free = new();
    readonly List<Gib> live = new();

    void BuildGibs()
    {
        // Chunks knocked out of round.
        var chunk = Knocked(new SphereMesh { Radius = 0.5f, Height = 1, RadialSegments = 6, Rings = 3 });
        // Bones and skulls read as bones and skulls from the arena's height, not as white
        // sticks and balls (docs/EXPERIENCE_AUDIT.md, finding 3): a shaft with knuckled ends,
        // a cranium with a jaw and dark sockets, in old, dirty bone rather than chalk.
        var bone = Bone();
        var skull = Skull();
        var meat = new StandardMaterial3D { AlbedoColor = Colors.White, VertexColorUseAsAlbedo = true, Roughness = 0.38f, Metallic = 0.05f };
        // Old bone, darker than the living: chalk-white pieces drew the eye before what was coming.
        var boneM = new StandardMaterial3D { AlbedoColor = new Color("#6e6555"), VertexColorUseAsAlbedo = true, Roughness = 0.9f };
        chunk.SurfaceSetMaterial(0, meat);
        bone.SurfaceSetMaterial(0, boneM);
        skull.SurfaceSetMaterial(0, boneM);
        Add(Kind.Meat, chunk, 360, true);
        Add(Kind.Bone, bone, 180, false);
        Add(Kind.Skull, skull, 48, false);
    }

    void Add(Kind kind, Mesh mesh, int n, bool colors)
    {
        var mm = new MultiMesh { TransformFormat = MultiMesh.TransformFormatEnum.Transform3D, UseColors = colors, InstanceCount = n, VisibleInstanceCount = n, Mesh = mesh };
        // Every piece put away to begin with (scaled to nothing), white.
        var pieces = new GibMeshes { Mesh = mm, Buffer = new float[n * (colors ? 16 : 12)], Stride = colors ? 16 : 12 };
        var zero = new Transform3D(Godot.Basis.FromScale(Vector3.Zero), Vector3.Zero);
        for (int i = 0; i < n; i++) { pieces.Place(i, zero); pieces.Tint(i, Colors.White); }
        pieces.Flush();
        var inst = new MultiMeshInstance3D { Multimesh = mm, CastShadow = GeometryInstance3D.ShadowCastingSetting.On, Layers = 1 };
        inst.CustomAabb = new Aabb(new Vector3(-1e4f, -1e4f, -1e4f), new Vector3(2e4f, 2e4f, 2e4f));
        AddChild(inst);
        meshes[kind] = pieces;
        var s = new Stack<int>();
        for (int i = n - 1; i >= 0; i--) s.Push(i);
        free[kind] = s;
    }

    /// <summary>A long bone, one unit long along Y: a narrow shaft, a knuckle at each end
    /// (two lobes at one, a ball at the other), darker toward the ends where the dirt is.</summary>
    static ArrayMesh Bone()
    {
        var st = new SurfaceTool();
        st.Begin(Mesh.PrimitiveType.Triangles);
        void Part(PrimitiveMesh m, Transform3D at, Color c)
        {
            var arr = m.GetMeshArrays();
            var v = (Vector3[])arr[(int)Mesh.ArrayType.Vertex];
            var nrm = (Vector3[])arr[(int)Mesh.ArrayType.Normal];
            var idx = arr[(int)Mesh.ArrayType.Index].AsInt32Array();
            foreach (int i in idx) { st.SetColor(c); st.SetNormal((at.Basis * nrm[i]).Normalized()); st.AddVertex(at * v[i]); }
        }
        var shaft = new Color(0.95f, 0.93f, 0.88f);
        var end = new Color(0.72f, 0.68f, 0.6f);
        Part(new CylinderMesh { TopRadius = 0.07f, BottomRadius = 0.08f, Height = 0.8f, RadialSegments = 7, Rings = 1 }, Transform3D.Identity, shaft);
        Part(new SphereMesh { Radius = 0.11f, Height = 0.2f, RadialSegments = 7, Rings = 4 }, new Transform3D(Godot.Basis.Identity, new Vector3(-0.06f, 0.42f, 0)), end);
        Part(new SphereMesh { Radius = 0.11f, Height = 0.2f, RadialSegments = 7, Rings = 4 }, new Transform3D(Godot.Basis.Identity, new Vector3(0.06f, 0.42f, 0)), end);
        Part(new SphereMesh { Radius = 0.13f, Height = 0.24f, RadialSegments = 7, Rings = 4 }, new Transform3D(Godot.Basis.Identity, new Vector3(0, -0.42f, 0)), end);
        return st.Commit();
    }

    /// <summary>A skull, about a unit across: the cranium long front to back, a face plate,
    /// a lower jaw, and the sockets and nose dark (vertex colour), so it reads as a skull.</summary>
    static ArrayMesh Skull()
    {
        var st = new SurfaceTool();
        st.Begin(Mesh.PrimitiveType.Triangles);
        void Part(PrimitiveMesh m, Transform3D at, Func<Vector3, Color> paint)
        {
            var arr = m.GetMeshArrays();
            var v = (Vector3[])arr[(int)Mesh.ArrayType.Vertex];
            var nrm = (Vector3[])arr[(int)Mesh.ArrayType.Normal];
            var idx = arr[(int)Mesh.ArrayType.Index].AsInt32Array();
            foreach (int i in idx) { var p = at * v[i]; st.SetColor(paint(p)); st.SetNormal((at.Basis * nrm[i]).Normalized()); st.AddVertex(p); }
        }
        // Facing +Z: sockets either side of the middle a little above it, the nose below.
        Color Face(Vector3 p)
        {
            float eye = Mathf.Min(new Vector2(p.X - 0.17f, p.Y - 0.02f).Length(), new Vector2(p.X + 0.17f, p.Y - 0.02f).Length());
            float nose = new Vector2(p.X * 1.6f, p.Y + 0.14f).Length();
            float dark = p.Z > 0.2f ? Mathf.Max(1 - Mathf.SmoothStep(0.07f, 0.12f, eye), 1 - Mathf.SmoothStep(0.04f, 0.08f, nose)) : 0;
            return new Color(1, 0.97f, 0.9f).Lerp(new Color(0.12f, 0.1f, 0.09f), dark);
        }
        Part(new SphereMesh { Radius = 0.5f, Height = 0.9f, RadialSegments = 12, Rings = 8 }, new Transform3D(Godot.Basis.FromScale(new Vector3(0.82f, 0.86f, 1)), new Vector3(0, 0.08f, -0.06f)), Face);
        Part(new SphereMesh { Radius = 0.3f, Height = 0.5f, RadialSegments = 10, Rings = 5 }, new Transform3D(Godot.Basis.FromScale(new Vector3(1.05f, 0.9f, 0.9f)), new Vector3(0, -0.14f, 0.2f)), Face);
        Part(new BoxMesh { Size = new Vector3(0.42f, 0.12f, 0.3f) }, new Transform3D(Godot.Basis.Identity, new Vector3(0, -0.36f, 0.16f)), _ => new Color(0.86f, 0.82f, 0.74f));
        return st.Commit();
    }

    /// <summary>A rough lump: a low sphere with its points pushed about, flat-shaded.</summary>
    static ArrayMesh Knocked(PrimitiveMesh m)
    {
        var st = new SurfaceTool();
        st.CreateFrom(m, 0);
        var arr = st.Commit().SurfaceGetArrays(0);
        var verts = (Vector3[])arr[(int)Mesh.ArrayType.Vertex];
        var r = new RandomNumberGenerator { Seed = 31 };
        // The same point is the same point on every face that shares it.
        var moved = new Dictionary<Vector3, Vector3>();
        for (int i = 0; i < verts.Length; i++)
        {
            var key = verts[i].Snapped(Vector3.One * 0.001f);
            if (!moved.TryGetValue(key, out var to)) moved[key] = to = new Vector3(verts[i].X * (0.7f + r.Randf() * 0.6f), verts[i].Y * (0.6f + r.Randf() * 0.5f), verts[i].Z * (0.7f + r.Randf() * 0.6f));
            verts[i] = to;
        }
        var idx = arr[(int)Mesh.ArrayType.Index].AsInt32Array();
        var flat = new SurfaceTool();
        flat.Begin(Mesh.PrimitiveType.Triangles);
        flat.SetSmoothGroup(uint.MaxValue);
        if (idx.Length > 0) foreach (int i in idx) flat.AddVertex(verts[i]);
        else foreach (var v in verts) flat.AddVertex(v);
        flat.GenerateNormals();
        return flat.Commit();
    }

    void Throw(Kind kind, Vector3 at, Vector3 v, float size, Blood? blood, Color? tint = null)
    {
        if (!free[kind].TryPop(out int slot))
        {
            // Full: the oldest of this kind goes.
            var old = live.Find(g => g.Kind == kind);
            if (old == null) return;
            Retire(old);
            slot = free[kind].Pop();
        }
        if (kind == Kind.Meat) meshes[kind].Tint(slot, tint ?? Colors.White);
        live.Add(new Gib
        {
            Kind = kind, Slot = slot, P = at, V = v, Axis = new Vector3(R() - 0.5f, R() - 0.5f, R() - 0.5f).Normalized(),
            // (Bone and skull go back to the ground sooner: in a horde they were a litter.)
            Ang = R() * 6, Spin = 6 + R() * 10, R = size * 0.4f, Life = kind == Kind.Meat ? 16 + R() * 6 : 8 + R() * 4, Blood = blood, Size = size,
        });
    }

    /// <summary>How a piece lies once still: a bone along the ground at any heading with a little
    /// roll, a skull on its back or side with its face (+Z) tipped up toward the sky.</summary>
    Quaternion RestPose(Kind kind)
    {
        var yaw = new Godot.Basis(Vector3.Up, R() * Mathf.Tau);
        if (kind == Kind.Bone) return new Quaternion(yaw * new Godot.Basis(Vector3.Right, Mathf.Pi / 2) * new Godot.Basis(Vector3.Up, R() * Mathf.Tau));
        return new Quaternion(yaw * new Godot.Basis(Vector3.Right, -(0.55f + R() * 0.6f)) * new Godot.Basis(Vector3.Forward, (R() - 0.5f) * 0.8f));
    }

    void Retire(Gib g)
    {
        meshes[g.Kind].Place(g.Slot, new Transform3D(Godot.Basis.FromScale(Vector3.Zero), Vector3.Zero));
        free[g.Kind].Push(g.Slot);
        live.Remove(g);
    }

    /* -------------------------------------------------------------- gore -- */

    /// <summary>A blow landing: blood thrown the way it was struck.</summary>
    public void Hit(Vector3 at, double amount, double maxHp, Blood? blood, bool undead, Vector3 dir, bool crit)
    {
        if (Level <= 0) return;
        float force = (float)Math.Min(1, amount / Math.Max(1, maxHp)) * (crit ? 1.6f : 1);
        int n = (int)Math.Round((3 + force * 14) * Level);
        if (blood != null)
        {
            hits.Spray(at, dir, blood.Spray, Math.Clamp(0.25f + force, 0.2f, 1) * Level);
            for (int i = 0; i < n; i++)
            {
                float sp = 2 + R() * 4 + force * 4, a = R() * Mathf.Tau;
                matter.Spawn(new Sparks.P
                {
                    At = at, V = new Vector3(dir.X * sp + Mathf.Cos(a) * sp * 0.45f, 1.5f + R() * 3.5f, dir.Z * sp + Mathf.Sin(a) * sp * 0.45f),
                    Gravity = 16, Drag = 0.6f, Life = 0.35f + R() * 0.35f, Size = 0.05f + R() * 0.07f, SizeEnd = 0.03f,
                    Color = blood.Spray, ColorEnd = blood.Pool, Alpha = 0.95f, Sprite = -1,
                });
            }
            // Some of it reaches the ground.
            if (Level >= 0.5f || R() < Level)
                if (R() < 0.35f + force)
                {
                    float d = 0.4f + R() * (0.8f + force * 1.6f);
                    Splash(at.X + dir.X * d, at.Z + dir.Z * d, 0.5f + force * 1.1f + R() * 0.4f, blood, 40 + R() * 20);
                }
        }
        else if (undead)
        {
            // The dry dead: chips of bone.
            for (int i = 0; i < Math.Ceiling(n * 0.6); i++)
            {
                float a = R() * Mathf.Tau, sp = 2 + R() * 3;
                matter.Spawn(new Sparks.P { At = at, V = new Vector3(dir.X * sp + Mathf.Cos(a) * 1.5f, 2 + R() * 3, dir.Z * sp + Mathf.Sin(a) * 1.5f), Gravity = 14, Drag = 0.4f, Life = 0.5f, Size = 0.06f, SizeEnd = 0.04f, Color = new Color("#d8cdb4"), ColorEnd = new Color("#8a8070"), Alpha = 1, Sprite = -1 });
            }
        }
    }

    /// <summary>A death at `at` (the body's middle). Burst: the blow was far more than it had left.</summary>
    public void Kill(Vector3 at, float scale, Blood? blood, bool undead, bool burst, Vector3 dir)
    {
        if (Level <= 0) return;
        if (blood != null)
        {
            // It bleeds out where it lies.
            Splash(at.X, at.Z, (1.3f + R() * 0.7f) * scale, blood, 60 + R() * 30, pool: true);
            Hit(at, 1, 1, blood, false, dir, true);
        }
        if (!burst || Level < 0.5f) return;
        // Burst: the body comes apart.
        int pieces = (int)Math.Round((blood != null ? 9 : 7) * Math.Min(2, scale) * Level);
        for (int i = 0; i < pieces; i++)
        {
            float a = R() * Mathf.Tau, sp = 2 + R() * 5;
            var v = new Vector3(dir.X * 4 + Mathf.Cos(a) * sp, 4 + R() * 6, dir.Z * 4 + Mathf.Sin(a) * sp);
            var kind = blood != null ? (i % 4 == 3 ? Kind.Bone : Kind.Meat) : Kind.Bone;
            var from = at + new Vector3(Mathf.Cos(a) * 0.2f, R() * 0.6f - 0.3f, Mathf.Sin(a) * 0.2f);
            Throw(kind, from, v, (0.14f + R() * 0.16f) * Math.Min(1.6f, scale), blood, blood?.Pool.Lerp(new Color("#8a2a24"), R() * 0.6f));
        }
        // The head goes its own way.
        if (undead || R() < 0.5f)
            Throw(Kind.Skull, at + Vector3.Up * 0.8f * scale, new Vector3(dir.X * 5 + (R() - 0.5f) * 3, 7 + R() * 3, dir.Z * 5 + (R() - 0.5f) * 3), 0.26f * Math.Min(1.5f, scale), blood);
        if (blood != null)
        {
            hits.Spray(at + Vector3.Up * 0.3f, -dir, blood.Spray, Level);
            for (int i = 0; i < 26 * Level; i++)
            {
                float a = R() * Mathf.Tau, sp = 3 + R() * 7;
                matter.Spawn(new Sparks.P { At = at + Vector3.Up * 0.3f, V = new Vector3(Mathf.Cos(a) * sp + dir.X * 3, 2 + R() * 6, Mathf.Sin(a) * sp + dir.Z * 3), Gravity = 18, Drag = 0.5f, Life = 0.5f + R() * 0.4f, Size = 0.08f + R() * 0.1f, SizeEnd = 0.04f, Color = blood.Spray, ColorEnd = blood.Pool, Alpha = 0.95f, Sprite = -1 });
            }
            for (int i = 0; i < 3; i++)
            {
                float a = R() * Mathf.Tau, d = 0.8f + R() * 1.8f;
                Splash(at.X + Mathf.Cos(a) * d, at.Z + Mathf.Sin(a) * d, 0.7f + R() * 0.9f, blood, 50 + R() * 20);
            }
        }
        // The dry dead burst into the dust of old bone: earth-dark, low and soon down, and told by the
        // first few bursts in a frame. (Pale, a metre across and a second long, every burst hung a
        // grey cloud over the crowd, and a shadow bolt or a moon read as grey smoke.)
        else if (dustBudget-- > 0)
            for (int i = 0; i < 5; i++)
                matter.Spawn(new Sparks.P { At = at + Vector3.Up * 0.3f, V = new Vector3((R() - 0.5f) * 3, 0.6f + R() * 1.2f, (R() - 0.5f) * 3), Gravity = 2, Drag = 2f, Life = 0.7f, Size = 0.3f, SizeEnd = 0.75f, Color = new Color("#5a5348"), ColorEnd = new Color("#2e2a24"), Alpha = 0.28f });
    }

    /// <summary>How many more bursts this frame raise their dust.</summary>
    int dustBudget = 4;

    /// <summary>Pieces in the air or on the ground, and blood on it (for the log).</summary>
    public (int Gibs, int Splats) Counts
    {
        get { int n = 0; foreach (var s in splats) if (s.Shown) n++; return (live.Count, n); }
    }

    public void Step(float dt)
    {
        time += dt;
        dustBudget = 4;
        foreach (var s in splats) if (s.Shown) Shape(s);
        for (int i = live.Count - 1; i >= 0; i--)
        {
            var g = live[i];
            g.Age += dt;
            if (g.Age > g.Life) { Retire(g); continue; }
            if (g.Still && g.Age <= g.Life - 2.5f) continue;
            float ground = Ground(g.P.X, g.P.Z);
            if (!g.Resting)
            {
                g.V.Y -= 22 * dt;
                g.P += g.V * dt;
                g.Ang += g.Spin * dt;
                if (g.P.Y < ground + g.R)
                {
                    g.P.Y = ground + g.R;
                    if (!g.Bled)
                    {
                        g.Bled = true;
                        // It bleeds where it lands.
                        if (g.Blood != null && g.Kind != Kind.Bone) Splash(g.P.X, g.P.Z, 0.25f + g.Size * 1.6f, g.Blood, 30 + R() * 15);
                    }
                    if (Math.Abs(g.V.Y) < 2.2f)
                    {
                        g.Resting = true;
                        g.V = Vector3.Zero;
                        g.From = new Quaternion(new Godot.Basis(g.Axis, g.Ang));
                        g.Rest = RestPose(g.Kind);
                    }
                    else { g.V = new Vector3(g.V.X * 0.55f, -g.V.Y * 0.28f, g.V.Z * 0.55f); g.Spin *= 0.5f; }
                }
            }
            // In their time the ground takes them.
            float sink = Math.Max(0, g.Age - (g.Life - 2.5f)) * 0.35f;
            // Bone and skull roll over into how they lie, so from the arena's height a bone is a
            // bone lying flat and a skull looks up out of the grass, not a stick on end or an egg.
            var rot = new Godot.Basis(g.Axis, g.Ang);
            float r = g.R;
            if (g.Resting && g.Kind != Kind.Meat)
            {
                g.Settle = Math.Min(1, g.Settle + dt / 0.2f);
                float k = g.Settle * g.Settle * (3 - 2 * g.Settle);
                rot = new Godot.Basis(g.From.Slerp(g.Rest, k));
                if (g.Kind == Kind.Bone) r = Mathf.Lerp(g.R, g.Size * 0.15f, k);
            }
            var p = new Vector3(g.P.X, Math.Max(g.P.Y, ground + r) - sink, g.P.Z);
            var scale = g.Kind == Kind.Bone ? new Vector3(g.Size * 1.1f, g.Size * 1.6f, g.Size * 1.1f) : Vector3.One * g.Size;
            meshes[g.Kind].Place(g.Slot, new Transform3D(rot * Godot.Basis.FromScale(scale), p));
            g.Still = g.Resting && (g.Kind == Kind.Meat || g.Settle >= 1);
        }
        foreach (var m in meshes.Values) m.Flush();
    }

    /// <summary>A new place: nothing of the last one's dead comes along.</summary>
    public void Clear()
    {
        for (int i = live.Count - 1; i >= 0; i--) Retire(live[i]);
        foreach (var m in meshes.Values) m.Flush();
        foreach (var s in splats) { s.Shown = false; s.Decal.Visible = false; }
    }
}
