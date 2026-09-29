using System;
using System.Collections.Generic;
using Godot;
using static SurvivorUnchained.View.Made;
using static SurvivorUnchained.View.Shapes;

namespace SurvivorUnchained.View;

/// <summary>
/// The KayKit props the web game still stands in its zones, replaced where
/// they stand. The exporter names each one (kk-PACK-NAME-N in landmarks.glb)
/// and records its size as authored (data/zones/kaykit.json); here it is
/// swapped for a piece of the world's own kits where one fits (a torch, a
/// crate, a dead tree, candles), and otherwise made in code to the KayKit
/// piece's size, in photographed stone, wood, iron and earth
/// (Made.Surface): headstones and graves, a crypt, ruined walls, pillars
/// and rubble, iron fences, the Watch's lamp posts, bones.
/// </summary>
public static class Pieces
{
    static Dictionary<string, float[]>? sizes;

    static Dictionary<string, float[]> Sizes =>
        sizes ??= Core.Json.Parse<Dictionary<string, float[]>>(FileAccess.GetFileAsString("res://data/zones/kaykit.json"));

    /// <summary>What stands in for a KayKit piece, in its frame, or null to
    /// keep it. The seed (which of its kind it is) varies the made ones; the
    /// scale it is placed at keeps what has a size in life that size; the
    /// ground (its height under a point, both in the piece's frame) keeps
    /// what is spread over it on it, and out of the water.</summary>
    public static Node3D? For(string pack, string name, int seed = 0, float scale = 1, Func<Vector3, float>? ground = null)
    {
        if (!Sizes.TryGetValue($"{pack}/{name}", out var s)) return null;
        var box = new Aabb(new Vector3(s[0], s[1], s[2]), new Vector3(s[3] - s[0], s[4] - s[1], s[5] - s[2]));
        Node3D? made = (pack, name) switch
        {
            ("halloween", "gravestone") => Stone(box, seed % 2 == 0 ? Head.Round : Head.Shoulders, seed),
            ("halloween", "gravemarker_A") => Marker(box, false, seed),
            ("halloween", "gravemarker_B") => Marker(box, true, seed),
            ("halloween", "grave_A") => Grave(box, Head.Round, seed),
            ("halloween", "grave_B") => Grave(box, Head.Gothic, seed),
            ("halloween", "grave_A_destroyed") => Grave(box, Head.Broken, seed),
            ("halloween", "crypt") => Crypt(box),
            ("halloween", "fence") => Fence(box, false, seed),
            ("halloween", "fence_broken") => Fence(box, true, seed),
            ("halloween", "post_lantern") => LampPost(box, true),
            ("halloween", "post") => LampPost(box, false),
            ("halloween", "shrine") => Shrine(box),
            ("halloween", "lantern_standing") => Fitted(Lantern(false), box),
            ("halloween", "pillar") or ("dungeon", "pillar") => Pillar(box, seed),
            ("halloween", "tree_dead_large") => Kit($"nature/DeadTree_{1 + seed % 3}", box),
            ("halloween", "candle_triple") => Kit("props/CandleStick_Triple", box),
            ("halloween", "skull") => Fitted(Skull(), box),
            ("halloween", "skull_candle") => SkullCandle(box),
            ("halloween", "ribcage") => Fitted(Ribcage(), box),
            ("halloween", "bone_A") or ("halloween", "bone_B") or ("halloween", "bone_C") => Fitted(LongBone(seed), box),
            ("dungeon", "wall_broken") => Wall(box, 0.45f, seed),
            ("dungeon", "wall_half") => Wall(box, 0.9f, seed),
            ("dungeon", "wall_cracked") => Wall(box, 1f, seed),
            ("dungeon", "rubble_half") or ("dungeon", "rubble_large") => Rubble(box, seed),
            ("dungeon", "torch_mounted") or ("dungeon", "torch_lit") => Kit("props/Torch_Metal", box),
            ("dungeon", "banner_thin_red") => Kit("props/Banner_1", box),
            ("dungeon", "box_small") => Kit("props/Crate_Wooden", box),
            ("dungeon", "box_small_decorated") => Kit("props/Crate_Metal", box),
            ("dungeon", "barrel_small") => Kit("props/Barrel", box),
            ("dungeon", "table_small_decorated_A") => Table(box),
            ("hex_nature", "rock_single_B") => Kit("nature/Rock_Medium_2", box),
            ("hex_nature", "tent") => Tent(box),
            ("hex_nature", "target") => Target(box),
            ("hex_nature", "flag_red") => Flag(box),
            ("hex_nature", "wheelbarrow") => Wheelbarrow(box),
            ("hex_nature", "bucket_arrows") => ArrowBucket(box),
            ("hex_buildings", "wall_straight") => CurtainWall(box, false),
            ("hex_buildings", "wall_straight_gate") => CurtainWall(box, true),
            ("hex_buildings", "building_tower_base_blue") => Tower(box),
            ("hex_buildings", "building_windmill_blue") => Windmill(box),
            ("hex_buildings", "building_watermill_blue") => Watermill(box),
            ("hex_buildings", "building_grain") => Stooks(box, scale, ground),
            ("hex_buildings", "building_mine_blue") => Mine(box),
            ("hex_buildings", "building_scaffolding") => Scaffold(box),
            _ => null,
        };
        if (made != null) made.Name = $"{pack}_{name}";
        return made;
    }

    /* ------------------------------------------------------------ fitting -- */

    /// <summary>The bounds of everything drawn under a node, in its frame.</summary>
    public static Aabb? Bounds(Node n, Transform3D at, Aabb? box = null)
    {
        if (n is MeshInstance3D { Mesh: not null } mi)
        {
            var b = at * mi.GetAabb();
            box = box is Aabb a ? a.Merge(b) : b;
        }
        foreach (var c in n.GetChildren()) box = Bounds(c, c is Node3D c3 ? at * c3.Transform : at, box);
        return box;
    }

    /// <summary>A piece scaled (evenly) to the KayKit piece's height, stood
    /// on its base, over the middle of its footprint.</summary>
    static Node3D Fitted(Node3D piece, Aabb box)
    {
        if (Bounds(piece, Transform3D.Identity) is not Aabb b || b.Size.Y < 1e-4f) return piece;
        float k = box.Size.Y / b.Size.Y;
        var holder = new Node3D();
        piece.Scale = Vector3.One * k;
        var mid = b.GetCenter();
        piece.Position = new Vector3(box.GetCenter().X - mid.X * k, box.Position.Y - b.Position.Y * k, box.GetCenter().Z - mid.Z * k);
        holder.AddChild(piece);
        return holder;
    }

    static Node3D? Kit(string id, Aabb box) => Dressing.Piece(id) is Node3D p ? Fitted(p, box) : null;

    static Node3D Hold(params (Mesh Mesh, Material Mat)[] parts)
    {
        var root = new Node3D();
        foreach (var (mesh, mat) in parts) Add(root, mesh, mat);
        return root;
    }

    static float Hash(int seed, int salt) => Mathf.PosMod(Mathf.Sin(seed * 12.9898f + salt * 78.233f) * 43758.547f, 1f);

    /* --------------------------------------------------------- materials -- */

    static StandardMaterial3D Headstone() => Surface("rock_boulder_dry", 0.9f, "#7a7a74");
    static StandardMaterial3D Blocks() => Surface("medieval_blocks_03", 2.2f, "#94908a");
    static StandardMaterial3D OldBone() => Mat("#a89c80", 0, 0.7f);
    static StandardMaterial3D Slates() => Surface("castle_wall_slates", 1.6f, "#9a9690");
    static StandardMaterial3D Timber() => Surface("rough_wood", 1.4f);
    static StandardMaterial3D Earth() => Surface("forest_ground_04", 1.6f, "#8a8074");
    static StandardMaterial3D Wrought() => Mat("#262422", 0.8f, 0.5f);

    /* ------------------------------------------------------- the graveyard -- */

    enum Head { Round, Shoulders, Gothic, Cross, Broken }

    /// <summary>A headstone's face, w wide and h tall (from y 0), as an outline.</summary>
    static Vector2[] Outline(Head head, float w, float h, int seed)
    {
        float hw = w / 2;
        var p = new List<Vector2> { new(-hw, -0.12f * h), new(hw, -0.12f * h) };
        switch (head)
        {
            case Head.Round:
                p.Add(new(hw, h - hw));
                for (int i = 1; i < 12; i++) { float a = Mathf.Pi * i / 12; p.Add(new(hw * Mathf.Cos(a), h - hw + hw * Mathf.Sin(a))); }
                p.Add(new(-hw, h - hw));
                break;
            case Head.Shoulders:
                float sh = h * 0.78f, r = hw * 0.55f;
                p.Add(new(hw, sh));
                for (int i = 1; i < 6; i++) { float a = Mathf.Pi / 2 * i / 6; p.Add(new(hw - r * 0.5f + r * 0.5f * Mathf.Cos(a), sh + r * 0.5f * Mathf.Sin(a))); }
                for (int i = 0; i <= 10; i++) { float a = Mathf.Pi * i / 10; p.Add(new(r * Mathf.Cos(a), h - r + r * Mathf.Sin(a))); }
                for (int i = 1; i < 6; i++) { float a = Mathf.Pi / 2 + Mathf.Pi / 2 * i / 6; p.Add(new(-hw + r * 0.5f + r * 0.5f * Mathf.Cos(a), sh + r * 0.5f * Mathf.Sin(a))); }
                p.Add(new(-hw, sh));
                break;
            case Head.Gothic:
                float spring = h - hw * 1.4f;
                p.Add(new(hw, spring));
                for (int i = 1; i < 8; i++) { float t = i / 8f; p.Add(new(hw * (1 - t * t), spring + (h - spring) * Mathf.Sin(t * Mathf.Pi / 2))); }
                p.Add(new(0, h));
                for (int i = 7; i >= 1; i--) { float t = i / 8f; p.Add(new(-hw * (1 - t * t), spring + (h - spring) * Mathf.Sin(t * Mathf.Pi / 2))); }
                p.Add(new(-hw, spring));
                break;
            case Head.Cross:
                float bw = w * 0.2f, arm = h * 0.68f, ah = w * 0.2f;
                p.Clear();
                p.AddRange(new Vector2[] { new(-bw, -0.12f * h), new(bw, -0.12f * h), new(bw, arm - ah), new(hw, arm - ah), new(hw, arm + ah), new(bw, arm + ah), new(bw, h), new(-bw, h), new(-bw, arm + ah), new(-hw, arm + ah), new(-hw, arm - ah), new(-bw, arm - ah) });
                break;
            case Head.Broken:
                float top = h * 0.55f;
                p.Add(new(hw, top * 0.8f));
                for (int i = 1; i < 7; i++) { float x = hw - w * i / 7; p.Add(new(x, top + (Hash(seed, i) - 0.3f) * h * 0.18f)); }
                p.Add(new(-hw, top * 1.05f));
                break;
        }
        return p.ToArray();
    }

    /// <summary>A headstone, as tall and wide as the KayKit one, weathered stone, set a little into the ground.</summary>
    static Build HeadstoneBuild(Head head, float w, float h, float t, int seed)
    {
        var b = new Build();
        Extrude(b, Outline(head, w, h, seed), t, Mathf.Min(0.03f * h, t * 0.3f));
        // A cross in relief on the face of the plainer ones.
        if (head is Head.Round or Head.Shoulders)
        {
            float cx = w * 0.07f, cy = h * 0.2f, mid = h * 0.62f;
            Extrude(b, Pts(-cx * 0.35f, mid - cy, cx * 0.35f, mid - cy, cx * 0.35f, mid + cy * 0.35f, cx, mid + cy * 0.35f, cx, mid + cy * 0.65f, cx * 0.35f, mid + cy * 0.65f,
                cx * 0.35f, mid + cy, -cx * 0.35f, mid + cy, -cx * 0.35f, mid + cy * 0.65f, -cx, mid + cy * 0.65f, -cx, mid + cy * 0.35f, -cx * 0.35f, mid + cy * 0.35f), 0.03f, 0.006f,
                At(0, 0, t / 2));
        }
        return b;
    }

    static Node3D Stone(Aabb box, Head head, int seed)
    {
        var c = box.GetCenter();
        float t = Mathf.Clamp(box.Size.Z, 0.06f, box.Size.Y * 0.2f);
        var b = HeadstoneBuild(head, box.Size.X * 0.92f, box.Size.Y, t, seed);
        var root = new Node3D();
        Add(root, b.Mesh(true), Headstone(), At(c.X, box.Position.Y, c.Z));
        return root;
    }

    /// <summary>A grave: its headstone on a stone plinth, the earth over
    /// it heaped in front, settling.</summary>
    static Node3D Grave(Aabb box, Head head, int seed)
    {
        var root = new Node3D();
        var c = box.GetCenter();
        float w = box.Size.X, d = box.Size.Z, y0 = box.Position.Y, plinth = box.Size.Y * 0.1f;
        var slab = new Build();
        Extrude(slab, Pts(-w / 2, 0, w / 2, 0, w / 2, plinth, -w / 2, plinth), d, plinth * 0.25f, At(c.X, y0 - plinth * 0.3f, c.Z));
        Add(root, slab.Mesh(true), Headstone());
        float st = Mathf.Min(d * 0.3f, 0.25f);
        var stone = HeadstoneBuild(head, w * 0.62f, box.Size.Y - plinth * 0.7f, st, seed);
        Add(root, stone.Mesh(true), Headstone(), At(c.X, y0 + plinth * 0.7f, box.Position.Z + d * 0.35f));
        var mound = new Build();
        float len = d * 1.6f, mh = box.Size.Y * 0.12f;
        Lathe(mound, Pts(0.5f, -0.1f, 0.48f, 0.3f, 0.38f, 0.65f, 0.22f, 0.9f, 0, 1), 28,
            warp: p => new Vector3(p.X * w * 0.55f, p.Y * mh + (Noise(p.X * 9 + seed, p.Z * 9) - 0.5f) * mh * 0.3f, p.Z * len));
        Add(root, mound.Mesh(true), Earth(), At(c.X, y0, box.End.Z + len * 0.42f));
        return root;
    }

    /// <summary>A wooden cross over a grave, leaning as the ground settles;
    /// the other kind lashed with rope where its arms cross.</summary>
    static Node3D Marker(Aabb box, bool lashed, int seed)
    {
        var root = new Node3D();
        var c = box.GetCenter();
        float h = box.Size.Y, w = box.Size.X, t = 0.09f * h;
        var wood = new Build();
        Extrude(wood, Pts(-t / 2, -0.15f * h, t / 2, -0.15f * h, t / 2, h, -t / 2, h), t * 0.8f, t * 0.12f);
        Extrude(wood, Pts(-w / 2, 0.66f * h - t / 2, w / 2, 0.66f * h - t / 2, w / 2, 0.66f * h + t / 2, -w / 2, 0.66f * h + t / 2), t * 0.7f, t * 0.12f, At(0, 0, t * 0.75f));
        var lean = new Basis(Vector3.Back, (Hash(seed, 5) - 0.5f) * 0.2f) * new Basis(Vector3.Right, (Hash(seed, 6) - 0.5f) * 0.15f);
        Add(root, wood.Mesh(true), Timber(), new Transform3D(lean, new Vector3(c.X, box.Position.Y, c.Z)));
        if (lashed)
        {
            var rope = new Build();
            for (int k = 0; k < 3; k++)
                Tube(rope, Circle(new Vector3(0, 0.66f * h + (k - 1) * t * 0.35f, t * 0.4f), t * 0.75f, Vector3.Right, Vector3.Back, 12), t * 0.08f, 4, true);
            Add(root, rope.Mesh(), Mat("#7a6a4a", 0, 0.95f), new Transform3D(lean, new Vector3(c.X, box.Position.Y, c.Z)));
        }
        return root;
    }

    /// <summary>A wayside shrine of stone: a plinth, a niche with a candle
    /// burning in it, a little pitched roof.</summary>
    static Node3D Shrine(Aabb box)
    {
        var root = new Node3D();
        var c = box.GetCenter();
        float w = box.Size.X, d = box.Size.Z, h = box.Size.Y, y0 = box.Position.Y;
        var stone = new Build();
        Extrude(stone, Pts(-w / 2, 0, w / 2, 0, w / 2, h * 0.12f, -w / 2, h * 0.12f), d, 0.02f * h, At(c.X, y0, c.Z));
        float bw = w * 0.78f, bd = d * 0.78f, top = h * 0.72f;
        // The body, with the niche cut into its face.
        Extrude(stone, Pts(-bw / 2, h * 0.12f, bw / 2, h * 0.12f, bw / 2, top, -bw / 2, top), bd * 0.5f, 0.01f * h, At(c.X, y0, c.Z - bd * 0.25f));
        foreach (float sx in new[] { -1f, 1f })
            Extrude(stone, Pts(-bw * 0.13f, h * 0.12f, bw * 0.13f, h * 0.12f, bw * 0.13f, top, -bw * 0.13f, top), bd * 0.5f, 0.01f * h, At(c.X + sx * bw * 0.37f, y0, c.Z + bd * 0.25f));
        Extrude(stone, Pts(-bw / 2, h * 0.12f, bw / 2, h * 0.12f, bw / 2, h * 0.3f, -bw / 2, h * 0.3f), bd * 0.5f, 0.01f * h, At(c.X, y0, c.Z + bd * 0.25f));
        Extrude(stone, Pts(-bw / 2, top - h * 0.1f, bw / 2, top - h * 0.1f, bw / 2, top, -bw / 2, top), bd * 0.5f, 0.01f * h, At(c.X, y0, c.Z + bd * 0.25f));
        Extrude(stone, Pts(-w * 0.5f, top, w * 0.5f, top, 0, h), d * 0.95f, 0.012f * h, At(c.X, y0, c.Z));
        Add(root, stone.Mesh(true), Blocks());
        var wax = new Build();
        Lathe(wax, Pts(0, 0, 0.05f * w, 0, 0.05f * w, 0.14f * h, 0, 0.14f * h), 10, At(c.X, y0 + h * 0.3f, c.Z + bd * 0.2f));
        Add(root, wax.Mesh(), Mat("#e8dcc0", 0, 0.6f));
        var flame = new Build();
        Lathe(flame, Pts(0, 0, 0.03f * w, 0.02f * h, 0.02f * w, 0.05f * h, 0, 0.08f * h), 10, At(c.X, y0 + h * 0.44f, c.Z + bd * 0.2f));
        Add(root, flame.Mesh(), Glow("#ffb050", 4));
        return root;
    }

    /// <summary>A crypt: a plinth, walls of dressed stone, a pitched roof, an iron door, a cross at the gable.</summary>
    static Node3D Crypt(Aabb box)
    {
        var root = new Node3D();
        var c = box.GetCenter();
        float w = box.Size.X, d = box.Size.Z, h = box.Size.Y, y0 = box.Position.Y;
        float plinth = h * 0.08f, wallH = h * 0.5f, roofH = h * 0.3f;
        var stone = new Build();
        Extrude(stone, Pts(-w / 2, 0, w / 2, 0, w / 2, plinth, -w / 2, plinth), d, 0.02f * h, At(c.X, y0, c.Z));
        float iw = w * 0.86f, id = d * 0.86f;
        Extrude(stone, Pts(-iw / 2, plinth, iw / 2, plinth, iw / 2, plinth + wallH, -iw / 2, plinth + wallH), id, 0.01f * h, At(c.X, y0, c.Z));
        // A cornice, and the gable's triangle over the door and at the back.
        Extrude(stone, Pts(-iw / 2 - 0.04f * w, plinth + wallH, iw / 2 + 0.04f * w, plinth + wallH, iw / 2 + 0.04f * w, plinth + wallH + 0.05f * h, -iw / 2 - 0.04f * w, plinth + wallH + 0.05f * h), id + 0.08f * d, 0.01f * h, At(c.X, y0, c.Z));
        float eave = plinth + wallH + 0.05f * h;
        Extrude(stone, Pts(-iw / 2, eave, iw / 2, eave, 0, eave + roofH), id, 0.01f * h, At(c.X, y0, c.Z));
        Add(root, stone.Mesh(true), Blocks());
        // The roof: two slabs of slate over the gable.
        var roof = new Build();
        float slope = Mathf.Sqrt(iw * iw / 4 + roofH * roofH), ang = Mathf.Atan2(roofH, iw / 2);
        foreach (float sx in new[] { -1f, 1f })
            Extrude(roof, Pts(0, -0.03f * h, slope + 0.08f * w, -0.03f * h, slope + 0.08f * w, 0.03f * h, 0, 0.03f * h), id + 0.14f * d, 0.008f * h,
                new Transform3D(new Basis(Vector3.Back, sx > 0 ? -ang : Mathf.Pi + ang), new Vector3(c.X, y0 + eave + roofH + 0.03f * h, c.Z)));
        Add(root, roof.Mesh(true), Slates());
        // The door: dark within, iron-bound, under a lintel.
        float dw = iw * 0.36f, dh = wallH * 0.8f, front = c.Z + id / 2;
        Add(root, new BoxMesh { Size = new Vector3(dw, dh, 0.05f * d) }, Wrought(), At(c.X, y0 + plinth + dh / 2, front + 0.005f));
        var bands = new Build();
        foreach (float yy in new[] { 0.25f, 0.75f })
            Extrude(bands, Pts(-dw / 2, -0.02f * h, dw / 2, -0.02f * h, dw / 2, 0.02f * h, -dw / 2, 0.02f * h), 0.02f * d, 0.004f, At(c.X, y0 + plinth + dh * yy, front + 0.03f * d));
        Add(root, bands.Mesh(), Mat("#4a4038", 0.9f, 0.4f));
        var lintel = new Build();
        Extrude(lintel, Pts(-dw / 2 - 0.05f * w, 0, dw / 2 + 0.05f * w, 0, dw / 2 + 0.05f * w, 0.07f * h, -dw / 2 - 0.05f * w, 0.07f * h), 0.06f * d, 0.01f * h, At(c.X, y0 + plinth + dh, front));
        // Columns either side of the door, and steps up to it.
        var cols = new Build();
        float cr = w * 0.05f;
        foreach (float sx in new[] { -1f, 1f })
            Lathe(cols, Pts(0, 0, cr * 1.4f, 0, cr * 1.4f, cr * 0.8f, cr, cr * 1.2f, cr * 0.85f, wallH * 0.95f, cr * 1.3f, wallH, cr * 1.3f, wallH + cr, 0, wallH + cr), 12,
                At(c.X + sx * (dw / 2 + cr * 2.8f), y0 + plinth, front + cr * 1.6f));
        for (int k = 0; k < 2; k++)
            Extrude(cols, Pts(-dw * 0.9f + k * dw * 0.1f, 0, dw * 0.9f - k * dw * 0.1f, 0, dw * 0.9f - k * dw * 0.1f, plinth * 0.5f, -dw * 0.9f + k * dw * 0.1f, plinth * 0.5f),
                d * 0.12f - k * d * 0.05f, 0.005f * h, At(c.X, y0 + k * plinth * 0.5f, box.End.Z - d * 0.04f + k * d * 0.02f));
        Add(root, cols.Mesh(true), Blocks());
        // A cross on the ridge at the front.
        float cs = h * 0.12f;
        Extrude(lintel, Outline(Head.Cross, cs, cs * 1.4f, 0), 0.04f * d, 0.004f * h, At(c.X, y0 + eave + roofH + 0.02f * h, front - 0.02f * d));
        Add(root, lintel.Mesh(true), Headstone());
        return root;
    }

    /// <summary>A length of wrought-iron fence: square posts with ball caps
    /// at the ends, two rails, bars with spear points; broken, bars gone and
    /// bent and a rail sagging.</summary>
    static Node3D Fence(Aabb box, bool broken, int seed)
    {
        bool alongX = box.Size.X >= box.Size.Z;
        float len = alongX ? box.Size.X : box.Size.Z, h = box.Size.Y;
        var c = box.GetCenter();
        var turn = alongX ? Basis.Identity : new Basis(Vector3.Up, Mathf.Pi / 2);
        var iron = new Build();
        float post = h * 0.05f;
        var stone = new Build();
        post = h * 0.1f;
        foreach (float s in new[] { -1f, 1f })
            Lathe(stone, Pts(0, 0, post * 1.41f, 0, post * 1.41f, 0, post * 1.41f, h * 0.06f, post * 1.41f, h * 0.06f, post * 1.2f, h * 0.08f, post * 1.2f, h * 0.08f,
                post * 1.2f, h * 0.9f, post * 1.2f, h * 0.9f, post * 1.5f, h * 0.93f, post * 1.5f, h * 0.93f, post * 1.3f, h, post * 1.3f, h, 0, h * 1.02f), 4,
                At(new Basis(Vector3.Up, Mathf.Pi / 4), s * (len / 2 - post), 0, 0));
        float sag = broken ? h * 0.12f : 0;
        foreach (float y in new[] { h * 0.18f, h * 0.72f })
            Tube(iron, Path(8, t => new Vector3(Mathf.Lerp(-len / 2 + post, len / 2 - post, t), y - sag * Mathf.Sin(t * Mathf.Pi) * (y > h * 0.5f ? 1 : 0.3f), 0)), h * 0.012f, 5);
        int bars = Math.Max(3, (int)(len / (h * 0.14f)));
        for (int i = 1; i < bars; i++)
        {
            if (broken && Hash(seed, i) < 0.3f) continue;
            float x = -len / 2 + len * i / bars;
            float lean = broken && Hash(seed, i + 40) < 0.35f ? (Hash(seed, i + 80) - 0.5f) * 0.5f : 0;
            var top = new Vector3(x + lean * h * 0.9f, h * 0.9f, lean * h * 0.3f);
            Tube(iron, new List<Vector3> { new(x, 0, 0), new(x + lean * h * 0.45f, h * 0.5f, lean * h * 0.1f), top }, h * 0.01f, 5);
            Lathe(iron, Pts(0, 0, h * 0.022f, h * 0.02f, 0, h * 0.09f), 4, new Transform3D(new Basis(Vector3.Back, -lean) , top));
        }
        var root = new Node3D();
        Add(root, iron.Mesh(), Wrought(), new Transform3D(turn, new Vector3(c.X, box.Position.Y, c.Z)));
        Add(root, stone.Faceted().Mesh(true), Blocks(), new Transform3D(turn, new Vector3(c.X, box.Position.Y, c.Z)));
        return root;
    }

    /// <summary>The Watch's lamp post: a timber post, an arm reaching out
    /// (along +Z) braced from below, an iron lantern hanging from it where
    /// the web game hangs its flame (2.72 up, 1.12 out; lit by the zone's
    /// own light); or the same post, its lantern gone.</summary>
    static Node3D LampPost(Aabb box, bool lit)
    {
        var root = new Node3D();
        const float Top = 2.72f, Out = 1.12f;
        var wood = new Build();
        float p = 0.075f;
        Extrude(wood, Pts(-p, 0, p, 0, p, box.End.Y, -p, box.End.Y), p * 2, 0.012f);
        Extrude(wood, Pts(-0.05f, -0.06f, Out + 0.12f, -0.06f, Out + 0.12f, 0.06f, -0.05f, 0.06f), 0.1f, 0.01f, At(new Basis(Vector3.Up, -Mathf.Pi / 2), 0, Top, 0));
        Extrude(wood, Pts(0, -0.035f, 0.75f, -0.035f, 0.75f, 0.035f, 0, 0.035f), 0.07f, 0.008f, new Transform3D(new Basis(Vector3.Up, -Mathf.Pi / 2) * new Basis(Vector3.Back, 0.75f), new Vector3(0, Top - 0.55f, p)));
        Add(root, wood.Mesh(true), Timber());
        var iron = new Build();
        Chain(iron, new Vector3(0, Top - 0.06f, Out), new Vector3(0, Top - 0.3f, Out), 0.025f, 0.006f);
        Add(root, iron.Mesh(), Wrought());
        // A post whose lantern is gone keeps its hook.
        if (!lit) return root;
        var lantern = Lantern(false);
        lantern.Transform = new Transform3D(Basis.Identity.Scaled(Vector3.One * 0.32f), new Vector3(0, Top - 0.55f, Out));
        root.AddChild(lantern);
        return root;
    }

    /// <summary>A square pillar of dressed stone: a plinth, the shaft, a capital.</summary>
    static Node3D Pillar(Aabb box, int seed)
    {
        var c = box.GetCenter();
        float r = Mathf.Min(box.Size.X, box.Size.Z) / 2 * 1.41f, h = box.Size.Y;
        var b = new Build();
        Lathe(b, Pts(0, 0, r, 0, r, 0, r, h * 0.08f, r, h * 0.08f, r * 0.82f, h * 0.1f, r * 0.82f, h * 0.1f, r * 0.78f, h * 0.86f, r * 0.78f, h * 0.86f,
            r * 0.95f, h * 0.9f, r * 0.95f, h * 0.9f, r * 0.95f, h, r * 0.95f, h, 0, h), 4, At(new Basis(Vector3.Up, Mathf.Pi / 4 + (Hash(seed, 1) - 0.5f) * 0.1f), c.X, box.Position.Y, c.Z));
        return Hold((b.Faceted().Mesh(true), Blocks()));
    }

    /// <summary>A length of ruined wall in dressed stone: whole to its full
    /// height, or broken down to a ragged top at some fraction of it, course
    /// by course.</summary>
    static Node3D Wall(Aabb box, float keep, int seed)
    {
        bool alongX = box.Size.X >= box.Size.Z;
        float len = alongX ? box.Size.X : box.Size.Z, thick = alongX ? box.Size.Z : box.Size.X, h = box.Size.Y;
        var c = box.GetCenter();
        var b = new Build();
        if (keep >= 1) Extrude(b, Pts(-len / 2, -0.1f, len / 2, -0.1f, len / 2, h, -len / 2, h), thick, 0.02f * h);
        else
        {
            // Stretches of wall standing to different heights, as blocks fell.
            const int Steps = 9;
            float course = h / 6;
            for (int i = 0; i < Steps; i++)
            {
                float x0 = -len / 2 + len * i / Steps, x1 = x0 + len / Steps;
                float top = h * (keep + (1 - keep) * Mathf.Pow(Mathf.Abs(Mathf.Sin((i + seed) * 0.9f)), 2) * 0.8f) - Hash(seed, i) * h * 0.12f;
                top = Mathf.Max(course, Mathf.Round(top / course) * course - (i % 2) * course * 0.3f);
                Extrude(b, Pts(x0, -0.1f, x1, -0.1f, x1, top, x0, top), thick * (0.96f + Hash(seed, i + 30) * 0.04f), 0.015f * h);
            }
        }
        var turn = alongX ? Basis.Identity : new Basis(Vector3.Up, Mathf.Pi / 2);
        var root = new Node3D();
        Add(root, b.Mesh(true), Blocks(), new Transform3D(turn, new Vector3(c.X, box.Position.Y, c.Z)));
        return root;
    }

    /// <summary>Fallen blocks of dressed stone, heaped low.</summary>
    static Node3D Rubble(Aabb box, int seed)
    {
        var c = box.GetCenter();
        var b = new Build();
        int n = 9;
        float bw = Mathf.Max(box.Size.X, box.Size.Z) * 0.28f;
        for (int i = 0; i < n; i++)
        {
            float bx = (Hash(seed, i) - 0.5f) * box.Size.X * 0.8f, bz = (Hash(seed, i + 20) - 0.5f) * box.Size.Z * 0.8f;
            float s = bw * (0.5f + Hash(seed, i + 40) * 0.6f), y = i > 5 ? box.Size.Y * 0.35f : 0;
            var turn = new Basis(Vector3.Up, Hash(seed, i + 60) * Mathf.Tau) * new Basis(Vector3.Back, (Hash(seed, i + 80) - 0.5f) * 0.6f);
            Extrude(b, Pts(-s / 2, 0, s / 2, 0, s / 2, s * 0.55f, -s / 2, s * 0.55f), s * 0.7f, s * 0.08f, new Transform3D(turn, new Vector3(c.X + bx, box.Position.Y + y - s * 0.1f, c.Z + bz)));
        }
        return Hold((b.Mesh(true), Blocks()));
    }

    /* -------------------------------------------------------------- bones -- */

    /// <summary>A long bone: the shaft, a knuckle at each end, lying along X.</summary>
    static Node3D LongBone(int seed)
    {
        var b = new Build();
        float len = 0.8f + Hash(seed, 3) * 0.3f;
        Lathe(b, Pts(0, 0, 0.07f, 0.01f, 0.1f, 0.05f, 0.09f, 0.11f, 0.05f, 0.18f, 0.042f, len / 2, 0.05f, len - 0.18f, 0.09f, len - 0.11f, 0.1f, len - 0.05f, 0.07f, len - 0.01f, 0, len), 12,
            new Transform3D(new Basis(Vector3.Back, -Mathf.Pi / 2), new Vector3(-len / 2, 0.08f, 0)), p => p + new Vector3(0, 0, Mathf.Sin(p.X * 4) * 0.01f));
        return Hold((b.Mesh(), OldBone()));
    }

    /// <summary>A ribcage lying on its back: the spine, the ribs curving up and over.</summary>
    static Node3D Ribcage()
    {
        var b = new Build();
        Tube(b, Path(12, t => new Vector3(Mathf.Lerp(-0.45f, 0.45f, t), 0.05f + Mathf.Sin(t * Mathf.Pi) * 0.03f, 0)), t => 0.035f + 0.01f * Mathf.Sin(t * 60), 6);
        for (int i = 0; i < 7; i++)
        {
            float x = -0.36f + i * 0.11f, r = 0.2f + 0.08f * Mathf.Sin(i / 6f * Mathf.Pi);
            foreach (float s in new[] { -1f, 1f })
                Tube(b, Path(10, t => new Vector3(x + t * 0.04f, 0.05f + Mathf.Sin(t * Mathf.Pi * 0.85f) * r * 0.9f, s * (0.03f + Mathf.Sin(t * Mathf.Pi * 0.5f) * r))), t => 0.018f * (1 - 0.4f * t), 5);
        }
        return Hold((b.Mesh(), OldBone()));
    }

    /// <summary>A skull: the cranium long front to back, the brow over
    /// deep sockets, the cheekbones, a row of teeth, the jaw hung open a little.</summary>
    static Node3D Skull()
    {
        var root = new Node3D();
        var b = new Build();
        Lathe(b, Pts(0.07f, -0.06f, 0.12f, -0.03f, 0.15f, 0.04f, 0.145f, 0.12f, 0.1f, 0.19f, 0, 0.21f), 20,
            warp: p => new Vector3(p.X * 0.82f, p.Y, p.Z * 1.12f - (p.Z > 0 ? 0 : p.Z * 0.1f)));
        // The face: a narrower block forward and down, the cheekbones either side.
        Lathe(b, Pts(0.04f, -0.13f, 0.075f, -0.11f, 0.085f, -0.05f, 0.08f, 0.02f, 0.05f, 0.05f), 14, At(0, 0, 0.07f), p => new Vector3(p.X * 1.15f, p.Y, p.Z * 0.85f));
        foreach (float sx in new[] { -1f, 1f })
            Tube(b, new List<Vector3> { new(sx * 0.07f, -0.02f, 0.13f), new(sx * 0.11f, -0.03f, 0.08f), new(sx * 0.12f, -0.02f, 0.02f) }, 0.018f, 5);
        // The jaw.
        Tube(b, Path(9, t => new Vector3(Mathf.Lerp(-0.09f, 0.09f, t), -0.16f - Mathf.Sin(t * Mathf.Pi) * 0.02f, 0.02f + Mathf.Sin(t * Mathf.Pi) * 0.11f)), 0.016f, 5);
        foreach (float sx in new[] { -1f, 1f })
            Tube(b, new List<Vector3> { new(sx * 0.09f, -0.16f, 0.02f), new(sx * 0.1f, -0.08f, -0.01f) }, 0.016f, 5);
        Add(root, b.Mesh(), OldBone());
        var dark = new Build();
        foreach (float x in new[] { -0.05f, 0.05f }) Lathe(dark, Pts(0.034f, 0, 0.03f, 0.018f, 0, 0.024f), 10, At(Made.Facing, x, 0.02f, 0.155f));
        Lathe(dark, Pts(0.017f, 0, 0.012f, 0.015f, 0, 0.02f), 3, At(Made.Facing, 0, -0.04f, 0.16f));
        Add(root, dark.Mesh(), Mat("#14100c", 0, 0.9f));
        var teeth = new Build();
        for (int i = 0; i < 8; i++)
        {
            float a = (i - 3.5f) * 0.16f;
            Extrude(teeth, Pts(-0.008f, -0.02f, 0.008f, -0.02f, 0.007f, 0.012f, -0.007f, 0.012f), 0.012f, 0.002f, At(new Basis(Vector3.Up, a), Mathf.Sin(a) * 0.075f, -0.11f, 0.07f + Mathf.Cos(a) * 0.075f));
        }
        Add(root, teeth.Mesh(), Mat("#c8bc9c", 0, 0.5f));
        root.Position = new Vector3(0, 0.18f, 0);
        var holder = new Node3D();
        holder.AddChild(root);
        return holder;
    }

    /// <summary>A skull with a candle burnt down on its crown, wax run over it.</summary>
    static Node3D SkullCandle(Aabb box)
    {
        var holder = new Node3D();
        var skull = Skull();
        holder.AddChild(skull);
        var wax = new Build();
        Lathe(wax, Pts(0, 0.36f, 0.035f, 0.36f, 0.035f, 0.47f, 0, 0.47f), 12);
        Lathe(wax, Pts(0.07f, 0.34f, 0.05f, 0.365f, 0, 0.37f), 12);
        Add(holder, wax.Mesh(), Mat("#e8dcc0", 0, 0.6f));
        return Fitted(holder, box);
    }

    /* ------------------------------------------------------ the gate, towers -- */

    static StandardMaterial3D Clay() => Surface("castle_wall_slates", 1.4f, "#9a5a40");
    static StandardMaterial3D Canvas() => Cloth("#a8987a", true, 10);

    /// <summary>A parapet's top edge walked from x1 back to x0: merlons and the gaps between.</summary>
    static void Battlements(List<Vector2> o, float x0, float x1, float top, float mh, float mw)
    {
        int n = Math.Max(2, (int)Mathf.Round((x1 - x0) / (mw * 2)));
        float step = (x1 - x0) / n;
        for (int i = 0; i < n; i++)
        {
            float a = x1 - i * step, m = a - step * 0.55f;
            o.Add(new(a, top + mh)); o.Add(new(m, top + mh)); o.Add(new(m, top)); o.Add(new(a - step, top));
        }
    }

    /// <summary>A curtain wall of dressed stone with a battlemented
    /// parapet; the gate's has an arch through it, the portcullis drawn up.</summary>
    static Node3D CurtainWall(Aabb box, bool gate)
    {
        var c = box.GetCenter();
        float w = box.Size.X, h = box.Size.Y, d = box.Size.Z;
        float top = h * (gate ? 0.7f : 0.82f), mh = h * 0.12f, mw = w * 0.05f;
        var o = new List<Vector2> { new(-w / 2, 0) };
        float aw = w * 0.2f, spring = top * 0.55f;
        if (gate)
        {
            o.Add(new(-aw, 0)); o.Add(new(-aw, spring));
            for (int i = 1; i < 14; i++) { float a = Mathf.Pi - Mathf.Pi * i / 14; o.Add(new(aw * Mathf.Cos(a), spring + aw * Mathf.Sin(a))); }
            o.Add(new(aw, spring)); o.Add(new(aw, 0));
        }
        o.Add(new(w / 2, 0)); o.Add(new(w / 2, top));
        Battlements(o, -w / 2, w / 2, top, mh, mw);
        var b = new Build();
        Extrude(b, o.ToArray(), d * 0.7f, h * 0.01f, At(c.X, box.Position.Y, c.Z));
        // A plinth, battered out at the foot.
        Extrude(b, Pts(-w / 2, 0, w / 2, 0, w / 2, h * 0.08f, -w / 2, h * 0.08f), d * 0.8f, h * 0.02f, At(c.X, box.Position.Y - h * 0.02f, c.Z));
        if (gate)
        {
            // The gatehouse over the arch stands a course higher.
            var g = new List<Vector2> { new(-aw * 1.6f, top - h * 0.05f), new(aw * 1.6f, top - h * 0.05f), new(aw * 1.6f, top + h * 0.12f) };
            Battlements(g, -aw * 1.6f, aw * 1.6f, top + h * 0.12f, mh, mw);
            Extrude(b, g.ToArray(), d * 0.75f, h * 0.01f, At(c.X, box.Position.Y, c.Z));
        }
        var root = new Node3D();
        Add(root, b.Mesh(true), Blocks());
        if (gate)
        {
            var iron = new Build();
            float py = box.Position.Y + spring + aw * 0.55f;
            for (int i = -4; i <= 4; i++)
            {
                float x = c.X + i * aw * 0.22f;
                Tube(iron, new List<Vector3> { new(x, py, c.Z + d * 0.2f), new(x, box.Position.Y + spring + aw * 0.9f, c.Z + d * 0.2f) }, h * 0.008f, 4);
                Lathe(iron, Pts(0, 0, h * 0.012f, h * 0.02f, 0, -h * 0.05f), 4, At(new Basis(Vector3.Right, Mathf.Pi), x, py, c.Z + d * 0.2f));
            }
            foreach (float y in new[] { 0.62f, 0.76f })
                Tube(iron, new List<Vector3> { new(c.X - aw * 0.95f, box.Position.Y + spring * 0.2f + y * aw + spring * 0.8f, c.Z + d * 0.2f), new(c.X + aw * 0.95f, box.Position.Y + spring * 0.2f + y * aw + spring * 0.8f, c.Z + d * 0.2f) }, h * 0.008f, 4);
            Add(root, iron.Mesh(), Wrought());
        }
        return root;
    }

    /// <summary>A round tower of dressed stone, battered at its foot, a
    /// clay-tiled cone for a roof.</summary>
    static Node3D Tower(Aabb box)
    {
        var c = box.GetCenter();
        float r = Mathf.Min(box.Size.X, box.Size.Z) / 2, h = box.Size.Y, body = h * 0.66f;
        var stone = new Build();
        Lathe(stone, Pts(0, 0, r * 1.02f, 0, r * 1.02f, 0, r * 0.95f, h * 0.12f, r * 0.9f, body, r * 0.9f, body, r, body + h * 0.02f, r, body + h * 0.02f, r, body + h * 0.06f, r, body + h * 0.06f, 0, body + h * 0.06f), 24,
            At(c.X, box.Position.Y, c.Z), textured: true);
        // Slits for arrows.
        var dark = new Build();
        for (int k = 0; k < 4; k++)
        {
            float a = k * Mathf.Tau / 4 + 0.4f;
            Extrude(dark, Pts(-r * 0.04f, 0, r * 0.04f, 0, r * 0.04f, h * 0.1f, -r * 0.04f, h * 0.1f), r * 0.05f, 0, new Transform3D(new Basis(Vector3.Up, -a + Mathf.Pi / 2), new Vector3(c.X + Mathf.Cos(a) * r * 0.9f, box.Position.Y + body * 0.6f, c.Z + Mathf.Sin(a) * r * 0.9f)));
        }
        var roof = new Build();
        Lathe(roof, Pts(r * 1.15f, body + h * 0.05f, r * 1.1f, body + h * 0.08f, r * 0.5f, body + (h - body) * 0.7f, 0.02f, h), 24, At(c.X, box.Position.Y, c.Z));
        return Hold((stone.Mesh(true), Blocks()), (dark.Mesh(), Mat("#0c0a08", 0, 1)), (roof.Mesh(true), Clay()));
    }

    /* ------------------------------------------------------- the farmland -- */

    /// <summary>A windmill: a stone tower tapering up, a timber cap, four
    /// sails of lattice and canvas turned to the wind.</summary>
    static Node3D Windmill(Aabb box)
    {
        var c = box.GetCenter();
        float h = box.Size.Y, r = Mathf.Min(box.Size.X, box.Size.Z) * 0.3f, body = h * 0.6f;
        var stone = new Build();
        Lathe(stone, Pts(0, 0, r, 0, r, 0, r * 0.72f, body, 0, body), 20, At(c.X, box.Position.Y, c.Z), textured: true);
        var wood = new Build();
        Lathe(wood, Pts(r * 0.82f, body, r * 0.82f, body + h * 0.04f, r * 0.7f, body + h * 0.1f, r * 0.3f, body + h * 0.15f, 0, body + h * 0.16f), 16, At(c.X, box.Position.Y, c.Z));
        var hub = new Vector3(c.X, box.Position.Y + body + h * 0.07f, c.Z + r * 0.9f);
        Tube(wood, new List<Vector3> { hub - new Vector3(0, 0, r * 0.4f), hub + new Vector3(0, 0, r * 0.25f) }, r * 0.1f, 8);
        var sails = new Build();
        float span = h * 0.42f;
        for (int k = 0; k < 4; k++)
        {
            float a = k * Mathf.Pi / 2 + 0.35f;
            var dir = new Vector3(Mathf.Cos(a), Mathf.Sin(a), 0);
            var side = new Vector3(-dir.Y, dir.X, 0);
            var z = new Vector3(0, 0, r * 0.2f);
            Tube(wood, new List<Vector3> { hub + z, hub + z + dir * span }, span * 0.018f, 5);
            for (int j = 0; j <= 6; j++)
            {
                var p = hub + z + dir * (span * (0.22f + 0.78f * j / 6));
                Tube(wood, new List<Vector3> { p, p + side * span * 0.2f }, span * 0.008f, 4);
            }
            Tube(wood, new List<Vector3> { hub + z + dir * span * 0.22f + side * span * 0.2f, hub + z + dir * span + side * span * 0.2f }, span * 0.008f, 4);
            var q0 = hub + z + dir * span * 0.24f + side * span * 0.02f;
            Ribbon(sails, new List<Vector3> { q0, q0 + dir * span * 0.38f, q0 + dir * span * 0.74f }, side, _ => span * 0.17f, At(side.X * span * 0.08f, side.Y * span * 0.08f, 0.01f));
        }
        return Hold((stone.Mesh(true), Surface("medieval_blocks_03", 2.2f, "#d8d0c4")), (wood.Mesh(true), Timber()), (sails.Mesh(), Canvas()));
    }

    /// <summary>A watermill: a stone ground floor, timber over it, a pitched
    /// roof, the wheel turning in the race at its side.</summary>
    static Node3D Watermill(Aabb box)
    {
        var c = box.GetCenter();
        float w = box.Size.X * 0.7f, d = box.Size.Z * 0.7f, h = box.Size.Y, g = Mathf.Max(0, -box.Position.Y);
        float y0 = 0, floor1 = h * 0.28f, eave = h * 0.55f;
        var stone = new Build();
        Extrude(stone, Pts(-w / 2, y0 - g * 0.3f, w / 2, y0 - g * 0.3f, w / 2, floor1, -w / 2, floor1), d, h * 0.01f, At(c.X, 0, c.Z));
        var wood = new Build();
        Extrude(wood, Pts(-w / 2 * 0.97f, floor1, w / 2 * 0.97f, floor1, w / 2 * 0.97f, eave, 0, eave + h * 0.22f, -w / 2 * 0.97f, eave), d * 0.97f, h * 0.008f, At(c.X, 0, c.Z));
        var roof = new Build();
        float rise = h * 0.24f, half = w / 2 * 1.12f, slope = Mathf.Sqrt(half * half + rise * rise), ang = Mathf.Atan2(rise, half);
        foreach (float sx in new[] { -1f, 1f })
            Extrude(roof, Pts(0, -h * 0.012f, slope, -h * 0.012f, slope, h * 0.012f, 0, h * 0.012f), d * 1.12f, h * 0.004f,
                new Transform3D(new Basis(Vector3.Back, sx > 0 ? -ang : Mathf.Pi + ang), new Vector3(c.X, eave + rise + h * 0.02f, c.Z)));
        var wheel = new Build();
        float wr = h * 0.3f, wx = c.X + w / 2 + h * 0.06f;
        var hub = new Vector3(wx, floor1 * 0.5f, c.Z);
        foreach (float dx in new[] { -h * 0.05f, h * 0.05f })
            Tube(wheel, Path(32, t => hub + new Vector3(dx, wr * Mathf.Sin(t * Mathf.Tau), wr * Mathf.Cos(t * Mathf.Tau)), true), h * 0.012f, 5, true);
        for (int k = 0; k < 10; k++)
        {
            float a = k * Mathf.Tau / 10;
            var dir = new Vector3(0, Mathf.Sin(a), Mathf.Cos(a));
            foreach (float dx in new[] { -h * 0.05f, h * 0.05f })
                Tube(wheel, new List<Vector3> { hub + new Vector3(dx, 0, 0), hub + new Vector3(dx, 0, 0) + dir * wr }, h * 0.008f, 4);
            Extrude(wheel, Pts(-h * 0.07f, 0, h * 0.07f, 0, h * 0.07f, wr * 0.18f, -h * 0.07f, wr * 0.18f), h * 0.01f, 0,
                new Transform3D(new Basis(Vector3.Right, -a), hub + dir * wr * 0.85f));
        }
        return Hold((stone.Mesh(true), Blocks()), (wood.Mesh(true), Timber()), (roof.Mesh(true), Slates()), (wheel.Mesh(true), Timber()));
    }

    /// <summary>A harvested field: the sheaves stood up in stooks in rows
    /// to dry, each a man's height, their ears together at the top.</summary>
    static Node3D Stooks(Aabb box, float scale, Func<Vector3, float>? ground)
    {
        var c = box.GetCenter();
        var straw = new Build();
        var one = new Build();
        float sh = 1.3f / scale;
        Lathe(one, Pts(sh * 0.34f, 0, sh * 0.27f, sh * 0.4f, sh * 0.17f, sh * 0.72f, sh * 0.22f, sh * 0.86f, sh * 0.1f, sh * 0.97f, 0, sh), 20,
            warp: p =>
            {
                float a = Mathf.Atan2(p.Z, p.X), lobe = 1 + 0.16f * Mathf.Abs(Mathf.Sin(a * 3));
                return new Vector3(p.X * lobe, p.Y, p.Z * lobe) + new Vector3(Noise(p.Y * 20 / sh, a * 3) - 0.5f, 0, Noise(a * 3 + 5, p.Y * 20 / sh) - 0.5f) * sh * 0.05f;
            });
        float gap = 3.2f / scale;
        int cols = Math.Max(1, (int)(box.Size.X / gap)), rows = Math.Max(1, (int)(box.Size.Z / gap));
        for (int i = 0; i < rows; i++)
            for (int j = 0; j < cols; j++)
            {
                float x = c.X + (j - (cols - 1) / 2f) * gap + (Hash(i, j) - 0.5f) * gap * 0.3f;
                float z = c.Z + (i - (rows - 1) / 2f) * gap + (Hash(j, i + 9) - 0.5f) * gap * 0.3f;
                // Where the field falls away (a bank, the river), none.
                float y = ground?.Invoke(new Vector3(x, 0, z)) ?? box.Position.Y;
                if (y < box.Position.Y - 0.35f / scale) continue;
                straw.Append(one, new Transform3D(new Basis(Vector3.Up, Hash(i + j * 7, 3) * Mathf.Tau) * Basis.FromScale(Vector3.One * (0.85f + Hash(i, j + 4) * 0.3f)), new Vector3(x, y - 0.05f / scale, z)));
            }
        return Hold((straw.Mesh(), Cloth("#9a7c40", false, 3)));
    }

    /* ----------------------------------------------------------- the dig -- */

    /// <summary>A mine's mouth: a hill of rock, a timbered portal into the dark, rails running out.</summary>
    static Node3D Mine(Aabb box)
    {
        var c = box.GetCenter();
        float w = box.Size.X, d = box.Size.Z, h = box.Size.Y;
        var rock = new Build();
        Lathe(rock, Pts(0.5f, 0, 0.47f, 0.25f, 0.38f, 0.55f, 0.22f, 0.85f, 0, 1), 24,
            warp: p => new Vector3(c.X + p.X * w, box.Position.Y + p.Y * h * (0.8f + (Noise(p.X * 5, p.Z * 5) - 0.5f) * 0.5f), c.Z - d * 0.1f + p.Z * d * 0.9f));
        var wood = new Build();
        float pw = w * 0.16f, ph = h * 0.42f, fz = c.Z + d * 0.28f, post = w * 0.025f;
        foreach (float sx in new[] { -1f, 1f })
            Extrude(wood, Pts(-post, 0, post, 0, post, ph, -post, ph), post * 2, post * 0.2f, At(c.X + sx * pw, box.Position.Y, fz));
        Extrude(wood, Pts(-pw - post * 2, ph, pw + post * 2, ph, pw + post * 2, ph + post * 2.4f, -pw - post * 2, ph + post * 2.4f), post * 2.4f, post * 0.2f, At(c.X, box.Position.Y, fz));
        var dark = new Build();
        Extrude(dark, Pts(-pw, 0, pw, 0, pw, ph, -pw, ph), d * 0.3f, 0, At(c.X, box.Position.Y, fz - d * 0.15f - post));
        var iron = new Build();
        foreach (float sx in new[] { -0.5f, 0.5f })
            Tube(iron, new List<Vector3> { new(c.X + sx * pw, box.Position.Y + 0.02f * h, fz - post), new(c.X + sx * pw, box.Position.Y + 0.02f * h, box.End.Z) }, h * 0.01f, 4);
        for (float z = fz; z < box.End.Z; z += d * 0.06f)
            Extrude(wood, Pts(-pw * 0.8f, 0, pw * 0.8f, 0, pw * 0.8f, h * 0.012f, -pw * 0.8f, h * 0.012f), d * 0.025f, 0, At(c.X, box.Position.Y, z));
        return Hold((rock.Mesh(true), Surface("rock_boulder_dry", 3f, "#6a645c")), (wood.Mesh(true), Timber()), (dark.Mesh(), Mat("#050404", 0, 1)), (iron.Mesh(), Wrought()));
    }

    /// <summary>Scaffolding: posts, ledgers and braces lashed together, planked decks, a ladder up.</summary>
    static Node3D Scaffold(Aabb box)
    {
        var c = box.GetCenter();
        float w = box.Size.X * 0.8f, d = box.Size.Z * 0.5f, h = box.Size.Y, r = h * 0.018f;
        var wood = new Build();
        var xs = new[] { -w / 2, 0, w / 2 };
        var zs = new[] { -d / 2, d / 2 };
        foreach (float x in xs)
            foreach (float z in zs)
                Tube(wood, new List<Vector3> { new(c.X + x, box.Position.Y, c.Z + z), new(c.X + x + (Hash((int)(x * 10), 1) - 0.5f) * r * 3, box.Position.Y + h, c.Z + z) }, r, 6);
        foreach (float y in new[] { h * 0.45f, h * 0.9f })
        {
            foreach (float z in zs) Tube(wood, new List<Vector3> { new(c.X - w / 2, box.Position.Y + y, c.Z + z), new(c.X + w / 2, box.Position.Y + y, c.Z + z) }, r * 0.8f, 5);
            foreach (float x in xs) Tube(wood, new List<Vector3> { new(c.X + x, box.Position.Y + y, c.Z - d / 2), new(c.X + x, box.Position.Y + y, c.Z + d / 2) }, r * 0.8f, 5);
            for (float x = -w / 2 + h * 0.06f; x < w / 2; x += h * 0.09f)
                Extrude(wood, Pts(-h * 0.04f, 0, h * 0.04f, 0, h * 0.04f, h * 0.012f, -h * 0.04f, h * 0.012f), d, 0, At(c.X + x, box.Position.Y + y + r, c.Z));
        }
        foreach (float z in zs)
            Tube(wood, new List<Vector3> { new(c.X - w / 2, box.Position.Y + h * 0.05f, c.Z + z), new(c.X, box.Position.Y + h * 0.45f, c.Z + z) }, r * 0.7f, 5);
        float lx = c.X + w / 2 + h * 0.08f;
        foreach (float dz in new[] { -h * 0.06f, h * 0.06f })
            Tube(wood, new List<Vector3> { new(lx + h * 0.1f, box.Position.Y, c.Z + dz), new(lx, box.Position.Y + h * 0.95f, c.Z + dz) }, r * 0.6f, 5);
        for (float y = h * 0.1f; y < h * 0.95f; y += h * 0.09f)
        {
            float x = lx + h * 0.1f * (1 - y / (h * 0.95f));
            Tube(wood, new List<Vector3> { new(x, box.Position.Y + y, c.Z - h * 0.06f), new(x, box.Position.Y + y, c.Z + h * 0.06f) }, r * 0.4f, 4);
        }
        return Hold((wood.Mesh(true), Timber()));
    }

    /* -------------------------------------------------------- the Blind -- */

    /// <summary>A ridge tent of canvas on poles, guyed out to pegs.</summary>
    static Node3D Tent(Aabb box)
    {
        var c = box.GetCenter();
        float w = box.Size.X * 0.9f, d = box.Size.Z * 0.95f, h = box.Size.Y * 0.95f, y0 = box.Position.Y;
        var canvas = new Build();
        foreach (float sx in new[] { -1f, 1f })
            Sheet(canvas, null, Pts(0, -d / 2, 1, -d / 2, 1, d / 2, 0, d / 2), d / 10, 0, p =>
            {
                float t = p.X, sag = Mathf.Sin(t * Mathf.Pi) * h * 0.04f * (1 - Mathf.Abs(p.Y) / (d / 2) * 0.5f);
                return new Vector3(c.X + sx * t * w / 2, y0 + h * (1 - t) - sag, c.Z + p.Y);
            });
        // The ends: a triangle of canvas at the back, the front left open.
        Extrude(canvas, Pts(-w / 2, 0, w / 2, 0, 0, h), 0.01f, 0, At(c.X, y0, c.Z - d / 2));
        var wood = new Build();
        foreach (float z in new[] { -d / 2, d / 2 })
            Tube(wood, new List<Vector3> { new(c.X, y0, c.Z + z), new(c.X, y0 + h * 1.05f, c.Z + z) }, h * 0.02f, 5);
        Tube(wood, new List<Vector3> { new(c.X, y0 + h, c.Z - d / 2 - h * 0.05f), new(c.X, y0 + h, c.Z + d / 2 + h * 0.05f) }, h * 0.018f, 5);
        var rope = new Build();
        foreach (float z in new[] { -d / 2, d / 2 })
            Tube(rope, new List<Vector3> { new(c.X, y0 + h * 1.02f, c.Z + z), new(c.X, y0, c.Z + z + Mathf.Sign(z) * h * 0.7f) }, h * 0.005f, 3);
        return Hold((canvas.Mesh(), Canvas()), (wood.Mesh(), Timber()), (rope.Mesh(), Mat("#8a7a5a", 0, 0.95f)));
    }

    /// <summary>A straw archery butt on a trestle, its face painted in rings, arrows in it.</summary>
    static Node3D Target(Aabb box)
    {
        var c = box.GetCenter();
        float h = box.Size.Y, r = Mathf.Min(box.Size.X, h) * 0.45f, cy = box.Position.Y + h - r;
        var tilt = new Basis(Vector3.Right, -0.2f);
        var at = new Transform3D(tilt, new Vector3(c.X, cy, c.Z));
        var straw = new Build();
        Lathe(straw, Pts(0, -r * 0.2f, r, -r * 0.2f, r * 1.02f, 0, r, r * 0.2f, 0, r * 0.2f), 28, at * new Transform3D(Made.Facing, Vector3.Zero));
        var rings = new List<(Build, string)>();
        string[] colours = { "#e8e0d0", "#1a1814", "#2a5aa8", "#b82020", "#e8c040" };
        for (int k = 0; k < 5; k++)
        {
            var ring = new Build();
            float ro = r * (0.95f - k * 0.18f), ri = Mathf.Max(0, ro - r * 0.18f);
            Lathe(ring, Pts(ro, 0, ri, 0), 32, at * new Transform3D(Made.Facing, new Vector3(0, 0, r * 0.2f + 0.002f * (k + 1) * h)));
            rings.Add((ring, colours[k]));
        }
        var wood = new Build();
        foreach (var (sx, sz) in new[] { (-1f, 1f), (1f, 1f), (0f, -1f) })
            Tube(wood, new List<Vector3> { new(c.X + sx * r * 0.7f, box.Position.Y, c.Z + sz * r * 0.5f), new(c.X + sx * r * 0.2f, cy, c.Z - sz * r * 0.05f) }, h * 0.02f, 5);
        var arrows = new Build();
        foreach (var (x, y) in new[] { (0.1f, 0.15f), (-0.3f, -0.1f), (0.35f, 0.4f) })
        {
            var tip = at * new Vector3(x * r, y * r, r * 0.2f);
            var tail = tip + tilt * new Vector3(0.1f * x, 0.05f, 1) * r * 0.9f;
            Tube(arrows, new List<Vector3> { tip, tail }, h * 0.006f, 4);
        }
        var root = Hold((straw.Mesh(), Cloth("#b89a58", false, 6)), (wood.Mesh(), Timber()), (arrows.Mesh(), Mat("#6a4a2a", 0, 0.7f)));
        foreach (var (ring, col) in rings) Add(root, ring.Mesh(), Mat(col, 0, 0.8f));
        return root;
    }

    /// <summary>A pennant on a pole, lifting in the wind.</summary>
    static Node3D Flag(Aabb box)
    {
        var c = box.GetCenter();
        float h = box.Size.Y, fw = Mathf.Max(box.Size.Z, box.Size.X) * 0.9f;
        var pole = new Build();
        Tube(pole, new List<Vector3> { new(c.X, box.Position.Y, box.Position.Z + 0.02f * h), new(c.X, box.End.Y, box.Position.Z + 0.02f * h) }, h * 0.015f, 6);
        Lathe(pole, Pts(0, 0, h * 0.03f, h * 0.02f, 0, h * 0.05f), 8, At(c.X, box.End.Y, box.Position.Z + 0.02f * h));
        var cloth = new Build();
        float top = box.End.Y - h * 0.08f, fh = h * 0.32f;
        Sheet(cloth, null, Pts(0, 0, fw, fh * 0.25f, fw, fh * 0.75f, 0, fh), fh / 8, 0,
            p => new Vector3(c.X + Mathf.Sin(p.X * 6 / fw * Mathf.Pi * 0.5f) * fw * 0.08f, top - fh + p.Y, box.Position.Z + 0.02f * h + p.X));
        return Hold((pole.Mesh(), Timber()), (cloth.Mesh(), Cloth("#8a1a16", true, 4)));
    }

    /// <summary>A barrow: a planked tray on one wheel at the front (+Z), handles and legs behind.</summary>
    static Node3D Wheelbarrow(Aabb box)
    {
        var c = box.GetCenter();
        float w = box.Size.X, d = box.Size.Z, h = box.Size.Y, y0 = box.Position.Y;
        var wood = new Build();
        float ty = y0 + h * 0.42f, tl = d * 0.55f, tw = w * 0.9f, side = h * 0.38f, t = h * 0.03f;
        var tray = new Transform3D(new Basis(Vector3.Right, -0.08f), new Vector3(c.X, ty, c.Z + d * 0.05f));
        void Board(Vector3 size, Vector3 at, Basis? turn = null) =>
            Extrude(wood, Pts(-size.X / 2, -size.Y / 2, size.X / 2, -size.Y / 2, size.X / 2, size.Y / 2, -size.X / 2, size.Y / 2), size.Z, Mathf.Min(size.X, size.Y) * 0.1f, tray * new Transform3D(turn ?? Basis.Identity, at));
        Board(new Vector3(tw, t, tl), new Vector3(0, 0, 0));
        foreach (float sx in new[] { -1f, 1f }) Board(new Vector3(t, side, tl), new Vector3(sx * tw / 2, side / 2, 0));
        Board(new Vector3(tw, side, t), new Vector3(0, side / 2, -tl / 2));
        Board(new Vector3(tw, side * 1.1f, t), new Vector3(0, side / 2, tl / 2), new Basis(Vector3.Right, 0.35f));
        foreach (float sx in new[] { -1f, 1f })
        {
            Tube(wood, new List<Vector3> { new(c.X + sx * tw * 0.3f, y0 + h * 0.3f, box.End.Z - h * 0.3f), new(c.X + sx * tw * 0.45f, y0 + h * 0.62f, box.Position.Z) }, h * 0.025f, 5);
            Tube(wood, new List<Vector3> { new(c.X + sx * tw * 0.38f, ty, c.Z - d * 0.2f), new(c.X + sx * tw * 0.4f, y0, c.Z - d * 0.24f) }, h * 0.025f, 5);
        }
        float wr = h * 0.3f;
        var wheel = new Build();
        var wc = new Vector3(c.X, y0 + wr, box.End.Z - wr * 1.1f);
        Tube(wheel, Path(24, a => wc + new Vector3(0, wr * Mathf.Sin(a * Mathf.Tau), wr * Mathf.Cos(a * Mathf.Tau)), true), h * 0.03f, 6, true);
        for (int k = 0; k < 6; k++) { float a = k * Mathf.Pi / 3; Tube(wheel, new List<Vector3> { wc, wc + new Vector3(0, Mathf.Sin(a), Mathf.Cos(a)) * wr }, h * 0.015f, 4); }
        Tube(wheel, new List<Vector3> { wc + new Vector3(-tw * 0.3f, 0, 0), wc + new Vector3(tw * 0.3f, 0, 0) }, h * 0.02f, 5);
        return Hold((wood.Mesh(true), Timber()), (wheel.Mesh(), Timber()));
    }

    /// <summary>A bucket stood full of arrows.</summary>
    static Node3D ArrowBucket(Aabb box)
    {
        var holder = new Node3D();
        if (Dressing.Piece("props/Bucket_Wooden_1") is Node3D bucket) holder.AddChild(bucket);
        var b = Bounds(holder, Transform3D.Identity) ?? new Aabb(new Vector3(-0.2f, 0, -0.2f), new Vector3(0.4f, 0.4f, 0.4f));
        var shafts = new Build();
        var fletch = new Build();
        for (int k = 0; k < 9; k++)
        {
            float a = k * 2.4f, rr = b.Size.X * 0.25f * Hash(k, 2);
            var foot = new Vector3(b.GetCenter().X + Mathf.Cos(a) * rr, b.Position.Y + b.Size.Y * 0.3f, b.GetCenter().Z + Mathf.Sin(a) * rr);
            var top = foot + new Vector3(Mathf.Cos(a) * 0.1f, 1, Mathf.Sin(a) * 0.1f).Normalized() * b.Size.Y * 1.6f;
            Tube(shafts, new List<Vector3> { foot, top }, b.Size.Y * 0.012f, 4);
            Ribbon(fletch, new List<Vector3> { top - (top - foot).Normalized() * b.Size.Y * 0.25f, top }, new Vector3(Mathf.Cos(a + 1), 0, Mathf.Sin(a + 1)), t => b.Size.Y * 0.08f * (0.4f + t * 0.6f));
        }
        Add(holder, shafts.Mesh(), Mat("#8a6a44", 0, 0.7f));
        Add(holder, fletch.Mesh(), Mat("#d8d0c0", 0, 0.9f, true));
        return Fitted(holder, box);
    }

    /// <summary>A table as the kit has it, sized to the footprint, set with a candlestick, a mug and a bottle.</summary>
    static Node3D? Table(Aabb box)
    {
        if (Dressing.Piece("props/Table_Large") is not Node3D table || Bounds(table, Transform3D.Identity) is not Aabb b) return null;
        float k = Mathf.Min(box.Size.X / b.Size.X, box.Size.Z / b.Size.Z) * 1.1f;
        var holder = new Node3D();
        var c = box.GetCenter();
        var at = new Transform3D(Basis.FromScale(Vector3.One * k), new Vector3(c.X - b.GetCenter().X * k, box.Position.Y - b.Position.Y * k, c.Z - b.GetCenter().Z * k));
        table.Transform = at;
        holder.AddChild(table);
        float top = at.Origin.Y + b.End.Y * k;
        foreach (var (id, x, z) in new[] { ("props/CandleStick", -0.2f, 0.1f), ("props/Mug", 0.15f, -0.15f), ("props/Bottle_1", 0.28f, 0.12f) })
            if (Dressing.Piece(id) is Node3D thing)
            {
                thing.Transform = new Transform3D(Basis.FromScale(Vector3.One * k), new Vector3(c.X + x * box.Size.X, top, c.Z + z * box.Size.Z));
                holder.AddChild(thing);
            }
        return holder;
    }
}
