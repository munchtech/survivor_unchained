using System;
using Godot;
using SurvivorUnchained.Play;

namespace SurvivorUnchained.Ui;

/// <summary>
/// M4 §1 (docs/design/M4_HUD.md): a campaign seat's key and kind, the hands rule ("the slot UI shows which keys she
/// actually presses"). Each seat wears its key cap at 12 o'clock (a KeyTag chip, a child so a callout's dimming takes it
/// too); GameHud feeds it a SeatState each frame (values only, nothing built). The kinds at a glance:
///   pressed and hold: a bright cap; channeled: a bright cap on a gold underline, a gold arc turning in the ring while it
///   runs; kindled: the cap at half, the well lit like a lantern (breathing, flaring when it fires itself).
/// A spender short of Resolve: a gold arc fills clockwise from 12 o'clock as Value / cost. A union: both rings' inner
/// edges gold, a clasp across the gap of adjacent seats (linked rings at 10:30 otherwise), the second key breathing
/// gold while the bond is live. Empty: locked = no cap; open = the cap at 30%.
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
        /// <summary>One of a union's two seats; the clasp drawn by this seat to its left neighbour; the linked rings
        /// (the two seats not side by side); the bond's "press now" on the second key.</summary>
        public bool Union, ClaspLeft, Rings, Bond;
    }

    /// <summary>Its key cap (Instrument makes it); null: no keys (the arena).</summary>
    public KeyTag? Cap;
    /// <summary>The rank chip at half past four instead of half past one: the cap came within a pixel of it (Measure).</summary>
    public bool RankLow;
    /// <summary>The last measure: the cap's box to the 1:30 rank chip's edge, in the art's px (negative: overlapping).</summary>
    public float CapGap { get; private set; } = float.NaN;

    SeatState st = new() { Cost = -1 };
    bool keyed, locked;
    float costShown = -1;
    double flareT = -1;
    SeatFx? lantern, spinner, bond;
    Color capShown = new(-1, -1, -1, -1);
    bool capVisible = true;

    static readonly Color Edge = new("#ca6e06"), Mid = new("#f9b214");
    const float CapAlphaKindled = 0.5f, CapAlphaOpen = 0.3f;

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
        float cq = s.Cost < 0 ? -1 : Mathf.Floor(Mathf.Clamp(s.Cost, 0, 1) * 96) / 96;
        // (the cost met: the arc goes and the ready glow plays once)
        if (costShown >= 0 && cq < 0 && filled && !waiting) cue = 0;
        if (cq != costShown || s.Kind != st.Kind || s.Union != st.Union || s.ClaspLeft != st.ClaspLeft || s.Rings != st.Rings) dirty = true;
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

    /// <summary>Short of its cost, the glyph cools as when waiting.</summary>
    bool CostShort => keyed && filled && st.Cost >= 0;

    /// <summary>A kindled seat that fired itself (its wait began): the well flares to the mid band.</summary>
    void FiredItself() { if (keyed && st.Kind == SeatKind.Kindled) flareT = 0; }

    SeatFx Fx(SeatFx.Mode m)
    {
        float hr = DgRiver.Hole(Index);
        if (hr <= 0) hr = Size.X * 0.34f;
        var f = new SeatFx(m, Size, hr) { Visible = false };
        AddChild(f);
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
                // lit and watching: edge amber at about 0.35, breathing 15% over 2.5 s; firing itself, the mid band
                // for 0.25 s, then back over 0.3 s
                float br = 1 + 0.15f * Mathf.Sin((float)(t * Mathf.Tau / 2.5));
                var col = Edge with { A = 0.35f * br };
                if (flareT >= 0)
                {
                    flareT += dt;
                    var hot = Mid with { A = 0.62f };
                    col = flareT <= 0.25 ? hot : hot.Lerp(col, Mathf.SmoothStep(0, 1, (float)((flareT - 0.25) / 0.3)));
                    if (flareT >= 0.55) flareT = -1;
                }
                lantern.Modulate = col;
            }
        }
        bool spin = keyed && filled && st.Channeling;
        if (spin && spinner == null) spinner = Fx(SeatFx.Mode.Spinner);
        if (spinner != null)
        {
            if (spinner.Visible != spin) spinner.Visible = spin;
            if (spin) spinner.Rotation = (spinner.Rotation + (float)(dt * 0.75 * Mathf.Tau)) % Mathf.Tau;
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
            : bd ? new Color(1.18f + 0.25f * breath, 1.08f + 0.18f * breath, 0.82f + 0.08f * breath)
            : kindled ? new Color(1, 1, 1, CapAlphaKindled)
            : Colors.White;
        if (c != capShown) { capShown = c; Cap.Modulate = c; }
        bool ul = filled && st.Kind == SeatKind.Channeled;
        if (Cap.Underline != ul) Cap.Underline = ul;
    }

    /// <summary>Where the cap's chip and the 1:30 rank chip stand apart (the art's px): within a pixel, the rank chip
    /// moves to 4:30 (M4 §1, "measure"). Called when the caps re-label.</summary>
    public void Measure()
    {
        if (Cap == null) return;
        var box = Cap.ChipBox();
        box.Position += Cap.Position;
        var cc = Size / 2 + DgPanel.ChipOff;
        float dx = Math.Max(Math.Max(box.Position.X - cc.X, 0), cc.X - box.End.X), dy = Math.Max(Math.Max(box.Position.Y - cc.Y, 0), cc.Y - box.End.Y);
        CapGap = Mathf.Sqrt(dx * dx + dy * dy) - DgPanel.ChipR;
        bool low = CapGap < 1;
        if (low != RankLow) { RankLow = low; dirty = true; }
    }

    /// <summary>The rank chip's middle: 1:30, or 4:30 when the cap would touch it.</summary>
    Vector2 RankAt(Vector2 c) => c + (RankLow ? new Vector2(DgPanel.ChipOff.X, -DgPanel.ChipOff.Y) : DgPanel.ChipOff);

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
            // a 2 px gold arc at the well's edge, filling clockwise from 12 o'clock as Value / cost (its dark track under it)
            DrawArc(c, hr - 1.5f, 0, Mathf.Tau, 64, new Color(0, 0, 0, 0.45f), 3, true);
            if (st.Cost > 0.005f) DrawArc(c, hr - 1.5f, -Mathf.Pi / 2, -Mathf.Pi / 2 + Mathf.Tau * st.Cost, Math.Max(4, (int)(64 * st.Cost)), DgMeters.Gold, 2, true);
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
/// channel's turning arc, the bond's breathing gold ring. Drawn once; the seat changes its Modulate or Rotation.</summary>
public partial class SeatFx : Control
{
    public enum Mode { Lantern, Spinner, Bond }
    readonly Mode mode;
    readonly float hr;

    public SeatFx(Mode mode, Vector2 size, float hr)
    {
        this.mode = mode;
        this.hr = hr;
        MouseFilter = MouseFilterEnum.Ignore;
        Size = size;
        PivotOffset = size / 2;
        if (mode == Mode.Lantern) Material = new CanvasItemMaterial { BlendMode = CanvasItemMaterial.BlendModeEnum.Add };
    }

    public override void _Draw()
    {
        var c = Size / 2;
        switch (mode)
        {
            case Mode.Lantern:
                DrawTextureRect(DgMeters.Disc, new Rect2(c - Vector2.One * hr * 1.1f, Vector2.One * hr * 2.2f), false);
                break;
            case Mode.Spinner:
                // a gold segment with a fading tail, turning clockwise in the ring
                DrawArc(c, hr + 0.5f, -Mathf.Pi / 2 - 0.9f, -Mathf.Pi / 2 - 0.35f, 12, Style.Gold with { A = 0.35f }, 2, true);
                DrawArc(c, hr + 0.5f, -Mathf.Pi / 2 - 0.35f, -Mathf.Pi / 2 + 0.55f, 16, Style.GoldHi, 2.5f, true);
                break;
            case Mode.Bond:
                DrawArc(c, hr + 0.5f, 0, Mathf.Tau, 64, Style.GoldHi, 2.5f, true);
                DrawArc(c, hr + 3f, 0, Mathf.Tau, 64, Style.EmberHi with { A = 0.35f }, 3, true);
                break;
        }
    }
}
