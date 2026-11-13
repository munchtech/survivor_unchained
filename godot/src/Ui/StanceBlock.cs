using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Ui;

/// <summary>bd-ui W3: the second weapon set as two round discs at the coin's right, mirroring the autos at its left. The
/// active set's disc stands in front, lit; the other behind it, smaller and dimmed; a swap trades them over 0.18 s. Each
/// disc carries its swap strike's cooldown as a sweep; the back disc, the one a swap would fire, wears a thin bright rim
/// when its strike is ready. The Swap key's cap at the block's right; the stance's name rises and fades over the block on
/// a swap. Hidden before level 8 (no second set) and in the arena. A child of Instrument, in its space.</summary>
public partial class StanceBlock : Control
{
    static readonly Color Glass = new(0.03f, 0.06f, 0.065f), Bronze = new("#d3a464"), Veil = new(0.02f, 0.015f, 0.01f, 0.62f);
    const float R = 16, BackScale = 0.70f, BackDim = 0.55f, EaseLen = 0.18f, NameLen = 1.2f, GlyphPx = 18;
    static readonly Vector2 Back = new(22, -6);
    static readonly Vector2 Front = new(1034, DgPanel.TopY - 13);

    /// <summary>A stance's color: set II's bezel and tint (set I: the plate's bronze).</summary>
    public static Color ColorOf(string? stanceId) => stanceId switch
    {
        "shield" => new Color("#8fb4d8"), "twin_blades" => new Color("#d4434e"), "mace" => new Color("#ff8a3a"), _ => Bronze,
    };

    readonly KeyTag swapKey = new(Act.Swap) { Chip = true };
    StanceDef? stance;
    bool inited;
    int active, swaps;
    double swapT = 1, nameT = NameLen, now;
    string nameText = "";
    Color nameColor = Bronze;
    readonly float[] share = [1, 1];
    readonly Texture2D?[] glyphs = new Texture2D?[2];
    string glyphFor = "";
    bool dirty = true;

    public StanceBlock()
    {
        MouseFilter = MouseFilterEnum.Ignore;
        TextureFilter = TextureFilterEnum.Linear;
        Size = new Vector2(1920, 1080);
        ZIndex = 2;
        AddChild(swapKey);
        swapKey.Place(1080, Front.Y - Instrument.TagH / 2);
        Visible = false;
    }

    public void Keys() => swapKey.Refresh();

    /// <summary>The key's label as the device in hand has it ("X", a pad button): the tip's last line.</summary>
    public string KeyName => swapKey.Shown2;

    /// <summary>The stance wearing the key seats now (Colors.Transparent: none; set I).</summary>
    public Color SeatTint(Battle b) => b.StanceNow is { } s ? ColorOf(s.Id) : Colors.Transparent;

    /// <summary>What the battle holds, each frame (values only).</summary>
    public void Feed(Battle b)
    {
        bool on = b.Campaign && b.StanceB != null;
        if (Visible != on) Visible = on;
        if (!on) { inited = false; return; }
        var st = b.StanceB!;
        int set = b.OnB ? 1 : 0;
        if (!inited) { inited = true; active = set; swapT = EaseLen; swaps = b.Swaps; nameT = NameLen; dirty = true; }
        if (set != active) { active = set; swapT = 0; dirty = true; }
        if (b.Swaps != swaps)
        {
            swaps = b.Swaps;
            nameT = 0;
            nameText = set == 1 ? st.Name.ToUpperInvariant() : "WARDEN";
            nameColor = set == 1 ? ColorOf(st.Id) : Bronze;
        }
        if (stance?.Id != st.Id) { stance = st; dirty = true; }
        if (glyphFor != st.Id)
        {
            glyphFor = st.Id;
            glyphs[0] = Glyphs.Texture(StanceText.Glyph(null), (int)GlyphPx, Bronze);
            glyphs[1] = Glyphs.Texture(StanceText.Glyph(st.Id), (int)GlyphPx, ColorOf(st.Id));
        }
        for (int s = 0; s < 2; s++)
        {
            float v = AutoRowModel.StrikeShare(b.StrikeReadyIn(s), b.StrikeOf(s)?.Cooldown ?? 6);
            if (Math.Abs(v - share[s]) > 0.004f) { share[s] = v; dirty = true; }
        }
    }

    public override void _Process(double delta)
    {
        now += delta;
        if (swapT < EaseLen) { swapT += delta; dirty = true; }
        if (nameT < NameLen) { nameT += delta; dirty = true; }
        if (dirty && Visible) { dirty = false; QueueRedraw(); }
    }

    // A set's disc this frame: middle, scale and dim (the active one forward).
    (Vector2 C, float S, float Dim) Disc(int set)
    {
        float e = Math.Clamp((float)(swapT / EaseLen), 0, 1);
        e = 1 - (1 - e) * (1 - e);
        float tf = set == active ? e : 1 - e;       // 0 behind .. 1 in front (a swap's old front shrinks back)
        if (swapT >= EaseLen) tf = set == active ? 1 : 0;
        return (Front + Back * (1 - tf), Mathf.Lerp(BackScale, 1f, tf), Mathf.Lerp(BackDim, 1f, tf));
    }

    /// <summary>Which disc a global point is over (0 set I, 1 set II; the front one first), or -1. Its global top middle.</summary>
    public (int Set, Vector2 Top)? Under(Vector2 global)
    {
        if (!Visible) return null;
        var xf = GetGlobalTransform();
        var local = xf.AffineInverse() * global;
        int[] order = active == 0 ? [0, 1] : [1, 0];
        foreach (int s in order)
        {
            var (c, sc, _) = Disc(s);
            if (local.DistanceTo(c) <= R * sc + 2) return (s, xf * new Vector2(c.X, c.Y - R * sc));
        }
        return null;
    }

    /// <summary>The hover card as (text, kind) lines: kind 0 the name, 1 plain, 2 a gift (pale gold), 3 a price (muted red),
    /// 4 muted.</summary>
    public List<(string Text, int Kind)> Tip(Battle b, int set)
    {
        var l = new List<(string, int)>();
        var strike = b.StrikeOf(set);
        string key = KeyName;
        if (set == 0)
        {
            l.Add(("Warden", 0));
            l.Add(("Her calling's own weapon: no gift, no price.", 4));
        }
        else if (b.StanceB is { } st)
        {
            l.Add((st.Name, 0));
            if (st.Flavor != "") l.Add((st.Flavor, 4));
            var (gifts, prices) = StanceText.Lines(st);
            foreach (var g in gifts) l.Add((g, 2));
            foreach (var p in prices) l.Add((p, 3));
        }
        if (strike != null) l.Add(($"Swap strike: {strike.Name}, {strike.Cooldown:0.#} s", 1));
        l.Add(($"Swap: {key}", 4));
        return l;
    }

    public override void _Draw()
    {
        if (!Visible || stance == null) return;
        int back = active == 0 ? 1 : 0;
        // (the one behind first; during the swap the two trade over the middle)
        int first = Disc(0).S < Disc(1).S ? 0 : 1;
        foreach (int s in new[] { first, 1 - first }) DrawOne(s, s == back && swapT >= EaseLen);
        if (nameT < NameLen && nameText != "")
        {
            float k = (float)(nameT / NameLen), rise = 10 * (1 - (1 - k) * (1 - k));
            var at = new Vector2(Front.X - 80, Front.Y - R - 12 - rise);
            DrawStringOutline(Style.UiBold, at, nameText, HorizontalAlignment.Center, 190, 13, 3, new Color(0.02f, 0.015f, 0.01f, 0.9f * (1 - k)));
            DrawString(Style.UiBold, at, nameText, HorizontalAlignment.Center, 190, 13, nameColor with { A = 1 - k });
        }
    }

    void DrawOne(int set, bool isBack)
    {
        var (c, sc, dim) = Disc(set);
        float r = R * sc;
        var col = set == 1 ? ColorOf(stance!.Id) : Bronze;
        float a = dim;
        DrawCircle(c, r, Glass with { A = a }, true, -1, true);
        if (glyphs[set] is { } g) DrawTextureRect(g, new Rect2(c - Vector2.One * GlyphPx * sc / 2, Vector2.One * GlyphPx * sc), false, new Color(1, 1, 1, a));
        float sh = share[set];
        if (sh < 0.996f) DrawColoredPolygon(CirclePie(c, r - 1, 1 - sh), Veil with { A = Veil.A * a });
        DrawArc(c, r, 0, Mathf.Tau, 48, col with { A = a }, 1.5f, true);
        // (the back disc's strike ready: a thin bright rim, the swap would fire it)
        if (isBack && sh >= 0.996f) DrawArc(c, r + 2, 0, Mathf.Tau, 48, col.Lightened(0.35f) with { A = 0.9f }, 1, true);
    }

    /// <summary>A circle's wedge from 12 o'clock clockwise, share (0..1) of the turn.</summary>
    static Vector2[] CirclePie(Vector2 c, float r, float share)
    {
        int n = Math.Max(2, (int)Math.Ceiling(share * 48));
        var p = new Vector2[n + 2];
        p[0] = c;
        for (int i = 0; i <= n; i++)
        {
            float ang = share * Mathf.Tau * i / n;
            p[i + 1] = c + new Vector2(Mathf.Sin(ang), -Mathf.Cos(ang)) * r;
        }
        return p;
    }
}

/// <summary>bd-ui W3: a plain hover card of colored lines (the stance's, the "+N" tile's), above a point. In the tip layer.</summary>
public partial class PlainTip : PanelContainer
{
    static readonly Color Pale = new("#f3d9a0"), Red = new("#c26a62"), Muted = new("#a89c88"), Parch = new("#e8dcc4");
    string key = "";
    readonly VBoxContainer v = new();

    public PlainTip()
    {
        MouseFilter = MouseFilterEnum.Ignore;
        Visible = false;
        var sb = new StyleBoxFlat { BgColor = new Color(0.04f, 0.035f, 0.04f, 0.94f), BorderColor = new Color("#8a6a3a"), ContentMarginLeft = 12, ContentMarginRight = 12, ContentMarginTop = 9, ContentMarginBottom = 9 };
        sb.SetBorderWidthAll(1);
        AddThemeStyleboxOverride("panel", sb);
        v.AddThemeConstantOverride("separation", 2);
        v.MouseFilter = MouseFilterEnum.Ignore;
        AddChild(v);
        CustomMinimumSize = new Vector2(220, 0);
    }

    /// <summary>Show lines (kind: 0 name, 1 plain, 2 gift, 3 price, 4 muted) with the card's bottom middle 10 px over foot, or hide.</summary>
    public void Set(bool show, Vector2 foot, IReadOnlyList<(string Text, int Kind)>? lines)
    {
        if (Visible != show) Visible = show;
        if (!show || lines == null) return;
        string k = string.Join("\n", lines.Select(l => $"{l.Kind}:{l.Text}"));
        if (k != key)
        {
            key = k;
            foreach (var c in v.GetChildren()) { v.RemoveChild(c); c.QueueFree(); }
            foreach (var (text, kind) in lines)
            {
                var (font, size, col) = kind switch { 0 => (Style.UiBold, 16, Style.GoldHi), 2 => (Style.Ui, 14, Pale), 3 => (Style.Ui, 14, Red), 4 => (Style.Ui, 13, Muted), _ => (Style.Ui, 14, Parch) };
                var lb = Style.Label(text, font, size, col, wrap: kind == 4 && text.Length > 40);
                if (kind == 4 && text.Length > 40) lb.CustomMinimumSize = new Vector2(260, 0);
                v.AddChild(lb);
            }
            Size = Vector2.Zero;
        }
        var s = GetCombinedMinimumSize();
        Size = s;
        Position = new Vector2(Mathf.Clamp(Mathf.Round(foot.X - s.X / 2), 8, 1920 - 8 - s.X), Mathf.Clamp(Mathf.Round(foot.Y - 10 - s.Y), 8, 1080 - 8 - s.Y));
    }
}
