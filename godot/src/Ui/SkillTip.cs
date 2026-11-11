using System;
using System.Collections.Generic;
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
    const int NameSize = 20, HowSize = 13, LineSize = 16, RowSize = 15;

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

    /// <summary>Show it with its foot's middle at foot (a 12 px gap above it; below foot when it would leave the top),
    /// clamped 8 px inside 1920x1080; or hide it.</summary>
    public void Set(bool show, Vector2 foot, SkillTipView? v, float outerGap = -1, float leftOf = float.NaN, float bottomAt = float.NaN)
    {
        show = show && v != null && v.Name != "";
        if (Visible != show) Visible = show;
        if (!show) return;
        string k = KeyOf(v!);
        if (k != key) { key = k; Build(v!); }
        if (!float.IsNaN(leftOf) && !float.IsNaN(bottomAt) && leftOf - Out - Size.X >= 8)
        {
            // (beside a panel: its outer right edge at leftOf, its outer bottom edge at bottomAt)
            var side = new Vector2(Mathf.Round(leftOf - Out - Size.X), Mathf.Clamp(Mathf.Round(bottomAt - Out - Size.Y), 8, 1080 - 8 - Size.Y));
            if (Position != side) Position = side;
            return;
        }
        float y = foot.Y - Size.Y - (outerGap >= 0 ? outerGap + Out : 12);
        if (y < 8) y = foot.Y + (outerGap >= 0 ? outerGap + Out : 12);
        var at = new Vector2(Mathf.Clamp(Mathf.Round(foot.X - Size.X / 2), 8, 1920 - 8 - Size.X), Mathf.Clamp(Mathf.Round(y), 8, 1080 - 8 - Size.Y));
        if (Position != at) Position = at;
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

    /// <summary>Word wrap by measuring with the font; the last of at most max lines ends in an ellipsis when cut.</summary>
    static List<string> Wrap(Font f, string s, int size, float width, int max)
    {
        var o = new List<string>();
        if (string.IsNullOrWhiteSpace(s)) return o;
        var words = s.Split(' ', StringSplitOptions.RemoveEmptyEntries);
        string cur = "";
        int i = 0;
        for (; i < words.Length; i++)
        {
            string t = cur == "" ? words[i] : cur + " " + words[i];
            if (cur != "" && TextW(f, t, size) > width)
            {
                o.Add(cur);
                cur = words[i];
                if (o.Count == max) break;
            }
            else cur = t;
        }
        if (o.Count < max) { if (cur != "") o.Add(cur); return o; }
        // cut: the last line takes an ellipsis, trimmed to fit
        string last = o[max - 1];
        while (last.Length > 1 && TextW(f, last + "…", size) > width) { int sp = last.LastIndexOf(' '); last = last[..(sp > 0 ? sp : last.Length - 1)]; }
        o[max - 1] = last.TrimEnd(',', ';', ':', '.') + "…";
        return o;
    }

    void Build(SkillTipView v)
    {
        view = v;
        how = v.How.ToUpperInvariant();
        lines.Clear();
        lines.AddRange(Wrap(Style.Ui, v.Line, LineSize, W - 2 * PadX, 3));
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
        nameBase = PadY + 16;
        float y = nameBase;
        if (how != "") { howBase = y + 6 + HowSize; y = howBase; }
        if (lines.Count > 0) { lineBase = y + 10 + LineSize; y = lineBase + (lines.Count - 1) * 21; }
        ruleY = y + 10;
        rowBase = ruleY + 10 + RowSize;
        int rows = v.Rows.Count + (v.Cost != null ? 1 : 0);
        float bottom = rows > 0 ? rowBase + (rows - 1) * 20 : ruleY;
        Size = new Vector2(W, Mathf.Ceil(bottom + 4 + PadY));
        if (cap != null)
        {
            float cw = cap.ChipBox().Size.X;
            cap.Place(W - PadX - cw / 2, Mathf.Round(nameBase - 7 - Instrument.TagH / 2));
        }
        QueueRedraw();
    }

    public override void _Draw()
    {
        if (view == null) return;
        box ??= UiArt.Frame("tooltip", new StyleBoxFlat { BgColor = new Color(0.08f, 0.06f, 0.05f, 0.95f) });
        box.Draw(GetCanvasItem(), new Rect2(Vector2.Zero, Size));
        void Text(Font f, int size, Vector2 p, string s, Color c, bool right = false)
        {
            if (s == "") return;
            if (right) p.X -= TextW(f, s, size);
            DrawString(f, p + new Vector2(1, 1), s, HorizontalAlignment.Left, -1, size, new Color(0, 0, 0, 0.7f));
            DrawString(f, p, s, HorizontalAlignment.Left, -1, size, c);
        }
        float x0 = PadX, x1 = W - PadX;
        Text(Style.Display, NameSize, new Vector2(x0, nameBase), view.Name, Gold);
        if (how != "") Text(Style.UiBold, HowSize, new Vector2(x0, howBase), how, Dim);
        for (int i = 0; i < lines.Count; i++) Text(Style.Ui, LineSize, new Vector2(x0, lineBase + i * 21), lines[i], Parch);
        // the rule: bronze across, its middle third gold (the level card's gold-middle rule, thin)
        float third = Mathf.Round((x1 - x0) / 3);
        DrawRect(new Rect2(x0, ruleY, third, 1), RuleBronze);
        DrawRect(new Rect2(x0 + third, ruleY, x1 - x0 - 2 * third, 1), RuleGold);
        DrawRect(new Rect2(x1 - third, ruleY, third, 1), RuleBronze);
        float y = rowBase;
        foreach (var r in view.Rows)
        {
            Text(Style.Ui, RowSize, new Vector2(x0, y), r.Label, Dim);
            Text(Style.UiBold, RowSize, new Vector2(x1, y), r.Value, Bone, true);
            y += 20;
        }
        if (view.Cost is { } c)
        {
            Text(Style.Ui, RowSize, new Vector2(x0, y), c.Label, Dim);
            Text(Style.UiBold, RowSize, new Vector2(x1, y), c.Value, Gold, true);
        }
    }
}
