using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.RegularExpressions;
using Godot;
using SurvivorUnchained.Look;
using StdCelCode = SurvivorUnchained.World.StdCelCode;

namespace SurvivorUnchained.View;

/// <summary>The material library on the game side (L1 B2; godot/data/look/materials.json, logic/Look/MaterialLibrary.cs).
/// <para>Apply: a builder's ShaderMaterial (KitLook and the rest) takes its class's per-material cel uniforms.</para>
/// <para>The loader: one hook on the tree's NodeAdded (drained once a frame before drawing, so a material set just after
/// AddChild is caught too) visits every MeshInstance3D and MultiMeshInstance3D of the world (surface materials, surface
/// overrides, the material override and overlay, their next passes). Each lit StandardMaterial3D or ORMMaterial3D is put
/// on the model in place: the engine's own generated shader for its feature set (StdCelCode, a port of Godot 4.5.1's
/// material.cpp) with shaders/std_cel.gdshaderinc included and CEL_FRAGMENT; last, cached per feature key, is bound to
/// the material's own RID, and its class's cel uniforms set there. The material object stays the game's, so every later
/// change game code makes to it (a hit flash, a fade, a tint) still lands; a change of feature set (the engine then
/// rebinds its own shader) is caught by a sweep of a few materials a frame. A cel ShaderMaterial of a known adopting
/// shader whose material name or asset matches a rule takes that class (person.gdshader's "Body" folk skin); one that
/// matches none keeps its shader's defaults, which are its default class (the tests hold them equal).</para>
/// <para>--cel off converts and re-classes nothing: today's materials by construction. --cel-audit prints, at every
/// shot (Shots), each lit material of the world not on the model, by node, material and surface, and the count.</para></summary>
public static class CelLib
{
    static MaterialLibrary? lib;
    public static MaterialLibrary Lib => lib ??= MaterialLibrary.Parse(Godot.FileAccess.GetFileAsString("res://data/look/materials.json"));
    /// <summary>Whether the library and the loader act: not at --cel off (nor --cel-lib off, the loader alone off, for measuring its cost).</summary>
    public static readonly bool On = SurvivorUnchained.Args.Get("cel") != "off" && SurvivorUnchained.Args.Get("cel-lib") != "off";
    static readonly bool Audit = SurvivorUnchained.Args.Has("cel-audit");
    const string Meta = "cel_class";

    /// <summary>The class of a material of an adopting shader: the first rule that matches, else the shader's default class.</summary>
    public static string ClassOf(string shader, string? material, string? asset) =>
        Lib.ClassFor(shader, material, asset) ?? (Lib.Shaders.TryGetValue(shader, out var c) ? c : Lib.Fallback);

    /// <summary>Sets a ShaderMaterial's (and its cel next passes') per-material cel uniforms from the class.</summary>
    public static T Apply<T>(T m, string cls) where T : ShaderMaterial
    {
        var c = Lib.Classes[cls];
        for (Material? p = m; p != null; p = p.NextPass)
            if (p is ShaderMaterial sm && UsesCel(sm.Shader))
            {
                foreach (var (name, v) in Uniforms(c)) sm.SetShaderParameter(name, v);
                sm.SetMeta(Meta, cls);
            }
        return m;
    }

    static IEnumerable<(string, Variant)> Uniforms(LookClass c)
    {
        var e = c.Cel;
        yield return ("cel_band", new Vector4(e.Band[0], e.Band[1], e.Band[2], e.Band[3]));
        yield return ("cel_mid", new Color(e.Mid[0], e.Mid[1], e.Mid[2], e.Mid[3]));
        yield return ("cel_form", e.Form);
        yield return ("cel_spec", new Vector4(e.Spec[0], e.Spec[1], e.Spec[2], e.Spec[3]));
        yield return ("cel_nmap", e.Nmap);
        yield return ("cel_ink", e.Ink);
        yield return ("cel_rim_k", e.RimK);
        if (c.Edge is { } ed) yield return ("cel_edge", new Vector2(ed[0], ed[1]));
        // (L1 l9 PACK2) the class's own rim hue (vat.gdshaderinc cel_edge_hue): linear, at luminance 1
        if (c.EdgeColor is { } ec)
        {
            var l = new Color(ec).SrgbToLinear();
            float y = Mathf.Max(l.R * 0.2126f + l.G * 0.7152f + l.B * 0.0722f, 1e-4f);
            yield return ("cel_edge_hue", new Vector4(l.R / y, l.G / y, l.B / y, 1f));
        }
        var al = c.AlbUniform;
        yield return ("cel_alb", new Vector4(al[0], al[1], al[2], al[3]));
        var ah = c.AlbHueUniform;
        yield return ("cel_alb_hue", new Vector4(ah[0], ah[1], ah[2], 0f));
    }

    static readonly Dictionary<ulong, bool> celShaders = new();
    /// <summary>Whether a shader is on the cel model (it has the include's per-material uniforms).</summary>
    static bool UsesCel(Shader? s)
    {
        if (s == null) return false;
        var id = s.GetInstanceId();
        if (!celShaders.TryGetValue(id, out var v))
            celShaders[id] = v = s.GetShaderUniformList().Any(u => (string)u.AsGodotDictionary()["name"] == "cel_ink");
        return v;
    }

    /* ------------------------------------------------------------------ the loader -- */

    static SceneTree? tree;
    static readonly List<GeometryInstance3D> queue = new();
    static readonly HashSet<ulong> seen = new();
    static readonly Dictionary<string, Shader> variants = new();
    static readonly List<(BaseMaterial3D M, string Key, string Cls)> live = new();
    static int sweep, watchAt;
    // (B2r2) The late-assigned: a mesh whose material (or mesh) is set after it entered the tree and was first visited.
    // Each visited mesh is looked at again every frame for its first YoungFrames frames (a spawn site's material set a
    // frame or two late), then joins the watch, a few of which are looked at again each frame (a pooled piece re-dressed
    // later). Visit is cheap on what it has seen (one id lookup per material), so neither scans the tree.
    const int YoungFrames = 30, WatchPerFrame = 24;
    static readonly List<(GeometryInstance3D G, ulong Id, int Left)> young = new();
    static readonly List<(GeometryInstance3D G, ulong Id)> watch = new();
    static readonly HashSet<ulong> tracked = new();

    /// <summary>Hooks the tree (once): every world mesh added from now on, and those already there.</summary>
    public static void Install(SceneTree t)
    {
        if (tree != null || !On) return;
        tree = t;
        t.NodeAdded += n => { if (n is MeshInstance3D or MultiMeshInstance3D) queue.Add((GeometryInstance3D)n); };
        RenderingServer.FramePreDraw += Drain;
        foreach (var n in t.Root.FindChildren("*", "GeometryInstance3D", true, false)) if (n is MeshInstance3D or MultiMeshInstance3D) queue.Add((GeometryInstance3D)n);
    }

    static void Drain()
    {
        if (queue.Count > 0)
        {
            var q = queue.ToArray();
            queue.Clear();
            foreach (var g in q)
                if (GodotObject.IsInstanceValid(g) && g.IsInsideTree() && g.GetViewport() == tree!.Root)
                {
                    Hero(g);
                    foreach (var (m, _) in Slots(g)) Visit(m, g);
                    var id = g.GetInstanceId();
                    if (tracked.Add(id)) young.Add((g, id, YoungFrames));
                }
        }
        for (int i = young.Count - 1; i >= 0; i--)
        {
            var (g, id, left) = young[i];
            if (!GodotObject.IsInstanceValid(g)) { young.RemoveAt(i); tracked.Remove(id); continue; }
            if (g.IsInsideTree()) { Hero(g); foreach (var (m, _) in Slots(g)) Visit(m, g); }
            if (left > 1) young[i] = (g, id, left - 1);
            else { young.RemoveAt(i); watch.Add((g, id)); }
        }
        for (int i = 0; i < WatchPerFrame && watch.Count > 0; i++)
        {
            watchAt = (watchAt + 1) % watch.Count;
            var (g, id) = watch[watchAt];
            if (!GodotObject.IsInstanceValid(g)) { tracked.Remove(id); watch[watchAt] = watch[^1]; watch.RemoveAt(watch.Count - 1); continue; }
            if (g.IsInsideTree() && g.IsVisibleInTree()) { Hero(g); foreach (var (m, _) in Slots(g)) Visit(m, g); }
        }
        // (a converted material whose feature set changed since: the engine bound its own shader for the new set)
        for (int i = 0; i < 4 && live.Count > 0; i++)
        {
            sweep = (sweep + 1) % live.Count;
            var (m, key, cls) = live[sweep];
            if (!GodotObject.IsInstanceValid(m)) { live.RemoveAt(sweep); continue; }
            var k = KeyOf(m);
            if (k != key) { live.RemoveAt(sweep); if (Why(m) is null) Bind(m, cls); }
        }
    }

    /// <summary>A mesh's materials as the renderer picks them: the override (over every surface) or each surface's
    /// override or own, and the overlay.</summary>
    static IEnumerable<(Material M, string Where)> Slots(GeometryInstance3D g)
    {
        if (g.MaterialOverride is { } o) yield return (o, "material_override");
        if (g.MaterialOverlay is { } ov) yield return (ov, "material_overlay");
        if (g.MaterialOverride != null) yield break;
        var mi = g as MeshInstance3D;
        var mesh = mi != null ? mi.Mesh : (g as MultiMeshInstance3D)?.Multimesh?.Mesh;
        if (mesh == null) yield break;
        for (int s = 0; s < mesh.GetSurfaceCount(); s++)
        {
            var so = mi != null && s < mi.GetSurfaceOverrideMaterialCount() ? mi.GetSurfaceOverrideMaterial(s) : null;
            if (so != null) yield return (so, $"surface {s} (override)");
            else if (mesh.SurfaceGetMaterial(s) is { } sm) yield return (sm, $"surface {s}");
        }
    }

    static void Visit(Material m, GeometryInstance3D g)
    {
        for (Material? p = m; p != null; p = p.NextPass)
        {
            if (!seen.Add(p.GetInstanceId())) continue;
            if (p is BaseMaterial3D b)
            {
                if (Why(b) is null) Bind(b, ClassFor(null, b.ResourceName, Asset(b, g)));
            }
            else if (p is ShaderMaterial sm && !sm.HasMeta(Meta) && sm.Shader is { } sh && Lib.Shaders.ContainsKey(sh.ResourcePath)
                     && !Lib.Excluded(sh.ResourcePath, sm.ResourceName) && UsesCel(sh)
                     && Lib.ClassFor(sh.ResourcePath, sm.ResourceName, Asset(sm, g)) is { } c)
                Apply(sm, c);
        }
    }

    static string ClassFor(string? shader, string? material, string? asset) => Lib.ClassFor(shader, material, asset) ?? Lib.Fallback;

    /// <summary>The asset a material came from: its own path (an imported scene's sub-resource), else the scene the node is part of.</summary>
    static string? Asset(Material m, Node g)
    {
        var p = m.ResourcePath;
        if (!string.IsNullOrEmpty(p)) return p.Split("::")[0];
        for (Node? n = g; n != null; n = n.GetParent())
            if (!string.IsNullOrEmpty(n.SceneFilePath)) return n.SceneFilePath;
        return null;
    }

    /// <summary>Why a standard material is not converted (null: it is), and whether that leaves it lit off the model.</summary>
    static (string What, bool Off)? Why(BaseMaterial3D b)
    {
        if (b.ShadingMode == BaseMaterial3D.ShadingModeEnum.Unshaded) return ("unshaded", false);
        if (b.BlendMode != BaseMaterial3D.BlendModeEnum.Mix) return ("FX blend", false);
        if (b.BillboardMode != BaseMaterial3D.BillboardModeEnum.Disabled) return ("billboard (FX)", false);
        if (Lib.Excluded(null, b.ResourceName)) return ("excluded by name", false);
        if (b.ShadingMode == BaseMaterial3D.ShadingModeEnum.PerVertex) return ("per-vertex lighting (a custom light() is per pixel)", true);
        return null;
    }

    /// <summary>Puts one standard material on the model in its class (the loader does it to every one it finds; the lookdev swatches call it).</summary>
    public static void Bind(BaseMaterial3D b, string cls)
    {
        var key = KeyOf(b);
        if (!variants.TryGetValue(key, out var sh))
        {
            bool hero = b.HasMeta(HeroMeta);
            var head = (b.RimEnabled ? "#define CEL_BUILTIN_RIM\n" : "") + (b.ClearcoatEnabled ? "#define CEL_CLEARCOAT\n" : "")
                + (hero ? "#define CEL_HERO\n#define CEL_HERO_ARM\n" : "") + "#include \"res://shaders/std_cel.gdshaderinc\"";
            var code = StdCelCode.Generate(b, head, hero ? "\tCEL_FRAGMENT;\n\tCEL_HERO_ARM_FRAGMENT;" : "\tCEL_FRAGMENT;");
            if (hero) code = code.Replace("void vertex() {", "void vertex() {\n\tCEL_HERO_ARM_VERTEX;");
            variants[key] = sh = new Shader { Code = code };
        }
        var rid = b.GetRid();
        RenderingServer.MaterialSetShader(rid, sh.GetRid());
        foreach (var (name, v) in Uniforms(Lib.Classes[cls])) RenderingServer.MaterialSetParam(rid, name, v);
        b.SetMeta(Meta, cls);
        live.Add((b, key, cls));
    }

    /// <summary>(L1 lead 19, HER3) A hero's held piece (cel.gdshaderinc CEL_HERO_ARM): its material's own variant.</summary>
    const string HeroMeta = "cel_hero_arm";
    static string KeyOf(BaseMaterial3D b) => StdCelCode.Key(b) + (b.HasMeta(HeroMeta) ? "|hero" : "");

    /// <summary>(L1 lead 19, HER3) The standard materials of a mesh under the player's view (her shield, her blade) become
    /// HER OWN copies, marked for the hero's variant: a body in her lit pool (the rig's hero_pool), as they were without
    /// the row. A surface that has her own copy already (PlayerView.WeaponClose's) is marked; any other gets a copy as a
    /// surface override. Other holders of the same weapon keep the shared material.</summary>
    static void Hero(GeometryInstance3D g)
    {
        if (g is not MeshInstance3D mi || mi.Mesh == null) return;
        Node? n = g;
        while (n != null && !n.IsInGroup(Brush.HerGroup)) n = n.GetParent();
        if (n == null) return;
        for (int s = 0; s < mi.Mesh.GetSurfaceCount() && s < mi.GetSurfaceOverrideMaterialCount(); s++)
        {
            var so = mi.GetSurfaceOverrideMaterial(s);
            if (so is BaseMaterial3D ob)
            {
                if (ob.HasMeta(HeroMeta)) continue;
                ob.SetMeta(HeroMeta, true);
                if (ob.HasMeta(Meta)) Bind(ob, (string)ob.GetMeta(Meta));   // (bound before she held it: bound again, the sweep drops the old entry)
            }
            else if (so == null && mi.Mesh.SurfaceGetMaterial(s) is BaseMaterial3D b && Why(b) is null)
            {
                var c = (BaseMaterial3D)b.Duplicate();
                c.SetMeta(HeroMeta, true);
                mi.SetSurfaceOverrideMaterial(s, c);
            }
        }
    }

    /// <summary>How many standard materials are on the model, and the shader variants made for them.</summary>
    public static (int Materials, int Variants) Count => (live.Count, variants.Count);

    /* ------------------------------------------------------------------- the audit -- */

    static readonly Regex Unshaded = new(@"render_mode[^;]*\bunshaded\b"), FxBlend = new(@"render_mode[^;]*\bblend_(add|sub|mul|premul_alpha)\b"),
        Spatial = new(@"shader_type\s+spatial\b");
    static readonly Regex Water = new("water|river|ford_|puddle", RegexOptions.IgnoreCase);

    /// <summary>--cel-audit: every lit material of the world not on the model, at this moment (Shots calls it at each frame saved).</summary>
    public static void AuditPrint(string tag)
    {
        if (!Audit || tree == null && !(Engine.GetMainLoop() is SceneTree)) return;
        var t = tree ?? (SceneTree)Engine.GetMainLoop();
        var off = new Dictionary<ulong, (string Line, int N)>();
        var on = new SortedDictionary<string, int>();
        void Count(string k) => on[k] = on.GetValueOrDefault(k) + 1;
        foreach (var n in t.Root.FindChildren("*", "GeometryInstance3D", true, false))
        {
            var g = (GeometryInstance3D)n;
            if (!g.IsVisibleInTree()) continue;
            if (g.GetViewport() != t.Root) { Count("excluded: UI viewport"); continue; }
            if (g is not (MeshInstance3D or MultiMeshInstance3D)) { Count($"excluded: {g.GetClass()} (FX, text)"); continue; }
            foreach (var (m, where) in Slots(g))
                for (Material? p = m; p != null; p = p.NextPass)
                {
                    var st = Status(p);
                    if (st != null) { Count(st); continue; }
                    var id = p.GetInstanceId();
                    off[id] = off.TryGetValue(id, out var o) ? (o.Line, o.N + 1)
                        : ($"{g.GetPath()} | '{p.ResourceName}' {p.GetClass()}{(p.ResourcePath != "" ? " " + p.ResourcePath : "")}{(p is ShaderMaterial q ? $" shader '{q.Shader?.ResourcePath}'" : "")} | {where}", 1);
                }
        }
        GD.Print($"cel-audit {tag}: {off.Count} lit materials off the model ({off.Values.Sum(v => v.N)} uses); {live.Count} standard materials converted in {variants.Count} variants");
        foreach (var v in off.Values.OrderBy(v => v.Line)) GD.Print($"cel-audit   OFF {v.Line}{(v.N > 1 ? $" (x{v.N})" : "")}");
        GD.Print("cel-audit   " + string.Join("; ", on.Select(kv => $"{kv.Key} {kv.Value}")));
    }

    static string? Status(Material p)
    {
        if (p is BaseMaterial3D b)
        {
            if (b.HasMeta(Meta)) return $"std_cel {(string)b.GetMeta(Meta)}";
            var w = Why(b);
            return w is { Off: false } ? "excluded: " + w.Value.What : null;
        }
        if (p is ShaderMaterial sm)
        {
            var s = sm.Shader;
            if (s == null) return "excluded: no shader";
            var code = s.Code;
            if (!Spatial.IsMatch(code)) return "excluded: not spatial";
            if (Unshaded.IsMatch(code)) return "excluded: unshaded";
            if (FxBlend.IsMatch(code)) return "excluded: FX blend";
            if (Lib.Excluded(s.ResourcePath, sm.ResourceName)) return "excluded: by the library";
            if (UsesCel(s)) return sm.HasMeta(Meta) ? $"cel {(string)sm.GetMeta(Meta)}" : "cel (shader default)";
            if (Water.IsMatch(s.ResourcePath) || Water.IsMatch(sm.ResourceName)) return "excluded: water surface";
            return null;
        }
        return "excluded: " + p.GetClass();
    }
}
