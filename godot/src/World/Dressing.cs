using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.World;
using ColliderKind = SurvivorUnchained.Sim.ColliderKind;

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

    /// <summary>Our own flora (E4; the default since E4h, --flora-kit for the kit's, kept to compare): the kit's
    /// pines, broadleaf trees, dead trees, bushes and ferns drawn as ours (tools/assets/env_trees.py), the same count,
    /// places and sizes. Which kit piece is which of ours is data: godot/data/flora_species.json (a zone may override it).</summary>
    public static readonly bool FloraOwn = !SurvivorUnchained.Args.Has("flora-kit");
    /// <summary>The piece as this zone draws it: "own:a" (or "own:a|b|c", one per copy by its place) with our own flora,
    /// null where ours drops it (an empty list: the kit's clover, flowers and mushrooms; our grass has its own flowers).</summary>
    public static string? Own(string piece, string zone = "", string? kind = null) =>
        FloraOwn && FloraSpecies.OwnFor(zone, piece, kind) is { } o ? (o.Length == 0 ? null : "own:" + string.Join('|', o)) : piece;

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
    public static Aabb BoundsOf(string piece) => bounds.GetOrAdd(piece, Bounds);

    /// <summary>(kept: the ground's paint, worked out on a worker thread ahead of its place, reads them there, each
    /// looked up first on the main thread, where the files are loaded: Game.Prepare)</summary>
    static readonly System.Collections.Concurrent.ConcurrentDictionary<string, Aabb> bounds = new();

    static Aabb Bounds(string piece)
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
        // (a zone's causeways, its flora_species.json: the kit's stones there dropped, ours laid in their place)
        var ways = FloraOwn ? FloraSpecies.CausewaysFor(z.Id) : [];
        bool Dropped(string kind, Vector3 o)
        {
            foreach (var w in ways)
            {
                bool any = false;
                foreach (var k in w.GetProperty("drop").EnumerateArray()) any |= k.GetString() == kind;
                if (!any) continue;
                var (a, b) = (new Vector2(w.GetProperty("from")[0].GetSingle(), w.GetProperty("from")[1].GetSingle()), new Vector2(w.GetProperty("to")[0].GetSingle(), w.GetProperty("to")[1].GetSingle()));
                var p = new Vector2(o.X, o.Z);
                float t = Mathf.Clamp((p - a).Dot(b - a) / (b - a).LengthSquared(), -0.1f, 1.1f);
                if (p.DistanceTo(a + (b - a) * t) < w.GetProperty("width").GetSingle() * 0.5f) return true;
            }
            return false;
        }
        var clear = Clearance.Of(z);
        foreach (var g0 in z.Flora)
        {
            // (the clearance first: a stone nudged off a trunk, or dropped; a tree off a boulder's crown dropped)
            var g = clear.Apply(g0);
            if (g.At.Length == 0) continue;
            if (ways.Length > 0 && g.At.Any(t => Dropped(g.Kind, t.Origin)))
            {
                var kept = g.At.Where(t => !Dropped(g.Kind, t.Origin)).ToArray();
                if (kept.Length == 0) continue;
                var gg = g with { At = kept };
                if (!g.Piece.StartsWith("own:")) { flora.Add(gg); continue; }
                Merge(gg);
                continue;
            }
            if (!g.Piece.StartsWith("own:")) { flora.Add(g); continue; }
            Merge(g);
        }
        foreach (var w in ways) Causeway(z, w, merged, clear);
        clear.Report(z);
        Stands(merged);
        void Merge(ZoneData.FloraGroup g)
        {
            var names = g.Piece[4..].Split('|');
            foreach (var t in g.At)
            {
                var name = OwnPick(names, t.Origin);
                var sp = FloraSpecies.Of(name);
                var (file, v) = sp.FileOf(name);
                // (our stones take no look: one material whatever the kind's moss and wind, so they merge across kinds)
                var look = sp.Stone ? KitLook.Look.Plain : g.Look with { LeafA = null, LeafB = null, LeafAmount = 0, Wind = sp.Wind ?? g.Look.Wind };
                if (!merged.TryGetValue((file, look), out var mg)) merged[(file, look)] = mg = (sp, new(), new());
                mg.At.Add(t); mg.Var.Add(v);
            }
        }
        // (--flora-hide A,B: a developer's switch, these species or kinds of ours left out (a frame's diff finds what they are))
        var hide = SurvivorUnchained.Args.Get("flora-hide")?.Split(',') ?? [];
        foreach (var ((file, look), (sp, at, vars)) in merged)
            if (!hide.Contains(sp.Name) && !hide.Contains(sp.Kind)) { OwnFlora(root, sp, file, look, at, vars); CanopyLog.Register(root, sp, at); }
        // (a stone darkened under a crown (sky_dark, the pebbles) reads the ground's exposure, as the ground's litter does)
        int skySet = 0;
        if (z.Place == null && merged.Keys.Any(k => merged[k].Sp.Stone && merged[k].Sp.Shader.ContainsKey("sky_dark")))
        {
            var expo = GroundPaint.Of(z).Exposure;
            var done = new HashSet<ulong>();
            foreach (var n in root.GetChildren().OfType<MultiMeshInstance3D>())
                if (n.Multimesh.Mesh is Mesh m)
                    for (int i = 0; i < m.GetSurfaceCount(); i++)
                        for (var mat = m.SurfaceGetMaterial(i) as ShaderMaterial; mat != null; mat = mat.NextPass as ShaderMaterial)
                            if (mat.GetShaderParameter("sky_dark").VariantType == Godot.Variant.Type.Float && (float)mat.GetShaderParameter("sky_dark") > 0f && done.Add(mat.GetInstanceId()))
                            { mat.SetShaderParameter("expo_tex", expo); mat.SetShaderParameter("zone_size", z.Size); skySet++; }
        }
        if (System.Environment.GetEnvironmentVariable("CLEAR_STATS") != null) GD.Print($"sky_dark: {skySet} stone materials given the ground's exposure");
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

    /// <summary>Dense stands thinned into clumps (flora_species.json "stands"; its _doc): a zone's edge wall, a tree on every
    /// cell of its grid at one size, read on a skyline as one pine copied at equal height and spacing (judge C03). A copy with
    /// at least 'dense' others of its kind within 'r' m is kept by a clump field (smooth value noise 'clump' m across), sized
    /// within 'scale' of 'base' (larger in a clump's heart) and turned anew; the thinner forest inside, where play is, as placed.</summary>
    static void Stands(Dictionary<(string File, KitLook.Look Look), (FloraSpecies.Species Sp, List<Transform3D> At, List<int> Var)> merged)
    {
        if (FloraSpecies.Stands is not { } all) return;
        bool stats = System.Environment.GetEnvironmentVariable("FLORA_STATS") != null;
        static float H(float x, float z, int k) => (uint)((Mathf.FloorToInt(x * 4.1f) * 73856093) ^ (Mathf.FloorToInt(z * 3.3f) * 19349663) ^ (k * 83492791)) % 10007u / 10007f;
        static float L(int i, int j, int k) => (uint)((i * 73856093) ^ (j * 19349663) ^ (k * 83492791)) % 10007u / 10007f;
        foreach (var st in all.EnumerateObject())
        {
            if (st.Name.StartsWith('_')) continue;
            var c = st.Value;
            float r = c.GetProperty("r").GetSingle(), cl = c.GetProperty("clump").GetSingle(), keep = c.GetProperty("keep").GetSingle(), bs = c.GetProperty("base").GetSingle();
            int dense = c.GetProperty("dense").GetInt32();
            float s0 = c.GetProperty("scale")[0].GetSingle(), s1 = c.GetProperty("scale")[1].GetSingle();
            var keys = merged.Keys.Where(k => merged[k].Sp.Kind == st.Name).ToList();
            // every copy of the kind on a grid of r-m cells, to count its neighbours
            var grid = new Dictionary<(int, int), List<Vector3>>();
            foreach (var k in keys) foreach (var t in merged[k].At)
            {
                var key = (Mathf.FloorToInt(t.Origin.X / r), Mathf.FloorToInt(t.Origin.Z / r));
                if (!grid.TryGetValue(key, out var l)) grid[key] = l = new();
                l.Add(t.Origin);
            }
            float Field(float x, float z)
            {
                // smooth value noise, two octaves: the clumps and their ragged edges
                float O(float x, float z, float s, int k)
                {
                    float fx = x / s, fz = z / s; int i = Mathf.FloorToInt(fx), j = Mathf.FloorToInt(fz);
                    float u = fx - i, v = fz - j; u = u * u * (3 - 2 * u); v = v * v * (3 - 2 * v);
                    return Mathf.Lerp(Mathf.Lerp(L(i, j, k), L(i + 1, j, k), u), Mathf.Lerp(L(i, j + 1, k), L(i + 1, j + 1, k), u), v);
                }
                return Mathf.Clamp((O(x, z, cl, 11) * 0.7f + O(x, z, cl * 0.4f, 12) * 0.3f - 0.5f) * 2.6f + 0.5f, 0f, 1f);
            }
            int seen = 0, thick = 0, kept = 0;
            foreach (var k in keys)
            {
                var (sp, at, vars) = merged[k];
                var nat = new List<Transform3D>(); var nvar = new List<int>();
                for (int i = 0; i < at.Count; i++)
                {
                    var o = at[i].Origin; seen++;
                    int n = 0, cx = Mathf.FloorToInt(o.X / r), cz = Mathf.FloorToInt(o.Z / r);
                    for (int a = -1; a <= 1; a++) for (int b = -1; b <= 1; b++)
                        if (grid.TryGetValue((cx + a, cz + b), out var l)) foreach (var p in l) if (p != o && p.DistanceSquaredTo(o) < r * r) n++;
                    if (n < dense) { nat.Add(at[i]); nvar.Add(vars[i]); continue; }
                    thick++;
                    float f = Field(o.X, o.Z);
                    // (the share kept follows the field: 'keep' on average, all of a clump's heart, few in the gaps)
                    if (H(o.X, o.Z, 1) > Mathf.Clamp(keep + (f - 0.5f) * 1.6f, 0.05f, 1f)) continue;
                    kept++;
                    float sc = bs * Mathf.Lerp(s0, s1, Mathf.Clamp(0.55f * f + 0.45f * H(o.X, o.Z, 2), 0f, 1f));
                    var basis = new Basis(Vector3.Up, H(o.X, o.Z, 3) * Mathf.Tau).Scaled(Vector3.One * sc);
                    nat.Add(new Transform3D(basis, o)); nvar.Add(vars[i]);
                }
                merged[k] = (sp, nat, nvar);
            }
            if (stats) GD.Print($"stands {st.Name}: {seen} copies, {thick} in dense stands, {kept} kept ({(thick > 0 ? 100f * kept / thick : 0):0}%)");
        }
    }

    /// <summary>A causeway's stepping stones (a zone's flora_species.json "causeways"; flora_species.json's _doc there): each
    /// row's stones at uneven steps, nudged across, turned, tilted and sized by their own hashes, no two neighbours alike, each
    /// set so its top stands 'above' over the water (or a little over the ground, where that is higher), its body sunk in the bed.</summary>
    static void Causeway(ZoneData z, System.Text.Json.JsonElement w, Dictionary<(string File, KitLook.Look Look), (FloraSpecies.Species Sp, List<Transform3D> At, List<int> Var)> merged, Clearance clearOf)
    {
        static Vector2 V2(System.Text.Json.JsonElement e) => new(e[0].GetSingle(), e[1].GetSingle());
        float F(string k, float d) => w.TryGetProperty(k, out var v) ? v.GetSingle() : d;
        var sp = FloraSpecies.Named(w.GetProperty("species").GetString()!);
        Vector2 a = V2(w.GetProperty("from")), b = V2(w.GetProperty("to"));
        Vector2 dir = (b - a).Normalized(), side = new(-dir.Y, dir.X);
        float len = (b - a).Length(), step = F("step", 2.2f), jitter = F("jitter", 0.35f), skip = F("skip", 0.1f), top = F("top", 0.75f), seed = F("seed", 1);
        Vector2 above = w.TryGetProperty("above", out var ab) ? V2(ab) : new(0.05f, 0.14f), scale = w.TryGetProperty("scale", out var sc) ? V2(sc) : new(0.85f, 1.2f);
        float water = z.Meta.Places.TryGetValue("WATER_Y", out var wy) ? wy.GetSingle() : -1000f;
        var key = (sp.Name, KitLook.Look.Plain);
        if (!merged.TryGetValue(key, out var mg)) merged[key] = mg = (sp, new(), new());
        // (E5b: each row drifts across by up to 'drift' m, slowly ('drift_len' m a wave), so the rows weave as one braided
        // path; 'row_skip' a share left out per row (a sparse middle row: the stones between); 'dry': none where the bed is
        // higher than the water + dry m (the cobbled ramp's dry end))
        float drift = F("drift", 0f), driftLen = F("drift_len", 7f), dry = F("dry", 1000f);
        var rowSkip = w.TryGetProperty("row_skip", out var rs) ? rs.EnumerateArray().Select(e => e.GetSingle()).ToArray() : null;
        // ('step_var' how far each step strays from 'step' (0.35: 0.65-1.35 of it); 'clear' m the least gap kept between any two
        // stones' rims (about 0.35 m a unit of scale from the middle), so the drifting rows never pile up)
        var cl = clearOf;
        // (C03 env fix: 'tilt' [lo, hi] deg each stone leans (was 0-5), 'low' a share standing only 'low_above' [lo, hi] m
        // proud (barely breaking the surface), so from a camera at the water no row of tops lines up like a ruler)
        Vector2 tilt = w.TryGetProperty("tilt", out var tl) ? V2(tl) : new(0f, 5f), lowAbove = w.TryGetProperty("low_above", out var la) ? V2(la) : new(0.01f, 0.03f);
        float low = F("low", 0f);
        float stepVar = F("step_var", 0.35f), clear = F("clear", -10f), stagger = F("stagger", -1f), shared = F("drift_shared", 0f);
        var placed = new List<(Vector2 P, float S)>();
        bool stats = System.Environment.GetEnvironmentVariable("CAUSEWAY_STATS") != null;
        int n = sp.Pieces.Length, r = 0;
        foreach (var row in w.GetProperty("rows").EnumerateArray())
        {
            float H(int k) => Mathf.PosMod(Mathf.Sin(r * 127.1f + k * 311.7f + seed * 74.7f) * 43758.5453f, 1f);
            // ('stagger': each row starts that share of a step after the one before, so the rows' stones alternate, a zigzag;
            // 'drift_shared': that share of the drift the whole path's, its rows weaving together, the rest each row's own)
            float t = stagger >= 0f ? step * (stagger * r + 0.15f * H(0)) : step * 0.6f * H(0);
            float ph1 = H(-1) * Mathf.Tau, ph2 = H(-2) * Mathf.Tau, rowSk = rowSkip != null && r < rowSkip.Length ? rowSkip[r] : skip;
            int i = 0, last = -1;
            while (t < len)
            {
                int k = i * 9 + 1;
                float dr = drift * ((1f - shared) * (0.7f * Mathf.Sin(t / driftLen * Mathf.Tau + ph1) + 0.3f * Mathf.Sin(t / driftLen * 2.3f * Mathf.Tau + ph2))
                    + shared * (0.7f * Mathf.Sin(t / driftLen * Mathf.Tau + seed) + 0.3f * Mathf.Sin(t / driftLen * 2.3f * Mathf.Tau + 2.1f * seed)));
                // (staggered rows keep their grid, each stone nudged along it by up to stepVar/2 of a step: the zigzag holds)
                float tAt = stagger >= 0f ? t + (H(k + 9) - 0.5f) * stepVar * step : t;
                var p0 = a + dir * tAt + side * (row.GetSingle() + dr + (H(k + 1) - 0.5f) * 2f * jitter);
                if (H(k) > rowSk && z.HeightAt(p0.X, p0.Y) <= water + dry)
                {
                    var p = p0;
                    int v = (int)(H(k + 2) * n) % n;
                    if (v == last) v = (v + 1 + r) % n;
                    last = v;
                    float s = Mathf.Lerp(scale.X, scale.Y, H(k + 3)), sy = s * Mathf.Lerp(0.9f, 1.1f, H(k + 4));
                    if (placed.Any(q => q.P.DistanceTo(p) < 0.35f * (q.S + s) + clear) || cl.NearProp(p, 0.35f * s)) { t += stagger >= 0f ? step : step * Mathf.Lerp(1f - stepVar, 1f + stepVar, H(k + 9)); i++; continue; }
                    placed.Add((p, s));
                    var ab2 = H(k * 7 + 5003) < low ? lowAbove : above;
                    float topY = Mathf.Max(water + Mathf.Lerp(ab2.X, ab2.Y, H(k + 5)), z.HeightAt(p.X, p.Y) + 0.06f);
                    float ta = H(k + 6) * Mathf.Tau;
                    var basis = new Basis(new Vector3(Mathf.Cos(ta), 0, Mathf.Sin(ta)), Mathf.DegToRad(Mathf.Lerp(tilt.X, tilt.Y, H(k + 7))))
                        * new Basis(Vector3.Up, H(k + 8) * Mathf.Tau).Scaled(new Vector3(s, sy, s));
                    mg.At.Add(new Transform3D(basis, new Vector3(p.X, topY - top * sy, p.Y)));
                    mg.Var.Add(v);
                    if (stats) GD.Print($"causeway stone row {r} t {tAt:F2} across {(p - a).Dot(side):F2} drift {dr:F2} scale {s:F2} top {topY - water:F3} ground {z.HeightAt(p.X, p.Y) - water:F3} at {p.X:F2},{p.Y:F2}");
                }
                t += stagger >= 0f ? step : step * Mathf.Lerp(1f - stepVar, 1f + stepVar, H(k + 9));
                i++;
            }
            r++;
        }
    }

    /// <summary>Our own flora of one file and look: its copies in cells (the species' cell), each cell a MultiMesh
    /// per LOD shown by distance, and its shadow proxy (if it casts) in cells twice as wide. A packed file's copies
    /// carry which of its pieces each is (custom data r: (index + 0.5) / 8, matched against the vertex's COLOR.a).</summary>
    /// <summary>One of our own trees as a node of its own (E7b: the Barrow's dead tree, a KayKit piece's stand-in),
    /// drawn as the zone's flora draws it (its LODs, its shadow proxy, its species' shader), or null if it isn't built.</summary>
    public static Node3D? OwnTree(string piece)
    {
        var sp = FloraSpecies.Of(piece);
        var (file, v) = sp.FileOf(piece);
        if (!ResourceLoader.Exists($"res://art/world/flora/{file}.gltf")) return null;
        var root = new Node3D { Name = "own_" + piece };
        OwnFlora(root, sp, file, KitLook.Look.Plain with { Wind = sp.Wind ?? 0 }, [Transform3D.Identity], [v]);
        return root;
    }

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
        // (Env 22 r1c, the triage judge: the crowns' shadows many-sided, straight-edged, block-shaped) a crown's proxy cast
        // through a leaf mask (leaf_shadow.gdshader; the species' shader "leaf_shadow": [mode, lobe m, hole, eat]), so its
        // outline is lobed and ragged. The same draws: a discard in the shadow pass.
        ShaderMaterial? leafSh = null;
        if (sp.Shader.TryGetValue("leaf_shadow", out var ls) && ls.ValueKind == System.Text.Json.JsonValueKind.Array && SurvivorUnchained.Args.Num("leaf-shadow", 1f) > 0)
        {
            var a = new List<float>();
            foreach (var v in ls.EnumerateArray()) a.Add(v.GetSingle());
            leafSh = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/leaf_shadow.gdshader") };
            leafSh.SetShaderParameter("mode", (int)a[0]);
            if (a.Count > 1) leafSh.SetShaderParameter("lobe", a[1]);
            if (a.Count > 2) leafSh.SetShaderParameter("hole", a[2]);
            if (a.Count > 3) leafSh.SetShaderParameter("eat", a[3]);
            if (a.Count > 4) leafSh.SetShaderParameter("rim_from", a[4]);
        }
        foreach (var ((cx, cz), idx) in Cells(shAt, 2 * cell))
        {
            var sh = Mmi(proxy, $"shadow_{cx}_{cz}", idx, shAt); sh.CastShadow = GeometryInstance3D.ShadowCastingSetting.ShadowsOnly;
            if (leafSh != null) sh.MaterialOverride = leafSh;
            root.AddChild(sh);
        }
    }

    /// <summary>What our stones keep clear of (flora_species.json "stone" "clear"; its _doc): a tree whose trunk stands within a
    /// stone's radius + 'gap' (judge E5b: a trunk out of a boulder's crown) is dropped; a stone, or a causeway's, within 'props' m
    /// of a prop or a solid tagged collider (a pylon, a chest, a gate: judge E5b, a stone in the ford's lantern post) is dropped.</summary>
    sealed class Clearance
    {
        readonly HashSet<string> trees = new();
        // (each stone kind: its radius, m a unit of its scale, and what gives way when a trunk stands in it: "tree" (dropped),
        // "nudge" (the stone moved off the trunk, dropped if it can't be), "none")
        readonly Dictionary<string, (float R, string Mode)> stoneKinds = new();
        float trunk, gap, propGap;
        readonly List<(Vector2 P, float R)> crowns = new();     // the stones a tree gives way to
        readonly List<(Vector2 P, float R)> trunks = new();     // the trees a stone gives way to
        readonly List<(Vector2 P, float R)> discs = new();
        readonly List<ColliderDef> boxes = new();
        int treesDropped, stonesDropped, stonesNudged;
        float minTree = float.MaxValue, minProp = float.MaxValue, minStone = float.MaxValue;

        static float ScaleOf(Transform3D t) => t.Basis.X.Length();

        public static Clearance Of(ZoneData z)
        {
            var c = new Clearance();
            if (!FloraOwn || !FloraSpecies.Stone.TryGetProperty("clear", out var d)) return c;
            foreach (var k in d.GetProperty("trees").EnumerateArray()) c.trees.Add(k.GetString()!);
            foreach (var k in d.GetProperty("stones").EnumerateObject()) c.stoneKinds[k.Name] = (k.Value.GetProperty("r").GetSingle(), k.Value.GetProperty("mode").GetString()!);
            c.trunk = d.GetProperty("trunk").GetSingle(); c.gap = d.GetProperty("gap").GetSingle(); c.propGap = d.GetProperty("props").GetSingle();
            foreach (var col in z.Meta.Colliders)
            {
                if (col.Tag == null || col.Soft) continue;
                if (col.Kind == ColliderKind.Box) c.boxes.Add(col);
                else c.discs.Add((new Vector2((float)col.X, (float)col.Z), (float)col.R));
            }
            foreach (var (id, at) in z.Props)
            {
                int sl = id.IndexOf('/');
                Aabb? b = null;
                foreach (var (mesh, local) in PartsOf(id[..sl], id[(sl + 1)..])) { var a = local * mesh.GetAabb(); b = b is Aabb o ? o.Merge(a) : a; }
                if (b is not Aabb bb) continue;
                c.discs.Add((new Vector2(at.Origin.X, at.Origin.Z) + new Vector2(bb.GetCenter().X, bb.GetCenter().Z) * ScaleOf(at), 0.5f * Mathf.Max(bb.Size.X, bb.Size.Z) * ScaleOf(at)));
            }
            foreach (var g in z.Flora)
            {
                if (c.stoneKinds.TryGetValue(g.Kind, out var sk) && sk.Mode == "tree")
                    foreach (var t in g.At) c.crowns.Add((new Vector2(t.Origin.X, t.Origin.Z), sk.R * ScaleOf(t)));
                if (c.trees.Contains(g.Kind))
                    foreach (var t in g.At) c.trunks.Add((new Vector2(t.Origin.X, t.Origin.Z), c.trunk * ScaleOf(t)));
            }
            // (the trees that give way are out of the trunks the stones give way to)
            c.trunks.RemoveAll(tr => Nearest(c.crowns, tr.P, tr.R, out _) < c.gap);
            return c;
        }

        /// <summary>How far a disc's rim stands from the nearest prop or tagged collider (negative: inside it).</summary>
        float PropGap(Vector2 p, float r)
        {
            float best = float.MaxValue;
            foreach (var (q, qr) in discs) best = Mathf.Min(best, p.DistanceTo(q) - qr - r);
            foreach (var b in boxes)
            {
                // (into the box's own frame: its half sizes hw, hd, turned by rot)
                var d = p - new Vector2((float)b.X, (float)b.Z);
                float cs = Mathf.Cos(-(float)b.Rot), sn = Mathf.Sin(-(float)b.Rot);
                var l = new Vector2(d.X * cs - d.Y * sn, d.X * sn + d.Y * cs);
                var o = new Vector2(Mathf.Max(Mathf.Abs(l.X) - (float)b.Hw, 0f), Mathf.Max(Mathf.Abs(l.Y) - (float)b.Hd, 0f));
                best = Mathf.Min(best, o.Length() - r);
            }
            return best;
        }

        public bool NearProp(Vector2 p, float r)
        {
            if (discs.Count + boxes.Count == 0) return false;
            float g = PropGap(p, r);
            if (g < propGap) { stonesDropped++; return true; }
            minProp = Mathf.Min(minProp, g);
            return false;
        }

        static float Nearest(List<(Vector2 P, float R)> l, Vector2 p, float r, out Vector2 at)
        {
            float best = float.MaxValue; at = p;
            foreach (var (q, qr) in l)
            {
                if (Mathf.Abs(q.X - p.X) > qr + r + 4f || Mathf.Abs(q.Y - p.Y) > qr + r + 4f) continue;
                float d = p.DistanceTo(q) - qr - r;
                if (d < best) { best = d; at = q; }
            }
            return best;
        }

        /// <summary>A group with its copies cleared: a tree too near a boulder dropped; a stone too near a trunk nudged off it
        /// (dropped if two tries leave it near one), or too near a prop dropped.</summary>
        public ZoneData.FloraGroup Apply(ZoneData.FloraGroup g)
        {
            bool tree = trees.Contains(g.Kind);
            bool stone = stoneKinds.TryGetValue(g.Kind, out var sk);
            if (!tree && !stone) return g;
            var outAt = new List<Transform3D>(g.At.Length);
            bool changed = false;
            foreach (var t0 in g.At)
            {
                var t = t0;
                var p = new Vector2(t.Origin.X, t.Origin.Z);
                if (tree)
                {
                    float d = Nearest(crowns, p, trunk * ScaleOf(t), out _);
                    if (d < gap) { treesDropped++; changed = true; continue; }
                    minTree = Mathf.Min(minTree, d);
                    outAt.Add(t);
                    continue;
                }
                float r = sk.R * ScaleOf(t);
                if (sk.Mode == "nudge")
                {
                    for (int k = 0; k < 2; k++)
                    {
                        float d = Nearest(trunks, p, r, out var q);
                        if (d >= gap) break;
                        var away = (p - q).LengthSquared() > 1e-6f ? (p - q).Normalized() : Vector2.Right;
                        p += away * (gap - d + 0.02f);
                        if (k == 0) stonesNudged++;
                        changed = true;
                    }
                    float d2 = Nearest(trunks, p, r, out _);
                    if (d2 < gap) { stonesDropped++; changed = true; continue; }
                    minStone = Mathf.Min(minStone, d2);
                    t.Origin = new Vector3(p.X, t.Origin.Y, p.Y);
                }
                if (NearProp(p, r)) { changed = true; continue; }
                outAt.Add(t);
            }
            return changed ? g with { At = outAt.ToArray() } : g;
        }

        public void Report(ZoneData z)
        {
            if (System.Environment.GetEnvironmentVariable("CLEAR_STATS") == null) return;
            GD.Print($"clearance {z.Id}: trees dropped {treesDropped}, stones nudged {stonesNudged}, stones dropped {stonesDropped}; nearest kept trunk to a boulder's rim {minTree:F2} m,"
                + $" nearest nudged-kind stone to a trunk {minStone:F2} m, nearest kept stone to a prop {minProp:F2} m");
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
        Slices.All(Props(z, root));
        return root;
    }

    /// <summary>Props' steps, under root (Slices: a frame may end after each piece).</summary>
    public static IEnumerable<object?> Props(ZoneData z, Node3D root)
    {
        var groups = new Dictionary<(string, int, int), List<Transform3D>>();
        float cell = PropCell;
        // Our own props where the zone swaps a kit piece for one (OwnProps: its props_own.json "pieces").
        var own = OwnProps.For(z.Id);
        var ours = new List<(string Id, string Preset, Transform3D At)>();
        int droppedInside = 0;
        var insideNodes = new List<Node3D>();
        // Our own town walls where the zone has them (OwnWalls: props_own.json "walls").
        var walls = OwnWalls.For(z);
        for (int pi = 0; pi < z.Props.Count; pi++)
        {
            if (pi % 16 == 15) yield return null;
            var (id, at) = z.Props[pi];
            int house = pi < z.PropHouse.Count ? z.PropHouse[pi] : -1;
            if (walls != null && walls.Take(id, house, at, cell)) continue;
            // (E9c2) nothing of the street's left standing inside a closed house (the cutaway shows the inside: a cart
            // parked in house 17, barrels in house 14's): its own furnishings below stand there instead
            if (walls != null && house < 0 && OwnWalls.InsideAny(z, at.Origin.X, at.Origin.Z, 0.25f)) { droppedInside++; continue; }
            // (E9d) the web game's wares and stock at the stalls our own stalls replace, cleared
            if (own != null && OwnProps.Cleared(own, id, at.Origin)) continue;
            if (own != null && OwnProps.Swap(own, id, at.Origin) is string preset) { ours.Add((id, preset, at)); continue; }
            var k = (id, Mathf.FloorToInt(at.Origin.X / cell), Mathf.FloorToInt(at.Origin.Z / cell));
            if (!groups.TryGetValue(k, out var list)) groups[k] = list = new();
            list.Add(at);
        }
        // (E9c2) the closed houses' floors, hearths and furniture (OwnWalls.Furnish), as kit pieces
        if (walls != null)
        {
            yield return "props: the street's";
            var furn = OwnWalls.Furnish(z);
            yield return "props: the houses furnished";
            foreach (var (id0, at) in furn)
            {
                yield return "props: a house's piece";
                // (E9d) our own trestle table and lidded barrel inside for the kit's (its table's pale battens read as a rug's
                // border over its top, its open barrels as pale empty rings from above)
                // (E9d r2: ours and the kit's both built along x, as Furnish lays the bench along the table's long side: no turn)
                var id = id0 switch { "props/Table_Large" => "own:table", "props/Barrel" => "own:barrel", _ => id0 };
                // (E9c3) ours, the hearths, rugs and rushes as nodes of their own (HouseFade brings them in with their house:
                // "inside"); the kit's pieces grouped apart from the street's ("in|"), their copies given their unit by OwnWalls
                if (Insides.Node(id, at) is Node3D n) { n.SetMeta("inside", true); insideNodes.Add(n); continue; }
                if (id.Contains(':') || id is "hearth" or "rug" or "straw") continue;
                var k = ("in|" + id, Mathf.FloorToInt(at.Origin.X / cell), Mathf.FloorToInt(at.Origin.Z / cell));
                if (!groups.TryGetValue(k, out var list)) groups[k] = list = new();
                list.Add(at);
            }
            GD.Print($"house insides: {furn.Count} pieces furnished, {droppedInside} street props dropped from inside");
        }
        // (Each piece's file loaded first, so the time it takes shows apart from placing them.)
        foreach (var ((gid, _, _), _) in groups) { var id = gid.StartsWith("in|") ? gid[3..] : gid; int sl = id.IndexOf('/'); PartsOf(id[..sl], id[(sl + 1)..]); yield return "props: a file loaded"; }
        Perf.Lap("props: their files loaded");
        foreach (var ((gid, _, _), list) in groups)
        {
            yield return "props: a group";
            bool inside = gid.StartsWith("in|");
            var id = inside ? gid[3..] : gid;
            int slash = id.IndexOf('/');
            string kit = id[..slash], piece = id[(slash + 1)..];
            // ((E9c2) a house's floor laid flat: no foot to darken)
            bool foot = kit is "village" or "custom" && !piece.StartsWith("Floor_");
            foreach (var (mesh, local) in PartsOf(kit, piece))
            {
                var mm = new MultiMesh { TransformFormat = MultiMesh.TransformFormatEnum.Transform3D, Mesh = Looked(mesh, KitLook.Look.Plain, foot), InstanceCount = list.Count };
                for (int i = 0; i < list.Count; i++) mm.SetInstanceTransform(i, list[i] * local);
                var mmi = new MultiMeshInstance3D { Multimesh = mm, Name = piece };
                // Which piece, and where each one stands, for taking one away in play (HideProps).
                mmi.SetMeta("prop", id);
                mmi.SetMeta("at", new Godot.Collections.Array<Vector3>(list.Select(t => t.Origin)));
                if (inside) { mmi.SetMeta("inside", true); mmi.CastShadow = GeometryInstance3D.ShadowCastingSetting.Off; }
                root.AddChild(mmi);
            }
        }
        foreach (var n in insideNodes) root.AddChild(n);
        if (walls != null) foreach (var s in walls.Build(root)) yield return s;
        foreach (var (id, preset, at) in ours)
        {
            yield return "props: one of ours";
            int slash = id.IndexOf('/');
            Aabb? kit = null;
            foreach (var (mesh, local) in PartsOf(id[..slash], id[(slash + 1)..]))
                kit = kit is Aabb k ? k.Merge(local * mesh.GetAabb()) : local * mesh.GetAabb();
            if (kit is not Aabb box || OwnProps.Fitted(preset, box) is not Node3D n) continue;
            n.Transform = own != null ? OwnProps.Nudged(own, at) : at;
            // Which piece, and where it stood in the kit, for taking it away in play (HideProps).
            n.SetMeta("prop", id);
            n.SetMeta("at1", at.Origin);
            root.AddChild(n);
        }
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
