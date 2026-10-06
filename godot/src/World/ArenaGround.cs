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
    /// order (tools/godot/arena_ground.py): its mean albedo in linear light (Y),
    /// how much of its colour it keeps (Sat), how far its own lights and darks
    /// are pulled apart (Con: from thirty metres up a scan's grain averages
    /// away, and the ground reads as asphalt), how high it lies over the bare
    /// ground in metres (Lift) and how much its photographed height swells it
    /// (Bump). The scans were shot on days of every brightness; here each is
    /// set where the place needs it, all below the living, and the steps in
    /// value and height between them draw the place's lines.</summary>
    public readonly record struct Layer(float Y, float Sat, float Con = 1.25f, float Lift = 0, float Bump = 0.05f, float Size = 1);

    static readonly Dictionary<string, Layer[]> Looks = new()
    {
        // turf, bare, way, grave, ash, rubble, face
        ["barrow"] = [new(0.07f, 0.55f, Lift: 0.04f, Bump: 0.08f), new(0.06f, 0.5f), new(0.095f, 0.5f, Lift: 0.02f, Bump: 0.06f, Size: 1.7f), new(0.035f, 0.7f, Lift: -0.02f),
            new(0.04f, 0.6f, Lift: -0.01f), new(0.085f, 0.45f, Lift: 0.02f, Bump: 0.08f), new(0.05f, 0.6f)],
        // litter, rot, roots, mud, bed, needles, face: the leaves warm and
        // red-brown against the cold night, the runs and banks black, the
        // stream's stones the palest thing on the ground (moss is the shader's)
        // (Leaves drawn a third larger than the scan's: a leaf must be a few pixels to read as
        // one from the arena camera. Whole red-brown leaves read as leaves; a scan of pale
        // chips on black read as gravel however it was toned.) The rot is black earth.
        ["hollow"] = [new(0.095f, 1.0f, Con: 1.1f, Lift: 0.02f, Size: 1.35f), new(0.04f, 0.85f, Con: 1.1f), new(0.075f, 0.8f, Lift: 0.03f, Bump: 0.1f, Size: 1.3f),
            // (The mud trodden smooth: at the scan's own contrast the den's floor read as asphalt.)
            new(0.035f, 0.8f, Con: 0.75f, Lift: -0.03f), new(0.1f, 0.6f, Lift: -0.05f, Bump: 0.08f), new(0.085f, 0.9f, Con: 0.9f, Lift: 0.01f, Size: 1.4f), new(0.07f, 0.7f)],
        // verge, churn, ruts, wet, camp, metal, face
        ["ruts"] = [new(0.065f, 0.6f, Lift: 0.04f, Bump: 0.06f), new(0.05f, 0.65f), new(0.045f, 0.6f, Lift: -0.02f, Bump: 0.08f), new(0.04f, 0.65f, Lift: -0.04f),
            new(0.06f, 0.55f, Lift: 0.01f), new(0.08f, 0.5f, Lift: 0.01f, Bump: 0.06f), new(0.055f, 0.55f)],
        // clay, spoil, ballast, slurry, rust, burnt, face: ochre clay and stone
        // stained rust in drifts, the spoil heaps coal-black, the cut walls
        // ochre; rust, never a red near her hair's
        // (The spoil a shade lighter than coal, 0.075: at 0.05 the moon's light and shade on a
        // tip's flanks fell below black, and a heap read as a flat hole.)
        // (The clay lighter, 0.13, so the black tips, the rails and the Lamplings stand out on it,
        // as the concept's do: at 0.1 the working was one dark brown field.)
        ["dig"] = [new(0.13f, 0.95f, Lift: 0.02f, Bump: 0.08f), new(0.075f, 0.35f, Con: 1.4f, Lift: 0.04f, Bump: 0.12f, Size: 1.3f),
            // (The broken stone grey-brown over the clay, not black: its drifts read as dark blots.)
            new(0.09f, 0.35f, Lift: 0.01f, Bump: 0.06f),
            // (The slurry's mud only a little darker than the clay: at 0.045 every spill was a black
            // ring and black stains round its pool.)
            new(0.085f, 0.7f, Lift: -0.05f),
            // (The rust as light as the clay and lying at its height: the stain is a shift of
            // hue, never a darker blot with a ledge round it, which read as camouflage.)
            new(0.12f, 0.85f, Con: 1.0f, Lift: 0.02f, Bump: 0.08f), new(0.035f, 0.5f), new(0.08f, 0.9f)],
    };

    /// <summary>The standing water's tint, place by place.</summary>
    static readonly Dictionary<string, Color> Wet = new()
    {
        ["barrow"] = new Color(0.62f, 0.64f, 0.66f), ["hollow"] = new Color(0.6f, 0.6f, 0.5f),
        ["ruts"] = new Color(0.62f, 0.6f, 0.56f), ["dig"] = new Color(0.7f, 0.6f, 0.46f),
    };

    /// <summary>A place's moss, how much its slurry glows (the Dig cooks
    /// it; it lies in the Dig's pools and runs in the Hollow's stream), and
    /// how much its rotting wood glows with foxfire where it is painted.</summary>
    static readonly Dictionary<string, (Color Moss, float Slurry, float Fox)> Growth = new()
    {
        // (sRGB: the shader takes them as colours.) The barrow's is lichen, grey.
        ["barrow"] = (new Color("#3d4230"), 0f, 0f),
        ["hollow"] = (new Color("#304620"), 0.16f, 1.6f),
        ["ruts"] = (new Color("#3b4826"), 0f, 0f),
        ["dig"] = (new Color("#3d4228"), 0.22f, 0f),
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
        var (moss, slurry, fox) = Growth[place.Id];
        mat.SetShaderParameter("moss_color", moss);
        mat.SetShaderParameter("slurry_glow", slurry);
        mat.SetShaderParameter("slurry_body", place.Id == "dig" ? 1f : 0f);
        mat.SetShaderParameter("fox_glow", fox);
        mat.SetShaderParameter("lip_glow", z.Story ? 0.3f : 1f);
        mat.SetShaderParameter("face_skip_b", place.Id == "dig" ? 1f : 0f);
        mat.SetShaderParameter("scorch_reach", z.Story ? 3.5f : 11f);
        mat.SetShaderParameter("past_dark", z.Story ? 0.25f : 0.6f);
        mat.SetShaderParameter("scorch_out", z.Story ? 3f : 1000f);
        mat.SetShaderParameter("g_alb", GD.Load<TextureLayered>($"{dir}/albedo.jpg"));
        mat.SetShaderParameter("g_nor", GD.Load<TextureLayered>($"{dir}/normal.jpg"));
        mat.SetShaderParameter("g_arh", GD.Load<TextureLayered>($"{dir}/arh.jpg"));
        mat.SetShaderParameter("zone_size", z.Size);
        using var meta = JsonDocument.Parse(FileAccess.GetFileAsString($"{dir}/layers.json"));
        var scales = new Godot.Collections.Array<float>();
        var tones = new Godot.Collections.Array<float>();
        var sats = new Godot.Collections.Array<float>();
        var cons = new Godot.Collections.Array<float>();
        var means = new Godot.Collections.Array<float>();
        var lifts = new Godot.Collections.Array<float>();
        var bumps = new Godot.Collections.Array<float>();
        var looks = Looks[place.Id];
        int k = 0;
        foreach (var l in meta.RootElement.GetProperty("layers").EnumerateArray())
        {
            var m = l.GetProperty("mean");
            float y = Mathf.Max(0.2126f * m[0].GetSingle() + 0.7152f * m[1].GetSingle() + 0.0722f * m[2].GetSingle(), 0.004f);
            var look = looks[k];
            // (The Legion's slabs drawn larger than the scan's cobbles: a road built by an empire.)
            scales.Add(1f / (l.GetProperty("metres").GetSingle() * look.Size));
            tones.Add(look.Y / y);
            sats.Add(look.Sat);
            cons.Add(look.Con);
            means.Add(y);
            lifts.Add(look.Lift);
            bumps.Add(look.Bump);
            k++;
        }
        mat.SetShaderParameter("g_scale", scales);
        mat.SetShaderParameter("g_tone", tones);
        mat.SetShaderParameter("g_sat", sats);
        mat.SetShaderParameter("g_con", cons);
        mat.SetShaderParameter("g_mean", means);
        mat.SetShaderParameter("g_lift", lifts);
        mat.SetShaderParameter("g_bump", bumps);
        mat.SetShaderParameter("wet_tint", Wet[place.Id]);
        // (The canopy's pools are real shadow now, ArenaEdge.Canopy: none painted on the ground.)
        mat.SetShaderParameter("dapple", 0f);
        mat.SetShaderParameter("ember", new Color(place.Air.Ember));
        mat.SetShaderParameter("ember_glow", (float)place.Air.EmberGlow);
        return mat;
    }

    /// <summary>A place's grass (shaders/arena_grass.gdshader): how thick it
    /// grows where its paint says, its tussocks (blades, a blade's half-width,
    /// the grid's cell, metres tall short and long, how far they spread), and
    /// its colours as sRGB hex: deep in the tussock, its body, its dead tips,
    /// the green still in it and how much of the field that is.</summary>
    public sealed record GrassLook(float Density, int Blades, float Width, float Cell, Vector2 Height, float Spread,
        string Root, string Body, string Tip, string Green, float GreenShare);

    static readonly Dictionary<string, GrassLook> Grasses = new()
    {
        // The barrow field's long dead grass, olive-brown and its tips gone
        // to pale straw under the moon: the field's whole face.
        // (Its tips warm and mid-toned: pale straw tips under a blue moon read from above as a
        // field of grey stars, one sticker per tussock.)
        ["barrow"] = new(1f, 26, 0.016f, 0.42f, new(0.4f, 0.9f), 1.3f, "#0c0a07", "#4e3e26", "#8c7448", "#3e462a", 0.3f),
        // Sparse and low where the canopy opens.
        ["hollow"] = new(0.5f, 12, 0.02f, 0.55f, new(0.2f, 0.45f), 0.8f, "#0a0b07", "#38402a", "#6c7048", "#2e4626", 0.6f),
        // The verges: greener, trodden shorter toward the road.
        ["ruts"] = new(1f, 24, 0.016f, 0.45f, new(0.3f, 0.7f), 1.2f, "#0a0b07", "#40482a", "#8e8a5c", "#34502a", 0.55f),
        // Dry yellow tufts on the working's spoil and edges, where nobody walks.
        ["dig"] = new(0.8f, 12, 0.022f, 0.55f, new(0.25f, 0.6f), 0.9f, "#0e0a06", "#6a5632", "#c4a466", "#4a4a2a", 0.1f),
    };

    public static GrassLook GrassOf(string place) => Grasses[place];

    /// <summary>A place's fallen leaves: how thick where its paint lays them, leaves to a
    /// cell of sixty centimetres, and how large (1: about eleven centimetres).</summary>
    public sealed record LeafLook(float Density, int PerCell, float Size);

    static readonly Dictionary<string, LeafLook> LeafLooks = new()
    {
        // The Hollow's: this autumn's, over the litter of years.
        ["hollow"] = new(1f, 14, 1.35f),
    };

    public static LeafLook? LeavesOf(string place) => LeafLooks.GetValueOrDefault(place);

    public static bool GrowsGrass(string place) => Grasses[place].Density > 0 || LeafLooks.ContainsKey(place);

    public static void Grass(ShaderMaterial mat, ZoneData z)
    {
        var g = Grasses[z.Place!.Id];
        mat.SetShaderParameter("density", g.Density);
        mat.SetShaderParameter("height", g.Height);
        mat.SetShaderParameter("spread", g.Spread);
        mat.SetShaderParameter("root_col", new Color(g.Root));
        mat.SetShaderParameter("body_col", new Color(g.Body));
        mat.SetShaderParameter("tip_col", new Color(g.Tip));
        mat.SetShaderParameter("green_col", new Color(g.Green));
        mat.SetShaderParameter("green", g.GreenShare);
    }

    static ImageTexture Mipped(Image img)
    {
        var copy = (Image)img.Duplicate();
        copy.Convert(Image.Format.Rgba8);
        copy.GenerateMipmaps();
        return ImageTexture.CreateFromImage(copy);
    }
}
