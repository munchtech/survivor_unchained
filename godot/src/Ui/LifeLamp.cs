using System;
using Godot;

namespace SurvivorUnchained.Ui;

/// <summary>The Drowned Girl HUD (UI 16-18, the owner's pick; the game's HUD since UI 18), her life: her bronze figure
/// (art/ui/lamp_life/drowned, tools/uiforge/dg_figure_cut.py) cradles the life orb at her lips at the bar's left end.
/// One quad and one shader (shaders/hud_dg_orb.gdshader): the glass over her palm, her fingers up its far side over
/// it, the screen behind it seen through its empty part (OrbCopy), the blood in it her life (Vessel.Flow's motion:
/// the damped slosh, the hurt film, the heal, the heartbeat at 30% and under, the shield's frost). The survivor, an
/// elite or a marked attack behind her figure fades it (never the glass): Behind. The number (the area titles'
/// serif, cream on a dark halo) stands on the orb; it redraws only when it changes. Every place comes from the
/// folder's lamp_geo.json, read once.</summary>
public partial class LifeLamp : Control
{
    const string Dir = "lamp_life/drowned";
    static readonly Godot.Collections.Dictionary Geo = LoadGeo();
    /// <summary>The quad, in 1080 px (the art is twice this).</summary>
    public static readonly Vector2 Canvas = V("canvas");
    /// <summary>The orb's middle in the quad (the number) and the number's height.</summary>
    public static readonly Vector2 FontMid = V("font_mid");
    public static readonly float NumberY = F("number_y");
    /// <summary>Her quad's top left on the 1080 screen (geo "at"), and the part of her above the bar line (geo
    /// "fade", in the quad) that fades when something is behind it.</summary>
    public static readonly Vector2 At = V("at");
    public static readonly Rect2 FadeLocal = new(V("fade_at"), V("fade_size"));

    static Godot.Collections.Dictionary LoadGeo()
    {
        string path = $"res://art/ui/{Dir}/lamp_geo.json";
        if (FileAccess.FileExists(path) && Json.ParseString(FileAccess.GetFileAsString(path)).AsGodotDictionary() is { Count: > 0 } d)
            return d;
        GD.PushError($"LifeLamp: {path} did not load: her figure draws wrong");
        return new Godot.Collections.Dictionary();
    }
    static float F(string k) => Geo.TryGetValue(k, out var v) ? (float)v.AsDouble() : 0;
    static Vector2 V(string k) => Geo.TryGetValue(k, out var v) && v.AsGodotArray() is { Count: 2 } a
        ? new Vector2((float)a[0].AsDouble(), (float)a[1].AsDouble()) : Vector2.Zero;

    /// <summary>The level and the shield (0..1 of her life), the trail (unused: the hurt film is the blood's own),
    /// and Pulse: 1 where her heartbeat may sound (the fight).</summary>
    public float Level = 1, Trail = 1, Shield, Pulse;
    /// <summary>The survivor, an elite or a marked attack behind her figure (Game sets it each frame): the figure
    /// fades to FadeTo over FadeTime, holds FadeHold after the last frame something was behind it (no flicker as a
    /// crowd mills past), and comes back over FadeBack. Her hand and forearm fade with her (ui17 A, the judge: held
    /// solid while she faded, they read as pasted on); the glass stays. (dg1 faded to 35% for any foe: in a horde
    /// that was the normal state, a murky ghost.)</summary>
    public bool Behind;
    public const float FadeTo = 0.55f, FadeTime = 0.25f, FadeBack = 0.4f, FadeHold = 0.8f;
    float figA = 1, sFigA = -1, clearFor = 99;
    bool wasBehind, liveShot;
    /// <summary>The orb: its rect (the glass and the refraction's reach) copied from the screen before the quad
    /// draws, so the empty glass shows what is behind it (the copy's rect is in the canvas's own coordinates: set
    /// where the orb stands, in OrbCopy).</summary>
    readonly BackBufferCopy orbCopy;
    Rect2 orbCopied;
    static readonly Vector2 OrbC = V("orb_c");
    static readonly float OrbR = F("orb_r");
    /// <summary>The number on the orb: the area titles' serif, cream on a dark halo.</summary>
    public static readonly Color Cream = new("#f3e7cc");
    static readonly StringName UFigA = "fig_a";
    /// <summary>The faded part's rect on the HUD (1080 px).</summary>
    public Rect2 FadeRect => new(Position + FadeLocal.Position * Scale, FadeLocal.Size * Scale);
    public string Number = "";
    /// <summary>Her figure on the HUD now.</summary>
    public static LifeLamp? Live;

    readonly ShaderMaterial mat;
    /// <summary>Her figure's shader.</summary>
    public ShaderMaterial Mat => mat;
    readonly Vessel.Flow flow;
    readonly Figure figure;
    string drawnNumber = "";

    public LifeLamp()
    {
        MouseFilter = MouseFilterEnum.Ignore;
        Size = Canvas;
        mat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/hud_dg_orb.gdshader") };
        foreach (var (u, f) in new[] { ("cold", "lamp_cold"), ("mask", "lamp_mask") })
            if (UiArt.Tex($"{Dir}/{f}.png", false) is { } t) mat.SetShaderParameter(u, t);
            else GD.PushError($"LifeLamp: {Dir}/{f}.png did not load (unimported?): her figure draws wrong");
        mat.SetShaderParameter("canvas", Canvas);
        if (Geo.ContainsKey("level_foot")) mat.SetShaderParameter("level_foot", F("level_foot"));
        mat.SetShaderParameter("orb_c", OrbC);
        mat.SetShaderParameter("orb_r", OrbR);
        mat.SetShaderParameter("orb_vis", F("orb_vis"));
        mat.SetShaderParameter("scr_at", At);
        AddChild(orbCopy = new BackBufferCopy { CopyMode = BackBufferCopy.CopyModeEnum.Rect, Rect = new Rect2(0, 0, 1, 1) });
        AddChild(new ColorRect { Material = mat, MouseFilter = MouseFilterEnum.Ignore, Size = Canvas });
        if (UiArt.Tex("dg_river/xp_light.png", false) is { } hm) mat.SetShaderParameter("hair_mask", hm);
        else GD.PushError("LifeLamp: dg_river/xp_light.png did not load: her hair's shine draws blank");
        var hg = HairGeo();
        mat.SetShaderParameter("hair_at", hg.At);
        mat.SetShaderParameter("hair_size", hg.Size);
        flow = new Vessel.Flow(mat, true);
        figure = new Figure(this);
        AddChild(figure);
    }

    /// <summary>UI 23 (HUD A): her group drawn at s about its outer bottom corner (the geo's group_anchor): her place
    /// and her shader's screen (the sheen's and the shine's run are in screen px; her masks stay in her own).</summary>
    public void Group(Vector2 anchor, float s)
    {
        Scale = new Vector2(s, s);
        Position = anchor + (At - anchor) * s;
        mat.SetShaderParameter("grp_anchor", anchor);
        mat.SetShaderParameter("grp_scale", s);
    }

    /// <summary>The hair mask's rect in her unscaled coordinates (dg_river/xp_light.json).</summary>
    static (Vector2 At, Vector2 Size) HairGeo()
    {
        const string path = UiArt.Root + "dg_river/xp_light.json";
        if (FileAccess.FileExists(path) && Json.ParseString(FileAccess.GetFileAsString(path)).AsGodotDictionary() is { Count: > 0 } d
            && d.TryGetValue("at", out var a) && a.AsGodotArray() is { Count: 2 } aa && d.TryGetValue("size", out var z) && z.AsGodotArray() is { Count: 2 } zz)
            return (new Vector2((float)aa[0].AsDouble(), (float)aa[1].AsDouble()), new Vector2((float)zz[0].AsDouble(), (float)zz[1].AsDouble()));
        GD.PushError($"LifeLamp: {path} did not load: her hair's shine runs wrong");
        return (new Vector2(295, 822), new Vector2(1310, 258));
    }

    /* ---- UI 23: the shine down her hair (decoration, never the experience) ---- */
    double shineT = 2;
    float sFront = float.NaN, sK = -1, sSheen = -1;
    int sDay = -1;
    static readonly StringName UShineFront = "shine_front", UShineK = "shine_k", UShineC = "shine_c", USheen = "sheen_on";
    /// <summary>The shine's front and strength now: from ShineFrom to ShineTo (hud.json xpRing) in ShineTravel seconds,
    /// once every ShinePeriod, fading over its last second past the end. A pin (--hud-pin shine=S) holds the front at S
    /// at full strength and the idle sheen off, as the judged mock's still frame.</summary>
    public static (float Front, float K) Shine(double t, Play.XpLight.RingLook k)
    {
        double u = t % k.ShinePeriod;
        if (u <= k.ShineTravel) return ((float)(k.ShineFrom + (k.ShineTo - k.ShineFrom) * (u / k.ShineTravel)), (float)Math.Min(1, u / 0.4));
        return ((float)k.ShineTo, (float)Math.Max(0, 1 - (u - k.ShineTravel)));
    }
    void ShineTick(double dt)
    {
        var (front, k) = HudPin.Shine is float ps ? (ps, 1f) : Shine(shineT += dt, Play.XpLight.RingLook.Game);
        float sheen = HudPin.Shine != null ? 0 : 1;
        if (k != sK) { sK = k; mat.SetShaderParameter(UShineK, k); }
        if (k > 0 && front != sFront) { sFront = front; mat.SetShaderParameter(UShineFront, front); }
        if (sheen != sSheen) { sSheen = sheen; mat.SetShaderParameter(USheen, sheen); }
        int day = Cuff.Day ? 1 : 0;
        if (day != sDay) { sDay = day; mat.SetShaderParameter(UShineC, day == 1 ? new Vector3(0.80f, 0.89f, 1.0f) : new Vector3(0.88f, 0.83f, 1.0f)); }
    }

    public override void _Process(double delta)
    {
        using var _ = new Perf.Span(Perf.Part.Hud);
        float dt = Math.Min((float)delta, 0.1f);
        flow.Tick(dt, Level, Shield, Pulse > 0);
        ShineTick(dt);
        clearFor = Behind ? 0 : clearFor + dt;
        bool dim = clearFor < FadeHold;
        figA = Mathf.MoveToward(figA, dim ? FadeTo : 1, dt * (1 - FadeTo) / (dim ? FadeTime : FadeBack));
        if (Behind != wasBehind && Args.Has("shot")) GD.Print($"dg fade {(Behind ? "on" : "off")} at {Time.GetTicksMsec() / 1000.0:0.00}");
        wasBehind = Behind;
        if (figA != sFigA) { sFigA = figA; mat.SetShaderParameter(UFigA, figA); }
        OrbCopy();
        // (dg3, the judge: the fade shown working live: with --shot, the first frame a real trigger (not HudPin's
        // behind=1) has taken her to FadeTo is saved as SHOT_livefade.png)
        if (!liveShot && Behind && HudPin.Behind != true && figA <= FadeTo + 0.02f && Args.Get("shot") is { } sn)
        {
            liveShot = true;
            GetViewport().GetTexture().GetImage().SavePng(ProjectSettings.GlobalizePath($"res://.shots/{sn}_livefade.png"));
            GD.Print($"dg live fade shot at {Time.GetTicksMsec() / 1000.0:0.00}");
        }
        if (Number != drawnNumber) { drawnNumber = Number; figure.QueueRedraw(); }
    }

    public override void _EnterTree() => Live = this;
    public override void _ExitTree() { if (Live == this) Live = null; }

    /// <summary>The orb's copy of the screen: the glass and 16 px round it (the refraction's reach), where the orb
    /// stands now.</summary>
    void OrbCopy()
    {
        var xf = GetGlobalTransformWithCanvas();
        float m = OrbR + 16;
        var at = new Rect2(xf * (OrbC - new Vector2(m, m)), xf.BasisXform(new Vector2(2 * m, 2 * m)).Abs());
        if (at != orbCopied) { orbCopied = at; orbCopy.Rect = at; }
    }

    /// <summary>Her life's number on the orb (dg2, the judge): the area titles' serif, Cinzel 700, cream on a dark
    /// garnet halo, with the shared soft shadow (0, 2 px).</summary>
    sealed partial class Figure : Control
    {
        readonly LifeLamp l;
        public Figure(LifeLamp l) { this.l = l; MouseFilter = MouseFilterEnum.Ignore; Size = Canvas; }

        public override void _Draw()
        {
            if (l.Number == "") return;
            // (Cinzel's lining figures stand 0.714 em tall on the baseline, their middle 0.357 em above it)
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
        }
    }
}
