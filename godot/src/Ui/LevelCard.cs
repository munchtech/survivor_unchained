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
    const int HeadSize = 14, PromptSize = 15;
    /// <summary>Dev flag `--card-look b` (read once): take B, type on the world (no plate, no rules, a feathered scrim, one open chain link). Default "a": the plate.</summary>
    static readonly bool CardB = Args.Get("card-look") == "b";
    static int NameSize => CardB ? 30 : 26;
    static int LineSize => CardB ? 17 : 16;
    const float GlyphB = 34, LinkH = 16, LinkW = 10, LinkGap = 50f, OpenFor = 0.18f + 0.25f;
    static readonly Color Dark = new(0.02f, 0.015f, 0.01f, 0.85f);
    float nameX = NameX, contentW, openT, bodyW, promptW, headRowW, row1W;
    int nameSz = 26;

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
        if (!again) openT = 0;
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
        else if (body)
        {
            name = s.Skill; line = s.Line ?? "";
            // (the road's card: its row's glyph, as a skill's card draws its own)
            if (s.Kind == LevelCardKind.NewRoad && s.Icon != "") glyph = Glyphs.Texture(s.Icon, 80, GlyphGold, line: true);
        }
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
        nameSz = NameSize; bodyW = 0; promptW = 0;
        float nameW = TextW(Style.Display, name, nameSz);
        float capW = 0;
        if (body)
        {
            capW = cap != null ? cap.ChipBox().Size.X * CapK + 12 : 0;
            // (a long name, the road's two roads joined, shrinks to the card's widest body rather than run off it)
            float nroom = LevelCardPlace.MaxW - NameX - Pad;
            if (nameW + capW > nroom) { nameSz = Math.Max(16, (int)(NameSize * nroom / (nameW + capW))); nameW = TextW(Style.Display, name, nameSz); }
            float lineW = s.Kind == LevelCardKind.LampLit
                ? TextW(Style.Ui, before + arrow + after + measure, LineSize)
                : TextW(Style.Ui, line, LineSize);
            // (bd-ui W8: at most 470 wide; a longer body wraps to two lines)
            float room = LevelCardPlace.MaxW - NameX - Pad;
            if (s.Kind != LevelCardKind.LampLit && lineW > room) { (line, line2) = Balanced(line, room); lineW = Math.Max(TextW(Style.Ui, line, LineSize), line2 == "" ? 0 : TextW(Style.Ui, line2, LineSize)); }
            need = Math.Max(need, NameX + Math.Max(nameW + capW, lineW) + Pad);
            if (CardB) { need = Math.Max(MinW, 2 * Pad + Math.Max(GlyphB + 10 + nameW + capW, lineW)); row1W = GlyphB + 10 + nameW + capW; bodyW = Math.Max(row1W, lineW); }
        }
        float headW = TextW(Style.Display, header, HeadSize) + 2 * Pad + (CardB ? LinkW + 8 : 0);
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
            promptW = promptCap.ChipBox().Size.X * CapK + 10 + TextW(Style.Ui, prompt, PromptSize);
            need = Math.Max(need, Pad + promptW + Pad);
        }
        else if (promptCap != null) { promptCap.QueueFree(); promptCap = null; }
        w = Mathf.Min(LevelCardPlace.MaxW, Mathf.Ceil(Math.Max(need, headW)));
        float bodyTop = 32, extra = line2 != "" ? LineSize + 4 : 0, promptTop = body ? 88 + extra : 36;
        h = s.HasPrompt ? promptTop + 24 : body ? 86 + extra : 44;
        Size = new Vector2(w, h);
        PivotOffset = Size / 2;
        // the chips, placed in their hosts' (scaled) space: the name's cap on the name's middle, the prompt's on its row
        float k = CapK;
        headRowW = TextW(Style.Display, header, HeadSize) + (CardB ? LinkW + 8 : 0);
        contentW = Math.Max(Math.Max(headRowW, bodyW), promptW);
        // (take B centres its rows; take A keeps the well's column)
        nameX = CardB ? (w - row1W) / 2 + GlyphB + 10 : NameX;
        if (cap != null)
        {
            float cw = cap.ChipBox().Size.X * k;
            cap.Place((nameX + nameW + 12 + cw / 2) / k, (bodyTop + 13 - Instrument.TagH * k / 2) / k);
        }
        if (promptCap != null)
        {
            float pw = promptCap.ChipBox().Size.X * k;
            promptCap.Place(((CardB ? (w - promptW) / 2 : Pad) + pw / 2) / k, (promptTop + 9 - Instrument.TagH * k / 2) / k);
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
        // (take B: the chain link's gap opens over the In phase plus 0.25 s: redrawn while it does)
        if (CardB && Visible && openT < OpenFor) { openT += (float)delta; QueueRedraw(); }
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

    /// <summary>Text with a dark outline: the string offset in 8 directions at r px, then itself.</summary>
    void Outlined(Font f, Vector2 p, string t, int size, Color c, float r)
    {
        for (int i = 0; i < 8; i++)
            DrawString(f, p + Vector2.FromAngle(i * Mathf.Pi / 4) * r, t, HorizontalAlignment.Left, -1, size, Dark);
        DrawString(f, p, t, HorizontalAlignment.Left, -1, size, c);
    }

    /// <summary>Take B: a soft feathered scrim (a vertex-coloured fan, no edge), the header with its one open chain link,
    /// the glyph bare, the name and line outlined, the 1 px stem fading out.</summary>
    void DrawB(LevelCardSpec s)
    {
        // the scrim: 1.25 x the text block's width, 1.6 x its height, black 0.62 in the middle, smooth to 0 at the rim
        var mid = new Vector2(w / 2, h / 2);
        float ra = 0.625f * contentW, rb = 0.8f * (h - 10);
        const int Seg = 56, Rings = 8;
        static float Fall(float t) { float u = 1 - t; return u * u * (3 - 2 * u); }   // (smoothstep down: flat in the middle, 0 slope at the rim)
        for (int r = 0; r < Rings; r++)
        {
            float t0 = (float)r / Rings, t1 = (float)(r + 1) / Rings;
            var c0 = new Color(0, 0, 0, 0.62f * Fall(t0)); var c1 = new Color(0, 0, 0, 0.62f * Fall(t1));
            for (int i = 0; i < Seg; i++)
            {
                float a0 = i * Mathf.Tau / Seg, a1 = (i + 1) * Mathf.Tau / Seg;
                Vector2 P(float t, float a) => mid + new Vector2(Mathf.Cos(a) * ra * t, Mathf.Sin(a) * rb * t);
                if (r == 0) DrawPolygon([mid, P(t1, a0), P(t1, a1)], [c0, c1, c1]);
                else DrawPolygon([P(t0, a0), P(t1, a0), P(t1, a1), P(t0, a1)], [c0, c1, c1, c0]);
            }
        }
        float scrimBottom = mid.Y + rb;
        // the stem: 1 px gold fading to nothing at its foot, from the scrim's bottom
        if (stem > 0)
        {
            float m = Mathf.Round(tailX), y0 = Math.Min(scrimBottom, h + stem - 6), y1 = h + stem;
            var gp = GetGlobalTransform().Origin;
            var avoid = Avoid().Select(r => (r.Position.X - gp.X, r.Position.Y - gp.Y, r.End.X - gp.X, r.End.Y - gp.Y));
            foreach (var (a0, a1) in LevelCardPlace.StemSpans(m, y0, y1, avoid))
            {
                var c0 = RuleGold with { A = 1 - (a0 - y0) / (y1 - y0) }; var c1 = RuleGold with { A = 1 - (a1 - y0) / (y1 - y0) };
                DrawPolygon([new(m - 0.5f, a0), new(m + 0.5f, a0), new(m + 0.5f, a1), new(m - 0.5f, a1)], [c0, c0, c1, c1]);
            }
        }
        // the header: the open link, then the words
        float hx = (w - headRowW) / 2;
        DrawLink(new Vector2(hx + LinkW / 2, 18), LinkGap * Mathf.Clamp(openT / OpenFor, 0f, 1f));
        DrawString(Style.Display, new Vector2(hx + LinkW + 8, 23), header, HorizontalAlignment.Left, -1, HeadSize, GlyphGold);
        if (s.Kind != LevelCardKind.Plain)
        {
            const float top = 32;
            float nameBase = top + 24, lineBase = top + 46;
            float gx = nameX - 10 - GlyphB, gy = nameBase - 11 - GlyphB / 2;
            if (glyph != null)
            {
                var gr = new Rect2(gx, gy, GlyphB, GlyphB);
                foreach (var o in new[] { new Vector2(1, 1), new Vector2(-1, 1), new Vector2(1, -1), new Vector2(-1, -1) })
                    DrawTextureRect(glyph, new Rect2(gr.Position + o, gr.Size), false, new Color(0, 0, 0, 0.7f));
                DrawTextureRect(glyph, gr, false);
            }
            Outlined(Style.Display, new Vector2(nameX, nameBase), name, nameSz, Cream, 2);
            if (s.Kind != LevelCardKind.LampLit)
            {
                Outlined(Style.Ui, new Vector2((w - TextW(Style.Ui, line, LineSize)) / 2, lineBase), line, LineSize, Parch, 1.5f);
                if (line2 != "") Outlined(Style.Ui, new Vector2((w - TextW(Style.Ui, line2, LineSize)) / 2, lineBase + LineSize + 4), line2, LineSize, Parch, 1.5f);
            }
            else
            {
                float x = (w - TextW(Style.Ui, before + arrow, LineSize) - TextW(Style.UiBold, after, LineSize) - TextW(Style.Ui, measure, LineSize)) / 2;
                Outlined(Style.Ui, new Vector2(x, lineBase), before + arrow, LineSize, Dim, 1.5f);
                x += TextW(Style.Ui, before + arrow, LineSize);
                Outlined(Style.UiBold, new Vector2(x, lineBase), after, LineSize, Cream, 1.5f);
                x += TextW(Style.UiBold, after, LineSize);
                Outlined(Style.Ui, new Vector2(x, lineBase), measure, LineSize, Parch, 1.5f);
            }
        }
        if (prompt != "" && promptCap != null)
        {
            float promptTop = s.Kind != LevelCardKind.Plain ? 88 + (line2 != "" ? LineSize + 4 : 0) : 36;
            float px = (w - promptW) / 2 + promptCap.ChipBox().Size.X * CapK + 10;
            Outlined(Style.Ui, new Vector2(px, promptTop + 14), prompt, PromptSize, Parch, 1.5f);
        }
    }

    /// <summary>The one chain motif: an open oval link (16 x 10, 2 px stroke), its right side cut by gapDeg, the cut ends flared outward.</summary>
    void DrawLink(Vector2 c, float gapDeg)
    {
        float a = LinkW / 2 - 1, b = LinkH / 2 - 1, half = Mathf.DegToRad(gapDeg) / 2;
        var pts = new List<Vector2>();
        if (half <= 0.001f) half = 0;
        int n = 36;
        for (int i = 0; i <= n; i++)
        {
            float t = half + (Mathf.Tau - 2 * half) * i / n;
            pts.Add(c + new Vector2(Mathf.Cos(t) * a, Mathf.Sin(t) * b));
        }
        // the flare: each cut end turns a hair outward (away from the gap's axis, and right)
        float fl = Mathf.Clamp(gapDeg / LinkGap, 0, 1) * 1.8f;
        if (fl > 0)
        {
            pts.Insert(0, pts[0] + new Vector2(fl, fl * 0.9f));
            pts.Add(pts[^1] + new Vector2(fl, -fl * 0.9f));
        }
        DrawPolyline(pts.ToArray(), RuleGold, 2, true);
    }

    public override void _Draw()
    {
        if (shown == null) return;
        var s = shown;
        if (CardB) { DrawB(s); return; }
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
            DrawString(Style.Display, new Vector2(NameX, top + 22), name, HorizontalAlignment.Left, -1, nameSz, Cream);
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
