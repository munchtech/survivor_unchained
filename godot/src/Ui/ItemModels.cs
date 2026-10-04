using System;
using System.Collections.Generic;
using Godot;
using SurvivorUnchained.View;
using static SurvivorUnchained.View.Made;
using static SurvivorUnchained.View.Shapes;

namespace SurvivorUnchained.Ui;

/// <summary>
/// What each item's photograph is of (ItemPhotos). A weapon is the model the
/// survivor holds (Arms), so the blade in the pack is the blade in the hand.
/// The rest are made here (Shapes): flasks, helms and lamps turned on a
/// lathe, chains and wire swept along paths, hides, petals and garments cut
/// out and draped, in materials that read as what they are (brass, glass,
/// mail, quilted linen, fur, bone).
/// </summary>
public static class ItemModels
{
    /// <summary>How an item sits for its picture: spun about its own long
    /// axis, tipped in the picture's plane, turned toward the light and
    /// pitched toward the camera, in that order; larger or smaller in the
    /// frame.</summary>
    public sealed record Pose(float Pitch = 0, float Turn = 0, float Tilt = 0, float Spin = 0, float Scale = 1)
    {
        public Basis Basis => new Basis(Vector3.Right, Pitch) * new Basis(Vector3.Up, Turn) * new Basis(Vector3.Back, Tilt) * new Basis(Vector3.Up, Spin);
    }

    sealed record Source(Func<Node3D?> Make, Pose Pose);

    static readonly Dictionary<string, Source> Sources = new()
    {
        // In hand.
        ["sword"] = new(() => Arms.Make("chevalier_sword"), new(Tilt: -0.78f, Spin: 0.35f)),
        ["cleaver"] = new(() => Arms.Make("viking_axe"), new(Tilt: -0.7f, Spin: 0.3f)),
        ["axe"] = new(() => Crossed("viking_axe", "viking_axe", 0.55f), new(Turn: 0.25f)),
        ["dagger"] = new(() => Crossed("daggers", "dagger_b", 0.5f), new(Turn: 0.2f)),
        ["bow"] = new(() => Arms.Make("crossbow"), new(Pitch: 0.6f, Turn: -0.9f, Tilt: 0.4f)),
        ["staff"] = new(() => Arms.Make("mage_staff"), new(Tilt: -0.7f, Spin: 0.4f)),
        ["shield"] = new(() => Arms.Make("shield_round"), new(Pitch: 0.1f, Turn: 0.5f)),
        ["wand"] = new(() => Arms.Make("wand"), new(Tilt: -0.75f, Spin: 0.3f)),
        ["wand_dark"] = new(DarkWand, new(Tilt: -0.72f, Spin: 0.3f)),
        // Worn.
        ["helm"] = new(Helm, new(Pitch: 0.2f, Turn: 0.6f)),
        ["helm_light"] = new(Cap, new(Pitch: 0.25f, Turn: 0.6f)),
        ["cloak"] = new(Cloak, new(Pitch: 0.2f, Turn: 0.9f)),
        ["armor"] = new(Mail, new(Pitch: 0.1f, Turn: 0.45f)),
        ["armor_heavy"] = new(Plate, new(Pitch: 0.1f, Turn: 0.45f)),
        ["armor_light"] = new(Jerkin, new(Pitch: 0.1f, Turn: 0.45f)),
        ["mask"] = new(Mask, new(Pitch: 0.15f, Turn: 0.7f)),
        ["kerchief"] = new(Kerchief, new(Pitch: -0.5f, Turn: 0.35f, Tilt: 0.1f)),
        ["circlet"] = new(Circlet, new(Pitch: 0.6f, Turn: 0.35f)),
        ["ring"] = new(() => Ring("#c8323a"), new(Pitch: 0.4f, Turn: 0.5f)),
        ["fang"] = new(() => Amulet("fang"), new(Turn: 0.3f)),
        ["bone"] = new(() => Amulet("bone"), new(Turn: 0.3f)),
        ["moon"] = new(() => Amulet("moon"), new(Turn: 0.3f)),
        ["pelt"] = new(() => Pelt(new Color("#8e8880"), new Color("#302c28"), 1), new(Pitch: -0.6f, Turn: 0.2f, Tilt: 0.5f)),
        ["hide"] = new(() => Pelt(new Color("#9a7450"), new Color("#34241a"), 1.7f), new(Pitch: -0.6f, Turn: 0.2f, Tilt: 0.5f)),
        // Carried.
        ["censer"] = new(Censer, new(Pitch: 0.15f, Turn: 0.3f)),
        ["lantern"] = new(() => Lantern(true), new(Pitch: 0.2f, Turn: 0.4f)),
        ["lamp"] = new(Lamp, new(Pitch: 0.2f, Turn: 0.4f)),
        ["lens"] = new(Lens, new(Pitch: 0.2f, Turn: 0.5f)),
        ["totem"] = new(Totem, new(Pitch: 0.2f, Turn: 0.4f, Tilt: 0.35f)),
        ["seed"] = new(SeedPouch, new(Pitch: 0.2f, Turn: 0.4f)),
        ["picks"] = new(Picks, new(Pitch: 0.15f, Turn: 0.4f, Tilt: -0.3f)),
        ["bomb"] = new(Bomb, new(Pitch: 0.3f, Turn: 0.5f)),
        ["key"] = new(Key, new(Pitch: 0.2f, Tilt: -0.6f, Spin: 0.4f)),
        ["chest"] = new(Chest, new(Pitch: 0.35f, Turn: 0.6f)),
        // Drunk and dressed.
        ["potion"] = new(() => Flask("#8a0a16", 0.12f, 0), new(Pitch: 0.15f, Tilt: -0.12f)),
        ["antidote"] = new(() => Flask("#2a7a1e", 0.12f, 1), new(Pitch: 0.15f, Turn: 0.2f, Tilt: 0.1f)),
        ["vial"] = new(() => Flask("#3a8a3a", 0.15f, 2), new(Pitch: 0.1f, Tilt: -0.5f)),
        ["vial_orange"] = new(() => Flask("#c84a06", 0.5f, 2), new(Pitch: 0.1f, Tilt: -0.5f)),
        ["bandage"] = new(Bandage, new(Pitch: 0.55f, Turn: 0.3f, Tilt: 0.15f)),
        // Gathered.
        ["ember"] = new(Ember, new(Pitch: 0.2f, Turn: 0.5f)),
        ["sigil"] = new(Sigil, new(Pitch: 0.3f, Turn: 0.6f)),
        ["root"] = new(Root, new(Pitch: 0.2f, Turn: 0.4f, Tilt: 0.3f)),
        ["flower"] = new(Flower, new(Pitch: 0.55f, Turn: 0.3f)),
        ["dust"] = new(Dust, new(Pitch: 0.45f, Turn: 0.3f)),
        ["iron"] = new(OldIron, new(Pitch: 0.5f, Turn: 0.35f)),
        // Written.
        ["book"] = new(() => Book("#3a2a1c", true), new(Pitch: 0.3f, Turn: 0.6f)),
        ["journal"] = new(() => Book("#5a2a2a", false), new(Pitch: 0.3f, Turn: -0.5f)),
        ["scroll"] = new(Scroll, new(Pitch: 0.3f, Turn: 0.4f, Tilt: 0.9f)),
        ["map"] = new(Map, new(Pitch: -0.7f, Turn: 0.3f)),
    };

    public static IEnumerable<string> Keys => Sources.Keys;
    public static bool Has(string key) => Sources.ContainsKey(key);

    /// <summary>The item's model, new, and how it sits; null if it cannot be made.</summary>
    public static (Node3D Model, Pose Pose)? Make(string key)
    {
        // For judging the world's pieces in the studio: kit:KIT/PIECE, a
        // world kit's piece; kk:PACK/NAME, what stands in for a KayKit one.
        if (key.StartsWith("kit:") && Dressing.Piece(key[4..]) is Node3D kit) return (kit, new Pose(Pitch: 0.25f, Turn: 0.6f));
        if (key.StartsWith("kk:") && key[3..].Split('/') is [var pack, var name] && Pieces.For(pack, name) is Node3D piece) return (piece, new Pose(Pitch: 0.25f, Turn: 0.6f));
        if (!Sources.TryGetValue(key, out var s)) return null;
        try { return s.Make() is Node3D n ? (n, s.Pose) : null; }
        catch (Exception e) { GD.PushWarning($"item photograph {key}: {e.Message}"); return null; }
    }

    /* ------------------------------------------------------------ sources -- */

    /// <summary>Two weapons crossed at the middle of their length.</summary>
    static Node3D Crossed(string a, string b, float spread)
    {
        var root = new Node3D();
        foreach (var (id, s) in new[] { (a, 1f), (b, -1f) })
        {
            var spec = Arms.All[id];
            float mid = (1 - 2 * spec.Grip) * spec.Length / 2;
            var basis = new Basis(Vector3.Back, spread * s) * new Basis(Vector3.Up, s < 0 ? Mathf.Pi : 0);
            var w = Arms.Make(id);
            w.Transform = new Transform3D(basis, basis * new Vector3(0, -mid, 0.04f * s));
            root.AddChild(w);
        }
        return root;
    }

    /* ----------------------------------------------------- drunk, dressed -- */

    /// <summary>A stoppered bottle and what is in it: a round-bellied flask
    /// (0), a six-sided apothecary's bottle with a label (1), a sample vial (2).</summary>
    static Node3D Flask(string liquid, float glow, int shape)
    {
        var root = new Node3D();
        Vector2[] glass, fill, cork;
        float neckY = 0.4f, neckR = 0.135f;
        switch (shape)
        {
            case 0:
                glass = Pts(0, -0.52f, 0.16f, -0.5f, 0.3f, -0.44f, 0.4f, -0.32f, 0.44f, -0.16f, 0.43f, 0, 0.37f, 0.14f, 0.24f, 0.24f, 0.15f, 0.3f, 0.13f, 0.36f, 0.13f, 0.56f, 0.165f, 0.58f, 0.165f, 0.62f, 0.13f, 0.63f);
                fill = Pts(0, -0.49f, 0.15f, -0.47f, 0.28f, -0.42f, 0.375f, -0.31f, 0.41f, -0.16f, 0.405f, 0, 0.37f, 0.1f, 0.37f, 0.1f, 0, 0.1f);
                cork = Pts(0, 0.5f, 0.11f, 0.5f, 0.115f, 0.62f, 0.13f, 0.74f, 0.11f, 0.77f, 0, 0.77f);
                break;
            case 1:
                glass = Pts(0, -0.6f, 0.27f, -0.6f, 0.3f, -0.57f, 0.3f, 0.18f, 0.27f, 0.28f, 0.13f, 0.38f, 0.1f, 0.42f, 0.1f, 0.58f, 0.125f, 0.6f, 0.125f, 0.64f, 0.1f, 0.65f);
                fill = Pts(0, -0.57f, 0.27f, -0.57f, 0.28f, -0.55f, 0.28f, 0.12f, 0.28f, 0.12f, 0, 0.12f);
                cork = Pts(0, 0.52f, 0.09f, 0.52f, 0.095f, 0.64f, 0.11f, 0.74f, 0.09f, 0.77f, 0, 0.77f);
                neckY = 0.46f; neckR = 0.105f;
                break;
            default:
                glass = Pts(0, -0.62f, 0.08f, -0.6f, 0.12f, -0.54f, 0.13f, -0.45f, 0.13f, 0.46f, 0.155f, 0.48f, 0.155f, 0.52f, 0.125f, 0.53f);
                fill = Pts(0, -0.59f, 0.07f, -0.575f, 0.105f, -0.53f, 0.115f, -0.45f, 0.115f, 0.18f, 0.115f, 0.18f, 0, 0.18f);
                cork = Pts(0, 0.36f, 0.11f, 0.36f, 0.115f, 0.52f, 0.125f, 0.62f, 0.105f, 0.65f, 0, 0.65f);
                break;
        }
        int seg = shape == 1 ? 6 : 40;
        var bf = new Build(); Lathe(bf, fill, seg);
        var bg = new Build(); Lathe(bg, glass, seg);
        Add(root, shape == 1 ? bf.Faceted() : bf, new StandardMaterial3D
        {
            AlbedoColor = new Color(liquid), Roughness = 0.3f, MetallicSpecular = 0.25f, EmissionEnabled = true, Emission = new Color(liquid), EmissionEnergyMultiplier = glow,
        });
        Add(root, shape == 1 ? bg.Faceted() : bg, Glass());
        var bc = new Build(); Lathe(bc, cork, 16);
        Add(root, bc, Mat("#8a5a36", 0, 0.9f));
        if (shape != 2)
        {
            var twine = new Build();
            Tube(twine, Circle(new Vector3(0, neckY, 0), neckR, Vector3.Right, Vector3.Back, 24), 0.014f, 6, true);
            Add(root, twine, Mat("#b49a6a", 0, 0.95f));
        }
        if (shape == 1)
        {
            var label = new Build(); Lathe(label, Pts(0.305f, -0.36f, 0.305f, 0.02f), 6);
            Add(root, label.Faceted(), new StandardMaterial3D { AlbedoTexture = Tex(Parchment(new Color("#ddcca4"), 64, 64)), Roughness = 0.9f });
        }
        return root;
    }

    /// <summary>A roll of linen, its end unwound.</summary>
    static Node3D Bandage()
    {
        var root = new Node3D();
        var linen = Cloth("#a89c86", true, 4);
        var roll = new Build();
        Lathe(roll, Pts(0.12f, 0.25f, 0.12f, -0.25f, 0.12f, -0.25f, 0.4f, -0.25f, 0.42f, -0.23f, 0.42f, 0.23f, 0.4f, 0.25f, 0.12f, 0.25f), 40, textured: true);
        Add(root, roll, linen);
        var wraps = new Build();
        foreach (float y in new[] { 0.252f, -0.252f })
            foreach (float r in new[] { 0.17f, 0.23f, 0.29f, 0.35f })
                Tube(wraps, Circle(new Vector3(0, y, 0), r, Vector3.Right, Vector3.Back, 40), 0.005f, 4, true);
        Add(root, wraps, Mat("#c8baa0", 0, 1));
        var tail = new Build();
        Ribbon(tail, new List<Vector3> { new(0.42f, 0, 0), new(0.44f, -0.01f, 0.18f), new(0.41f, -0.05f, 0.38f), new(0.33f, -0.13f, 0.55f), new(0.22f, -0.26f, 0.66f), new(0.12f, -0.4f, 0.7f) },
            Vector3.Up, _ => 0.46f);
        Add(root, tail, linen);
        return root;
    }

    /// <summary>The beaked mask of a plague doctor: leather, brass-rimmed green glass.</summary>
    static Node3D Mask()
    {
        var root = new Node3D();
        var leather = Mat("#5a4430", 0, 0.62f, true);
        var face = new Build();
        var dome = new List<Vector2>();
        for (int k = 0; k <= 10; k++) { float a = k / 10f * Mathf.Pi / 2; dome.Add(new Vector2(0.5f * Mathf.Cos(a), 0.5f * Mathf.Sin(a))); }
        Lathe(face, dome, 40, warp: p => new Vector3(p.X, -p.Z * 1.1f, p.Y * 0.7f));
        var beakProfile = Pts(0.2f, 0, 0.18f, 0.2f, 0.14f, 0.42f, 0.09f, 0.64f, 0.04f, 0.82f, 0, 0.92f);
        float Droop(float z) => 0.32f * Mathf.Pow(z / 0.92f, 2);
        Lathe(face, beakProfile, 24, warp: p => new Vector3(p.X, -p.Z - Droop(p.Y) - 0.12f, p.Y + 0.2f));
        Add(root, face, leather);
        float R(float y)
        {
            for (int i = 1; i < beakProfile.Length; i++)
                if (y <= beakProfile[i].Y) return Mathf.Lerp(beakProfile[i - 1].X, beakProfile[i].X, (y - beakProfile[i - 1].Y) / (beakProfile[i].Y - beakProfile[i - 1].Y));
            return 0;
        }
        var dark = new Build();
        Tube(dark, Path(20, t => { float y = 0.05f + t * 0.8f; return new Vector3(0, R(y) - Droop(y) - 0.12f + 0.004f, y + 0.2f); }), 0.012f, 5);
        Ribbon(dark, Path(24, t => new Vector3(0.5f * Mathf.Cos(t * Mathf.Pi), 0.02f, -0.46f * Mathf.Sin(t * Mathf.Pi))), Vector3.Up, _ => 0.07f);
        Add(root, dark, Mat("#2a2018", 0, 0.8f, true));
        var rims = new Build();
        var lenses = new Build();
        foreach (float x in new[] { -0.19f, 0.19f })
        {
            Tube(rims, Circle(new Vector3(x, 0.12f, 0.325f), 0.11f, Vector3.Right, Vector3.Up, 32), 0.026f, 8, true);
            Lathe(lenses, Pts(0.1f, 0, 0, 0), 24, At(Facing, x, 0.12f, 0.33f));
            rims.Append(Rivet(), At(x > 0 ? 0.5f : -0.5f, 0.02f, 0));
        }
        Add(root, rims, Brass());
        Add(root, lenses, new StandardMaterial3D { AlbedoColor = new Color("#9ad8a0"), Roughness = 0.05f, EmissionEnabled = true, Emission = new Color("#2a6a3a"), EmissionEnergyMultiplier = 0.8f });
        return root;
    }

    /// <summary>A red cloth folded to a triangle, knotted at the corners.</summary>
    static Node3D Kerchief()
    {
        var root = new Node3D();
        var red = Cloth("#6e1210", true, 5);
        var sheet = new Build();
        Sheet(sheet, null, Pts(-0.8f, 0.4f, 0.8f, 0.4f, 0, -0.7f), 0.04f, 0,
            p => new Vector3(p.X, p.Y, p.Z + Mathf.Sin(p.X * 3) * 0.08f + p.Y * p.Y * 0.2f + 0.07f * Mathf.Sin(p.X * 9 + p.Y * 4) * (0.5f - p.Y)));
        foreach (float s in new[] { -1f, 1f })
            Ribbon(sheet, new List<Vector3> { new(s * 0.8f, 0.42f, 0.06f), new(s * 0.9f, 0.32f, 0.08f), new(s * 0.97f, 0.18f, 0.06f), new(s * 1.0f, 0.05f, 0.03f) },
                new Vector3(1, 0.3f, 0.4f), t => 0.13f * (1 - t * 0.6f));
        Add(root, sheet, red);
        foreach (float s in new[] { -1f, 1f }) Add(root, Ball(0.085f), red, At(s * 0.8f, 0.42f, 0.05f));
        return root;
    }

    /// <summary>A silver circlet with a crescent at the brow and a pale stone.</summary>
    static Node3D Circlet()
    {
        var root = new Node3D();
        var silver = new Build();
        Tube(silver, Path(72, t => new Vector3(0.62f * Mathf.Sin(t * Mathf.Tau), 0, 0.56f * Mathf.Cos(t * Mathf.Tau)), true),
            t => 0.05f + 0.02f * Mathf.Pow(Mathf.Max(0, Mathf.Cos(t * Mathf.Tau)), 8), 8, true);
        // The brow-piece leans back, as it would over a forehead.
        Extrude(silver, Crescent(0.32f, 0.28f, 0.14f), 0.06f, 0.014f, At(new Basis(Vector3.Right, -0.35f), 0, 0.22f, 0.55f));
        foreach (float s in new[] { -1f, 1f })
            Extrude(silver, Leaf, 0.03f, 0.008f, At(new Basis(Vector3.Up, s * 0.47f) * new Basis(Vector3.Back, -s * 0.9f), s * 0.3f, 0.06f, 0.5f));
        Add(root, silver, Silver());
        var stone = new Build();
        Lathe(stone, Pts(0.1f, 0, 0.095f, 0.035f, 0.065f, 0.07f, 0, 0.085f), 10, At(new Basis(Vector3.Right, -0.35f) * Facing, 0, 0.2f, 0.58f));
        Add(root, stone.Faceted(), Gem("#cfe8ff", 0.5f));
        return root;
    }

    /// <summary>A gold ring, thicker at the shoulders, a stone held in four prongs.</summary>
    static Node3D Ring(string stone)
    {
        var root = new Node3D();
        var gold = new Build();
        Tube(gold, Path(64, t => new Vector3(0.5f * Mathf.Sin(t * Mathf.Tau), 0.5f * Mathf.Cos(t * Mathf.Tau), 0), true),
            t => 0.08f + 0.04f * Mathf.Pow(Mathf.Max(0, Mathf.Cos(t * Mathf.Tau)), 6), 10, true);
        Lathe(gold, Pts(0, 0, 0.08f, 0, 0.12f, 0.06f, 0.13f, 0.1f, 0.12f, 0.11f, 0, 0.11f), 16, At(0, 0.56f, 0));
        for (int k = 0; k < 4; k++)
        {
            float a = k * Mathf.Pi / 2 + Mathf.Pi / 4;
            var d = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
            Tube(gold, new List<Vector3> { d * 0.1f + new Vector3(0, 0.64f, 0), d * 0.15f + new Vector3(0, 0.72f, 0), d * 0.11f + new Vector3(0, 0.79f, 0) }, t => 0.02f * (1 - 0.4f * t), 5);
        }
        Add(root, gold, Gold());
        var gem = new Build();
        Lathe(gem, Pts(0, -0.1f, 0.15f, 0.02f, 0.15f, 0.02f, 0.1f, 0.08f, 0, 0.08f), 8, At(0, 0.73f, 0));
        Add(root, gem.Faceted(), Gem(stone));
        return root;
    }

    /// <summary>Something on a gold chain: a wolf's fang bound in wire, a
    /// knucklebone, a silver crescent; the pendant large, as a jeweller
    /// photographs it.</summary>
    static Node3D Amulet(string pendant)
    {
        var root = new Node3D();
        var gold = new Build();
        Vector3 E(float t) => new(0.38f * Mathf.Sin(t * Mathf.Tau), 0.3f + 0.46f * Mathf.Cos(t * Mathf.Tau), 0);
        const int Links = 28;
        for (int k = 0; k < Links; k++)
        {
            float t = (float)k / Links;
            var p = E(t);
            var T = (E(t + 0.002f) - E(t - 0.002f)).Normalized();
            var w = k % 2 == 0 ? Vector3.Back : Vector3.Back.Cross(T);
            Tube(gold, Path(12, s => p + T * (0.05f * Mathf.Cos(s * Mathf.Tau)) + w * (0.028f * Mathf.Sin(s * Mathf.Tau)), true), 0.011f, 5, true);
        }
        Tube(gold, Circle(new Vector3(0, -0.21f, 0), 0.05f, Vector3.Right, Vector3.Up, 16), 0.016f, 6, true);
        Add(root, gold, Gold());
        // The pendant, made hanging from y -0.455, half as large again from where it hangs.
        var hang = new Node3D { Transform = new Transform3D(Basis.FromScale(Vector3.One * 1.5f), new Vector3(0, 0.42f, 0)) };
        root.AddChild(hang);
        switch (pendant)
        {
            case "fang":
            {
                var fang = new Build();
                Lathe(fang, Pts(0, 0, 0.1f, 0, 0.1f, 0, 0.105f, 0.08f, 0.095f, 0.2f, 0.075f, 0.34f, 0.048f, 0.48f, 0.02f, 0.58f, 0, 0.63f), 20,
                    warp: p => new Vector3(-p.X + 0.12f * Mathf.Pow(p.Y / 0.63f, 2), -p.Y - 0.46f, p.Z));
                Add(hang, fang, Mat("#efe4c8", 0, 0.38f));
                var wraps = new Build();
                foreach (float y in new[] { -0.49f, -0.53f })
                    Tube(wraps, Circle(new Vector3(0.002f, y, 0), 0.106f, Vector3.Right, Vector3.Back, 20), 0.009f, 5, true);
                Add(hang, wraps, Gold());
                break;
            }
            case "bone":
            {
                var bone = new Build();
                Lathe(bone, Pts(0, 0, 0.08f, 0.005f, 0.105f, 0.04f, 0.1f, 0.09f, 0.065f, 0.14f, 0.055f, 0.22f, 0.065f, 0.3f, 0.1f, 0.35f, 0.105f, 0.4f, 0.08f, 0.435f, 0, 0.44f), 18,
                    warp: p => new Vector3(-p.X + Mathf.Sin(p.Y * 20) * 0.01f, -p.Y - 0.455f, p.Z * 0.8f));
                Add(hang, bone, Bone());
                break;
            }
            default:
            {
                var moon = new Build();
                Extrude(moon, Crescent(0.2f, 0.17f, 0.09f), 0.045f, 0.012f, At(new Basis(Vector3.Back, 0.5f), 0.03f, -0.63f, 0));
                var m = Silver();
                m.EmissionEnabled = true; m.Emission = new Color("#9ac0ff"); m.EmissionEnergyMultiplier = 0.15f;
                Add(hang, moon, m);
                var gem = new Build();
                Lathe(gem, Pts(0.045f, 0, 0.042f, 0.018f, 0.028f, 0.034f, 0, 0.04f), 10, At(Facing, -0.03f, -0.57f, 0.015f));
                Add(hang, gem.Faceted(), Gem("#bfe0ff", 0.8f));
                break;
            }
        }
        return root;
    }

    /// <summary>A hide pegged out flat the way a trapper stretches it:
    /// four legs, a head, a tail, draped a little; fur up, the flesh side
    /// pale under it.</summary>
    static Node3D Pelt(Color light, Color dark, float coarse)
    {
        var root = new Node3D();
        var half = Pts(0, 0.86f, 0.1f, 0.8f, 0.13f, 0.62f, 0.28f, 0.52f, 0.56f, 0.66f, 0.72f, 0.58f, 0.62f, 0.48f, 0.38f, 0.34f,
            0.34f, 0.05f, 0.37f, -0.22f, 0.62f, -0.36f, 0.74f, -0.5f, 0.6f, -0.54f, 0.3f, -0.46f, 0.11f, -0.56f, 0.07f, -0.9f, 0, -0.96f);
        var outline = new List<Vector2>(half);
        for (int i = half.Length - 2; i >= 1; i--) outline.Add(new Vector2(-half[i].X, half[i].Y));
        var face = new Build();
        var back = new Build();
        Sheet(face, back, outline.ToArray(), 0.05f, 0.05f,
            p => new Vector3(p.X, p.Y, p.Z + Mathf.Sin(p.X * 4.5f) * 0.035f + Mathf.Cos(p.Y * 5) * 0.03f - Mathf.Abs(p.X) * 0.12f));
        var (albedo, normal) = Fur(light, dark, coarse);
        Add(root, face, new StandardMaterial3D
        {
            AlbedoTexture = albedo, NormalEnabled = true, NormalTexture = normal, Roughness = 1, RimEnabled = true, Rim = 0.6f, RimTint = 0.8f,
        }, true);
        Add(root, back, Mat("#c9a57c", 0, 0.85f));
        return root;
    }

    /* --------------------------------------------------------- garments -- */

    /// <summary>A garment's cut from half of it: from the middle of the
    /// neck, round the shoulder, down the side to the middle of the hem.</summary>
    static Vector2[] Cut(params float[] half)
    {
        var h = Pts(half);
        var l = new List<Vector2>(h);
        for (int i = h.Length - 2; i >= 1; i--) l.Add(new Vector2(-h[i].X, h[i].Y));
        return l.ToArray();
    }

    /// <summary>How far out from the middle a cut reaches at a height.</summary>
    static float HalfWidth(Vector2[] ring, float y)
    {
        float w = 0.05f;
        for (int i = 0; i < ring.Length; i++)
        {
            Vector2 a = ring[i], b = ring[(i + 1) % ring.Length];
            if (a.Y == b.Y || (a.Y - y) * (b.Y - y) > 0) continue;
            w = Mathf.Max(w, Mathf.Abs(Mathf.Lerp(a.X, b.X, (y - a.Y) / (b.Y - a.Y))));
        }
        return w;
    }

    /// <summary>A point of a flat cut, worn: wrapped round a body so its
    /// sides meet the other half's, fuller at the breast in front; a ridge
    /// down the middle for plate. The back half is turned round to face away.</summary>
    static Vector3 Worn(Vector2[] ring, Vector3 p, float depth, bool front, float ridge = 0)
    {
        float w = Mathf.Clamp(p.X / (HalfWidth(ring, p.Y) + 0.001f), -1, 1);
        float round = Mathf.Sqrt(Mathf.Max(0, 1 - w * w));
        float chest = front ? 1 + 0.2f * Mathf.Exp(-Mathf.Pow((p.Y - 0.25f) / 0.2f, 2)) : 1;
        float z = depth * round * chest + ridge * Mathf.Max(0, 1 - Mathf.Abs(p.X) / 0.1f) * round + p.Z;
        return front ? new Vector3(p.X, p.Y, z) : new Vector3(-p.X, p.Y, -z);
    }

    /// <summary>A garment's front and back, sewn at the sides and shoulders:
    /// outside and lining.</summary>
    static void Garment(Build outside, Build lining, Vector2[] front, Vector2[] back, float thick, float ridge = 0)
    {
        Sheet(outside, lining, front, 0.035f, thick, p => Worn(front, p, 0.24f, true, ridge));
        Sheet(outside, lining, back, 0.035f, thick, p => Worn(back, p, 0.2f, false));
    }

    /// <summary>Along a garment's edge (between two heights on one side, or
    /// across), on its outside.</summary>
    static List<Vector3> Along(Vector2[] ring, IEnumerable<Vector2> pts, float lift) =>
        new(System.Linq.Enumerable.Select(pts, q => Worn(ring, new Vector3(q.X, q.Y, lift), 0.24f, true)));

    /// <summary>n points along f(t) in a flat cut, t from 0 to 1.</summary>
    static List<Vector2> Flat(int n, Func<float, Vector2> f)
    {
        var l = new List<Vector2>(n);
        for (int i = 0; i < n; i++) l.Add(f((float)i / (n - 1)));
        return l;
    }

    static Vector2[] Jerkin(float neck) => Cut(0, neck, 0.13f, 0.6f, 0.3f, 0.62f, 0.44f, 0.55f, 0.43f, 0.38f, 0.35f, 0.24f, 0.34f, -0.05f, 0.36f, -0.4f, 0.34f, -0.6f, 0, -0.62f);

    /// <summary>A mail shirt: steel rings on rings, a leather collar.</summary>
    static Node3D Mail()
    {
        var root = new Node3D();
        var outside = new Build();
        var lining = new Build();
        var front = Jerkin(0.46f);
        Garment(outside, lining, front, Jerkin(0.56f), 0.03f);
        var (albedo, normal) = Shapes.Mail();
        Add(root, outside, new StandardMaterial3D
        {
            AlbedoColor = new Color("#b8bcc4"), AlbedoTexture = albedo, NormalEnabled = true, NormalTexture = normal, Uv1Scale = new Vector3(7, 7, 1),
            Metallic = 0.9f, Roughness = 0.38f,
        }, true);
        Add(root, lining, Mat("#3a2e24", 0, 0.9f));
        var trim = new Build();
        Tube(trim, Along(front, Flat(16, t => new Vector2(Mathf.Lerp(-0.13f, 0.13f, t), 0.46f + 0.14f * Mathf.Abs(t - 0.5f) * 2)), 0.02f), 0.028f, 6);
        Add(root, trim, Mat("#4a3322", 0, 0.6f));
        return root;
    }

    /// <summary>A padded jerkin: quilted linen, laced up the front.</summary>
    static Node3D Jerkin()
    {
        var root = new Node3D();
        var outside = new Build();
        var lining = new Build();
        var front = Jerkin(0.4f);
        Garment(outside, lining, front, Jerkin(0.56f), 0.05f);
        var (albedo, normal) = Quilt();
        Add(root, outside, new StandardMaterial3D
        {
            AlbedoColor = new Color("#9a8460"), AlbedoTexture = albedo, NormalEnabled = true, NormalTexture = normal, Uv1Scale = new Vector3(3, 3, 1),
            Roughness = 0.95f, RimEnabled = true, Rim = 0.3f, RimTint = 0.7f,
        }, true);
        Add(root, lining, Mat("#5a4a36", 0, 0.95f));
        var lace = new Build();
        var cross = new List<Vector2>();
        for (int k = 0; k <= 8; k++) cross.Add(new Vector2(k % 2 == 0 ? -0.05f : 0.05f, 0.36f - k * 0.055f));
        Tube(lace, Along(front, cross, 0.035f), 0.012f, 5);
        Add(root, lace, Mat("#3a2616", 0, 0.8f));
        return root;
    }

    /// <summary>The Ashen Plate: a blackened breastplate, ridged, riveted,
    /// its lames and pauldrons, embers still in its seams.</summary>
    static Node3D Plate()
    {
        var root = new Node3D();
        var outside = new Build();
        var lining = new Build();
        var front = Cut(0, 0.48f, 0.14f, 0.58f, 0.28f, 0.6f, 0.42f, 0.52f, 0.4f, 0.36f, 0.32f, 0.22f, 0.31f, -0.05f, 0.33f, -0.2f, 0, -0.24f);
        var back = Cut(0, 0.56f, 0.14f, 0.6f, 0.28f, 0.6f, 0.42f, 0.52f, 0.4f, 0.36f, 0.32f, 0.22f, 0.31f, -0.05f, 0.33f, -0.2f, 0, -0.24f);
        Garment(outside, lining, front, back, 0.04f, 0.03f);
        // Lames below, each a little wider and overlapping the one above.
        for (int k = 0; k < 3; k++)
        {
            float top = -0.2f - k * 0.1f, w = 0.34f + k * 0.025f;
            var lame = Pts(-w, top, w, top, w + 0.01f, top - 0.13f, -w - 0.01f, top - 0.13f);
            Sheet(outside, lining, lame, 0.035f, 0.03f, p => Worn(lame, p, 0.26f + k * 0.01f, true));
        }
        var steel = new StandardMaterial3D { AlbedoColor = new Color("#34312e"), Metallic = 0.85f, Roughness = 0.34f };
        Add(root, outside, steel);
        Add(root, lining, Mat("#2a2018", 0, 0.9f));
        var pauldrons = new Build();
        foreach (float sx in new[] { -1f, 1f })
            for (int k = 0; k < 3; k++)
                Lathe(pauldrons, Pts(0.21f - k * 0.02f, -0.02f, 0.21f - k * 0.02f, 0.02f, 0.18f - k * 0.02f, 0.1f, 0.1f, 0.16f - k * 0.01f, 0, 0.18f - k * 0.01f), 24,
                    new Transform3D(new Basis(Vector3.Back, -sx * (0.5f + k * 0.25f)) * Basis.FromScale(new Vector3(1, 0.8f, 0.9f)), new Vector3(sx * (0.43f + k * 0.04f), 0.5f - k * 0.08f, 0)));
        Add(root, pauldrons, steel);
        var rivets = new Build();
        foreach (var q in Along(front, Flat(9, t => new Vector2(Mathf.Lerp(-0.28f, 0.28f, t), -0.18f)), 0.025f)) rivets.Append(Rivet(), At(q.X, q.Y, q.Z));
        Add(root, rivets, Brass());
        var embers = new Build();
        Tube(embers, Along(front, Flat(14, t => new Vector2(Mathf.Lerp(-0.3f, 0.3f, t), -0.215f)), 0.03f), 0.008f, 4);
        Tube(embers, Along(front, Flat(12, t => new Vector2(Mathf.Lerp(-0.11f, 0.11f, t), 0.5f + 0.07f * Mathf.Abs(t - 0.5f) * 2)), 0.03f), 0.007f, 4);
        Add(root, embers, Glow("#ff6a10", 2.2f));
        return root;
    }

    /// <summary>A traveller's cloak of grey wool hanging open from the
    /// shoulders, the lining darker, a clasp and chain at the throat.</summary>
    static Node3D Cloak()
    {
        var root = new Node3D();
        var wool = new Build();
        var lining = new Build();
        // Round the back of the neck and down, widening; folds deepening toward the hem.
        Vector3 Hang(Vector3 p)
        {
            float v = (0.8f - p.Y) / 1.6f, a = -p.X * 1.75f;
            float r = 0.26f + 0.44f * v + 0.04f * v * Mathf.Sin(p.X * 21) + p.Z;
            return new Vector3(r * Mathf.Sin(a), p.Y, -r * Mathf.Cos(a));
        }
        Sheet(wool, lining, Pts(-1, 0.8f, 1, 0.8f, 1, -0.8f, -1, -0.8f), 0.05f, 0.03f, Hang);
        Add(root, wool, Cloth("#4e4a46", false, 8));
        Add(root, lining, Cloth("#2a2220", false, 8));
        // The hood, down, lying over the shoulders at the back.
        var hood = new Build();
        Lathe(hood, Pts(0.25f, 0, 0.27f, 0.1f, 0.23f, 0.22f, 0.12f, 0.31f, 0, 0.33f), 28, warp: p => new Vector3(p.X, p.Y * 0.9f, p.Z * 1.15f));
        Add(root, hood.Mesh(), Cloth("#4a4642", true, 6), new Transform3D(new Basis(Vector3.Right, -1.2f), new Vector3(0, 0.74f, -0.26f)));
        var collar = new Build();
        Tube(collar, Shapes.Path(24, t => Hang(new Vector3(Mathf.Lerp(-1, 1, t), 0.79f, 0.03f))), 0.045f, 8);
        Add(root, collar, Cloth("#3e3a36", false, 4));
        var clasp = new Build();
        foreach (float sx in new[] { -1f, 1f })
        {
            var at = Hang(new Vector3(sx, 0.76f, 0.04f));
            Lathe(clasp, Pts(0.06f, 0, 0.065f, 0.012f, 0.04f, 0.03f, 0, 0.035f), 18, new Transform3D(new Basis(Vector3.Up, sx * 0.35f) * Facing, at));
        }
        Chain(clasp, Hang(new Vector3(-1, 0.74f, 0.05f)), Hang(new Vector3(1, 0.74f, 0.05f)), 0.03f, 0.007f);
        Add(root, clasp, Brass());
        return root;
    }

    /// <summary>An iron helm: a dome dented in service, a riveted rim, bands
    /// over the crown, a nasal guard.</summary>
    static Node3D Helm()
    {
        var root = new Node3D();
        var prof = Pts(0.37f, -0.3f, 0.375f, -0.12f, 0.355f, 0.05f, 0.3f, 0.19f, 0.2f, 0.31f, 0.09f, 0.38f, 0, 0.4f);
        static Vector3 Oval(Vector3 p) => new(p.X * 0.92f, p.Y, p.Z * 1.06f);
        var dome = new Build();
        Lathe(dome, prof, 48, warp: p => Oval(p) * (1 - Mathf.Max(0, Noise(p.X * 5 + 7, p.Y * 5 + p.Z * 3) - 0.62f) * 0.12f));
        var steel = Mat("#86847e", 0.9f, 0.38f, true);
        Add(root, dome, steel);
        var iron = new Build();
        Tube(iron, Shapes.Path(48, t => Oval(new Vector3(0.378f * Mathf.Sin(t * Mathf.Tau), -0.27f, 0.378f * Mathf.Cos(t * Mathf.Tau))), true), 0.032f, 8, true);
        for (int k = 0; k < 4; k++)
        {
            float a = k * Mathf.Pi / 2 + Mathf.Pi / 4;
            Tube(iron, Shapes.Path(14, t =>
            {
                float y = Mathf.Lerp(-0.25f, 0.39f, t), r = RadiusAt(prof, y) + 0.01f;
                return Oval(new Vector3(r * Mathf.Sin(a), y, r * Mathf.Cos(a)));
            }), t => 0.024f * (1 - 0.5f * t), 6);
        }
        for (int k = 0; k < 16; k++)
        {
            float a = k * Mathf.Tau / 16;
            var dir = Oval(new Vector3(Mathf.Sin(a), 0, Mathf.Cos(a))).Normalized();
            iron.Append(Rivet(), new Transform3D(new Basis(Vector3.Up, a) * new Basis(Vector3.Right, -Mathf.Pi / 2) * new Basis(Vector3.Right, Mathf.Pi / 2), Oval(new Vector3(0.41f * Mathf.Sin(a), -0.27f, 0.41f * Mathf.Cos(a)))));
        }
        Extrude(iron, Pts(-0.035f, -0.44f, 0.035f, -0.44f, 0.045f, 0, -0.045f, 0), 0.025f, 0.007f, At(new Basis(Vector3.Right, -0.1f), 0, -0.14f, 0.41f));
        Add(root, iron, Mat("#5a5854", 0.9f, 0.45f));
        return root;
    }

    /// <summary>A leather cap: panels stitched over the crown, a rolled brim.</summary>
    static Node3D Cap()
    {
        var root = new Node3D();
        var prof = Pts(0.35f, -0.18f, 0.36f, -0.05f, 0.33f, 0.08f, 0.26f, 0.2f, 0.14f, 0.28f, 0, 0.3f);
        static Vector3 Oval(Vector3 p) => new(p.X * 0.93f, p.Y, p.Z * 1.05f);
        var leather = new Build();
        Lathe(leather, prof, 40, warp: p => Oval(p) * (1 + (Noise(p.X * 6, p.Z * 6 + p.Y * 4) - 0.5f) * 0.03f));
        Tube(leather, Shapes.Path(40, t => Oval(new Vector3(0.36f * Mathf.Sin(t * Mathf.Tau), -0.18f, 0.36f * Mathf.Cos(t * Mathf.Tau))), true), 0.035f, 8, true);
        Lathe(leather, Pts(0.04f, 0.29f, 0.045f, 0.31f, 0.03f, 0.335f, 0, 0.34f), 12);
        Add(root, leather, Mat("#5a3c24", 0, 0.62f, true));
        var seams = new Build();
        for (int k = 0; k < 6; k++)
        {
            float a = k * Mathf.Tau / 6;
            Tube(seams, Shapes.Path(14, t =>
            {
                float y = Mathf.Lerp(-0.14f, 0.29f, t), r = RadiusAt(prof, y) + 0.006f;
                return Oval(new Vector3(r * Mathf.Sin(a), y, r * Mathf.Cos(a)));
            }), 0.009f, 5);
        }
        Add(root, seams, Mat("#3a2616", 0, 0.8f));
        return root;
    }

    /// <summary>The radius of a lathe profile at a height.</summary>
    static float RadiusAt(Vector2[] prof, float y)
    {
        for (int i = 1; i < prof.Length; i++)
            if ((prof[i - 1].Y - y) * (prof[i].Y - y) <= 0 && prof[i].Y != prof[i - 1].Y)
                return Mathf.Lerp(prof[i - 1].X, prof[i].X, (y - prof[i - 1].Y) / (prof[i].Y - prof[i - 1].Y));
        return 0;
    }

    /* ------------------------------------------------------------ carried -- */

    /// <summary>A brass censer, embers glowing through its pierced lid, on three chains.</summary>
    static Node3D Censer()
    {
        var root = new Node3D();
        var brass = new Build();
        Lathe(brass, Pts(0, -0.55f, 0.2f, -0.55f, 0.2f, -0.55f, 0.21f, -0.5f, 0.09f, -0.45f, 0.08f, -0.38f, 0.28f, -0.3f, 0.39f, -0.16f, 0.42f, -0.02f, 0.45f, 0), 40);
        Lathe(brass, Pts(0.45f, 0.02f, 0.44f, 0.06f, 0.37f, 0.2f, 0.25f, 0.32f, 0.11f, 0.38f, 0.07f, 0.44f, 0.09f, 0.5f, 0.05f, 0.56f, 0, 0.58f), 40);
        for (int k = 0; k < 3; k++)
        {
            float a = Mathf.Pi / 2 + k * Mathf.Tau / 3;
            Chain(brass, new Vector3(0.44f * Mathf.Cos(a), 0.03f, 0.44f * Mathf.Sin(a)), new Vector3(0, 1.0f, 0), 0.04f, 0.009f);
        }
        Tube(brass, Circle(new Vector3(0, 1.06f, 0), 0.07f, Vector3.Right, Vector3.Up, 20), 0.015f, 6, true);
        Add(root, brass, Brass());
        var vents = new Build();
        for (int ring = 0; ring < 2; ring++)
        {
            float y = ring == 0 ? 0.14f : 0.27f, r = ring == 0 ? 0.405f : 0.29f;
            int n = ring == 0 ? 12 : 8;
            for (int k = 0; k < n; k++)
            {
                float a = (k + ring * 0.5f) * Mathf.Tau / n;
                Lathe(vents, Pts(0.028f, 0, 0.018f, 0.012f, 0, 0.014f), 8,
                    new Transform3D(new Basis(Vector3.Up, -a) * new Basis(Vector3.Back, -Mathf.Pi / 2 + (ring == 0 ? 0.5f : 0.8f)), new Vector3(r * Mathf.Cos(a), y, r * Mathf.Sin(a))));
            }
        }
        Add(root, vents, Glow("#ff8a3a", 3.5f));
        return root;
    }

    /// <summary>A miner's lamp: a brass font, a glass chimney in a wire
    /// guard, a flame, a bail to hang it by.</summary>
    static Node3D Lamp()
    {
        var root = new Node3D();
        var brass = new Build();
        Lathe(brass, Pts(0, -0.5f, 0.3f, -0.5f, 0.3f, -0.5f, 0.32f, -0.46f, 0.3f, -0.32f, 0.22f, -0.24f, 0.15f, -0.2f, 0.15f, -0.2f, 0.15f, -0.17f, 0, -0.17f), 40);
        Lathe(brass, Pts(0.13f, 0.38f, 0.17f, 0.4f, 0.16f, 0.44f, 0.09f, 0.5f, 0, 0.52f), 24);
        Add(root, brass, Brass());
        var glass = new Build();
        Lathe(glass, Pts(0.14f, -0.17f, 0.2f, -0.05f, 0.22f, 0.1f, 0.19f, 0.28f, 0.12f, 0.38f), 40);
        Add(root, glass, Glass("#1a140c", 0.16f));
        var wire = new Build();
        for (int k = 0; k < 4; k++)
        {
            float a = Mathf.Pi / 4 + k * Mathf.Pi / 2;
            var d = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
            Tube(wire, new List<Vector3> { d * 0.23f + Vector3.Up * -0.22f, d * 0.27f + Vector3.Up * 0.1f, d * 0.16f + Vector3.Up * 0.41f }, 0.012f, 5);
        }
        Tube(wire, Circle(new Vector3(0, 0.1f, 0), 0.268f, Vector3.Right, Vector3.Back, 32), 0.012f, 5, true);
        Tube(wire, Path(16, t => new Vector3(-0.16f * Mathf.Cos(t * Mathf.Pi), 0.44f + 0.26f * Mathf.Sin(t * Mathf.Pi), 0)), 0.016f, 6);
        Add(root, wire, Iron());
        var flame = new Build();
        Lathe(flame, Pts(0, -0.14f, 0.045f, -0.1f, 0.06f, -0.03f, 0.04f, 0.06f, 0, 0.15f), 16);
        Add(root, flame, Glow("#ffb050", 4));
        root.AddChild(Light("#ffa050", 2, 1.4f, Vector3.Zero));
        return root;
    }

    /// <summary>A reading glass on a turned handle, cracked across.</summary>
    static Node3D Lens()
    {
        var root = new Node3D();
        var brass = new Build();
        Tube(brass, Circle(Vector3.Zero, 0.45f, Vector3.Right, Vector3.Up, 48), 0.055f, 10, true);
        var handle = new Basis(Vector3.Back, Mathf.Atan2(-0.6f, -0.8f));
        var at = new Vector3(0.6f, -0.8f, 0) * 0.47f;
        Lathe(brass, Pts(0.075f, 0, 0.078f, 0.035f, 0.075f, 0.07f), 16, new Transform3D(handle, at));
        Add(root, brass, Brass());
        var glass = new Build();
        Lathe(glass, Pts(0, -0.035f, 0.44f, -0.01f, 0.44f, 0.01f, 0, 0.035f), 40, At(Facing, 0, 0, 0));
        Add(root, glass, Glass("#0a1420", 0.22f));
        var crack = new Build();
        Tube(crack, new List<Vector3> { new(-0.22f, 0.28f, 0.04f), new(-0.1f, 0.12f, 0.04f), new(-0.02f, 0.1f, 0.04f), new(0.05f, -0.02f, 0.04f), new(0.16f, -0.08f, 0.04f), new(0.3f, -0.26f, 0.04f) }, 0.005f, 4);
        Tube(crack, new List<Vector3> { new(0.05f, -0.02f, 0.04f), new(0.12f, 0.1f, 0.04f), new(0.2f, 0.14f, 0.04f) }, 0.004f, 4);
        Add(root, crack, Glow("#e8f4ff", 0.6f));
        var wood = new Build();
        Lathe(wood, Pts(0, 0.07f, 0.065f, 0.07f, 0.065f, 0.07f, 0.06f, 0.12f, 0.072f, 0.3f, 0.07f, 0.48f, 0.055f, 0.55f, 0.062f, 0.6f, 0, 0.63f), 16, new Transform3D(handle, at), textured: true);
        Add(root, wood, Grain("#8a5e38", "#3e2414"));
        return root;
    }

    /// <summary>A post of lightning-struck oak, carved, banded with light,
    /// a crystal at its crown; the strike's scar still glowing.</summary>
    static Node3D Totem()
    {
        var root = new Node3D();
        var post = new Build();
        Lathe(post, Pts(0, -0.75f, 0.2f, -0.75f, 0.2f, -0.75f, 0.22f, -0.62f, 0.17f, -0.52f, 0.22f, -0.4f, 0.21f, -0.12f, 0.16f, -0.02f, 0.21f, 0.08f, 0.21f, 0.46f, 0.15f, 0.55f, 0.2f, 0.63f, 0.12f, 0.72f, 0, 0.74f), 6, textured: true);
        Add(root, post.Faceted(), Grain("#7a5a3a", "#3a2616", 1, 0.85f));
        var glow = new Build();
        foreach (float y in new[] { 0.28f, -0.26f })
            Tube(glow, Circle(new Vector3(0, y, 0), 0.215f, Vector3.Right, Vector3.Back, 6), 0.026f, 6, true);
        foreach (var (lo, hi) in new[] { (0.1f, 0.44f), (-0.38f, -0.14f) })
            Tube(glow, Path(9, t => new Vector3(0.03f * (((int)(t * 8)) % 2 == 0 ? 1 : -1) * Mathf.Min(1, t * 8), Mathf.Lerp(lo, hi, t), 0.186f)), 0.011f, 5);
        Add(root, glow, Glow("#5a9aff", 0.8f, "#3a6ac0"));
        var crystal = new Build();
        Lathe(crystal, Pts(0, 0, 0.11f, 0.1f, 0.1f, 0.3f, 0, 0.44f), 6, At(0, 0.72f, 0));
        Add(root, crystal.Faceted(), Gem("#9ac8ff", 1.2f));
        return root;
    }

    /// <summary>A burlap pouch tied at the neck, thorny sprigs springing from it, a few seeds spilled.</summary>
    static Node3D SeedPouch()
    {
        var root = new Node3D();
        var sack = new Build();
        Lathe(sack, Pts(0, -0.45f, 0.25f, -0.43f, 0.41f, -0.3f, 0.46f, -0.1f, 0.42f, 0.1f, 0.3f, 0.24f, 0.15f, 0.33f, 0.12f, 0.38f, 0.17f, 0.46f, 0.22f, 0.52f), 40,
            warp: p =>
            {
                float a = Mathf.Atan2(p.Z, p.X);
                float k = 1 + 0.05f * Mathf.Sin(a * 7 + p.Y * 9) * Mathf.Clamp((0.3f - p.Y) * 2, 0, 1) + 0.1f * Mathf.Sin(a * 11) * Mathf.Clamp((p.Y - 0.38f) * 8, 0, 1);
                return new Vector3(p.X * k, p.Y, p.Z * k);
            }, textured: true);
        Add(root, sack, Cloth("#6a5238", true, 5));
        var cord = new Build();
        Tube(cord, Circle(new Vector3(0, 0.37f, 0), 0.13f, Vector3.Right, Vector3.Back, 24), 0.026f, 6, true);
        Tube(cord, new List<Vector3> { new(0.1f, 0.37f, 0.1f), new(0.17f, 0.3f, 0.2f), new(0.2f, 0.18f, 0.26f), new(0.18f, 0.08f, 0.3f) }, 0.02f, 6);
        Tube(cord, new List<Vector3> { new(0.06f, 0.37f, 0.12f), new(0.07f, 0.28f, 0.22f), new(0.04f, 0.16f, 0.28f) }, 0.02f, 6);
        Add(root, cord, Mat("#3a2a18", 0, 0.95f));
        var thorn = new Build();
        foreach (var (dx, dz, h) in new[] { (-0.06f, 0f, 0.85f), (0.05f, 0.03f, 0.75f), (0.0f, -0.05f, 0.68f) })
        {
            var stem = Path(8, t => new Vector3(dx * (1 + t * 3), 0.3f + t * (h - 0.3f), dz * (1 + t * 3) + t * t * 0.05f));
            Tube(thorn, stem, t => 0.018f * (1 - t * 0.6f), 5);
            for (int k = 2; k < 7; k++)
            {
                var p = stem[k];
                float a = k * 2.1f;
                var o = new Vector3(Mathf.Cos(a), 0.4f, Mathf.Sin(a)).Normalized();
                Tube(thorn, new List<Vector3> { p, p + o * 0.07f }, t => 0.012f * (1 - t), 4);
            }
        }
        Add(root, thorn, Mat("#4a5a2a", 0, 0.7f));
        var seeds = new Build();
        foreach (var (x, z, a) in new[] { (0.22f, 0.38f, 0.3f), (0.08f, 0.44f, 1.2f), (0.3f, 0.3f, 2.2f) })
            Lathe(seeds, Pts(0, -0.03f, 0.03f, -0.015f, 0.03f, 0.015f, 0, 0.03f), 10, new Transform3D(Rot(1.4f, a, 0) * Basis.FromScale(new Vector3(1, 1.6f, 1)), new Vector3(x, -0.43f, z)));
        Add(root, seeds, Mat("#3a2616", 0, 0.5f));
        return root;
    }

    /// <summary>A ring of lockpicks: a hook, a rake, a diamond, a tension wrench.</summary>
    static Node3D Picks()
    {
        var root = new Node3D();
        var steel = new Build();
        Tube(steel, Circle(new Vector3(0, 0.45f, 0), 0.2f, Vector3.Right, Vector3.Up, 36), 0.022f, 8, true);
        var picks = new[]
        {
            new List<Vector3> { new(-0.12f, 0.28f, 0), new(-0.14f, -0.4f, 0), new(-0.14f, -0.5f, 0), new(-0.1f, -0.54f, 0) },
            new List<Vector3> { new(0, 0.26f, 0), new(0, -0.3f, 0), new(0.03f, -0.35f, 0), new(-0.02f, -0.4f, 0), new(0.03f, -0.45f, 0), new(-0.02f, -0.5f, 0), new(0, -0.56f, 0) },
            new List<Vector3> { new(0.12f, 0.28f, 0), new(0.14f, -0.38f, 0), new(0.17f, -0.45f, 0), new(0.14f, -0.52f, 0) },
            new List<Vector3> { new(0.2f, 0.34f, 0.01f), new(0.3f, -0.2f, 0.01f), new(0.38f, -0.22f, 0.01f) },
        };
        foreach (var p in picks) Tube(steel, p, 0.016f, 6);
        Add(root, steel, Steel());
        var grips = new Build();
        foreach (var p in picks.AsSpan(0, 3)) Tube(grips, new List<Vector3> { p[0] + Vector3.Down * 0.08f, p[0].Lerp(p[1], 0.35f) }, 0.032f, 8);
        Add(root, grips, Mat("#3a2616", 0, 0.7f));
        return root;
    }

    /// <summary>A small keg of blasting ember, iron-hooped, glowing through
    /// its seams, its fuse lit.</summary>
    static Node3D Bomb()
    {
        var root = new Node3D();
        var keg = new Build();
        Lathe(keg, Pts(0, -0.42f, 0.3f, -0.42f, 0.3f, -0.42f, 0.35f, -0.25f, 0.37f, 0, 0.35f, 0.25f, 0.3f, 0.42f, 0.3f, 0.42f, 0, 0.42f), 32, textured: true);
        var staves = Tex(Paint(256, 128, (u, v) =>
        {
            float s = u * 14, gap = Mathf.Abs(s - Mathf.Round(s));
            var c = new Color("#7a5634").Lerp(new Color("#4a321e"), Noise(u * 40, v * 3) * 0.7f + ((int)s % 3) * 0.1f);
            return gap < 0.04f ? c.Darkened(0.6f) : c;
        }));
        Add(root, keg, new StandardMaterial3D { AlbedoTexture = staves, Roughness = 0.75f });
        var hoops = new Build();
        foreach (var (y, r) in new[] { (0.33f, 0.335f), (-0.33f, 0.335f), (0.12f, 0.368f), (-0.12f, 0.368f) })
            Tube(hoops, Circle(new Vector3(0, y, 0), r, Vector3.Right, Vector3.Back, 40), 0.018f, 5, true);
        Add(root, hoops, Iron());
        var cracks = new Build();
        foreach (var (a0, lo, hi) in new[] { (1.5f, -0.3f, -0.14f), (1.75f, 0.14f, 0.3f), (1.3f, -0.1f, 0.1f) })
            Tube(cracks, Path(7, t =>
            {
                float y = Mathf.Lerp(lo, hi, t), a = a0 + 0.06f * ((int)(t * 6) % 2 == 0 ? 1 : -1);
                float r = 0.37f - Mathf.Abs(y) * 0.12f + 0.004f;
                return new Vector3(r * Mathf.Cos(a), y, r * Mathf.Sin(a));
            }), 0.009f, 4);
        Add(root, cracks, Glow("#ff7a20", 3.5f));
        var fuse = new Build();
        Tube(fuse, new List<Vector3> { new(0.1f, 0.4f, 0), new(0.14f, 0.55f, 0.05f), new(0.1f, 0.68f, 0.1f), new(0.16f, 0.78f, 0.12f) }, 0.018f, 6);
        Add(root, fuse, Mat("#4a3a28", 0, 0.9f));
        Add(root, Ball(0.035f), Glow("#ffd080", 5), At(0.16f, 0.8f, 0.12f));
        root.AddChild(Light("#ff9a40", 1.2f, 1.2f, new Vector3(0.16f, 0.8f, 0.2f)));
        return root;
    }

    /// <summary>An iron key: a ring bow, a collared shank, a cut bit.</summary>
    static Node3D Key()
    {
        var root = new Node3D();
        var iron = new Build();
        Tube(iron, Circle(new Vector3(0, 0.44f, 0), 0.15f, Vector3.Right, Vector3.Up, 32), 0.035f, 8, true);
        Lathe(iron, Pts(0, -0.52f, 0.04f, -0.52f, 0.04f, -0.52f, 0.04f, 0.2f, 0.07f, 0.22f, 0.07f, 0.26f, 0.045f, 0.28f, 0.045f, 0.3f, 0, 0.3f), 12);
        Extrude(iron, Pts(0, 0, 0.2f, 0, 0.2f, 0.05f, 0.14f, 0.05f, 0.14f, 0.09f, 0.2f, 0.09f, 0.2f, 0.16f, 0, 0.16f), 0.05f, 0.008f, At(0.02f, -0.52f, 0));
        Add(root, iron, Mat("#6a6258", 0.85f, 0.42f));
        return root;
    }

    /// <summary>A strongbox: planked wood, iron-banded and cornered, a brass lock plate.</summary>
    static Node3D Chest()
    {
        var root = new Node3D();
        var wood = Grain("#8a6a48", "#4a3420", 3, 0.75f);
        var iron = Iron();
        Add(root, new BoxMesh { Size = new Vector3(1.0f, 0.5f, 0.6f) }, wood);
        Add(root, new BoxMesh { Size = new Vector3(1.02f, 0.16f, 0.62f) }, wood, At(0, 0.33f, 0));
        foreach (float x in new[] { -0.32f, 0.32f }) Add(root, new BoxMesh { Size = new Vector3(0.07f, 0.68f, 0.625f) }, iron, At(x, 0.08f, 0));
        Add(root, new BoxMesh { Size = new Vector3(1.03f, 0.04f, 0.63f) }, iron, At(0, 0.25f, 0));
        foreach (float x in new[] { -0.49f, 0.49f })
            foreach (float y in new[] { -0.23f, 0.39f })
                foreach (float z in new[] { -0.29f, 0.29f })
                    Add(root, new BoxMesh { Size = new Vector3(0.08f, 0.08f, 0.08f) }, iron, At(x, y, z));
        Add(root, new BoxMesh { Size = new Vector3(0.2f, 0.22f, 0.03f) }, Brass(), At(0, 0.18f, 0.31f));
        Add(root, new BoxMesh { Size = new Vector3(0.03f, 0.07f, 0.01f) }, Mat("#0a0806"), At(0, 0.15f, 0.327f));
        Add(root, new BoxMesh { Size = new Vector3(0.08f, 0.14f, 0.03f) }, iron, At(0, 0.33f, 0.325f));
        var rivets = new Build();
        foreach (float x in new[] { -0.32f, 0.32f })
            foreach (float y in new[] { -0.15f, 0.05f, 0.33f })
                rivets.Append(Rivet(), At(x, y, 0.313f));
        Add(root, rivets, iron);
        return root;
    }

    /* ----------------------------------------------------------- gathered -- */

    /// <summary>A cluster of ember crystals on a lump of dark rock, lit from within.</summary>
    static Node3D Ember()
    {
        var root = new Node3D();
        var one = new Build();
        Lathe(one, Pts(0, 0, 0.12f, 0.03f, 0.13f, 0.5f, 0, 0.74f), 6);
        var cluster = new Build();
        cluster.Append(one, At(0, -0.42f, 0));
        cluster.Append(one, At(Rot(0, 0.4f, 0.55f).Scaled(Vector3.One * 0.7f), -0.12f, -0.45f, 0.02f));
        cluster.Append(one, At(Rot(0, 1.1f, -0.45f).Scaled(Vector3.One * 0.6f), 0.12f, -0.45f, -0.03f));
        cluster.Append(one, At(Rot(-0.45f, 0.2f, 0.1f).Scaled(Vector3.One * 0.5f), 0.02f, -0.45f, -0.1f));
        Add(root, cluster.Faceted(), new StandardMaterial3D
        {
            AlbedoColor = new Color("#c85a1a"), Roughness = 0.12f, EmissionEnabled = true, Emission = new Color("#ff5a08"), EmissionEnergyMultiplier = 0.55f,
        });
        var rock = new Build();
        Lathe(rock, Pts(0, -0.56f, 0.26f, -0.54f, 0.3f, -0.46f, 0.2f, -0.4f, 0, -0.38f), 9,
            warp: p => p + new Vector3(0, (Noise(p.X * 9, p.Z * 9) - 0.5f) * 0.06f, 0));
        Add(root, rock.Faceted(), Mat("#2e2622", 0, 0.8f));
        root.AddChild(Light("#ff8a2a", 0.8f, 1.2f, new Vector3(0, -0.2f, 0.25f)));
        return root;
    }

    /// <summary>Old iron for the forge: bent nails, a buckle, a blade's broken half, all of it
    /// gone brown at the edges.</summary>
    static Node3D OldIron()
    {
        var root = new Node3D();
        var nails = new Build();
        Tube(nails, new List<Vector3> { new(-0.4f, -0.44f, 0.06f), new(-0.08f, -0.36f, 0.1f), new(0.02f, -0.16f, 0.08f) }, 0.026f, 6);
        Tube(nails, new List<Vector3> { new(0.08f, -0.48f, -0.04f), new(0.34f, -0.4f, 0.03f), new(0.42f, -0.18f, 0.0f) }, 0.026f, 6);
        Tube(nails, new List<Vector3> { new(-0.34f, -0.3f, -0.12f), new(-0.14f, -0.1f, -0.1f) }, 0.022f, 6);
        // The nails' heads: flat discs at one end of each.
        Lathe(nails, Pts(0, 0, 0.06f, 0, 0.06f, 0.02f, 0, 0.03f), 10, At(-0.4f, -0.45f, 0.06f));
        Lathe(nails, Pts(0, 0, 0.06f, 0, 0.06f, 0.02f, 0, 0.03f), 10, At(0.08f, -0.49f, -0.04f));
        // A buckle's ring.
        Tube(nails, Path(28, t => { float a = Mathf.Tau * t; return new Vector3(0.17f * Mathf.Cos(a) - 0.04f, -0.42f, 0.17f * Mathf.Sin(a) + 0.14f); }, true), 0.026f, 6, true);
        Add(root, nails, Mat("#4a423c", 0.65f, 0.6f));
        var blade = new Build();
        Extrude(blade, Pts(-0.05f, -0.1f, 0.07f, -0.12f, 0.05f, 0.38f, 0.0f, 0.5f, -0.06f, 0.32f), 0.03f, 0.01f, At(Rot(-1.25f, 0.5f, 0.2f), 0.12f, -0.36f, -0.12f));
        Add(root, blade, Mat("#837870", 0.85f, 0.32f));
        return root;
    }

    /// <summary>A shard of black stone, cut to fit a door, a rune inlaid in light.</summary>
    static Node3D Sigil()
    {
        var root = new Node3D();
        var stone = new Build();
        Extrude(stone, Pts(-0.32f, -0.5f, 0.3f, -0.52f, 0.36f, -0.1f, 0.3f, 0.18f, 0.38f, 0.34f, 0.12f, 0.56f, -0.05f, 0.4f, -0.2f, 0.52f, -0.36f, 0.2f, -0.3f, -0.05f), 0.14f, 0.03f);
        Add(root, stone, new StandardMaterial3D { AlbedoColor = new Color("#18161c"), Metallic = 0.35f, Roughness = 0.28f });
        var rune = new Build();
        Tube(rune, Path(28, t => { float a = Mathf.DegToRad(200 + 300 * t); return new Vector3(0.18f * Mathf.Cos(a), 0.02f + 0.18f * Mathf.Sin(a), 0.07f); }), 0.012f, 5);
        Tube(rune, new List<Vector3> { new(0, -0.28f, 0.07f), new(0, 0.3f, 0.07f) }, 0.012f, 5);
        Tube(rune, new List<Vector3> { new(-0.1f, 0.34f, 0.07f), new(0, 0.24f, 0.07f), new(0.1f, 0.34f, 0.07f) }, 0.012f, 5);
        Add(root, rune, Glow("#9a6aff", 1.4f, "#6a3ad0"));
        return root;
    }

    /// <summary>A gnarled root with its rootlets, leaves at its crown.</summary>
    static Node3D Root()
    {
        var root = new Node3D();
        var bark = new Build();
        var main = Path(24, t => new Vector3(0.06f * Mathf.Sin(t * 9), 0.72f - t * 1.5f, 0.04f * Mathf.Cos(t * 7)));
        Tube(bark, main, t => 0.13f * Mathf.Pow(1 - t, 0.9f) + 0.012f + 0.012f * Mathf.Sin(t * 40), 9);
        foreach (var (at, a, len) in new[] { (7, 0.6f, 0.4f), (11, 2.4f, 0.35f), (14, 4.2f, 0.3f), (18, 1.2f, 0.25f) })
        {
            var from = main[at];
            var d = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
            Tube(bark, Path(8, t => from + d * (len * t) + Vector3.Down * (len * 0.8f * t * t) + d.Cross(Vector3.Up) * (0.05f * Mathf.Sin(t * 6))), t => 0.035f * (1 - t) + 0.004f, 6);
        }
        Add(root, bark, new StandardMaterial3D { AlbedoTexture = Wood(new Color("#9a7a52"), new Color("#5a4028")), Roughness = 0.9f, Uv1Scale = new Vector3(1, 3, 1) });
        var green = new Build();
        Tube(green, new List<Vector3> { new(0, 0.7f, 0), new(0.01f, 0.84f, 0.01f), new(0.03f, 0.95f, 0) }, 0.02f, 6);
        var leaf = new Build();
        Sheet(leaf, null, Leaf, 0.02f, 0, p => new Vector3(p.X, p.Y, p.Z + p.X * p.X * 6));
        foreach (var (a, tip) in new[] { (0.2f, 0.9f), (2.3f, 0.8f), (4.2f, 1.0f) })
            green.Append(leaf, new Transform3D(new Basis(Vector3.Up, a) * new Basis(Vector3.Right, -tip) * Basis.FromScale(Vector3.One * 1.6f), new Vector3(0, 0.84f, 0)));
        Add(root, green, Mat("#5a8a3a", 0, 0.6f, true));
        return root;
    }

    /// <summary>A moonpetal in bloom: pale petals that glow, a golden heart.</summary>
    static Node3D Flower()
    {
        var root = new Node3D();
        var petal = new Build();
        Sheet(petal, null, Pts(0, 0, 0.12f, 0.1f, 0.14f, 0.28f, 0.08f, 0.42f, 0, 0.46f, -0.08f, 0.42f, -0.14f, 0.28f, -0.12f, 0.1f), 0.03f, 0,
            p => new Vector3(p.X, p.Y, p.Z + p.X * p.X * 4 + p.Y * p.Y * 0.4f));
        var bloom = new Build();
        for (int k = 0; k < 6; k++)
            bloom.Append(petal, new Transform3D(new Basis(Vector3.Up, k * Mathf.Tau / 6) * new Basis(Vector3.Right, -(Mathf.Pi / 2 - 0.6f)), Vector3.Zero));
        for (int k = 0; k < 5; k++)
            bloom.Append(petal, new Transform3D(new Basis(Vector3.Up, (k + 0.5f) * Mathf.Tau / 5) * new Basis(Vector3.Right, -(Mathf.Pi / 2 - 1.05f)) * Basis.FromScale(Vector3.One * 0.7f), new Vector3(0, 0.02f, 0)));
        Add(root, bloom, new StandardMaterial3D
        {
            AlbedoColor = new Color("#7088c0"), Roughness = 0.45f, EmissionEnabled = true, Emission = new Color("#4a6ac0"), EmissionEnergyMultiplier = 0.3f,
            CullMode = BaseMaterial3D.CullModeEnum.Disabled,
        });
        var heart = new Build();
        for (int k = 0; k < 9; k++)
        {
            float a = k * Mathf.Tau / 9;
            var tip = new Vector3(0.09f * Mathf.Cos(a), 0.16f, 0.09f * Mathf.Sin(a));
            Tube(heart, new List<Vector3> { Vector3.Zero, tip * 0.6f + Vector3.Up * 0.02f, tip }, 0.006f, 4);
            heart.Append(Rivet(), new Transform3D(Basis.Identity.Scaled(Vector3.One * 0.6f), tip));
        }
        Add(root, heart, Glow("#fff2b0", 1.4f));
        Add(root, Ball(0.06f), Glow("#ffe890", 1.2f), At(0, 0.03f, 0));
        var stem = new Build();
        Tube(stem, Path(10, t => new Vector3(0.1f * t * t, -0.85f * t, 0.05f * t)), 0.022f, 6);
        stem.Append(Leafed(), At(0.03f, -0.45f, 0.02f));
        Add(root, stem, Mat("#4a7a3a", 0, 0.6f, true));
        return root;
    }

    static Build Leafed()
    {
        var b = new Build();
        Sheet(b, null, Leaf, 0.02f, 0, p => new Vector3(p.X, p.Y, p.Z + p.X * p.X * 5));
        var o = new Build();
        o.Append(b, new Transform3D(new Basis(Vector3.Back, -1.0f) * Basis.FromScale(Vector3.One * 1.8f), new Vector3(0.12f, 0.08f, 0)));
        return o;
    }

    /// <summary>A sack of barrow dust, open, the grey stuff heaped in it
    /// and spilled in front, chips of bone in it.</summary>
    static Node3D Dust()
    {
        var root = new Node3D();
        var sack = new Build();
        Lathe(sack, Pts(0, -0.4f, 0.28f, -0.39f, 0.42f, -0.28f, 0.46f, -0.1f, 0.42f, 0.08f, 0.34f, 0.18f, 0.36f, 0.22f, 0.4f, 0.24f, 0.38f, 0.28f), 40,
            warp: p =>
            {
                float a = Mathf.Atan2(p.Z, p.X), k = 1 + 0.05f * Mathf.Sin(a * 6 + p.Y * 8);
                return new Vector3(p.X * k, p.Y, p.Z * k);
            }, textured: true);
        Add(root, sack, Cloth("#5a4a3a", true, 5));
        var dust = new Build();
        Lathe(dust, Pts(0.36f, 0.16f, 0.3f, 0.24f, 0.16f, 0.34f, 0, 0.38f), 32, warp: p => p + new Vector3(0, (Noise(p.X * 8, p.Z * 8) - 0.5f) * 0.05f, 0));
        Lathe(dust, Pts(0.34f, 0, 0.22f, 0.04f, 0.09f, 0.07f, 0, 0.08f), 24,
            At(Basis.FromScale(new Vector3(1, 1, 0.7f)), 0.16f, -0.4f, 0.42f), p => p + new Vector3(0, (Noise(p.X * 7 + 3, p.Z * 7) - 0.5f) * 0.04f, 0));
        Add(root, dust, Mat("#8a8272", 0, 1));
        var chips = new Build();
        foreach (var (x, y, z, a) in new[] { (0.1f, 0.36f, 0.05f, 0.4f), (-0.08f, 0.33f, 0.12f, 1.9f), (0.22f, -0.33f, 0.45f, 2.7f), (0.05f, -0.34f, 0.5f, 0.9f) })
            Lathe(chips, Pts(0, -0.03f, 0.035f, 0, 0, 0.03f), 4, new Transform3D(Rot(a, a * 2, 0.5f) * Basis.FromScale(new Vector3(1, 1.8f, 0.8f)), new Vector3(x, y, z)));
        Add(root, chips.Faceted(), Bone());
        return root;
    }

    /* ------------------------------------------------------------ written -- */

    /// <summary>A bound book: boards, a rounded spine, the pages' edges; a
    /// ledger strapped and cornered in brass, or a journal with a ribbon.</summary>
    static Node3D Book(string leather, bool ledger)
    {
        var root = new Node3D();
        var hide = Mat(leather, 0, 0.6f);
        foreach (float z in new[] { 0.12f, -0.12f }) Add(root, new BoxMesh { Size = new Vector3(0.9f, 1.2f, 0.035f) }, hide, At(0, 0, z));
        Add(root, new CylinderMesh { TopRadius = 0.14f, BottomRadius = 0.14f, Height = 1.2f, RadialSegments = 20 }, hide, At(Basis.FromScale(new Vector3(0.35f, 1, 1)), -0.44f, 0, 0));
        Add(root, new BoxMesh { Size = new Vector3(0.86f, 1.15f, 0.205f) }, Mat("#e8dcc0", 0, 0.9f), At(0.01f, 0, 0));
        var metal = new Build();
        if (ledger)
        {
            // Brass corners, a triangle over each of the front board's.
            foreach (float sx in new[] { -1f, 1f })
                foreach (float sy in new[] { -1f, 1f })
                    Extrude(metal, Pts(0, 0, 0.14f, 0, 0, 0.14f), 0.01f, 0.003f, At(new Basis(Vector3.Back, Mathf.Atan2(-sy, -sx) - Mathf.Pi / 4), sx * 0.45f, sy * 0.6f, 0.143f));
            Add(root, new BoxMesh { Size = new Vector3(0.55f, 0.1f, 0.012f) }, Mat("#2a1c12", 0, 0.7f), At(0.2f, 0, 0.144f));
            Add(root, new BoxMesh { Size = new Vector3(0.012f, 0.1f, 0.3f) }, Mat("#2a1c12", 0, 0.7f), At(0.47f, 0, 0));
            Tube(metal, Path(4, t => new Vector3(0.06f * Mathf.Cos(t * Mathf.Tau), 0.06f * Mathf.Sin(t * Mathf.Tau), 0) + new Vector3(0.02f, 0, 0.152f), true), 0.012f, 5, true);
            Add(root, metal, Brass());
        }
        else
        {
            Tube(metal, Circle(new Vector3(0.02f, 0.05f, 0.138f), 0.18f, Vector3.Right, Vector3.Up, 36), 0.01f, 5, true);
            Tube(metal, new List<Vector3> { new(0.02f, -0.18f, 0.138f), new(0.02f, 0.28f, 0.138f) }, 0.01f, 5);
            Tube(metal, new List<Vector3> { new(-0.21f, 0.05f, 0.138f), new(0.25f, 0.05f, 0.138f) }, 0.01f, 5);
            Add(root, metal, Gold());
            var ribbon = new Build();
            Ribbon(ribbon, new List<Vector3> { new(0.1f, -0.55f, 0.02f), new(0.12f, -0.7f, 0.06f), new(0.16f, -0.82f, 0.05f), new(0.15f, -0.92f, 0.08f) }, Vector3.Right, _ => 0.05f);
            Add(root, ribbon, Mat("#8a1a1a", 0, 0.7f, true));
        }
        return root;
    }

    /// <summary>A scroll half unrolled, written on, tied with a ribbon and sealed.</summary>
    static Node3D Scroll()
    {
        var root = new Node3D();
        var paper = Parchment(new Color("#e2d2aa"), 256, 256);
        var sheet = Parchment(new Color("#e2d2aa"), 256, 256);
        var ink = new Color("#3a2a1a") with { A = 0.8f };
        for (int line = 0; line < 9; line++)
        {
            float x = 30 + line * 24;
            for (float y = 40; y < 230; y += 18 + (line * 7 + (int)y) % 13)
                Stroke(sheet, new List<Vector2> { new(x, y), new(x + (line % 2), y + 10 + (line * 3 + (int)y) % 8) }, 2, ink);
        }
        var roll = new Build();
        Lathe(roll, Pts(0, -0.5f, 0.17f, -0.5f, 0.17f, -0.5f, 0.17f, 0.5f, 0.17f, 0.5f, 0, 0.5f), 32, textured: true);
        Add(root, roll, new StandardMaterial3D { AlbedoTexture = Tex(paper), Roughness = 0.9f });
        var flap = new Build();
        Ribbon(flap, new List<Vector3> { new(0.02f, 0, 0.17f), new(0.2f, 0, 0.19f), new(0.4f, 0, 0.14f), new(0.58f, 0, 0.1f), new(0.72f, 0, 0.12f) }, Vector3.Up, _ => 0.9f);
        Add(root, flap, new StandardMaterial3D { AlbedoTexture = Tex(sheet), Roughness = 0.9f, CullMode = BaseMaterial3D.CullModeEnum.Disabled });
        var knobs = new Build();
        var knob = Pts(0, 0, 0.05f, 0, 0.05f, 0.08f, 0.08f, 0.12f, 0.07f, 0.17f, 0, 0.19f);
        Lathe(knobs, knob, 14, At(0, 0.5f, 0));
        Lathe(knobs, knob, 14, At(new Basis(Vector3.Right, Mathf.Pi), 0, -0.5f, 0));
        Add(root, knobs, Mat("#4a2e1a", 0, 0.5f));
        var tie = new Build();
        Tube(tie, Circle(new Vector3(0, -0.2f, 0), 0.178f, Vector3.Right, Vector3.Back, 32), 0.02f, 6, true);
        Add(root, tie, Mat("#8a1a1a", 0, 0.8f));
        var seal = new Build();
        Lathe(seal, Pts(0.085f, 0, 0.09f, 0.02f, 0.07f, 0.035f, 0, 0.04f), 16, At(new Basis(Vector3.Up, -0.25f) * Facing, -0.04f, -0.2f, 0.17f));
        Add(root, seal, Mat("#a01818", 0, 0.35f));
        return root;
    }

    /// <summary>A lampling's map, drawn in tunnels, one end still curled from the roll.</summary>
    static Node3D Map()
    {
        var root = new Node3D();
        var img = Parchment(new Color("#dccaa0"), 256, 192);
        var ink = new Color("#5a3a20");
        Stroke(img, Curve(new(20, 140), new(90, 60), new(180, 60), 40), 3, ink);
        Stroke(img, Curve(new(180, 60), new(210, 60), new(230, 110), 20), 3, ink);
        Stroke(img, Curve(new(40, 40), new(110, 110), new(160, 170), 40), 2, ink with { A = 0.85f }, 6);
        foreach (var (x, y) in new[] { (60, 150), (120, 130), (200, 150) })
            Stroke(img, Curve(new(x, y), new(x + 8, y - 20), new(x - 4, y - 36), 12), 2, ink with { A = 0.7f });
        Stroke(img, new List<Vector2> { new(228, 110), new(232, 170) }, 3, ink);
        Stroke(img, new List<Vector2> { new(222, 160), new(232, 174), new(242, 160) }, 3, ink);
        for (float a = 0; a < Mathf.Tau; a += 0.2f) Stroke(img, new List<Vector2> { new(160 + 7 * Mathf.Cos(a), 170 + 7 * Mathf.Sin(a)), new(160 + 7 * Mathf.Cos(a + 0.2f), 170 + 7 * Mathf.Sin(a + 0.2f)) }, 3, new Color("#8a1a1a"));
        var sheet = new Build();
        Sheet(sheet, null, Pts(-0.65f, -0.475f, 0.65f, -0.475f, 0.65f, 0.475f, -0.65f, 0.475f), 0.05f, 0, p =>
        {
            if (p.X > 0.35f) { float a = (p.X - 0.35f) * 3.2f; return new Vector3(0.35f + Mathf.Sin(a) * 0.3f, p.Y, (1 - Mathf.Cos(a)) * 0.3f); }
            return new Vector3(p.X, p.Y, Mathf.Sin(p.Y * 4) * 0.02f);
        });
        Add(root, sheet, new StandardMaterial3D { AlbedoTexture = Tex(img), Roughness = 0.9f, CullMode = BaseMaterial3D.CullModeEnum.Disabled });
        return root;
    }
}
