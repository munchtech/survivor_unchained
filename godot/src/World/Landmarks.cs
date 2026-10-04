using System.Collections.Generic;
using System.Globalization;
using System.Text.Json;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// Everything the web game stands up in a zone that is not the ground, its
/// flora or a kit piece (the camps, the Hunters' Blind, ruins, the KayKit
/// props, a lantern's flame), exported where it stands as landmarks.glb
/// (tools/godot/export_zone.mjs). What glTF cannot say the exporter puts in
/// a material's name, 'key=value|...':
///   kit=NAME     a world kit material: taken from the kit, weathered (KitLook)
///   hdr=R,G,B    an unlit colour brighter than white (linear)
///   add          drawn additively
/// The pieces the runtime reaches for (a glowing bit, a gate, a wheel) are
/// nodes of their own, found by name (Nodes). The KayKit props are nodes of
/// their own too (kk-PACK-NAME-N), swapped for better pieces (Pieces).
/// </summary>
public sealed class Landmarks
{
    public readonly Node3D Root;
    /// <summary>Every node by name (the runtime's are unique).</summary>
    public readonly Dictionary<string, Node3D> Nodes = new();

    readonly ZoneData zone;

    public Landmarks(ZoneData z)
    {
        zone = z;
        // (A map made for a run has none: its pieces are all flora and fires.)
        var file = $"{z.Dir}/landmarks.glb";
        Root = ResourceLoader.Exists(file) ? GD.Load<PackedScene>(file).Instantiate<Node3D>() : new Node3D();
        Root.Name = "Landmarks";
        Walk(Root);
        foreach (var n in z.Meta.HiddenNodes) if (Nodes.TryGetValue(n, out var h)) h.Visible = false;
    }

    void Walk(Node n)
    {
        foreach (var c in n.GetChildren())
        {
            // A KayKit piece (kk-PACK-NAME-N): a better one in its place, where there is one.
            if (c is Node3D kk && kk.Name.ToString().StartsWith("kk-") && Swap(kk)) continue;
            if (c is Node3D n3 && !Nodes.ContainsKey(n3.Name)) Nodes[n3.Name] = n3;
            if (c is MeshInstance3D m && m.Mesh != null)
            {
                for (int i = 0; i < m.Mesh.GetSurfaceCount(); i++)
                    if (m.Mesh.SurfaceGetMaterial(i) is Material mat && Remade(mat) is Material to) m.SetSurfaceOverrideMaterial(i, to);
                // Shadows from the big pieces only.
                if (m.GetAabb().Size.Length() < 0.8f) m.CastShadow = GeometryInstance3D.ShadowCastingSetting.Off;
            }
            Walk(c);
        }
    }

    /// <summary>
    /// The plain pieces gathered into one mesh per material, per kind of
    /// vertex, per 32 m square: the unnamed, visible, opaque meshes nothing
    /// reaches for by name (the runtime's nodes are named: night-, glow-,
    /// bramble-, cage-, kk- and whatever the zone's refs list). Each was a
    /// draw of its own in the picture and again in every shadow cascade
    /// (the Verge's 788, the Waystation's 223). The originals stay, hidden,
    /// so a lookup by name still finds them. Called once the place has hidden
    /// what it hides (the stones under a fire). Only with --merge-landmarks
    /// for now (to be measured and looked at first).
    /// </summary>
    public void Merge()
    {
        // Not yet measured or looked at in the game: only with --merge-landmarks until it has been.
        if (!Args.Has("merge-landmarks")) return;
        var keep = new HashSet<string>(zone.Meta.NightNodes);
        keep.UnionWith(zone.Meta.HiddenNodes);
        foreach (var l in zone.Meta.Lights) keep.UnionWith(l.Glow);
        Strings(zone.Meta.Refs, keep);
        keep.Add("pump_wheel");
        var groups = new Dictionary<(ulong Mat, ulong Format, int X, int Z, bool Shadow), (Material Mat, SurfaceTool Tool)>();
        var merged = new List<MeshInstance3D>();
        void Collect(Node n, Transform3D at)
        {
            foreach (var c in n.GetChildren())
            {
                if (c is not Node3D n3 || !n3.Visible) continue;
                string name = n3.Name;
                // A named node is the runtime's (or a swapped piece): left whole, with all below it.
                if (keep.Contains(name) || name.StartsWith("kk-") || Named(name)) continue;
                var here = at * n3.Transform;
                if (c is MeshInstance3D mi && Plain(mi))
                {
                    var box = here * mi.GetAabb();
                    var mid = box.GetCenter();
                    int gx = Mathf.FloorToInt(mid.X / 32), gz = Mathf.FloorToInt(mid.Z / 32);
                    bool shadow = mi.CastShadow != GeometryInstance3D.ShadowCastingSetting.Off;
                    for (int s = 0; s < mi.Mesh.GetSurfaceCount(); s++)
                    {
                        var mat = mi.GetSurfaceOverrideMaterial(s) ?? mi.Mesh.SurfaceGetMaterial(s);
                        ulong format = (ulong)((ArrayMesh)mi.Mesh).SurfaceGetFormat(s) & 0xFFFF;
                        var key = (mat.GetInstanceId(), format, gx, gz, shadow);
                        if (!groups.TryGetValue(key, out var g))
                        {
                            var st = new SurfaceTool();
                            groups[key] = g = (mat, st);
                        }
                        g.Tool.AppendFrom(mi.Mesh, s, here);
                    }
                    merged.Add(mi);
                }
                if (c.GetChildCount() > 0) Collect(c, here);
            }
        }
        Collect(Root, Transform3D.Identity);
        if (merged.Count == 0) return;
        foreach (var mi in merged) mi.Visible = false;
        var into = new Node3D { Name = "Merged" };
        foreach (var ((_, _, _, _, shadow), (mat, tool)) in groups)
        {
            var mesh = tool.Commit();
            mesh.SurfaceSetMaterial(0, mat);
            into.AddChild(new MeshInstance3D { Mesh = mesh, CastShadow = shadow ? GeometryInstance3D.ShadowCastingSetting.On : GeometryInstance3D.ShadowCastingSetting.Off });
        }
        Root.AddChild(into);
        Perf.Lap($"landmarks merged: {merged.Count} meshes into {groups.Count}");
    }

    /// <summary>Whether a node's name was given it (the runtime's names have letters
    /// and a dash; Godot names the unnamed after their type or mesh, with no dash).</summary>
    static bool Named(string name) => name.Contains('-');

    /// <summary>A mesh that can be drawn as part of another: unskinned, no blend shapes,
    /// nothing hanging from it, triangles, every surface opaque.</summary>
    static bool Plain(MeshInstance3D mi)
    {
        if (mi.Mesh is not ArrayMesh am || mi.Skin != null || !mi.Skeleton.IsEmpty || am.GetBlendShapeCount() > 0 || mi.GetChildCount() > 0
            || mi.MaterialOverride != null || mi.MaterialOverlay != null || mi.VisibilityRangeEnd > 0 || mi.Layers != 1) return false;
        for (int s = 0; s < am.GetSurfaceCount(); s++)
        {
            if (am.SurfaceGetPrimitiveType(s) != Mesh.PrimitiveType.Triangles) return false;
            if (!Mergeable(mi.GetSurfaceOverrideMaterial(s) ?? am.SurfaceGetMaterial(s))) return false;
        }
        return true;
    }

    /// <summary>A material that draws a piece the same whatever mesh it is part of:
    /// opaque, and reading nothing of its own model's space. (The kits' shader
    /// does: each piece's sway and jitter from its origin, its foot from its own
    /// height; those stay apart.)</summary>
    static bool Mergeable(Material? mat)
    {
        if (mat == null || mat.NextPass != null) return false;
        if (mat is BaseMaterial3D b)
            return b.Transparency == BaseMaterial3D.TransparencyEnum.Disabled && b.BillboardMode == BaseMaterial3D.BillboardModeEnum.Disabled
                && !b.Grow && !(b.Uv1Triplanar && !b.Uv1WorldTriplanar);
        if (mat is ShaderMaterial { Shader: { } sh })
        {
            var code = sh.Code;
            return !code.Contains("blend_") && !code.Contains("ALPHA") && !code.Contains("MODEL_MATRIX") && !code.Contains("NODE_POSITION")
                && !code.Contains("INSTANCE") && !code.Contains("VERTEX.") && !code.Contains("VERTEX =") && !code.Contains("VERTEX +=") && !code.Contains("v_y");
        }
        return false;
    }

    /// <summary>Every string in the zone's refs (node names among them).</summary>
    static void Strings(JsonElement e, HashSet<string> into)
    {
        switch (e.ValueKind)
        {
            case JsonValueKind.String: into.Add(e.GetString()!); break;
            case JsonValueKind.Array: foreach (var x in e.EnumerateArray()) Strings(x, into); break;
            case JsonValueKind.Object: foreach (var p in e.EnumerateObject()) Strings(p.Value, into); break;
        }
    }

    bool Swap(Node3D kk)
    {
        var part = kk.Name.ToString().Split('-');
        // The ground under a point of the piece, in its frame (the landmarks stand at the world's origin).
        var at = kk.Transform;
        var back = at.AffineInverse();
        float Ground(Vector3 p) { var w = at * p; return (back * new Vector3(w.X, zone.HeightAt(w.X, w.Z), w.Z)).Y; }
        if (part.Length < 4 || Pieces.For(part[1], part[2], int.TryParse(part[3], out var i) ? i : 0, at.Basis.Scale.Y, Ground) is not Node3D piece) return false;
        foreach (var c in kk.GetChildren()) { kk.RemoveChild(c); c.QueueFree(); }
        kk.AddChild(piece);
        return true;
    }

    static readonly Dictionary<ulong, Material?> remade = new();

    /// <summary>A material as its name says to make it, or null to keep it.</summary>
    static Material? Remade(Material mat)
    {
        if (remade.TryGetValue(mat.GetInstanceId(), out var hit)) return hit;
        var tags = new Dictionary<string, string>();
        foreach (var part in mat.ResourceName.Split('|'))
        {
            int eq = part.IndexOf('=');
            if (eq > 0) tags[part[..eq]] = part[(eq + 1)..];
            else if (part == "add") tags["add"] = "";
        }
        Material? to = null;
        if (tags.TryGetValue("kit", out var kit) && KitMaterials.Get(kit) is Material k)
            to = KitLook.For(k, KitLook.Look.Plain, foot: KitMaterials.Footed(kit));
        else if (tags.ContainsKey("hdr") || tags.ContainsKey("add"))
        {
            var src = mat as BaseMaterial3D;
            var color = src != null ? src.AlbedoColor.SrgbToLinear() : Colors.White;
            if (tags.TryGetValue("hdr", out var hdr))
            {
                var v = hdr.Split(',');
                color = new Color(float.Parse(v[0], CultureInfo.InvariantCulture), float.Parse(v[1], CultureInfo.InvariantCulture), float.Parse(v[2], CultureInfo.InvariantCulture));
            }
            to = Unlit(color, src?.AlbedoTexture, tags.ContainsKey("add"), src?.AlbedoColor.A ?? 1);
        }
        remade[mat.GetInstanceId()] = to;
        return to;
    }

    static Shader? unlit, unlitAdd;

    /// <summary>A colour that takes no light (linear, may be brighter than
    /// white), over a texture; additive, or not.</summary>
    public static ShaderMaterial Unlit(Color linear, Texture2D? tex, bool additive, float opacity = 1)
    {
        unlit ??= GD.Load<Shader>("res://shaders/unlit.gdshader");
        unlitAdd ??= new Shader { Code = unlit.Code.Replace("render_mode unshaded, cull_back, depth_draw_opaque", "render_mode unshaded, cull_disabled, blend_add, depth_draw_never") };
        var m = new ShaderMaterial { Shader = additive ? unlitAdd : unlit };
        m.SetShaderParameter("color", new Vector3(linear.R, linear.G, linear.B));
        if (tex != null) m.SetShaderParameter("tex", tex);
        m.SetShaderParameter("opacity", opacity);
        return m;
    }
}

/// <summary>The world kits' materials by name, taken from the kit files
/// that have them (data/zones/kit_materials.json, written by the exporter):
/// a sheet is loaded once, whoever uses it.</summary>
public static class KitMaterials
{
    static Dictionary<string, string>? index;
    static readonly Dictionary<string, Material?> cache = new();

    static Dictionary<string, string> Index => index ??=
        JsonSerializer.Deserialize<Dictionary<string, string>>(FileAccess.GetFileAsString("res://data/zones/kit_materials.json")) ?? new();

    /// <summary>Which kit a material is from ('village/Wall_Plaster').</summary>
    public static string? FileOf(string name) => Index.TryGetValue(name, out var f) ? f : null;

    /// <summary>The village kit and the game's own models darken toward the foot.</summary>
    public static bool Footed(string name) => FileOf(name) is string f && (f.StartsWith("village/") || f.StartsWith("custom/"));

    public static Material? Get(string name)
    {
        if (cache.TryGetValue(name, out var hit)) return hit;
        Material? found = null;
        if (FileOf(name) is string file)
        {
            var scene = GD.Load<PackedScene>($"res://assets/env/{file}.gltf").Instantiate<Node3D>();
            found = Find(scene, name);
            scene.Free();
        }
        if (found == null) GD.PushWarning($"kit material {name} not found");
        cache[name] = found;
        return found;
    }

    static Material? Find(Node n, string name)
    {
        foreach (var c in n.GetChildren())
        {
            if (c is MeshInstance3D m && m.Mesh != null)
                for (int i = 0; i < m.Mesh.GetSurfaceCount(); i++)
                    if (m.Mesh.SurfaceGetMaterial(i) is Material mat && mat.ResourceName == name) return mat;
            if (Find(c, name) is Material f) return f;
        }
        return null;
    }
}
