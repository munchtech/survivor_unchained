using System;
using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.Ui;

/// <summary>
/// The interface's look (the web game's ui/theme.css): iron and ember.
/// Panels are dark iron plates with an engraved gold hairline; anything that
/// matters (health, ember, rarity, danger) carries colour, everything else
/// recedes to warm greys; reading text sits on parchment. Cinzel for names
/// carved in stone, Alegreya for what is read, Alegreya Sans for the rest.
/// </summary>
public static class Style
{
    public static readonly Color Gold = new("#d9b56a"), GoldHi = new("#f3d9a0"), GoldDim = new("#8a6f3e");
    public static readonly Color Ember = new("#ff8a3a"), EmberHi = new("#ffd07a"), Blood = new("#c8323a"), BloodHi = new("#ff5a5a");
    public static readonly Color Iron0 = new("#0b0a0d"), Iron1 = new("#15131a"), Iron2 = new("#1e1b24"), Iron3 = new("#2a2631");
    public static readonly Color Line = new(0.851f, 0.71f, 0.416f, 0.35f), LineHi = new(0.953f, 0.851f, 0.627f, 0.7f);
    public static readonly Color Parchment = new("#e8dcc0"), ParchmentInk = new("#2a2118");
    public static readonly Color Ink = new("#e8dcc4"), InkDim = new("#a89c88"), InkFaint = new("#6f6556");
    public static readonly Color Good = new("#8ae05a"), Bad = new("#ff7a6a");
    public static readonly Color[] Rarity = { new("#c8c0b0"), new("#6fd46a"), new("#5aa8ff"), new("#c070ff"), new("#ffb040"), new("#ff6a3a") };
    public static Color RarityOf(int r) => Rarity[Math.Clamp(r, 0, Rarity.Length - 1)];

    static readonly Dictionary<string, Font> fonts = new();
    static Font F(string file) => fonts.TryGetValue(file, out var f) ? f : fonts[file] = GD.Load<Font>($"res://art/fonts/{file}.woff2");
    public static Font Display => F("cinzel-700");
    public static Font DisplayLight => F("cinzel-600");
    public static Font Text => F("alegreya-400");
    public static Font TextItalic => F("alegreya-400-italic");
    public static Font TextBold => F("alegreya-700");
    public static Font Ui => F("alegreya-sans-500");
    public static Font UiBold => F("alegreya-sans-700");
    public static Font UiHeavy => F("alegreya-sans-800");

    /* ------------------------------------------------------------ boxes -- */

    public static StyleBoxFlat Box(Color bg, Color border, int width = 1, int radius = 4, int pad = 12)
    {
        var b = new StyleBoxFlat
        {
            BgColor = bg, BorderColor = border, CornerDetail = 6,
            ContentMarginLeft = pad, ContentMarginRight = pad, ContentMarginTop = pad * 2 / 3, ContentMarginBottom = pad * 2 / 3,
        };
        b.SetBorderWidthAll(width);
        b.SetCornerRadiusAll(radius);
        return b;
    }

    /// <summary>An iron plate with a gold hairline and a shadow under it.</summary>
    public static StyleBoxFlat Plate(int pad = 18)
    {
        var b = Box(new Color(0.09f, 0.08f, 0.105f, 0.97f), Line, 1, 6, pad);
        b.ShadowColor = new Color(0, 0, 0, 0.6f);
        b.ShadowSize = 18;
        b.ShadowOffset = new Vector2(0, 6);
        return b;
    }

    public static StyleBoxFlat Paper(int pad = 22)
    {
        var b = Box(new Color("#e4d6b6"), new Color(0.35f, 0.24f, 0.08f, 0.35f), 1, 4, pad);
        b.ShadowColor = new Color(0, 0, 0, 0.6f);
        b.ShadowSize = 18;
        return b;
    }

    /* ---------------------------------------------------------- widgets -- */

    public static T Font<T>(T c, Font font, int size, Color color, bool shadow = true) where T : Control
    {
        c.AddThemeFontOverride("font", font);
        c.AddThemeFontSizeOverride("font_size", size);
        c.AddThemeColorOverride("font_color", color);
        if (shadow)
        {
            c.AddThemeColorOverride("font_shadow_color", new Color(0, 0, 0, 0.85f));
            c.AddThemeConstantOverride("shadow_offset_y", 1);
            c.AddThemeConstantOverride("shadow_offset_x", 0);
        }
        return c;
    }

    public static Label Label(string text, Font font, int size, Color color, bool wrap = false, HorizontalAlignment align = HorizontalAlignment.Left, bool shadow = true)
    {
        var l = new Label { Text = text, HorizontalAlignment = align, MouseFilter = Control.MouseFilterEnum.Ignore };
        if (wrap) { l.AutowrapMode = TextServer.AutowrapMode.WordSmart; l.SizeFlagsHorizontal = Control.SizeFlags.ExpandFill; }
        return Font(l, font, size, color, shadow);
    }

    /// <summary>A small capital heading in gold (the web game's title-cap).</summary>
    public static Label Cap(string text, int size = 16) => Label(text.ToUpperInvariant(), Display, size, GoldHi);

    public static Label SubLabel(string text) => Label(text.ToUpperInvariant(), UiHeavy, 12, Gold);

    /// <summary>A button in the iron style; primary is ember-lit.</summary>
    public static Button Button(string text, Action? onPress = null, bool primary = false, bool small = false)
    {
        var b = new Button { Text = text, FocusMode = Control.FocusModeEnum.None, MouseDefaultCursorShape = Control.CursorShape.PointingHand };
        Font(b, UiBold, small ? 14 : 16, primary ? new Color("#ffe4b0") : GoldHi);
        b.AddThemeColorOverride("font_hover_color", Colors.White);
        b.AddThemeColorOverride("font_pressed_color", Colors.White);
        b.AddThemeColorOverride("font_disabled_color", new Color(0.6f, 0.55f, 0.45f, 0.5f));
        var bg = primary ? new Color("#43290f") : new Color("#221e28");
        int padX = small ? 10 : 18, padY = small ? 4 : 8;
        StyleBoxFlat S(Color c, Color border) { var s = Box(c, border, 1, 4); s.ContentMarginLeft = s.ContentMarginRight = padX; s.ContentMarginTop = s.ContentMarginBottom = padY; return s; }
        b.AddThemeStyleboxOverride("normal", S(bg, Line));
        b.AddThemeStyleboxOverride("hover", S(bg.Lightened(0.12f), LineHi));
        b.AddThemeStyleboxOverride("pressed", S(bg.Lightened(0.2f), LineHi));
        b.AddThemeStyleboxOverride("disabled", S(bg.Darkened(0.3f), Line with { A = 0.15f }));
        b.AddThemeStyleboxOverride("focus", new StyleBoxEmpty());
        if (onPress != null) b.Pressed += onPress;
        return b;
    }

    /// <summary>A toggle among several (the settings' segments): the one on is gold.</summary>
    public static Button Segment(string text, bool on, Action onPress)
    {
        var b = Button(text, onPress, false, true);
        if (on)
        {
            var s = Box(new Color("#d0a858"), new Color("#6a4a14"), 1, 4);
            s.ContentMarginLeft = s.ContentMarginRight = 10; s.ContentMarginTop = s.ContentMarginBottom = 4;
            b.AddThemeStyleboxOverride("normal", s);
            b.AddThemeStyleboxOverride("hover", s);
            b.AddThemeColorOverride("font_color", new Color("#2a1a0c"));
            b.AddThemeColorOverride("font_hover_color", new Color("#2a1a0c"));
        }
        return b;
    }

    /// <summary>A key, as a keycap.</summary>
    public static Control Key(string text)
    {
        var p = new PanelContainer { MouseFilter = Control.MouseFilterEnum.Ignore };
        var s = Box(new Color("#0d0c10"), GoldDim, 1, 3, 5);
        s.ContentMarginTop = s.ContentMarginBottom = 1;
        p.AddThemeStyleboxOverride("panel", s);
        p.AddChild(Label(text, UiBold, 12, GoldHi, false, HorizontalAlignment.Center, false));
        return p;
    }

    /// <summary>A hairline rule, gold fading at both ends.</summary>
    public static Control Rule()
    {
        var r = new TextureRect
        {
            Texture = new GradientTexture2D
            {
                Gradient = new Gradient { Offsets = new[] { 0f, 0.5f, 1f }, Colors = new[] { LineHi with { A = 0 }, LineHi, LineHi with { A = 0 } } },
                Width = 256, Height = 1,
            },
            StretchMode = TextureRect.StretchModeEnum.Scale, CustomMinimumSize = new Vector2(0, 1), MouseFilter = Control.MouseFilterEnum.Ignore,
            SizeFlagsHorizontal = Control.SizeFlags.ExpandFill,
        };
        var m = new MarginContainer { MouseFilter = Control.MouseFilterEnum.Ignore };
        m.AddThemeConstantOverride("margin_top", 8);
        m.AddThemeConstantOverride("margin_bottom", 8);
        m.AddChild(r);
        return m;
    }

    /// <summary>A darkening over the game behind an overlay; a click on it closes.</summary>
    public static ColorRect Scrim(Action? onClick = null, float alpha = 0.55f)
    {
        var s = new ColorRect { Color = new Color(0.02f, 0.015f, 0.03f, alpha), MouseFilter = Control.MouseFilterEnum.Stop };
        Fill(s);
        if (onClick != null) s.GuiInput += e => { if (e is InputEventMouseButton { Pressed: true, ButtonIndex: MouseButton.Left }) onClick(); };
        return s;
    }

    public static void Fill(Control c)
    {
        c.AnchorLeft = c.AnchorTop = 0;
        c.AnchorRight = c.AnchorBottom = 1;
        c.OffsetLeft = c.OffsetTop = c.OffsetRight = c.OffsetBottom = 0;
    }

    /// <summary>A control centred on the screen at a size.</summary>
    public static T Centered<T>(T c, Vector2 size, Vector2 offset = default) where T : Control
    {
        c.AnchorLeft = c.AnchorRight = c.AnchorTop = c.AnchorBottom = 0.5f;
        c.OffsetLeft = -size.X / 2 + offset.X; c.OffsetRight = size.X / 2 + offset.X;
        c.OffsetTop = -size.Y / 2 + offset.Y; c.OffsetBottom = size.Y / 2 + offset.Y;
        return c;
    }

    public static VBoxContainer V(int gap = 6, params Control[] items)
    {
        var v = new VBoxContainer { MouseFilter = Control.MouseFilterEnum.Ignore };
        v.AddThemeConstantOverride("separation", gap);
        foreach (var i in items) v.AddChild(i);
        return v;
    }

    public static HBoxContainer H(int gap = 6, params Control[] items)
    {
        var h = new HBoxContainer { MouseFilter = Control.MouseFilterEnum.Ignore };
        h.AddThemeConstantOverride("separation", gap);
        foreach (var i in items) h.AddChild(i);
        return h;
    }

    public static PanelContainer Panel(StyleBox box, Control? child = null)
    {
        var p = new PanelContainer();
        p.AddThemeStyleboxOverride("panel", box);
        if (child != null) p.AddChild(child);
        return p;
    }

    /// <summary>A scrolling column (a long list in a panel).</summary>
    public static ScrollContainer Scroll(Control content)
    {
        var s = new ScrollContainer { HorizontalScrollMode = ScrollContainer.ScrollMode.Disabled, SizeFlagsVertical = Control.SizeFlags.ExpandFill, SizeFlagsHorizontal = Control.SizeFlags.ExpandFill };
        content.SizeFlagsHorizontal = Control.SizeFlags.ExpandFill;
        s.AddChild(content);
        return s;
    }

    public static Control Gap(float h) => new Control { CustomMinimumSize = new Vector2(0, h), MouseFilter = Control.MouseFilterEnum.Ignore };

    public static string Cap1(string s) => s.Length == 0 ? s : char.ToUpperInvariant(s[0]) + s[1..];
}
