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
    /// <summary>Each layer's colour multiplier, place by place, in the
    /// layers' order (tools/godot/arena_ground.py): the scans were shot in
    /// daylight, often bright and warm; this valley at night is not.</summary>
    static readonly Dictionary<string, Vector3[]> Tones = new()
    {
        // turf, bare, way, grave, ash, rubble, face
        ["barrow"] = [new(0.62f, 0.62f, 0.58f), new(0.78f, 0.78f, 0.8f), new(0.95f, 0.95f, 1.0f), new(0.7f, 0.66f, 0.62f), new(0.8f, 0.78f, 0.76f), new(0.62f, 0.62f, 0.64f), new(1, 1, 1)],
        // litter, moss, roots, mud, bed, needles, face
        ["hollow"] = [new(0.8f, 0.76f, 0.7f), new(0.75f, 0.8f, 0.72f), new(0.75f, 0.7f, 0.66f), new(0.8f, 0.78f, 0.76f), new(0.7f, 0.7f, 0.72f), new(0.62f, 0.58f, 0.52f), new(0.8f, 0.8f, 0.8f)],
        // verge, churn, ruts, wet, camp, metal, face
        ["ruts"] = [new(0.62f, 0.62f, 0.56f), new(0.8f, 0.76f, 0.72f), new(0.74f, 0.7f, 0.66f), new(0.72f, 0.68f, 0.64f), new(0.62f, 0.56f, 0.5f), new(0.62f, 0.62f, 0.62f), new(0.8f, 0.8f, 0.8f)],
        // clay, spoil, rubble, slurry, dry, burnt, face
        ["dig"] = [new(0.66f, 0.6f, 0.58f), new(0.8f, 0.8f, 0.82f), new(0.62f, 0.6f, 0.58f), new(0.68f, 0.62f, 0.5f), new(0.55f, 0.5f, 0.46f), new(0.8f, 0.78f, 0.76f), new(0.7f, 0.66f, 0.62f)],
    };

    /// <summary>The ground's value and saturation, all told, place by place.</summary>
    static readonly Dictionary<string, (float Value, float Sat, Color Wet)> Range = new()
    {
        ["barrow"] = (0.78f, 0.72f, new Color(0.62f, 0.64f, 0.66f)),
        ["hollow"] = (0.72f, 0.78f, new Color(0.6f, 0.6f, 0.5f)),
        ["ruts"] = (0.78f, 0.75f, new Color(0.62f, 0.6f, 0.56f)),
        ["dig"] = (0.78f, 0.78f, new Color(0.7f, 0.6f, 0.46f)),
    };

    public static ShaderMaterial Material(ZoneData z)
    {
        var place = z.Place!;
        string dir = $"res://art/arena/{place.Id}";
        var mat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/arena_ground.gdshader") };
        mat.SetShaderParameter("noise_tex", NoiseTex.Get());
        mat.SetShaderParameter("splat", Mipped(z.Splat));
        mat.SetShaderParameter("splat2", Mipped(z.Splat2!));
        mat.SetShaderParameter("g_alb", GD.Load<TextureLayered>($"{dir}/albedo.jpg"));
        mat.SetShaderParameter("g_nor", GD.Load<TextureLayered>($"{dir}/normal.jpg"));
        mat.SetShaderParameter("g_arh", GD.Load<TextureLayered>($"{dir}/arh.jpg"));
        mat.SetShaderParameter("zone_size", z.Size);
        using var meta = JsonDocument.Parse(FileAccess.GetFileAsString($"{dir}/layers.json"));
        var scales = new Godot.Collections.Array<float>();
        foreach (var l in meta.RootElement.GetProperty("layers").EnumerateArray()) scales.Add(1f / l.GetProperty("metres").GetSingle());
        mat.SetShaderParameter("g_scale", scales);
        var tones = new Godot.Collections.Array<Vector3>(Tones[place.Id]);
        mat.SetShaderParameter("g_tone", tones);
        var (value, sat, wet) = Range[place.Id];
        mat.SetShaderParameter("value", value);
        mat.SetShaderParameter("sat", sat);
        mat.SetShaderParameter("wet_tint", wet);
        mat.SetShaderParameter("dapple", (float)place.Air.Dapple);
        mat.SetShaderParameter("ember", new Color(place.Air.Ember));
        mat.SetShaderParameter("ember_glow", (float)place.Air.EmberGlow);
        return mat;
    }

    static ImageTexture Mipped(Image img)
    {
        var copy = (Image)img.Duplicate();
        copy.Convert(Image.Format.Rgba8);
        copy.GenerateMipmaps();
        return ImageTexture.CreateFromImage(copy);
    }
}
