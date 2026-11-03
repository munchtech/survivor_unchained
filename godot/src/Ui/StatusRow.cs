using System;
using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Play;

namespace SurvivorUnchained.Ui;

/// <summary>UI 28: what is on her, as two families of small glass marks (StatusShelf orders them). A buff is a dark
/// glass disc with a round rim, its glyph cool blue; a debuff the same size cut to an eight-point facet, red-tinted
/// glass, its glyph ember. Its time is a ring on the rim draining clockwise from 12 o'clock (pulsing its last 1.5 s;
/// full and still if permanent); stacks over one a small number at its foot right. The barrier ("aegis") wears the
/// orb's silver-blue (HerLight's ShieldC), glyph and ring, so it reads with the ring round the orb.
/// Where (--status-at shelf|orb, default shelf): "shelf" one row over the bar above the passive studs, buffs from
/// x 948 growing left, debuffs from x 972 growing right; "orb" two rows right-aligned at x 375 beside the orb, buffs
/// over debuffs, growing left. Design px at 1.0: it lives in Instrument, which carries HudBottom's scale.</summary>
public partial class StatusRow : Control
{
    public const float D = 30, Pitch = 34;
    public static readonly Color BuffC = new("#9ad4ff"), DebuffC = new("#ff8a6a"), BarrierC = new("#c6d6e6");
    public static readonly bool AtOrb = (Args.Get("status-at") ?? "shelf").Trim().ToLowerInvariant() == "orb";

    readonly StatusShelf shelf = new();
    readonly List<Mark> buffs = new(), debuffs = new();

    public StatusRow()
    {
        MouseFilter = MouseFilterEnum.Ignore;
        Position = Vector2.Zero;
        Size = new Vector2(1920, 1080);
    }

    /// <summary>The centre of slot i (0 nearest the anchor) of a side.</summary>
    public static Vector2 Centre(bool good, int i)
    {
        if (AtOrb) return new Vector2(375 - D / 2 - Pitch * i, good ? 958 : 994);
        return good ? new Vector2(948 - D / 2 - Pitch * i, 950) : new Vector2(972 + D / 2 + Pitch * i, 950);
    }

    public void Show(IReadOnlyList<StatusShelf.Entry> now)
    {
        shelf.Update(now);
        Fill(buffs, shelf.Buffs, true);
        Fill(debuffs, shelf.Debuffs, false);
    }

    void Fill(List<Mark> marks, List<StatusShelf.Slot> slots, bool good)
    {
        while (marks.Count < slots.Count)
        {
            var m = new Mark();
            m.Position = Centre(good, marks.Count) - new Vector2(D / 2, D / 2);
            AddChild(m);
            marks.Add(m);
        }
        for (int i = 0; i < marks.Count; i++)
        {
            marks[i].Visible = i < slots.Count;
            if (i < slots.Count) marks[i].Set(slots[i]);
        }
    }

    /// <summary>One mark (30 px).</summary>
    sealed partial class Mark : Control
    {
        StatusShelf.Slot s;
        bool has;
        float drawnF = -1;
        Texture2D? glyph;
        string glyphKey = "";

        public Mark() { MouseFilter = MouseFilterEnum.Ignore; Size = new Vector2(D, D); }

        public void Set(StatusShelf.Slot n)
        {
            bool same = has && n.Key == s.Key && n.Glyph == s.Glyph && n.Good == s.Good && n.Stacks == s.Stacks && n.More == s.More
                && n.Pulse == s.Pulse && n.Permanent == s.Permanent;
            s = n;
            has = true;
            var col = Ink(n);
            string gk = n.Glyph + "|" + col.ToHtml();
            if (n.Glyph != "" && gk != glyphKey) { glyphKey = gk; glyph = Glyphs.Texture(n.Glyph, 40, col, 1.6f, true); }
            if (!same || Math.Abs(n.Fraction - drawnF) > 0.002f) QueueRedraw();
            SetProcess(n.Pulse);
        }

        static Color Ink(StatusShelf.Slot n) => n.Glyph == "aegis" && n.Good ? BarrierC : n.Good ? BuffC : DebuffC;

        public override void _Process(double delta) { if (s.Pulse) QueueRedraw(); }

        /// <summary>The facet's outline at radius r: eight points, one at the top (clockwise from it).</summary>
        static Vector2[] Facet(Vector2 c, float r, int extra = 0)
        {
            var p = new Vector2[8 + extra];
            for (int i = 0; i < p.Length; i++)
            {
                float a = -Mathf.Pi / 2 + Mathf.Tau * (i % 8) / 8f;
                p[i] = c + new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * r;
            }
            return p;
        }

        /// <summary>The first fraction f of the facet's outline, clockwise from its top point.</summary>
        static Vector2[] FacetRun(Vector2 c, float r, float f)
        {
            var pts = new List<Vector2>();
            var v = Facet(c, r, 1);
            float run = f * 8;
            for (int i = 0; i < 8 && run > 0; i++)
            {
                if (i == 0) pts.Add(v[0]);
                float t = Math.Min(1, run);
                pts.Add(v[i].Lerp(v[i + 1], t));
                run -= 1;
            }
            return pts.ToArray();
        }

        public override void _Draw()
        {
            if (!has) return;
            drawnF = s.Fraction;
            var c = new Vector2(D / 2, D / 2);
            var ink = Ink(s);
            float pulse = s.Pulse ? 0.5f + 0.5f * Mathf.Cos((float)Time.GetTicksMsec() / 1000f * Mathf.Tau * 2.6f) : 1;
            var ringC = ink with { A = s.Pulse ? 0.45f + 0.55f * pulse : 1 };
            const float rw = 2.5f;
            if (s.Good)
            {
                // the glass: a soft drop under it, the dark disc, a lift of light in its upper half
                DrawCircle(c + new Vector2(0, 1), 15.2f, new Color(0, 0, 0, 0.35f));
                DrawCircle(c, 14.6f, new Color("#0a141d") with { A = 0.88f });
                DrawCircle(c + new Vector2(0, -3.5f), 9.5f, new Color("#2a4458") with { A = 0.22f });
                // the rim, and the timer on it
                DrawArc(c, 14.6f, 0, Mathf.Tau, 48, (s.Glyph == "aegis" ? BarrierC : new Color("#6e8799")) with { A = 0.9f }, 1.0f, true);
                DrawArc(c, 12.6f, 0, Mathf.Tau, 48, new Color(0, 0, 0, 0.45f), rw, true);
                if (s.More == 0 && s.Fraction > 0.001f)
                {
                    if (s.Fraction >= 0.999f) DrawArc(c, 12.6f, 0, Mathf.Tau, 48, ringC, rw, true);
                    else DrawArc(c, 12.6f, -Mathf.Pi / 2, -Mathf.Pi / 2 + Mathf.Tau * s.Fraction, Math.Max(4, (int)(48 * s.Fraction)), ringC, rw, true);
                }
            }
            else
            {
                var shadow = Facet(c + new Vector2(0, 1), 16.0f);
                DrawColoredPolygon(shadow, new Color(0, 0, 0, 0.35f));
                DrawColoredPolygon(Facet(c, 15.4f), new Color("#160807") with { A = 0.9f });
                DrawColoredPolygon(Facet(c + new Vector2(0, -3.5f), 9.5f), new Color("#43201a") with { A = 0.17f });
                var rim = Facet(c, 15.4f, 1);
                DrawPolyline(rim, new Color("#a3604c") with { A = 0.9f }, 1.0f, true);
                DrawPolyline(Facet(c, 13.2f, 1), new Color(0, 0, 0, 0.45f), rw, true);
                if (s.More == 0 && s.Fraction > 0.001f)
                    DrawPolyline(s.Fraction >= 0.999f ? Facet(c, 13.2f, 1) : FacetRun(c, 13.2f, s.Fraction), ringC, rw, true);
            }
            if (s.More > 0)
            {
                var f = Style.UiHeavy;
                string t = $"+{s.More}";
                var sz = f.GetStringSize(t, HorizontalAlignment.Left, -1, 13);
                var at = new Vector2(Mathf.Round(c.X - sz.X / 2), Mathf.Round(c.Y + 4.6f));
                DrawStringOutline(f, at, t, HorizontalAlignment.Left, -1, 13, 4, new Color(0, 0, 0, 0.8f));
                DrawString(f, at, t, HorizontalAlignment.Left, -1, 13, ink);
                return;
            }
            if (glyph != null) DrawTextureRect(glyph, new Rect2(c - new Vector2(10, 10), new Vector2(20, 20)), false);
            if (s.Stacks > 1)
            {
                var f = Style.UiHeavy;
                string t = $"{s.Stacks}";
                var sz = f.GetStringSize(t, HorizontalAlignment.Left, -1, 12);
                var at = new Vector2(Mathf.Round(D + 2 - sz.X), D + 2);
                DrawStringOutline(f, at, t, HorizontalAlignment.Left, -1, 12, 4, new Color(0.02f, 0.02f, 0.03f, 0.95f));
                DrawString(f, at, t, HorizontalAlignment.Left, -1, 12, new Color("#f4efe6"));
            }
        }
    }
}
