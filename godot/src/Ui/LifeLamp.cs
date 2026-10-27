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
    /// <summary>UI 15: the lamp's shape (--lamp-shape squat|tall|globe|font; squat until the owner picks): its art
    /// in art/ui/lamp_life (squat) or art/ui/lamp_life/&lt;shape&gt;/, cut by tools/uiforge/lamp_life_cut.py, and
    /// every place below from that folder's lamp_geo.json, read once.</summary>
    public static readonly string Shape = Args.Get("lamp-shape") is "tall" or "globe" or "font" ? Args.Get("lamp-shape")! : "squat";
    /// <summary>UI 16 (the owner: "the typical orbs that these games have, but lets have what they are encased in
    /// show our themes"): her life as a classic orb in a themed casing (--life-orb link|ring|waystone|linkk|ember|lamp; none until the
    /// owner picks): shaders/hud_orb.gdshader over art/ui/lamp_life/&lt;theme&gt;/ (lamp_life_cut.py's ORBS). No
    /// pool on the ground; the low-life edge pulse (HerLight.Edge) runs with it.</summary>
    public static readonly string? Orb = Args.Get("hud") == "drowned" ? "drowned" : Args.Get("life-orb") is "link" or "linkk" or "ring" or "waystone" or "ember" or "lamp" ? Args.Get("life-orb") : null;
    /// <summary>UI 16, the owner's pick of the whole-HUD directions: The Drowned Girl (--hud drowned), piece 1. Her
    /// bronze figure (art/ui/lamp_life/drowned, tools/uiforge/dg_figure_cut.py) cradles the life orb at her lips at
    /// the bar's left end; the orb is its own shader (dg2: shaders/hud_dg_orb.gdshader, the glass over her palm, her
    /// fingers up its far side over it, the screen behind it seen through its empty part: OrbCopy). The survivor, an
    /// elite or a marked attack behind her figure fades it (never the glass, her hand or her forearm): Behind.</summary>
    public static bool Drowned => Orb == "drowned";
    static readonly string Dir = Orb != null ? $"lamp_life/{Orb}" : Shape == "squat" ? "lamp_life" : $"lamp_life/{Shape}";
    static readonly Godot.Collections.Dictionary Geo = LoadGeo();
    /// <summary>UI 16 ring: the front half of the casing's welded eye (lamp_front.png, the quad's size), drawn over
    /// the chain so its first link runs through the eye; null where the casing has none.</summary>
    public static Texture2D? Front => Orb != null && !Drowned ? UiArt.Tex($"{Dir}/lamp_front.png") : null;
    /// <summary>The quad, in 1080 px (the art is twice this).</summary>
    public static readonly Vector2 Canvas = V("canvas");
    /// <summary>The lamp's foot in the quad, the eye on its font's right side (the chain leaves from it), the
    /// font's middle (the number) and the wick.</summary>
    public static readonly float FootY = F("foot");
    public static readonly Vector2 Eye = V("eye"), FontMid = V("font_mid"), Wick = V("wick");
    /// <summary>The oil's top and foot rows, the font's sides, and the flame's height at full: its tip and the
    /// lamp's top stay under the top line (squat: 904, the old cuff's top; the UI 15 shapes: 900).</summary>
    public static readonly float OilTop = F("oil_top"), OilBot = F("oil_bot"), FlameFull = F("flame_full");
    public static readonly Vector2 FontX = V("font_x");
    /// <summary>An iron band across the glass (its rows in the quad; zero: none): the level jumps it.</summary>
    public static readonly Vector2 Skip = V("skip");
    /// <summary>Where its foot stands on the screen (squat: the old life cuff's foot, 28 px clear of the edge;
    /// the UI 15 shapes 16 px clear), and the top line nothing of it crosses.</summary>
    public static readonly float Floor = F("floor"), TopLine = F("top_line");
    /// <summary>Where the number stands: its middle on the lamp's foot, under the font.</summary>
    public static readonly float NumberY = F("number_y");
    /// <summary>The pool's quad round the lamp's foot (1080 px, from the lamp's quad's top left) and its gain at
    /// full light (the scene's brightness lifted by about +45% at its heart: the warm tint takes a share).</summary>
    /// <summary>The Drowned Girl: her quad's top left on the 1080 screen (geo "at"), and the part of her above the
    /// bar line (geo "fade", in the quad) that fades when something is behind it.</summary>
    public static readonly Vector2 At = V("at");
    public static readonly Rect2 FadeLocal = new(V("fade_at"), V("fade_size"));
    public static readonly Rect2 PoolRect = new(Canvas.X / 2 - 240, FootY - 272, 480, 300);
    public const float PoolGain = 0.54f;
    static readonly bool noPool = Args.Has("no-lamp-pool"), noOil = Args.Has("lamp-no-oil");

    static Godot.Collections.Dictionary LoadGeo()
    {
        string path = $"res://art/ui/{Dir}/lamp_geo.json";
        if (FileAccess.FileExists(path) && Json.ParseString(FileAccess.GetFileAsString(path)).AsGodotDictionary() is { Count: > 0 } d)
            return d;
        GD.PushError($"LifeLamp: {path} did not load: the lamp draws wrong");
        return new Godot.Collections.Dictionary();
    }
    static float F(string k) => Geo.TryGetValue(k, out var v) ? (float)v.AsDouble() : 0;
    static Vector2 V(string k) => Geo.TryGetValue(k, out var v) && v.AsGodotArray() is { Count: 2 } a
        ? new Vector2((float)a[0].AsDouble(), (float)a[1].AsDouble()) : Vector2.Zero;

    /// <summary>The level and the shield (0..1 of her life), the trail (unused: the hurt film is the oil's own),
    /// and Pulse: 1 where her heartbeat may sound (the fight).</summary>
    public float Level = 1, Trail = 1, Shield, Pulse;
    /// <summary>The Drowned Girl: the survivor, an elite or a marked attack behind her figure (Game sets it each
    /// frame): the figure fades to FadeTo over FadeTime, holds FadeHold after the last frame something was behind
    /// it (no flicker as a crowd mills past), and comes back over FadeBack. Her hand and forearm fade with her (ui17
    /// A, the judge: held solid while she faded, they read as pasted on); the glass stays. (dg1 faded to 35% for any
    /// foe: in a horde that was the normal state, a murky ghost.)</summary>
    public bool Behind;
    public const float FadeTo = 0.55f, FadeTime = 0.25f, FadeBack = 0.4f, FadeHold = 0.8f;
    float figA = 1, sFigA = -1, clearFor = 99;
    bool wasBehind, liveShot;
    /// <summary>The Drowned Girl's orb: its rect (the glass and the refraction's reach) copied from the screen
    /// before the quad draws, so the empty glass shows what is behind it (the copy's rect is in the canvas's own
    /// coordinates: set where the orb stands, in OrbCopy).</summary>
    readonly BackBufferCopy? orbCopy;
    Rect2 orbCopied;
    static readonly Vector2 OrbC = V("orb_c");
    static readonly float OrbR = F("orb_r");
    /// <summary>The number on the orb (the Drowned Girl): the area titles' serif, cream on a dark halo.</summary>
    public static readonly Color Cream = new("#f3e7cc");
    static readonly StringName UFigA = "fig_a";
    /// <summary>The faded part's rect on the HUD (1080 px).</summary>
    public Rect2 FadeRect => new(Position + FadeLocal.Position, FadeLocal.Size);
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
    readonly BackBufferCopy? copy;
    string drawnNumber = "";
    static readonly StringName UFlame = "flame", UGutter = "gutter", UOut = "out_t", UFlick = "flick", UGlow = "glow", UGain = "gain";
    float sFlame = -1, sGutter = -1, sOut = -2, sFlick = -1, sGlow = -1, sGain = -1;

    public LifeLamp()
    {
        MouseFilter = MouseFilterEnum.Ignore;
        Size = Canvas;
        PivotOffset = new Vector2(Canvas.X / 2, FootY);
        mat = new ShaderMaterial { Shader = GD.Load<Shader>(Drowned ? "res://shaders/hud_dg_orb.gdshader" : Orb != null ? "res://shaders/hud_orb.gdshader" : "res://shaders/hud_lamp.gdshader") };
        foreach (var (u, f) in new[] { ("lit", "lamp_lit"), ("cold", "lamp_cold"), ("mask", "lamp_mask"), ("flame_tex", "lamp_flame") })
            if (Orb != null && Orb != "lamp" && f == "lamp_flame" || Drowned && f is not ("lamp_cold" or "lamp_mask")) continue;
            else if (UiArt.Tex($"{Dir}/{f}.png", false) is { } t) mat.SetShaderParameter(u, t);
            else GD.PushError($"LifeLamp: {Dir}/{f}.png did not load (unimported?): the lamp draws wrong");
        mat.SetShaderParameter("canvas", Canvas);
        if (Orb != null)
        {
            mat.SetShaderParameter("theme", Orb switch { "ember" => 1, "lamp" => 2, "drowned" => 3, _ => 0 });
            if (Geo.ContainsKey("level_foot")) mat.SetShaderParameter("level_foot", F("level_foot"));
            mat.SetShaderParameter("orb_c", V("orb_c"));
            mat.SetShaderParameter("orb_r", F("orb_r"));
            mat.SetShaderParameter("orb_vis", F("orb_vis"));
            if (Drowned) mat.SetShaderParameter("scr_at", At);
        }
        mat.SetShaderParameter("wick", Wick);
        mat.SetShaderParameter("oil_top", OilTop);
        mat.SetShaderParameter("oil_bot", OilBot);
        mat.SetShaderParameter("font_x", FontX);
        mat.SetShaderParameter("flame_full", FlameFull);
        mat.SetShaderParameter("flame_aspect", F("flame_aspect"));
        mat.SetShaderParameter("chim_top", F("chim_top"));
        mat.SetShaderParameter("skip", Skip);
        mat.SetShaderParameter("halo_row", TopLine - (Floor - FootY));
        if (noOil) mat.SetShaderParameter("oil_off", 1);
        if (Drowned) AddChild(orbCopy = new BackBufferCopy { CopyMode = BackBufferCopy.CopyModeEnum.Rect, Rect = new Rect2(0, 0, 1, 1) });
        AddChild(new ColorRect { Material = mat, MouseFilter = MouseFilterEnum.Ignore, Size = Canvas });
        flow = new Vessel.Flow(mat, true);
        figure = new Figure(this);
        AddChild(figure);
        // the pool: a copy of the world under its rect only, then the quad that lifts it
        Pool = new Control { MouseFilter = MouseFilterEnum.Ignore, Visible = false };
        // (Godot 4.5 takes the copy's rect in the canvas's own coordinates, not the node's: it is set where the
        // pool stands, in PoolTick; a local rect copied the screen's top left and the pool read black)
        // (orb modes never show the pool: no copy, no quad built)
        if (Orb == null) Pool.AddChild(copy = new BackBufferCopy { CopyMode = BackBufferCopy.CopyModeEnum.Rect, Rect = new Rect2(Vector2.Zero, PoolRect.Size) });
        poolMat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/hud_lamp_pool.gdshader") };
        poolMat.SetShaderParameter("size", PoolRect.Size);
        poolMat.SetShaderParameter("centre", new Vector2(Canvas.X / 2, FootY - 30) - PoolRect.Position);
        if (Orb == null) Pool.AddChild(new ColorRect { Material = poolMat, MouseFilter = MouseFilterEnum.Ignore, Size = PoolRect.Size });
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
        if (Drowned)
        {
            clearFor = Behind ? 0 : clearFor + dt;
            bool dim = clearFor < FadeHold;
            figA = Mathf.MoveToward(figA, dim ? FadeTo : 1, dt * (1 - FadeTo) / (dim ? FadeTime : FadeBack));
            if (Behind != wasBehind && Args.Has("shot")) GD.Print($"dg fade {(Behind ? "on" : "off")} at {Time.GetTicksMsec() / 1000.0:0.00}");
            wasBehind = Behind;
            Send(UFigA, figA, ref sFigA);
            OrbCopy();
            // (dg3, the judge: the fade shown working live: with --shot, the first frame a real trigger (not
            // HudPin's behind=1) has taken her to FadeTo is saved as SHOT_livefade.png)
            if (!liveShot && Behind && HudPin.Behind != true && figA <= FadeTo + 0.02f && Args.Get("shot") is { } sn)
            {
                liveShot = true;
                GetViewport().GetTexture().GetImage().SavePng(ProjectSettings.GlobalizePath($"res://.shots/{sn}_livefade.png"));
                GD.Print($"dg live fade shot at {Time.GetTicksMsec() / 1000.0:0.00}");
            }
        }
        if (Number != drawnNumber) { drawnNumber = Number; figure.QueueRedraw(); }
        PoolTick();
    }

    public override void _EnterTree() => Live = this;
    public override void _ExitTree() { if (Live == this) Live = null; }

    void Send(StringName u, float v, ref float sent) => Send(u, v, ref sent, mat);

    /// <summary>The orb's copy of the screen: the glass and 16 px round it (the refraction's reach), where the orb
    /// stands now.</summary>
    void OrbCopy()
    {
        if (orbCopy == null) return;
        var xf = GetGlobalTransformWithCanvas();
        float m = OrbR + 16;
        var at = new Rect2(xf * (OrbC - new Vector2(m, m)), xf.BasisXform(new Vector2(2 * m, 2 * m)).Abs());
        if (at != orbCopied) { orbCopied = at; orbCopy.Rect = at; }
    }

    /// <summary>The pool follows the lamp: where it stands on the screen, shown only while the lamp is (the HUD
    /// hidden, it goes), its gain the flame's light and the lamp's fade.</summary>
    void PoolTick()
    {
        float gain = PoolGain * State.Light * Modulate.A * (IsVisibleInTree() ? 1 : 0);
        bool want = !noPool && Orb == null && !PoolHeld && gain > 0.0005f;
        if (Pool.Visible != want) Pool.Visible = want;
        if (!want) return;
        var at = GetGlobalTransformWithCanvas() * PoolRect.Position;
        if (Pool.Position != at) { Pool.Position = at; if (copy != null) copy.Rect = new Rect2(at, PoolRect.Size); }
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
            if (Drowned)
            {
                // (dg2, the judge: the area titles' serif, Cinzel 700, cream on a dark garnet halo; its lining
                // figures stand 0.714 em tall on the baseline, their middle 0.357 em above it)
                var d = Style.Display;
                const int ds = 26;
                var dsz = d.GetStringSize(l.Number, HorizontalAlignment.Left, -1, ds);
                var dat = new Vector2(Mathf.Round(FontMid.X - dsz.X / 2), Mathf.Round(NumberY + 0.357f * ds));
                var dsh = dat + new Vector2(0, 2);
                DrawStringOutline(d, dsh, l.Number, HorizontalAlignment.Left, -1, ds, 10, new Color(0, 0, 0, 0.20f));
                DrawStringOutline(d, dat, l.Number, HorizontalAlignment.Left, -1, ds, 7, new Color(0.05f, 0.006f, 0.012f, 0.42f));
                DrawStringOutline(d, dat, l.Number, HorizontalAlignment.Left, -1, ds, 4, new Color(0.04f, 0.004f, 0.01f, 0.80f));
                DrawString(d, dsh, l.Number, HorizontalAlignment.Left, -1, ds, new Color(0, 0, 0, 0.40f));
                DrawString(d, dat, l.Number, HorizontalAlignment.Left, -1, ds, Cream);
                return;
            }
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
