using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// Effects filmed and cut into atlases (art/fx/fb/NAME.png with NAME.json,
/// made by tools/comfy/fx_clips.py and tools/comfy/flipbook.py): each plays
/// once over its life, lying flat on the ground or facing the camera
/// (shaders/flipbook.gdshader). One instanced batch per atlas, stepped with
/// the fight's own clock so hitstop and pause hold them too.
/// </summary>
public partial class Flipbooks : Node3D
{
    /// <summary>How each atlas is drawn: how additive (1 light, 0 smoke laid
    /// over the world) and how softly it meets the ground.</summary>
    static readonly Dictionary<string, (float Add, float Soft)> Looks = new()
    {
        // The pale schools are drawn less as light and more as colour laid
        // over the ground: added, their bright clips burn to white in the bloom.
        ["fire_blast"] = (0.45f, 0.5f), ["fire_loop"] = (0.85f, 0.4f), ["frost_burst"] = (0.3f, 0.5f),
        ["storm_strike"] = (0.7f, 0.3f), ["holy_burst"] = (0.55f, 0.5f), ["shadow_burst"] = (0.3f, 0.5f),
        ["nature_burst"] = (0.6f, 0.5f), ["blood_burst"] = (0f, 0.3f), ["blood_splat"] = (0f, 0.3f), ["blood_spray"] = (0f, 0.3f),
        // Shadow's wisps drink the light: dark laid over the world, a little glow of their own.
        ["shadow_wisps"] = (0.12f, 0.5f),
        ["dust_ring"] = (0f, 0.6f), ["lc_dust"] = (0f, 0.6f), ["smoke_puff"] = (0f, 0.8f), ["sparks"] = (1f, 0.2f), ["ember_motes"] = (1f, 0.3f), ["arcane_burst"] = (0.6f, 0.5f),
        // Not Yet's watch dial (one painted frame): light only.
        ["watch_dial"] = (1f, 0f),
    };

    struct Play
    {
        public Vector3 At, V;
        public float Size, SizeEnd, Life, Age, Angle, Spin, Fade, Tall;
        public Color Tint;
        public bool Flat;
    }

    sealed class Book
    {
        public required MultiMeshInstance3D Node;
        public required ShaderMaterial Mat;
        /// <summary>The atlas's path while it is still being read on the loader's threads (null once it is in).</summary>
        public string? Waiting;
        public ulong AskedMs;
        public readonly List<Play> Plays = new();
        public float[] Buffer = new float[64 * Stride];
    }

    const int Stride = 20;
    readonly Dictionary<string, Book?> books = new();

    public Flipbooks() { Name = "Flipbooks"; }

    // The shader readied with a first material as the first fight's effects stand up (making it is the costly part).
    // Each atlas is read on the loader's threads when it is first wanted (Want, or its first Spawn), never on the main
    // thread: read there on its first use, the first level-up's blast held its frame 30-90 ms (MR4). A take spawned
    // before its atlas is in waits, unaged and undrawn, and then plays whole. Every atlas used to be read ahead at the
    // first fight and kept: 106 MB of video memory, of which a den run used 2 atlases (lc_dust, smoke_puff; the tester
    // lane, 24 Nov). Kept for the game's life once read (5.3 MB each).
    static Shader? shader;
    static readonly Dictionary<string, Texture2D?> atlases = new();
    static readonly HashSet<string> asked = new();
    static readonly bool fbLog = Args.Has("fb-log");

    static string AtlasPath(string name) => $"res://art/fx/fb/{name}.png";

    public override void _Ready()
    {
        if (shader != null) return;
        shader = GD.Load<Shader>("res://shaders/flipbook.gdshader");
        // (the shader's first material made here, off the fight: making it is the costly part)
        _ = new ShaderMaterial { Shader = shader };
    }

    /// <summary>Start reading an atlas on the loader's threads ahead of its first take (a caller that knows it is coming).</summary>
    public static void Want(string name)
    {
        if (atlases.ContainsKey(name)) return;
        var path = AtlasPath(name);
        if (asked.Contains(path) || !ResourceLoader.Exists(path)) return;
        if (ResourceLoader.LoadThreadedRequest(path) == Error.Ok) asked.Add(path);
    }

    /// <summary>The atlas if it is in (taken from the loader when its read is done); null while it is still being read.</summary>
    static Texture2D? Ready(string name, out bool failed)
    {
        failed = false;
        if (atlases.TryGetValue(name, out var t)) { failed = t == null; return t; }
        var path = AtlasPath(name);
        if (!asked.Contains(path)) Want(name);
        if (!asked.Contains(path)) { failed = true; return atlases[name] = null; }
        var st = ResourceLoader.LoadThreadedGetStatus(path);
        if (st == ResourceLoader.ThreadLoadStatus.InProgress) return null;
        asked.Remove(path);
        t = st == ResourceLoader.ThreadLoadStatus.Loaded ? ResourceLoader.LoadThreadedGet(path) as Texture2D : null;
        failed = t == null;
        return atlases[name] = t;
    }

    /// <summary>(MemLog's census) the atlases taken so far this game, of those on disk.</summary>
    public static string UsedReport() => $"{atlases.Count} atlases read ({asked.Count} still being read): {string.Join(",", atlases.Keys)}";

    public static bool Has(string name) => FileAccess.FileExists($"res://art/fx/fb/{name}.json");

    Book? Of(string name)
    {
        if (books.TryGetValue(name, out var b)) return b;
        if (!Has(name)) { books[name] = null; return null; }
        var meta = Core.Json.Parse<Dictionary<string, object>>(FileAccess.GetFileAsString($"res://art/fx/fb/{name}.json"));
        int grid = System.Convert.ToInt32(meta["grid"].ToString()), frames = System.Convert.ToInt32(meta["frames"].ToString());
        var mat = new ShaderMaterial { Shader = shader ??= GD.Load<Shader>("res://shaders/flipbook.gdshader") };
        Want(name);
        mat.SetShaderParameter("grid", grid);
        mat.SetShaderParameter("frames", frames);
        var (add, soft) = Looks.TryGetValue(name, out var l) ? l : (0.7f, 0.5f);
        mat.SetShaderParameter("add", add);
        mat.SetShaderParameter("soft", soft);
        var node = new MultiMeshInstance3D
        {
            Name = name, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off,
            CustomAabb = new Aabb(new Vector3(-1e4f, -1e4f, -1e4f), new Vector3(2e4f, 2e4f, 2e4f)),
            Multimesh = new MultiMesh
            {
                TransformFormat = MultiMesh.TransformFormatEnum.Transform3D, UseColors = true, UseCustomData = true,
                InstanceCount = 64, VisibleInstanceCount = 0, Mesh = new QuadMesh { Size = Vector2.One, Material = mat },
            },
        };
        AddChild(node);
        b = new Book { Node = node, Mat = mat, Waiting = name, AskedMs = Time.GetTicksMsec() };
        books[name] = b;
        return b;
    }

    /// <summary>Play an atlas once at `at`: `size` across growing to
    /// `sizeEnd`, over `life` seconds, tinted (rgb above 1 blooms), flat on
    /// the ground or facing the camera, drifting with `v`. False if there is
    /// no such atlas (the caller falls back to what it drew before).
    /// `tall` above 1: a camera-facing take stretched that many times up the
    /// screen (a jet), its foot lit warm from below over its first half-life.</summary>
    public bool Spawn(string name, Vector3 at, float size, float life, Color tint, bool flat = false, float sizeEnd = -1, float angle = float.NaN, float spin = 0, Vector3 v = default, float tall = 0, float delay = 0)
    {
        var b = Of(name);
        if (b == null) return false;
        if (b.Plays.Count >= 512) return true;
        b.Plays.Add(new Play
        {
            At = at, V = v, Size = size, SizeEnd = sizeEnd < 0 ? size : sizeEnd, Life = Mathf.Max(0.05f, life), Tint = tint, Flat = flat,
            Angle = float.IsNaN(angle) ? Sparks.R() * Mathf.Tau : angle, Spin = spin, Fade = 1, Tall = tall, Age = -Mathf.Max(0, delay),
        });
        return true;
    }

    /// <summary>True once the book's atlas is in and set (or failed: its takes are then dropped).</summary>
    bool Take(Book b)
    {
        var t = Ready(b.Waiting!, out bool failed);
        if (t == null && !failed) return false;
        if (fbLog) GD.Print($"flipbook {b.Waiting}: atlas {(failed ? "FAILED" : "in")} {Time.GetTicksMsec() - b.AskedMs} ms after its first want, frame {Engine.GetFramesDrawn()}, {b.Plays.Count} takes waited");
        if (failed) b.Plays.Clear(); else b.Mat.SetShaderParameter("atlas", t);
        b.Waiting = null;
        return !failed;
    }

    public void Step(float dt)
    {
        foreach (var b in books.Values)
        {
            if (b == null) continue;
            // (its atlas still being read: its takes wait, unaged and undrawn)
            if (b.Waiting != null && !Take(b)) continue;
            var plays = b.Plays;
            int n = 0;
            for (int i = 0; i < plays.Count; i++)
            {
                var p = plays[i];
                p.Age += dt;
                if (p.Age < 0) { plays[n++] = p; continue; }
                if (p.Age >= p.Life) continue;
                p.At += p.V * dt;
                p.Angle += p.Spin * dt;
                plays[n++] = p;
            }
            plays.RemoveRange(n, plays.Count - n);
            var mm = b.Node.Multimesh;
            if (n > mm.InstanceCount)
            {
                mm.InstanceCount = Mathf.NearestPo2(n);
                b.Buffer = new float[mm.InstanceCount * Stride];
            }
            for (int i = 0; i < n; i++)
            {
                var p = plays[i];
                float k = Mathf.Max(0, p.Age) / p.Life;
                // Grows fast at first and settles, as a burst does.
                float s = Mathf.Lerp(p.Size, p.SizeEnd, 1 - (1 - k) * (1 - k));
                int o = i * Stride;
                var buf = b.Buffer;
                buf[o] = s; buf[o + 1] = 0; buf[o + 2] = 0; buf[o + 3] = p.At.X;
                buf[o + 4] = 0; buf[o + 5] = s; buf[o + 6] = 0; buf[o + 7] = p.At.Y;
                buf[o + 8] = 0; buf[o + 9] = 0; buf[o + 10] = s; buf[o + 11] = p.At.Z;
                // Every take fades over its last quarter, whether or not the clip did.
                float fade = (p.Age < 0 ? 0 : p.Tint.A) * (k < 0.75f ? 1 : 1 - (k - 0.75f) / 0.25f);
                buf[o + 12] = p.Tint.R; buf[o + 13] = p.Tint.G; buf[o + 14] = p.Tint.B; buf[o + 15] = fade;
                buf[o + 16] = k; buf[o + 17] = p.Angle; buf[o + 18] = p.Flat ? 1 : 0; buf[o + 19] = p.Tall;
            }
            // Only what is live is sent; the rest of the buffer is left as it was.
            if (n > 0) mm.Buffer = b.Buffer;
            mm.VisibleInstanceCount = n;
        }
    }
}
