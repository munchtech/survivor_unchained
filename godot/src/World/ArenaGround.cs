using System.Collections.Generic;
using System.Text.Json;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// An ember arena's ground: its place's seven photoscanned materials
/// (art/arena/PLACE, tools/godot/arena_ground.py) through
/// shaders/arena_ground.gdshader, painted by the arena's two paints.
/// Each photograph is brought into the place's own light here (Tones), and
/// the whole ground held below the living (Value, Sat): the creatures, the
/// dead and the survivor must all read against it from thirty metres up.
/// </summary>
public static class ArenaGround
{
    /// <summary>What each layer is brought to, place by place, in the layers'
    /// order (tools/godot/arena_ground.py): its mean albedo in linear light (Y)
    /// and how much of its colour it keeps (Sat). The scans were shot on days
    /// of every brightness, from 0.01 (a black rock) to 0.4 (sunlit straw);
    /// here every one is set where the place needs it, and all of them low:
    /// the creatures, the dead and her light read over the ground. Steps in
    /// value draw the place's lines (the Legion's road a shade paler than its
    /// turf; the ruts a shade darker than the road).</summary>
    static readonly Dictionary<string, (float Y, float Sat)[]> Looks = new()
    {
        // turf, bare, way, grave, ash, rubble, face
        ["barrow"] = [(0.07f, 0.55f), (0.06f, 0.5f), (0.095f, 0.5f), (0.035f, 0.7f), (0.04f, 0.6f), (0.085f, 0.45f), (0.05f, 0.6f)],
        // litter, rot, roots, mud, bed, needles, face: the leaves warm and
        // red-brown against the cold night, the runs and banks black, the
        // stream's stones the palest thing on the ground (moss is the shader's)
        ["hollow"] = [(0.08f, 1.0f), (0.045f, 0.85f), (0.065f, 0.8f), (0.026f, 0.8f), (0.1f, 0.6f), (0.085f, 0.9f), (0.07f, 0.7f)],
        // verge, churn, ruts, wet, camp, metal, face
        ["ruts"] = [(0.065f, 0.6f), (0.05f, 0.65f), (0.045f, 0.6f), (0.04f, 0.65f), (0.06f, 0.55f), (0.08f, 0.5f), (0.055f, 0.55f)],
        // clay, spoil, ballast, slurry, rust, burnt, face: ochre clay and stone
        // stained rust in drifts, the spoil heaps coal-black, the cut walls
        // ochre; rust, never a red near her hair's
        ["dig"] = [(0.1f, 0.95f), (0.038f, 0.35f), (0.05f, 0.6f), (0.045f, 0.8f), (0.075f, 0.85f), (0.035f, 0.5f), (0.08f, 0.9f)],
    };

    /// <summary>The standing water's tint, place by place.</summary>
    static readonly Dictionary<string, Color> Wet = new()
    {
        ["barrow"] = new Color(0.62f, 0.64f, 0.66f), ["hollow"] = new Color(0.6f, 0.6f, 0.5f),
        ["ruts"] = new Color(0.62f, 0.6f, 0.56f), ["dig"] = new Color(0.7f, 0.6f, 0.46f),
    };

    /// <summary>A place's moss, and how much its slurry glows (the Dig cooks
    /// it; it lies in the Dig's pools and runs in the Hollow's stream).</summary>
    static readonly Dictionary<string, (Color Moss, float Slurry)> Growth = new()
    {
        // (sRGB: the shader takes them as colours.) The barrow's is lichen, grey.
        ["barrow"] = (new Color("#3d4230"), 0f),
        ["hollow"] = (new Color("#304620"), 0.55f),
        ["ruts"] = (new Color("#3b4826"), 0f),
        ["dig"] = (new Color("#3d4228"), 0.22f),
    };

    public static ShaderMaterial Material(ZoneData z)
    {
        var place = z.Place!;
        string dir = $"res://art/arena/{place.Id}";
        var mat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/arena_ground.gdshader") };
        mat.SetShaderParameter("noise_tex", NoiseTex.Get());
        mat.SetShaderParameter("splat", Mipped(z.Splat));
        mat.SetShaderParameter("splat2", Mipped(z.Splat2!));
        if (z.Splat3 != null) mat.SetShaderParameter("splat3", Mipped(z.Splat3));
        var (moss, slurry) = Growth[place.Id];
        mat.SetShaderParameter("moss_color", moss);
        mat.SetShaderParameter("slurry_glow", slurry);
        mat.SetShaderParameter("g_alb", GD.Load<TextureLayered>($"{dir}/albedo.jpg"));
        mat.SetShaderParameter("g_nor", GD.Load<TextureLayered>($"{dir}/normal.jpg"));
        mat.SetShaderParameter("g_arh", GD.Load<TextureLayered>($"{dir}/arh.jpg"));
        mat.SetShaderParameter("zone_size", z.Size);
        using var meta = JsonDocument.Parse(FileAccess.GetFileAsString($"{dir}/layers.json"));
        var scales = new Godot.Collections.Array<float>();
        var tones = new Godot.Collections.Array<float>();
        var sats = new Godot.Collections.Array<float>();
        var looks = Looks[place.Id];
        int k = 0;
        foreach (var l in meta.RootElement.GetProperty("layers").EnumerateArray())
        {
            scales.Add(1f / l.GetProperty("metres").GetSingle());
            var m = l.GetProperty("mean");
            float y = 0.2126f * m[0].GetSingle() + 0.7152f * m[1].GetSingle() + 0.0722f * m[2].GetSingle();
            tones.Add(looks[k].Y / Mathf.Max(y, 0.004f));
            sats.Add(looks[k].Sat);
            k++;
        }
        mat.SetShaderParameter("g_scale", scales);
        mat.SetShaderParameter("g_tone", tones);
        mat.SetShaderParameter("g_sat", sats);
        mat.SetShaderParameter("wet_tint", Wet[place.Id]);
        mat.SetShaderParameter("dapple", (float)place.Air.Dapple);
        mat.SetShaderParameter("ember", new Color(place.Air.Ember));
        mat.SetShaderParameter("ember_glow", (float)place.Air.EmberGlow);
        return mat;
    }

    /// <summary>The grass a place grows: its colour from the place's first
    /// layer (brought to its value), how green or straw, how thick.</summary>
    static readonly Dictionary<string, (Vector3 Tint, float Straw, float Density)> Grasses = new()
    {
        // The barrow field's dead grass over chalk: straw, thin, grey-blond.
        ["barrow"] = (new Vector3(1.0f, 1.0f, 0.82f), 0.75f, 0f),
        ["hollow"] = (new Vector3(0.85f, 1.15f, 0.7f), 0.2f, 0f),
        ["ruts"] = (new Vector3(0.9f, 1.1f, 0.72f), 0.45f, 0f),
        ["dig"] = (new Vector3(1, 1, 1), 0.6f, 0f),
    };

    public static bool GrowsGrass(string place) => Grasses[place].Density > 0;

    public static void Grass(ShaderMaterial mat, ZoneData z)
    {
        var place = z.Place!;
        string dir = $"res://art/arena/{place.Id}";
        mat.SetShaderParameter("splat", ImageTexture.CreateFromImage(z.GrassMask!));
        mat.SetShaderParameter("g_alb", GD.Load<TextureLayered>($"{dir}/albedo.jpg"));
        using var meta = JsonDocument.Parse(FileAccess.GetFileAsString($"{dir}/layers.json"));
        var l0 = meta.RootElement.GetProperty("layers")[0];
        mat.SetShaderParameter("meadow_scale", 1f / l0.GetProperty("metres").GetSingle());
        var m = l0.GetProperty("mean");
        float y = 0.2126f * m[0].GetSingle() + 0.7152f * m[1].GetSingle() + 0.0722f * m[2].GetSingle();
        // A blade a shade paler than the ground it stands in, so the field has a nap.
        mat.SetShaderParameter("tone", Looks[place.Id][0].Y * 1.35f / Mathf.Max(y, 0.004f));
        var (tint, straw, density) = Grasses[place.Id];
        mat.SetShaderParameter("tint", tint);
        mat.SetShaderParameter("straw_bias", straw);
        mat.SetShaderParameter("straw_mix", 0.3f + straw * 0.6f);
        // Straw at the place's own value, a little over its ground.
        float sv = Looks[place.Id][0].Y * 1.5f;
        mat.SetShaderParameter("straw_color", new Vector3(sv * 1.45f, sv * 1.25f, sv * 0.7f));
        mat.SetShaderParameter("density", density);
        mat.SetShaderParameter("leaves", 0f);
    }

    static ImageTexture Mipped(Image img)
    {
        var copy = (Image)img.Duplicate();
        copy.Convert(Image.Format.Rgba8);
        copy.GenerateMipmaps();
        return ImageTexture.CreateFromImage(copy);
    }
}
