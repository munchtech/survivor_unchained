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
        ["fire_blast"] = (0.45f, 0.5f), ["fire_loop"] = (0.85f, 0.4f), ["frost_burst"] = (0.7f, 0.5f),
        ["storm_strike"] = (1f, 0.3f), ["holy_burst"] = (0.95f, 0.5f), ["shadow_burst"] = (0.35f, 0.5f),
        ["nature_burst"] = (0.85f, 0.5f), ["blood_burst"] = (0f, 0.3f), ["dust_ring"] = (0f, 0.6f),
        ["smoke_puff"] = (0f, 0.8f), ["sparks"] = (1f, 0.2f), ["ember_motes"] = (1f, 0.3f), ["arcane_burst"] = (0.9f, 0.5f),
    };

    struct Play
    {
        public Vector3 At, V;
        public float Size, SizeEnd, Life, Age, Angle, Spin, Fade;
        public Color Tint;
        public bool Flat;
    }

    sealed class Book
    {
        public required MultiMeshInstance3D Node;
        public readonly List<Play> Plays = new();
        public float[] Buffer = new float[64 * Stride];
    }

    const int Stride = 20;
    readonly Dictionary<string, Book?> books = new();

    public Flipbooks() { Name = "Flipbooks"; }

    public static bool Has(string name) => FileAccess.FileExists($"res://art/fx/fb/{name}.json");

    Book? Of(string name)
    {
        if (books.TryGetValue(name, out var b)) return b;
        if (!Has(name)) { books[name] = null; return null; }
        var meta = Core.Json.Parse<Dictionary<string, object>>(FileAccess.GetFileAsString($"res://art/fx/fb/{name}.json"));
        int grid = System.Convert.ToInt32(meta["grid"].ToString()), frames = System.Convert.ToInt32(meta["frames"].ToString());
        var mat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/flipbook.gdshader") };
        mat.SetShaderParameter("atlas", GD.Load<Texture2D>($"res://art/fx/fb/{name}.png"));
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
        b = new Book { Node = node };
        books[name] = b;
        return b;
    }

    /// <summary>Play an atlas once at `at`: `size` across growing to
    /// `sizeEnd`, over `life` seconds, tinted (rgb above 1 blooms), flat on
    /// the ground or facing the camera, drifting with `v`. False if there is
    /// no such atlas (the caller falls back to what it drew before).</summary>
    public bool Spawn(string name, Vector3 at, float size, float life, Color tint, bool flat = false, float sizeEnd = -1, float angle = float.NaN, float spin = 0, Vector3 v = default)
    {
        var b = Of(name);
        if (b == null) return false;
        if (b.Plays.Count >= 512) return true;
        b.Plays.Add(new Play
        {
            At = at, V = v, Size = size, SizeEnd = sizeEnd < 0 ? size : sizeEnd, Life = Mathf.Max(0.05f, life), Tint = tint, Flat = flat,
            Angle = float.IsNaN(angle) ? Sparks.R() * Mathf.Tau : angle, Spin = spin, Fade = 1,
        });
        return true;
    }

    public void Step(float dt)
    {
        foreach (var b in books.Values)
        {
            if (b == null) continue;
            var plays = b.Plays;
            int n = 0;
            for (int i = 0; i < plays.Count; i++)
            {
                var p = plays[i];
                p.Age += dt;
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
                float k = p.Age / p.Life;
                // Grows fast at first and settles, as a burst does.
                float s = Mathf.Lerp(p.Size, p.SizeEnd, 1 - (1 - k) * (1 - k));
                int o = i * Stride;
                var buf = b.Buffer;
                buf[o] = s; buf[o + 1] = 0; buf[o + 2] = 0; buf[o + 3] = p.At.X;
                buf[o + 4] = 0; buf[o + 5] = s; buf[o + 6] = 0; buf[o + 7] = p.At.Y;
                buf[o + 8] = 0; buf[o + 9] = 0; buf[o + 10] = s; buf[o + 11] = p.At.Z;
                // Every take fades over its last quarter, whether or not the clip did.
                float fade = p.Tint.A * (k < 0.75f ? 1 : 1 - (k - 0.75f) / 0.25f);
                buf[o + 12] = p.Tint.R; buf[o + 13] = p.Tint.G; buf[o + 14] = p.Tint.B; buf[o + 15] = fade;
                buf[o + 16] = k; buf[o + 17] = p.Angle; buf[o + 18] = p.Flat ? 1 : 0; buf[o + 19] = 0;
            }
            // Only what is live is sent; the rest of the buffer is left as it was.
            if (n > 0) mm.Buffer = b.Buffer;
            mm.VisibleInstanceCount = n;
        }
    }
}
