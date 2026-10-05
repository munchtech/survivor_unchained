using System;
using System.Collections.Generic;
using System.Linq;
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
    /// <summary>Rarity is never colour alone: each also has a count of small
    /// diamonds, one for common up to six (drawn, not typed: the faces lack them).</summary>
    public static HBoxContainer Gems(int r, float size = 7)
    {
        int n = Math.Clamp(r, 0, Rarity.Length - 1) + 1;
        var h = new HBoxContainer { MouseFilter = Control.MouseFilterEnum.Ignore };
        h.AddThemeConstantOverride("separation", (int)(size * 0.9f));
        for (int i = 0; i < n; i++)
        {
            var box = new Control { CustomMinimumSize = new Vector2(size * 1.2f, size * 1.6f), MouseFilter = Control.MouseFilterEnum.Ignore };
            box.AddChild(new ColorRect { Color = RarityOf(r), Size = new Vector2(size, size), Position = new Vector2(size * 0.6f, size * 0.1f), Rotation = Mathf.Pi / 4, MouseFilter = Control.MouseFilterEnum.Ignore });
            h.AddChild(box);
        }
        return h;
    }
    /// <summary>The day's growing (experience), cool where the night's ember is warm.</summary>
    public static readonly Color Day = new("#86b0d8"), DayHi = new("#d8ecff");
    public static readonly Color Shield = new("#9ad4ff");
    /// <summary>What has focus: the ember's light.</summary>
    public static readonly Color Focus = new("#ffc46a");

    /* The type scale, in pixels at 1080p (docs/UI_DESIGN.md). Body text is
     * Body or more (XAG 101 asks 18 at 1080p on a PC); nothing a player
     * must read is under Caption; Badge is only for numerals on a badge. */
    public const int Hero = 54, Heading = 32, Title = 24, Lead = 20, Body = 18, Small = 16, Caption = 15, Badge = 13;
    /* Spacing steps: everything sits on these. */
    public const int Gap1 = 4, Gap2 = 8, Gap3 = 12, Gap4 = 16, Gap5 = 24, Gap6 = 32;

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

    /// <summary>A forged iron plate: gradient, bevel, inset hairline, bracketed corners (Ornate.cs).</summary>
    public static StyleBox Plate(int pad = 18) => UiArt.Frame("plate", OrnateBox.Make(OrnateBox.Kind.Plate, pad));

    public static StyleBox Paper(int pad = 22) => UiArt.Frame("paper", OrnateBox.Make(OrnateBox.Kind.Paper, pad));

    /// <summary>Iron sunk into a plate: where a grid or a list sits.</summary>
    public static StyleBox Well(int pad = 12) => UiArt.Frame("well", OrnateBox.Make(OrnateBox.Kind.Well, pad));

    static ImageTexture? column;

    /// <summary>A column on a page, with no frame: dark glass over the blurred world, a gold
    /// hairline along its top, darkest where its words begin and fading down, so the space
    /// under what it holds is never a flat black box. Frames are for what is acted on.</summary>
    public static StyleBox Column(int pad = 20)
    {
        if (column == null)
        {
            const int w = 64, h = 256;
            var img = Image.CreateEmpty(w, h, false, Image.Format.Rgba8);
            for (int y = 0; y < h; y++)
                for (int x = 0; x < w; x++)
                {
                    float fy = (y - 2) / (float)(h - 3), fx = Math.Min(x, w - 1 - x) / (w * 0.06f);
                    // (fading in at the sides over a few pixels' worth of the width, so its edges are soft)
                    float side = Math.Clamp(fx, 0, 1);
                    float a = y < 2 ? 0.55f * side : (0.66f - 0.5f * MathF.Pow(fy, 0.8f)) * side;
                    img.SetPixel(x, y, y < 2 ? new Color(GoldDim, a) : new Color(0.03f, 0.024f, 0.036f, a));
                }
            column = ImageTexture.CreateFromImage(img);
        }
        var b = new StyleBoxTexture { Texture = column, TextureMarginTop = 2 };
        b.ContentMarginLeft = b.ContentMarginRight = pad;
        b.ContentMarginTop = pad + 2;
        b.ContentMarginBottom = pad;
        // Ruled in gilt where the art is (frames/column.png), its fade stretched with the column.
        return UiArt.Frame("column", b);
    }

    /// <summary>A group inside a column (a calling, a group of numbers, a quiet note): no iron,
    /// only a wash a shade lighter than the column and a gold hairline over it, so groups read
    /// as groups without a frame in a frame.</summary>
    public static StyleBox Slab(int pad = 14)
    {
        var b = new StyleBoxFlat { BgColor = new Color(0.1f, 0.085f, 0.11f, 0.5f), BorderColor = GoldDim with { A = 0.35f }, CornerDetail = 4 };
        b.SetBorderWidth(Side.Top, 1);
        b.SetCornerRadiusAll(3);
        b.ContentMarginLeft = b.ContentMarginRight = pad;
        b.ContentMarginTop = b.ContentMarginBottom = pad * 3 / 4f;
        return b;
    }

    /// <summary>The ring round what has focus: ember-gold, a soft glow, seen from a sofa.</summary>
    public static StyleBox FocusFrame()
    {
        var b = Box(new Color(0, 0, 0, 0), Focus, 2, 7, 0);
        b.ShadowColor = Focus with { A = 0.45f };
        b.ShadowSize = 10;
        return UiArt.Frame("focus", b);
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
        int padX = small ? 12 : 18, padY = small ? 5 : 8;
        StyleBox S(string id, Color c, Color border)
        {
            var s = Box(c, border, 1, 4);
            s.ContentMarginLeft = s.ContentMarginRight = padX; s.ContentMarginTop = s.ContentMarginBottom = padY;
            return UiArt.Frame(id, s);
        }
        string p = primary ? "button_primary" : "button";
        b.AddThemeStyleboxOverride("normal", S(p, bg, Line));
        b.AddThemeStyleboxOverride("hover", S(p + "_hover", bg.Lightened(0.12f), LineHi));
        b.AddThemeStyleboxOverride("pressed", S(p + "_pressed", bg.Lightened(0.2f), LineHi));
        b.AddThemeStyleboxOverride("disabled", S("button_disabled", bg.Darkened(0.3f), Line with { A = 0.15f }));
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
            var flat = Box(new Color("#d0a858"), new Color("#6a4a14"), 1, 4);
            flat.ContentMarginLeft = flat.ContentMarginRight = 12; flat.ContentMarginTop = flat.ContentMarginBottom = 5;
            var s = UiArt.Frame("segment_on", flat);
            b.AddThemeStyleboxOverride("normal", s);
            b.AddThemeStyleboxOverride("hover", s);
            b.AddThemeColorOverride("font_color", new Color("#2a1a0c"));
            b.AddThemeColorOverride("font_hover_color", new Color("#2a1a0c"));
        }
        return b;
    }

    /// <summary>A level from nothing to full (the settings' volumes): a gold
    /// groove that fills from the left, and its value in words beside it.
    /// `change` runs as it moves, `done` when it is let go.</summary>
    public static Control Slider(float value, Action<float> change, Action done, bool enabled = true)
    {
        var s = new HSlider
        {
            MinValue = 0, MaxValue = 1, Step = 0.05, Value = value, CustomMinimumSize = new Vector2(200, 22),
            SizeFlagsVertical = Control.SizeFlags.ShrinkCenter, FocusMode = Control.FocusModeEnum.None, Editable = enabled,
            MouseDefaultCursorShape = Control.CursorShape.PointingHand,
        };
        var groove = Box(new Color("#0d0c10"), Line, 1, 3);
        groove.ContentMarginTop = groove.ContentMarginBottom = 3;
        var fill = Box(enabled ? new Color("#d0a858") : GoldDim, new Color("#6a4a14"), 1, 3);
        fill.ContentMarginTop = fill.ContentMarginBottom = 3;
        s.AddThemeStyleboxOverride("slider", groove);
        s.AddThemeStyleboxOverride("grabber_area", fill);
        s.AddThemeStyleboxOverride("grabber_area_highlight", fill);
        var knob = new GradientTexture2D
        {
            Gradient = new Gradient { Offsets = new[] { 0f, 0.55f, 0.62f, 1f }, Colors = new[] { GoldHi, GoldHi, new Color("#6a4a14"), new Color("#6a4a14", 0) } },
            Width = 16, Height = 16, Fill = GradientTexture2D.FillEnum.Radial, FillFrom = new Vector2(0.5f, 0.5f), FillTo = new Vector2(1, 0.5f),
        };
        s.AddThemeIconOverride("grabber", knob);
        s.AddThemeIconOverride("grabber_highlight", knob);
        s.AddThemeIconOverride("grabber_disabled", knob);
        var said = Label($"{Mathf.RoundToInt(value * 100)}%", UiBold, 14, enabled ? Ink : InkDim);
        said.CustomMinimumSize = new Vector2(44, 0);
        bool dragging = false;
        s.DragStarted += () => dragging = true;
        s.DragEnded += _ => { dragging = false; done(); };
        // A click on the groove moves it without a drag: that is done at once.
        s.ValueChanged += v => { said.Text = $"{Mathf.RoundToInt((float)v * 100)}%"; change((float)v); if (!dragging) done(); };
        return H(8, s, said);
    }

    /// <summary>A key, as a keycap.</summary>
    public static Control Key(string text)
    {
        var p = new PanelContainer { MouseFilter = Control.MouseFilterEnum.Ignore, CustomMinimumSize = new Vector2(24, 22) };
        var s = Box(new Color("#0d0c10"), GoldDim, 1, 3, 6);
        s.ContentMarginTop = s.ContentMarginBottom = 1;
        p.AddThemeStyleboxOverride("panel", UiArt.Frame("keycap", s));
        var l = Label(text, UiBold, 14, GoldHi, false, HorizontalAlignment.Center, false);
        l.VerticalAlignment = VerticalAlignment.Center;
        p.AddChild(l);
        return p;
    }

    /// <summary>The face buttons' colours, each with its letter, so they are
    /// never told apart by colour alone.</summary>
    static readonly Dictionary<string, Color> PadColours = new()
    {
        ["A"] = new("#6bc45a"), ["B"] = new("#ec5a50"), ["X"] = new("#4a9cf0"), ["Y"] = new("#f2c440"),
    };

    static readonly Dictionary<string, string> PadFiles = new()
    {
        ["A"] = "pad_a", ["B"] = "pad_b", ["X"] = "pad_x", ["Y"] = "pad_y", ["LB"] = "pad_lb", ["RB"] = "pad_rb", ["LT"] = "pad_lt", ["RT"] = "pad_rt",
        ["View"] = "pad_view", ["Menu"] = "pad_menu", ["D-pad up"] = "pad_dpad_up", ["D-pad down"] = "pad_dpad_down", ["D-pad left"] = "pad_dpad_left",
        ["D-pad right"] = "pad_dpad_right", ["D-pad"] = "pad_dpad", ["Left stick"] = "pad_lstick", ["Right stick"] = "pad_rstick",
    };

    /// <summary>A pad button as it looks: a face button is a dark disc with its
    /// letter in its colour; a bumper, a trigger, View and Menu are dark pills.</summary>
    public static Control PadButton(string name)
    {
        if (PadFiles.TryGetValue(name, out var file) && UiArt.Icon("prompt", file) is { } art)
            return new TextureRect { Texture = art, CustomMinimumSize = new Vector2(name.Length == 1 ? 26 : 34, 26), ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.KeepAspectCentered, MouseFilter = Control.MouseFilterEnum.Ignore };
        if (name.StartsWith("D-pad")) return Dpad(name.Length > 6 ? name[6..] : "");
        bool face = PadColours.TryGetValue(name, out var col);
        string text = name;
        var p = new PanelContainer { MouseFilter = Control.MouseFilterEnum.Ignore, CustomMinimumSize = new Vector2(face ? 26 : 30, 26) };
        var s = Box(new Color("#0d0c10"), face ? col : GoldDim, face ? 2 : 1, face ? 13 : 7, face ? 0 : 6);
        p.AddThemeStyleboxOverride("panel", s);
        var l = Label(text, UiHeavy, face ? 15 : 13, face ? col : GoldHi, false, HorizontalAlignment.Center, false);
        l.VerticalAlignment = VerticalAlignment.Center;
        p.AddChild(l);
        return p;
    }

    /// <summary>The D-pad as a little cross, the arm meant lit (none: all four).</summary>
    static Control Dpad(string arm)
    {
        var c = new Control { CustomMinimumSize = new Vector2(26, 26), MouseFilter = Control.MouseFilterEnum.Ignore };
        var back = new Panel { Size = new Vector2(26, 26), MouseFilter = Control.MouseFilterEnum.Ignore };
        back.AddThemeStyleboxOverride("panel", Box(new Color("#0d0c10"), GoldDim, 1, 6, 0));
        c.AddChild(back);
        void Arm(string which, Vector2 at, Vector2 size) =>
            c.AddChild(new ColorRect { Position = at, Size = size, Color = arm == "" || arm == which ? GoldHi : GoldDim with { A = 0.6f }, MouseFilter = Control.MouseFilterEnum.Ignore });
        Arm("up", new Vector2(10, 4), new Vector2(6, 7));
        Arm("down", new Vector2(10, 15), new Vector2(6, 7));
        Arm("left", new Vector2(4, 10), new Vector2(7, 6));
        Arm("right", new Vector2(15, 10), new Vector2(7, 6));
        return c;
    }

    /// <summary>The key or button for an action, as the device last touched has it.</summary>
    public static Control Prompt(Play.Act a)
    {
        var c = Play.Controls.Instance;
        if (c != null && c.UsingPad && c.PadLabels(a).FirstOrDefault() is string pad) return PadButton(pad);
        return Key(c?.KeyLabel(a) ?? "?");
    }

    /// <summary>A prompt and what it does ("A  Wear"), for a screen's footer.</summary>
    public static Control Hint(Play.Act a, string text, Color? color = null)
    {
        var h = H(6, Prompt(a), Label(text, Ui, Caption, color ?? InkDim));
        h.Alignment = BoxContainer.AlignmentMode.Center;
        return h;
    }

    /// <summary>A footer of prompts, spaced like words in a line.</summary>
    public static HBoxContainer Hints(params (Play.Act Act, string Text)[] items)
    {
        var h = H(Gap5);
        foreach (var (a, t) in items) h.AddChild(Hint(a, t));
        return h;
    }

    /// <summary>A hairline rule, gold fading at both ends.</summary>
    public static Control Rule()
    {
        // A painted divider (ornaments/rule.png, a filigree with a centre stone) if there is one.
        var art = UiArt.Art("ornaments/rule.png");
        var r = new TextureRect
        {
            Texture = art ?? new GradientTexture2D
            {
                Gradient = new Gradient { Offsets = new[] { 0f, 0.5f, 1f }, Colors = new[] { LineHi with { A = 0 }, LineHi, LineHi with { A = 0 } } },
                Width = 256, Height = 1,
            },
            StretchMode = art != null ? TextureRect.StretchModeEnum.KeepAspectCentered : TextureRect.StretchModeEnum.Scale,
            ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize,
            CustomMinimumSize = new Vector2(0, art != null ? art.GetHeight() : 1), MouseFilter = Control.MouseFilterEnum.Ignore,
            SizeFlagsHorizontal = Control.SizeFlags.ExpandFill,
        };
        var m = new MarginContainer { MouseFilter = Control.MouseFilterEnum.Ignore };
        m.AddThemeConstantOverride("margin_top", 8);
        m.AddThemeConstantOverride("margin_bottom", 8);
        m.AddChild(r);
        return m;
    }

    /// <summary>The ornament under a great heading (ornaments/flourish.png), or nothing.</summary>
    public static Control Flourish()
    {
        if (UiArt.Art("ornaments/flourish.png") is not { } art) return Gap(0);
        return new TextureRect { Texture = art, CustomMinimumSize = art.GetSize(), ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.KeepAspectCentered, MouseFilter = Control.MouseFilterEnum.Ignore, SizeFlagsHorizontal = Control.SizeFlags.ShrinkCenter };
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
    /// <summary>The first letter small, the rest as written ("Foreman of the Dig" after a comma).</summary>
    public static string Lower1(string s) => s.Length == 0 ? s : char.ToLowerInvariant(s[0]) + s[1..];

    /// <summary>A press for what cannot be undone (break down, unmake, steep): it is held, not clicked,
    /// and does its work when full ("Hold: Break down"). Never a second dialog. See HoldButton.</summary>
    public static HoldButton HoldButton(string text, Action onDone, bool danger = true, bool small = true)
    {
        var b = new HoldButton(danger);
        b.Text = $"Hold: {text}";
        var look = Button("", null, false, small);
        foreach (var s in new[] { "normal", "hover", "pressed", "disabled", "focus" })
            b.AddThemeStyleboxOverride(s, look.GetThemeStylebox(s));
        foreach (var c in new[] { "font_color", "font_hover_color", "font_pressed_color", "font_disabled_color" })
            b.AddThemeColorOverride(c, look.GetThemeColor(c));
        b.AddThemeFontOverride("font", look.GetThemeFont("font"));
        b.AddThemeFontSizeOverride("font_size", look.GetThemeFontSize("font_size"));
        look.Free();
        b.Done += onDone;
        return b;
    }
}

/// <summary>
/// Hold to confirm (UI design's rule for every screen's irreversible acts; the salvage press of
/// Destiny 2 and Diablo IV): the press fills from left to right over <see cref="Time"/> while it is
/// held (the mouse held on it, A or the confirm key held while it has the focus); let go early and the
/// fill drains away and nothing happens; full, it flashes and Done fires once. A tap only nudges
/// the fill, the hint that it must be held. Its look is the button's own boxes plus one fill
/// (<see cref="Fill"/>), so the art pass can replace it in one place.
/// </summary>
public partial class HoldButton : Button
{
    public const double Time = 0.8, Drain = 0.25;
    public event Action? Done;
    /// <summary>The fill: a light laid over the press, added to it (blood for what cannot be undone, ember for the rest).</summary>
    public readonly ColorRect Fill;
    readonly float alpha;
    double p, flash;
    /// <summary>Done, and not yet let go: held on, it does not fill again.</summary>
    bool fired;
    bool mouse;

    public HoldButton(bool danger)
    {
        FocusMode = FocusModeEnum.None;
        MouseDefaultCursorShape = CursorShape.PointingHand;
        alpha = 0.55f;
        Fill = new ColorRect
        {
            Color = (danger ? Style.BloodHi : Style.Ember) with { A = alpha }, MouseFilter = MouseFilterEnum.Ignore,
            Material = new CanvasItemMaterial { BlendMode = CanvasItemMaterial.BlendModeEnum.Add },
        };
        AddChild(Fill);
        ButtonDown += () => { mouse = true; if (!Disabled) Sound.Sfx.Hover(); };
        ButtonUp += () => mouse = false;
        // A click that was not held: a nudge, and nothing else.
        Pressed += Nudge;
        Nav.Mark(this, "hold", Nudge);
    }

    /// <summary>A tap: the fill jumps a little and drains, as a hint that it must be held.</summary>
    public void Nudge() { if (!Disabled && !fired && p < 0.18) p = 0.18; }

    bool Held()
    {
        if (Disabled || !IsVisibleInTree()) return false;
        if (mouse) return true;
        for (Node? n = GetParent(); n != null; n = n.GetParent())
            if (n is Overlay o) return o.Focused(this) && Play.Controls.Instance.Held(Play.Act.Confirm);
        return false;
    }

    public override void _Process(double delta)
    {
        bool held = Held();
        if (flash > 0)
        {
            // Full: a short flash, then it is done.
            flash -= delta;
            Fill.Color = Fill.Color with { A = alpha + (1 - alpha) * (float)Math.Max(0, flash / 0.18) };
            if (flash <= 0) { p = 0; Fill.Color = Fill.Color with { A = alpha }; Done?.Invoke(); }
        }
        else if (held && !fired)
        {
            p = Math.Min(1, p + delta / Time);
            if (p >= 1) { flash = 0.18; fired = true; }
        }
        else if (!held)
        {
            fired = false;
            if (p > 0) p = Math.Max(0, p - delta / Drain);
        }
        // The fill inside the press's border, growing from its left edge.
        float w = (float)(Size.X - 4) * (float)(flash > 0 ? 1 : p);
        Fill.Position = new Vector2(2, 2);
        Fill.Size = new Vector2(Math.Max(0, w), Math.Max(0, Size.Y - 4));
        Fill.Visible = w > 0.5f;
    }
}
