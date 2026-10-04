using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// What a blow leaves on the ground (art/fx/marks, painted by Krea and
/// keyed by tools/comfy/marks.py): scorch, a cracked crater, blight, frost,
/// a seared sigil, arcane runes, spectral roots. Each is a decal over the
/// ground and what stands low on it; it comes in at once, holds, and fades,
/// its glow cooling well before the mark itself goes (embers die before the
/// char does). Oldest reused first.
/// </summary>
public partial class Scars : Node3D
{
    /// <summary>How each mark burns: its glow's strength, and how much of its
    /// life the glow lasts.</summary>
    static readonly Dictionary<string, (float Glow, float GlowShare)> Looks = new()
    {
        ["scorch"] = (5f, 0.35f), ["crack"] = (0f, 0f), ["blight"] = (0.6f, 0.5f), ["frost"] = (0.5f, 0.4f),
        // A sigil burns gold, not white: brighter, past the tone curve's knee, it read as peach.
        ["sigil"] = (1.5f, 0.7f), ["runes"] = (1.6f, 0.7f), ["roots"] = (4f, 0.7f),
    };

    /// <summary>How far each mark covers the ground: the dark ones less, or
    /// under moonlight they read as holes of ink.</summary>
    static readonly Dictionary<string, float> Strengths = new() { ["blight"] = 0.55f, ["scorch"] = 0.7f, ["crack"] = 0.8f, ["frost"] = 0.4f };

    sealed class Scar
    {
        public required Decal Decal;
        public float T = 1, Life, Glow, GlowShare, Spin, Strength = 0.85f;
    }

    readonly List<Scar> pool = new();
    readonly Dictionary<string, (Texture2D Albedo, Texture2D Emit)> textures = new();
    int next;
    const int Max = 48;

    public Scars() { Name = "Scars"; }

    (Texture2D, Texture2D)? Of(string name)
    {
        if (textures.TryGetValue(name, out var t)) return t;
        string a = $"res://art/fx/marks/{name}.png", e = $"res://art/fx/marks/{name}_emit.png";
        if (!ResourceLoader.Exists(a)) return null;
        t = (GD.Load<Texture2D>(a), GD.Load<Texture2D>(e));
        textures[name] = t;
        return t;
    }

    /// <summary>A mark `radius` across at `at` for `life` seconds, turned at
    /// random, spinning slowly if `spin` (a sigil turning as it fades).</summary>
    public void Add(string name, Vector3 at, float radius, float life, float spin = 0)
    {
        if (Of(name) is not var (albedo, emit)) return;
        Scar s;
        if (pool.Count < Max)
        {
            s = new Scar { Decal = new Decal { UpperFade = 0.25f, LowerFade = 0.4f, CullMask = 1, NormalFade = 0.3f } };
            AddChild(s.Decal);
            pool.Add(s);
        }
        else s = pool[next++ % Max];
        var (glow, share) = Looks.TryGetValue(name, out var l) ? l : (1f, 0.5f);
        var d = s.Decal;
        d.TextureAlbedo = albedo;
        d.TextureEmission = emit;
        d.EmissionEnergy = glow;
        // The dark marks lie over the ground's own colour rather than
        // replacing it: under the moon pure char reads as a hole.
        d.AlbedoMix = name is "scorch" or "crack" or "blight" ? 0.7f : 1f;
        d.Position = at;
        d.Rotation = new Vector3(0, Sparks.R() * Mathf.Tau, 0);
        d.Size = new Vector3(radius * 2, 3, radius * 2);
        d.Modulate = Colors.White;
        d.Visible = true;
        s.T = 0; s.Life = Mathf.Max(0.2f, life); s.Glow = glow; s.GlowShare = share; s.Spin = spin;
        s.Strength = Strengths.TryGetValue(name, out var k) ? k : 0.85f;
    }

    public void Step(float dt)
    {
        foreach (var s in pool)
        {
            if (s.T >= 1) continue;
            s.T += dt / s.Life;
            if (s.T >= 1) { s.Decal.Visible = false; continue; }
            // In over the first instant, out over the last third.
            float a = s.Strength * Mathf.Min(1, s.T * 25) * (s.T < 0.67f ? 1 : 1 - (s.T - 0.67f) / 0.33f);
            s.Decal.Modulate = new Color(1, 1, 1, a);
            float g = s.GlowShare <= 0 ? 0 : Mathf.Clamp(1 - s.T / s.GlowShare, 0, 1);
            s.Decal.EmissionEnergy = s.Glow * g * g;
            if (s.Spin != 0) s.Decal.Rotation += new Vector3(0, s.Spin * dt, 0);
        }
    }
}
