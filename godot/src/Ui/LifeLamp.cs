using System;
using Godot;
using SurvivorUnchained.Play;

namespace SurvivorUnchained.Ui;

/// <summary>HUD A2 "Lamps Are Lit" (the owner's pick, 26 October): her life is an oil lamp on the left of the
/// instrument, in place of the life vessel and its cuff. One quad and one shader (shaders/hud_lamp.gdshader)
/// over the painted lamp (art/ui/lamp_life, tools/uiforge/lamp_life_cut.py): the oil in its font is her life
/// (Vessel.Flow's motion: the damped slosh, the hurt film, the heal, the heartbeat at 30% and under, the
/// shield's frost); the flame on its wick is her life too (LampState: tall, smaller, guttering, out with
/// smoke, relit). Its light falls on the ground under it: one OmniLight3D, no shadows, placed each frame on
/// her ground plane under the lamp's spot on the screen, its energy her flame's, off when the HUD is hidden.
/// The number (bone on a dark halo) redraws only when it changes.</summary>
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
    /// <summary>Her ground's height under the lamp's spot (set by the game each frame: her feet's).</summary>
    public static float GroundY;
    static readonly bool noLight = Args.Has("no-lamp-light");

    /// <summary>The level and the shield (0..1 of her life), the trail (unused: the hurt film is the oil's own),
    /// and Pulse: 1 where her heartbeat may sound (the fight).</summary>
    public float Level = 1, Trail = 1, Shield, Pulse;
    public string Number = "";
    public readonly LampState State = new();

    readonly ShaderMaterial mat;
    readonly Vessel.Flow flow;
    readonly Figure figure;
    OmniLight3D? light;
    string drawnNumber = "";
    static readonly StringName UFlame = "flame", UGutter = "gutter", UOut = "out_t", UFlick = "flick";
    float sFlame = -1, sGutter = -1, sOut = -2, sFlick = -1;

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
        AddChild(new ColorRect { Material = mat, MouseFilter = MouseFilterEnum.Ignore, Size = Canvas });
        flow = new Vessel.Flow(mat, true);
        figure = new Figure(this);
        AddChild(figure);
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
        if (Number != drawnNumber) { drawnNumber = Number; figure.QueueRedraw(); }
        Ground();
    }

    void Send(StringName u, float v, ref float sent)
    {
        if (v == sent) return;
        sent = v;
        mat.SetShaderParameter(u, v);
    }

    /// <summary>The flame's light on the ground: a real light (an overlay reads as a smudge once the camera
    /// moves), warm, no shadows, on her ground under the lamp's spot; small by day, plain by night.</summary>
    void Ground()
    {
        var cam = GetViewport()?.GetCamera3D();
        bool want = !noLight && cam != null && IsVisibleInTree() && State.Light > 0.001f;
        if (!want)
        {
            if (light != null && GodotObject.IsInstanceValid(light)) light.Visible = false;
            return;
        }
        if (light == null || !GodotObject.IsInstanceValid(light))
        {
            light = new OmniLight3D { LightColor = new Color("#ffb060"), ShadowEnabled = false, OmniAttenuation = 1.5f, LightSpecular = 0.25f, Visible = false };
            cam!.GetViewport().CallDeferred(Node.MethodName.AddChild, light);
            return;
        }
        if (!light.IsInsideTree()) return;
        // the lamp's foot on the screen (the HUD's 1920 by 1080 is the viewport's, stretched as canvas items)
        var spot = GetGlobalTransformWithCanvas() * new Vector2(Canvas.X / 2, FootY - 30);
        var o = cam!.ProjectRayOrigin(spot);
        var d = cam.ProjectRayNormal(spot);
        if (Math.Abs(d.Y) < 1e-3f) { light.Visible = false; return; }
        float k = (GroundY - o.Y) / d.Y;
        if (k <= 0) { light.Visible = false; return; }
        var hit = o + d * k;
        float l = State.Light;
        light.GlobalPosition = hit + new Vector3(0, 0.9f, 0);
        light.LightEnergy = 2.2f * l * Modulate.A;
        light.OmniRange = 3.6f + 3.0f * Math.Min(1, l);
        light.Visible = true;
    }

    public override void _ExitTree()
    {
        if (light != null && GodotObject.IsInstanceValid(light)) light.QueueFree();
        light = null;
    }

    /// <summary>Her life's number on the font: Alegreya Sans 800, lining tabular figures, bone on a dark halo
    /// (it reads on the full oil and the empty glass alike), with the shared soft shadow (0, 2, 4 px).</summary>
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
            var at = new Vector2(Mathf.Round(FontMid.X - ts.X / 2), Mathf.Round(FontMid.Y + 0.293f * fs));
            var sh = at + new Vector2(0, 2);
            DrawStringOutline(f, sh, l.Number, HorizontalAlignment.Left, -1, fs, 10, new Color(0, 0, 0, 0.18f));
            DrawStringOutline(f, at, l.Number, HorizontalAlignment.Left, -1, fs, 7, new Color(0.04f, 0.01f, 0.01f, 0.45f));
            DrawStringOutline(f, at, l.Number, HorizontalAlignment.Left, -1, fs, 4, new Color(0.03f, 0.0f, 0.0f, 0.75f));
            DrawString(f, sh, l.Number, HorizontalAlignment.Left, -1, fs, new Color(0, 0, 0, 0.45f));
            DrawString(f, at, l.Number, HorizontalAlignment.Left, -1, fs, Vessel.Bone);
        }
    }
}
