using System;
using System.Linq;
using System.Text.RegularExpressions;
using SurvivorUnchained.Play;
using Godot;

namespace SurvivorUnchained.Ui;

/// <summary>
/// Words set straight on the world, with no box behind them (the owner: "the item toasts could be
/// transparent and stylized"; the tips "not on a cheap looking backdrop and just stylized readable
/// text"). Legible by their type alone: a dark soft outline and a shadow under every letter, and,
/// for what matters, a faint light of its own colour behind. They arrive out of a spark (UI art's
/// hud/spark.png) and glint once as they settle (hud/glint.png).
/// </summary>
public static partial class WorldType
{
    /// <summary>Lettering for the world: the colour, a dark outline soft enough to read over sunlit
    /// cobbles, and a shadow to lift it off them.</summary>
    public static Label Lettering(string text, Font font, int size, Color colour)
    {
        var l = new Label { Text = text, MouseFilter = Control.MouseFilterEnum.Ignore };
        l.AddThemeFontOverride("font", font);
        l.AddThemeFontSizeOverride("font_size", size);
        l.AddThemeColorOverride("font_color", colour);
        l.AddThemeColorOverride("font_outline_color", new Color(0.03f, 0.02f, 0.02f, 0.82f));
        l.AddThemeConstantOverride("outline_size", Math.Max(4, size / 4));
        l.AddThemeColorOverride("font_shadow_color", new Color(0, 0, 0, 0.6f));
        l.AddThemeConstantOverride("shadow_offset_x", 0);
        l.AddThemeConstantOverride("shadow_offset_y", 2);
        l.AddThemeConstantOverride("shadow_outline_size", Math.Max(6, size / 3));
        return l;
    }

    /// <summary>An action on the world: its key (none: a pad walks to it) and its word in lettering,
    /// no box; the word brightens under the pointer. Returns the button and its word.</summary>
    public static (Button Button, Label Word) Keyed(Act? key, string text, Font font, int size, Color ink, Action press)
    {
        var b = new Button { FocusMode = Control.FocusModeEnum.None, Flat = true, MouseDefaultCursorShape = Control.CursorShape.PointingHand };
        foreach (var s in new[] { "normal", "hover", "pressed", "focus" }) b.AddThemeStyleboxOverride(s, new StyleBoxEmpty());
        var word = Lettering(text, font, size, ink);
        var row = new HBoxContainer { MouseFilter = Control.MouseFilterEnum.Ignore };
        row.AddThemeConstantOverride("separation", 12);
        if (key is Act k) row.AddChild(Style.Prompt(k));
        row.AddChild(word);
        foreach (var c in row.GetChildren().OfType<Control>()) c.SizeFlagsVertical = Control.SizeFlags.ShrinkCenter;
        Kit.Quiet(row);
        b.AddChild(row);
        b.CustomMinimumSize = row.GetCombinedMinimumSize();
        b.Ready += () => b.CustomMinimumSize = row.GetCombinedMinimumSize();
        b.MouseEntered += () => word.AddThemeColorOverride("font_color", ink.Lightened(0.25f));
        b.MouseExited += () => word.AddThemeColorOverride("font_color", ink);
        b.Pressed += press;
        return (b, word);
    }

    static GradientTexture2D? soft;

    /// <summary>A soft light the size of `size`, for behind words of note (additive).</summary>
    public static TextureRect Light(Vector2 size, Color colour)
    {
        soft ??= new GradientTexture2D
        {
            Width = 64, Height = 64, Fill = GradientTexture2D.FillEnum.Radial, FillFrom = new Vector2(0.5f, 0.5f), FillTo = new Vector2(1, 0.5f),
            Gradient = new Gradient { Colors = new[] { Colors.White, Colors.White with { A = 0.35f }, Colors.White with { A = 0 } }, Offsets = new[] { 0f, 0.45f, 1f } },
        };
        return new TextureRect
        {
            Texture = soft, ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Scale, Size = size,
            Modulate = colour, MouseFilter = Control.MouseFilterEnum.Ignore, Material = new CanvasItemMaterial { BlendMode = CanvasItemMaterial.BlendModeEnum.Add },
        };
    }

    /// <summary>The spark a notice is struck from: UI art's burst, eight frames in a strip (drawn
    /// normally: its alpha already fades), or a drawn burst until it lands.</summary>
    public partial class Spark : Control
    {
        public double T;
        public float Life = 0.42f;
        readonly Color tint;
        static Texture2D? strip;

        public Spark(Color tint, float size = 48)
        {
            this.tint = tint;
            MouseFilter = MouseFilterEnum.Ignore;
            Size = new Vector2(size, size);
            strip ??= UiArt.Art("hud/spark.png");
        }

        public override void _Process(double delta)
        {
            T += delta;
            if (T >= Life) { Visible = false; SetProcess(false); }
            QueueRedraw();
        }

        public override void _Draw()
        {
            float k = (float)(T / Life);
            if (strip is { } s)
            {
                float fw = s.GetWidth() / 8f;
                int f = Math.Clamp((int)(k * 8), 0, 7);
                DrawTextureRectRegion(s, new Rect2(Vector2.Zero, Size), new Rect2(f * fw, 0, fw, s.GetHeight()), Colors.White.Lerp(tint, 0.25f));
                return;
            }
            var c = Size / 2;
            DrawCircle(c, Size.X * 0.2f * (1 - k), new Color(1, 0.9f, 0.7f, 1 - k));
            for (int i = 0; i < 8; i++)
            {
                float a = i * Mathf.Tau / 8 + 0.4f, r0 = Size.X * 0.15f + k * Size.X * 0.3f;
                var d = new Vector2(Mathf.Cos(a), Mathf.Sin(a));
                DrawLine(c + d * r0, c + d * (r0 + 5), Style.Ember with { A = 1 - k }, 1.5f, true);
            }
        }
    }

    /// <summary>A glint running once along the top of a word as it settles.</summary>
    public partial class Glint : Control
    {
        public double T;
        readonly float width;
        readonly Color tint;
        static Texture2D? star;

        public Glint(float width, Color tint)
        {
            this.width = width;
            this.tint = tint;
            MouseFilter = MouseFilterEnum.Ignore;
            star ??= UiArt.Art("hud/glint.png");
        }

        public override void _Process(double delta) { T += delta; QueueRedraw(); if (T > 0.6) SetProcess(false); }

        public override void _Draw()
        {
            float k = (float)Math.Clamp(T / 0.45, 0, 1);
            if (k <= 0 || k >= 1) return;
            float a = Mathf.Sin(k * Mathf.Pi);
            var at = new Vector2(width * (0.08f + 0.84f * k), 0);
            var c = tint.Lightened(0.6f) with { A = a };
            if (star != null) { var s = star.GetSize() * (0.7f + 0.3f * a); DrawTextureRect(star, new Rect2(at - s / 2, s), false, c); return; }
            DrawLine(at - new Vector2(9 * a, 0), at + new Vector2(9 * a, 0), c, 1.5f, true);
            DrawLine(at - new Vector2(0, 6 * a), at + new Vector2(0, 6 * a), c, 1.5f, true);
        }
    }
}

/// <summary>
/// A notice on the world (a pickup, a discovery, a quest's turn): its icon small, its name in its
/// tier's colour, its count after it, no box. It is struck from a spark, rises a little into
/// place and glints once; it holds; then it drifts up and fades like an ember. Rare and up carry
/// a faint light of their colour; a Legendary is larger and stays longer.
/// </summary>
public partial class Notice : Control
{
    public double T;
    public readonly double Life;
    readonly Control body;
    readonly WorldType.Spark spark;
    readonly WorldType.Glint glint;
    public readonly Label Title;
    /// <summary>How wide a notice may run on one line before its words set under its title.</summary>
    const float Wide = 560;

    public Notice(Control? icon, string text, string? sub, Color colour, bool noted, bool grand, double life)
    {
        Life = life;
        MouseFilter = MouseFilterEnum.Ignore;
        int size = grand ? 26 : 18;
        var titleFont = grand ? Style.Display : Style.UiBold;
        Title = WorldType.Lettering(text, titleFont, size, colour);
        Title.Name = "Title";
        var row = new HBoxContainer { MouseFilter = MouseFilterEnum.Ignore };
        row.AddThemeConstantOverride("separation", 8);
        // A long title (a lore line: "Ember: light that seeps up from under the valley...") breaks evenly at the
        // notice's width rather than running 1200 px across the play; its glyph stays on the first line.
        float iconW0 = icon?.GetCombinedMinimumSize().X ?? 0, textW = Wide - (icon != null ? iconW0 + 8 : 0);
        bool wraps = titleFont.GetStringSize(text, HorizontalAlignment.Left, -1, size).X > textW;
        float line1 = titleFont.GetHeight(size);
        if (wraps)
        {
            Title.Text = Kit.Balance(text, titleFont, size, textW);
            GD.Print($"notice: '{(text.Length > 40 ? text[..40] + "..." : text)}' wrapped at {textW:0} px into {Title.Text.Count(ch => ch == (char)10) + 1} lines");
        }
        if (icon != null)
        {
            if (!wraps) { icon.SizeFlagsVertical = SizeFlags.ShrinkCenter; row.AddChild(icon); }
            else
            {
                // (centred on the first line, not on the block)
                var at = new MarginContainer { MouseFilter = MouseFilterEnum.Ignore, SizeFlagsVertical = SizeFlags.ShrinkBegin };
                at.AddThemeConstantOverride("margin_top", (int)Math.Max(0, Math.Round((line1 - icon.GetCombinedMinimumSize().Y) / 2)));
                at.AddChild(icon);
                row.AddChild(at);
            }
        }
        row.AddChild(Title);
        Control whole = row;
        float lineH = wraps ? line1 : row.GetCombinedMinimumSize().Y;
        if (!string.IsNullOrEmpty(sub))
        {
            int subSize = grand ? 17 : 15;
            float indent = row.GetCombinedMinimumSize().X - Title.GetCombinedMinimumSize().X;
            // (measured by the font: a label out of the tree keeps the size of its first words)
            bool fits = row.GetCombinedMinimumSize().X + 8 + Style.TextItalic.GetStringSize(sub, HorizontalAlignment.Left, -1, subSize).X <= Wide;
            var s = WorldType.Lettering(fits ? sub : Kit.Balance(sub, Style.TextItalic, subSize, Wide - indent), Style.TextItalic, subSize, new Color("#cfc4b0"));
            s.SizeFlagsVertical = SizeFlags.ShrinkEnd;
            if (fits) row.AddChild(s);
            else
            {
                // A long line (a quest's entry) sets under its title, broken evenly, rather than
                // running across the screen and over the names on the world.
                var under = new HBoxContainer { MouseFilter = MouseFilterEnum.Ignore };
                under.AddChild(new Control { CustomMinimumSize = new Vector2(indent, 0), MouseFilter = MouseFilterEnum.Ignore });
                under.AddChild(s);
                var stack = new VBoxContainer { MouseFilter = MouseFilterEnum.Ignore };
                stack.AddThemeConstantOverride("separation", 1);
                stack.AddChild(row);
                stack.AddChild(under);
                whole = stack;
            }
        }
        var size2 = whole.GetCombinedMinimumSize();
        if (noted)
        {
            // Its own light behind it, faint, the colour of what it is.
            light = WorldType.Light(new Vector2(size2.X + 60, size2.Y + 26), colour with { A = grand ? 0.4f : 0.22f });
            light.Position = new Vector2(-30, -13);
            AddChild(light);
        }
        body = whole;
        AddChild(whole);
        CustomMinimumSize = size2;
        float iconW = icon?.GetCombinedMinimumSize().X ?? 0;
        spark = new WorldType.Spark(colour, grand ? 72 : 48) { Position = new Vector2(iconW / 2 - (grand ? 36 : 24), lineH / 2 - (grand ? 36 : 24)) };
        AddChild(spark);
        glint = new WorldType.Glint(Title.GetCombinedMinimumSize().X, colour) { Position = new Vector2(iconW + 8, 4) };
        AddChild(glint);
        glint.T = -0.3;
        body.Modulate = Colors.Transparent;
        if (light != null) light.Modulate = Colors.Transparent;
        lightColour = colour with { A = grand ? 0.4f : 0.22f };
    }

    readonly TextureRect? light;
    readonly Color lightColour;

    /// <summary>The notice's life, frame by frame: in, held, drifting out. False when it is done.
    /// (Only the words and their light fade: the spark they come from is seen before them.)</summary>
    public bool Step(double delta)
    {
        T += delta;
        double inT = Math.Clamp((T - 0.06) / 0.24, 0, 1), outT = Math.Clamp((T - (Life - 0.9)) / 0.9, 0, 1);
        float ease = 1 - (float)Math.Pow(1 - inT, 3);
        float a = (float)(ease * (1 - outT));
        body.Position = new Vector2(0, 7 * (1 - ease) - 16 * (float)(outT * outT));
        body.Modulate = Colors.White with { A = a };
        if (light != null) light.Modulate = lightColour with { A = lightColour.A * a };
        return T < Life;
    }
}

/// <summary>
/// The fall's two choices in a story night, as a held moment (the experience director's brief): no
/// page and no box, the world darkened under them on its own layer, and the two set on it as type,
/// side by side about her: "Get up" in the ember's light, its key drawn as the key, and "Let the night
/// go" quieter; under each, what it means. The ember breathes behind "Get up" while it waits. A
/// click, or the key, chooses.
/// </summary>
public partial class FallChoices : Control
{
    double t;
    readonly TextureRect light;

    public FallChoices(int risesLeft, Action rise, Action letGo)
    {
        MouseFilter = MouseFilterEnum.Ignore;
        Size = new Vector2(1920, 1080);
        light = WorldType.Light(new Vector2(520, 200), Style.Ember with { A = 0 });
        // Mirrored about her, where she lies at the screen's middle: "Get up" set flush to the
        // gap's left side, "Let the night go" flush to its right, each line under its word the
        // same way, on one baseline (a centred row put the gap off her by the words' difference).
        var up = Choice(Act.Confirm, "Get up", risesLeft == 1 ? "Once, this night: back where you last stood fast." : "Back where you last stood fast.", Style.EmberHi, 34, rise, true, out var upHead);
        var go = Choice(Act.Cancel, "Let the night go", "The night is lost. The day comes on without it.", new Color("#cfc4b0"), 34, letGo, false, out _);
        const float half = 90, y = 560;
        up.Position = new Vector2(960 - half - up.CustomMinimumSize.X, y);
        go.Position = new Vector2(960 + half, y);
        AddChild(up);
        AddChild(go);
        // (the light sits behind the words "Get up" themselves, at the button's right)
        float hw = upHead.GetCombinedMinimumSize().X;
        light.Position = new Vector2(up.CustomMinimumSize.X - hw / 2, upHead.GetCombinedMinimumSize().Y / 2) - light.Size / 2;
        light.ShowBehindParent = true;
        up.AddChild(light);
        Modulate = Colors.Transparent;
    }

    static Control Choice(Act key, string title, string line, Color ink, int size, Action pick, bool towardRight, out Control head)
    {
        var b = new Button { FocusMode = FocusModeEnum.None, Flat = true, MouseDefaultCursorShape = CursorShape.PointingHand };
        foreach (var s in new[] { "normal", "hover", "pressed", "focus" }) b.AddThemeStyleboxOverride(s, new StyleBoxEmpty());
        var h = new HBoxContainer { MouseFilter = MouseFilterEnum.Ignore, Alignment = towardRight ? BoxContainer.AlignmentMode.End : BoxContainer.AlignmentMode.Begin };
        h.AddThemeConstantOverride("separation", 14);
        var cap = Style.Prompt(key);
        cap.SizeFlagsVertical = SizeFlags.ShrinkCenter;
        h.AddChild(cap);
        var word = WorldType.Lettering(title.ToUpperInvariant(), Style.Display, size, ink);
        h.AddChild(word);
        head = h;
        var col = new VBoxContainer { MouseFilter = MouseFilterEnum.Ignore };
        col.AddThemeConstantOverride("separation", 6);
        col.AddChild(h);
        var under = WorldType.Lettering(line, Style.TextItalic, 18, new Color("#d8cebc"));
        under.HorizontalAlignment = towardRight ? HorizontalAlignment.Right : HorizontalAlignment.Left;
        col.AddChild(under);
        b.AddChild(col);
        b.CustomMinimumSize = col.GetCombinedMinimumSize();
        col.Size = b.CustomMinimumSize;
        col.Position = new Vector2(0, 0);
        b.MouseEntered += () => word.AddThemeColorOverride("font_color", ink.Lightened(0.25f));
        b.MouseExited += () => word.AddThemeColorOverride("font_color", ink);
        b.Pressed += pick;
        return b;
    }

    public override void _Process(double delta)
    {
        t += delta;
        Modulate = Colors.White with { A = (float)Math.Clamp(t / 0.5, 0, 1) };
        // The ember's light behind "Get up", breathing while it waits.
        light.Modulate = Style.Ember with { A = 0.22f + 0.08f * Mathf.Sin((float)t * 2.1f) };
    }
}

/// <summary>
/// A choice the story puts to her (StoryChoice: spare him, or finish it), held over the live world while
/// he lies there, with no box and no shade (the world is the picture): his name small, the choice named in
/// display type, and its answers side by side, each its key and its words, alike in weight (nothing
/// chooses for her). It comes up a breath after he goes down, under the bar and over the fight. A key is
/// held to choose: a ledger line under its words fills as it is held. A click chooses at once.
/// </summary>
public partial class StoryChoices : Control
{
    double t;
    readonly VBoxContainer column;
    /// <summary>Each answer: its button, its words and their row, the ledger line under them and its fill.</summary>
    sealed class Answer
    {
        public required Button Button;
        public required VBoxContainer Col;
        public required HBoxContainer Head;
        public required Label Word;
        public required Control Track;
        public required ColorRect Line, Fill;
        public required Color Ink;
    }
    readonly System.Collections.Generic.List<Answer> answers = new();
    int held = -1;
    float heldK;
    /// <summary>Where its top stands: the banner's place in the upper third (the boss's bar has gone), clear
    /// of the fight round her.</summary>
    const float Top = 1080 * 0.2f;

    public StoryChoices(StoryChoice c, Act[] keys, Action<int> pick)
    {
        MouseFilter = MouseFilterEnum.Ignore;
        Size = new Vector2(1920, 1080);
        column = new VBoxContainer { MouseFilter = MouseFilterEnum.Ignore, Alignment = BoxContainer.AlignmentMode.Center };
        column.AddThemeConstantOverride("separation", 2);
        // His name over it as the banner's kicker is set, the choice in the banner's place and type.
        var who = WorldType.Lettering(c.Who.ToUpperInvariant(), Style.UiHeavy, 16, new Color("#ffcf8a"));
        who.HorizontalAlignment = HorizontalAlignment.Center;
        column.AddChild(who);
        var title = WorldType.Lettering(c.Title.ToUpperInvariant(), Style.Display, 40, new Color("#e2dac8"));
        title.HorizontalAlignment = HorizontalAlignment.Center;
        column.AddChild(title);
        column.AddChild(new Control { CustomMinimumSize = new Vector2(0, 16), MouseFilter = MouseFilterEnum.Ignore });
        var row = new HBoxContainer { MouseFilter = MouseFilterEnum.Ignore, Alignment = BoxContainer.AlignmentMode.Center };
        row.AddThemeConstantOverride("separation", 96);
        for (int i = 0; i < c.Answers.Count && i < keys.Length; i++)
        {
            int at = i;
            // Mercy in the moon's pale, the end in the ember's red: two colours, one weight.
            var ink = c.Answers[i].Id == "finish" ? new Color("#ff8a62") : new Color("#dce4ea");
            row.AddChild(Make(keys[i], c.Answers[i].Verb, ink, () => pick(at)));
        }
        row.SizeFlagsHorizontal = SizeFlags.ShrinkCenter;
        column.AddChild(row);
        column.AddChild(new Control { CustomMinimumSize = new Vector2(0, 8), MouseFilter = MouseFilterEnum.Ignore });
        var how = WorldType.Lettering("Hold to choose", Style.TextItalic, 17, new Color("#cfc4b0") with { A = 0.85f });
        how.HorizontalAlignment = HorizontalAlignment.Center;
        column.AddChild(how);
        AddChild(column);
        Modulate = Colors.Transparent;
    }

    Control Make(Act key, string verb, Color ink, Action pick)
    {
        var b = new Button { FocusMode = FocusModeEnum.None, Flat = true, MouseDefaultCursorShape = CursorShape.PointingHand };
        foreach (var s in new[] { "normal", "hover", "pressed", "focus" }) b.AddThemeStyleboxOverride(s, new StyleBoxEmpty());
        var head = new HBoxContainer { MouseFilter = MouseFilterEnum.Ignore, Alignment = BoxContainer.AlignmentMode.Center };
        head.AddThemeConstantOverride("separation", 14);
        var cap = Style.Prompt(key);
        cap.SizeFlagsVertical = SizeFlags.ShrinkCenter;
        head.AddChild(cap);
        var word = WorldType.Lettering(verb.ToUpperInvariant(), Style.Display, 30, ink);
        head.AddChild(word);
        var col = new VBoxContainer { MouseFilter = MouseFilterEnum.Ignore };
        col.AddThemeConstantOverride("separation", 6);
        col.AddChild(head);
        // The ledger line under the words: faint, filling in their colour as the key is held.
        var track = new Control { CustomMinimumSize = new Vector2(1, 2), MouseFilter = MouseFilterEnum.Ignore };
        var line = new ColorRect { Size = new Vector2(1, 2), Color = ink with { A = 0.22f }, MouseFilter = MouseFilterEnum.Ignore };
        var fill = new ColorRect { Size = new Vector2(0, 2), Color = ink, MouseFilter = MouseFilterEnum.Ignore };
        track.AddChild(line);
        track.AddChild(fill);
        col.AddChild(track);
        b.AddChild(col);
        b.MouseEntered += () => word.AddThemeColorOverride("font_color", ink.Lightened(0.25f));
        b.MouseExited += () => word.AddThemeColorOverride("font_color", ink);
        b.Pressed += pick;
        answers.Add(new Answer { Button = b, Col = col, Head = head, Word = word, Track = track, Line = line, Fill = fill, Ink = ink });
        return b;
    }

    /// <summary>The answer whose key is held (-1: none), and how far to choosing it.</summary>
    public void Held(int i, float k)
    {
        held = i;
        heldK = k;
        for (int j = 0; j < answers.Count; j++)
            answers[j].Word.AddThemeColorOverride("font_color", j == i ? answers[j].Ink.Lightened(0.2f * k) : answers[j].Ink);
    }

    public override void _Process(double delta)
    {
        t += delta;
        // Each answer as wide as its words, its line as wide as them (a button does not size to what is in it,
        // and measured before its words were in the tree the two ran into each other).
        for (int j = 0; j < answers.Count; j++)
        {
            var a = answers[j];
            float w = a.Head.GetCombinedMinimumSize().X;
            a.Track.CustomMinimumSize = new Vector2(w, 2);
            a.Line.Size = new Vector2(w, 2);
            a.Fill.Size = new Vector2(j == held ? w * heldK : 0, 2);
            a.Button.CustomMinimumSize = a.Col.GetCombinedMinimumSize();
        }
        var s = column.GetCombinedMinimumSize();
        column.Size = s;
        column.Position = new Vector2((1920 - s.X) / 2, Top);
        // A breath after he goes down (his words land first), then it comes up.
        Modulate = Colors.White with { A = (float)Math.Clamp((t - 0.45) / 0.4, 0, 1) };
    }
}

/// <summary>
/// A tip, centred in the upper third with no panel (the owner: "a centered attention grabbing
/// thing that is also not on a cheap looking backdrop and just stylized readable text"): the key
/// line in display type, a quieter line under it, its keys drawn as the keys themselves. It burns
/// in from an ember glow, holds long enough to read, then fades. One word, the tip's subject where
/// it appears in the line, is marked in ember. It is shown at its full size from the first (the
/// owner: shrinking from big to small was "more distracting not less"), and waits while a banner
/// holds the upper third.
/// </summary>
public partial class TipLine : Control
{
    public double T;
    readonly Control column;
    readonly TextureRect burn;
    /// <summary>Waiting (a banner holds the upper third): unseen, and its burning in not yet begun.</summary>
    public bool Held;
    /// <summary>The Flare's labels alpha (0 to 1), multiplied into its fade; its children ignore SelfModulate.</summary>
    public float Fade = 1;

    public TipLine(string title, string text, Control? keys)
    {
        MouseFilter = MouseFilterEnum.Ignore;
        column = new VBoxContainer { MouseFilter = MouseFilterEnum.Ignore, Alignment = BoxContainer.AlignmentMode.Center };
        column.AddThemeConstantOverride("separation", 6);
        var head = new HBoxContainer { MouseFilter = MouseFilterEnum.Ignore, Alignment = BoxContainer.AlignmentMode.Center };
        head.AddThemeConstantOverride("separation", 12);
        if (keys != null) { keys.SizeFlagsVertical = SizeFlags.ShrinkCenter; head.AddChild(keys); }
        head.AddChild(WorldType.Lettering(title.ToUpperInvariant(), Style.Display, 30, new Color("#f2e8d4")));
        column.AddChild(head);
        // The line under it, the tip's subject marked in ember once.
        var line = new RichTextLabel { BbcodeEnabled = true, FitContent = true, ScrollActive = false, MouseFilter = MouseFilterEnum.Ignore, AutowrapMode = TextServer.AutowrapMode.WordSmart };
        line.AddThemeFontOverride("normal_font", Style.Text);
        line.AddThemeFontSizeOverride("normal_font_size", 20);
        line.AddThemeColorOverride("default_color", new Color("#e6dccb"));
        line.AddThemeColorOverride("font_outline_color", new Color(0.03f, 0.02f, 0.02f, 0.85f));
        line.AddThemeConstantOverride("outline_size", 6);
        line.AddThemeColorOverride("font_shadow_color", new Color(0, 0, 0, 0.6f));
        line.AddThemeConstantOverride("shadow_offset_y", 2);
        line.AddThemeConstantOverride("shadow_outline_size", 8);
        // (a key the words name stands in them as its keycap: "{key:I}" in a tip's text, round 2 judge)
        string marked = Marked(text, title);
        line.PushParagraph(HorizontalAlignment.Center);
        int at = 0;
        foreach (Match m in KeyToken.Matches(marked))
        {
            line.AppendText(marked[at..m.Index]);
            line.AddImage(Chip(m.Groups[1].Value), 0, 0, Colors.White, InlineAlignment.Center);
            at = m.Index + m.Length;
        }
        line.AppendText(marked[at..]);
        line.Pop();
        float widest = KeyToken.Replace(text.Replace("*", ""), "  $1  ").Split('\n').Max(l => Style.Text.GetStringSize(l, HorizontalAlignment.Left, -1, 20).X);
        line.CustomMinimumSize = new Vector2(Balanced(KeyToken.Replace(text.Replace("*", ""), "  $1  "), Math.Min(720, widest + 10)), 0);
        column.AddChild(line);
        burn = WorldType.Light(new Vector2(760, 150), Style.Ember with { A = 0 });
        AddChild(burn);
        AddChild(column);
        Modulate = Colors.Transparent;
    }

    /// <summary>The wrap width, narrowed (never under 70%) until no wrapped line of the text ends in a lone word or two
    /// (a last line under 35% of the width). Measured once, as the tip is built.</summary>
    static float Balanced(string text, float w0)
    {
        float Last(string para, float w)
        {
            float cur = 0, space = Style.Text.GetStringSize(" ", HorizontalAlignment.Left, -1, 20).X;
            bool wrapped = false;
            foreach (var word in para.Split(' ', StringSplitOptions.RemoveEmptyEntries))
            {
                float ww = Style.Text.GetStringSize(word, HorizontalAlignment.Left, -1, 20).X;
                if (cur > 0 && cur + space + ww > w) { cur = ww; wrapped = true; }
                else cur += (cur > 0 ? space : 0) + ww;
            }
            return wrapped ? cur / w : 1;
        }
        float best = w0, bestMin = 0;
        for (float w = w0; w >= w0 * 0.7f; w -= w0 * 0.03f)
        {
            float worst = text.Split('\n').Min(p => Last(p, w));
            if (worst >= 0.35f) return w;
            if (worst > bestMin) { bestMin = worst; best = w; }
        }
        return best;
    }

    static readonly Regex KeyToken = new(@"\{key:([^}]+)\}");

    /// <summary>A keycap for the words, drawn once into a small viewport that stays with the tip, its texture
    /// set inline in the line: the shared keycap (Style.KeyCap), as the head's keys and the callouts draw it.</summary>
    Texture2D Chip(string key)
    {
        var cap = Style.KeyCap(key, 1.05f);
        var size = (Vector2I)cap.GetCombinedMinimumSize().Ceil();
        size = new Vector2I(Math.Max(size.X, Math.Max(28, 14 + 10 * key.Length)), Math.Max(size.Y, 28));
        cap.Size = size;
        var vp = new SubViewport { TransparentBg = true, Disable3D = true, Size = size, RenderTargetUpdateMode = SubViewport.UpdateMode.Always };
        vp.AddChild(cap);
        AddChild(vp);
        return vp.GetTexture();
    }

    /// <summary>The text with its subject (the title's word, where the text says it) marked in ember, once.</summary>
    static string Marked(string text, string title)
    {
        string safe = text.Replace("[", "[lb]");
        // A term the text marks itself ("*watchman's chest*") is colored whole.
        var hand = Regex.Match(safe, @"\*([^*]+)\*");
        if (hand.Success) return safe[..hand.Index] + "[color=#ffa04a]" + hand.Groups[1].Value + "[/color]" + safe[(hand.Index + hand.Length)..].Replace("*", "");
        // Else the title's words, last first, skipping the articles (a bare "the" is never the subject).
        var word = title.Split(' ', StringSplitOptions.RemoveEmptyEntries);
        foreach (var w0 in word.Reverse())
        {
            var w = w0.TrimEnd('s');
            if (w.Length < 3 || w.Equals("the", StringComparison.OrdinalIgnoreCase)) continue;
            var m = Regex.Match(safe, $@"\b{Regex.Escape(w)}\w*", RegexOptions.IgnoreCase);
            if (m.Success) return safe[..m.Index] + "[color=#ffa04a]" + m.Value + "[/color]" + safe[(m.Index + m.Length)..];
        }
        return safe;
    }

    /// <summary>Where its words are on the screen (what loot's labels give way to).</summary>
    public Rect2 Area => column.GetGlobalRect() with { Size = column.Size * column.Scale };

    public override void _Process(double delta)
    {
        if (Held) { Modulate = Colors.Transparent; return; }
        T += delta;
        var s = column.GetCombinedMinimumSize();
        column.Size = s;
        // Always at its full size (the owner: no shrinking from big to small).
        column.Position = new Vector2(-s.X / 2, 0);
        burn.Position = new Vector2(-380, s.Y / 2 - 75);
        // It burns in: the ember's glow first, the words coming up through it, then the glow cools away.
        float k = (float)Math.Clamp(T / 0.5, 0, 1);
        Modulate = Colors.White with { A = k * Fade };
        burn.Modulate = Style.Ember with { A = 0.32f * (float)Math.Max(0, 1 - Math.Abs(T - 0.25) / 0.6) };
    }
}
