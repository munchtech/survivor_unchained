using System;
using Godot;
using SurvivorUnchained.Play;

namespace SurvivorUnchained.Ui;

/// <summary>HUD A2 "Lamps Are Lit" (the owner's pick, 26 October): her life is an oil lamp on the left of the
/// instrument, in place of the life vessel and its cuff. One quad and one shader (shaders/hud_lamp.gdshader)
/// over the painted lamp (art/ui/lamp_life, tools/uiforge/lamp_life_cut.py): the oil in its font is her life
/// (Vessel.Flow's motion: the damped slosh, the hurt film, the heal, the heartbeat at 30% and under, the
/// shield's frost); the flame on its wick is her life too (LampState: tall, smaller, guttering, out with
/// smoke, relit). Its light falls on the ground round it: Pool, a local screen-space light under the whole HUD
/// (shaders/hud_lamp_pool.gdshader; GameHud lays it first), its gain her flame's light, hidden with the lamp.
/// The number (bone on a dark halo) stands on the lamp's foot, out of the font's middle where the level reads;
/// it redraws only when it changes.</summary>
public partial class LifeLamp : Control
{
    /// <summary>The quad, in 1080 px (art/ui/lamp_life/lamp_geo.json; the art is twice this).</summary>
    public static readonly Vector2 Canvas = new(176, 196);
    /// <summary>The lamp's foot in the quad, the eye on its font's right strap (the chain leaves from it), the
    /// font's middle (the number) and the wick.</summary>
    public const float FootY = 194.22f;
    public static readonly Vector2 Eye = new(162.02f, 165.03f), FontMid = new(88.18f, 152.01f), Wick = new(88.38f, 85.35f);
    /// <summary>The oil's top and foot rows, the font's sides, and the flame's height at full: its tip (35 px over
    /// the wick at its brightest flicker) stays under the instrument's top line (904: the old cuff's top, 176 px
    /// over the foot of the screen), the lamp's own top at 908.</summary>
    public const float OilTop = 129.5f, OilBot = 169.25f, FlameFull = 34f;
    public static readonly Vector2 FontX = new(18.18f, 158.18f);
    /// <summary>Where its foot stands on the screen (the old life cuff's foot, 28 px clear of the edge).</summary>
    public const float Floor = 1052;
    /// <summary>Where the number stands: its middle on the lamp's foot, under the font.</summary>
    public const float NumberY = 182f;
    /// <summary>The pool's quad round the lamp's foot (1080 px, from the lamp's quad's top left) and its gain at
    /// full light (the scene's brightness lifted by about +45% at its heart: the warm tint takes a share).</summary>
    public static readonly Rect2 PoolRect = new(-152, -78, 480, 300);
    public const float PoolGain = 0.54f;
    static readonly bool noPool = Args.Has("no-lamp-pool"), noOil = Args.Has("lamp-no-oil");

    /// <summary>The level and the shield (0..1 of her life), the trail (unused: the hurt film is the oil's own),
    /// and Pulse: 1 where her heartbeat may sound (the fight).</summary>
    public float Level = 1, Trail = 1, Shield, Pulse;
    public string Number = "";
    public readonly LampState State = new();
    /// <summary>The lamp on the HUD now (the shots' --pool-ab hides its pool for a second picture).</summary>
    public static LifeLamp? Live;
    /// <summary>The pool held off (the shots' --pool-ab second picture).</summary>
    public static bool PoolHeld;

    readonly ShaderMaterial mat;
    readonly Vessel.Flow flow;
    readonly Figure figure;
    /// <summary>The flame's light on the ground (GameHud adds it under everything else on the HUD).</summary>
    public readonly Control Pool;
    readonly ShaderMaterial poolMat;
    readonly BackBufferCopy copy;
    string drawnNumber = "";
    static readonly StringName UFlame = "flame", UGutter = "gutter", UOut = "out_t", UFlick = "flick", UGlow = "glow", UGain = "gain";
    float sFlame = -1, sGutter = -1, sOut = -2, sFlick = -1, sGlow = -1, sGain = -1;

    public LifeLamp()
    {
        MouseFilter = MouseFilterEnum.Ignore;
        Size = Canvas;
        PivotOffset = new Vector2(Canvas.X / 2, FootY);
        mat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/hud_lamp.gdshader") };
        foreach (var (u, f) in new[] { ("lit", "lamp_lit"), ("cold", "lamp_cold"), ("mask", "lamp_mask"), ("flame_tex", "lamp_flame") })
            if (UiArt.Tex($"lamp_life/{f}.png", false) is { } t) mat.SetShaderParameter(u, t);
            else GD.PushError($"LifeLamp: lamp_life/{f}.png did not load (unimported?): the lamp draws wrong");
        mat.SetShaderParameter("canvas", Canvas);
        mat.SetShaderParameter("wick", Wick);
        mat.SetShaderParameter("oil_top", OilTop);
        mat.SetShaderParameter("oil_bot", OilBot);
        mat.SetShaderParameter("font_x", FontX);
        mat.SetShaderParameter("flame_full", FlameFull);
        if (noOil) mat.SetShaderParameter("oil_off", 1);
        AddChild(new ColorRect { Material = mat, MouseFilter = MouseFilterEnum.Ignore, Size = Canvas });
        flow = new Vessel.Flow(mat, true);
        figure = new Figure(this);
        AddChild(figure);
        // the pool: a copy of the world under its rect only, then the quad that lifts it
        Pool = new Control { MouseFilter = MouseFilterEnum.Ignore, Visible = false };
        // (Godot 4.5 takes the copy's rect in the canvas's own coordinates, not the node's: it is set where the
        // pool stands, in PoolTick; a local rect copied the screen's top left and the pool read black)
        Pool.AddChild(copy = new BackBufferCopy { CopyMode = BackBufferCopy.CopyModeEnum.Rect, Rect = new Rect2(Vector2.Zero, PoolRect.Size) });
        poolMat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/hud_lamp_pool.gdshader") };
        poolMat.SetShaderParameter("size", PoolRect.Size);
        poolMat.SetShaderParameter("centre", new Vector2(Canvas.X / 2, FootY - 30) - PoolRect.Position);
        Pool.AddChild(new ColorRect { Material = poolMat, MouseFilter = MouseFilterEnum.Ignore, Size = PoolRect.Size });
    }

    public override void _Process(double delta)
    {
        using var _ = new Perf.Span(Perf.Part.Hud);
        float dt = Math.Min((float)delta, 0.1f);
        flow.Tick(dt, Level, Shield, Pulse > 0);
        State.Tick(flow.Shown, dt, Time.GetTicksMsec() / 1000.0);
        Send(UFlame, State.Flame, ref sFlame);
        Send(UGutter, State.Gutter, ref sGutter);
        Send(UOut, State.OutT, ref sOut);
        Send(UFlick, State.Flick, ref sFlick);
        Send(UGlow, State.Light, ref sGlow);
        if (Number != drawnNumber) { drawnNumber = Number; figure.QueueRedraw(); }
        PoolTick();
    }

    public override void _EnterTree() => Live = this;
    public override void _ExitTree() { if (Live == this) Live = null; }

    void Send(StringName u, float v, ref float sent) => Send(u, v, ref sent, mat);

    /// <summary>The pool follows the lamp: where it stands on the screen, shown only while the lamp is (the HUD
    /// hidden, it goes), its gain the flame's light and the lamp's fade.</summary>
    void PoolTick()
    {
        float gain = PoolGain * State.Light * Modulate.A * (IsVisibleInTree() ? 1 : 0);
        bool want = !noPool && !PoolHeld && gain > 0.0005f;
        if (Pool.Visible != want) Pool.Visible = want;
        if (!want) return;
        var at = GetGlobalTransformWithCanvas() * PoolRect.Position;
        if (Pool.Position != at) { Pool.Position = at; copy.Rect = new Rect2(at, PoolRect.Size); }
        Send(UGain, gain, ref sGain, poolMat);
    }

    void Send(StringName u, float v, ref float sent, ShaderMaterial m)
    {
        if (v == sent) return;
        sent = v;
        m.SetShaderParameter(u, v);
    }

    /// <summary>Her life's number on the lamp's foot (round 2: on the font's middle it hid the level): Alegreya
    /// Sans 800, lining tabular figures, bone on a dark halo, with the shared soft shadow (0, 2, 4 px).</summary>
    sealed partial class Figure : Control
    {
        readonly LifeLamp l;
        public Figure(LifeLamp l) { this.l = l; MouseFilter = MouseFilterEnum.Ignore; Size = Canvas; }

        public override void _Draw()
        {
            if (l.Number == "") return;
            var f = Vessel.Figures;
            const int fs = 27;
            var ts = f.GetStringSize(l.Number, HorizontalAlignment.Left, -1, fs);
            // (the figures stand 0.596 em tall on the baseline: their middle 0.293 em above it)
            var at = new Vector2(Mathf.Round(FontMid.X - ts.X / 2), Mathf.Round(NumberY + 0.293f * fs));
            var sh = at + new Vector2(0, 2);
            DrawStringOutline(f, sh, l.Number, HorizontalAlignment.Left, -1, fs, 10, new Color(0, 0, 0, 0.18f));
            DrawStringOutline(f, at, l.Number, HorizontalAlignment.Left, -1, fs, 7, new Color(0.04f, 0.01f, 0.01f, 0.45f));
            DrawStringOutline(f, at, l.Number, HorizontalAlignment.Left, -1, fs, 4, new Color(0.03f, 0.0f, 0.0f, 0.75f));
            DrawString(f, sh, l.Number, HorizontalAlignment.Left, -1, fs, new Color(0, 0, 0, 0.45f));
            DrawString(f, at, l.Number, HorizontalAlignment.Left, -1, fs, Vessel.Bone);
        }
    }
}
