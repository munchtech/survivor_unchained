using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Godot;
using SurvivorUnchained.World;

namespace SurvivorUnchained.View;

/// <summary>
/// Our own town walls (E9b1; tools/assets/env_house.py, art/world/house): each KayKit village wall, corner,
/// window, door and shutter piece of a zone's props.json drawn as one of our presets, built in the kit
/// piece's own frame and box (so it tiles on the 2 m grid and the 3 m storey), all on one trim sheet
/// (house_albedo.jpg, house_normal.png, house_aux.png) and one material (kit.gdshader's OWN_WALL, KitLook.Wall).
///
/// The zone's props_own.json "walls": "pieces" maps a kit piece to its presets as treatments (a list of lists:
/// a house takes the list of its treatment, each copy one preset of it by its place, so a run of wall doesn't
/// repeat); an empty list drops the kit piece (its glass, frame or door is in our piece). "houses" gives each
/// house (props.json's "h", tools/godot/house_ids.py) its plaster tint and its timber treatment, so neighbors differ.
/// Each copy's custom data: r its tint ((i + 0.5) / 8), g its height above its house's ground (the grime rises
/// from the ground, not from each storey's foot), b its own hash (value), a its treatment.
/// One MultiMesh per preset per square of the props' cells, as the kit pieces are drawn.
///
/// Roofs (E9b2; tools/assets/env_roof.py, KitLook.Roof): the roof bodies, spires and chimneys "by_roof" lists take the list
/// of their house's roof covering (its third number: 0 clay pantiles, 1 oak shingles) and carry its roof tint (the fourth)
/// in their custom data's a ((treatment * 8 + roof tint + 0.5) / 32); the gable fronts take their house's treatment's list
/// like the walls. Each chimney's top goes to KitLook.SetChimneys (the soot round it on the roofs).
/// --walls-kit: the kit's walls as they were (before/after measures).
/// </summary>
public sealed class OwnWalls
{
    public const string Dir = "res://art/world/house";

    readonly Dictionary<string, string[][]> pieces = new();
    readonly Dictionary<int, (int Tint, int Style, int Roof, int RoofTint)> houses = new();
    readonly HashSet<string> byRoof = new();
    readonly Dictionary<int, float> ground = new();
    ZoneData? zone;
    readonly List<(Vector3 At, float Foot)> feet = new();
    readonly Dictionary<(string Preset, int X, int Z), List<(Transform3D At, Color Data)>> groups = new();
    static readonly Dictionary<string, List<(Mesh Mesh, Transform3D Local)>> parts = new();

    /// <summary>The zone's own walls, or null if it has none (or --walls-kit, --props-own-off).</summary>
    public static OwnWalls? For(ZoneData z)
    {
        if (SurvivorUnchained.Args.Has("walls-kit") || SurvivorUnchained.Args.Has("props-own-off")) return null;
        var path = $"res://data/zones/{z.Id}/props_own.json";
        if (!FileAccess.FileExists(path)) return null;
        using var doc = JsonDocument.Parse(FileAccess.GetFileAsString(path));
        if (!doc.RootElement.TryGetProperty("walls", out var w) || !w.TryGetProperty("pieces", out var ps)) return null;
        var o = new OwnWalls { zone = z };
        foreach (var p in ps.EnumerateObject())
            o.pieces[p.Name] = p.Value.EnumerateArray().Select(g => g.EnumerateArray().Select(s => s.GetString()!).ToArray()).ToArray();
        if (w.TryGetProperty("houses", out var hs))
            foreach (var h in hs.EnumerateObject())
                o.houses[int.Parse(h.Name)] = (h.Value[0].GetInt32(), h.Value[1].GetInt32(),
                    h.Value.GetArrayLength() > 2 ? h.Value[2].GetInt32() : 0, h.Value.GetArrayLength() > 3 ? h.Value[3].GetInt32() : 0);
        if (w.TryGetProperty("by_roof", out var br))
            foreach (var id in br.EnumerateArray()) o.byRoof.Add(id.GetString()!);
        // each house's ground: its lowest wall piece's foot
        for (int i = 0; i < z.Props.Count && i < z.PropHouse.Count; i++)
        {
            int h = z.PropHouse[i];
            if (h < 0 || !o.houses.ContainsKey(h) || !o.pieces.ContainsKey(z.Props[i].Id)) continue;
            float y = z.Props[i].At.Origin.Y;
            o.ground[h] = o.ground.TryGetValue(h, out var g) ? Mathf.Min(g, y) : y;
        }
        return o;
    }

    static uint Hash(Vector3 p) => (uint)(Mathf.FloorToInt(p.X * 2.3f + 0.5f) * 73856093) ^ (uint)(Mathf.FloorToInt(p.Z * 2.3f + 0.5f) * 19349663) ^ (uint)(Mathf.FloorToInt(p.Y + 0.5f) * 83492791);

    /// <summary>Takes a kit piece as ours (true: drawn by Build, or dropped), or false to leave it to the kit.</summary>
    public bool Take(string id, int house, Transform3D at, float cell)
    {
        if (!pieces.TryGetValue(id, out var lists)) return false;
        if (lists.Length == 0 || lists[0].Length == 0) return true;
        var (tint, style, roof, roofTint) = houses.TryGetValue(house, out var hl) ? hl : ((int)(Hash(at.Origin) % 6), 0, 0, 0);
        uint hs = Hash(at.Origin);
        bool isRoof = byRoof.Contains(id);
        var list = lists[(isRoof ? roof : style) % lists.Length];
        // (a copy's pick by its place, mixed with its house's, so two houses' runs don't repeat alike)
        var preset = list[(int)((hs ^ (uint)(house * 2654435761u)) % (uint)list.Length)];
        if (!ResourceLoader.Exists($"{Dir}/{preset}.glb")) return false;
        float gy = ground.TryGetValue(house, out var g0) ? at.Origin.Y - g0 : 0f;
        var data = new Color((tint + 0.5f) / 8f, gy, (hs % 997) / 997f, isRoof ? (style * 8 + roofTint + 0.5f) / 32f : (style + 0.5f) / 4f);
        var k = (preset, Mathf.FloorToInt(at.Origin.X / cell), Mathf.FloorToInt(at.Origin.Z / cell));
        if (!groups.TryGetValue(k, out var l)) groups[k] = l = new();
        l.Add((at, data));
        if (!isRoof && ground.TryGetValue(house, out var gf)) feet.Add((at.Origin, gf));
        return true;
    }

    static List<(Mesh Mesh, Transform3D Local)> PartsOf(string preset)
    {
        if (parts.TryGetValue(preset, out var list)) return list;
        list = new();
        var scene = GD.Load<PackedScene>($"{Dir}/{preset}.glb").Instantiate<Node3D>();
        void Walk(Node n, Transform3D at)
        {
            foreach (var c in n.GetChildren())
            {
                var t = c is Node3D c3 ? at * c3.Transform : at;
                if (c is MeshInstance3D mi && mi.Mesh != null)
                {
                    var m = (Mesh)mi.Mesh.Duplicate();
                    for (int i = 0; i < m.GetSurfaceCount(); i++)
                        if (m.SurfaceGetMaterial(i) is Material mat) m.SurfaceSetMaterial(i, KitLook.For(mat, KitLook.Look.Plain));
                    list.Add((m, t));
                }
                Walk(c, t);
            }
        }
        Walk(scene, Transform3D.Identity);
        scene.Free();
        parts[preset] = list;
        return list;
    }

    /// <summary>The taken pieces as MultiMeshes under root (one per preset per square).</summary>
    public void Build(Node3D root)
    {
        int n = 0;
        // the chimneys' tops, for the soot on the roofs round them
        var tops = new List<Vector3>();
        foreach (var ((preset, _, _), list) in groups)
        {
            if (!preset.StartsWith("chim_")) continue;
            float top = PartsOf(preset).Select(p => p.Local * p.Mesh.GetAabb().End).Select(v => v.Y).DefaultIfEmpty(3f).Max();
            foreach (var (at, _) in list) tops.Add(at * new Vector3(0, top, 0));
        }
        KitLook.SetChimneys(tops);
        // the terrain's height under the town (0.5 m cells), so the walls' grime rises from the ground itself (E9b3)
        if (zone != null && groups.Count > 0)
        {
            var at = groups.Values.SelectMany(l => l).Select(t => t.At.Origin).ToList();
            float x0 = at.Min(p => p.X) - 10f, z0 = at.Min(p => p.Z) - 10f, x1 = at.Max(p => p.X) + 10f, z1 = at.Max(p => p.Z) + 10f;
            const float c = 0.5f;
            int w = Mathf.Min(1024, Mathf.CeilToInt((x1 - x0) / c) + 1), h = Mathf.Min(1024, Mathf.CeilToInt((z1 - z0) / c) + 1);
            var img = Image.CreateEmpty(w, h, false, Image.Format.Rf);
            for (int j = 0; j < h; j++)
                for (int i = 0; i < w; i++)
                    img.SetPixel(i, j, new Color(zone.HeightAt(x0 + (i + 0.5f) * (x1 - x0) / w, z0 + (j + 0.5f) * (z1 - z0) / h), 0, 0));
            // (the terrain is pressed down under the houses: within 1.2 m of a wall piece the ground is at least its house's foot,
            // where the street meets the wall)
            float sx = w / (x1 - x0), sz = h / (z1 - z0);
            foreach (var (p, foot) in feet)
                for (int j = Mathf.Max(0, (int)((p.Z - 1.2f - z0) * sz)); j <= Mathf.Min(h - 1, (int)((p.Z + 1.2f - z0) * sz)); j++)
                    for (int i = Mathf.Max(0, (int)((p.X - 1.2f - x0) * sx)); i <= Mathf.Min(w - 1, (int)((p.X + 1.2f - x0) * sx)); i++)
                        if (img.GetPixel(i, j).R < foot + 0.04f) img.SetPixel(i, j, new Color(foot + 0.04f, 0, 0));
            KitLook.SetGround(ImageTexture.CreateFromImage(img), new Vector4(x0, z0, x1 - x0, z1 - z0));
        }
        foreach (var ((preset, _, _), list) in groups)
            foreach (var (mesh, local) in PartsOf(preset))
            {
                var mm = new MultiMesh { TransformFormat = MultiMesh.TransformFormatEnum.Transform3D, UseCustomData = true, Mesh = mesh, InstanceCount = list.Count };
                for (int i = 0; i < list.Count; i++)
                {
                    mm.SetInstanceTransform(i, list[i].At * local);
                    mm.SetInstanceCustomData(i, list[i].Data);
                }
                var mmi = new MultiMeshInstance3D { Multimesh = mm, Name = "own_" + preset };
                mmi.SetMeta("prop", "house/" + preset);
                mmi.SetMeta("at", new Godot.Collections.Array<Vector3>(list.Select(t => t.At.Origin)));
                root.AddChild(mmi);
                n += list.Count;
            }
        GD.Print($"own walls: {n} pieces in {groups.Count} groups, {tops.Count} chimneys");
    }
}
