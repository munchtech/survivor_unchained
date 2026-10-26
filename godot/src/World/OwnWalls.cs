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
    // (E9b4) corner pieces the kit set in the middle of a straight run (the town walls' joints every 8 m): drawn as
    // piers in their wall's frame, the lower storey's ("pier_lo") or the top one's ("pier_hi"), not as an outer
    // corner's quoins (which stood in the face like a post crossing the coping)
    readonly Dictionary<(int, int, int), (Basis Wall, bool Top)> piers = new();
    static (int, int, int) Key(Vector3 p) => (Mathf.RoundToInt(p.X * 4), Mathf.RoundToInt(p.Y * 4), Mathf.RoundToInt(p.Z * 4));
    ZoneData? zone;
    readonly List<(Vector3 At, float Foot)> feet = new();
    readonly Dictionary<(string Preset, int X, int Z), List<(Transform3D At, Color Data, int House, bool Roof)>> groups = new();
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
        // the mid-run corners: a wall piece each side of it, opposite, on its storey
        var walls = z.Props.Where(p => p.Id.StartsWith("village/Wall_")).Select(p => p.At).ToList();
        var corners = z.Props.Where(p => p.Id.StartsWith("village/Corner_Exterior")).Select(p => p.At.Origin).ToList();
        foreach (var c in corners)
        {
            var near = walls.Where(t => Mathf.Abs(t.Origin.Y - c.Y) < 0.3f && new Vector2(t.Origin.X - c.X, t.Origin.Z - c.Z).Length() is > 0.5f and < 1.3f).ToList();
            var pair = near.FirstOrDefault(a => near.Any(b => (new Vector2(a.Origin.X + b.Origin.X - 2 * c.X, a.Origin.Z + b.Origin.Z - 2 * c.Z)).Length() < 0.3f));
            if (pair.Basis == default) continue;
            bool top = !corners.Any(u => u.Y > c.Y + 2.5f && u.Y < c.Y + 3.5f && new Vector2(u.X - c.X, u.Z - c.Z).Length() < 0.4f);
            o.piers[Key(c)] = (pair.Basis, top);
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
        if (id.StartsWith("village/Corner_Exterior") && piers.TryGetValue(Key(at.Origin), out var pier))
        {
            preset = pier.Top ? "pier_hi" : "pier_lo";
            at = new Transform3D(pier.Wall, at.Origin);
        }
        if (!ResourceLoader.Exists($"{Dir}/{preset}.glb")) return false;
        float gy = ground.TryGetValue(house, out var g0) ? at.Origin.Y - g0 : 0f;
        var data = new Color((tint + 0.5f) / 8f, gy, (hs % 997) / 997f, isRoof ? (style * 8 + roofTint + 0.5f) / 32f : (style + 0.5f) / 4f);
        var k = (preset, Mathf.FloorToInt(at.Origin.X / cell), Mathf.FloorToInt(at.Origin.Z / cell));
        if (!groups.TryGetValue(k, out var l)) groups[k] = l = new();
        l.Add((at, data, house, isRoof));
        if (!isRoof && ground.TryGetValue(house, out var gf)) feet.Add((at.Origin, gf));
        return true;
    }

    /// <summary>(E9c) The houses' fade units (HouseFade, added under root): each house, or each 12 m length of a long one
    /// (a town wall, so only the length in her way fades), as a box in its house's own frame: its footprint from its walls
    /// (not the eaves' overhang, so a house behind her is never taken), its height from all of it. Returns each copy's
    /// unit by its house and place.</summary>
    Dictionary<(int, Vector3), int> FadeUnits(Node3D root)
    {
        var unitOf = new Dictionary<(int, Vector3), int>();
        var byHouse = groups.SelectMany(g => g.Value.Select(e => (Preset: g.Key.Preset, e.At, e.House, e.Roof))).Where(e => e.House >= 0).GroupBy(e => e.House);
        var fade = new HouseFade();
        foreach (var h in byHouse)
        {
            // the house's frame: its walls' direction, folded to a quarter turn
            double sx = 0, sy = 0;
            foreach (var e in h.Where(e => !e.Roof))
            {
                double a = 4 * Mathf.Atan2(e.At.Basis.Column0.Z, e.At.Basis.Column0.X);
                sx += System.Math.Cos(a); sy += System.Math.Sin(a);
            }
            float yaw = (float)System.Math.Atan2(sy, sx) / 4, c = Mathf.Cos(yaw), sn = Mathf.Sin(yaw);
            Vector3 F(Vector3 p) => new(p.X * c + p.Z * sn, p.Y, -p.X * sn + p.Z * c);
            // its long axis, cut in lengths of at most 12 m (by each copy's own place)
            var walls = h.Where(e => !e.Roof).Select(e => F(e.At.Origin)).DefaultIfEmpty(F(h.First().At.Origin)).ToList();
            float u0 = walls.Min(p => p.X), u1 = walls.Max(p => p.X), v0 = walls.Min(p => p.Z), v1 = walls.Max(p => p.Z);
            bool alongU = u1 - u0 >= v1 - v0;
            float lo = alongU ? u0 : v0, len = alongU ? u1 - u0 : v1 - v0;
            int n = Mathf.Max(1, Mathf.RoundToInt(len / 12f));
            var boxes = new (Vector3 Min, Vector3 Max, bool Any)[n];
            for (int i = 0; i < n; i++) boxes[i] = (Vector3.Inf, -Vector3.Inf, false);
            foreach (var e in h)
            {
                var o = F(e.At.Origin);
                int k = Mathf.Clamp((int)(((alongU ? o.X : o.Z) - lo) / Mathf.Max(len, 1e-3f) * n), 0, n - 1);
                unitOf[(h.Key, e.At.Origin)] = fade.Units.Count + k;
                foreach (var (mesh, local) in PartsOf(e.Preset))
                {
                    var bb = mesh.GetAabb();
                    for (int j = 0; j < 8; j++)
                    {
                        var p = F(e.At * local * bb.GetEndpoint(j));
                        ref var b = ref boxes[k];
                        // (the footprint from the walls only; the height from all)
                        if (!e.Roof) { b.Min = new(Mathf.Min(b.Min.X, p.X), b.Min.Y, Mathf.Min(b.Min.Z, p.Z)); b.Max = new(Mathf.Max(b.Max.X, p.X), b.Max.Y, Mathf.Max(b.Max.Z, p.Z)); b.Any = true; }
                        b.Min.Y = Mathf.Min(b.Min.Y, p.Y); b.Max.Y = Mathf.Max(b.Max.Y, p.Y);
                    }
                }
            }
            foreach (var b in boxes) fade.Units.Add((c, sn, b.Any ? b.Min : Vector3.Zero, b.Any ? b.Max : Vector3.Zero));
        }
        fade.Name = "house_fade";
        root.AddChild(fade);
        GD.Print($"house fade: {fade.Units.Count} units");
        return unitOf;
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
            foreach (var (at, _, _, _) in list) tops.Add(at * new Vector3(0, top, 0));
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
        var unitOf = FadeUnits(root);
        foreach (var ((preset, _, _), list) in groups)
            foreach (var (mesh, local) in PartsOf(preset))
            {
                var mm = new MultiMesh { TransformFormat = MultiMesh.TransformFormatEnum.Transform3D, UseCustomData = true, Mesh = mesh, InstanceCount = list.Count };
                for (int i = 0; i < list.Count; i++)
                {
                    mm.SetInstanceTransform(i, list[i].At * local);
                    // (r's whole part: the copy's fade unit + 1, HouseFade; its fraction the tint)
                    var d = list[i].Data;
                    mm.SetInstanceCustomData(i, new Color(d.R + (unitOf.TryGetValue((list[i].House, list[i].At.Origin), out var u) ? u + 1 : 0), d.G, d.B, d.A));
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
