using System;
using System.Text.RegularExpressions;
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

    public Notice(Control? icon, string text, string? sub, Color colour, bool noted, bool grand, double life)
    {
        Life = life;
        MouseFilter = MouseFilterEnum.Ignore;
        int size = grand ? 26 : 18;
        Title = WorldType.Lettering(text, grand ? Style.Display : Style.UiBold, size, colour);
        Title.Name = "Title";
        var row = new HBoxContainer { MouseFilter = MouseFilterEnum.Ignore };
        row.AddThemeConstantOverride("separation", 8);
        if (icon != null) { icon.SizeFlagsVertical = SizeFlags.ShrinkCenter; row.AddChild(icon); }
        row.AddChild(Title);
        if (!string.IsNullOrEmpty(sub))
        {
            var s = WorldType.Lettering(sub, Style.TextItalic, grand ? 17 : 15, new Color("#cfc4b0"));
            s.SizeFlagsVertical = SizeFlags.ShrinkEnd;
            row.AddChild(s);
        }
        var size2 = row.GetCombinedMinimumSize();
        if (noted)
        {
            // Its own light behind it, faint, the colour of what it is.
            light = WorldType.Light(new Vector2(size2.X + 60, size2.Y + 26), colour with { A = grand ? 0.4f : 0.22f });
            light.Position = new Vector2(-30, -13);
            AddChild(light);
        }
        body = row;
        AddChild(row);
        CustomMinimumSize = size2;
        float iconW = icon?.GetCombinedMinimumSize().X ?? 0;
        spark = new WorldType.Spark(colour, grand ? 72 : 48) { Position = new Vector2(iconW / 2 - (grand ? 36 : 24), size2.Y / 2 - (grand ? 36 : 24)) };
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
/// A tip, centred in the upper third with no panel (the owner: "a centered attention grabbing
/// thing that is also not on a cheap looking backdrop and just stylized readable text"): the key
/// line in display type, a quieter line under it, its keys drawn as the keys themselves. It burns
/// in from an ember glow, holds long enough to read, then fades. One word, the tip's subject where
/// it appears in the line, is marked in ember. Mid-fight it keeps small and high until a lull.
/// </summary>
public partial class TipLine : Control
{
    public double T;
    readonly Control column;
    readonly TextureRect burn;
    public bool Small;

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
        line.Text = $"[center]{Marked(text, title)}[/center]";
        line.CustomMinimumSize = new Vector2(Math.Min(720, Style.Text.GetStringSize(text, HorizontalAlignment.Left, -1, 20).X + 10), 0);
        column.AddChild(line);
        burn = WorldType.Light(new Vector2(760, 150), Style.Ember with { A = 0 });
        AddChild(burn);
        AddChild(column);
        Modulate = Colors.Transparent;
    }

    /// <summary>The text with its subject (the title's word, where the text says it) marked in ember, once.</summary>
    static string Marked(string text, string title)
    {
        string safe = text.Replace("[", "[lb]");
        var word = title.Split(' ', StringSplitOptions.RemoveEmptyEntries);
        foreach (var w in word.Length > 0 ? new[] { word[^1].TrimEnd('s'), word[0] } : Array.Empty<string>())
        {
            if (w.Length < 3) continue;
            var m = Regex.Match(safe, $@"\b{Regex.Escape(w)}\w*", RegexOptions.IgnoreCase);
            if (m.Success) return safe[..m.Index] + "[color=#ffa04a]" + m.Value + "[/color]" + safe[(m.Index + m.Length)..];
        }
        return safe;
    }

    public override void _Process(double delta)
    {
        T += delta;
        var s = column.GetCombinedMinimumSize();
        column.Size = s;
        float scale = Small ? 0.72f : 1;
        column.Scale = new Vector2(scale, scale);
        column.Position = new Vector2(-s.X * scale / 2, 0);
        burn.Position = new Vector2(-380, s.Y * scale / 2 - 75);
        // It burns in: the ember's glow first, the words coming up through it, then the glow cools away.
        float k = (float)Math.Clamp(T / 0.5, 0, 1);
        Modulate = Colors.White with { A = k };
        burn.Modulate = Style.Ember with { A = 0.32f * (float)Math.Max(0, 1 - Math.Abs(T - 0.25) / 0.6) };
    }
}
