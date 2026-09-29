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
        Root = GD.Load<PackedScene>($"{z.Dir}/landmarks.glb").Instantiate<Node3D>();
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
