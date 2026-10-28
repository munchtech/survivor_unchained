using System;
using Godot;
using SurvivorUnchained.Play;

namespace SurvivorUnchained.Ui;

/// <summary>Her life where the eye already is (UI 15 fix 1; the owner, 27 Oct: "we don't have our eyes down there
/// very often"), from the life the HUD shows (so --hud-pin and --hud-seq drive it): Bar, her own bar under her feet
/// (bone and iron, warm red; the recent hit draining in bone; the shield in pale silver-blue; at 30% and under it
/// beats with her heart); Edge, the screen's edges darkening to blood on the beat at 30% and under
/// (shaders/hud_low_edge.gdshader). The beat follows the heartbeat sound (HeartPulse.LastSound) while it sounds, its
/// own clock at the same pace while it does not (a pinned shot).</summary>
public sealed partial class HerLight : Control
{
    /// <summary>--no-edge: the low-life edge pulse off entirely (for an ABAB of the perf).</summary>
    static readonly bool NoEdge = Args.Has("no-edge");
    /// <summary>Shots only (--beat-peak): the low-life beat held at its peak, so a still shows the edge pulse.</summary>
    static readonly bool beatPeak = Args.Has("beat-peak");
    /// <summary>The live one (the shots log its life).</summary>
    public static HerLight? Live;
    /// <summary>Her life as last shown (the shots log it).</summary>
    public float LifeNow { get; private set; } = 1;
    public Vector2 FeetNow { get; private set; }
    /// <summary>For the shots' log: her feet on the screen and her life as shown ("" without this HUD).</summary>
    public static string Note() => Live is { } h ? $" feet {h.FeetNow.X:0} {h.FeetNow.Y:0} life {h.LifeNow:0.000}" : "";

    public readonly Control Edge;
    public readonly Bar Under;
    readonly ShaderMaterial edgeMat;
    float sStrength = -1, sBeat = -1;
    double clock, lastSync = double.NegativeInfinity;

    public HerLight()
    {
        MouseFilter = MouseFilterEnum.Ignore;
        edgeMat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/hud_low_edge.gdshader") };
        // (the edge reads the screen: its own full copy first, since the orb's rect copy leaves the rest of the
        // back buffer stale or black; a still caught the edges black the frame the pulse came on)
        Edge = new Control { MouseFilter = MouseFilterEnum.Ignore, Size = new Vector2(1920, 1080), Visible = false };
        Edge.AddChild(new BackBufferCopy { CopyMode = BackBufferCopy.CopyModeEnum.Viewport });
        Edge.AddChild(new ColorRect { Material = edgeMat, MouseFilter = MouseFilterEnum.Ignore, Size = new Vector2(1920, 1080) });
        Under = new Bar();
    }

    public override void _EnterTree() => Live = this;
    public override void _ExitTree() { if (Live == this) Live = null; }

    /// <summary>A frame. life and trail: as the HUD shows them (0..1); shield (0..1 of her life); fight: her fight
    /// is on and the HUD shown (the bar and the edge show only then); at: her feet on the screen; bar: the
    /// bar's own fade (the HUD eases it in and out with the night's fight and the "Health under you" setting).</summary>
    public void Tick(float dt, float life, float trail, float shield, bool fight, Vector2? at, float bar = 1)
    {
        using var _ = new Perf.Span(Perf.Part.Hud);
        LifeNow = life;
        if (at is { } ft) FeetNow = ft;
        double now = Time.GetTicksMsec() / 1000.0;
        // the heart: in step with the sound while it beats, its own clock at the same pace otherwise
        bool low = fight && life <= HeartPulse.LowAt && life > 0;
        // (UI 18 judge M1: the edge follows the fight itself, not the bar under her feet, which the HUD shows only
        // in the night's fight: by day at 18% there was no edge at all)
        bool edgeFight = fight;
        fight &= bar > 0.001f;
        double period = HeartPulse.Period(life);
        if (HeartPulse.LastSound > lastSync && now - HeartPulse.LastSound < 0.2) { lastSync = HeartPulse.LastSound; clock = now - HeartPulse.LastSound; }
        else { clock += dt; if (clock >= period) clock %= period; }
        float beat = low ? beatPeak ? 1 : HeartPulse.Shape(clock) : 0;
        float strength = !NoEdge && (low || (edgeFight && life <= 0)) ? HeartPulse.EdgeStrength(life) : 0;

        bool show = fight && at != null;
        Under.Visible = show;
        if (show)
        {
            Under.Set(at!.Value, life, trail, shield, beat, dt);
            var mod = Colors.White with { A = bar };
            if (Under.Modulate != mod) Under.Modulate = mod;
        }

        Send(edgeMat, "strength", strength, ref sStrength);
        Send(edgeMat, "beat", beat, ref sBeat);
        bool edge = edgeFight && strength > 0.001f;
        if (Edge.Visible != edge) Edge.Visible = edge;
    }

    static void Send(ShaderMaterial m, string u, float v, ref float sent)
    {
        if (v == sent) return;
        sent = v;
        m.SetShaderParameter(u, v);
    }

    /// <summary>Her bar under her feet (UI 15 fix 1: in every HUD, the HUD's own iron and copper): a forged iron
    /// strap in the instrument's iron (Cuff.Iron under the irons' night/day light, Cuff.Cold), a hammered lit
    /// top edge and a dark foot, copper collars riveted round its ends (the chain's warm links' copper); in its
    /// sunk well her life in warm red with an ember wick burning at its end (a hot bead, its glow added over the
    /// iron), the recent hit in bone draining after it, the shield in pale silver-blue after her life, quarter
    /// notches over all. At 30% and under a blood glow stands round the strap (there in a still, swelling on
    /// each beat) and the red warms with the heart.</summary>
    public sealed partial class Bar : Control
    {
        /// <summary>The strap and the well in it (px at 1080), and how far under her feet it hangs.</summary>
        public const float W = 96, H = 14, Wx = 6, Wy = 3, Drop = 21, Collar = 5;
        public static float WellW => W - 2 * Wx;
        public static float WellH => H - 2 * Wy;
        float life = 1, trail = 1, shield, beat, shown = -1;
        bool day;
        static readonly Color Well = new("#120605"), RedTop = new("#e5503a"), RedFoot = new("#7e140e"), Hot = new("#ff8a5c"),
            TrailC = new("#e6cfa8"), ShieldC = new("#c6d6e6"), ShieldTop = new("#eef4fa"),
            CopperLit = new("#f0b07a"), CopperHi = new("#c87440"), CopperMid = new("#8e4522"), CopperFoot = new("#3a170a"),
            WickCore = new("#fff0c8"), WickHot = new("#ffb35a");
        readonly WickGlow glow;

        public Bar()
        {
            MouseFilter = MouseFilterEnum.Ignore;
            Size = new Vector2(W, H);
            glow = new WickGlow(this) { Material = new CanvasItemMaterial { BlendMode = CanvasItemMaterial.BlendModeEnum.Add } };
            AddChild(glow);
        }

        public void Set(Vector2 feet, float life, float trail, float shield, float beat, float dt)
        {
            var at = (feet + new Vector2(-W / 2, Drop)).Round();
            if (Position != at) Position = at;
            // the red eases down fast (a blow in about 0.1 s), up slower
            if (shown < 0) shown = life;
            shown += (life - shown) * (1 - Mathf.Exp(-(life < shown ? 24f : 8f) * dt));
            if (Math.Abs(life - shown) < 0.0005f) shown = life;
            trail = Math.Max(trail, shown);
            if (shown == this.life && trail == this.trail && shield == this.shield && beat == this.beat && day == Cuff.Day) return;
            this.life = shown; this.trail = trail; this.shield = shield; this.beat = beat; day = Cuff.Day;
            QueueRedraw();
            glow.QueueRedraw();
        }

        bool Low => life <= HeartPulse.LowAt && life > 0;
        /// <summary>The low-life glow now: there in a still (0.45), full on the beat.</summary>
        float LowGlow => Low ? 0.45f + 0.55f * beat : 0;

        static Color Iron(float light) => (Cuff.Iron(light) * Cuff.Cold) with { A = 1 };

        void Shade(float x, float y, float w, float h, Color top, Color foot) =>
            DrawPolygon(new[] { new Vector2(x, y), new Vector2(x + w, y), new Vector2(x + w, y + h), new Vector2(x, y + h) }, new[] { top, top, foot, foot });

        public override void _Draw()
        {
            float l = Math.Clamp(life, 0, 1), t = Math.Clamp(trail, 0, 1), sh = Math.Clamp(shield, 0, 1);
            bool low = Low;
            // a soft shadow, and at low life a blood glow standing round it, swelling on the beat
            DrawRect(new Rect2(-2, -1, W + 4, H + 4), new Color(0, 0, 0, 0.30f));
            DrawRect(new Rect2(-1, 0, W + 2, H + 2), new Color(0, 0, 0, 0.45f));
            if (low)
                for (int i = 4; i >= 1; i--)
                    DrawRect(new Rect2(-i - 1, -i, W + 2 * i + 2, H + 2 * i), new Color(0.80f, 0.06f, 0.04f, 0.085f * LowGlow * (5 - i) / 2.5f));
            // the strap: forged iron, round in section (lit across its upper third, dark at its foot)
            Shade(0, 0, W, H * 0.4f, Iron(0.8f), Iron(0.44f));
            Shade(0, H * 0.4f, W, H * 0.6f, Iron(0.44f), Iron(0.1f));
            DrawRect(new Rect2(1, 0, W - 2, 1), Iron(1) with { A = 0.85f });
            DrawRect(new Rect2(0, H - 1, W, 1), new Color(0.03f, 0.025f, 0.02f));
            // hammer marks: a few dents in the lit edge, each a dark pit with a lit lip after it
            foreach (float x in new[] { 11f, 23f, 38f, 52f, 61f, 74f, 86f })
            {
                DrawRect(new Rect2(x, 1, 2, 1), Iron(0.12f) with { A = 0.7f });
                DrawRect(new Rect2(x + 2, 1, 1, 1), Iron(1) with { A = 0.5f });
                DrawRect(new Rect2(x - 3, H - 2, 2, 1), Iron(0.5f) with { A = 0.35f });
            }
            // the well
            float x0 = Wx, y0 = Wy, ww = WellW, wh = WellH;
            DrawRect(new Rect2(x0 - 1, y0 - 1, ww + 2, wh + 2), new Color(0.02f, 0.012f, 0.01f));
            DrawRect(new Rect2(x0, y0, ww, wh), Well);
            DrawRect(new Rect2(x0 - 1, y0 + wh, ww + 2, 1), Iron(0.75f) with { A = 0.55f });
            // the recent hit, in bone, draining
            if (t > l + 0.002f)
                Shade(x0 + ww * l, y0, ww * (t - l), wh, TrailC, TrailC.Darkened(0.28f));
            // her life: warm red, lit at the top, deep at the foot; warmer and swelling on the beat when low
            if (l > 0)
            {
                float fw = ww * l;
                Color top = RedTop, foot = RedFoot;
                if (low) { top = top.Lerp(Hot, 0.2f + 0.5f * LowGlow); foot = foot.Lerp(RedTop, 0.3f * LowGlow); }
                Shade(x0, y0, fw, wh, top, foot);
                DrawRect(new Rect2(x0, y0, fw, 1), new Color(1, 0.80f, 0.64f, 0.6f + 0.3f * LowGlow));
                // the wick: the fill's end burns, a hot bead two px wide, warmer toward the foot
                float wx = Mathf.Max(x0, x0 + fw - 2);
                Shade(wx, y0, Mathf.Min(2, fw), wh, WickCore, WickHot);
            }
            // the shield: after her life (over its end when it would run past the strap)
            if (sh > 0.002f)
            {
                float sw = ww * Math.Min(sh, 1);
                float sx = Math.Min(x0 + ww * l, x0 + ww - sw);
                Shade(sx, y0, sw, wh, ShieldC with { A = 0.95f }, ShieldC.Darkened(0.3f) with { A = 0.95f });
                DrawRect(new Rect2(sx, y0, sw, 1), ShieldTop);
                DrawRect(new Rect2(sx, y0, 1, wh), new Color(0.22f, 0.27f, 0.36f, 0.85f));
            }
            // the quarter notches
            for (int q = 1; q < 4; q++)
            {
                float qx = Mathf.Round(x0 + ww * q / 4f);
                DrawRect(new Rect2(qx, y0 + 1, 1, wh - 1), new Color(0.04f, 0.015f, 0.01f, 0.5f));
                DrawRect(new Rect2(qx, 0, 1, y0 - 1), Iron(0.1f));
            }
            // the well's own shade under the strap's lip
            DrawRect(new Rect2(x0, y0, ww, 1), new Color(0, 0, 0, 0.35f));
            // the copper collars round its ends: round in section, a rivet through each, the seam where they meet the iron
            foreach (float cx in new[] { 0f, W - Collar })
            {
                Shade(cx, -1, Collar, H * 0.45f + 1, CopperLit, CopperHi);
                Shade(cx, H * 0.45f, Collar, H * 0.55f + 1, CopperMid, CopperFoot);
                DrawRect(new Rect2(cx, -1, Collar, 1), CopperLit with { A = 0.9f });
                DrawRect(new Rect2(cx, H, Collar, 1), new Color(0.05f, 0.02f, 0.01f, 0.9f));
                float seam = cx == 0 ? Collar : cx - 1;
                DrawRect(new Rect2(seam, -1, 1, H + 2), new Color(0.06f, 0.03f, 0.02f, 0.85f));
                var rv = new Vector2(cx + Collar / 2f, H / 2f);
                DrawCircle(rv, 1.6f, CopperFoot);
                DrawCircle(rv - new Vector2(0.4f, 0.5f), 0.8f, CopperLit);
            }
        }

        /// <summary>The wick's glow and the low beat's warmth, added over the strap (CanvasItemMaterial add).</summary>
        sealed partial class WickGlow : Control
        {
            readonly Bar bar;
            public WickGlow(Bar bar) { this.bar = bar; MouseFilter = MouseFilterEnum.Ignore; Size = new Vector2(W, H); }

            public override void _Draw()
            {
                float l = Math.Clamp(bar.life, 0, 1);
                if (l <= 0) return;
                var at = new Vector2(Wx + WellW * l - 1, Wy + WellH / 2f);
                float k = 1 + 0.6f * bar.LowGlow;
                var c = new Color(1, 0.42f, 0.12f);
                DrawCircle(at, 9, c with { A = 0.07f * k });
                DrawCircle(at, 6, c with { A = 0.11f * k });
                DrawCircle(at, 3.5f, new Color(1, 0.6f, 0.25f, 0.20f * k));
                DrawCircle(at, 1.8f, new Color(1, 0.85f, 0.55f, 0.35f * k));
            }
        }
    }
}
