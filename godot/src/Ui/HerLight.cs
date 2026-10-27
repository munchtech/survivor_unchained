using System;
using Godot;
using SurvivorUnchained.Play;

namespace SurvivorUnchained.Ui;

/// <summary>HUD variant "her life" (--hud-life her; the owner, 27 Oct: "we don't have our eyes down there very
/// often... interesting idea to just not even have the bubbles"): the life lamp hidden, her life read where the
/// eye already is. Three parts, all from the life the HUD shows (so --hud-pin and --hud-seq drive them):
/// Bar, her own bar under her feet (bone and iron, warm red; the recent hit draining in bone; the shield in pale
/// silver-blue; at 30% and under it beats with her heart); Pool, the lamp's warm screen-space light moved to her
/// (shaders/hud_lamp_pool.gdshader over a BackBufferCopy of its rect only, centred on her feet, its gain her
/// life: HeartPulse.PoolGain, flickering at 25% and under, none at 0); Edge, the screen's edges darkening to
/// blood on the beat at 30% and under (shaders/hud_low_edge.gdshader). The beat follows the heartbeat sound
/// (HeartPulse.LastSound) while it sounds, its own clock at the same pace while it does not (a pinned shot).</summary>
public sealed partial class HerLight : Control
{
    public static readonly bool On = Args.Get("hud-life") == "her";
    /// <summary>The live one (the shots' --pool-ab holds its pool off for a second picture).</summary>
    public static HerLight? Live;
    public static bool PoolHeld;
    /// <summary>Her life as last shown (the shots log it).</summary>
    public float LifeNow { get; private set; } = 1;

    /// <summary>The pool's quad round her feet (1080 px) and the pool's reach in it.</summary>
    static readonly Vector2 PoolSize = new(520, 340), PoolRadii = new(240, 158);

    public readonly Control Pool;
    public readonly ColorRect Edge;
    public readonly Bar Under;
    readonly BackBufferCopy copy;
    readonly ShaderMaterial poolMat, edgeMat;
    float sGain = -1, sStrength = -1, sBeat = -1;
    double clock, lastSync = double.NegativeInfinity;

    public HerLight()
    {
        MouseFilter = MouseFilterEnum.Ignore;
        Pool = new Control { MouseFilter = MouseFilterEnum.Ignore, Visible = false };
        Pool.AddChild(copy = new BackBufferCopy { CopyMode = BackBufferCopy.CopyModeEnum.Rect, Rect = new Rect2(Vector2.Zero, PoolSize) });
        poolMat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/hud_lamp_pool.gdshader") };
        poolMat.SetShaderParameter("size", PoolSize);
        poolMat.SetShaderParameter("centre", PoolSize / 2);
        poolMat.SetShaderParameter("radii", PoolRadii);
        Pool.AddChild(new ColorRect { Material = poolMat, MouseFilter = MouseFilterEnum.Ignore, Size = PoolSize });
        edgeMat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/hud_low_edge.gdshader") };
        Edge = new ColorRect { Material = edgeMat, MouseFilter = MouseFilterEnum.Ignore, Size = new Vector2(1920, 1080), Visible = false };
        Under = new Bar();
    }

    public override void _EnterTree() => Live = this;
    public override void _ExitTree() { if (Live == this) Live = null; }

    /// <summary>A frame. life and trail: as the HUD shows them (0..1); shield (0..1 of her life); fight: her fight
    /// is on and the HUD shown (the bar, the pool and the edge show only then); at: her feet on the screen.</summary>
    public void Tick(float dt, float life, float trail, float shield, bool fight, Vector2? at)
    {
        using var _ = new Perf.Span(Perf.Part.Hud);
        LifeNow = life;
        double now = Time.GetTicksMsec() / 1000.0;
        // the heart: in step with the sound while it beats, its own clock at the same pace otherwise
        bool low = fight && life <= HeartPulse.LowAt && life > 0;
        double period = HeartPulse.Period(life);
        if (HeartPulse.LastSound > lastSync && now - HeartPulse.LastSound < 0.2) { lastSync = HeartPulse.LastSound; clock = now - HeartPulse.LastSound; }
        else { clock += dt; if (clock >= period) clock %= period; }
        float beat = low ? HeartPulse.Shape(clock) : 0;
        float strength = low || (fight && life <= 0) ? HeartPulse.EdgeStrength(life) : 0;

        bool show = fight && at != null;
        Under.Visible = show;
        if (show) Under.Set(at!.Value, life, trail, shield, beat, dt);

        Send(edgeMat, "strength", strength, ref sStrength);
        Send(edgeMat, "beat", beat, ref sBeat);
        bool edge = fight && strength > 0.001f;
        if (Edge.Visible != edge) Edge.Visible = edge;

        float gain = show ? HeartPulse.PoolGain(life) * HeartPulse.Flicker(life, now) : 0;
        bool want = !PoolHeld && gain > 0.0005f;
        if (Pool.Visible != want) Pool.Visible = want;
        if (!want) return;
        var p = at!.Value - PoolSize / 2;
        if (Pool.Position != p) { Pool.Position = p; copy.Rect = new Rect2(p, PoolSize); }
        Send(poolMat, "gain", gain, ref sGain);
    }

    static void Send(ShaderMaterial m, string u, float v, ref float sent)
    {
        if (v == sent) return;
        sent = v;
        m.SetShaderParameter(u, v);
    }

    /// <summary>Her bar under her feet: a forged iron strap (dark, a lit top edge, riveted ends) round a sunk
    /// well; her life in warm red (a lit top, a deep foot), the recent hit in bone draining after it, the shield
    /// in pale silver-blue after her life, quarter marks over all. At 30% and under the red warms and swells on
    /// each beat and a blood glow breathes round the strap.</summary>
    public sealed partial class Bar : Control
    {
        /// <summary>The strap and the well in it (px at 1080), and how far under her feet it hangs.</summary>
        public const float W = 88, H = 12, Wx = 4, Wy = 2.5f, Drop = 22;
        public static float WellW => W - 2 * Wx;
        public static float WellH => H - 2 * Wy;
        float life = 1, trail = 1, shield, beat, shown = -1;
        static readonly Color Iron = new("#2b2521"), IronLit = new("#9a8b78"), IronCap = new("#5a4f45"), Well = new("#160807"),
            RedTop = new("#e2533d"), RedFoot = new("#8e1a12"), Hot = new("#ff8a5c"), TrailC = new("#e6cfa8"), ShieldC = new("#c6d6e6"), ShieldTop = new("#eef4fa");

        public Bar() { MouseFilter = MouseFilterEnum.Ignore; Size = new Vector2(W, H); }

        public void Set(Vector2 feet, float life, float trail, float shield, float beat, float dt)
        {
            var at = (feet + new Vector2(-W / 2, Drop)).Round();
            if (Position != at) Position = at;
            // the red eases down fast (a blow in about 0.1 s), up slower
            if (shown < 0) shown = life;
            shown += (life - shown) * (1 - Mathf.Exp(-(life < shown ? 24f : 8f) * dt));
            if (Math.Abs(life - shown) < 0.0005f) shown = life;
            trail = Math.Max(trail, shown);
            if (shown == this.life && trail == this.trail && shield == this.shield && beat == this.beat) return;
            this.life = shown; this.trail = trail; this.shield = shield; this.beat = beat;
            QueueRedraw();
        }

        public override void _Draw()
        {
            float l = Math.Clamp(life, 0, 1), t = Math.Clamp(trail, 0, 1), sh = Math.Clamp(shield, 0, 1);
            bool low = l <= HeartPulse.LowAt && l > 0;
            // a soft shadow, and at low life a blood glow breathing round it on the beat
            DrawRect(new Rect2(-2, -1, W + 4, H + 4), new Color(0, 0, 0, 0.28f));
            DrawRect(new Rect2(-1, 0, W + 2, H + 2), new Color(0, 0, 0, 0.42f));
            if (low && beat > 0.01f)
                for (int i = 3; i >= 1; i--)
                    DrawRect(new Rect2(-i - 1, -i - 1, W + 2 * i + 2, H + 2 * i + 2), new Color(0.85f, 0.12f, 0.06f, 0.10f * beat));
            // the strap: dark iron, a lit top edge, a dark foot, riveted end caps
            DrawRect(new Rect2(0, 0, W, H), Iron);
            DrawRect(new Rect2(1, 0, W - 2, 1), IronLit with { A = 0.85f });
            DrawRect(new Rect2(0, H - 1, W, 1), new Color(0.05f, 0.04f, 0.035f));
            foreach (float x in new[] { 0f, W - 3 })
            {
                DrawRect(new Rect2(x, 1, 3, H - 2), IronCap);
                DrawRect(new Rect2(x + 1, H / 2 - 1, 1, 2), IronLit with { A = 0.9f });
            }
            // the well
            float x0 = Wx, y0 = Wy, ww = WellW, wh = WellH;
            DrawRect(new Rect2(x0, y0, ww, wh), Well);
            // the recent hit, in bone, draining
            if (t > l + 0.002f) DrawRect(new Rect2(x0 + ww * l, y0, ww * (t - l), wh), TrailC with { A = 0.9f });
            // her life: warm red, lit at the top, deep at the foot; warmer and swelling on the beat when low
            if (l > 0)
            {
                float fw = ww * l;
                Color top = RedTop, foot = RedFoot;
                if (low) { top = top.Lerp(Hot, 0.25f + 0.55f * beat); foot = foot.Lerp(RedTop, 0.35f * beat); }
                DrawPolygon(new[] { new Vector2(x0, y0), new Vector2(x0 + fw, y0), new Vector2(x0 + fw, y0 + wh), new Vector2(x0, y0 + wh) },
                    new[] { top, top, foot, foot });
                DrawRect(new Rect2(x0, y0, fw, 1), new Color(1, 0.78f, 0.62f, 0.55f + (low ? 0.35f * beat : 0)));
            }
            // the shield: after her life (over its end when it would run past the strap)
            if (sh > 0.002f)
            {
                float sw = ww * Math.Min(sh, 1);
                float sx = Math.Min(x0 + ww * l, x0 + ww - sw);
                DrawRect(new Rect2(sx, y0, sw, wh), ShieldC with { A = 0.92f });
                DrawRect(new Rect2(sx, y0, sw, 1), ShieldTop);
                DrawRect(new Rect2(sx, y0, 1, wh), new Color(0.25f, 0.3f, 0.38f, 0.8f));
            }
            // the quarter marks
            for (int q = 1; q < 4; q++) DrawRect(new Rect2(Mathf.Round(x0 + ww * q / 4f), y0 + 1, 1, wh - 1), new Color(0.05f, 0.02f, 0.02f, 0.45f));
            // the well's own shade: a dark line under the strap's lit lip
            DrawRect(new Rect2(x0, y0, ww, 1), new Color(0, 0, 0, 0.35f));
        }
    }
}

/// <summary>HUD variant "her life": the chain's left end, where the lamp's eye held it: a forged iron ring the
/// first link passes through.</summary>
public sealed partial class ChainEnd : Control
{
    public ChainEnd() { MouseFilter = MouseFilterEnum.Ignore; Size = new Vector2(1920, 1080); }

    public override void _Draw()
    {
        var c = Instrument.EyeL + new Vector2(-7, 0);
        DrawCircle(c + new Vector2(0, 2), 10.5f, new Color(0, 0, 0, 0.45f));
        DrawCircle(c, 10, new Color("#2b2521"));
        DrawArc(c, 8.2f, Mathf.Pi * 1.05f, Mathf.Pi * 1.95f, 20, new Color("#9a8b78"), 1.6f, true);
        DrawArc(c, 8.2f, Mathf.Pi * 0.1f, Mathf.Pi * 0.9f, 20, new Color("#14100d"), 1.6f, true);
        DrawCircle(c, 4.2f, new Color("#0b0807"));
        DrawArc(c, 4.4f, Mathf.Pi * 0.1f, Mathf.Pi * 0.9f, 12, new Color("#6f6355"), 1.1f, true);
    }
}
