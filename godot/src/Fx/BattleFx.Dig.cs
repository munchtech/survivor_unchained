using System;
using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Play.Bosses;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.View;

/// <summary>
/// The Dig's own looks (combat's Grimtunnel and the tub-way): what moves under the ground and on
/// its rails, and what the ground does when it goes.
///
///   Under      Grimtunnel going along under the ground: a mound of earth heaving up ahead of him,
///              clods thrown, the ground left broken behind (his body is sunk, CrowdView.Under);
///   a tub      after its lane is marked, an iron tub running the rail down it, sparks off its wheels;
///   the barrel Snib's barrel: its fuse spitting while its circle is marked;
///   a pit      where "the ground goes": it caves in (dust, rubble) and a black hole stays;
///   the crack  where "the crack opens": a long dark fissure across the ground, embers far down in it.
///
/// Combat's hooks: GrimtunnelStory.Under; the blows' labels ("A tub", "The barrel", "The ground
/// goes", "The crack opens"); a pit's lasting mark is a Wall circle held for minutes.
/// </summary>
public partial class BattleFx
{
    /// <summary>The boss's script this frame, if any (Game sets it): for looks that read its state.</summary>
    public object? Boss;

    readonly Dictionary<int, Decal> holes = new();
    readonly List<(Vector3 From, Vector3 To, float T)> tubRuns = new();
    readonly List<(Vector3 At, float Left)> fuses = new();
    Node3D[]? tubPool;
    static Texture2D? holeTex, fissureTex;
    Vector3 lastUnder;
    float underScar;
    double underShot;
    float tubTest = 1.5f;

    /// <summary>A Dig look for this telegraph, drawn instead of (or as well as) its mark: false to
    /// draw the mark as usual.</summary>
    bool DigMark(Ev.Telegraph e)
    {
        if (!e.Hostile) return false;
        // A pit's lasting mark: a black hole in the ground (its grey ring said "wall", not "hole").
        if (e.Kind == TelegraphKind.Wall && e.Shape == TelegraphShape.Circle && e.Label == null && e.Id >= 900000)
        {
            if (holes.Remove(e.Id, out var old)) old.QueueFree();
            if (e.Radius < 0.05 || e.Duration < 0.05) return true;
            holes[e.Id] = Hole(e.X, e.Z, (float)e.Radius);
            return true;
        }
        double x = e.X, z = e.Z, life = e.Duration;
        switch (e.Label)
        {
            case "The ground goes":
                pending.Add((time + life, () => CaveIn(x, z, (float)e.Radius)));
                if (Shots.On("boss")) Shots.Want("cavein", life + 0.3);
                return false;
            case "The crack opens" when e.X1 is double x1 && e.Z1 is double z1:
                pending.Add((time + life, () => Fissure(x, z, x1, z1, (float)(e.Width ?? 4))));
                if (Shots.On("boss")) Shots.Want("fissure", life + 0.35);
                return false;
            case "A tub" when e.X1 is double tx1 && e.Z1 is double tz1:
                pending.Add((time + life, () => tubRuns.Add((V(x, Y(x, z), z), V(tx1, Y(tx1, tz1), tz1), 0))));
                if (Shots.On("boss")) { Shots.Want("tubrun", life + 0.12); Shots.Want("tubrun", life + 0.3); }
                return false;
            case "The barrel":
                fuses.Add((V(x, Y(x, z) + 0.95, z), (float)life));
                if (Shots.On("boss")) Shots.Want("fuse", life * 0.5);
                return false;
        }
        return false;
    }

    /// <summary>Each frame: Grimtunnel's mound, the tubs on their rails, the fuses.</summary>
    void StepDig(float dt)
    {
        CrowdView.Under ??= e => Boss is GrimtunnelStory { Under: true } gu && gu.E == e;
        if (Boss is GrimtunnelStory { Under: true } g && g.E is { Alive: true } ge)
        {
            var at = V(ge.X, Y(ge.X, ge.Z), ge.Z);
            var heading = new Vector3((float)ge.Vx, 0, (float)ge.Vz);
            if (heading.LengthSquared() < 0.01f) heading = at - lastUnder;
            heading.Y = 0;
            var fwd = heading.LengthSquared() > 1e-4f ? heading.Normalized() : Vector3.Forward;
            if (Shots.On("boss") && time > underShot) { underShot = time + 2.5; Shots.Want("under", 0.05); }
            // The earth heaving up ahead of him, clods and dust thrown off the mound.
            if (dt > 0)
            {
                for (int i = 0; i < 3; i++)
                {
                    var side = new Vector3(-fwd.Z, 0, fwd.X) * (R() - 0.5f) * 1.2f;
                    Smoke.Spawn(at + fwd * 0.6f + side + Vector3.Up * 0.15f, fwd * (1 + R()) + side * 2 + Vector3.Up * (2 + R() * 2.5f), 0.55f, 0.07f + R() * 0.07f,
                        new Color("#3e3024"), gravity: 12, sprite: Sprites.Of("dirt"), spinV: 5);
                }
                if (R() < 0.5f)
                    Smoke.Spawn(at + Vector3.Up * 0.2f, Vector3.Up * 0.4f - fwd * 0.5f, 0.9f, 0.5f, new Color(0.3f, 0.25f, 0.2f), new Color(0.2f, 0.17f, 0.14f), 1.1f, drag: 1.5f, alpha: 0.35f);
            }
            // The ground left broken behind him, a crack every stride.
            underScar += (at - lastUnder).Length();
            if (underScar > 0.7f && (at - lastUnder).Length() < 3) { underScar = 0; Scars.Add("crack", at, 0.75f, 6f, 0); }
            if (Cam != null && R() < 0.2f) Cam.AddTrauma(0.03f);
            lastUnder = at;
            // The mound itself: the earth heaved up round his back and ahead of him, breathing as he digs.
            mound ??= Mound();
            mound.Visible = true;
            float heave = 1 + 0.07f * Mathf.Sin((float)time * 9);
            mound.GlobalTransform = new Transform3D(new Godot.Basis(Vector3.Up, Mathf.Atan2(fwd.X, fwd.Z)) * Godot.Basis.FromScale(new Vector3(1.15f, 0.75f * heave, 1.6f)), at + fwd * 0.45f - Vector3.Up * 0.08f);
        }
        else if (mound != null) mound.Visible = false;
        // The tubs on their rails. (--tubs: one run past her every three seconds, a picture of a tub anywhere.)
        if (tubPool == null) MakeTubs();
        if (Args.Has("tubs") && (tubTest -= dt) <= 0)
        {
            tubTest = 3;
            var c = PlayerPos;
            tubRuns.Add((V(c.X - 14, Y(c.X - 14, c.Z + 2.5), c.Z + 2.5), V(c.X + 14, Y(c.X + 14, c.Z + 2.5), c.Z + 2.5), 0));
            if (Shots.On("boss")) for (int i = 0; i < 6; i++) Shots.Want("tubtest", 0.6 + i * 0.12);
        }
        int used = 0;
        for (int i = tubRuns.Count - 1; i >= 0; i--)
        {
            var (from, to, t) = tubRuns[i];
            float len = Mathf.Max(1, (to - from).Length());
            t += dt * 16 / len;
            if (t >= 1) { tubRuns.RemoveAt(i); continue; }
            tubRuns[i] = (from, to, t);
            var at = from.Lerp(to, t);
            at.Y = Y(at.X, at.Z);
            var dir = (to - from).Normalized();
            if (used < tubPool!.Length)
            {
                var tub = tubPool[used++];
                tub.Visible = true;
                tub.GlobalTransform = new Transform3D(new Godot.Basis(Vector3.Up, Mathf.Atan2(dir.X, dir.Z)), at + Vector3.Up * (0.1f + 0.025f * Mathf.Sin(t * 60)));
            }
            // Sparks off its wheels on the rail, grit thrown, the rails' rumble.
            if (dt > 0)
            {
                var side = new Vector3(-dir.Z, 0, dir.X);
                for (int k = 0; k < 2; k++)
                {
                    var wheel = at + side * (k == 0 ? -0.5f : 0.5f) - dir * 0.45f + Vector3.Up * 0.12f;
                    Sparks.Spawn(wheel, -dir * (3 + R() * 4) + side * (R() - 0.5f) * 2 + Vector3.Up * (1 + R() * 2), 0.2f + R() * 0.15f, 0.035f, new Color(2.2f, 1.1f, 0.3f), new Color(1.2f, 0.3f, 0.05f), 0.01f, 9, 2);
                }
                if (R() < 0.4f) Smoke.Spawn(at - dir * 0.7f + Vector3.Up * 0.2f, -dir * 1.5f + Vector3.Up * 0.5f, 0.6f, 0.3f, new Color(0.32f, 0.27f, 0.22f), new Color(0.2f, 0.17f, 0.14f), 0.8f, drag: 2, alpha: 0.3f);
                if (Cam != null && R() < 0.15f) Cam.AddTrauma(0.025f);
            }
        }
        for (int i = used; i < tubPool!.Length; i++) tubPool[i].Visible = false;
        // Fuses spitting.
        for (int i = fuses.Count - 1; i >= 0; i--)
        {
            var (at, left) = fuses[i];
            left -= dt;
            if (left <= 0) { fuses.RemoveAt(i); continue; }
            fuses[i] = (at, left);
            if (dt > 0)
                for (int k = 0; k < 2; k++)
                    Sparks.Spawn(at, new Vector3((R() - 0.5f) * 2.5f, 1.5f + R() * 2.5f, (R() - 0.5f) * 2.5f), 0.25f + R() * 0.2f, 0.03f + R() * 0.02f, new Color(2.4f, 1.3f, 0.35f), new Color(1.3f, 0.3f, 0.05f), 0.01f, 7, 1.5f);
            if (dt > 0 && R() < 0.3f) Sparks.Spawn(at, Vector3.Zero, 0.06f, 0.3f, new Color(1.6f, 0.8f, 0.2f), null, 0.15f, sprite: Sprites.Of("flare"));
        }
    }

    /// <summary>Where the ground goes: it caves in with a breath of dust and rubble thrown up.</summary>
    void CaveIn(double x, double z, float r)
    {
        var g = V(x, Y(x, z), z);
        for (int i = 0; i < 16; i++)
        {
            float a = R() * Mathf.Tau, d = r * Mathf.Sqrt(R()) * 0.9f;
            var at = g + new Vector3(Mathf.Cos(a) * d, 0.2f, Mathf.Sin(a) * d);
            Smoke.Spawn(at, new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a)) * -1.5f + Vector3.Up * (1.5f + R() * 2.5f), 0.6f, 0.08f + R() * 0.08f, new Color("#3a2e22"), gravity: 14, sprite: Sprites.Of("dirt"), spinV: 5);
        }
        for (int i = 0; i < 8; i++)
        {
            float a = i / 8f * Mathf.Tau;
            var dir = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
            Smoke.Spawn(g + dir * r * 0.6f + Vector3.Up * 0.3f, dir * 1.2f + Vector3.Up * 0.8f, 1.1f, r * 0.3f, new Color(0.34f, 0.28f, 0.22f), new Color(0.22f, 0.18f, 0.15f), r * 0.6f, drag: 1.6f, alpha: 0.4f);
        }
        Scars.Add("crack", g, r * 1.1f, 8f, 0);
        Cam?.AddTrauma(0.2f);
    }

    /// <summary>The crack opening: a long dark fissure where it was marked, rubble going in, and
    /// embers far down in it.</summary>
    void Fissure(double x0, double z0, double x1, double z1, float width)
    {
        fissureTex ??= FissureTexture();
        var a = V(x0, Y(x0, z0), z0);
        var b = V(x1, Y(x1, z1), z1);
        var d = new Decal
        {
            TextureAlbedo = fissureTex, TextureEmission = fissureTex, AlbedoMix = 1, Modulate = new Color(0.05f, 0.035f, 0.03f), EmissionEnergy = 0.9f,
            UpperFade = 0.3f, LowerFade = 0.4f, CullMask = 1, Size = new Vector3(width * 0.95f, 4, Mathf.Max(1, (b - a).Length())),
        };
        AddChild(d);
        d.Position = (a + b) / 2;
        d.Rotation = new Vector3(0, Mathf.Atan2(b.X - a.X, b.Z - a.Z), 0);
        holes[700000 + holes.Count] = d;
        int n = (int)((b - a).Length() / 0.8f);
        for (int i = 0; i <= n; i++)
        {
            var at = a.Lerp(b, i / (float)Math.Max(1, n));
            for (int k = 0; k < 2; k++)
                Smoke.Spawn(at + Vector3.Up * 0.2f, new Vector3((R() - 0.5f) * 2, 1.5f + R() * 2, (R() - 0.5f) * 2), 0.55f, 0.07f + R() * 0.07f, new Color("#3a2e22"), gravity: 14, sprite: Sprites.Of("dirt"), spinV: 5);
            Smoke.Spawn(at + Vector3.Up * 0.3f, Vector3.Up * 0.6f, 1.2f, 0.7f, new Color(0.33f, 0.27f, 0.21f), new Color(0.2f, 0.17f, 0.14f), 1.4f, drag: 1.4f, alpha: 0.35f);
        }
        Cam?.AddTrauma(0.35f);
    }

    /// <summary>A black hole in the ground, `r` across its mouth, left as long as its mark stands.</summary>
    Decal Hole(double x, double z, float r)
    {
        holeTex ??= HoleTexture();
        var d = new Decal
        {
            TextureAlbedo = holeTex, AlbedoMix = 1, Modulate = new Color(0.04f, 0.03f, 0.025f),
            UpperFade = 0.3f, LowerFade = 0.4f, CullMask = 1, Size = new Vector3(r * 2.3f, 4, r * 2.3f),
        };
        AddChild(d);
        d.Position = V(x, Y(x, z), z);
        d.Rotation = new Vector3(0, R() * Mathf.Tau, 0);
        return d;
    }

    /// <summary>A hole's mouth: black and soft at its heart, its edge broken (ragged, never a circle).</summary>
    static Texture2D HoleTexture()
    {
        const int N = 192;
        var img = Image.CreateEmpty(N, N, true, Image.Format.Rgba8);
        var noise = new FastNoiseLite { Seed = 7, Frequency = 0.035f, FractalOctaves = 4 };
        for (int y = 0; y < N; y++)
            for (int x = 0; x < N; x++)
            {
                float u = (x + 0.5f) / N * 2 - 1, v = (y + 0.5f) / N * 2 - 1;
                float r = Mathf.Sqrt(u * u + v * v);
                float edge = 0.78f + 0.12f * noise.GetNoise2D(x, y);
                float a = 1 - Mathf.SmoothStep(edge - 0.08f, edge + 0.04f, r);
                // Darkest at its heart: a lip of broken ground, then the dark going down.
                float lip = Mathf.SmoothStep(edge - 0.3f, edge, r) * 0.5f;
                float c = 0.05f + lip;
                img.SetPixel(x, y, new Color(c, c * 0.85f, c * 0.7f, Mathf.Clamp(a, 0, 1)));
            }
        img.GenerateMipmaps();
        return ImageTexture.CreateFromImage(img);
    }

    /// <summary>A fissure along v: dark, its sides jagged, a thread of embers deep in its middle
    /// (as emission: only the middle is lit).</summary>
    static Texture2D FissureTexture()
    {
        const int W = 96, H = 512;
        var img = Image.CreateEmpty(W, H, true, Image.Format.Rgba8);
        var noise = new FastNoiseLite { Seed = 11, Frequency = 0.04f, FractalOctaves = 4 };
        for (int y = 0; y < H; y++)
            for (int x = 0; x < W; x++)
            {
                float u = Mathf.Abs((x + 0.5f) / W * 2 - 1), v = (y + 0.5f) / H;
                float half = 0.62f + 0.22f * noise.GetNoise2D(0, y * 1.5f) + 0.08f * noise.GetNoise2D(x * 3, y * 3);
                float ends = Mathf.SmoothStep(0, 0.06f, v) * Mathf.SmoothStep(1, 0.94f, v);
                float a = (1 - Mathf.SmoothStep(half - 0.1f, half + 0.05f, u)) * ends;
                float glow = Mathf.Clamp(1 - u / 0.12f, 0, 1) * (0.5f + 0.5f * noise.GetNoise2D(5, y * 4)) * ends;
                // Albedo near black; the red channel carries the embers for the emission.
                img.SetPixel(x, y, new Color(0.05f + glow * 0.9f, 0.04f + glow * 0.3f, 0.03f + glow * 0.05f, Mathf.Clamp(a, 0, 1)));
            }
        img.GenerateMipmaps();
        return ImageTexture.CreateFromImage(img);
    }

    MeshInstance3D? mound;
    static readonly Dictionary<string, Texture2D?> digLayers = new();

    /// <summary>One layer of the Dig's ground (arena art's texture arrays: 0 clay, 1 spoil, ...), as a
    /// plain texture for a thing made of the same earth.</summary>
    static Texture2D? DigLayer(string map, int layer)
    {
        string key = map + layer;
        if (digLayers.TryGetValue(key, out var t)) return t;
        var arr = GD.Load<Resource>($"res://art/arena/dig/{map}.jpg") as TextureLayered;
        var img = arr != null && layer < arr.GetLayers() ? arr.GetLayerData(layer) : null;
        return digLayers[key] = img != null ? ImageTexture.CreateFromImage(img) : null;
    }

    /// <summary>Grimtunnel's mound: a low dome of broken earth, clods standing proud of it (its
    /// faces lumpy, its colour the Dig's dirt, darker where it is freshly turned).</summary>
    MeshInstance3D Mound()
    {
        // The Dig's own dirt (arena art's), a shade darker: freshly turned earth is damp. (Its own
        // dark noise read as a black disc on the lit ground.)
        var mat = new StandardMaterial3D
        {
            AlbedoTexture = DigLayer("albedo", 0), AlbedoColor = new Color(0.82f, 0.78f, 0.74f),
            NormalEnabled = true, NormalTexture = new NoiseTexture2D { Width = 128, Height = 128, Seamless = true, AsNormalMap = true, BumpStrength = 5, Noise = new FastNoiseLite { Seed = 9, Frequency = 0.08f, FractalOctaves = 3 } },
            // (the clay layer is laid four metres to a tile, as the ground lays it: layers.json)
            Uv1Triplanar = true, Uv1WorldTriplanar = true, Uv1Scale = new Vector3(0.25f, 0.25f, 0.25f), Roughness = 0.95f,
        };
        var m = new MeshInstance3D { Mesh = new SphereMesh { Radius = 1, Height = 1.2f, RadialSegments = 14, Rings = 7 }, MaterialOverride = mat, Visible = false };
        // Clods proud of it.
        var rng = new Random(3);
        for (int i = 0; i < 9; i++)
        {
            float a = (float)rng.NextDouble() * Mathf.Tau, d = 0.5f + (float)rng.NextDouble() * 0.45f;
            m.AddChild(new MeshInstance3D
            {
                Mesh = new SphereMesh { Radius = 0.18f, Height = 0.26f, RadialSegments = 5, Rings = 3 }, MaterialOverride = mat,
                Position = new Vector3(Mathf.Cos(a) * d, 0.45f - d * 0.3f, Mathf.Sin(a) * d),
                Rotation = new Vector3((float)rng.NextDouble() * 3, (float)rng.NextDouble() * 3, 0),
                Scale = Vector3.One * (0.7f + (float)rng.NextDouble() * 0.8f),
            });
        }
        AddChild(m);
        return m;
    }

    /// <summary>The Dig's iron tubs: a few, reused (MineTub).</summary>
    void MakeTubs()
    {
        tubPool = new Node3D[4];
        for (int i = 0; i < tubPool.Length; i++)
        {
            var tub = MineTub.Make(17 + i * 7);
            tub.Visible = false;
            AddChild(tub);
            tubPool[i] = tub;
        }
    }
}
