using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Content;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Ui;

/// <summary>
/// Direction C, "The Day's Book" (docs/design/LAMPS_SCREEN_BRIEF.md §4, §7, §9, §12 C, §16; the mock is
/// tools/uiforge/lamps_mock/mock/frames_c.py and skins/c.py): the Lamps page around the board. Laid out absolutely in the
/// book's content rect, as the mock is (CONTENT (1030, 152)-(1876, 948) at 1080): the header row (the layouts, the
/// count, the keys), the board's window (LampBoard, y 232-874), the wick tabs (centered at y 911) and the prompt row
/// (y 971). Every piece draws its own type (one canvas item each), so the page costs a handful of draw calls.
/// </summary>
public partial class LampPage : Control
{
    /// <summary>The mock's rows, from the content rect's top (y 152 at 1080).</summary>
    public const float HeaderH = 80, BoardTop = 80, BoardH = 642, TabsY = 759, PromptY = 819, Height = 846;

    public readonly LampBoard Board;
    public readonly LampHeader Header;
    public readonly WickTabs Tabs;
    readonly HBoxContainer prompts;

    public LampPage(CharacterData ch, WorldState? w, string? zone)
    {
        MouseFilter = MouseFilterEnum.Pass;
        CustomMinimumSize = new Vector2(0, Height);
        SizeFlagsHorizontal = SizeFlags.ExpandFill;
        bool night = w?.Time == TimeOfDay.Night;
        AddChild(Header = new LampHeader(ch, w, zone));
        AddChild(Board = new LampBoard(ch, w));
        AddChild(Tabs = new WickTabs(ch));
        bool pad = Play.Controls.Instance?.UsingPad == true;
        prompts = LampInk.Row(night
            ? pad ? [("A", "Plan"), ("Y", "Light my way"), ("B", "Board")] : [("Click", "Plan"), ("Space", "Light my way"), ("Tab", "Board")]
            : pad ? [("A", "Choose a wick"), ("D-pad down", "Wick"), ("L3", "Find"), ("R3", "Home")]
                  : [("Click", "Choose a wick"), ("Tab", "Wick"), ("F", "Find"), ("H", "Home")], pad);
        AddChild(prompts);
        Resized += Lay;
        Lay();
    }

    /// <summary>The book's page sits at (1034, 154), 840 wide; C's content rect is (1030, 152), 846 wide: the page
    /// bleeds 4 px left, 2 px right and 2 px up so the board's window lands on the mock's (1030, 232)-(1876, 874).</summary>
    static readonly Vector2 Bleed = new(-4, -2);
    const float Wider = 6;

    void Lay()
    {
        float wd = Size.X + Wider;
        Header.Position = Bleed;
        Header.Size = new Vector2(wd, HeaderH);
        Board.Position = Bleed + new Vector2(0, BoardTop);
        Board.Size = new Vector2(wd, BoardH);
        Tabs.Position = Bleed + new Vector2(0, TabsY - WickTabs.H / 2);
        Tabs.Size = new Vector2(wd, WickTabs.H);
        var ps = prompts.GetCombinedMinimumSize();
        prompts.Size = ps;
        prompts.Position = Bleed + new Vector2(Mathf.Round((wd - ps.X) / 2), Mathf.Round(PromptY - ps.Y / 2));
    }
}

/// <summary>The page's type and colors (skins/a.py's), and drawing helpers for one-canvas-item controls.</summary>
public static class LampInk
{
    public static readonly Color Ink = new("#efe4cc"), Body = new("#d8cfbd"), Dim = new("#9b9282"), Gold = new("#e9c27a"),
        RimGold = new("#cdae72"), Red = new("#e0705a"), Cobalt = new("#8fb0ff"), Fire = new("#ff9a52"), Focus = new("#e8c87a"),
        Post = new("#e8b36a"), Dark = new("#07080b"), Gate = new("#c9a46a"), Chip = new("#d9c08a");

    static readonly Dictionary<string, Font> fonts = new();
    /// <summary>A house font (art/fonts/name.woff2), letterspaced by track px when asked.</summary>
    public static Font F(string name, int track = 0)
    {
        var key = $"{name}/{track}";
        if (fonts.TryGetValue(key, out var f)) return f;
        Font b = GD.Load<Font>($"res://art/fonts/{name}.woff2");
        return fonts[key] = track == 0 ? b : new FontVariation { BaseFont = b, SpacingGlyph = track };
    }

    public static float W(Font f, string s, int px) => f.GetStringSize(s, HorizontalAlignment.Left, -1, px).X;

    /// <summary>Text with its baseline at (x, y); align -1 left, 0 center, 1 right. Returns the advance.</summary>
    public static float Text(CanvasItem ci, Font f, int px, float x, float y, string s, Color c, int align = -1, float halo = 0, float haloA = 0.7f)
    {
        float w = W(f, s, px);
        float x0 = Mathf.Round(align < 0 ? x : align == 0 ? x - w / 2 : x - w);
        var at = new Vector2(x0, Mathf.Round(y));
        if (halo > 0)
        {
            ci.DrawStringOutline(f, at, s, HorizontalAlignment.Left, -1, px, (int)(halo * 2), Dark with { A = haloA * 0.45f * c.A });
            ci.DrawStringOutline(f, at, s, HorizontalAlignment.Left, -1, px, (int)halo, Dark with { A = haloA * c.A });
        }
        ci.DrawString(f, at, s, HorizontalAlignment.Left, -1, px, c);
        return w;
    }

    /// <summary>The house's rule: 1 px gold at 28%, its ends faded over 30 px.</summary>
    public static void Rule(CanvasItem ci, float x0, float x1, float y, float a = 0.28f)
    {
        var c = RimGold with { A = a };
        var z = RimGold with { A = 0 };
        y += 0.5f;
        ci.DrawPolylineColors([new(x0, y), new(x0 + 30, y), new(x1 - 30, y), new(x1, y)], [z, c, c, z], 1f, true);
    }

    /// <summary>Words broken greedily to fit maxw.</summary>
    public static List<string> Wrap(string s, Font f, int px, float maxw)
    {
        var lines = new List<string>();
        var cur = "";
        foreach (var word in s.Split(' ', StringSplitOptions.RemoveEmptyEntries))
        {
            var t = cur == "" ? word : cur + " " + word;
            if (cur == "" || W(f, t, px) <= maxw) cur = t;
            else { lines.Add(cur); cur = word; }
        }
        if (cur != "") lines.Add(cur);
        return lines;
    }

    /// <summary>A key cap as the device in hand has it: a pad button's art, else the book's key cap.</summary>
    public static Control Cap(string key, bool pad) =>
        pad && key is "A" or "B" or "X" or "Y" or "LB" or "RB" or "LT" or "RT" or "View" or "Menu" or "D-pad down" or "D-pad up" or "D-pad"
            ? Style.PadButton(key) : Style.Key(key);

    /// <summary>The book's prompt row: each cap, then its word (Alegreya Sans 16), 32 px between.</summary>
    public static HBoxContainer Row(IEnumerable<(string Key, string Word)> items, bool pad, int size = 16, int sep = 32)
    {
        var h = Style.H(sep);
        h.MouseFilter = Control.MouseFilterEnum.Ignore;
        foreach (var (k, wd) in items)
        {
            var one = Style.H(9, Cap(k, pad), Style.Label(wd, Style.Ui, size, Body with { A = 0.95f }, false, HorizontalAlignment.Left, false));
            one.Alignment = BoxContainer.AlignmentMode.Center;
            h.AddChild(one);
        }
        return h;
    }
}

/// <summary>
/// The header row (§4, §9, §12 C; skins/c.py header()): left, the three layout coins (32 px, I II III, the active one
/// lit) and the layout's name (Alegreya 700 17, her type's: "The Sunderer"); center, "3 LAMPS TO LIGHT" (Cinzel 700 30
/// and 600 16 letterspaced, warm gold), under it what was earned (Alegreya Sans 14, dim) and by day at a town's
/// lamp-post the warm italic line (by night, the board is read-only); right, Light my way and Open wide with their caps.
/// </summary>
public partial class LampHeader : Control
{
    readonly int count, active;
    readonly string sub, name;
    readonly string? post, night;
    readonly HBoxContainer keys;

    public LampHeader(CharacterData ch, WorldState? w, string? zone)
    {
        MouseFilter = MouseFilterEnum.Ignore;
        count = Math.Max(0, LampBook.Spare(ch, w));
        var st = LampBook.State(ch);
        active = st.Active;
        var type = LampBook.Now(ch).Type;
        var road = Lamps.Roads.TryGetValue(type, out var r) ? r.Name : "";
        name = road.StartsWith("Road of the ") ? "The " + road[12..] : road;
        int lit = LampBook.Now(ch).Lit.Count, levels = Math.Max(0, ch.Level - 1), story = LampBook.StoryLamps(w),
            atlas = LampBook.AtlasLit(w), posts = LampBook.PostLamps(w);
        var parts = new List<string> { $"{levels} from levels" };
        if (story > 0) parts.Add($"{story} from the story");
        if (atlas > 0) parts.Add($"{atlas} from the atlas");
        if (posts > 0) parts.Add($"{posts} from the lamp-posts");
        sub = $"{lit} lit  ·  {string.Join(", ", parts)}";
        bool isNight = w?.Time == TimeOfDay.Night;
        if (isNight) night = "By night the board is read-only";
        else if (LampBook.LayoutsOpen(w, zone))
            post = $"At the {Style.Cap1(zone ?? "")}’s lamp-post: lamps go out free";
        bool pad = Play.Controls.Instance?.UsingPad == true;
        keys = LampInk.Row(pad ? [("Y", "Light my way"), ("View", "Open wide")] : [("Space", "Light my way"), ("Z", "Open wide")], pad, 16, 22);
        AddChild(keys);
        Resized += Lay;
    }

    const float Yb = 28;            // the count's baseline (skins/c.py: y0 + 28)
    float Ccy => Yb - 9;            // the coins' and keys' middle

    void Lay()
    {
        var s = keys.GetCombinedMinimumSize();
        keys.Size = s;
        keys.Position = new Vector2(Mathf.Round(Size.X - s.X), Mathf.Round(Ccy - s.Y / 2));
    }

    public override void _Draw()
    {
        float cx = Size.X / 2;
        var fnum = LampInk.F("cinzel-700");
        var fw = LampInk.F("cinzel-600", 3);
        string num = count.ToString(), words = count == 1 ? "LAMP TO LIGHT" : "LAMPS TO LIGHT";
        float wn = LampInk.W(fnum, num, 30), ww = LampInk.W(fw, words, 16) - 3;
        float xs = cx - (wn + 10 + ww) / 2;
        LampInk.Text(this, fnum, 30, xs, Yb, num, LampInk.Gold);
        LampInk.Text(this, fw, 16, xs + wn + 10, Yb - 1, words, LampInk.Gold with { A = 0.95f });
        LampInk.Text(this, LampInk.F("alegreya-sans-400"), 14, cx, Yb + 19, sub, LampInk.Dim, 0);
        if (post != null) LampInk.Text(this, LampInk.F("alegreya-400-italic"), 15, cx, Yb + 38, post, LampInk.Post with { A = 0.95f }, 0);
        if (night != null) LampInk.Text(this, LampInk.F("alegreya-400-italic"), 15, cx, Yb + 38, night, LampInk.Dim with { A = 0.85f }, 0);
        for (int i = 0; i < 3; i++) Coin(this, new Vector2(16 + i * 40, Ccy), ArtsScreen.Numerals[i], i == active);
        LampInk.Text(this, LampInk.F("alegreya-700"), 17, 16 + 2 * 40 + 28, Ccy + 6, name, LampInk.Ink with { A = 0.95f });
    }

    /// <summary>A layout coin (skins/a.py coin()): bronze, 32 px; the active one lit, its numeral warm.</summary>
    public static void Coin(CanvasItem ci, Vector2 c, string numeral, bool on)
    {
        const float R = 16;
        if (on)
        {
            for (int k = 6; k >= 1; k--) ci.DrawCircle(c, R + k * 2.2f, new Color("#ffb04a") with { A = 0.022f }, true, -1, true);
            ci.DrawCircle(c, R, new Color("#2c2112"), true, -1, true);
            ci.DrawCircle(c + new Vector2(-3, -4), R * 0.62f, new Color("#5b4526") with { A = 0.55f }, true, -1, true);
            ci.DrawArc(c, R - 0.9f, 0, Mathf.Tau, 64, new Color("#e8c27a"), 1.8f, true);
            ci.DrawArc(c, R - 3.2f, 0, Mathf.Tau, 64, new Color("#a8823e") with { A = 0.6f }, 0.8f, true);
        }
        else
        {
            ci.DrawCircle(c, R, new Color("#1a150d") with { A = 0.92f }, true, -1, true);
            ci.DrawCircle(c + new Vector2(-3, -4), R * 0.6f, new Color("#2d2418") with { A = 0.5f }, true, -1, true);
            ci.DrawArc(c, R - 0.6f, 0, Mathf.Tau, 64, new Color("#6b5532") with { A = 0.85f }, 1.2f, true);
        }
        LampInk.Text(ci, LampInk.F("cinzel-700"), 14, c.X + 0.5f, c.Y + 5, numeral, on ? new Color("#ffe2a6") : new Color("#7d6a4c"), 0);
    }
}

/// <summary>
/// The wick tabs (§12 C, §16; skins/c.py tabs()): "WICKS" in small caps, her carried skills as the HUD's own seats
/// (its bronze ring and river-glass well with the skill's gold inlay, at 56 px), a hairline, then "All learned". The
/// chosen tab wears the gold ring. Choosing opens the wick panel (phase 4); here it only moves the choice.
/// </summary>
public partial class WickTabs : Control
{
    public const float H = 64, D = 56, Pitch = 70;
    public int Chosen { get; private set; }
    public event Action<int>? ChosenChanged;
    readonly List<(Socket S, int Index)> seats = new();
    readonly Socket empty;
    readonly GlyphMark scroll = new("scroll", 24, new Color("#d6c4a0") with { A = 0.85f });
    readonly Control row = new() { MouseFilter = MouseFilterEnum.Ignore };
    float lead, allX;
    const string Lead = "WICKS", All = "All learned";
    /// <summary>The tab centers in this control (the wick stem rises from these in phase 4).</summary>
    public readonly List<Vector2> Centers = new();

    public WickTabs(CharacterData ch)
    {
        MouseFilter = MouseFilterEnum.Pass;
        AddChild(row);
        int i = 0;
        foreach (var (id, _) in SkillBook.Carried(ch))
        {
            if (!Weapons.All.TryGetValue(id, out var wd) || i >= 6) continue;
            var s = new Socket { Index = i, Scale = Vector2.One * K };
            s.Show(id, wd.Art, ItemViews.SchoolColors[wd.School], 1, 0, Weapons.MaxRank, false, false);
            row.AddChild(s);
            seats.Add((s, i++));
        }
        empty = new Socket { Index = 5, Scale = Vector2.One * K };
        empty.Empty();
        row.AddChild(empty);
        row.AddChild(scroll);
        Resized += Lay;
    }

    /// <summary>The HUD seat's bezel (36.6 px out) to the tab's 56 px.</summary>
    static float K => D / (2 * 36.6f);

    float Total(out float ldw, out float lw)
    {
        ldw = LampInk.W(LampInk.F("alegreya-sans-700", 2), Lead, 13) - 2;
        lw = LampInk.W(Style.Ui, All, 15);
        int n = seats.Count;
        return ldw + 20 + n * D + Math.Max(0, n - 1) * (Pitch - D) + 26 + D + 8 + lw;
    }

    void Lay()
    {
        float tot = Total(out var ldw, out _);
        float x = Mathf.Round(Size.X / 2 - tot / 2), cy = Size.Y / 2;
        lead = x;
        x += ldw + 20;
        Centers.Clear();
        foreach (var (s, _) in seats)
        {
            var c = new Vector2(x + D / 2, cy);
            s.Position = c - s.Size / 2;
            s.PivotOffset = s.Size / 2;
            Centers.Add(c);
            x += Pitch;
        }
        if (seats.Count > 0) x += D - Pitch;
        x += 26;
        allX = x;
        var ce = new Vector2(x + D / 2, cy);
        empty.Position = ce - empty.Size / 2;
        empty.PivotOffset = empty.Size / 2;
        Centers.Add(ce);
        scroll.Position = ce - scroll.Size / 2;
        QueueRedraw();
    }

    public override void _GuiInput(InputEvent e)
    {
        if (e is not InputEventMouseButton { Pressed: true, ButtonIndex: MouseButton.Left } mb) return;
        for (int i = 0; i < Centers.Count; i++)
            if (mb.Position.DistanceTo(Centers[i]) <= D / 2 + 2) { Choose(i); AcceptEvent(); return; }
    }

    /// <summary>Move the choice (the last tab is All learned).</summary>
    public void Choose(int i)
    {
        i = Math.Clamp(i, 0, Centers.Count - 1);
        if (i == Chosen) return;
        Chosen = i;
        QueueRedraw();
        ChosenChanged?.Invoke(i);
    }

    public override void _Draw()
    {
        float cy = Size.Y / 2;
        Total(out _, out _);
        LampInk.Text(this, LampInk.F("alegreya-sans-700", 2), 13, lead, cy + 5, Lead, LampInk.Dim with { A = 0.95f });
        // the HUD's bronze ring under each seat's well (the plate bakes it in play; here each tab carries its own)
        foreach (var (s, idx) in seats) RingUnder(s.Position + s.Size / 2, idx);
        RingUnder(empty.Position + empty.Size / 2, 5);
        // the hairline, then All learned
        float hx = allX - 13;
        DrawLine(new Vector2(hx, cy - 18), new Vector2(hx, cy + 18), LampInk.RimGold with { A = 0.35f }, 1);
        LampInk.Text(this, Style.Ui, 15, allX + D + 8, cy + 5, All, LampInk.Body with { A = 0.95f });
        if (Chosen >= 0 && Chosen < Centers.Count)
        {
            var c = Centers[Chosen];
            for (int k = 4; k >= 1; k--) DrawArc(c, 29.5f, 0, Mathf.Tau, 72, LampInk.Focus with { A = 0.07f }, 2 + k * 2.5f, true);
            DrawArc(c, 29.5f, 0, Mathf.Tau, 72, LampInk.Focus, 2f, true);
        }
    }

    void RingUnder(Vector2 c, int idx)
    {
        if (DgRiver.Ring(idx) is not { } ring) { DrawArc(c, D / 2 - 2, 0, Mathf.Tau, 64, new Color("#7a5a30"), 4, true); return; }
        var rs = ring.GetSize() * K;
        DrawTextureRect(ring, new Rect2(c - rs / 2, rs), false);
    }
}

/// <summary>A line glyph (Glyphs) drawn at a size and color.</summary>
public partial class GlyphMark : Control
{
    readonly string key;
    readonly int px;
    readonly Color color;
    public GlyphMark(string key, int px, Color color)
    {
        this.key = key; this.px = px; this.color = color;
        MouseFilter = MouseFilterEnum.Ignore;
        Size = new Vector2(px, px);
    }
    public override void _Draw() => DrawTextureRect(Glyphs.Texture(key, px * 2, Colors.White, line: true), new Rect2(Vector2.Zero, Size), false, color);
}

/// <summary>What the focus card says (§7, in order; LampBoard words it from the lamp).</summary>
public sealed record LampCardText(string Name, string? Chip, Color ChipColor, string Place, string Line,
    IReadOnlyList<(string Glyph, bool Carried)> Feeds, string? FeedsText, string? Price, string State, Color StateColor,
    string? Fires, IReadOnlyList<(string Key, string Word)> Prompts);

/// <summary>
/// The focus card (§7, §16; skins/a.py card()): 380 px of smoked glass with the HUD's 1 px gold rim and a soft 20 px
/// drop shadow (black 45%), padding 16: the name (Alegreya 700 21) with the kind's chip at its right, the place
/// (Alegreya Sans 13 caps, dim), a rule, the one line (Alegreya 17, up to two lines), what it feeds (16 px glyphs,
/// carried gold, others gray), a blue lamp's price in red (Alegreya italic 16, #e0705a), a rule, the state line, a
/// link's pick, then this lamp's prompts.
/// </summary>
public partial class LampCard : Control
{
    public const float Wd = 380, Pad = 16;
    LampCardText? c;
    List<string> lines = new(), price = new();
    readonly HBoxContainer promptHost = new() { MouseFilter = MouseFilterEnum.Ignore };
    readonly StyleBoxFlat glass;
    float promptY;

    public LampCard()
    {
        MouseFilter = MouseFilterEnum.Ignore;
        Visible = false;
        glass = new StyleBoxFlat
        {
            BgColor = new Color("#0d1015") with { A = 0.86f }, BorderColor = LampInk.RimGold with { A = 0.70f },
            ShadowColor = new Color(0, 0, 0, 0.45f), ShadowSize = 20, ShadowOffset = new Vector2(0, 4), AntiAliasing = true,
        };
        glass.SetBorderWidthAll(1);
        glass.SetCornerRadiusAll(3);
        AddChild(promptHost);
    }

    static Font FName => LampInk.F("alegreya-700");
    static Font FPlace => LampInk.F("alegreya-sans-500", 1);
    static Font FLine => LampInk.F("alegreya-400");
    static Font FUi => Style.Ui;
    static Font FPrice => LampInk.F("alegreya-400-italic");

    /// <summary>Its height for these words (skins/a.py _card()'s rows).</summary>
    public static float HeightOf(LampCardText t, out List<string> lines, out List<string> price, out float promptY)
    {
        float iw = Wd - 2 * Pad;
        lines = t.Line != "" ? LampInk.Wrap(t.Line, FLine, 17, iw) : new();
        price = t.Price is { } p ? LampInk.Wrap(p, FPrice, 16, iw) : new();
        float y = Pad + 19 + 20 + 11 + 8 + 22 * lines.Count;
        if (t.FeedsText != null) y += 27;
        y += 21 * price.Count + 13 + 22;
        if (t.Fires != null) y += 22;
        promptY = 0;
        if (t.Prompts.Count > 0) { y += 27; promptY = y; }
        return y + Pad - 2;
    }

    public float Show(LampCardText t, bool pad)
    {
        c = t;
        float h = HeightOf(t, out lines, out price, out promptY);
        Size = new Vector2(Wd, h);
        foreach (var ch in promptHost.GetChildren()) { promptHost.RemoveChild(ch); ch.QueueFree(); }
        if (t.Prompts.Count > 0)
        {
            var row = LampInk.Row(t.Prompts, pad, 15, 20);
            promptHost.AddChild(row);
            var s = row.GetCombinedMinimumSize();
            promptHost.Position = new Vector2(Pad, promptY - 5 - s.Y / 2);
            promptHost.Size = s;
        }
        QueueRedraw();
        return h;
    }

    public override void _Draw()
    {
        if (c == null) return;
        DrawStyleBox(glass, new Rect2(Vector2.Zero, Size));
        DrawLine(new Vector2(3, 1.5f), new Vector2(Wd - 3, 1.5f), new Color(1, 1, 1, 0.06f), 1);
        float x0 = Pad, x1 = Wd - Pad, y = Pad;
        // the name, the chip at its right
        y += 19;
        float xc = x1;
        if (c.Chip != null) xc = Chip(x1, y - 2, c.Chip, c.ChipColor) - 8;
        LampInk.Text(this, FName, 21, x0, y, Ellipsize(c.Name, FName, 21, xc - x0), LampInk.Ink);
        y += 20;
        LampInk.Text(this, FPlace, 13, x0, y, c.Place, LampInk.Dim);
        y += 11;
        LampInk.Rule(this, x0, x1, y);
        y += 8;
        foreach (var ln in lines) { y += 22; LampInk.Text(this, FLine, 17, x0, y, ln, LampInk.Body); }
        if (c.FeedsText != null)
        {
            y += 27;
            float x = x0;
            foreach (var (g, carried) in c.Feeds)
            {
                DrawTextureRect(Glyphs.Texture(g, 32, Colors.White, line: true), new Rect2(x, y - 13, 16, 16), false, carried ? LampInk.Gold : LampInk.Dim);
                x += 21;
            }
            LampInk.Text(this, FUi, 15, x + 4, y, c.FeedsText, LampInk.Body with { A = 0.95f });
        }
        foreach (var ln in price) { y += 21; LampInk.Text(this, FPrice, 16, x0, y, ln, LampInk.Red); }
        y += 13;
        LampInk.Rule(this, x0, x1, y);
        y += 22;
        LampInk.Text(this, FUi, 15, x0, y, c.State, c.StateColor);
        if (c.Fires != null) { y += 22; LampInk.Text(this, FUi, 15, x0, y, c.Fires, LampInk.Body); }
    }

    /// <summary>The kind's chip, right-aligned at xr (Alegreya Sans 700 13 caps in a thin rounded outline); its left x.</summary>
    float Chip(float xr, float yb, string s, Color col)
    {
        var f = LampInk.F("alegreya-sans-700", 1);
        float w = LampInk.W(f, s, 13) - 1;
        float x0 = xr - w - 14;
        var box = new StyleBoxFlat { BgColor = (col * 0.25f) with { A = 0.35f }, BorderColor = col with { A = 0.55f }, AntiAliasing = true };
        box.SetBorderWidthAll(1);
        box.SetCornerRadiusAll(3);
        DrawStyleBox(box, new Rect2(x0, yb - 13.5f, xr - x0, 18));
        LampInk.Text(this, f, 13, x0 + 7, yb, s, col with { A = 0.95f });
        return x0;
    }

    static string Ellipsize(string s, Font f, int px, float maxw)
    {
        if (LampInk.W(f, s, px) <= maxw) return s;
        while (s.Length > 0 && LampInk.W(f, s + "…", px) > maxw) s = s[..^1].TrimEnd();
        return s + "…";
    }
}
