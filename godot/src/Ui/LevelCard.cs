using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Play;

namespace SurvivorUnchained.Ui;

/// <summary>
/// M4 §4, the level-up card (docs/design/M4_HUD.md): one card over the world, rising from the level coin, centred on
/// x 960, its foot clear of the beads and statuses. The panel language: an ink ground at 82%, a 2 px rule top and
/// bottom (gold at its middle, bronze thinning to the ends), no border; the header in gold; a short gold stem from the
/// card's foot down to the coin it rose from (judge r1, 9: "a tooltip, not a moment"). The card is as wide as its words
/// (no dead half). A new key: the skill's gold glyph in a round ringed well (the seats' own shape), its name (display
/// serif 26, cream), its key cap chip (the bar's own KeyTag, 16 px tall on screen), one line of what it does (UI sans 16,
/// parchment 80%). A lamp lit: the glyph, the name, "42 → 47 a blow" (before dim, after bright). A new skill (the calling's, on
/// no key yet): the glyph, the name, its one line, no key cap; its prompt row names the skills screen. Plain: the header and the prompt
/// row. The prompt row: a key chip and words; the card then holds 3 s. In 0.18 s, hold 2.2 s, out 0.3 s folding toward
/// the seat that opened (its ring flashes). Words built once a card; drawn once a card; per frame only its transform.
/// </summary>
public partial class LevelCard : Control
{
    static readonly Color Ground = new(0.043f, 0.035f, 0.024f, 0.82f), Rule = new("#8a6a3a"), Bone = new("#e9dfcc"),
        Cream = new("#f3e7cc"), Parch = new Color("#e8dcc0") with { A = 0.8f }, Dim = new Color("#e8dcc0") with { A = 0.5f },
        FieldIn = new("#6a5236"), FieldRim = new("#3b2c1d"), WellInk = new(0.035f, 0.028f, 0.02f, 0.92f), GlyphGold = new("#e9c27a"), RuleGold = new("#f2d28c"), Ring = new("#b8904e");
    /// <summary>The chips' scale: the bar's KeyTag chip at 16 px tall on screen (judge r1, 15: at the bottom HUD's own
    /// scale it was a 12 px chip beside a 26 px name).</summary>
    const float CapK = 1f;
    const float MinW = 230, Pad = 18, WellD = 40, NameX = Pad + WellD + 14, CoinR = 43, StemMax = 64;   // (CoinR: the coin arch's top, 43 over its middle: the stem ends on it)
    const int HeadSize = 14, NameSize = 26, LineSize = 16, PromptSize = 15;

    public readonly LevelCardQueue Queue = new();
    /// <summary>True while the card must wait (banners held, a screen open): GameHud sets it once.</summary>
    public Func<bool> Held = () => false;
    /// <summary>Where the card folds to (the opened seat's middle, else the coin), asked when the out begins.</summary>
    public Func<LevelCardSpec, Vector2?> FoldTo = _ => null;
    /// <summary>The fold began toward the seat of this slot (GameHud flashes its ring).</summary>
    public Action<LevelCardSpec> OnFold = _ => { };
    /// <summary>The y the card's foot must stay above (the beads' and statuses' top), asked when a card begins.</summary>
    public Func<float, float> FootFor = _ => 960;
    /// <summary>bd-ui W8: the top of the status shelf in the campaign (the card's bottom stays 8 px above it), else null.</summary>
    public Func<float?> RowTop = () => null;
    /// <summary>bd-ui W6: the global top-middle of what opened (a key seat's cap, an auto tile, the stance disc), null: the coin.</summary>
    public Func<LevelCardSpec, Vector2?> TopOf = _ => null;
    /// <summary>bd-ui W13: the global rects of the auto tiles and the stance discs, which the tail breaks around (3 px clear).</summary>
    public Func<List<Rect2>> Avoid = () => new();

    /// <summary>Where it rises from (the coin's middle).</summary>
    public Vector2 From = new(960, 1042);

    string line2 = "";
    string header = "", name = "", line = "", before = "", after = "", measure = "", arrow = " → ", prompt = "";
    Texture2D? glyph, discIcon;
    bool discReal;
    float h = 110, w = MinW, stem, tailX;
    Vector2 rest, fold;
    readonly Control capHost = new() { MouseFilter = MouseFilterEnum.Ignore };
    readonly Control promptHost = new() { MouseFilter = MouseFilterEnum.Ignore };
    KeyTag? cap, promptCap;
    LevelCardSpec? shown;

    public LevelCard()
    {
        MouseFilter = MouseFilterEnum.Ignore;
        Visible = false;
        ZIndex = 4;
        AddChild(capHost);
        AddChild(promptHost);
        // (the seats' caps are drawn under the bottom HUD's scale: held at that size here, so the chip matches its seat)
        capHost.Scale = promptHost.Scale = new Vector2(CapK, CapK);
    }

    /// <summary>The offer showing now (a lamp card not yet lit), else null.</summary>
    public LevelCardSpec? OfferUp => Queue.Current is { Offer: true } c && Queue.Now is LevelCardQueue.Phase.In or LevelCardQueue.Phase.Hold && Visible ? c : null;

    /// <summary>The showing card's spec changed (an offer lit): its words, chips and size again, no second stinger.</summary>
    public void Refresh(LevelCardSpec s) { if (shown == s) Begin(s, true); }

    /// <summary>A card to show (in turn, after any showing).</summary>
    public void Add(LevelCardSpec s) => Queue.Add(s);

    /// <summary>A line broken at a space into at most two lines that fit room (the second carries the rest).</summary>
    static (string, string) Wrap(string text, float room)
    {
        var words = text.Split(' ');
        string a = "";
        int i = 0;
        for (; i < words.Length; i++)
        {
            string t = a == "" ? words[i] : a + " " + words[i];
            if (a != "" && TextW(Style.Ui, t, LineSize) > room) break;
            a = t;
        }
        return (a, string.Join(" ", words[i..]));
    }

    /// <summary>(bd-ui W13) Wrap, then narrow the body width by 10 px steps (never under 300) until the last line holds at least 3 words.</summary>
    static (string, string) Balanced(string text, float room)
    {
        var (a, b) = Wrap(text, room);
        for (float r = room - 10; b != "" && b.Split(' ').Length < 3 && r >= 300; r -= 10) (a, b) = Wrap(text, r);
        return (a, b);
    }

    static float TextW(Font f, string s, int size) => f.GetStringSize(s, HorizontalAlignment.Left, -1, size).X;

    /// <summary>A card begins: its words, glyph, chips and size, once.</summary>
    void Begin(LevelCardSpec s, bool again = false)
    {
        shown = s;
        header = LevelCards.Header(s);
        // (the level's stinger, once the card shows: Journey's "Level N" banner, which carried it, is gone in the campaign;
        // a new skill's card that follows its level's key card is the same level-up: it does not ring twice)
        if (!again && (s.Kind != LevelCardKind.NewSkill || s.Level > 0)) SurvivorUnchained.Sound.Sfx.Stinger("triumph");
        bool body = s.Kind != LevelCardKind.Plain;
        name = line = line2 = before = after = measure = "";
        glyph = null; discIcon = null;
        if (body && Content.Weapons.All.TryGetValue(s.Skill, out var wd))
        {
            name = wd.Name;
            // (bd-ui W8: the seat's own icon source, Instrument.Socket.Show: the skill's painting, else its gold line glyph)
            string gk = SeatIcon.For(s.Skill, wd.Art);
            // (bd-ui W9: a NewAuto card shows its tile's drawing, the line glyph in the tile's colour, not the painting)
            glyph = s.Kind == LevelCardKind.NewAuto ? AutoRow.LineGlyph(gk, 78, ItemViews.SchoolColors[wd.School])
                : s.Kind == LevelCardKind.NewKey ? SeatPicture.Gold(LevelCards.PictureKey(s.Skill))
                : Glyphs.Texture(gk, 80, GlyphGold, line: true);
            if (s.Kind == LevelCardKind.NewKey && Args.Get("level-card") != null) GD.Print($"level-card picture: key {gk} = DgGold gold line glyph {SeatPicture.CardPx} px (card)");
            if (s.Kind != LevelCardKind.LampLit) line = s.Line ?? LevelCards.Line(s.Skill, wd.Description);
        }
        else if (body) { name = s.Skill; line = s.Line ?? ""; }
        if (s.Kind == LevelCardKind.LampLit) { measure = " " + s.Measure; before = LevelCards.Num(s.Before); after = LevelCards.Num(s.After);
            // (U1: a blow reads in whole numbers, as the wick's sum line and the skill tips print it)
            if (s.Measure is "a blow" or "a cut") { before = Math.Round(s.Before).ToString(System.Globalization.CultureInfo.InvariantCulture); after = Math.Round(s.After).ToString(System.Globalization.CultureInfo.InvariantCulture); } }
        prompt = s.HasPrompt ? s.PromptText! : "";

        // the skill's key chip (a new key only), after its name
        float need = MinW;
        if (s.Kind == LevelCardKind.NewKey && s.Slot >= 0 && s.Slot < KeyMap.Skills.Length && KeyMap.SeatOf(s.Slot) >= 0)
        {
            cap?.QueueFree();
            cap = new KeyTag(LevelCardPlace.CapAct(s.Slot)) { Chip = true };
            capHost.AddChild(cap);
            cap.Refresh();
        }
        else if (s.Kind == LevelCardKind.NewStance)
        {
            // (bd-ui W8: the disc shows what the stance block's disc shows: the weapon's line glyph in cream on the field)
            glyph = Glyphs.Texture(StanceText.Glyph(s.StanceId), 80, Cream, 2.4f, line: true);
            cap?.QueueFree();
            cap = new KeyTag(Act.Swap) { Chip = true };
            capHost.AddChild(cap);
            cap.Refresh();
        }
        else if (cap != null) { cap.QueueFree(); cap = null; }
        float nameW = TextW(Style.Display, name, NameSize);
        if (body)
        {
            float capW = cap != null ? cap.ChipBox().Size.X * CapK + 12 : 0;
            float lineW = s.Kind == LevelCardKind.LampLit
                ? TextW(Style.Ui, before + arrow + after + measure, LineSize)
                : TextW(Style.Ui, line, LineSize);
            // (bd-ui W8: at most 470 wide; a longer body wraps to two lines)
            float room = LevelCardPlace.MaxW - NameX - Pad;
            if (s.Kind != LevelCardKind.LampLit && lineW > room) { (line, line2) = Balanced(line, room); lineW = Math.Max(TextW(Style.Ui, line, LineSize), line2 == "" ? 0 : TextW(Style.Ui, line2, LineSize)); }
            need = Math.Max(need, NameX + Math.Max(nameW + capW, lineW) + Pad);
        }
        float headW = TextW(Style.Display, header, HeadSize) + 2 * Pad;
        if (s.HasPrompt)
        {
            promptCap?.QueueFree();
            // On a pad the book's pages have no button of their own (KeyMap.Pad): View opens the book and the bumpers
            // turn to the page, so the cap is View's, never a keyboard's "C" in a pad player's hands (M4 lead 7).
            var pk = s.PromptKey!.Value;
            if (Controls.Instance is { UsingPad: true } ctl && !System.Linq.Enumerable.Any(ctl.PadLabels(pk))) pk = Act.Inventory;
            promptCap = new KeyTag(pk) { Chip = true };
            promptHost.AddChild(promptCap);
            promptCap.Refresh();
            need = Math.Max(need, Pad + promptCap.ChipBox().Size.X * CapK + 10 + TextW(Style.Ui, prompt, PromptSize) + Pad);
        }
        else if (promptCap != null) { promptCap.QueueFree(); promptCap = null; }
        w = Mathf.Min(LevelCardPlace.MaxW, Mathf.Ceil(Math.Max(need, headW)));
        float bodyTop = 32, extra = line2 != "" ? LineSize + 4 : 0, promptTop = body ? 88 + extra : 36;
        h = s.HasPrompt ? promptTop + 24 : body ? 86 + extra : 44;
        Size = new Vector2(w, h);
        PivotOffset = Size / 2;
        // the chips, placed in their hosts' (scaled) space: the name's cap on the name's middle, the prompt's on its row
        float k = CapK;
        if (cap != null)
        {
            float cw = cap.ChipBox().Size.X * k;
            cap.Place((NameX + nameW + 12 + cw / 2) / k, (bodyTop + 13 - Instrument.TagH * k / 2) / k);
        }
        if (promptCap != null)
        {
            float pw = promptCap.ChipBox().Size.X * k;
            promptCap.Place((Pad + pw / 2) / k, (promptTop + 9 - Instrument.TagH * k / 2) / k);
        }
        float foot = FootFor(w);
        var top = TopOf(s);
        var pl = LevelCardPlace.Compute(w, h, foot, RowTop(), top is { } tv ? (tv.X, tv.Y) : null);
        rest = new Vector2(pl.X, pl.Y);
        tailX = pl.TailX;
        // (bd-ui W14: a key seat's target gets no long tail: a 10 px stem under the diamond, the seat itself pulses; tiles and discs keep theirs)
        if (top != null) stem = s.Kind == LevelCardKind.NewKey ? Math.Min(10, pl.Stem) : pl.Stem;
        else
        {
            // the stem: from the card's foot to the coin's rim; a card held high over beads gets a short one that fades out
            float gap = From.Y - CoinR - (rest.Y + h);
            stem = gap <= 0 ? 0 : Math.Min(gap, StemMax);
        }
        GD.Print($"level card: {header} rect ({rest.X:0},{rest.Y:0} {w:0}x{h:0}) foot {foot:0}{(prompt != "" ? $", prompt \"{prompt}\"" : "")}");
        QueueRedraw();
    }

    /// <summary>U1 §5B: the card being read (the pointer on it, or the pad's LB held while it shows): its hold clock stops
    /// (it does not fold while read) and resumes from where it was.</summary>
    public bool Read;
    /// <summary>(bd-ui W14) The new-key card showing now (risen or holding): its seat pulses while it holds.</summary>
    public LevelCardSpec? HoldingKey => Visible && Queue.Current is { Kind: LevelCardKind.NewKey } c && Queue.Now is LevelCardQueue.Phase.In or LevelCardQueue.Phase.Hold ? c : null;

    /// <summary>The card a skill tip can be read from (a new key, a new skill or a lamp lit, risen or holding), or null.</summary>
    public LevelCardSpec? Readable => Visible && Queue.Current is { Skill: not "" } c
        && c.Kind is LevelCardKind.NewKey or LevelCardKind.NewSkill or LevelCardKind.LampLit
        && Queue.Now is LevelCardQueue.Phase.In or LevelCardQueue.Phase.Hold ? c : null;

    public override void _Process(double delta)
    {
        bool held = Held();
        Queue.Tick(Read && Queue.Now == LevelCardQueue.Phase.Hold ? 0 : delta, held);
        if (Queue.Began && Queue.Current != null) Begin(Queue.Current);
        if (Queue.Current == null) { if (Visible) Visible = false; return; }
        if (held) { if (Visible) Visible = false; return; }
        if (Queue.Folding) { fold = FoldTo(Queue.Current) ?? From; OnFold(Queue.Current); }
        Visible = true;
        float kk = (float)Queue.K;
        switch (Queue.Now)
        {
            case LevelCardQueue.Phase.In:
            {
                // rising from the coin: up from 18 px lower, eased out, fading in
                float e = 1 - (1 - kk) * (1 - kk);
                Position = rest + new Vector2(0, 18 * (1 - e));
                Scale = Vector2.One;
                Modulate = Colors.White with { A = e };
                break;
            }
            case LevelCardQueue.Phase.Hold:
                Position = rest; Scale = Vector2.One; Modulate = Colors.White;
                break;
            case LevelCardQueue.Phase.Out:
            {
                // folding toward the seat that opened: drawn in toward it, smaller, gone
                float e = kk * kk;
                var mid = rest + Size / 2;
                Position = rest + (fold - mid) * e;
                Scale = new Vector2(1 - 0.75f * e, 1 - 0.85f * e);
                Modulate = Colors.White with { A = 1 - e };
                break;
            }
        }
    }

    public override void _Draw()
    {
        if (shown == null) return;
        var s = shown;
        // the ground and its two rules (the panel ends cleanly: square, no border, no ornament)
        DrawRect(new Rect2(0, 0, w, h), Ground);
        foreach (float ry in new[] { 0f, h - 2 })
        {
            var end = Rule with { A = 0.55f };
            float m = w / 2;
            DrawPolygon([new(0, ry), new(m, ry), new(m, ry + 2), new(0, ry + 2)], [end, RuleGold, RuleGold, end]);
            DrawPolygon([new(m, ry), new(w, ry), new(w, ry + 2), new(m, ry + 2)], [RuleGold, end, end, RuleGold]);
        }
        // the stem to the coin: gold at the card's foot, thinning toward the coin, an ink edge under it, the house's
        // diamond where it leaves the rule
        if (stem > 0)
        {
            float m = Mathf.Round(tailX);
            var far = Rule with { A = 0.5f };
            var gp = GetGlobalTransform().Origin;
            var avoid = Avoid().Select(r => (r.Position.X - gp.X, r.Position.Y - gp.Y, r.End.X - gp.X, r.End.Y - gp.Y));
            foreach (var (a0, a1) in LevelCardPlace.StemSpans(m, h, h + stem, avoid))
            {
                var c0 = RuleGold.Lerp(far, (a0 - h) / stem); var c1 = RuleGold.Lerp(far, (a1 - h) / stem);
                DrawRect(new Rect2(m - 2, a0, 4, a1 - a0), new Color(0, 0, 0, 0.45f));
                DrawPolygon([new(m - 1, a0), new(m + 1, a0), new(m + 1, a1), new(m - 1, a1)], [c0, c0, c1, c1]);
            }
            DrawColoredPolygon([new(m - 7, h - 1), new(m, h - 7), new(m + 7, h - 1), new(m, h + 5)], new Color(0.035f, 0.028f, 0.02f));
            DrawColoredPolygon([new(m - 5, h - 1), new(m, h - 5), new(m + 5, h - 1), new(m, h + 3)], RuleGold);
        }
        // the header, small caps, gold
        DrawString(Style.Display, new Vector2(Pad, 23), header, HorizontalAlignment.Left, -1, HeadSize, GlyphGold);
        if (s.Kind != LevelCardKind.Plain)
        {
            const float top = 32;
            var well = new Rect2(Pad, top + 2, WellD, WellD);
            var wc = well.GetCenter();
            if (s.Kind == LevelCardKind.NewAuto)
            {
                // (an auto skill's frame is the tile's: a square, the bronze bezel)
                DrawRect(well, WellInk);
                DrawRect(well.Grow(-0.5f), new Color("#1a120a") with { A = 0.8f }, false, 1);
                DrawRect(well.Grow(-1.75f), Ring, false, 1.5f);
            }
            else if (s.Kind == LevelCardKind.NewStance)
            {
                // (a stance's is the block's disc: the mid-tone field, the stance's color for its bezel)
                for (int i = 0; i < 10; i++) DrawCircle(wc, WellD / 2 * (1 - 0.85f * i / 10), FieldRim.Lerp(FieldIn, i / 9f), true, -1, true);
                DrawArc(wc, WellD / 2 - 1, 0, Mathf.Tau, 48, StanceBlock.ColorOf(s.StanceId) is var sc && sc != Colors.Transparent ? sc : Ring, 2, true);
            }
            else
            {
                // the seats' round well: an ink disc, a bronze ring, a hair of gold on its upper rim
                DrawCircle(wc, WellD / 2, WellInk);
                DrawArc(wc, WellD / 2 - 1, 0, Mathf.Tau, 48, Ring, 2, true);
                DrawArc(wc, WellD / 2 - 1, Mathf.Pi * 1.15f, Mathf.Pi * 1.85f, 20, RuleGold with { A = 0.8f }, 1, true);
            }
            if (glyph != null && s.Kind == LevelCardKind.NewKey)
            {
                // (bd-ui W14: the seat's own gold inlay, 26 px, centred on the dark well, as the seat draws it)
                float gs = SeatPicture.CardPx + 2 * DgGold.Pad;
                DrawTextureRect(glyph, new Rect2(wc - new Vector2(gs, gs) / 2, new Vector2(gs, gs)), false);
            }
            else if (glyph != null) DrawTextureRect(glyph, well.Grow(s.Kind == LevelCardKind.NewStance ? -9 : -8), false);
            DrawString(Style.Display, new Vector2(NameX, top + 22), name, HorizontalAlignment.Left, -1, NameSize, Cream);
            if (s.Kind != LevelCardKind.LampLit)
            {
                DrawString(Style.Ui, new Vector2(NameX, top + 44), line, HorizontalAlignment.Left, -1, LineSize, Parch);
                if (line2 != "") DrawString(Style.Ui, new Vector2(NameX, top + 44 + LineSize + 4), line2, HorizontalAlignment.Left, -1, LineSize, Parch);
            }
            else
            {
                float x = NameX;
                DrawString(Style.Ui, new Vector2(x, top + 44), before, HorizontalAlignment.Left, -1, LineSize, Dim);
                x += TextW(Style.Ui, before, LineSize);
                DrawString(Style.Ui, new Vector2(x, top + 44), arrow, HorizontalAlignment.Left, -1, LineSize, Dim);
                x += TextW(Style.Ui, arrow, LineSize);
                DrawString(Style.UiBold, new Vector2(x, top + 44), after, HorizontalAlignment.Left, -1, LineSize, Cream);
                x += TextW(Style.UiBold, after, LineSize);
                DrawString(Style.Ui, new Vector2(x, top + 44), measure, HorizontalAlignment.Left, -1, LineSize, Parch);
            }
        }
        if (prompt != "" && promptCap != null)
        {
            float promptTop = s.Kind != LevelCardKind.Plain ? 88 + (line2 != "" ? LineSize + 4 : 0) : 36;
            float px = Pad + promptCap.ChipBox().Size.X * CapK + 10;
            DrawString(Style.Ui, new Vector2(px, promptTop + 14), prompt, HorizontalAlignment.Left, -1, PromptSize, Parch);
        }
    }
}
