using System.Collections.Generic;
using System.Text.Json;
using System.Text.RegularExpressions;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// The kits' materials as the web game weathers them (src/render/env.ts's
/// WEATHER table) and colours its flora (the kind's leaves and moss): each
/// imported StandardMaterial3D becomes shaders/kit.gdshader with the same
/// textures, cached per material and look.
/// </summary>
public static class KitLook
{
    /// Material name pattern: saturation kept, colour multiply.
    static readonly (Regex Re, float Sat, Vector3 Tint)[] Weather =
    {
        (new("RoundTiles"), 0.42f, new(0.74f, 0.7f, 0.68f)),
        (new("Plaster"), 0.6f, new(0.84f, 0.82f, 0.78f)),
        (new("WoodTrim|Wood"), 0.7f, new(0.72f, 0.7f, 0.68f)),
        (new("Brick|Rock|Stone"), 0.7f, new(0.84f, 0.83f, 0.8f)),
        (new("Leaf|Leaves|Grass|Clover|Fern|Plant|Bush"), 0.7f, new(0.8f, 0.84f, 0.76f)),
        (new("Bark"), 0.75f, new(0.8f, 0.78f, 0.76f)),
        (new("."), 0.82f, new(0.88f, 0.87f, 0.85f)),
    };
    static readonly Regex Foliage = new("Leaf|Leaves|Flower|Petal|Grass|Clover|Fern|Plant|Bush", RegexOptions.IgnoreCase);

    /// <param name="Shade">How much light the leaves give back: under an ember
    /// arena's night they stand as dark crowns round the fight, not lit lawns.</param>
    public sealed record Look(float Wind, Color? LeafA, Color? LeafB, float LeafAmount, float Moss, float Shade = 1)
    {
        /// <summary>A piece as it comes: still, its own colours.</summary>
        public static readonly Look Plain = new(0, null, null, 0, 0);
    }

    static Shader? solid, twoSided, solidRim, twoSidedRim, own, ownRim, ownLeaf, ownLeafRim, ownRock, ownRockRim;
    static readonly Dictionary<string, ShaderMaterial> cache = new();

    /// <summary>--see-debug (a developer's switch): the kit's pieces tinted green where whole and
    /// red on the window's rim, and what else stands in the window listed (Dump), so a piece in
    /// the window that is neither can be found.</summary>
    public static readonly bool SeeDebug = SurvivorUnchained.Args.Has("see-debug");
    // (whole: each copy its own tint, so pieces can be told apart; rim: opaque, coloured by how much
    // is kept, blue none to red all)
    const string Whole = "ALBEDO = col;",
        WholeDebug = "ALBEDO = col * (0.45 + 0.55 * vec3(fract(v_jit * 7.0), fract(v_jit * 13.0), fract(v_jit * 29.0)));",
        RimDebug = "ALBEDO = FRONT_FACING ? mix(vec3(0.0, 0.25, 1.0), vec3(1.0, 0.1, 0.0), kept) : vec3(0.1, 1.0, 0.2); ALPHA = 1.0;";

    /// <summary>--see-fix back,screen (a developer's switch while the window's pale wedge is
    /// fixed; shaders/kit.gdshader SEE_BACK, SEE_SCREEN): faces seen from behind cut whole
    /// inside the window, with no rim; the feather held to its width on the screen where
    /// how far a piece is opened varies across it. (--see-debug draws the rim's back faces green.)</summary>
    static readonly string SeeFix = SurvivorUnchained.Args.Get("see-fix") ?? "";

    static string Fixed(string code) => code.Replace("shader_type spatial;", "shader_type spatial;"
        + (SeeFix.Contains("back") ? "\n#define SEE_BACK" : "") + (SeeFix.Contains("screen") ? "\n#define SEE_SCREEN" : "")
        + (SeeFix.Contains("underao") ? "\n#define SEE_UNDER" : "") + (SeeFix.Contains("undercut") ? "\n#define SEE_UNDERCUT" : "") + (SeeFix.Contains("norim") ? "\n#define SEE_NORIM" : "")
        + (SeeFix.Contains("narrow") ? "\n#define SEE_NARROW" : ""));

    /// <summary>The see-through window's feathered rim (shaders/kit.gdshader): the same code
    /// with REVEAL defined, blended, drawn as each kit material's next pass.</summary>
    static Shader Rim(Shader of) => new()
    {
        Code = of.Code.Replace("shader_type spatial;", "shader_type spatial;\n#define REVEAL")
            .Replace("render_mode ", "render_mode blend_mix, depth_draw_never, ")
            .Replace(WholeDebug, RimDebug),
    };

    /// <summary>(--see-debug) Every mesh standing between the survivor's chest and the camera,
    /// within the window's reach of that line, with its materials: printed once.</summary>
    public static void Dump(Node root, Vector3 her, Vector3 cam)
    {
        var line = cam - her;
        float len = line.Length();
        var dir = line / len;
        foreach (var n in root.FindChildren("*", "GeometryInstance3D", true, false))
        {
            if (n is not GeometryInstance3D g || !g.IsVisibleInTree()) continue;
            var box = g.GlobalTransform * g.GetAabb();
            var c = box.GetCenter();
            float t = Mathf.Clamp((c - her).Dot(dir), 0, len);
            float off = (her + dir * t).DistanceTo(c) - box.Size.Length() * 0.5f;
            if (off > 2.6f || (c - her).Dot(dir) < -box.Size.Length() * 0.5f) continue;
            var mats = new List<string>();
            if (g is MeshInstance3D mi && mi.Mesh != null)
                for (int s = 0; s < mi.Mesh.GetSurfaceCount(); s++)
                    mats.Add(Describe(mi.GetActiveMaterial(s)));
            else if (g is MultiMeshInstance3D mm && mm.Multimesh?.Mesh is { } mesh)
                for (int s = 0; s < mesh.GetSurfaceCount(); s++)
                    mats.Add(Describe(g.MaterialOverride ?? mesh.SurfaceGetMaterial(s)) + $" x{mm.Multimesh.InstanceCount}");
            GD.Print($"see-debug: {g.GetPath()} [{g.GetClass()}] at {c} size {box.Size} off-line {off:0.0} m along {t:0.0} m: {string.Join(" | ", mats)}");
        }
    }

    static string Describe(Material? m) => m switch
    {
        null => "none",
        ShaderMaterial sm => $"shader {sm.Shader?.ResourcePath}{(sm.Shader == solid || sm.Shader == twoSided ? " (kit)" : "")} '{sm.ResourceName}'{(sm.NextPass != null ? " +next" : "")}",
        BaseMaterial3D b => $"{b.GetClass()} '{b.ResourceName}' transparency {b.Transparency} cull {b.CullMode}",
        _ => m.GetClass(),
    };

    /// <summary>A kit material as the web game shades it.</summary>
    /// <param name="foot">Darker toward the piece's foot (the village kit
    /// and the game's own models).</param>
    public static Material For(Material src, Look look, bool foot = false)
    {
        if (src is not StandardMaterial3D s) return src;
        var foliage = Foliage.IsMatch(s.ResourceName);
        var key = $"{s.GetInstanceId()}|{look}|{foot}";
        if (cache.TryGetValue(key, out var m)) return m;
        solid ??= SeeDebug || SeeFix != "" ? new Shader { Code = Fixed(GD.Load<Shader>("res://shaders/kit.gdshader").Code).Replace(Whole, SeeDebug ? WholeDebug : Whole) } : GD.Load<Shader>("res://shaders/kit.gdshader");
        twoSided ??= new Shader { Code = solid.Code.Replace("render_mode diffuse_burley", "render_mode cull_disabled, diffuse_burley") };
        // (our own rocks, tools/assets/env_rocks.py: Stone_Own<Species>, the one stone, OWN_ROCK)
        if (s.ResourceName.StartsWith("Stone_Own")) return cache[key] = Rock(s, look);
        // (our own trees, tools/assets/env_trees.py: Leaves_Own*, one material for bark and needles)
        bool mine = foliage && s.ResourceName.Contains("Own");
        own ??= new Shader { Code = twoSided.Code.Replace("shader_type spatial;", "shader_type spatial;\n#define OWN_FOLIAGE") };
        // (our alder, a broadleaf: its own light, the key's shadow taken in part, OWN_BROADLEAF)
        ownLeaf ??= new Shader { Code = own.Code.Replace("#define OWN_FOLIAGE", "#define OWN_FOLIAGE\n#define OWN_BROADLEAF") };
        // (the species' data, godot/data/flora_species.json: its shader parameters; "broadleaf" the leaf light)
        var sp = mine ? FloraSpecies.ByMaterial(s.ResourceName) : null;
        bool alder = sp?.Broadleaf ?? (mine && s.ResourceName.Contains("Alder"));
        m = new ShaderMaterial { Shader = alder ? ownLeaf : mine ? own : foliage || s.CullMode == BaseMaterial3D.CullModeEnum.Disabled ? twoSided : solid };
        m.SetShaderParameter("albedo_tex", s.AlbedoTexture);
        m.SetShaderParameter("albedo_color", s.AlbedoColor);
        m.SetShaderParameter("use_vcolor", s.VertexColorUseAsAlbedo);
        if (s.NormalEnabled && s.NormalTexture != null) { m.SetShaderParameter("use_normal", true); m.SetShaderParameter("normal_tex", s.NormalTexture); }
        m.SetShaderParameter("roughness", Mathf.Max(s.Roughness, 0.6f));
        bool cut = foliage || s.Transparency is BaseMaterial3D.TransparencyEnum.AlphaScissor or BaseMaterial3D.TransparencyEnum.Alpha;
        m.SetShaderParameter("alpha_scissor", cut ? Mathf.Max(s.AlphaScissorThreshold, 0.5f) : 0f);
        foreach (var (re, sat, tint) in Weather)
            if (re.IsMatch(s.ResourceName)) { m.SetShaderParameter("weather_sat", sat); m.SetShaderParameter("weather_tint", foliage ? tint * look.Shade : tint); break; }
        // (--kit-paint: a painted sheet carries its own warmth, so it is weathered as its painter says)
        if (Textures.PaintedWeather(s.AlbedoTexture) is var (psat, ptint)) { m.SetShaderParameter("weather_sat", psat); m.SetShaderParameter("weather_tint", ptint); }
        // (ours are painted for the look: weathered lightly, and trunk and needles sway as one)
        // (the vertex colour is their occlusion, read in OWN_FOLIAGE, not paint)
        if (mine) { m.SetShaderParameter("weather_sat", 0.86f); m.SetShaderParameter("weather_tint", new Vector3(0.7f, 0.76f, 0.7f) * look.Shade); m.SetShaderParameter("use_vcolor", false); }
        // (a packed species: its pieces in one file, each copy drawing only its own, OWN_FOLIAGE)
        if (sp is { Packed: true }) m.SetShaderParameter("packed", true);
        // (our alder, a broadleaf: its leaves flutter more than needles, and its olive is held off yellow under a low sun)
        // (the floors are set above the hue wanted on screen, ~100 and ~88: the grade warms them by 8-12 degrees, measured at roaddawn)
        // (alder at 86 left its sunlit tops pale yellow-olive at dawn, judge E4c: its brightest tenth at hue 90 or above wanted;
        // its crown core lightened, core 0.45, as its top by day read as a hole)
        // (the alder's flutter 2.2, hue floor 98 and core 0.3, the spruce's floor 108: now flora_species.json's "shader")
        if (sp != null)
            foreach (var (k, v) in sp.Shader)
            {
                if (k == "broadleaf") continue;
                if (k == "tint") { m.SetShaderParameter("weather_tint", new Vector3(v[0].GetSingle(), v[1].GetSingle(), v[2].GetSingle()) * look.Shade); continue; }
                m.SetShaderParameter(k == "sat" ? "weather_sat" : k, v.GetSingle());
            }
        if (alder && SurvivorUnchained.Args.Has("flora-sun-lift")) m.SetShaderParameter("sun_lift", SurvivorUnchained.Args.Num("flora-sun-lift", 0.1f));
        // (--flora-near-back F, --flora-near-dim F: a near tree's light through its leaves and its albedo cut by day, for pictures)
        if (mine) { m.SetShaderParameter("near_back", SurvivorUnchained.Args.Num("flora-near-back", 0.25f)); if (SurvivorUnchained.Args.Has("flora-near-dim")) m.SetShaderParameter("near_dim", SurvivorUnchained.Args.Num("flora-near-dim", 0.2f)); }
        m.SetShaderParameter("wind", foliage ? look.Wind : look.Wind * 0.3f);
        // (ours keep their own greens: the kit's autumn recolour gave gold tops, cut for the cinematics)
        if (foliage && !mine && look.LeafA is Color a && look.LeafB is Color b)
        {
            m.SetShaderParameter("recolor_a", new Vector4(a.R, a.G, a.B, look.LeafAmount));
            m.SetShaderParameter("recolor_b", new Vector3(b.R, b.G, b.B));
        }
        m.SetShaderParameter("moss", foliage ? 0f : look.Moss);
        m.SetShaderParameter("jitter", mine ? 0f : foliage ? 0.14f : 0.08f);  // (ours: OWN_FOLIAGE jitters each tree itself)
        m.SetShaderParameter("foot", foot);
        m.SetShaderParameter("leaves", foliage);
        // The window's rim, drawn again over what the piece's own pass left open: every
        // parameter the same, so the rim is the piece itself, fading.
        solidRim ??= Rim(solid);
        twoSidedRim ??= Rim(twoSided);
        ownRim ??= Rim(own);
        ownLeafRim ??= Rim(ownLeaf);
        var rim = new ShaderMaterial { Shader = m.Shader == solid ? solidRim : m.Shader == own ? ownRim : m.Shader == ownLeaf ? ownLeafRim : twoSidedRim };
        foreach (var u in m.Shader.GetShaderUniformList())
        {
            var name = (string)u.AsGodotDictionary()["name"];
            rim.SetShaderParameter(name, m.GetShaderParameter(name));
        }
        m.NextPass = rim;
        cache[key] = m;
        return m;
    }

    static Texture2D? stoneTex, stoneNor;

    /// <summary>Our own stone (kit.gdshader's OWN_ROCK): the sheet and parameters of flora_species.json's "stone", its
    /// species' "shader" over them; drawn with the see-through window's rim like the rest.</summary>
    static ShaderMaterial Rock(StandardMaterial3D s, Look look)
    {
        ownRock ??= new Shader { Code = solid!.Code.Replace("shader_type spatial;", "shader_type spatial;\n#define OWN_ROCK") };
        ownRockRim ??= Rim(ownRock);
        var st = FloraSpecies.Stone;
        stoneTex ??= GD.Load<Texture2D>(st.GetProperty("albedo").GetString()!);
        stoneNor ??= GD.Load<Texture2D>(st.GetProperty("normal").GetString()!);
        var m = new ShaderMaterial { Shader = ownRock };
        m.SetShaderParameter("stone_tex", stoneTex);
        m.SetShaderParameter("stone_nor", stoneNor);
        m.SetShaderParameter("use_vcolor", false);
        m.SetShaderParameter("jitter", 0f);
        m.SetShaderParameter("wind", 0f);
        void Set(string k, JsonElement v)
        {
            if (k == "broadleaf") return;
            if (v.ValueKind == JsonValueKind.Number) m.SetShaderParameter(k, v.GetSingle());
            else if (v.ValueKind == JsonValueKind.String && v.GetString()!.StartsWith('#')) m.SetShaderParameter(k, new Color(v.GetString()!));
            else if (v.ValueKind == JsonValueKind.Array && v.GetArrayLength() == 2) m.SetShaderParameter(k, new Vector2(v[0].GetSingle(), v[1].GetSingle()));
            else if (v.ValueKind == JsonValueKind.Array && v.GetArrayLength() == 3) m.SetShaderParameter(k, new Vector3(v[0].GetSingle(), v[1].GetSingle(), v[2].GetSingle()));
        }
        foreach (var kv in st.GetProperty("shader").EnumerateObject()) Set(kv.Name, kv.Value);
        if (FloraSpecies.ByMaterial(s.ResourceName) is { } sp)
        {
            foreach (var (k, v) in sp.Shader) Set(k, v);
            if (sp.Packed) m.SetShaderParameter("packed", true);
        }
        var rim = new ShaderMaterial { Shader = ownRockRim };
        foreach (var u in m.Shader.GetShaderUniformList())
        {
            var name = (string)u.AsGodotDictionary()["name"];
            rim.SetShaderParameter(name, m.GetShaderParameter(name));
        }
        m.NextPass = rim;
        return m;
    }
}
