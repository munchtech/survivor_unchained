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
        LineStep();
        HeroClassStep();
        if (HeroId) HeroIdStep();
    }

    /// <summary>(L1 lead 22, HERPAIR) Every material on a mesh under the player's view that goes through the hero paint
    /// (the uniform cel_hero_class of cel.gdshaderinc's CEL_HERO block) gets its CLASS once (Rigs.HeroClassOf: its shader's
    /// file and its outfit kind): the rig's value pair per class (hero_pool values 36-44) lands it. The ID's walk.</summary>
    static readonly Dictionary<ulong, int> heroClasses = new();
    static readonly Dictionary<ulong, bool> heroClassShader = new();
    static void HeroClassStep()
    {
        foreach (var (g, _) in lined)
        {
            if (!GodotObject.IsInstanceValid(g) || !g.IsInsideTree()) continue;
            foreach (var (m, _) in Slots(g))
                for (Material? p = m; p != null; p = p.NextPass)
                {
                    if (p is not ShaderMaterial { Shader: { } sh } sm || heroClasses.ContainsKey(p.GetInstanceId())) continue;
                    var sid = sh.GetInstanceId();
                    if (!heroClassShader.TryGetValue(sid, out bool has))
                    {
                        has = false;
                        foreach (var d in RenderingServer.GetShaderParameterList(sh.GetRid()))
                            if (d["name"].AsString() == "cel_hero_class") { has = true; break; }
                        heroClassShader[sid] = has;
                    }
                    int cls = -1;
                    if (has)
                    {
                        var kv = sm.GetShaderParameter("kind");
                        cls = SurvivorUnchained.Look.Rigs.HeroClassOf(sh.ResourcePath.GetFile(), kv.VariantType == Variant.Type.Int ? kv.AsInt32() : -1);
                        if (cls >= 0) sm.SetShaderParameter("cel_hero_class", (float)cls);
                    }
                    heroClasses[p.GetInstanceId()] = cls;
                }
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
        bool mirror = false;   // (HER5: her reflection's copies are placed by their own vertex code: no line, as PlayerView.Gather leaves them out)
        while (n != null && !n.IsInGroup(Brush.HerGroup)) { mirror |= n is global::SurvivorUnchained.View.Reflections; n = n.GetParent(); }
        if (n == null) return;
        if (!mirror && n is Node3D her && lineIds.Add(mi.GetInstanceId())) lined.Add((mi, her));
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

    /* ------------------------------------------------------------------ her line -- */

    /// <summary>(L1 lead 20, HER5) The hero's LINE (hero_line.gdshader): every solid mesh under the player's view wears the
    /// hull as its overlay while the rig's hero rule is on (Atmosphere.HeroLinePx), six passes, one per direction. Where
    /// the overlay is another's (her x-ray, a wraith's walk: PlayerView's own materials) the hull is the last of its
    /// passes. Off: taken away again, so a rig without the row draws nothing more than before.</summary>
    const int LinePasses = 6;
    const string LineName = "hero_line";
    static readonly List<(MeshInstance3D G, Node3D Her)> lined = new();
    static readonly HashSet<ulong> lineIds = new();
    static readonly Dictionary<ulong, bool> lineShader = new();
    static ShaderMaterial? line;
    // (lead 22, HAIRLINE) hair: a chain per OPAQUE surface (its first material -> our passes hung after its last pass), cut
    // like that surface; never the overlay, which would also draw the blended cap and fine hairs' whole cards
    static readonly Dictionary<Material, ShaderMaterial> lineCut = new();
    const float LineHairCut = 0.3f;   // (the strands' cover from which the hull counts them: their blended fringe's reach)
    static readonly HashSet<ulong> lineHairIds = new();
    static readonly Dictionary<Material, ShaderMaterial> lineOver = new();   // (another's overlay -> our passes with it after them)
    static bool lineWas;

    static ShaderMaterial LineChain(bool hair, ShaderMaterial? cutBy = null)
    {
        var sh = GD.Load<Shader>("res://shaders/hero_line.gdshader");
        ShaderMaterial? first = null, last = null;
        for (int i = 0; i < LinePasses; i++)
        {
            float a = Mathf.Tau * i / LinePasses;   // (from 0: her sides, the long edges of a standing figure, take the full width)
            var m = new ShaderMaterial { Shader = sh, ResourceName = LineName };
            m.SetShaderParameter("dir", new Vector2(Mathf.Cos(a), Mathf.Sin(a)));
            if (hair) m.SetShaderParameter("near_px", 250f);   // (hair cards: the hull is the card's quad, so no line in a close view)
            if (cutBy != null) LineCutBy(m, cutBy);
            if (last == null) first = m; else last.NextPass = m;
            last = m;
        }
        // (L1 lead 22, R2INK) the interior ink (hero_ink.gdshader): the chain's last pass, on her own visible pixels, cut as the
        // hull is on hair; named as the line so every walk of the chain (take off, floor_y) treats it as the line's
        if (InkOn)
        {
            var ink = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/hero_ink.gdshader"), ResourceName = LineName };
            if (cutBy != null) LineCutBy(ink, cutBy);
            last!.NextPass = ink;
        }
        return first!;
    }
    static readonly bool InkOn = string.IsNullOrEmpty(System.Environment.GetEnvironmentVariable("SU_HERO_INK_OFF"));

    static bool IsLine(Material? m) => m is ShaderMaterial { ResourceName: LineName };

    /// <summary>(lead 22) A hair surface the line goes round: a lit, depth-writing hair shader (the cards' core, the braid's
    /// ropes, the tie), never the blended cap or fine hairs (depth_draw_never) nor the cap drawn as a core.</summary>
    static bool HairOpaque(Material? m) => m is ShaderMaterial { Shader: { } sh } sm && sh.ResourcePath.Contains("heroine_hair")
        && ShaderLines(sh) && !(sm.GetShaderParameter("cap").AsBool() && !sh.ResourcePath.Contains("rope_core"));

    /// <summary>The pass's cut, as its hair surface cuts (heroine_hair.gdshaderinc's cover): 2 the braid's ropes, 0 the tie
    /// (solid), else 1 a card at core_cut (a hashed one at half).</summary>
    static void LineCutBy(ShaderMaterial pass, ShaderMaterial src)
    {
        var path = src.Shader.ResourcePath;
        int mode = path.Contains("rope_core") ? 2 : src.GetShaderParameter("tie").AsBool() ? 0 : 1;
        var cc = src.GetShaderParameter("core_cut");
        float cut = path.Contains("_core") ? (cc.VariantType == Variant.Type.Nil ? 0.9f : cc.AsSingle()) : 0.5f;
        // (hairline_01: cut at the core's own 0.9 the hull sat under the blended fringe the over/soft passes draw past the
        // core, which washed the line to L 0.31-0.38 against the body's 0.19; cut at the fringe's visible reach instead)
        cut = Mathf.Min(cut, LineHairCut);
        // (no atlas, as on the tie: no cut; a null sampler set on a pass is "not a valid texture" at draw)
        if (src.GetShaderParameter("strands").AsGodotObject() is Texture2D tex) pass.SetShaderParameter("cut_tex", tex); else mode = 0;
        pass.SetShaderParameter("cut_mode", mode);
        pass.SetShaderParameter("cut", cut);
        pass.SetShaderParameter("cut_bias", src.GetShaderParameter("strand_bias").VariantType == Variant.Type.Nil ? 0f : src.GetShaderParameter("strand_bias").AsSingle());
    }

    static bool ShaderLines(Shader sh)
    {
        var id = sh.GetInstanceId();
        if (!lineShader.TryGetValue(id, out var ok))
        {
            var code = sh.Code;
            lineShader[id] = ok = Spatial.IsMatch(code) && !Unshaded.IsMatch(code) && !FxBlend.IsMatch(code) && !code.Contains("depth_draw_never");
        }
        return ok;
    }

    static Material? SurfaceMat(MeshInstance3D g, int s) => (s < g.GetSurfaceOverrideMaterialCount() ? g.GetSurfaceOverrideMaterial(s) : null) ?? g.Mesh.SurfaceGetMaterial(s);

    /// <summary>(lead 22) Hangs (want) or takes off the line on each of a hair mesh's surfaces: our passes after the last of
    /// an opaque surface's own; the soft ones never. Returns what it did per surface, for the print.</summary>
    static string HairLine(MeshInstance3D g, bool want)
    {
        string said = "";
        int n = g.Mesh?.GetSurfaceCount() ?? 0;
        for (int s = 0; s < n; s++)
        {
            if (SurfaceMat(g, s) is not ShaderMaterial m) { said += $" s{s}:-"; continue; }
            Material tail = m;
            while (tail.NextPass != null && !IsLine(tail.NextPass)) tail = tail.NextPass;
            bool has = IsLine(tail.NextPass), wants = want && HairOpaque(m);
            if (wants && !has)
            {
                if (!lineCut.TryGetValue(m, out var chain)) lineCut[m] = chain = LineChain(true, m);
                tail.NextPass = chain;
            }
            else if (!wants && has) tail.NextPass = null;
            said += $" s{s}:{(wants ? "line" : "-")}";
        }
        return said;
    }

    /// <summary>A mesh the line goes round: drawn (no shadow proxy), every surface a lit, solid material. Hair: its own chain.</summary>
    static bool LineFits(MeshInstance3D g, out bool hair)
    {
        hair = false;
        // (lead 21) a mesh the camera does not draw takes no line: hidden in the tree, a shadow-only proxy, a ghost's fade
        if (g.Mesh == null || !g.IsVisibleInTree() || g.CastShadow == GeometryInstance3D.ShadowCastingSetting.ShadowsOnly || g.MaterialOverride != null || g.Transparency > 0) return false;
        if (g.GetViewport()?.GetCamera3D() is { } cam && (g.Layers & cam.CullMask) == 0) return false;   // (on no layer the view's camera draws)
        int n = g.Mesh.GetSurfaceCount();
        for (int s = 0; s < n; s++)
        {
            var m = SurfaceMat(g, s);
            // (lead 22) a hair surface: lined on its own if opaque (HairLine), the soft ones left out; the mesh still fits
            if (m is ShaderMaterial { Shader: { } hs } && hs.ResourcePath.Contains("heroine_hair")) { hair = true; continue; }
            if (m is BaseMaterial3D b) { if (Why(b) is not null || b.Transparency == BaseMaterial3D.TransparencyEnum.Alpha) return false; }
            else if (m is ShaderMaterial { Shader: { } sh })
            {
                if (!ShaderLines(sh)) return false;
            }
            else return false;
        }
        if (hair) { bool any = false; for (int s = 0; s < n && !any; s++) any = HairOpaque(SurfaceMat(g, s)); return any; }
        return n > 0;
    }

    /// <summary>(lead 21) A dev print, off unless the environment has SU_HERO_LINE_PRINT: each lined mesh once per change of
    /// state (its path, whether it is drawn, its shadow mode, layers, fade, skin, overlay passes, first surface's shader).</summary>
    static readonly bool LinePrint = !string.IsNullOrEmpty(System.Environment.GetEnvironmentVariable("SU_HERO_LINE_PRINT"));
    static readonly Dictionary<ulong, string> lineSaid = new();
    static void LineSay(MeshInstance3D g, bool want, bool hair, Material? ov, string surfs = "")
    {
        var m = g.Mesh == null || g.Mesh.GetSurfaceCount() == 0 ? null : (g.GetSurfaceOverrideMaterialCount() > 0 ? g.GetSurfaceOverrideMaterial(0) : null) ?? g.Mesh.SurfaceGetMaterial(0);
        string sh = m switch { ShaderMaterial { Shader: { } x } => x.ResourcePath + " [" + (Regex.Match(x.Code, @"render_mode[^;]*").Value) + "]", BaseMaterial3D b => "std " + b.ResourceName + " transp " + b.Transparency, null => "none", _ => m.GetClass() };
        string passes = "";
        for (var p = ov; p != null; p = p.NextPass) passes += (p is ShaderMaterial { Shader: { } o } ? (IsLine(p) ? "line" : o.ResourcePath.GetFile()) : p.GetClass()) + ">";
        var cam = g.GetViewport()?.GetCamera3D();
        string say = $"want {want} hair {hair} vis {g.Visible}/{g.IsVisibleInTree()} cast {g.CastShadow} layers {g.Layers} cam_mask {cam?.CullMask} fade {g.Transparency} skin {g.Skin != null} surfs {g.Mesh?.GetSurfaceCount()} overlay {passes}{(surfs.Length > 0 ? " hair_surfaces" + surfs : "")} | {sh}";
        var id = g.GetInstanceId();
        if (lineSaid.TryGetValue(id, out var was) && was == say) return;
        lineSaid[id] = say;
        GD.Print($"HERO_LINE {Engine.GetFramesDrawn()} {g.GetPath()} : {say}");
    }

    static void LineStep()
    {
        bool on = Atmosphere.HeroLinePx > 0;
        if (!on && !lineWas) return;
        lineWas = on;
        Node3D? at = null;
        for (int i = lined.Count - 1; i >= 0; i--)
        {
            var (g, her) = lined[i];
            if (!GodotObject.IsInstanceValid(g) || !GodotObject.IsInstanceValid(her)) { lined.RemoveAt(i); continue; }
            if (!g.IsInsideTree()) continue;
            at = her;
            bool hair = false, fits = on && LineFits(g, out hair);
            // (lead 22) hair: per surface, never the overlay
            bool want = fits && !hair;
            string surfs = "";
            if (fits && hair && lineHairIds.Add(g.GetInstanceId()) || lineHairIds.Contains(g.GetInstanceId())) surfs = HairLine(g, fits && hair);
            var ov = g.MaterialOverlay;
            if (LinePrint) LineSay(g, want || fits && hair, hair, ov, surfs);
            if (ov == null) { if (want) g.MaterialOverlay = line ??= LineChain(false); }
            else if (IsLine(ov)) { if (!want) { Material? under = ov; while (IsLine(under)) under = under!.NextPass; g.MaterialOverlay = under; } }
            else if (want)
            {
                // (lead 21) another's overlay (her x-ray, a wraith's walk): OUR passes first, its own after them, as this mesh's
                // overlay. Never a pass hung on ITS material: the x-ray's one material is also the overlay of meshes the line
                // must not reach (each mesh's FxAfterHole copy, drawn for another camera on layer 20: the fill of her5_01).
                if (!lineOver.TryGetValue(ov, out var over))
                {
                    lineOver[ov] = over = LineChain(false);
                    Material last = over;
                    while (last.NextPass != null) last = last.NextPass;
                    last.NextPass = ov;
                }
                g.MaterialOverlay = over;
            }
        }
        if (on && at != null && at.IsInsideTree())
        {
            float y = at.GlobalPosition.Y;
            foreach (var first in lineOver.Values.Append(line).Concat(lineCut.Values))
                for (Material? p = first; IsLine(p); p = p!.NextPass) ((ShaderMaterial)p!).SetShaderParameter("floor_y", y);
        }
    }

    /* -------------------------------------------------------------------- her ID -- */

    /// <summary>(L1 lead 21, HERMASK) A dev instrument, off unless the environment has SU_HERO_ID: every material on a mesh
    /// under the player's view that goes through the hero paint (the uniform cel_hero_id of cel.gdshaderinc's CEL_HERO
    /// block) is drawn as ONE flat color, its ID; whatever of her does not go through it stays as rendered. The table goes
    /// to the log (lines HERO_ID: mesh, slot, pass, material, shader, the mesh's state), once and again on a change.</summary>
    static readonly bool HeroId = !string.IsNullOrEmpty(System.Environment.GetEnvironmentVariable("SU_HERO_ID"));
    static readonly Dictionary<ulong, int> heroIds = new();   // (material -> its ID; -1: a shader with no hero paint)
    static readonly Dictionary<string, string> heroIdSaid = new();
    static int heroIdNext;
    // (22 colors that stay apart after the tonemap and off the floor's orange and the line's dark: six hues and a grey
    // at levels a factor 4 apart; yellow, red and violet land on the floor or on each other. More materials than
    // colors: the ids wrap and the log says so.)
    static readonly float[][] HeroIdHues = { new[] { 0f, 1f, 0f }, new[] { 1f, 0f, 1f }, new[] { 0f, 1f, 1f }, new[] { 0f, 0f, 1f },
        new[] { 0f, 1f, 0.45f }, new[] { 0f, 0.45f, 1f }, new[] { 1f, 1f, 1f } };
    static readonly (int Hue, float Level)[] HeroIdTable = Enumerable.Range(0, 7).Select(h => (h, 1.2f)).Concat(Enumerable.Range(0, 7).Select(h => (h, 0.3f)))
        .Concat(Enumerable.Range(0, 6).Select(h => (h, 0.075f))).Concat(Enumerable.Range(0, 2).Select(h => (h, 0.019f))).ToArray();
    static Vector4 HeroIdColor(int id)
    {
        var (hue, k) = HeroIdTable[id % HeroIdTable.Length];
        var h = HeroIdHues[hue];
        return new Vector4(h[0] * k, h[1] * k, h[2] * k, 1f);
    }

    static void HeroIdStep()
    {
        foreach (var (g, her) in lined)
        {
            if (!GodotObject.IsInstanceValid(g) || !GodotObject.IsInstanceValid(her) || !g.IsInsideTree() || g.Mesh == null) continue;
            uint mask = g.GetViewport()?.GetCamera3D()?.CullMask ?? 0;
            // (only a mesh the play camera draws takes an ID: her hidden pieces and the layer 20 copies use none of the 25 colors)
            bool drawn = g.IsVisibleInTree() && g.CastShadow != GeometryInstance3D.ShadowCastingSetting.ShadowsOnly && (g.Layers & mask) != 0;
            string state = $"vis {g.IsVisibleInTree()} cast {g.CastShadow} layers {g.Layers} cam_mask {mask} fade {g.Transparency}";
            foreach (var (m, where) in Slots(g))
            {
                int k = -1;
                for (Material? p = m; p != null; p = p.NextPass)
                {
                    k++;
                    if (IsLine(p)) continue;
                    var mid = p.GetInstanceId();
                    if (!heroIds.TryGetValue(mid, out int id)) id = -1;
                    if (id < 0 && !heroIds.ContainsKey(mid) && drawn)
                    {
                        if (p is ShaderMaterial { Shader: { } sh } sm)
                        {
                            // (an unshaded variant, the hair's erase pass, has the uniform and never writes the paint)
                            if (!Unshaded.IsMatch(sh.Code))
                                foreach (var d in RenderingServer.GetShaderParameterList(sh.GetRid()))
                                    if (d["name"].AsString() == "cel_hero_id") { id = heroIdNext++; break; }
                            heroIds[mid] = id;
                            if (id >= 0) sm.SetShaderParameter("cel_hero_id", HeroIdColor(id));
                        }
                        else if (p is BaseMaterial3D b && b.HasMeta(HeroMeta) && b.HasMeta(Meta)) heroIds[mid] = id = heroIdNext++;   // (her held piece's own variant)
                    }
                    if (id >= 0 && p is BaseMaterial3D held) RenderingServer.MaterialSetParam(held.GetRid(), "cel_hero_id", HeroIdColor(id));   // (a bind sets its parameters again)
                    string wears = p switch
                    {
                        ShaderMaterial { Shader: { } x } => (x.ResourcePath.Length > 0 ? x.ResourcePath.GetFile() : "(built)") + " [" + Regex.Match(x.Code, @"render_mode[^;]*").Value + "]",
                        BaseMaterial3D b => "std transp " + b.Transparency + " shading " + b.ShadingMode,
                        _ => p.GetClass(),
                    };
                    if (id == HeroIdTable.Length && heroIdSaid.TryAdd("wrapped", "")) GD.Print("HERO_ID WRAPPED: more painted materials than the ", HeroIdTable.Length, " colors; ids share colors from here");
                    var c = id >= 0 ? HeroIdColor(id) : default;
                    string say = FormattableString.Invariant($"id {id} rgb {c.X:0.###} {c.Y:0.###} {c.Z:0.###} | {where} pass {k} | {p.ResourceName} | {wears} | {state} | class {(heroClasses.TryGetValue(mid, out int hcl) ? hcl : -1)}");
                    string key = g.GetInstanceId() + "|" + where + "|" + k;
                    if (heroIdSaid.TryGetValue(key, out var was) && was == say) continue;
                    heroIdSaid[key] = say;
                    GD.Print($"HERO_ID {Engine.GetFramesDrawn()} {her.GetPathTo(g)} : {say}");
                }
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
