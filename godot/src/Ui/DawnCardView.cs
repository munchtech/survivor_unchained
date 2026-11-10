using System.Linq;
using System;
using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Play;

namespace SurvivorUnchained.Ui;

/// <summary>
/// The dawn's card (H8, N24): one storybook page at the middle of the screen over the held, dimmed
/// dawn, in the journal's parchment and ink. What the ember takes beside what she keeps, the last line,
/// and "Click to go on", which comes up once the card hears input (1.0 s in, so a held key does not skip it).
/// The words are Play.DawnCard's; this only draws them.
/// </summary>
public partial class DawnCardView : Control
{
    public const double Deaf = 1.0, In = 0.35, Out = 0.25;
    static readonly Color Ink = Style.ParchmentInk, InkSoft = new("#5a4a36"), HeadInk = new("#3a2414"), Red = new("#8a2a1a");

    double t, outT = -1;
    Action? go;
    readonly Control more;
    readonly Control card;

    /// <summary>Clicks and keys are heard (the first second is deaf).</summary>
    public bool Listening => t >= Deaf && outT < 0;

    public DawnCardView(DawnCard c, Action go)
    {
        this.go = go;
        Size = new Vector2(1920, 1080);
        MouseFilter = MouseFilterEnum.Stop;
        // The dawn under it, dimmed: darker at the edges, so the page is the brightest thing on the screen.
        var shade = new TextureRect
        {
            ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Scale, MouseFilter = MouseFilterEnum.Ignore,
            Texture = new GradientTexture2D
            {
                Gradient = new Gradient { Colors = [new Color(0.03f, 0.02f, 0.02f, 0.42f), new Color(0.02f, 0.01f, 0.01f, 0.78f)], Offsets = [0f, 1f] },
                Fill = GradientTexture2D.FillEnum.Radial, FillFrom = new Vector2(0.5f, 0.5f), FillTo = new Vector2(1.1f, 0.5f), Width = 256, Height = 256,
            },
            Size = Size,
        };
        AddChild(shade);

        var page = new VBoxContainer { MouseFilter = MouseFilterEnum.Ignore };
        page.AddThemeConstantOverride("separation", 0);
        page.AddChild(Words(c.Title, Style.Display, Style.Heading, HeadInk, HorizontalAlignment.Center));
        page.AddChild(Gap(12));
        page.AddChild(new InkRule(460) { SizeFlagsHorizontal = SizeFlags.ShrinkCenter });
        page.AddChild(Gap(22));
        var cols = new HBoxContainer { MouseFilter = MouseFilterEnum.Ignore, Alignment = BoxContainer.AlignmentMode.Center };
        cols.AddThemeConstantOverride("separation", 0);
        cols.AddChild(Column(c.TakesHead, c.Takes));
        cols.AddChild(new InkRule(0, true) { CustomMinimumSize = new Vector2(64, 0), SizeFlagsVertical = SizeFlags.ExpandFill });
        cols.AddChild(Column(c.KeepsHead, c.Keeps));
        page.AddChild(cols);
        // (M4 §5: one title, one line each of what the dark took and what she keeps, the go-on prompt; the closing
        // line, c.Last, stays in the card's words for M6 but is not laid out)
        page.AddChild(Gap(24));
        // (judge r1, 19: bare words, mouse only: a chip and the words, as the level card's prompt row: the mouse with its
        // left button lit, or the pad's A cap when a pad is in hand)
        var goRow = new HBoxContainer { MouseFilter = MouseFilterEnum.Ignore, Alignment = BoxContainer.AlignmentMode.Center };
        goRow.AddThemeConstantOverride("separation", 9);
        goRow.AddChild(new GoChip { SizeFlagsVertical = SizeFlags.ShrinkCenter });
        goRow.AddChild(Words("Go on", Style.Text, 19, Ink, HorizontalAlignment.Center));   // (judge 1: the card's serif, 19 px, in the darker ink)
        more = goRow;
        more.Modulate = Colors.Transparent;
        page.AddChild(more);

        var tex = UiArt.Tex("frames/dawn_paper.png") ?? UiArt.Tex("frames/paper.png");   // (the card's own untiled sheet; judge: no tone step inside)
        StyleBox box = tex == null ? Style.Paper(40) : new StyleBoxTexture
        {
            Texture = tex, TextureMarginLeft = 44, TextureMarginTop = 44, TextureMarginRight = 44, TextureMarginBottom = 44,
            AxisStretchHorizontal = StyleBoxTexture.AxisStretchMode.Stretch, AxisStretchVertical = StyleBoxTexture.AxisStretchMode.Stretch,
            ContentMarginLeft = 64, ContentMarginRight = 64, ContentMarginTop = 46, ContentMarginBottom = 34,
        };
        var panel = new PanelContainer { MouseFilter = MouseFilterEnum.Ignore, CustomMinimumSize = new Vector2(700, 0) };
        panel.AddThemeStyleboxOverride("panel", box);
        panel.AddChild(page);
        AddChild(panel);
        card = panel;
        Modulate = Colors.Transparent;
    }

    static Control Gap(float h) => new() { CustomMinimumSize = new Vector2(0, h), MouseFilter = MouseFilterEnum.Ignore };

    static Label Words(string text, Font font, int size, Color ink, HorizontalAlignment align = HorizontalAlignment.Left) =>
        Style.Label(text, font, size, ink, false, align, false);

    /// <summary>A column: its head in the storybook's capitals, its lines in the hand beneath.</summary>
    static Control Column(string head, IReadOnlyList<string> lines)
    {
        var col = new VBoxContainer { MouseFilter = MouseFilterEnum.Ignore, CustomMinimumSize = new Vector2(250, 0) };
        col.AddThemeConstantOverride("separation", 4);
        col.AddChild(Words(head.ToUpperInvariant(), Style.DisplayLight, Style.Small, Red, HorizontalAlignment.Center));
        col.AddChild(Gap(6));
        // (the column's items run together with a dot between two on one line. M4 lead 6: the lines are packed here,
        // not by the label's wrap, which left a dot hanging at a line's end: "Whirling Ember" and its dot alone)
        var rows = new List<string>();
        string row = "";
        foreach (var l in lines)
        {
            string both = row.Length == 0 ? l : row + " · " + l;
            if (row.Length > 0 && Style.Text.GetStringSize(both, HorizontalAlignment.Left, -1, Style.Lead).X > 250) { rows.Add(row); row = l; }
            else row = both;
        }
        if (row.Length > 0) rows.Add(row);
        var line = Style.Label(string.Join('\n', rows.Select(r => r.Replace(" ", "\u00A0"))), Style.Text, Style.Lead, Ink, true, HorizontalAlignment.Center, false);
        line.CustomMinimumSize = new Vector2(250, 0);
        col.AddChild(line);
        return col;
    }

    public override void _GuiInput(InputEvent e)
    {
        if (e is InputEventMouseButton { Pressed: true }) { Go(); AcceptEvent(); }
    }

    /// <summary>On (a click, or a key the game passes): the card fades out, then what waited goes on.</summary>
    public bool Go()
    {
        if (!Listening) return false;
        outT = 0;
        return true;
    }

    public override void _Process(double delta)
    {
        // (real time: the world under it is held)
        if (outT >= 0)
        {
            outT += delta;
            Modulate = Colors.White with { A = (float)Math.Clamp(1 - outT / Out, 0, 1) };
            if (outT >= Out) { var g = go; go = null; QueueFree(); g?.Invoke(); }
            return;
        }
        t += delta;
        float k = (float)Math.Clamp(t / In, 0, 1);
        Modulate = Colors.White with { A = k * k * (3 - 2 * k) };
        // Centered, the page settling a few pixels as it comes.
        var s = card.GetCombinedMinimumSize();
        card.Size = s;
        card.Position = new Vector2((1920 - s.X) / 2, (1080 - s.Y) / 2 + 10 * (1 - k));
        // "Go on" (chip and verb) comes up as the card begins to listen.
        more.Modulate = Colors.White with { A = (float)Math.Clamp((t - Deaf) / 0.3, 0, 1) };
    }

    /// <summary>The go-on prompt's chip, in the key caps' language (a dark chip, radius 3, a 1 px bronze rim, bone on
    /// ink): a mouse with its left button bone, or on a pad the A cap (its green half way to bone). Redrawn when the
    /// device in hand changes.</summary>
    partial class GoChip : Control
    {
        bool pad;

        public GoChip()
        {
            MouseFilter = MouseFilterEnum.Ignore;
            CustomMinimumSize = new Vector2(22, 22);
            pad = Controls.Instance is { UsingPad: true };
        }

        public override void _Process(double delta)
        {
            bool now = Controls.Instance is { UsingPad: true };
            if (now != pad) { pad = now; QueueRedraw(); }
        }

        public override void _Draw()
        {
            Color bone = new(240 / 255f, 230 / 255f, 208 / 255f), ground = new(22 / 255f, 18 / 255f, 14 / 255f, 242 / 255f), rim = new(138 / 255f, 108 / 255f, 70 / 255f);
            var chip = new Rect2(0, 0, 22, 22);
            var plate = new StyleBoxFlat { BgColor = ground, BorderColor = rim, AntiAliasing = true };
            plate.SetBorderWidthAll(1); plate.SetCornerRadiusAll(pad ? 11 : 3);
            DrawStyleBox(plate, chip);
            if (pad)
            {
                var f = Style.UiBold;
                const int fs = 16;
                float tw = f.GetStringSize("A", HorizontalAlignment.Left, -1, fs).X;
                DrawString(f, new Vector2(Mathf.Round(11 - tw / 2), 17), "A", HorizontalAlignment.Left, -1, fs, bone.Lerp(new Color("#6cc24a"), 0.5f));
                return;
            }
            // the mouse: 13 x 17, a bone outline on ink, the left button solid bone
            var r = new Rect2(4.5f, 2.5f, 13, 17);
            var body = new StyleBoxFlat { BgColor = new Color(10 / 255f, 8 / 255f, 6 / 255f), BorderColor = bone, AntiAliasing = true };
            body.SetBorderWidthAll(1);
            body.CornerRadiusTopLeft = body.CornerRadiusTopRight = 6;
            body.CornerRadiusBottomLeft = body.CornerRadiusBottomRight = 5;
            DrawStyleBox(body, r);
            float midX = r.Position.X + 6;
            var btn = new StyleBoxFlat { BgColor = bone, AntiAliasing = true, CornerRadiusTopLeft = 6 };
            DrawStyleBox(btn, new Rect2(r.Position.X, r.Position.Y, 6, 8));
            DrawRect(new Rect2(midX, r.Position.Y + 1, 1, 7), bone, true);
            DrawRect(new Rect2(r.Position.X + 1, r.Position.Y + 8, 11, 1), bone, true);
        }
    }

    /// <summary>An ink rule: a stroke thinning to nothing at its ends (or standing, between the columns).</summary>
    partial class InkRule : Control
    {
        readonly bool standing;

        public InkRule(float len, bool standing = false)
        {
            this.standing = standing;
            MouseFilter = MouseFilterEnum.Ignore;
            CustomMinimumSize = standing ? new Vector2(1, 0) : new Vector2(len, 10);
        }

        public override void _Draw()
        {
            var ink = Style.ParchmentInk with { A = 0.62f };
            var clear = ink with { A = 0 };
            if (standing)
            {
                float x = Size.X / 2, y0 = 6, y1 = Size.Y - 2, ym = (y0 + y1) / 2;
                var soft = ink with { A = 0.32f };
                DrawPolygon([new Vector2(x, y0), new Vector2(x + 0.8f, ym), new Vector2(x, y1), new Vector2(x - 0.8f, ym)], [clear, soft, clear, soft]);
                return;
            }
            float m = Size.Y / 2, mid = Size.X / 2;
            // Thick at the middle, a hair at the ends, a small lozenge on it.
            DrawPolygon([new Vector2(0, m), new Vector2(mid, m - 1.1f), new Vector2(Size.X, m), new Vector2(mid, m + 1.1f)], [clear, ink, clear, ink]);
            DrawColoredPolygon([new Vector2(mid - 6, m), new Vector2(mid, m - 4.5f), new Vector2(mid + 6, m), new Vector2(mid, m + 4.5f)], Style.ParchmentInk with { A = 0.8f });
        }
    }
}
