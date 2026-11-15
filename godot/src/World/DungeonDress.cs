using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// A dungeon's props, placed by rule from its room graph (ZoneData.Rooms) and its wall field. Every room is dressed by
/// its Kind and the map's theme: the ravine is the Kerchiefs' bandit camp (boulders, stores, tents, a palisade across the
/// south), the den is a wolf's lair (mossy rocks, fallen logs, glow fungus, bones). Spots come from one finder that marches
/// a ray from the room's centre to its wall. All randomness is the hash, seeded by room index: a map always dresses the same.
/// The camera looks north from the south, so tall props stand on north and side walls only; nothing here has a collider.
/// </summary>
public static partial class DungeonDress
{
    // A place on a wall: x, z, yaw facing the room's centre, and the ray's outward direction.
    readonly record struct Spot(float X, float Z, float Yaw, float Dx, float Dz);

    static readonly string[] Stores = { "barrel", "barrels_door", "crate", "heap_crates", "heap_sacks" };
    // (the flora boulders draw black off their kit material: the scanned rocks, which carry their own)
    static readonly string[] RavineRocks = { "res://art/world/rock_07.glb", "res://art/world/rock_09.glb", "res://art/world/boulder_01.glb" };
    // (the den's rocks: our own painted plane rocks, env_rocks.py through tools/look/wild.py rocks, drawn in their kit look)
    // (lead 6 tried the CC0 scans boulder_01 / rock_07 / rock_moss_set_01 here, lifted: crusty yellow sponge, not painted
    // stone; and these plane rocks rebuilt with smooth normals: they lost their kit data and drew dark)
    static readonly string[] DenRocks = { "res://art/world/flora/boulder.gltf", "res://art/world/flora/bouldermid.gltf", "res://art/world/flora/boulderlarge.gltf" };
    static readonly string[] Logs = { "res://art/world/dead_tree_trunk.glb", "res://art/world/dead_tree_trunk_02.glb", "fallen_trunk" };

    sealed class Ctx
    {
        public ZoneData Z = null!;
        public Node3D Root = null!;
        public readonly List<Vector2> Used = new();
        public readonly Dictionary<string, int> Count = new();
        public readonly SurfaceTool Shrooms = new(), Bones = new(), Poles = new(), Canvas = new(), Cloth = new();
        public int PoleParts, CanvasTris, ClothTris;
        public int Clusters, BoneCount;
        public void Tick(string k) { Count[k] = Count.GetValueOrDefault(k) + 1; }
    }

    public static Node3D? Build(ZoneData z)
    {
        if (z.WallField == null || z.Rooms.Count == 0) return null;
        var c = new Ctx { Z = z, Root = new Node3D { Name = "DungeonDress" } };
        c.Shrooms.Begin(Mesh.PrimitiveType.Triangles);
        c.Bones.Begin(Mesh.PrimitiveType.Triangles);
        c.Poles.Begin(Mesh.PrimitiveType.Triangles);
        c.Canvas.Begin(Mesh.PrimitiveType.Triangles);
        c.Cloth.Begin(Mesh.PrimitiveType.Triangles);
        bool den = z.DungeonTheme == "den";
        for (int i = 0; i < z.Rooms.Count; i++)
        {
            var r = z.Rooms[i];
            int s = i + 1;
            if (den) Den(c, r, s); else Ravine(c, r, s);
        }
        if (den) { DenDecals(c); DenBankDecals(c); }
        if (c.Clusters > 0) Flush(c, c.Shrooms, "Fungus", new StandardMaterial3D { ShadingMode = BaseMaterial3D.ShadingModeEnum.Unshaded, AlbedoColor = new Color(0.45f, 1.0f, 0.88f) });
        if (c.BoneCount > 0) Flush(c, c.Bones, "Bones", new StandardMaterial3D { AlbedoColor = new Color(0.56f, 0.5f, 0.41f), Roughness = 1f });
        // Poles (palisade, tents, banners) in one mesh in bark; canvas (vertex-coloured per tent) and banner cloth in one each.
        if (c.PoleParts > 0) { c.Poles.GenerateTangents(); c.Root.AddChild(new MeshInstance3D { Name = "Poles", Mesh = c.Poles.Commit(), MaterialOverride = Bark() }); }
        if (c.CanvasTris > 0) { c.Canvas.GenerateNormals(); c.Root.AddChild(new MeshInstance3D { Name = "Canvas", Mesh = c.Canvas.Commit(), MaterialOverride = new StandardMaterial3D { Roughness = 1f, CullMode = BaseMaterial3D.CullModeEnum.Disabled, VertexColorUseAsAlbedo = true } }); }
        if (c.ClothTris > 0) { c.Cloth.GenerateNormals(); c.Root.AddChild(new MeshInstance3D { Name = "BannerCloth", Mesh = c.Cloth.Commit(), MaterialOverride = new StandardMaterial3D { AlbedoColor = new Color(0.48f, 0.07f, 0.06f), Roughness = 1f, CullMode = BaseMaterial3D.CullModeEnum.Disabled } }); }
        var parts = new List<string>();
        foreach (var kv in c.Count) parts.Add($"{kv.Key} {kv.Value}");
        GD.Print($"DungeonDress {z.DungeonTheme}: {string.Join(", ", parts)} over {z.Rooms.Count} rooms");
        return c.Root;
    }

    // ---- themes ----

    static void Ravine(Ctx c, (float X, float Z, float R, string Kind) r, int s)
    {
        if (r.Kind != "Bend")
        {
            // 2 to 4 boulders, low, any side.
            int n = 2 + (int)(Hash(s, 1, 1) * 3);
            foreach (var sp in WallSpots(c, r, 0.4f + 0.6f * Hash(s, 1, 2), n, s * 7 + 1, false))
                PlaceScene(c, Pick(RavineRocks, s, sp), sp.X, sp.Z, Hash(s, 2, (int)sp.X) * Mathf.Tau, 0.7f + 0.8f * Hash(s, 3, (int)sp.Z), 0.15f, "boulders");
        }
        switch (r.Kind)
        {
            case "Start":
                var at = new Vector2(r.X, r.Z - 0.45f * r.R);
                if (Open(c, at.X, at.Y, 2.5f))
                {
                    c.Root.AddChild(Campfire.Build(new Vector3(at.X, H(c, at.X, at.Y), at.Y), 1, true));
                    c.Tick("campfire");
                    for (int k = 0; k < 2; k++)
                    {
                        float a = Hash(s, 4, k) * Mathf.Tau;
                        float bx = at.X + Mathf.Cos(a) * 1.6f, bz = at.Y + Mathf.Sin(a) * 1.6f;
                        if (Open(c, bx, bz, 1f)) PlaceProp(c, "bedroll_open", bx, bz, Mathf.Atan2(-(at.X - bx), -(at.Y - bz)), 1f);
                    }
                    float pa = Hash(s, 5, 0) * Mathf.Tau, px = at.X + Mathf.Cos(pa) * 2.4f, pz = at.Y + Mathf.Sin(pa) * 2.4f;
                    if (Open(c, px, pz, 1f)) PlaceProp(c, "pack", px, pz, pa, 1f);
                }
                Palisade(c, r, s);
                break;
            case "Clearing":
                foreach (var sp in WallSpots(c, r, 1.0f + 0.6f * Hash(s, 6, 0), 2, s * 7 + 2, true))
                    Cluster(c, sp, (int)(Hash(s, 7, (int)sp.X) * 3), s);
                break;
            case "Altar":
                foreach (int side in new[] { -1, 1 })
                    PlaceAt(c, r, -90 + side * 22, 1.2f, "banner", s);
                PlaceAt(c, r, -90, 2.8f, "brazier", s);
                break;
            case "Boss":
                PlaceAt(c, r, -90, 1.2f, "chest", s);
                foreach (int side in new[] { -1, 1 })
                {
                    PlaceAt(c, r, -90 + side * 26, 1.2f, "banner", s);
                    PlaceAt(c, r, -90 + side * 45, 1.6f, "brazier", s);
                }
                foreach (var sp in WallSpots(c, r, 1.3f, 1, s * 7 + 3, true)) Cluster(c, sp, 0, s);
                Palisade(c, r, s);
                break;
        }
    }

    static void Den(Ctx c, (float X, float Z, float R, string Kind) r, int s)
    {
        if (r.Kind != "Bend")
        {
            // 2 to 4 mossy rocks, the first on a north/side wall, the rest anywhere.
            int n = 2 + (int)(Hash(s, 1, 1) * 3);
            for (int k = 0; k < n; k++)
                foreach (var sp in WallSpots(c, r, 0.5f + 0.7f * Hash(s, 1, 10 + k), 1, s * 7 + 10 + k, k == 0))
                    PlaceScene(c, Pick(DenRocks, s * 3 + k, sp), sp.X, sp.Z, Hash(s, 2, k) * Mathf.Tau, 0.8f + 0.8f * Hash(s, 3, k), 0.1f, "rocks");   // (1.4-2.4 tried: the plane rocks grew into big grey boxes)
        }
        if (r.Kind == "Clearing" || r.Kind == "Boss")
            foreach (var sp in WallSpots(c, r, 1.2f, 1, s * 7 + 5, true))
            {
                string log = Logs[(int)(Hash(s, 8, 0) * Logs.Length)];
                float yaw = sp.Yaw + Mathf.Pi / 2;
                if (log.StartsWith("res:")) PlaceScene(c, log, sp.X, sp.Z, yaw, 0.7f, 0.1f, "logs");   // (at 1 the trunks lay as long dark bars across a room)
                else PlaceProp(c, log, sp.X, sp.Z, yaw, 1f);
            }
        Fungus(c, r, s);
    }

    // ---- clusters ----

    // One cluster by kind (0 stores, 1 tent, 2 wood) around a wall spot, spread along the wall and in from it.
    static void Cluster(Ctx c, Spot sp, int kind, int s)
    {
        string[] set = kind switch
        {
            0 => PickStores(s, sp),
            1 => new[] { "bedroll_rolled", "pack" },
            _ => new[] { "woodpile", "log_long", "crate" },
        };
        if (kind == 1) Tent(c, sp, s);
        var inward = new Vector2(-Mathf.Sin(sp.Yaw), -Mathf.Cos(sp.Yaw));
        var tan = new Vector2(-inward.Y, inward.X);
        for (int k = 0; k < set.Length; k++)
        {
            float along = (Hash(s, k, (int)(sp.X * 3)) * 2 - 1) * 1.4f, back = Hash(s, k, (int)(sp.Z * 3) + 99) * 1.1f;
            float x = sp.X + tan.X * along + inward.X * back, zz = sp.Z + tan.Y * along + inward.Y * back;
            if (!Open(c, x, zz, 0.3f)) continue;
            PlaceProp(c, set[k], x, zz, Hash(s, k, 55) * Mathf.Tau, 0.95f + 0.2f * Hash(s, k, 56));
        }
        c.Tick(kind == 0 ? "stores" : kind == 1 ? "tents" : "woodpiles");
    }

    static string[] PickStores(int s, Spot sp)
    {
        int n = 3 + (int)(Hash(s, 9, (int)sp.X) * 3);
        var a = new string[n];
        for (int k = 0; k < n; k++) a[k] = Stores[(int)(Hash(s, 10 + k, (int)sp.Z) * Stores.Length)];
        return a;
    }

    // A prop on the ray at a given angle (degrees; -90 is north), `inside` metres from the wall; skipped if no wall or a pit.
    static void PlaceAt(Ctx c, (float X, float Z, float R, string Kind) r, float deg, float inside, string preset, int s)
    {
        var sp = Ray(c, r, deg * Mathf.Pi / 180f, inside, 0);
        if (sp == null) return;
        c.Used.Add(new Vector2(sp.Value.X, sp.Value.Z));
        if (preset == "banner") { Banner(c, sp.Value.X, sp.Value.Z, sp.Value.Yaw); return; }
        PlaceProp(c, preset, sp.Value.X, sp.Value.Z, sp.Value.Yaw + (Hash(s, (int)deg, 3) - 0.5f) * 0.2f, 1f);
    }

    // ---- spot finder ----

    static float Bil(ZoneData z, float[] f, float x, float zz)
    {
        int res = z.Res; float half = z.Half, step = z.Step;
        float u = Mathf.Clamp((x + half) / step, 0, res - 1.001f), v = Mathf.Clamp((zz + half) / step, 0, res - 1.001f);
        int i = (int)u, j = (int)v; float fu = u - i, fv = v - j;
        return Mathf.Lerp(Mathf.Lerp(f[j * res + i], f[j * res + i + 1], fu), Mathf.Lerp(f[(j + 1) * res + i], f[(j + 1) * res + i + 1], fu), fv);
    }

    static float Wall(Ctx c, float x, float zz) => c.Z.DungeonTheme == "den" && c.Z.HoleField != null ? DungeonWalls.WallOnly(Bil(c.Z, c.Z.WallField!, x, zz), Bil(c.Z, c.Z.HoleField, x, zz)) : Bil(c.Z, c.Z.WallField!, x, zz);   // (the den's pits are not walls)
    static float Hole(Ctx c, float x, float zz) => c.Z.HoleField == null ? 99f : Bil(c.Z, c.Z.HoleField, x, zz);
    static bool Open(Ctx c, float x, float zz, float m) => Wall(c, x, zz) > m && Hole(c, x, zz) > m;
    static float H(Ctx c, float x, float zz) => (float)c.Z.Ground.HeightAt(x, zz);

    // March from the centre outward in 0.25 m steps until the wall field drops below `inside`; the spot there.
    // Rejects pits (hole field < 1.5), anything past 1.6*R, and (sep > 0) a place within sep of one already used.
    static Spot? Ray(Ctx c, (float X, float Z, float R, string Kind) r, float ang, float inside, float sep)
    {
        float dx = Mathf.Cos(ang), dz = Mathf.Sin(ang), max = 1.6f * r.R;
        for (float d = 0; d <= max; d += 0.25f)
        {
            float x = r.X + dx * d, zz = r.Z + dz * d;
            if (Wall(c, x, zz) >= inside) continue;
            if (d < 0.5f || Hole(c, x, zz) < 1.5f) return null;
            if (sep > 0) foreach (var u in c.Used) if (u.DistanceTo(new Vector2(x, zz)) < sep) return null;
            return new Spot(x, zz, Mathf.Atan2(dx, dz) + Mathf.Pi, dx, dz);
        }
        return null;
    }

    // `count` spots round the room, `inside` metres off the wall, evenly stepped from a hashed start angle.
    // northish keeps rays with dz <= 0.35 (north and side walls) for tall props.
    static List<Spot> WallSpots(Ctx c, (float X, float Z, float R, string Kind) r, float inside, int count, int seed, bool northish)
    {
        var res = new List<Spot>();
        const int N = 24;
        int stride = System.Math.Max(1, N / count), start = (int)(Hash(seed, 1, 1) * N);
        float a0 = Hash(seed, 2, 2) * Mathf.Tau / N;
        for (int pass = 0; pass < stride && res.Count < count; pass++)
            for (int k = 0; k < count * 2 && res.Count < count; k++)
            {
                int idx = (start + k * stride + pass) % N;
                float ang = a0 + idx * Mathf.Tau / N;
                if (northish && Mathf.Sin(ang) > 0.35f) continue;
                var sp = Ray(c, r, ang, inside, 2.5f);
                if (sp == null) continue;
                res.Add(sp.Value);
                c.Used.Add(new Vector2(sp.Value.X, sp.Value.Z));
            }
        return res;
    }

    // ---- placing ----

    static void PlaceProp(Ctx c, string preset, float x, float zz, float yaw, float scale)
    {
        var n = OwnProps.Piece(preset);
        if (n == null) return;
        float y = H(c, x, zz) - (OwnProps.Box(preset)?.Position.Y ?? 0) * scale;
        n.Scale = Vector3.One * scale;
        n.Position = new Vector3(x, y, zz);
        n.Rotation = new Vector3(0, yaw, 0);
        c.Root.AddChild(n);
        c.Tick("props");
    }

    // A scene from a path, sunk `sink` of its height into the floor (its bounds from its meshes).
    static void PlaceScene(Ctx c, string path, float x, float zz, float yaw, float scale, float sink, string tag)
    {
        if (!ResourceLoader.Exists(path)) return;
        var n = GD.Load<PackedScene>(path)?.Instantiate<Node3D>();
        if (n == null) return;
        if (path.Contains("/flora/")) Kit(n, c.Z.DungeonTheme == "den");
        else if (tag == "logs" && c.Z.DungeonTheme == "den") Lift(n, new Color(1.5f, 1.36f, 1.18f));   // (den_room.png's log: pale, weathered)
        var b = Bounds(n, Transform3D.Identity) ?? new Aabb();
        n.Scale = Vector3.One * scale;
        n.Position = new Vector3(x, H(c, x, zz) - (b.Position.Y + sink * b.Size.Y) * scale, zz);
        n.Rotation = new Vector3(0, yaw, 0);
        c.Root.AddChild(n);
        c.Tick(tag);
    }

    // A flora piece's materials through the kit look (KitLook.For: our own rocks' painted OWN_ROCK); raw they draw black.
    static void Kit(Node n, bool den)
    {
        if (n is MeshInstance3D mi && mi.Mesh != null)
        {
            var m = (Mesh)mi.Mesh.Duplicate();
            for (int i = 0; i < m.GetSurfaceCount(); i++)
                if (m.SurfaceGetMaterial(i) is Material mat)
                {
                    var k = KitLook.For(mat, KitLook.Look.Plain);
                    // (the den's rocks: the one stone a step darker and olive, mossed over their tops, FROM den_room.png)
                    if (k is ShaderMaterial sm && den)
                    {
                        sm = (ShaderMaterial)sm.Duplicate();
                        sm.SetShaderParameter("paint_tint", new Vector3(1.0f, 0.9f, 0.76f));   // (lead 6: warm grey-brown, not grey)
                        sm.SetShaderParameter("moss_amount", 1.0f);
                        sm.SetShaderParameter("moss_face", new Vector2(0.2f, 0.6f));
                        sm.SetShaderParameter("moss_edge", 0.0f);
                        sm.SetShaderParameter("moss_color", new Color(0.36f, 0.4f, 0.18f));
                        k = sm;
                    }
                    m.SurfaceSetMaterial(i, k);
                }
            mi.Mesh = m;
        }
        foreach (var ch in n.GetChildren()) Kit(ch, den);
    }

    // A scan's own albedo lifted (the den's scanned trunks drew as dark bars against den_room.png's pale weathered log).
    static void Lift(Node n, Color tint)
    {
        if (n is MeshInstance3D mi && mi.Mesh != null)
        {
            var m = (Mesh)mi.Mesh.Duplicate();
            for (int i = 0; i < m.GetSurfaceCount(); i++)
                if (m.SurfaceGetMaterial(i) is StandardMaterial3D sm)
                {
                    var d = (StandardMaterial3D)sm.Duplicate();
                    d.AlbedoColor = tint;
                    m.SurfaceSetMaterial(i, d);
                }
            mi.Mesh = m;
        }
        foreach (var ch in n.GetChildren()) Lift(ch, tint);
    }

    static Aabb? Bounds(Node3D n, Transform3D parent)
    {
        var t = parent * n.Transform;
        Aabb? box = null;
        if (n is MeshInstance3D mi && mi.Mesh != null) box = t * mi.Mesh.GetAabb();
        foreach (var ch in n.GetChildren())
            if (ch is Node3D cn && Bounds(cn, t) is Aabb cb) box = box == null ? cb : box.Value.Merge(cb);
        return box;
    }

    static string Pick(string[] a, int s, Spot sp) => a[(int)(Hash(s, (int)(sp.X * 10), (int)(sp.Z * 10)) * a.Length) % a.Length];

    // ---- procedural: tent, banner ----

    static void Pole(Ctx c, Transform3D t, float r, float h, Vector3 mid, bool alongX)
    {
        var b = alongX ? new Basis(Vector3.Back, Mathf.Pi / 2) : Basis.Identity;
        c.Poles.AppendFrom(new CylinderMesh { TopRadius = r, BottomRadius = r, Height = h, RadialSegments = 8, Rings = 1 }, 0, t * new Transform3D(b, mid));
        c.PoleParts++;
    }

    static void Tri(SurfaceTool st, Transform3D t, Vector3 a, Vector3 b, Vector3 d)
    {
        st.AddVertex(t * a); st.AddVertex(t * b); st.AddVertex(t * d);
    }

    // A ridge tent against a wall: long axis along the wall, two sagging slopes (6x4 quads), two end panels, one end open.
    static void Tent(Ctx c, Spot sp, int s)
    {
        float k = 0.85f + 0.3f * Hash(s, 60, (int)sp.X), L = 2.2f * k, W = 1.8f * (0.85f + 0.3f * Hash(s, 61, (int)sp.Z)), Hr = 1.5f;
        // Placed a metre in from the wall spot, its local -z toward the room, local x along the wall.
        var inward = new Vector3(-Mathf.Sin(sp.Yaw), 0, -Mathf.Cos(sp.Yaw));
        float x = sp.X + inward.X * 1.0f, zz = sp.Z + inward.Z * 1.0f;
        if (!Open(c, x, zz, 0.5f)) return;
        var t = new Transform3D(new Basis(Vector3.Up, sp.Yaw), new Vector3(x, H(c, x, zz), zz));
        Color[] cols = { new(0.42f, 0.12f, 0.09f), new(0.52f, 0.45f, 0.35f), new(0.38f, 0.32f, 0.24f) };
        c.Canvas.SetColor(cols[(int)(Hash(s, 62, (int)sp.X) * 3) % 3]);
        foreach (int side in new[] { -1, 1 })
            for (int j = 0; j < 4; j++)
                for (int i = 0; i < 6; i++)
                {
                    Vector3 P(int ii, int jj)
                    {
                        float tt = jj / 4f;
                        return new Vector3(-L / 2 + L * ii / 6f, Hr * tt - 0.08f * Mathf.Sin(Mathf.Pi * tt) * Mathf.Sin(Mathf.Pi * ii / 6f), side * W / 2 * (1 - tt));
                    }
                    Tri(c.Canvas, t, P(i, j), P(i + 1, j), P(i, j + 1));
                    Tri(c.Canvas, t, P(i + 1, j), P(i + 1, j + 1), P(i, j + 1));
                    c.CanvasTris += 2;
                }
        // End panel at +x; the -x end stays open.
        Tri(c.Canvas, t, new Vector3(L / 2, 0, -W / 2), new Vector3(L / 2, 0, W / 2), new Vector3(L / 2, Hr, 0));
        c.CanvasTris++;
        Pole(c, t, 0.04f, L + 0.2f, new Vector3(0, Hr, 0), true);
        foreach (int e in new[] { -1, 1 }) Pole(c, t, 0.04f, Hr, new Vector3(e * L / 2, Hr / 2, 0), false);
        c.Tick("tents");
    }

    // A banner: pole 3.2 m, crossbar 0.9 m, a 0.8 x 1.6 cloth (4x8) with a swallowtail foot and a wave, facing the room.
    static void Banner(Ctx c, float x, float zz, float yaw)
    {
        var t = new Transform3D(new Basis(Vector3.Up, yaw), new Vector3(x, H(c, x, zz), zz));
        Pole(c, t, 0.05f, 3.2f, new Vector3(0, 1.6f, 0), false);
        Pole(c, t, 0.03f, 0.9f, new Vector3(0, 3.1f, -0.06f), true);
        Vector3 P(int i, int j)
        {
            float y = 3.05f - 1.6f * j / 8f;
            if (j == 8 && i == 2) y += 0.3f;
            return new Vector3(-0.4f + 0.8f * i / 4f, y, -0.1f + 0.04f * Mathf.Sin(j));
        }
        for (int j = 0; j < 8; j++)
            for (int i = 0; i < 4; i++)
            {
                Tri(c.Cloth, t, P(i, j), P(i + 1, j), P(i, j + 1));
                Tri(c.Cloth, t, P(i + 1, j), P(i + 1, j + 1), P(i, j + 1));
                c.ClothTris += 2;
            }
        c.Tick("banners");
    }

    // ---- procedural: palisade, fungus, bones ----

    // Stakes along the south-facing wall of a room (ray dz >= 0.6), one every 0.3 m, leaning outward, in one mesh.
    static void Palisade(Ctx c, (float X, float Z, float R, string Kind) r, int s)
    {
        var st = c.Poles;
        Spot? prev = null;
        float carry = 0;
        int stakes = 0;
        for (int deg = 0; deg < 360; deg += 2)
        {
            var sp = Ray(c, r, deg * Mathf.Pi / 180f, 0.5f, 0);
            if (sp == null || sp.Value.Dz < 0.6f) { prev = null; continue; }
            var p = sp.Value;
            if (prev is Spot q)
            {
                float gap = new Vector2(p.X - q.X, p.Z - q.Z).Length();
                if (gap > 1f) carry = 0;
                else
                {
                    float d = 0.3f - carry;
                    for (; d <= gap; d += 0.3f)
                    {
                        float t = d / gap, x = Mathf.Lerp(q.X, p.X, t), zz = Mathf.Lerp(q.Z, p.Z, t);
                        Stake(c, st, x, zz, new Vector2(Mathf.Lerp(q.Dx, p.Dx, t), Mathf.Lerp(q.Dz, p.Dz, t)).Normalized(), s * 1000 + stakes++);
                    }
                    carry = gap - (d - 0.3f);
                }
            }
            else carry = 0;
            prev = p;
        }
        if (stakes == 0) return;
        c.PoleParts += stakes;
        c.Count["stakes"] = c.Count.GetValueOrDefault("stakes") + stakes;
    }

    static void Stake(Ctx c, SurfaceTool st, float x, float zz, Vector2 outward, int id)
    {
        float h = 1.5f + 0.6f * Hash(id, 1, 1), tip = 0.35f;
        var o = new Vector3(outward.X, 0, outward.Y);
        var axis = Vector3.Up.Cross(o).Normalized();
        float lean = Mathf.DegToRad(6 + 4 * Hash(id, 2, 2));
        var t = new Transform3D(new Basis(axis, lean), new Vector3(x, H(c, x, zz) - 0.1f, zz));
        st.AppendFrom(new CylinderMesh { TopRadius = 0.1f, BottomRadius = 0.1f, Height = h, RadialSegments = 8, Rings = 1 }, 0, t * new Transform3D(Basis.Identity, new Vector3(0, h / 2, 0)));
        st.AppendFrom(new CylinderMesh { TopRadius = 0.035f, BottomRadius = 0.1f, Height = tip, RadialSegments = 8, Rings = 1 }, 0, t * new Transform3D(Basis.Identity, new Vector3(0, h + tip / 2, 0)));
    }

    // 1 to 3 glow-fungus clusters at a room's wall foot, 4 to 8 mushrooms each, one cool light apiece; 14 to the map.
    static void Fungus(Ctx c, (float X, float Z, float R, string Kind) r, int s)
    {
        int n = 3 + (int)(Hash(s, 20, 0) * 3);
        for (int k = 0; k < n && c.Clusters < 48; k++)
        {
            var sp = Ray(c, r, Hash(s, 21, k) * Mathf.Tau, 0.5f + 0.5f * Hash(s, 22, k), 0);
            if (sp == null) continue;
            float cx = sp.Value.X, cz = sp.Value.Z;
            int m = 4 + (int)(Hash(s, 23, k) * 5);
            for (int q = 0; q < m; q++)
            {
                float a = Hash(s, 24 + q, k) * Mathf.Tau, d = Mathf.Sqrt(Hash(s, 25 + q, k)) * 0.5f;
                float x = cx + Mathf.Cos(a) * d, zz = cz + Mathf.Sin(a) * d;
                if (Wall(c, x, zz) < 0.05f || Hole(c, x, zz) < 0.3f) continue;
                float sh = 0.12f + 0.24f * Hash(s, 26 + q, k), sr = 0.025f + 0.025f * Hash(s, 27 + q, k), cr = 0.1f + 0.14f * Hash(s, 28 + q, k);
                var basis = new Basis(Vector3.Right, (Hash(s, 29 + q, k) - 0.5f) * 0.4f) * new Basis(Vector3.Forward, (Hash(s, 30 + q, k) - 0.5f) * 0.4f);
                var t = new Transform3D(basis, new Vector3(x, H(c, x, zz), zz));
                c.Shrooms.AppendFrom(new CylinderMesh { TopRadius = sr, BottomRadius = sr, Height = sh, RadialSegments = 6, Rings = 1 }, 0, t * new Transform3D(Basis.Identity, new Vector3(0, sh / 2, 0)));
                c.Shrooms.AppendFrom(new SphereMesh { Radius = cr, Height = cr, IsHemisphere = true, RadialSegments = 8, Rings = 4 }, 0, t * new Transform3D(Basis.Identity, new Vector3(0, sh, 0)));
            }
            c.Root.AddChild(new OmniLight3D { Name = "FungusLight", LightColor = new Color(0.35f, 0.95f, 0.85f), LightEnergy = 2.4f, OmniRange = 3.6f, ShadowEnabled = false, Position = new Vector3(cx, H(c, cx, cz) + 0.5f, cz) });
            c.Clusters++;
            c.Tick("fungus");
        }
    }

    // 5 to 10 bones on the floor of a room, every 4th crossed by another.
    static void Bones(Ctx c, (float X, float Z, float R, string Kind) r, int s)
    {
        int n = 5 + (int)(Hash(s, 40, 0) * 6);
        for (int k = 0; k < n; k++)
        {
            float a = Hash(s, 41, k) * Mathf.Tau, d = Mathf.Sqrt(Hash(s, 42, k)) * 0.8f * r.R;
            float x = r.X + Mathf.Cos(a) * d, zz = r.Z + Mathf.Sin(a) * d;
            if (!Open(c, x, zz, 1.5f)) continue;
            float yaw = Hash(s, 43, k) * Mathf.Tau;
            Bone(c, x, zz, yaw, s, k, 0);
            if (k % 4 == 3) Bone(c, x + 0.05f, zz + 0.05f, yaw + 1.2f + 0.6f * Hash(s, 44, k), s, k, 1);
        }
    }

    // A capsule shaft lying flat (x-rotated 90 degrees, then yawed) with a knob at each end.
    static void Bone(Ctx c, float x, float zz, float yaw, int s, int k, int j)
    {
        float rad = 0.018f + 0.01f * Hash(s, 45 + j, k), len = 0.18f + 0.2f * Hash(s, 46 + j, k);
        float knob = rad * 1.35f;
        var t = new Transform3D(new Basis(Vector3.Up, yaw), new Vector3(x, H(c, x, zz) + rad + j * rad * 1.8f, zz));
        var lie = new Transform3D(new Basis(Vector3.Right, Mathf.Pi / 2), Vector3.Zero);
        c.Bones.AppendFrom(new CapsuleMesh { Radius = rad, Height = len, RadialSegments = 8, Rings = 2 }, 0, t * lie);
        foreach (int e in new[] { -1, 1 })
            c.Bones.AppendFrom(new SphereMesh { Radius = knob, Height = knob * 2, RadialSegments = 8, Rings = 4 }, 0, t * new Transform3D(Basis.Identity, new Vector3(0, 0, e * (len / 2 - rad * 0.3f))));
        c.BoneCount++;
        c.Tick("bones");
    }

    static void Flush(Ctx c, SurfaceTool st, string name, Material mat)
    {
        c.Root.AddChild(new MeshInstance3D { Name = name, Mesh = st.Commit(), MaterialOverride = mat, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off });
    }

    /// <summary>The pine bark (as Camp.Bark), a little greyed: the tree has been dead a while.</summary>
    static StandardMaterial3D Bark()
    {
        const string dir = "res://art/materials/pine_bark";
        var arm = GD.Load<Texture2D>($"{dir}/arm.jpg");
        return new StandardMaterial3D
        {
            AlbedoTexture = GD.Load<Texture2D>($"{dir}/albedo.jpg"), AlbedoColor = new Color(0.86f, 0.82f, 0.78f),
            NormalEnabled = true, NormalTexture = GD.Load<Texture2D>($"{dir}/normal.jpg"), NormalScale = 1.3f,
            Roughness = 1, RoughnessTexture = arm, RoughnessTextureChannel = BaseMaterial3D.TextureChannel.Green,
            AOEnabled = true, AOTexture = arm, AOTextureChannel = BaseMaterial3D.TextureChannel.Red,
        };
    }

    static float Hash(int a, int b, int c)
    {
        unchecked
        {
            uint h = (uint)(a * 374761393 + b * 668265263 + c * 1274126177);
            h = (h ^ (h >> 13)) * 1274126177u;
            h ^= h >> 16;
            return (h & 0xFFFFFF) / (float)0x1000000;
        }
    }
}
