using System.Collections.Generic;
using System.Linq;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// What stands on the ground: the nature kit's trees, rocks and undergrowth
/// (one MultiMesh per part of a piece per 48 m bucket, as the web game
/// buckets them, so what is off screen is culled), the kit props placed one
/// by one, and the zone's lamps and fires.
/// </summary>
public static class Dressing
{
    /// Undergrowth: walked through, no shadow of its own.
    static readonly HashSet<string> Low = new() { "fern", "flowers", "plant", "clover", "mushroom", "pebble", "scan_grass", "scan_stones", "scan_moss", "scan_bark", "scan_fern" };

    static readonly Dictionary<string, List<(Mesh Mesh, Transform3D Local)>> parts = new();

    /// <summary>A piece's file: a photoscan (art/world), one of our own trees (art/world/flora) or a kit piece.</summary>
    static string FileOf(string kit, string piece) =>
        piece.StartsWith("scan:") ? $"res://art/world/{piece[5..]}.glb"
        : piece.StartsWith("own:") ? $"res://art/world/flora/{OwnFile(piece)}.gltf" : $"res://assets/env/{kit}/{piece}.gltf";

    /// <summary>--flora-own (E4, a developer's switch while our own flora replaces the kit's, default off): the kit's
    /// pines, broadleaf trees, dead trees, bushes and ferns drawn as ours (tools/assets/env_trees.py), the same count,
    /// places and sizes. Which kit piece is which of ours is data: godot/data/flora_species.json (a zone may override it).</summary>
    public static readonly bool FloraOwn = SurvivorUnchained.Args.Has("flora-own");
    /// <summary>The piece as this zone draws it: "own:a" (or "own:a|b|c", one per copy by its place) under --flora-own.</summary>
    public static string Own(string piece, string zone = "") =>
        FloraOwn && FloraSpecies.OwnFor(zone, piece) is { } o ? "own:" + string.Join('|', o) : piece;

    /// <summary>Where our own flora changes LOD (a cell's middle from the camera, m; flora_species.json's "lod" per
    /// species, --flora-lod1/--flora-lod2/--flora-cell override every species, for measuring): lod0 inside the first,
    /// lod1 to the second, lod2 beyond. The play camera (23 m back at 56 degrees, 34 degrees high) sees no ground
    /// farther than about 40 m from it, so lod0 is only what is on screen in play. The copies are gathered in
    /// cells for this, so a tree's LOD goes by its own square, not by its bucket's middle. The shadows are cast by
    /// the piece's shadow proxy alone (the file's "shadow" node), in cells twice as wide.</summary>
    static float[] LodsFor(FloraSpecies.Species sp)
    {
        float l1 = sp.Lod.Length > 0 ? sp.Lod[0] : 44, l2 = sp.Lod.Length > 1 ? sp.Lod[1] : 0;
        if (SurvivorUnchained.Args.Has("flora-lod1")) l1 = SurvivorUnchained.Args.Num("flora-lod1", l1);
        if (SurvivorUnchained.Args.Has("flora-lod2")) l2 = SurvivorUnchained.Args.Num("flora-lod2", l2);
        return [l1, l2];
    }
    static float CellFor(FloraSpecies.Species sp) => SurvivorUnchained.Args.Has("flora-cell") ? SurvivorUnchained.Args.Num("flora-cell", 24) : sp.Cell;

    /// <summary>An own file's meshes: lod0, lod1, lod2 (a missing one is the one before it) and its shadow proxy
    /// (null if the file has none).</summary>
    static Mesh?[] LodsOf(string file)
    {
        var scene = GD.Load<PackedScene>($"res://art/world/flora/{file}.gltf").Instantiate<Node3D>();
        var m = new Mesh?[4];
        for (int i = 0; i < 4; i++) m[i] = scene.FindChild(i < 3 ? $"lod{i}" : "shadow", true, false) is MeshInstance3D mi ? mi.Mesh : i < 3 ? m[Mathf.Max(i - 1, 0)] : null;
        scene.Free();
        return m;
    }

    /// <summary>One own piece of a copy: "own:a|b" chooses by the copy's place.</summary>
    static string OwnPick(string[] names, Vector3 o) =>
        names.Length == 1 ? names[0] : names[(int)((uint)(Mathf.FloorToInt(o.X * 3.7f) * 73856093 ^ Mathf.FloorToInt(o.Z * 2.9f) * 19349663) % (uint)names.Length)];

    /// <summary>An own piece's file (without .gltf).</summary>
    static string OwnFile(string piece) { var p0 = piece[4..].Split('|')[0]; return FloraSpecies.Of(p0).FileOf(p0).File; }

    /// <summary>Every file the place's flora and props are made from (Prefetch asks for them ahead).</summary>
    public static IEnumerable<string> Files(ZoneData z)
    {
        foreach (var g in z.Flora) yield return FileOf("nature", g.Piece);
        foreach (var (id, _) in z.Props)
        {
            int slash = id.IndexOf('/');
            if (slash > 0) yield return FileOf(id[..slash], id[(slash + 1)..]);
        }
    }

    /// <summary>The meshes of a kit piece, with where each sits in it.</summary>
    static List<(Mesh Mesh, Transform3D Local)> PartsOf(string kit, string piece)
    {
        var key = $"{kit}/{piece}";
        if (parts.TryGetValue(key, out var list)) return list;
        list = new();
        var scene = GD.Load<PackedScene>(FileOf(kit, piece)).Instantiate<Node3D>();
        void Walk(Node n, Transform3D at)
        {
            foreach (var c in n.GetChildren())
            {
                var t = c is Node3D c3 ? at * c3.Transform : at;
                if (c is MeshInstance3D mi && mi.Mesh != null) list.Add((mi.Mesh, t));
                Walk(c, t);
            }
        }
        Walk(scene, Transform3D.Identity);
        scene.Free();
        parts[key] = list;
        return list;
    }

    /// <summary>A flora piece's bounds as it stands (its meshes where they sit in it; a scan's first
    /// variant): GroundPaint reads its crown from it, for the frost's sky exposure.</summary>
    public static Aabb BoundsOf(string piece)
    {
        if (piece.StartsWith("own:")) return LodsOf(OwnFile(piece))[0]!.GetAabb();
        var list = piece.StartsWith("scan:") ? VariantsOf(piece[5..]) : PartsOf("nature", piece);
        Aabb? b = null;
        foreach (var (mesh, local) in list)
        {
            var a = local * mesh.GetAabb();
            b = b is Aabb o ? o.Merge(a) : a;
            if (piece.StartsWith("scan:")) break;
        }
        return b ?? new Aabb();
    }

    static readonly Dictionary<string, Mesh> looked = new();

    /// <summary>A piece's mesh with its kind's look (KitLook): one copy per
    /// mesh and look, its surfaces' materials swapped.</summary>
    static Mesh Looked(Mesh mesh, KitLook.Look look, bool foot = false)
    {
        var key = $"{mesh.GetInstanceId()}|{look}|{foot}";
        if (looked.TryGetValue(key, out var m)) return m;
        m = (Mesh)mesh.Duplicate();
        for (int i = 0; i < m.GetSurfaceCount(); i++)
            if (m.SurfaceGetMaterial(i) is Material mat) m.SurfaceSetMaterial(i, KitLook.For(mat, look, foot));
        looked[key] = m;
        return m;
    }

    /// <summary>How big each scan is drawn, against its true size: the arena
    /// is seen from thirty metres up, where a real pebble is nothing, so small
    /// things are drawn large (as the genre does) and large ones near true.</summary>
    static readonly Dictionary<string, float> ScanScale = new()
    {
        ["grass_medium_01"] = 3.2f, ["grass_medium_02"] = 2.4f, ["weed_plant_02"] = 2.6f,
        ["stone_01"] = 6f, ["namaqualand_stones_01"] = 5f, ["moss_01"] = 5f, ["bark_debris_01"] = 1.4f,
        ["fern_02"] = 1.4f, ["nettle_plant"] = 3f, ["shrub_03"] = 2.6f, ["shrub_01"] = 1.2f, ["shrub_02"] = 1f, ["shrub_04"] = 2.4f,
        ["root_cluster_01"] = 1f, ["root_cluster_02"] = 1.2f, ["single_root"] = 1.3f, ["pine_roots"] = 1.3f,
        ["tree_stump_01"] = 1.2f, ["tree_stump_02"] = 1.2f, ["dry_branches_medium_01"] = 1.4f,
        ["rock_07"] = 6f, ["rock_09"] = 12f, ["rock_moss_set_01"] = 1.5f, ["rock_moss_set_02"] = 1.5f,
        ["dead_tree_trunk"] = 1.1f, ["dead_tree_trunk_02"] = 1f, ["boulder_01"] = 1.5f,
    };

    /// <summary>Scans whose photographed colour is too pale for this country
    /// (bright sandstone, sunlit gravel): their albedo multiplied down.</summary>
    static readonly Dictionary<string, Color> ScanTint = new()
    {
        ["stone_01"] = new(0.5f, 0.47f, 0.42f), ["namaqualand_stones_01"] = new(0.45f, 0.42f, 0.38f),
        ["rock_07"] = new(0.6f, 0.58f, 0.55f), ["rock_09"] = new(0.6f, 0.58f, 0.55f), ["bark_debris_01"] = new(0.7f, 0.65f, 0.6f),
        // (Roots photographed washed and dry, near white: from above a cluster read as a pale
        // cut-out of card lying on the litter.)
        ["root_cluster_01"] = new(0.5f, 0.45f, 0.4f), ["root_cluster_02"] = new(0.5f, 0.45f, 0.4f),
        ["single_root"] = new(0.55f, 0.5f, 0.45f), ["pine_roots"] = new(0.55f, 0.5f, 0.45f),
    };

    static readonly Dictionary<string, List<(Mesh Mesh, Transform3D Local)>> variants = new();

    /// <summary>A scan's variants: Poly Haven lays several takes of a thing
    /// out in a row in one file (tufts, stones, the rocks of a set); each is
    /// one variant here, set on its own middle, at its drawn size.</summary>
    static List<(Mesh Mesh, Transform3D Local)> VariantsOf(string id)
    {
        if (variants.TryGetValue(id, out var list)) return list;
        list = new();
        float k = ScanScale.TryGetValue(id, out var sc) ? sc : 1;
        foreach (var (src, local) in PartsOf("nature", "scan:" + id))
        {
            var mesh = src;
            if (ScanTint.TryGetValue(id, out var tint))
            {
                mesh = (Mesh)src.Duplicate();
                for (int i = 0; i < mesh.GetSurfaceCount(); i++)
                    if (mesh.SurfaceGetMaterial(i) is StandardMaterial3D m)
                    {
                        var d = (StandardMaterial3D)m.Duplicate();
                        d.AlbedoColor = tint;
                        mesh.SurfaceSetMaterial(i, d);
                    }
            }
            var box = local * mesh.GetAabb();
            var mid = box.GetCenter();
            // Its foot on the ground and its middle on the spot.
            var at = new Transform3D(local.Basis, local.Origin - new Vector3(mid.X, box.Position.Y, mid.Z));
            list.Add((mesh, new Transform3D(Basis.FromScale(Vector3.One * k), Vector3.Zero) * at));
        }
        variants[id] = list;
        return list;
    }

    public static Node3D Flora(ZoneData z)
    {
        var root = new Node3D { Name = "Flora" };
        // Our own flora gathered across the zone's groups (the kit's Pine_1 and Pine_3 are both spruce_a, its
        // broadleaf and autumn CommonTrees both alders, in many groups): one set of cells per file and look, not per
        // group (E4c: the trees' draws). A packed species' pieces share one file (each copy told which it is, its
        // MultiMesh's custom data). Ours keep their own greens (no recolour) and their species' wind.
        var flora = new List<ZoneData.FloraGroup>();
        var merged = new Dictionary<(string File, KitLook.Look Look), (FloraSpecies.Species Sp, List<Transform3D> At, List<int> Var)>();
        foreach (var g in z.Flora)
        {
            if (!g.Piece.StartsWith("own:")) { flora.Add(g); continue; }
            var names = g.Piece[4..].Split('|');
            foreach (var t in g.At)
            {
                var name = OwnPick(names, t.Origin);
                var sp = FloraSpecies.Of(name);
                var (file, v) = sp.FileOf(name);
                var look = g.Look with { LeafA = null, LeafB = null, LeafAmount = 0, Wind = sp.Wind ?? g.Look.Wind };
                if (!merged.TryGetValue((file, look), out var mg)) merged[(file, look)] = mg = (sp, new(), new());
                mg.At.Add(t); mg.Var.Add(v);
            }
        }
        foreach (var ((file, look), (sp, at, vars)) in merged) OwnFlora(root, sp, file, look, at, vars);
        foreach (var g in flora)
        {
            var low = Low.Contains(g.Kind);
            if (g.Piece.StartsWith("scan:"))
            {
                // Each instance takes one of the scan's variants; each keeps
                // its own photographed materials.
                var vs = VariantsOf(g.Piece[5..]);
                var by = new List<Transform3D>[vs.Count];
                for (int i = 0; i < vs.Count; i++) by[i] = new();
                for (int i = 0; i < g.At.Length; i++)
                {
                    var o = g.At[i].Origin;
                    int v = (int)((uint)(Mathf.FloorToInt(o.X * 7.3f) * 73856093 ^ Mathf.FloorToInt(o.Z * 5.1f) * 19349663) % (uint)vs.Count);
                    by[v].Add(g.At[i]);
                }
                for (int v = 0; v < vs.Count; v++)
                {
                    if (by[v].Count == 0) continue;
                    var mm = new MultiMesh { TransformFormat = MultiMesh.TransformFormatEnum.Transform3D, Mesh = vs[v].Mesh, InstanceCount = by[v].Count };
                    for (int i = 0; i < by[v].Count; i++) mm.SetInstanceTransform(i, by[v][i] * vs[v].Local);
                    root.AddChild(new MultiMeshInstance3D
                    {
                        Multimesh = mm, Name = $"{g.Kind}:{g.Piece}:{v}",
                        CastShadow = low ? GeometryInstance3D.ShadowCastingSetting.Off : GeometryInstance3D.ShadowCastingSetting.On,
                        VisibilityRangeEnd = low ? 90 : 0,
                    });
                }
                continue;
            }
            foreach (var (mesh, local) in PartsOf("nature", g.Piece))
            {
                var mm = new MultiMesh { TransformFormat = MultiMesh.TransformFormatEnum.Transform3D, Mesh = Looked(mesh, g.Look), InstanceCount = g.At.Length };
                for (int i = 0; i < g.At.Length; i++) mm.SetInstanceTransform(i, g.At[i] * local);
                root.AddChild(Kind(new MultiMeshInstance3D
                {
                    Multimesh = mm,
                    Name = $"{g.Kind}:{g.Piece}",
                    CastShadow = low ? GeometryInstance3D.ShadowCastingSetting.Off : GeometryInstance3D.ShadowCastingSetting.On,
                    // Undergrowth goes before it gets small on screen.
                    VisibilityRangeEnd = low ? 70 : 0,
                }, g.Kind));
            }
        }
        return root;
    }

    /// <summary>Our own flora of one file and look: its copies in cells (the species' cell), each cell a MultiMesh
    /// per LOD shown by distance, and its shadow proxy (if it casts) in cells twice as wide. A packed file's copies
    /// carry which of its pieces each is (custom data r: (index + 0.5) / 8, matched against the vertex's COLOR.a).</summary>
    static void OwnFlora(Node3D root, FloraSpecies.Species sp, string file, KitLook.Look look, List<Transform3D> all, List<int> vars)
    {
        var lods = LodsOf(file);
        var lr = LodsFor(sp);
        float cell = CellFor(sp);
        MultiMeshInstance3D Mmi(Mesh mesh, string tag, List<int> idx, List<Transform3D> at)
        {
            var mm = new MultiMesh { TransformFormat = MultiMesh.TransformFormatEnum.Transform3D, UseCustomData = sp.Packed, Mesh = Looked(mesh, look), InstanceCount = idx.Count };
            for (int i = 0; i < idx.Count; i++)
            {
                mm.SetInstanceTransform(i, at[idx[i]]);
                if (sp.Packed) mm.SetInstanceCustomData(i, new Color((vars[idx[i]] + 0.5f) / 8f, 0, 0, 0));
            }
            return Kind(new MultiMeshInstance3D { Multimesh = mm, Name = $"{sp.Kind}:{file}:{tag}", CastShadow = GeometryInstance3D.ShadowCastingSetting.Off }, sp.Kind);
        }
        static Dictionary<(int, int), List<int>> Cells(List<Transform3D> at, float side)
        {
            var cells = new Dictionary<(int, int), List<int>>();
            for (int i = 0; i < at.Count; i++)
            {
                var k = (Mathf.FloorToInt(at[i].Origin.X / side), Mathf.FloorToInt(at[i].Origin.Z / side));
                if (!cells.TryGetValue(k, out var l)) cells[k] = l = new();
                l.Add(i);
            }
            return cells;
        }
        foreach (var ((cx, cz), idx) in Cells(all, cell))
        {
            // lod0 to lr[0]; lod1 to lr[1] (if any), then lod2; the last to the species' end (0: always)
            var l0 = Mmi(lods[0]!, $"lod0_{cx}_{cz}", idx, all); l0.VisibilityRangeEnd = lr[0]; l0.VisibilityRangeEndMargin = 2;
            var l1 = Mmi(lods[1]!, $"lod1_{cx}_{cz}", idx, all); l1.VisibilityRangeBegin = lr[0]; l1.VisibilityRangeBeginMargin = 2;
            root.AddChild(l0); root.AddChild(l1);
            if (lr[1] > lr[0])
            {
                l1.VisibilityRangeEnd = lr[1]; l1.VisibilityRangeEndMargin = 4;
                var l2 = Mmi(lods[2]!, $"lod2_{cx}_{cz}", idx, all); l2.VisibilityRangeBegin = lr[1]; l2.VisibilityRangeBeginMargin = 4;
                if (sp.End > 0) l2.VisibilityRangeEnd = sp.End;
                root.AddChild(l2);
            }
            else if (sp.End > 0) l1.VisibilityRangeEnd = sp.End;
        }
        if (!sp.Shadow || lods[3] is not Mesh proxy) return;
        // (cast as the kit's pines are: by the key and by a lamp in reach, every one of them)
        // Each copy's shadow its own (judge E4b: the camp's night shadows stood as identical blades): the proxy
        // turned about the trunk and stretched by its own hash, width within 15%; its height within 30% (judge
        // E4c: under the low moon the tips stood in a line, a fence of spikes).
        var shAt = new List<Transform3D>(all.Count);
        foreach (var t in all)
        {
            float h1 = Mathf.PosMod(Mathf.Sin(t.Origin.X * 12.9898f + t.Origin.Z * 78.233f) * 43758.5453f, 1f);
            float h2 = Mathf.PosMod(h1 * 91.7f + 0.31f, 1f), h3 = Mathf.PosMod(h1 * 57.3f + 0.67f, 1f);
            var jit = new Basis(Vector3.Up, h1 * Mathf.Tau).Scaled(new Vector3(0.85f + 0.3f * h2, 0.7f + 0.6f * h3, 0.85f + 0.3f * h2));
            shAt.Add(t * new Transform3D(jit, Vector3.Zero));
        }
        foreach (var ((cx, cz), idx) in Cells(shAt, 2 * cell))
        {
            var sh = Mmi(proxy, $"shadow_{cx}_{cz}", idx, shAt); sh.CastShadow = GeometryInstance3D.ShadowCastingSetting.ShadowsOnly;
            root.AddChild(sh);
        }
    }

    /// <summary>A flora node in its kind's group ("flora_pine"; perf's pines flip finds them so: Godot
    /// renames a second node of one name, so the names can't be matched).</summary>
    static T Kind<T>(T n, string kind) where T : Node { n.AddToGroup($"flora_{kind}"); return n; }

    /// <summary>The side of the squares the kit pieces are gathered in
    /// (--prop-cell to measure others). Measured in the Waystation by day:
    /// 24 m drew 13% fewer shadow draws than 32 m (each square is drawn into
    /// every lamp's and cascade's view it touches, so smaller squares are
    /// culled more tightly), and 16 m was no better for having more squares.</summary>
    static float PropCell => Args.Num("prop-cell", 24);

    /// <summary>The world kits' pieces, placed one by one in the web game
    /// (the houses and walls too, which it merges): here each piece's parts
    /// as MultiMeshes, one per square (PropCell) so what is out of view is culled.</summary>
    public static Node3D Props(ZoneData z)
    {
        var root = new Node3D { Name = "Props" };
        var groups = new Dictionary<(string, int, int), List<Transform3D>>();
        float cell = PropCell;
        foreach (var (id, at) in z.Props)
        {
            var k = (id, Mathf.FloorToInt(at.Origin.X / cell), Mathf.FloorToInt(at.Origin.Z / cell));
            if (!groups.TryGetValue(k, out var list)) groups[k] = list = new();
            list.Add(at);
        }
        // (Each piece's file loaded first, so the time it takes shows apart from placing them.)
        foreach (var ((id, _, _), _) in groups) { int sl = id.IndexOf('/'); PartsOf(id[..sl], id[(sl + 1)..]); }
        Perf.Lap("props: their files loaded");
        foreach (var ((id, _, _), list) in groups)
        {
            int slash = id.IndexOf('/');
            string kit = id[..slash], piece = id[(slash + 1)..];
            bool foot = kit is "village" or "custom";
            foreach (var (mesh, local) in PartsOf(kit, piece))
            {
                var mm = new MultiMesh { TransformFormat = MultiMesh.TransformFormatEnum.Transform3D, Mesh = Looked(mesh, KitLook.Look.Plain, foot), InstanceCount = list.Count };
                for (int i = 0; i < list.Count; i++) mm.SetInstanceTransform(i, list[i] * local);
                var mmi = new MultiMeshInstance3D { Multimesh = mm, Name = piece };
                // Which piece, and where each one stands, for taking one away in play (HideProps).
                mmi.SetMeta("prop", id);
                mmi.SetMeta("at", new Godot.Collections.Array<Vector3>(list.Select(t => t.Origin)));
                root.AddChild(mmi);
            }
        }
        return root;
    }

    /// <summary>One kit piece as a node of its own (set down in play), or
    /// null if its kit is not in the Godot game.</summary>
    public static Node3D? Piece(string id)
    {
        int slash = id.IndexOf('/');
        if (slash < 0) return null;
        string kit = id[..slash], piece = id[(slash + 1)..];
        if (!ResourceLoader.Exists($"res://assets/env/{kit}/{piece}.gltf")) return null;
        var root = new Node3D { Name = piece };
        bool foot = kit is "village" or "custom";
        foreach (var (mesh, local) in PartsOf(kit, piece)) root.AddChild(new MeshInstance3D { Mesh = Looked(mesh, KitLook.Look.Plain, foot), Transform = local });
        return root;
    }
}
