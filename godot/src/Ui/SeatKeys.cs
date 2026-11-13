using System;
using Godot;
using SurvivorUnchained.Play;

namespace SurvivorUnchained.Ui;

/// <summary>
/// M4 §1 (docs/design/M4_HUD.md): a campaign seat's key and kind, the hands rule ("the slot UI shows which keys she
/// actually presses"). Each seat wears its key cap at 12 o'clock (a KeyTag chip, a child so a callout's dimming takes it
/// too); GameHud feeds it a SeatState each frame (values only, nothing built). The kinds at a glance:
///   pressed and hold: a bright cap; channeled: a bright cap on a gold underline, a gold arc turning in the ring while it
///   runs; kindled: the cap at half, the well lit like a lantern (breathing; when it fires itself the lantern catches:
///   a radial flare, hot at the well's middle, the glyph in dark ink over it, settling back).
/// A spender short of Resolve: a gold arc fills clockwise from 12 o'clock as Value / cost. A union: both rings' inner
/// edges gold, a clasp across the gap of adjacent seats (linked rings at 10:30 otherwise), the second key breathing
/// gold while the bond is live. Empty: locked = no cap; open = the cap at 30%. A seat that wears a cap draws no rank chip (lead 4).
/// What moves by the clock (the lantern, the turning arc, the bond's breath) is a small child changed by its
/// Modulate or Rotation, never a redraw of the seat.
/// </summary>
public partial class Socket
{
    public enum SeatKind : byte { Pressed, Channeled, Kindled }

    /// <summary>What GameHud feeds a campaign seat each frame.</summary>
    public struct SeatState
    {
        public SeatKind Kind;
        /// <summary>The channel runs (the first key of a channel); the ring's gold arc turns.</summary>
        public bool Channeling;
        /// <summary>A spender short of Resolve: Value / cost (0..1); -1 not short.</summary>
        public float Cost;
        /// <summary>M4 lead 14 (judge r3c M3): the press floor as a share of the cost (SeatCost.FloorShare: 0.5 a kindled
        /// "now" key, 1 or 0 the full cost). Short of it: the short look; from it to the cost: lit, the arc as strength.</summary>
        public float Floor;
        /// <summary>One of a union's two seats; the clasp drawn by this seat to its left neighbour; the linked rings
        /// (the two seats not side by side); the bond's "press now" on the second key.</summary>
        public bool Union, ClaspLeft, Rings, Bond;
        /// <summary>Fix A (6): its key is down (the sim's own Held of the skill on this seat): the pressed state.</summary>
        public bool Held;
        /// <summary>bd-ui W3: the stance she is in wears on every key seat: a 2 px ring just inside the bezel at 75% alpha
        /// (Colors.Transparent: none, set I).</summary>
        public Color Tint;
    }

    /// <summary>Its key cap (Instrument makes it); null: no keys (the arena).</summary>
    public KeyTag? Cap;

    SeatState st = new() { Cost = -1 };
    bool keyed, locked;
    float costShown = -1;
    double flareT = -1;
    SeatFx? lantern, spinner, bond, flare, ink, press, heldRing;
    string inkKey = "";
    Color capShown = new(-1, -1, -1, -1);
    bool capVisible = true;

    static readonly bool Trace = Args.Has("slots-trace");
    static readonly Color Edge = new("#ca6e06"), Mid = new("#f9b214");
    const float CapAlphaOpen = 0.3f;

    /// <summary>The cap hung on the seat: its chip centred on the seat's 12 o'clock, straddling the plate's top line and
    /// the ring's top (DgPanel.TopY, the ring at SeatR).</summary>
    public void SetCap(KeyTag cap)
    {
        Cap = cap;
        AddChild(cap);
        var seat = DgPanel.Seat(Index);
        float mid = (DgPanel.TopY + seat.Y - DgPanel.SeatR) / 2;
        cap.Place(Size.X / 2, mid - Instrument.TagH / 2 - Position.Y);
    }

    /// <summary>A campaign seat this frame (after Show or Empty).</summary>
    public void Feed(in SeatState s)
    {
        keyed = true;
        float cq = SeatCost.Shown(s.Cost);
        // (the cost met: the arc goes and the ready glow plays once)
        if (costShown >= 0 && cq < 0 && filled && !waiting) cue = 0;
        if (cq != costShown || s.Kind != st.Kind || s.Union != st.Union || s.ClaspLeft != st.ClaspLeft || s.Rings != st.Rings || s.Held != st.Held || s.Floor != st.Floor || s.Tint != st.Tint) dirty = true;
        costShown = cq;
        st = s;
        st.Cost = cq;
    }

    /// <summary>No keys here (the arena, the Lamps' wide view): the cap and the kinds go.</summary>
    public void Unkeyed()
    {
        if (!keyed) return;
        keyed = false;
        st = new SeatState { Cost = -1 };
        costShown = -1;
        dirty = true;
    }

    /// <summary>An empty seat: locked (not yet open at her level: no cap) or open (the cap at 30%).</summary>
    public void Empty(bool locked)
    {
        Empty();
        if (this.locked != locked) { this.locked = locked; dirty = true; }
    }

    /// <summary>Short of its press floor (a press does nothing), the glyph cools as when waiting.</summary>
    bool CostShort => keyed && filled && SeatCost.ShortShown(st.Cost, st.Floor);

    /// <summary>Under its full cost (the arc shows): short, or the fourth look (fires, not at full strength).</summary>
    bool BelowCost => keyed && filled && st.Cost >= 0;

    /// <summary>The lantern catching, by the seconds since a kindled seat fired itself (M4 §1, lead 6: the flat mid-band
    /// disc lost the glyph). Light: how much of the flare shows (whole for FlareHold, then gone over FlareSettle);
    /// Swell: the flare's size (it catches from FlareFrom of the well to all of it in FlareCatch).</summary>
    public const double FlareHold = 0.25, FlareSettle = 0.3, FlareCatch = 0.06;
    public const float FlareFrom = 0.6f;
    public static float FlareLight(double t) => t < 0 || t >= FlareHold + FlareSettle ? 0
        : t <= FlareHold ? 1 : 1 - Mathf.SmoothStep(0, 1, (float)((t - FlareHold) / FlareSettle));
    public static float FlareSwell(double t)
    {
        float k = (float)Math.Clamp(t / FlareCatch, 0, 1);
        return FlareFrom + (1 - FlareFrom) * (1 - (1 - k) * (1 - k));
    }

    /// <summary>The wait's level and the lantern's flare (M4 lead 5). The level's surface is a straight line across the
    /// well (DgMeters.Level), and it showed through the flare as the flare settled: a square-cornered lighter box
    /// climbing the lit disc (a short wait's level runs the whole well in the settle's 0.3 s). So under the flare the
    /// well holds no level: all of it dark, a round shade the lantern dims down to; when the flare has gone the level
    /// rises from the foot to where the wait stands in LevelRise. A wait known to be over about when the flare is
    /// (BriefWait) shows no level at all, as a fast cycle shows none.</summary>
    public const double LevelRise = 0.15, BriefWait = FlareHold + FlareSettle + 0.25;
    double levelRiseT = -1;
    bool briefWait;

    /// <summary>The level the well draws while it waits (0 all dark .. 1); -1: none drawn.</summary>
    float WaitLevel()
    {
        if (briefWait && waiting) return -1;
        if (flareT >= 0) return 0;
        float r = (float)ready;
        return levelRiseT >= 0 ? r * Mathf.SmoothStep(0, 1, (float)(levelRiseT / LevelRise)) : r;
    }

    /// <summary>A kindled seat that fired itself (its wait began): the lantern catches.</summary>
    void FiredItself()
    {
        briefWait = false;
        levelRiseT = -1;
        if (!keyed || st.Kind != SeatKind.Kindled) return;
        flareT = 0;
        briefWait = waitSecs >= 0 && waitSecs <= BriefWait;
        // (--slots-trace: a frame of the flare is picked by this line: the well is at the mid band for 0.25 s from here)
        if (Trace) GD.Print($"seat {Index}: {Id} flare begins (kindled, fired itself) frame {Engine.GetFramesDrawn()}");
    }

    int tracedWait = -1;

    /// <summary>--slots-trace: the wait number the seat draws, logged when it changes (n: the numeral; -1 none drawn), with
    /// the timer it was the ceiling of. A frame's facts are the last such line before its "saved" line: the trace's own
    /// lines come only every 0.3 s, and a shot's "at N s" is the shot's clock, about 0.4 s ahead of the fight's.</summary>
    void TraceWait(int n)
    {
        if (!Trace || n == tracedWait) return;
        tracedWait = n;
        if (n >= 0) GD.Print($"seat {Index}: {Id} wait number {n} (timer {waitSecs:0.00}) frame {Engine.GetFramesDrawn()}");
        else GD.Print($"seat {Index}: {Id} wait number none frame {Engine.GetFramesDrawn()}");
    }

    SeatFx Fx(SeatFx.Mode m)
    {
        float hr = DgRiver.Hole(Index);
        if (hr <= 0) hr = Size.X * 0.34f;
        var f = new SeatFx(m, Size, hr) { Visible = false };
        AddChild(f);
        // (the lantern's own light under the flare, the glyph's ink over it)
        if (lantern != null && m != SeatFx.Mode.Lantern) MoveChild(lantern, 0);
        if (ink != null && m != SeatFx.Mode.Ink) MoveChild(ink, -1);
        // (fix A2: the held ring stays above every added layer)
        if (heldRing != null && m != SeatFx.Mode.Held) MoveChild(heldRing, -1);
        // (the lights under the cap: the cap stays on top)
        if (Cap != null) MoveChild(Cap, -1);
        return f;
    }

    /// <summary>Each frame: the lantern, the turning arc, the bond's breath and the cap's light (Modulate and Rotation
    /// only; nothing redrawn, nothing built).</summary>
    void SeatTick(double dt)
    {
        bool kindled = keyed && filled && st.Kind == SeatKind.Kindled;
        if (kindled && lantern == null) lantern = Fx(SeatFx.Mode.Lantern);
        if (lantern != null)
        {
            if (lantern.Visible != kindled) lantern.Visible = kindled;
            if (kindled)
            {
                // lit and watching: edge amber at about 0.35, breathing 15% over 2.5 s; firing itself, the lantern
                // catches for 0.25 s (SeatFx.Flare: hot core, mid band, amber rim; the glyph in ink over it), then
                // settles back over 0.3 s
                float br = 1 + 0.15f * Mathf.Sin((float)(t * Mathf.Tau / 2.5));
                var col = Edge with { A = 0.35f * br };
                if (flareT >= 0)
                {
                    flareT += dt;
                    float k = FlareLight(flareT);
                    flare ??= Fx(SeatFx.Mode.Flare);
                    flare.Visible = k > 0;
                    flare.Modulate = new Color(1, 1, 1, k);
                    flare.Scale = Vector2.One * FlareSwell(flareT);
                    if (glyphKey != "")
                    {
                        ink ??= Fx(SeatFx.Mode.Ink);
                        if (inkKey != glyphKey)
                        {
                            inkKey = glyphKey;
                            int gi = (int)Mathf.Round(Mathf.Min(38, lantern.Hr * 2 * 0.80f));
                            ink.Glyph = Glyphs.Texture(glyphKey, gi * 2, Colors.White, 2.1f, line: true);
                            ink.GlyphSize = gi;
                            ink.QueueRedraw();
                        }
                        ink.Visible = k > 0;
                        ink.Modulate = new Color(1, 1, 1, k);
                    }
                    // (its own amber spills a little further over the bezel while it burns)
                    col = col.Lerp(Edge with { A = 0.62f }, k);
                    // (the flare gone: the wait's level, held dark under it, rises from the foot: WaitLevel)
                    if (k <= 0) { flareT = -1; levelRiseT = 0; dirty = true; }
                }
                lantern.Modulate = col;
            }
            else if (flareT >= 0 || (flare?.Visible ?? false))
            {
                flareT = -1;
                dirty = true;
                if (flare != null) flare.Visible = false;
                if (ink != null) ink.Visible = false;
            }
        }
        if (levelRiseT >= 0)
        {
            levelRiseT += dt;
            if (levelRiseT >= LevelRise) levelRiseT = -1;
            dirty = true;
        }
        // (fix A, 6: a key down, whatever the seat's kind: the ring lit, the well warm, and the bright head turning on
        // the arc, so held is never quieter than invited)
        bool held = keyed && filled && st.Held;
        // (M4 lead 13, r3b M2: held while short, the ring says the key is down but the well stays the short one)
        // (M4 lead 14, r3c M3: and no warm well from the floor to the cost: it fires, but not at full)
        bool warm = SeatCost.WarmWell(held, BelowCost);
        if (warm && press == null) press = Fx(SeatFx.Mode.Press);
        if (press != null && press.Visible != warm) press.Visible = warm;
        bool spin = keyed && filled && (st.Channeling || st.Held);
        if (Trace && (spin != (spinner?.Visible ?? false) || st.Bond != (bond?.Visible ?? false))) GD.Print($"seat {Index}: spin {spin} bond {st.Bond} keyed {keyed} filled {filled}");
        // (fix A2: a held seat's ring and bead are one Mix-blend node above the added layers; a channeling seat not held
        // keeps the added spinner)
        bool spinAdd = spin && !held;
        if (spinAdd && spinner == null) spinner = Fx(SeatFx.Mode.Spinner);
        if (spinner != null)
        {
            if (spinner.Visible != spinAdd) spinner.Visible = spinAdd;
            if (spinAdd) spinner.Rotation = (spinner.Rotation + (float)(dt * 0.75 * Mathf.Tau)) % Mathf.Tau;
        }
        if (held && heldRing == null) heldRing = Fx(SeatFx.Mode.Held);
        if (heldRing != null)
        {
            if (heldRing.Visible != held) heldRing.Visible = held;
            // (M4 lead 14, r3c S6: held under the cost, the ring stands 2 px out past an ink gap, with no sheen, so the
            // arc and its head read apart from it)
            bool wide = held && BelowCost;
            if (heldRing.Wide != wide) { heldRing.Wide = wide; heldRing.QueueRedraw(); }
            if (held) heldRing.Rotation = (heldRing.Rotation + (float)(dt * 0.75 * Mathf.Tau)) % Mathf.Tau;
        }
        bool bd = keyed && filled && st.Bond;
        if (bd && bond == null) bond = Fx(SeatFx.Mode.Bond);
        float breath = 0.5f + 0.5f * Mathf.Sin((float)t * 4.2f);
        if (bond != null)
        {
            if (bond.Visible != bd) bond.Visible = bd;
            if (bd) bond.Modulate = new Color(1, 1, 1, 0.45f + 0.5f * breath);
        }
        if (Cap == null) return;
        bool vis = keyed && (filled || !locked);
        if (vis != capVisible) { capVisible = vis; Cap.Visible = vis; }
        if (!vis) return;
        Color c = !filled ? new Color(1, 1, 1, CapAlphaOpen)
            : Colors.White;   // (M4 lead 9: no bond tint over 1.0 here: it pushed the bone cap's fill to pale yellow; the bond ring breathes)
        if (c != capShown) { capShown = c; Cap.Modulate = c; }
        if (Cap.Quiet != (kindled && !bd)) Cap.Quiet = kindled && !bd;
        if (Cap.Down != held) Cap.Down = held;
        bool ul = filled && st.Kind == SeatKind.Channeled;
        if (Cap.Underline != ul) Cap.Underline = ul;
    }

    /// <summary>The seat's marks over the well (DrawRing, after the ring's inner edge): the union's gold edge, its clasp or
    /// linked rings, and the cost arc.</summary>
    void DrawSeatMarks(Vector2 c, float hr)
    {
        if (!keyed || !filled) return;
        if (st.Union)
        {
            DrawArc(c, hr + 0.5f, 0, Mathf.Tau, 64, Style.Gold with { A = 0.92f }, 2, true);
            if (st.ClaspLeft) Clasp(c);
            if (st.Rings) LinkedRings(c + new Vector2(-0.7071f, -0.7071f) * (DgPanel.SeatR - 3));
        }
        if (st.Cost >= 0)
        {
            // a 2 px deep amber arc at the well's edge, filling clockwise from 12 o'clock as Value / cost
            // (M4 lead 11: it sits in a dark groove, with a ghost of the part still to fill)
            DrawArc(c, hr - 1.5f, 0, Mathf.Tau, 64, new Color(0.02f, 0.015f, 0.01f, 0.9f), 4, true);
            DrawArc(c, hr - 1.5f, 0, Mathf.Tau, 64, Color.Color8(200, 138, 48) with { A = 0.26f }, 2, true);
            if (st.Cost > 0.005f) DrawArc(c, hr - 1.5f, -Mathf.Pi / 2, -Mathf.Pi / 2 + Mathf.Tau * st.Cost, Math.Max(4, (int)(64 * st.Cost)), Color.Color8(200, 138, 48), 2, true);
            // (fix A, 12: near full it read as a selection ring: a dark tick at 12 o'clock breaks it where it starts,
            // and a bright bead rides its head)
            DrawLine(c + new Vector2(0, -(hr - 5.5f)), c + new Vector2(0, -(hr + 2f)), new Color(0.03f, 0.02f, 0.01f, 0.95f), 3);
            // (M4 lead 14, r3c M3: a kindled "now" key's press floor, a 2 px ink tick across the groove; past it the key
            // fires at the arc's strength)
            if (SeatCost.Tick(st.Floor) is var tk and > 0)
            {
                float ta = -Mathf.Pi / 2 + Mathf.Tau * tk;
                var td = new Vector2(Mathf.Cos(ta), Mathf.Sin(ta));
                // (r3d S2: ink on the arc, bone (the cap's, at 70%) on the empty groove, where ink was lost)
                var tc = st.Cost >= tk ? new Color(0.03f, 0.02f, 0.01f, 0.95f) : (Color.Color8(226, 214, 186) * 0.7f) with { A = 0.95f };
                DrawLine(c + td * (hr - 4f), c + td * (hr + 1f), tc, 2);
            }
            if (st.Cost > 0.005f)
            {
                float ha = -Mathf.Pi / 2 + Mathf.Tau * st.Cost;
                var hp = c + new Vector2(Mathf.Cos(ha), Mathf.Sin(ha)) * (hr - 1.5f);
                DrawCircle(hp, 3.6f, new Color(0.03f, 0.02f, 0.01f, 0.8f), true, -1, true);
                DrawCircle(hp, 2.6f, new Color("#fbf1d8"), true, -1, true);
            }
        }
    }

    /// <summary>The union's clasp across the gap to the left neighbour, at mid-height: a short gold bar with two rivets.</summary>
    void Clasp(Vector2 c)
    {
        float dx = DgPanel.Seat(Index).X - DgPanel.Seat(Index - 1).X;
        var m = new Vector2(c.X - dx / 2, c.Y);
        const float hw = 9, hh = 2.5f;
        DrawRect(new Rect2(m.X - hw - 1, m.Y - hh - 1, 2 * hw + 2, 2 * hh + 2), new Color(0.04f, 0.03f, 0.02f, 0.9f), true);
        DrawRect(new Rect2(m.X - hw, m.Y - hh, 2 * hw, 2 * hh), DgMeters.Gold, true);
        DrawRect(new Rect2(m.X - hw, m.Y - hh, 2 * hw, 1), new Color(1f, 0.93f, 0.75f, 0.8f), true);
        Rivet(m.X - 5.5f, m.Y);
        Rivet(m.X + 5.5f, m.Y);
        void Rivet(float x, float y)
        {
            DrawCircle(new Vector2(x, y), 1.7f, new Color(0.32f, 0.22f, 0.1f), true, -1, true);
            DrawCircle(new Vector2(x - 0.4f, y - 0.4f), 0.8f, new Color(1f, 0.92f, 0.7f), true, -1, true);
        }
    }

    /// <summary>Two small linked rings (a union whose seats are not side by side), at 10:30 on the bezel.</summary>
    void LinkedRings(Vector2 at)
    {
        var dark = new Color(0.04f, 0.03f, 0.02f, 0.9f);
        DrawArc(at + new Vector2(-2.3f, 0), 3.6f, 0, Mathf.Tau, 20, dark, 3.2f, true);
        DrawArc(at + new Vector2(2.3f, 0), 3.6f, 0, Mathf.Tau, 20, dark, 3.2f, true);
        DrawArc(at + new Vector2(-2.3f, 0), 3.6f, 0, Mathf.Tau, 20, DgMeters.Gold, 1.4f, true);
        DrawArc(at + new Vector2(2.3f, 0), 3.6f, 0, Mathf.Tau, 20, DgMeters.Gold, 1.4f, true);
    }
}

/// <summary>A seat's light that moves by the clock (M4 §1): the kindled well's lantern (a soft disc, added), the
/// lantern catching (Flare: the well's disc, hot #ffe9a8 at its middle through the mid band #f9b214 to the lit amber
/// #ca6e06 at its rim, laid over the well; Ink: the skill's line glyph in dark ink #1a1410 over the flare), the
/// channel's turning arc, the bond's breathing gold ring. Drawn once; the seat changes its Modulate, Scale or Rotation.</summary>
public partial class SeatFx : Control
{
    public enum Mode { Lantern, Spinner, Bond, Flare, Ink, Press, Held }
    readonly Mode mode;
    /// <summary>The held ring stood out past an ink gap, plain (held under the cost: judge r3c S6).</summary>
    public bool Wide;
    readonly float hr;
    public float Hr => hr;
    /// <summary>Ink: the glyph's white shape and the px it is shown across (the seat's gold inlay's).</summary>
    public Texture2D? Glyph;
    public int GlyphSize;
    static readonly Color Head = new("#fbf1d8"), Spin = new("#f9b214");
    /// <summary>M4 lead 9: the held ring's gold (#ffcd5a) and its head bead (#fff4d6).</summary>
    static readonly Color HeldGold = new("#ffcd5a"), HeldBead = new("#fff4d6");
    public static readonly Color FlareCore = new("#ffe9a8"), FlareMid = new("#f9b214"), FlareRim = new("#ca6e06"), InkDark = new("#1a1410");

    /// <summary>The flare's colour at d of the well's radius (0 its middle .. 1 its rim): the hot core held to 0.18,
    /// the mid band at 0.6, the lit amber at the rim.</summary>
    public static Color FlareAt(float d)
    {
        d = Mathf.Clamp(d, 0, 1);
        return d <= 0.6f ? FlareCore.Lerp(FlareMid, Mathf.SmoothStep(0.18f, 0.6f, d)) : FlareMid.Lerp(FlareRim, Mathf.SmoothStep(0.6f, 1f, d));
    }

    static ImageTexture? flareTex;
    /// <summary>The flare's disc (128 px, drawn at the well's size): FlareAt across it, its last 8% easing to nothing.</summary>
    static Texture2D FlareTex
    {
        get
        {
            if (flareTex != null) return flareTex;
            const int n = 128;
            var im = Image.CreateEmpty(n, n, false, Image.Format.Rgba8);
            for (int y = 0; y < n; y++)
                for (int x = 0; x < n; x++)
                {
                    float d = new Vector2(x + 0.5f - n / 2f, y + 0.5f - n / 2f).Length() / (n / 2f);
                    im.SetPixel(x, y, FlareAt(d) with { A = 1 - Mathf.SmoothStep(0.92f, 1f, d) });
                }
            im.GenerateMipmaps();
            return flareTex = ImageTexture.CreateFromImage(im);
        }
    }

    public SeatFx(Mode mode, Vector2 size, float hr)
    {
        this.mode = mode;
        this.hr = hr;
        MouseFilter = MouseFilterEnum.Ignore;
        Size = size;
        PivotOffset = size / 2;
        // (added light: the lantern in the well; the turning arc and the bond's breath read over the union's gold edge.
        // The flare and its ink are laid over, not added: added to a lit well the flare was a flat disc with no glyph)
        if (mode != Mode.Flare && mode != Mode.Ink && mode != Mode.Held) Material = new CanvasItemMaterial { BlendMode = CanvasItemMaterial.BlendModeEnum.Add };
    }

    public override void _Draw()
    {
        var c = Size / 2;
        switch (mode)
        {
            case Mode.Lantern:
                DrawTextureRect(DgMeters.Disc, new Rect2(c - Vector2.One * hr * 1.1f, Vector2.One * hr * 2.2f), false);
                break;
            case Mode.Flare:
                DrawTextureRect(FlareTex, new Rect2(c - Vector2.One * hr, Vector2.One * hr * 2), false);
                break;
            case Mode.Ink:
                if (Glyph != null) DrawTextureRect(Glyph, new Rect2(c - Vector2.One * GlyphSize / 2f, Vector2.One * GlyphSize), false, InkDark);
                break;
            case Mode.Spinner:
                // a white-gold head with a fading gold tail, turning clockwise in the bezel just outside the gold edge
                for (int i = 0; i < 6; i++)
                {
                    float a0 = -Mathf.Pi / 2 - 1.2f + i * 0.2f;
                    DrawArc(c, hr + 2.5f, a0, a0 + 0.21f, 6, Spin.Lerp(Head, i / 5f) with { A = 0.15f + 0.17f * i }, 3, true);
                }
                DrawArc(c, hr + 2.5f, -Mathf.Pi / 2 - 0.05f, -Mathf.Pi / 2 + 0.35f, 8, HeldBead, 3.5f, true);
                break;
            case Mode.Press:
                // the key down: the well warm, the ring fully lit (added light)
                DrawTextureRect(DgMeters.Disc, new Rect2(c - Vector2.One * (hr + 1f), Vector2.One * (hr + 1f) * 2), false, new Color(1f, 0.66f, 0.28f, 0.6f));
                DrawArc(c, hr + 5f, 0, Mathf.Tau, 64, Style.EmberHi with { A = 0.3f }, 4, true);
                break;
            case Mode.Held when Wide:
                // M4 lead 14 (r3c S6): held under the cost: a 2 px ink gap outside the arc's groove, then the plain gold
                // ring 2 px further out (no tail, no bead: the arc's head is the one bright point)
                DrawArc(c, hr + 2.25f, 0, Mathf.Tau, 64, new Color(0.03f, 0.02f, 0.01f, 0.9f), 2.5f, true);
                DrawArc(c, hr + 4.5f, 0, Mathf.Tau, 64, HeldGold, 2.5f, true);
                break;
            case Mode.Held:
                // M4 lead 9 (fix A2): the held ring in NORMAL blend (added to the lit bronze it clipped to lemon): the bar's
                // gold #ffcd5a at full alpha, above every added layer; its head bead white-gold #fff4d6 with a tail of 46
                // degrees fading to the ring's gold. Nothing here is brighter than the bead.
                DrawArc(c, hr + 2.5f, 0, Mathf.Tau, 64, HeldGold, 2.5f, true);
                for (int i = 0; i < 6; i++)
                {
                    float a0 = -Mathf.Pi / 2 - 0.05f - 0.8f + i * (0.8f / 6);
                    DrawArc(c, hr + 2.5f, a0, a0 + 0.8f / 6 + 0.01f, 4, HeldGold.Lerp(HeldBead, (i + 1) / 7f), 2.5f + 1f * (i + 1) / 6f, true);
                }
                DrawArc(c, hr + 2.5f, -Mathf.Pi / 2 - 0.05f, -Mathf.Pi / 2 + 0.35f, 8, HeldBead, 3.5f, true);
                break;
            case Mode.Bond:
                // the second key's "press now": a gold light in the well and a bright ring, breathing (the seat's Modulate)
                DrawTextureRect(DgMeters.Disc, new Rect2(c - Vector2.One * hr * 1.15f, Vector2.One * hr * 2.3f), false, Style.Gold with { A = 0.55f });
                DrawArc(c, hr + 2.5f, 0, Mathf.Tau, 64, Head with { A = 0.9f }, 2.5f, true);
                DrawArc(c, hr + 5f, 0, Mathf.Tau, 64, Style.EmberHi with { A = 0.4f }, 4, true);
                break;
        }
    }
}
