using Godot;

namespace SurvivorUnchained;

/// <summary>
/// The slice's HUD, in the web game's hand (src/ui/hud): the ember bar with
/// the level on its medallion across the top, health low on the left, the
/// place's name top right; Cinzel for names, Alegreya Sans for the rest, the
/// same golds, embers and blood.
/// </summary>
public partial class Hud : CanvasLayer
{
    static readonly Color Gold = new("#d9b56a"), GoldHi = new("#f3d9a0"), GoldDim = new("#8a6f3e");
    static readonly Color Ember = new("#ff8a3a"), EmberHi = new("#ffd07a"), Blood = new("#c8323a"), Ink = new("#e8dcc4");
    static readonly Color Panel = new(0.05f, 0.04f, 0.06f, 0.72f);

    Font display = null!, ui = null!, uiBold = null!;
    ColorRect hpFill = null!, emberFill = null!;
    Label hpText = null!, level = null!, kills = null!;
    float hpMax = 212;

    public override void _Ready()
    {
        display = GD.Load<Font>("res://art/fonts/cinzel-600.woff2");
        ui = GD.Load<Font>("res://art/fonts/alegreya-sans-500.woff2");
        uiBold = GD.Load<Font>("res://art/fonts/alegreya-sans-700.woff2");
        var root = new Control { AnchorRight = 1, AnchorBottom = 1, MouseFilter = Control.MouseFilterEnum.Ignore };
        AddChild(root);

        // The ember bar across the top, the level on its medallion.
        var bar = Frame(root, new Rect2(640, 26, 860, 16));
        emberFill = new ColorRect { Color = Ember, Size = new Vector2(0, 12), Position = new Vector2(2, 2) };
        bar.AddChild(emberFill);
        var medal = new Panel { Position = new Vector2(606, 14), Size = new Vector2(44, 44) };
        medal.AddThemeStyleboxOverride("panel", new StyleBoxFlat { BgColor = new Color("#2a1a12"), BorderColor = Gold, BorderWidthLeft = 2, BorderWidthRight = 2, BorderWidthTop = 2, BorderWidthBottom = 2, CornerRadiusTopLeft = 22, CornerRadiusTopRight = 22, CornerRadiusBottomLeft = 22, CornerRadiusBottomRight = 22 });
        root.AddChild(medal);
        level = Text(medal, "1", display, 20, GoldHi, new Rect2(0, 6, 44, 30), HorizontalAlignment.Center);
        kills = Text(root, "0", ui, 20, Ink, new Rect2(900, 50, 120, 28), HorizontalAlignment.Center);

        // Health, low on the left.
        var hp = Frame(root, new Rect2(30, 1030, 400, 28));
        hpFill = new ColorRect { Color = Blood, Size = new Vector2(396, 24), Position = new Vector2(2, 2) };
        hp.AddChild(hpFill);
        hpText = Text(hp, "212 / 212", uiBold, 17, Ink, new Rect2(0, 1, 400, 26), HorizontalAlignment.Center);

        // The place, top right.
        Text(root, "THORNHOLLOW VERGE", display, 26, GoldHi, new Rect2(1380, 18, 510, 36), HorizontalAlignment.Right);
        Text(root, "Night  ·  Day 1  ·  East of the Waystation", ui, 18, Ink with { A = 0.8f }, new Rect2(1380, 54, 510, 26), HorizontalAlignment.Right);
    }

    Panel Frame(Control parent, Rect2 at)
    {
        var p = new Panel { Position = at.Position, Size = at.Size };
        p.AddThemeStyleboxOverride("panel", new StyleBoxFlat { BgColor = Panel, BorderColor = GoldDim, BorderWidthLeft = 1, BorderWidthRight = 1, BorderWidthTop = 1, BorderWidthBottom = 1, CornerRadiusTopLeft = 3, CornerRadiusTopRight = 3, CornerRadiusBottomLeft = 3, CornerRadiusBottomRight = 3 });
        parent.AddChild(p);
        return p;
    }

    static Label Text(Control parent, string s, Font font, int size, Color color, Rect2 at, HorizontalAlignment align)
    {
        var l = new Label { Text = s, Position = at.Position, Size = at.Size, HorizontalAlignment = align, VerticalAlignment = VerticalAlignment.Center };
        l.AddThemeFontOverride("font", font);
        l.AddThemeFontSizeOverride("font_size", size);
        l.AddThemeColorOverride("font_color", color);
        l.AddThemeColorOverride("font_shadow_color", new Color(0, 0, 0, 0.8f));
        l.AddThemeConstantOverride("shadow_offset_y", 2);
        parent.AddChild(l);
        return l;
    }

    public void Show(float hp, float ember, int lvl, int killed)
    {
        hpFill.Size = new Vector2(396 * Mathf.Clamp(hp / hpMax, 0, 1), 24);
        hpText.Text = $"{Mathf.CeilToInt(Mathf.Max(hp, 0))} / {hpMax}";
        emberFill.Size = new Vector2(856 * Mathf.Clamp(ember, 0, 1), 12);
        emberFill.Color = ember > 0.9f ? EmberHi : Ember;
        level.Text = lvl.ToString();
        kills.Text = killed > 0 ? $"{killed} fallen" : "";
    }
}
