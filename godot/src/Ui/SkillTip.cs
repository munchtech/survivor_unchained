using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Play;
using SurvivorUnchained.Content;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Ui;

/// <summary>
/// U1 §4: a skill's tooltip, in the HUD's own tooltip language (XpCard: the morocco card, UiArt "tooltip"). 380 wide,
/// as tall as its words: the name (display serif 20, gold) with its key chip at the right of the row, the small
/// upper-case How line, the plain line (wrapped, at most 3 lines), a thin bronze rule with a gold middle, the label/value
/// rows and the cost row last in gold. Built once per view, redrawn only when its view changes; per frame only its place.
/// </summary>
public partial class SkillTip : Control
{
    public const float W = 380, PadX = 16, PadY = 14;
    static readonly Color Gold = new("#f3d9a0"), Dim = new("#a89c88"), Parch = new("#e8dcc4"), Bone = new("#f6efe0"),
        RuleBronze = new Color("#8a6a3a") with { A = 0.55f }, RuleGold = new Color("#c9a35a") with { A = 0.8f };
    
    string key = "";
    SkillTipView? view;
    string how = "";
    readonly List<string> lines = new();
    float nameBase, howBase, lineBase, ruleY, rowBase;
    StyleBox? box;
    readonly Control capHost = new() { MouseFilter = MouseFilterEnum.Ignore };
    KeyTag? cap;
    Act? capAct;

    public SkillTip()
    {
        MouseFilter = MouseFilterEnum.Ignore;
        Size = new Vector2(W, 120);
        Visible = false;
        AddChild(capHost);
    }

    /// <summary>A weapon's cast as the taught build writes it (the card's How line): kindle, channel, hold, press or auto.</summary>
    public static string CastOf(WeaponInst w) => w.KindledNow ? "kindle" : w.Cast == CastMode.Channel ? "channel" : w.Hold ? "hold" : w.Pressed ? "press" : "auto";

    /// <summary>A skill's card where a fight may or may not run: the fight's own weapon (its key, its form) when it carries
    /// it; else the taught build's form (or its press's own kind) and the key of fallbackSlot.</summary>
    public static SkillTipView For(CharacterData ch, Battle? b, string id, int fallbackSlot)
    {
        if (b?.Weapons.Find(x => x.Id == id) is { } w)
            return SkillTipModel.Build(ch, b, id, CastOf(w), w.Slot >= 0 && w.Slot < KeyMap.Skills.Length ? KeyMap.Skills[w.Slot].ToString() : null);
        string cast = TaughtBuilds.Of(ch.Archetype)?.Slots.Find(x => x.Skill == id)?.Cast
            ?? (Weapons.All.TryGetValue(id, out var d) ? d.Press?.Kind switch { PressKind.Hold => "hold", PressKind.Channel => "channel", PressKind.Kindle => "kindle", null => "auto", _ => "press" } : "press");
        return SkillTipModel.Build(ch, null, id, cast, fallbackSlot >= 0 && fallbackSlot < KeyMap.Skills.Length ? KeyMap.Skills[fallbackSlot].ToString() : null);
    }

    /// <summary>How far UiArt's tooltip frame draws past the rect.</summary>
    public const float Out = 6;

    /// <summary>The view now shown (null when hidden).</summary>
    public SkillTipView? View => Visible ? view : null;

    bool compact;
    float width = W;
    string lastRect = "";

    /// <summary>The seat card: Compact, between the caps (capL..capR, the open span between the two bronze figures that end
    /// the seat row), centred on the seat then clamped 12 px inside them, its outer bottom edge 14 px above topY (the seat
    /// row's highest point); or hide it.</summary>
    public void SetSeat(bool show, float seatX, float topY, SkillTipView? v, float capL, float capR)
    {
        show = show && v != null && v.Name != "";
        if (Visible != show) Visible = show;
        if (!show) return;
        compact = true;
        float w = Mathf.Min(480, capR - capL - 24 - 2 * Out);
        Rebuild(v!, w);
        float x = Mathf.Clamp(seatX - Size.X / 2, capL + 12 + Out, capR - 12 - Out - Size.X);
        float y = Mathf.Max(8, topY - 14 - Out - Size.Y);
        Place(new Vector2(Mathf.Round(x), Mathf.Round(y)));
    }

    /// <summary>The level card's tip: its outer left edge 12 px right of the card, its outer bottom edge at the card's top;
    /// flipped to the card's left when the outer right edge would pass 1920 - 8.</summary>
    public void SetBeside(bool show, Rect2 card, SkillTipView? v)
    {
        show = show && v != null && v.Name != "";
        if (Visible != show) Visible = show;
        if (!show) return;
        compact = false;
        Rebuild(v!, W);
        float x = card.End.X + 12 + Out;
        if (x + Size.X + Out > 1920 - 8) x = card.Position.X - 12 - Out - Size.X;
        float y = Mathf.Clamp(card.Position.Y - Out - Size.Y, 8, 1080 - 8 - Size.Y);
        Place(new Vector2(Mathf.Round(x), Mathf.Round(y)));
    }

    void Place(Vector2 at)
    {
        if (Position != at) Position = at;
        if (!(HudPin.Active || Args.Has("lamps-tip"))) return;
        var g = GetGlobalPosition();
        string r = $"SKILLTIP rect {g.X - Out:0} {g.Y - Out:0} {g.X + Size.X + Out:0} {g.Y + Size.Y + Out:0}";
        if (r != lastRect) { lastRect = r; GD.Print(r); }
    }

    /// <summary>Show it with its foot's middle at foot (a 12 px gap above it; below foot when it would leave the top),
    /// clamped 8 px inside 1920x1080; or hide it. (The Lamps tab's tip: leftOf/bottomAt put it beside the panel.)</summary>
    public void Set(bool show, Vector2 foot, SkillTipView? v, float outerGap = -1, float leftOf = float.NaN, float bottomAt = float.NaN)
    {
        show = show && v != null && v.Name != "";
        if (Visible != show) Visible = show;
        if (!show) return;
        compact = false;
        Rebuild(v!, W);
        float px = GetParent() is Control pci ? pci.GetGlobalPosition().X : 0;
        if (!float.IsNaN(leftOf) && !float.IsNaN(bottomAt) && leftOf - Out - Size.X + px >= 8)
        {
            // (beside a panel: its outer right edge at leftOf, its outer bottom edge at bottomAt)
            Place(new Vector2(Mathf.Round(leftOf - Out - Size.X), Mathf.Clamp(Mathf.Round(bottomAt - Out - Size.Y), 8, 1080 - 8 - Size.Y)));
            return;
        }
        float y = foot.Y - Size.Y - (outerGap >= 0 ? outerGap + Out : 12);
        if (y < 8) y = foot.Y + (outerGap >= 0 ? outerGap + Out : 12);
        Place(new Vector2(Mathf.Clamp(Mathf.Round(foot.X - Size.X / 2), 8, 1920 - 8 - Size.X), Mathf.Clamp(Mathf.Round(y), 8, 1080 - 8 - Size.Y)));
    }

    void Rebuild(SkillTipView v, float w)
    {
        string k = KeyOf(v) + "|" + (compact ? "c" : "f") + w.ToString("0.#");
        if (k != key) { key = k; Build(v, w); }
    }

    /// <summary>--tip-audit: the compact card for a view at a width, built and measured, one TIPAUDIT line printed.</summary>
    public void Audit(SkillTipView v, float w)
    {
        compact = true;
        Build(v, w);
        key = "";
        GD.Print($"TIPAUDIT {v.Skill} h={Size.Y + 2 * Out:0} w={Size.X + 2 * Out:0} how={(lay.HowInline ? "inline" : "own")} lines={lay.Lines.Count} rows={lay.RowLines}");
    }

    static string KeyOf(SkillTipView v)
    {
        var sb = new System.Text.StringBuilder();
        sb.Append(v.Name).Append('|').Append(v.How).Append('|').Append(v.Line).Append('|').Append(v.Key);
        foreach (var r in v.Rows) sb.Append('|').Append(r.Label).Append('=').Append(r.Value);
        if (v.Cost is { } c) sb.Append("|$").Append(c.Label).Append('=').Append(c.Value);
        return sb.ToString();
    }

    static float TextW(Font f, string s, int size) => f.GetStringSize(s, HorizontalAlignment.Left, -1, size).X;

    static FontVariation? howFont;
    /// <summary>The How line's face: Alegreya Sans bold with lining figures (the old-style 3 dropped below the line).</summary>
    static Font HowFont => howFont ??= new FontVariation
    {
        BaseFont = Style.UiBold,
        OpentypeFeatures = new Godot.Collections.Dictionary { { TextServerManager.Singleton.GetPrimaryInterface().NameToTag("lnum"), 1 } },
    };

    static readonly System.Text.RegularExpressions.Regex Unit = new(@"(\d) ([MS])\b", System.Text.RegularExpressions.RegexOptions.Compiled);
    /// <summary>The How line in capitals, but a unit after a number stays lower-case ("10 m", "0.6 s": "10 M" reads as millions).</summary>
    public static string HowCaps(string s) => Unit.Replace(s.ToUpperInvariant(), m => m.Groups[1].Value + " " + m.Groups[2].Value.ToLowerInvariant());

    /// <summary>Word wrap by measuring with the font; never cuts (a number keeps its unit on its line).</summary>
    static List<string> Wrap(Font f, string s, int size, float width)
    {
        var o = new List<string>();
        if (string.IsNullOrWhiteSpace(s)) return o;
        s = System.Text.RegularExpressions.Regex.Replace(s, @"(\d) (m|s|%)\b", "$1 $2");
        string cur = "";
        foreach (var word in s.Split(' ', StringSplitOptions.RemoveEmptyEntries))
        {
            string t = cur == "" ? word : cur + " " + word;
            if (cur != "" && TextW(f, t, size) > width) { o.Add(cur); cur = word; }
            else cur = t;
        }
        if (cur != "") o.Add(cur);
        return o;
    }

    /// <summary>Wrap, then if the last line is a stub (under 45% of the width) re-wrap at the narrowest width (4 px steps, down to 60%) that keeps the same line count.</summary>
    static List<string> WrapBalanced(Font f, string s, int size, float width)
    {
        var o = Wrap(f, s, size, width);
        if (o.Count < 2 || TextW(f, o[^1], size) >= 0.45f * width) return o;
        for (float w = width - 4; w >= 0.6f * width; w -= 4)
        {
            var t = Wrap(f, s, size, w);
            if (t.Count != o.Count) break;
            o = t;
        }
        return o;
    }

    /// <summary>One label/value pair placed: its line, where the label starts, where the value ends (right-aligned).</summary>
    sealed record Cell(string Label, string Value, int Line, float LabelX, float ValueRight, bool Gold);
    sealed class Lay
    {
        public float NameBase, HowBase, HowX, LineBase, RuleY, RowBase, H;
        public bool HowInline;
        public string How = "";
        public List<string> Lines = new();
        public List<Cell> Cells = new();
        public int RowLines;
        public int NameSize, HowSize, LineSize, RowSize;
        public float LinePitch, RowPitch;
    }
    Lay lay = new();
    readonly HashSet<string> said = new();

    Lay Compute(SkillTipView v, float w, float chipW)
    {
        var L = new Lay
        {
            NameSize = compact ? 19 : 20, HowSize = compact ? 12 : 13, LineSize = compact ? 15 : 16, RowSize = compact ? 14 : 15,
            LinePitch = compact ? 19 : 21, RowPitch = compact ? 18 : 20, How = HowCaps(v.How),
        };
        float padX = compact ? 16 : PadX, padY = compact ? 10 : PadY, inner = w - 2 * padX;
        L.NameBase = padY + (compact ? 15 : 16);
        float y = L.NameBase;
        if (L.How != "")
        {
            float nameW = TextW(Style.Display, v.Name, L.NameSize), howW = TextW(HowFont, L.How, L.HowSize);
            float right = w - padX - (chipW > 0 ? chipW + 10 : 0);
            if (compact && padX + nameW + 16 + howW <= right) { L.HowInline = true; L.HowX = right - howW; }
            else { L.HowBase = y + (compact ? 4 : 6) + L.HowSize; y = L.HowBase; }
        }
        L.Lines = WrapBalanced(Style.Ui, v.Line, L.LineSize, inner);
        int maxLines = compact ? 2 : 3;
        if (L.Lines.Count > maxLines && said.Add(v.Skill + "|line")) GD.Print($"SKILLTIP OVERFLOW {v.Skill} line={L.Lines.Count}");
        if (L.Lines.Count > 0) { L.LineBase = y + 10 + L.LineSize; y = L.LineBase + (L.Lines.Count - 1) * L.LinePitch; }
        L.RuleY = y + (compact ? 8 : 10);
        L.RowBase = L.RuleY + (compact ? 8 : 10) + L.RowSize;
        var items = v.Rows.Select(r => (r.Label, r.Value, Gold: false)).ToList();
        if (v.Cost is { } c) items.Add((c.Label, c.Value, true));
        if (!compact)
        {
            for (int i = 0; i < items.Count; i++) L.Cells.Add(new Cell(items[i].Label, items[i].Value, i, padX, w - padX, items[i].Gold));
            L.RowLines = items.Count;
        }
        else
        {
            // two columns: a row that fits half the inner width (less a 24 px gutter) is a cell; cells pair in order, a lone
            // cell taking the next cell even past a full-width row
            float half = (inner - 24) / 2, xr = padX + half + 24;
            int line = 0, open = -1;
            foreach (var it in items)
            {
                bool cell = TextW(Style.Ui, it.Label, L.RowSize) + 12 + TextW(Style.UiBold, it.Value, L.RowSize) <= half;
                if (!cell) { L.Cells.Add(new Cell(it.Label, it.Value, line++, padX, w - padX, it.Gold)); continue; }
                if (open < 0) { open = line++; L.Cells.Add(new Cell(it.Label, it.Value, open, padX, padX + half, it.Gold)); }
                else { L.Cells.Add(new Cell(it.Label, it.Value, open, xr, w - padX, it.Gold)); open = -1; }
            }
            L.RowLines = line;
        }
        if (compact && L.RowLines > 2 && said.Add(v.Skill + "|rows")) GD.Print($"SKILLTIP OVERFLOW {v.Skill} rows={L.RowLines}");
        float bottom = L.RowLines > 0 ? L.RowBase + (L.RowLines - 1) * L.RowPitch : L.RuleY;
        L.H = Mathf.Ceil(bottom + (compact ? 3 : 4) + padY);
        return L;
    }

    void Build(SkillTipView v, float w)
    {
        view = v;
        width = w;
        // the key chip (the bar's own KeyTag), at the right of the name row
        Act? act = v.Key != null && Enum.TryParse<Act>(v.Key, out var a) ? a : null;
        if (act != capAct)
        {
            cap?.QueueFree();
            cap = null;
            capAct = act;
            if (act is { } ak)
            {
                cap = new KeyTag(ak) { Chip = true };
                capHost.AddChild(cap);
            }
        }
        cap?.Refresh();
        float cw = cap?.ChipBox().Size.X ?? 0;
        lay = Compute(v, w, cw);
        Size = new Vector2(w, lay.H);
        if (cap != null) cap.Place(w - (compact ? 16 : PadX) - cw / 2, Mathf.Round(lay.NameBase - 7 - Instrument.TagH / 2));
        QueueRedraw();
    }

    /// <summary>The frame's 1 px edge (the painted dark line, rgb 68,57,46 over the ground: tooltip.png's px 10 of its 14 px
    /// margin, drawn 6 px out, so 4 px inside the rect) raised to the HUD's bronze. Straight runs only: the frame's corners are
    /// cut, so each run stops 10 px short of its corner.</summary>
    public static void DrawEdge(CanvasItem c, Vector2 size)
    {
        var col = new Color("#9C7A45") with { A = 0.9f };
        c.DrawRect(new Rect2(10, 4, size.X - 20, 1), col);
        c.DrawRect(new Rect2(10, size.Y - 5, size.X - 20, 1), col);
        c.DrawRect(new Rect2(4, 10, 1, size.Y - 20), col);
        c.DrawRect(new Rect2(size.X - 5, 10, 1, size.Y - 20), col);
    }

    public override void _Draw()
    {
        if (view == null) return;
        box ??= UiArt.Frame("tooltip", new StyleBoxFlat { BgColor = new Color(0.08f, 0.06f, 0.05f, 0.95f) });
        box.Draw(GetCanvasItem(), new Rect2(Vector2.Zero, Size));
        DrawEdge(this, Size);
        void Text(Font f, int size, Vector2 p, string s, Color c, bool right = false)
        {
            if (s == "") return;
            if (right) p.X -= TextW(f, s, size);
            DrawString(f, p + new Vector2(1, 1), s, HorizontalAlignment.Left, -1, size, new Color(0, 0, 0, 0.7f));
            DrawString(f, p, s, HorizontalAlignment.Left, -1, size, c);
        }
        var L = lay;
        float x0 = compact ? 16 : PadX, x1 = width - x0;
        Text(Style.Display, L.NameSize, new Vector2(x0, L.NameBase), view.Name, Gold);
        if (L.How != "") Text(HowFont, L.HowSize, new Vector2(L.HowInline ? L.HowX : x0, L.HowInline ? L.NameBase : L.HowBase), L.How, Dim);
        for (int i = 0; i < L.Lines.Count; i++) Text(Style.Ui, L.LineSize, new Vector2(x0, L.LineBase + i * L.LinePitch), L.Lines[i], Parch);
        // the rule: bronze across, its middle third gold (the level card's gold-middle rule, thin)
        float third = Mathf.Round((x1 - x0) / 3);
        DrawRect(new Rect2(x0, L.RuleY, third, 1), RuleBronze);
        DrawRect(new Rect2(x0 + third, L.RuleY, x1 - x0 - 2 * third, 1), RuleGold);
        DrawRect(new Rect2(x1 - third, L.RuleY, third, 1), RuleBronze);
        foreach (var c in L.Cells)
        {
            float y = L.RowBase + c.Line * L.RowPitch;
            Text(Style.Ui, L.RowSize, new Vector2(c.LabelX, y), c.Label, Dim);
            Text(Style.UiBold, L.RowSize, new Vector2(c.ValueRight, y), c.Value, c.Gold ? Gold : Bone, true);
        }
    }
}

/// <summary>The open span between the two bronze figures that end the seat row (her head at the left, the keeper's hood at the
/// right), on the screen: read once from the figures' own art (lamp_cold.png, keeper.png) at their placed rects, as the
/// Lamps' knockout places them. For a band of rows, the left figure's rightmost opaque pixel and the right figure's leftmost.</summary>
public static class CapSpan
{
    static float[]? left, right;

    static float[] Edges(string rel, Rect2 r, bool rightmost)
    {
        var o = new float[1080];
        Array.Fill(o, rightmost ? float.NegativeInfinity : float.PositiveInfinity);
        var im = UiArt.Tex(rel, false)?.GetImage();
        if (im == null || im.IsEmpty()) return o;
        if (im.IsCompressed()) im.Decompress();
        if (im.GetFormat() != Image.Format.Rgba8) im.Convert(Image.Format.Rgba8);
        var d = im.GetData();
        int W = im.GetWidth(), H = im.GetHeight();
        for (int y = 0; y < 1080; y++)
        {
            int py = (int)((y + 0.5f - r.Position.Y) / r.Size.Y * H);
            if (py < 0 || py >= H) continue;
            if (rightmost) { for (int x = W - 1; x >= 0; x--) if (d[(py * W + x) * 4 + 3] > 90) { float sx = r.Position.X + (x + 1f) / W * r.Size.X; if (sx < 960) o[y] = sx; break; } }
            else for (int x = 0; x < W; x++) if (d[(py * W + x) * 4 + 3] > 90) { float sx = r.Position.X + x / (float)W * r.Size.X; if (sx > 960) o[y] = sx; break; }
        }
        return o;
    }

    /// <summary>(left edge, right edge) of the open span over screen rows y0..y1; falls back to the plate's own ends.</summary>
    public static (float L, float R) Of(float y0, float y1)
    {
        if (left == null || right == null)
        {
            float gs = DgPanel.GroupScale;
            var girlTl = DgPanel.GirlAnchor + (LifeLamp.At - DgPanel.GirlAnchor) * gs + DgPanel.GirlOffset;
            left = Edges("lamp_life/drowned/lamp_cold.png", HudBottom.Map(new Rect2(girlTl, LifeLamp.Canvas * gs)), true);
            right = Edges("dg_keeper/keeper.png", HudBottom.Map(DgPanel.KeeperRect), false);
        }
        float l = float.NegativeInfinity, r = float.PositiveInfinity;
        for (int y = Math.Max(0, (int)y0); y <= Math.Min(1079, (int)y1); y++) { l = Math.Max(l, left[y]); r = Math.Min(r, right[y]); }
        if (float.IsInfinity(l)) l = HudBottom.MapX(660);
        if (float.IsInfinity(r)) r = HudBottom.MapX(1260);
        return (l, r);
    }
}
