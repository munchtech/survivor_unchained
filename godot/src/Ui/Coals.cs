using System;
using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.Ui;

/// <summary>
/// A point to spend, as a live coal (the owner on Self: "the stat stuff in blocks still dosn't work
/// for me"; the coordinator: make spending a world object, not a + button). A rough dark crust with
/// its heart glowing through the cracks, breathing. UI art's coal/coal_0..3.png wins where painted;
/// until then it is drawn, each coal its own shape by its seed.
/// </summary>
public partial class Coal : Control
{
    public int Seed;
    public float Scale = 1;
    double t;
    readonly Control halo;
    static GradientTexture2D? soft;

    public Coal(int seed, float scale = 1)
    {
        Seed = seed;
        Scale = scale;
        MouseFilter = MouseFilterEnum.Ignore;
        TextureFilter = TextureFilterEnum.LinearWithMipmaps;
        CustomMinimumSize = new Vector2(20, 16) * scale;
        Size = CustomMinimumSize;
        t = seed * 0.37;
        soft ??= new GradientTexture2D
        {
            Width = 64, Height = 64, Fill = GradientTexture2D.FillEnum.Radial, FillFrom = new Vector2(0.5f, 0.5f), FillTo = new Vector2(1, 0.5f),
            Gradient = new Gradient { Colors = new[] { Colors.White, Colors.White with { A = 0.3f }, Colors.White with { A = 0 } }, Offsets = new[] { 0f, 0.4f, 1f } },
        };
        // Its light on what it lies on, laid on additively under it.
        halo = new HaloLight(this) { MouseFilter = MouseFilterEnum.Ignore, ShowBehindParent = true, Material = new CanvasItemMaterial { BlendMode = CanvasItemMaterial.BlendModeEnum.Add } };
        AddChild(halo);
    }

    /// <summary>How it breathes now (0.8 to 1.15), the halo and the heart together.</summary>
    float Breath => 0.97f + 0.11f * Mathf.Sin((float)t * 2.3f + Seed) + 0.06f * Mathf.Sin((float)t * 5.7f + Seed * 2.1f);

    public override void _Process(double delta)
    {
        t += delta;
        QueueRedraw();
        halo.QueueRedraw();
    }

    static float Hash(int k, int salt)
    {
        uint h = (uint)(k * 374761393 + salt * 668265263);
        h = (h ^ (h >> 13)) * 1274126177;
        return ((h ^ (h >> 16)) & 0xffff) / 65535f;
    }

    public override void _Draw()
    {
        var c = Size / 2;
        if (UiArt.Art($"coal/coal_{((Seed % 4) + 4) % 4}.png") is { } art)
        {
            var s = art.GetSize() * Scale;
            DrawTextureRect(art, new Rect2(c - s / 2, s), false, new Color(Breath, Breath, Breath));
            return;
        }
        float rx = 9 * Scale, ry = 6.5f * Scale;
        var crust = new Vector2[9];
        for (int i = 0; i < 9; i++)
        {
            float a = i / 9f * Mathf.Tau, r = 0.8f + 0.32f * Hash(Seed, i);
            crust[i] = c + new Vector2(Mathf.Cos(a) * rx * r, Mathf.Sin(a) * ry * r);
        }
        DrawColoredPolygon(crust, new Color("#2a1410"));
        // the heart, and the cracks it shows through
        float b = Breath;
        var hot = new Color(1f, 0.55f * b, 0.2f * b);
        for (int i = 0; i < 3; i++)
        {
            float a = Hash(Seed, 20 + i) * Mathf.Tau;
            var p0 = c + new Vector2(Mathf.Cos(a) * rx * 0.2f, Mathf.Sin(a) * ry * 0.2f);
            var p1 = c + new Vector2(Mathf.Cos(a + 2.1f) * rx * 0.75f, Mathf.Sin(a + 2.1f) * ry * 0.6f);
            DrawLine(p0, p1, hot with { A = 0.85f }, 1.3f * Scale, true);
        }
        DrawCircle(c, 3.2f * Scale, hot);
        DrawCircle(c, 1.6f * Scale, new Color(1f, 0.85f, 0.55f) with { A = Mathf.Clamp(b - 0.2f, 0, 1) });
    }

    partial class HaloLight : Control
    {
        readonly Coal coal;
        public HaloLight(Coal coal) { this.coal = coal; }

        public override void _Draw()
        {
            var c = coal.Size / 2;
            float r = 20 * coal.Scale * coal.Breath;
            DrawTextureRect(soft!, new Rect2(c - new Vector2(r * 1.3f, r), new Vector2(r * 2.6f, r * 2)), false, Style.Ember with { A = 0.32f });
        }
    }
}

/// <summary>
/// A small iron dish of live coals at the end of Self's ledger: one coal for each point to spend.
/// A coal is taken from it to an attribute (a click on the attribute, or a drag from the dish),
/// and comes back to it if taken back. UI art's coal/dish.png and dish_rim.png win where painted.
/// </summary>
public partial class CoalDish : Control
{
    /// <summary>Where each coal lies in the dish, from its middle.</summary>
    static readonly Vector2[] Spots = { new(-10, -1), new(9, 1), new(0, -5), new(-3, 4), new(15, -4) };
    public readonly List<Coal> Coals = new();
    readonly int count;

    public CoalDish(int count)
    {
        this.count = count;
        MouseFilter = MouseFilterEnum.Stop;
        CustomMinimumSize = new Vector2(84, 40);
        TooltipText = count == 1 ? "A point to spend: give the coal to an attribute" : $"{count} points to spend: give each coal to an attribute";
        for (int i = 0; i < Math.Min(count, Spots.Length); i++)
        {
            var coal = new Coal(11 + i) { Position = new Vector2(42, 18) + Spots[i] - new Vector2(10, 8) };
            Coals.Add(coal);
            AddChild(coal);
        }
        AddChild(new Rim());
    }

    /// <summary>Where the next coal taken would come from, on the screen.</summary>
    public Vector2 TopCoal => Coals.Count > 0 ? Coals[^1].GlobalPosition + Coals[^1].Size / 2 : GlobalPosition + new Vector2(42, 18);

    public override Variant _GetDragData(Vector2 at)
    {
        if (Coals.Count == 0) return default;
        var held = new Coal(99);
        var holder = new Control { MouseFilter = MouseFilterEnum.Ignore };
        held.Position = -held.Size / 2;
        holder.AddChild(held);
        SetDragPreview(holder);
        Sound.Sfx.Click();
        return "coal";
    }

    public override void _Draw()
    {
        var c = new Vector2(42, 18);
        if (UiArt.Art("coal/dish.png") is { } art) { DrawTexture(art, c - art.GetSize() / 2); return; }
        // A shallow iron dish: its shadow, its rim, the dark of its bowl, the light along its far edge.
        DrawSetTransform(c + new Vector2(0, 5), 0, new Vector2(1, 0.38f));
        DrawCircle(Vector2.Zero, 37, new Color(0, 0, 0, 0.55f));
        DrawSetTransform(c, 0, new Vector2(1, 0.38f));
        DrawCircle(Vector2.Zero, 34, new Color("#3a3638"));
        DrawCircle(new Vector2(0, 3), 29, new Color("#161314"));
        DrawArc(Vector2.Zero, 33.5f, Mathf.Pi * 1.1f, Mathf.Pi * 1.9f, 24, new Color("#7a7068"), 1.6f, true);
        DrawSetTransform(Vector2.Zero);
    }

    /// <summary>The dish's near rim, over the coals' feet.</summary>
    partial class Rim : Control
    {
        public Rim() { MouseFilter = MouseFilterEnum.Ignore; }

        public override void _Draw()
        {
            var c = new Vector2(42, 18);
            if (UiArt.Art("coal/dish_rim.png") is { } art) { DrawTexture(art, c - art.GetSize() / 2); return; }
            if (UiArt.Art("coal/dish.png") != null) return;
            DrawSetTransform(c, 0, new Vector2(1, 0.38f));
            DrawArc(Vector2.Zero, 33, 0.25f, Mathf.Pi - 0.25f, 24, new Color("#4a4446"), 5, true);
            DrawSetTransform(Vector2.Zero);
        }
    }
}
