using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Content;

namespace SurvivorUnchained.View;

/// <summary>
/// Per-copy colours for a Marionette package NPC, so a crowd of one package is not clones (art/npc/NAME/dye.json and
/// dye.png, by tools/meshy/dye_mask.py: R the main cloth "a", G the second cloth "b", B hair and beard, A the head cloth
/// "coif"; where all are 0, bare skin, which a package with a "skin" entry (the risen) tints per copy).
/// One material per package (shaders/npc_dye.gdshader, the importer's StandardMaterial3D with a dye in its albedo), each
/// copy's colours instance uniforms on its full and lod meshes. From the spec: Dye.Cloth the "a" channel, Dye.Under "b",
/// HairColor hair, the coif always from the palette; a null one is picked from the package's palette, per copy (Args "seed" plus a running count, so a shot
/// repeats). With no Dye at all, the copy's height is also jittered by the package's "scale" (Person.Jitter). Every
/// target is held to its channel's Oklab lightness range. A package with no dye.json is drawn as before.
/// --npc-dye off: the dye material with no dye (the parity check); --npc-dye none: the importer's own material.
/// </summary>
public static class NpcDye
{
    sealed class Def
    {
        public Texture2D Mask = null!;
        public readonly (double R, double G, double B)?[] Base = new (double, double, double)?[4];
        public readonly (double Lo, double Hi)?[] Range = new (double, double)?[4];
        public readonly string[][] Palette = { System.Array.Empty<string>(), System.Array.Empty<string>(), System.Array.Empty<string>(), System.Array.Empty<string>() };
        public double Scale;
        // bare-skin tint (the risen): value range, chroma, Oklab hues
        public (double Lo, double Hi, double Chroma, double[] Hues)? Skin;
    }

    static readonly string[] Keys = { "a", "b", "hair", "coif" };
    static readonly string[] Uniforms = { "dye_a", "dye_b", "dye_h", "dye_c" };
    static readonly Dictionary<string, Def?> defs = new();
    static readonly Dictionary<string, ShaderMaterial?> mats = new();
    static readonly Dictionary<string, Shader> shaders = new();
    static string? code;
    static int copies;
    static readonly HashSet<string> told = new();

    /// <summary>Called under People.BuildLock (the count and caches are shared with WalkerView's worker thread).</summary>
    public static void Apply(People.Person p, string pkg, SurvivorUnchained.World.PersonSpec spec)
    {
        int seed = int.TryParse(Args.Get("seed"), out var s) ? s : 0;
        int copy = copies++;
        p.Phase = (float)NpcDyePick.Phase(seed, copy);
        if (Args.Get("npc-dye") == "none" || Read(pkg) is not { } def) { if (Args.Has("npc-dye-log")) GD.Print($"npc dye: {pkg} copy {copy}: none"); return; }
        var meshes = p.Meshes.Concat(p.Skeleton.GetChildren().OfType<MeshInstance3D>().Where(m => m.Name == "lod")).Distinct().ToList();
        ShaderMaterial? mat = null;
        foreach (var mi in meshes)
            for (int i = 0; i < mi.Mesh.GetSurfaceCount(); i++)
            {
                // (the lod's surface is drawn with the body's material already, NpcPackage.BakedLod: that one is the source)
                var cur = mi.GetSurfaceOverrideMaterial(i);
                if ((cur ?? mi.Mesh.SurfaceGetMaterial(i)) is not StandardMaterial3D src || src.ResourceName != "generated") continue;
                mat ??= Material(pkg, src, def);
                if (mat == null) return;
                mi.SetSurfaceOverrideMaterial(i, mat);
            }
        if (mat == null)
        {
            if (told.Add(pkg)) GD.PushWarning($"npc dye: {pkg} has no \"generated\" surface to dye ({string.Join(", ", meshes.SelectMany(m => Enumerable.Range(0, m.Mesh.GetSurfaceCount()).Select(i => $"{m.Name}:{m.Mesh.SurfaceGetMaterial(i)?.GetType().Name}:{m.Mesh.SurfaceGetMaterial(i)?.ResourceName}/{m.GetSurfaceOverrideMaterial(i)?.GetType().Name}")))})");
            return;
        }
        bool off = Args.Get("npc-dye") == "off";
        string?[] asked = { spec.Dye?.Cloth, spec.Dye?.Under, spec.HairColor, null };
        var cols = new Color[4];
        for (int c = 0; c < 4; c++)
        {
            if (off || def.Base[c] == null) { cols[c] = new Color(0, 0, 0, 0); continue; }
            var pal = def.Palette[c];
            var want = NpcDyePick.Hex(asked[c]) ?? (pal.Length > 0 ? NpcDyePick.Hex(pal[NpcDyePick.Pick(seed, copy, c, pal.Length)]) : null);
            if (want is not { } t) { cols[c] = new Color(0, 0, 0, 0); continue; }
            if (def.Range[c] is { } r) t = NpcDyePick.ClampL(t, r.Lo, r.Hi);
            t = NpcDyePick.CapChroma(t);
            // (a Color instance uniform is taken as sRGB and made linear on its way in: so handed over as sRGB)
            cols[c] = new Color((float)t.R, (float)t.G, (float)t.B, 1).LinearToSrgb();
        }
        var skin = new Color(1, 1, 1, 0);
        if (!off && def.Skin is { } sk)
        {
            var t = NpcDyePick.SkinTint(seed, copy, sk.Lo, sk.Hi, sk.Chroma, sk.Hues);
            skin = new Color((float)t.R, (float)t.G, (float)t.B, 1).LinearToSrgb();
        }
        foreach (var mi in meshes)
        {
            for (int c = 0; c < 4; c++) mi.SetInstanceShaderParameter(Uniforms[c], cols[c]);
            mi.SetInstanceShaderParameter("dye_s", skin);
        }
        if (Args.Has("npc-dye-log")) GD.Print($"npc dye: {pkg} copy {copy}: a {cols[0].ToHtml()} b {cols[1].ToHtml()} hair {cols[2].ToHtml()} coif {cols[3].ToHtml()} skin {skin.ToHtml()} on {meshes.Count} meshes");
        if (spec.Dye == null && !off) p.Jitter = (float)NpcDyePick.Scale(seed, copy, def.Scale);
    }

    static Def? Read(string pkg)
    {
        if (defs.TryGetValue(pkg, out var d)) return d;
        string dir = NpcPackage.Dir(pkg);
        defs[pkg] = null;
        if (!FileAccess.FileExists($"{dir}/dye.json")) return null;
        var j = Json.ParseString(FileAccess.GetFileAsString($"{dir}/dye.json")).AsGodotDictionary();
        string maskFile = $"{dir}/{(string)j["mask"]}";
        if (!ResourceLoader.Exists(maskFile)) { GD.PushWarning($"npc dye: {maskFile} is not there (or not imported)"); return null; }
        d = new Def { Mask = GD.Load<Texture2D>(maskFile), Scale = j.TryGetValue("scale", out var sc) ? (double)sc : 0 };
        var bases = j["base"].AsGodotDictionary();
        var ranges = j.TryGetValue("range", out var rg) ? rg.AsGodotDictionary() : new Godot.Collections.Dictionary();
        var pals = j.TryGetValue("palette", out var pl) ? pl.AsGodotDictionary() : new Godot.Collections.Dictionary();
        if (j.TryGetValue("skin", out var skv) && skv.AsGodotDictionary() is { } skd && skd.TryGetValue("value", out var vv) && vv.AsGodotArray() is { Count: 2 } va)
            d.Skin = ((double)va[0], (double)va[1], skd.TryGetValue("chroma", out var ch) ? (double)ch : 0,
                skd.TryGetValue("hues", out var hu) ? hu.AsGodotArray().Select(h => (double)h).ToArray() : System.Array.Empty<double>());
        for (int c = 0; c < 4; c++)
        {
            if (bases.TryGetValue(Keys[c], out var b)) d.Base[c] = NpcDyePick.Hex((string)b);
            if (ranges.TryGetValue(Keys[c], out var r) && r.AsGodotArray() is { Count: 2 } ra) d.Range[c] = ((double)ra[0], (double)ra[1]);
            if (pals.TryGetValue(Keys[c], out var pa)) d.Palette[c] = pa.AsGodotArray().Select(v => (string)v).ToArray();
        }
        return defs[pkg] = d;
    }

    /// <summary>The package's one dye material, from the importer's: null (and drawn as before) if that material uses a
    /// feature the dye shader does not copy.</summary>
    static ShaderMaterial? Material(string pkg, StandardMaterial3D src, Def def)
    {
        if (mats.TryGetValue(pkg, out var have)) return have;
        mats[pkg] = null;
        string? why = src.Transparency != BaseMaterial3D.TransparencyEnum.Disabled ? "transparency"
            : src.ShadingMode != BaseMaterial3D.ShadingModeEnum.PerPixel ? "shading mode"
            : src.DiffuseMode != BaseMaterial3D.DiffuseModeEnum.Burley ? "diffuse mode"
            : src.SpecularMode != BaseMaterial3D.SpecularModeEnum.SchlickGgx ? "specular mode"
            : src.EmissionEnabled || src.AOEnabled || src.RimEnabled || src.ClearcoatEnabled || src.AnisotropyEnabled || src.HeightmapEnabled
              || src.SubsurfScatterEnabled || src.BacklightEnabled || src.RefractionEnabled || src.DetailEnabled ? "an extra feature"
            : src.VertexColorUseAsAlbedo ? "vertex colour albedo"
            : src.AlbedoTexture == null || src.RoughnessTexture == null || !src.NormalEnabled || src.NormalTexture == null ? "a missing map"
            : src.RoughnessTextureChannel != BaseMaterial3D.TextureChannel.Green ? "roughness channel"
            : src.Uv1Triplanar || src.BillboardMode != BaseMaterial3D.BillboardModeEnum.Disabled || src.Grow || src.ProximityFadeEnabled
              || src.DistanceFadeMode != BaseMaterial3D.DistanceFadeModeEnum.Disabled || src.UseParticleTrails || src.FixedSize ? "an extra feature"
            : src.DepthDrawMode != BaseMaterial3D.DepthDrawModeEnum.OpaqueOnly || src.NoDepthTest || src.BlendMode != BaseMaterial3D.BlendModeEnum.Mix ? "depth or blend"
            : null;
        if (why != null) { GD.PushWarning($"npc dye: {pkg}'s material has {why}; drawn without dye"); return null; }
        string filter = src.TextureFilter switch
        {
            BaseMaterial3D.TextureFilterEnum.Nearest => "filter_nearest",
            BaseMaterial3D.TextureFilterEnum.Linear => "filter_linear",
            BaseMaterial3D.TextureFilterEnum.NearestWithMipmaps => "filter_nearest_mipmap",
            BaseMaterial3D.TextureFilterEnum.LinearWithMipmaps => "filter_linear_mipmap",
            BaseMaterial3D.TextureFilterEnum.NearestWithMipmapsAnisotropic => "filter_nearest_mipmap_anisotropic",
            _ => "filter_linear_mipmap_anisotropic",
        };
        string repeat = src.TextureRepeat ? "repeat_enable" : "repeat_disable";
        string cull = src.CullMode switch { BaseMaterial3D.CullModeEnum.Back => "cull_back", BaseMaterial3D.CullModeEnum.Front => "cull_front", _ => "cull_disabled" };
        string key = $"{filter} {repeat} {cull}";
        if (!shaders.TryGetValue(key, out var sh))
        {
            code ??= FileAccess.GetFileAsString("res://shaders/npc_dye.gdshader");
            // (the importer's sampler flags and cull, as the source material has them; the mask keeps its own sampler)
            var body = code.Replace("filter_linear_mipmap_anisotropic, repeat_enable", $"{filter}, {repeat}").Replace("cull_disabled", cull);
            sh = shaders[key] = new Shader { Code = body };
        }
        var m = new ShaderMaterial { Shader = sh, ResourceName = "generated_dye" };
        m.SetShaderParameter("albedo", src.AlbedoColor);
        m.SetShaderParameter("texture_albedo", src.AlbedoTexture);
        m.SetShaderParameter("roughness", src.Roughness);
        m.SetShaderParameter("texture_roughness", src.RoughnessTexture);
        m.SetShaderParameter("metallic", src.Metallic);
        m.SetShaderParameter("texture_metallic", src.MetallicTexture);
        m.SetShaderParameter("metallic_texture_channel", src.MetallicTextureChannel switch
        {
            BaseMaterial3D.TextureChannel.Red => new Vector4(1, 0, 0, 0),
            BaseMaterial3D.TextureChannel.Green => new Vector4(0, 1, 0, 0),
            BaseMaterial3D.TextureChannel.Blue => new Vector4(0, 0, 1, 0),
            BaseMaterial3D.TextureChannel.Alpha => new Vector4(0, 0, 0, 1),
            _ => new Vector4(0.333333f, 0.333333f, 0.333333f, 0),
        });
        m.SetShaderParameter("specular", src.MetallicSpecular);
        m.SetShaderParameter("texture_normal", src.NormalTexture);
        m.SetShaderParameter("normal_scale", src.NormalScale);
        m.SetShaderParameter("uv1_scale", src.Uv1Scale);
        m.SetShaderParameter("uv1_offset", src.Uv1Offset);
        m.SetShaderParameter("dye_mask", def.Mask);
        var lum = new Vector4();
        for (int c = 0; c < 4; c++) lum[c] = def.Base[c] is { } b ? (float)NpcDyePick.Lum(b) : 1f;
        m.SetShaderParameter("dye_max_chroma", (float)NpcDyePick.MaxChroma);
        m.SetShaderParameter("dye_base_lum", lum);
        // (its render priority and next pass as the source's, should it have them)
        m.RenderPriority = src.RenderPriority;
        m.NextPass = src.NextPass;
        return mats[pkg] = m;
    }
}
