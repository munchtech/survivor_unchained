using System.Collections.Generic;
using System.Text.Json;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>B3's bake-off hook (L1 texture authoring; tools/look/bakeoff.py): --b3-maps MANIFEST.json puts a painter
/// arm's maps on named stage items, through the material library's loader (CelLib: each material keeps its
/// "&lt;asset&gt;_&lt;class&gt;" name, so the assign rules give the class and its preset). Off unless the flag is given.
/// <para>--b3-painted installs res://art/world/painted/maps.json (tools/look/build.py's output, data/look/painted.json) the same
/// way; paths starting res:// are globalized. Off unless given (the art is not judged yet).</para>
/// <para>Manifest: {"items": [{"node": "own_barrel", "mesh": "ABS/mesh.glb", "maps": {"plank": {"albedo": "ABS.png",
/// "normal": "ABS.png", "rough": "ABS.png"}, ...}}, {"node": "LookSetts", "tile": 4.0, "name": "setts_b3", "maps":
/// {"setts": {...}}}]}. A node with a mesh: its own drawn geometry is hidden and the mesh (the painter's re-unwrapped
/// copy, same place) drawn instead; a node without one (a tile): its material replaced by a world-triplanar one at
/// 1/tile.</para></summary>
public static class B3Maps
{
    record Item(string Node, string? Mesh, float Tile, string? Name, Dictionary<string, Dictionary<string, string>> Maps, float[]? At, float[]? Near);

    static readonly Dictionary<string, Item> items = new();

    public static void Install(SceneTree t)
    {
        var path = SurvivorUnchained.Args.Get("b3-maps") as string;
        if (path == null && SurvivorUnchained.Args.Has("b3-painted")) path = "res://art/world/painted/maps.json";
        if (path == null) return;
        using var doc = JsonDocument.Parse(System.IO.File.ReadAllText(Abs(path)));
        foreach (var e in doc.RootElement.GetProperty("items").EnumerateArray())
        {
            var maps = new Dictionary<string, Dictionary<string, string>>();
            foreach (var c in e.GetProperty("maps").EnumerateObject())
            {
                var m = new Dictionary<string, string>();
                foreach (var k in c.Value.EnumerateObject()) m[k.Name] = k.Value.GetString()!;
                maps[c.Name] = m;
            }
            var it = new Item(e.GetProperty("node").GetString()!, e.TryGetProperty("mesh", out var me) ? me.GetString() : null,
                e.TryGetProperty("tile", out var ti) ? ti.GetSingle() : 4f, e.TryGetProperty("name", out var nm) ? nm.GetString() : null, maps, Floats(e, "at"), Floats(e, "near"));
            items[it.Node] = it;
        }
        GD.Print($"b3-maps: {items.Count} items from {path}");
        t.NodeAdded += n => { if (n is Node3D d && items.TryGetValue(d.Name, out var it)) Swap(d, it); };
    }

    static float[]? Floats(JsonElement e, string k)
    {
        if (!e.TryGetProperty(k, out var a)) return null;
        var r = new List<float>();
        foreach (var v in a.EnumerateArray()) r.Add(v.GetSingle());
        return r.ToArray();
    }

    /// <summary>"near": the item moved in the stage's frame (x right, y away, on the ground) to where the close view
    /// sees it beside her; the frame is read back from the item's own placement ("at": the stage's x, y, yaw for it).</summary>
    static void Move(Node3D d, float[] at, float[] near)
    {
        var b = d.GlobalTransform.Basis * new Basis(Vector3.Up, Mathf.DegToRad(-at[2]));
        Vector3 r = b.X.Normalized(), f = -b.Z.Normalized();
        var p = d.GlobalPosition - r * at[0] - f * at[1];
        var q = p + r * near[0] + f * near[1];
        d.GlobalTransform = new Transform3D(b * new Basis(Vector3.Up, Mathf.DegToRad(near[2])), new Vector3(q.X, d.GlobalPosition.Y, q.Z));
        GD.Print($"b3-maps: {d.Name} moved to stage ({near[0]}, {near[1]})");
    }

    /// <summary>res:// paths (the painted build's manifest) to disk paths; others as given.</summary>
    static string Abs(string p) => p.StartsWith("res://") ? ProjectSettings.GlobalizePath(p) : p;

    static Texture2D Tex(string p)
    {
        var im = Image.LoadFromFile(Abs(p));
        im.GenerateMipmaps();
        return ImageTexture.CreateFromImage(im);
    }

    static StandardMaterial3D Mat(string name, Dictionary<string, string> m) => new()
    {
        ResourceName = name,
        AlbedoTexture = Tex(m["albedo"]),
        NormalEnabled = true, NormalTexture = Tex(m["normal"]), NormalScale = 1f,
        Roughness = 1f, RoughnessTexture = Tex(m["rough"]), RoughnessTextureChannel = BaseMaterial3D.TextureChannel.Red,
        Metallic = 0f,
        TextureFilter = BaseMaterial3D.TextureFilterEnum.LinearWithMipmapsAnisotropic,
    };

    static void Swap(Node3D d, Item it)
    {
        if (it.At is { } at && it.Near is { } near) Callable.From(() => Move(d, at, near)).CallDeferred();
        if (it.Maps.Count == 0) return;
        if (it.Mesh == null)
        {
            if (d is not MeshInstance3D mi) return;
            var (cls, m) = First(it.Maps);
            var mat = Mat(it.Name ?? $"{cls}_b3", m);
            mat.Uv1Triplanar = true; mat.Uv1WorldTriplanar = true; mat.Uv1Scale = Vector3.One / it.Tile;
            mi.MaterialOverride = mat;
            GD.Print($"b3-maps: {d.Name} tile {it.Tile} m, class {cls}");
            return;
        }
        var gd = new GltfDocument(); var st = new GltfState();
        if (gd.AppendFromFile(Abs(it.Mesh), st) != Error.Ok || gd.GenerateScene(st) is not Node3D scene) { GD.PushWarning($"b3-maps: no mesh {it.Mesh}"); return; }
        foreach (var n in d.FindChildren("*", "GeometryInstance3D", true, false))
            if (n is GeometryInstance3D g) g.Visible = false;
        foreach (var n in scene.FindChildren("*", "MeshInstance3D", true, false))
        {
            if (n is not MeshInstance3D mi || mi.Mesh == null) continue;
            for (int s = 0; s < mi.Mesh.GetSurfaceCount(); s++)
            {
                var name = mi.Mesh.SurfaceGetMaterial(s)?.ResourceName ?? "";
                var cls = name.Contains('_') ? name[(name.LastIndexOf('_') + 1)..] : name;
                if (it.Maps.TryGetValue(cls, out var m)) mi.SetSurfaceOverrideMaterial(s, Mat(name, m));
            }
            mi.CastShadow = GeometryInstance3D.ShadowCastingSetting.On;
        }
        scene.Name = "b3_" + d.Name;
        d.CallDeferred(Node.MethodName.AddChild, scene);
        GD.Print($"b3-maps: {d.Name} drawn with {it.Mesh}");
    }

    static (string, Dictionary<string, string>) First(Dictionary<string, Dictionary<string, string>> m)
    {
        foreach (var kv in m) return (kv.Key, kv.Value);
        return ("stone", new());
    }
}
