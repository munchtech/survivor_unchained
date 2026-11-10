using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.World;

namespace SurvivorUnchained.View;

/// <summary>
/// Light, air and colour for a moment of the day, as the web game's
/// render/atmosphere.ts sets them from a preset (World/Atmospheres.cs): the
/// key light (moon or sun), the sky and what it lights (shaders/sky.gdshader
/// carries the web game's environment map and hemisphere light), the fog,
/// the exposure through AgX, bloom, and the colour grade (render/grade.ts,
/// baked into a lookup table Godot applies after tone mapping).
///
/// three.js and Godot count light differently: a three.js light of
/// intensity I lights a white surface facing it to I/pi, a Godot light of
/// energy E to E, so energies here are the web game's intensities over pi.
/// The fog is exp² in three.js and exp in Godot: the density is matched
/// where the fight is seen from, 60 m off.
/// </summary>
public partial class Atmosphere : Node3D
{
    public readonly Godot.Environment Env;
    public readonly DirectionalLight3D Key;
    readonly ShaderMaterial sky;
    public AtmospherePreset Current { get; private set; } = Atmospheres.Night;

    /// <summary>A cinematic's far haze (C03: the far ridge 27-33% darker than the sky over it, a cut-out): depth fog from
    /// Begin to End m (Curve its ramp), at most Amount, its colour the sky's behind it by Sky (aerial perspective), so
    /// distance pales toward the sky and near stays clear. Null: play's exponential fog. Kept across Set (a blend's tween).</summary>
    public (float Begin, float End, float Curve, float Amount, float Sky, Color? Tint)? Haze { get => haze; set { hazeFadeDur = 0; hazeScale = 1; fogScale = 1; haze = value; HazeApply(); } }
    (float Begin, float End, float Curve, float Amount, float Sky, Color? Tint)? haze;

    /// <summary>The haze let go over seconds rather than at once (the hand-back, H4 solver r2: C02's depth fog dropped
    /// 0.90 to play's 0.0038 in one frame, a 29% brightness pop): the depth haze thins to nothing over the first 70%
    /// (it carries nearly all the change), then play's own fog comes up from nothing over the rest. A new Haze set cancels it.</summary>
    public void FadeHaze(double seconds)
    {
        if (haze == null || hazeFadeDur > 0) return;   // (one running already carries on)
        if (seconds <= 0) { Haze = null; return; }
        hazeFadeT = 0; hazeFadeDur = seconds;
    }
    double hazeFadeT, hazeFadeDur;
    const double HazeShare = 0.7;
    float hazeScale = 1, fogScale = 1;
    static float Smooth(double k) { k = Math.Clamp(k, 0, 1); return (float)(k * k * (3 - 2 * k)); }
    void HazeFadeTick(double delta)
    {
        if (hazeFadeDur <= 0) return;
        hazeFadeT += delta;
        double k = hazeFadeT / hazeFadeDur;
        if (haze != null)
        {
            hazeScale = 1 - Smooth(k / HazeShare);
            if (k < HazeShare) { HazeApply(); return; }
            haze = null; hazeScale = 1; fogScale = 0;
            HazeApply();
        }
        fogScale = Smooth((k - HazeShare) / (1 - HazeShare));
        if (k >= 1) { fogScale = 1; hazeFadeDur = 0; }
        Env.FogDensity = (float)(Current.FogDensity * Current.FogDensity * FogMatchDistance) * fogScale;
    }

    void HazeApply()
    {
        if (haze is { } h)
        {
            Env.FogMode = Godot.Environment.FogModeEnum.Depth;
            Env.FogDepthBegin = h.Begin; Env.FogDepthEnd = h.End; Env.FogDepthCurve = h.Curve;
            Env.FogDensity = h.Amount * hazeScale; Env.FogAerialPerspective = h.Sky;
            if (h.Tint is Color tc) Env.FogLightColor = tc;
            // (--dbg-haze-tint #hex, --dbg-haze-sky, --dbg-haze-amount, --dbg-haze-begin/-end/-curve: A/B a cinematic haze cue without its data; Env 23)
            if (SurvivorUnchained.Args.Get("dbg-haze-tint") is string dt) Env.FogLightColor = new Color(dt);
            if (SurvivorUnchained.Args.Has("dbg-haze-sky")) Env.FogAerialPerspective = SurvivorUnchained.Args.Num("dbg-haze-sky", h.Sky);
            if (SurvivorUnchained.Args.Has("dbg-haze-amount")) Env.FogDensity = SurvivorUnchained.Args.Num("dbg-haze-amount", h.Amount);
            if (SurvivorUnchained.Args.Has("dbg-haze-begin")) Env.FogDepthBegin = SurvivorUnchained.Args.Num("dbg-haze-begin", h.Begin);
            if (SurvivorUnchained.Args.Has("dbg-haze-end")) Env.FogDepthEnd = SurvivorUnchained.Args.Num("dbg-haze-end", h.End);
            if (SurvivorUnchained.Args.Has("dbg-haze-curve")) Env.FogDepthCurve = SurvivorUnchained.Args.Num("dbg-haze-curve", h.Curve);
            if (System.Environment.GetEnvironmentVariable("FLORA_STATS") != null) GD.Print($"haze: depth {h.Begin}-{h.End} m, amount {h.Amount}, sky {h.Sky}; fog on {Env.FogEnabled}");
        }
        else if (Env.FogMode != Godot.Environment.FogModeEnum.Exponential)
        {
            Env.FogMode = Godot.Environment.FogModeEnum.Exponential; Env.FogAerialPerspective = 0;
            Env.FogLightColor = C(Current.FogColor);
            Env.FogDensity = (float)(Current.FogDensity * Current.FogDensity * FogMatchDistance) * fogScale;
        }
    }
    /// <summary>A touch less exposure at low quality keeps the mood (the web
    /// game's exposureScale).</summary>
    public float ExposureScale = 1;
    /// <summary>The eye stopping down after a Flare's BOOM (Fx/Flare/FlareFx.Dip): 1 none.</summary>
    public float FlareDip = 1;
    float dipShown = 1;
    /// <summary>The sun and the sky's ambient dipped under a Flare by day (Fx/Flare/FlareFx.LightDip, the Long Cut's sweep
    /// and cleave: its own light chain carries the frame): 1 none. Applied relative to what is set, so a cinematic's own
    /// say over the key and ambient keeps its share.</summary>
    public float FlareLight = 1;
    float lightShown = 1;
    /// <summary>How much colour the world keeps below the brights (0 all, 1
    /// none): the grade's worn world.</summary>
    public float Mute = 0.16f;
    /// <summary>Her carried light's gain under the air in force (AtmospherePreset.Ember).</summary>
    public static float EmberGain = 1;
    /// <summary>Her carried light's colour and reach under the air in force (AtmospherePreset.EmberColor/EmberReach; null: her own).</summary>
    public static Color? EmberColor;
    public static float EmberReach = 1;
    /// <summary>H2 R4 on (the foes at night; --crowd-r4 off: the r1_2 crowd). Before the crowd terms: their defaults read it
    /// (static fields start in the order written).</summary>
    static readonly bool R4 = SurvivorUnchained.Args.Get("crowd-r4") != "off";
    /// <summary>The preset's crowd light by night (CrowdFill; 0 by day). --crowd-fill off: none (Rendering 4's A/B);
    /// --crowd-moon K: the sky's fill on the crowd; --crowd-reach M: her lamp's reach on it (PlayerView: --crowd-ember K, --crowd-ember-h H).</summary>
    public static float CrowdFill;
    static readonly bool CrowdFillOn = SurvivorUnchained.Args.Get("crowd-fill") != "off";
    const float CrowdSkyRef = 2f;
    static readonly float CrowdMoonK = SurvivorUnchained.Args.Num("crowd-moon", R4 ? 0.3f : 0.45f), CrowdEmberRange = SurvivorUnchained.Args.Num("crowd-reach", 10f);
    /// <summary>Round 2 (vat.gdshaderinc crowd_night, crowd_top): --crowd-lift L the luminance the darkest paint is lifted to (it goes
    /// into ALBEDO, so the moon's shadowed light and the ambient light it); --crowd-flat K the cut on flat, up-facing low surfaces;
    /// --crowd-wrap W her lamp's wrap; --crowd-top K the cool on heads and shoulders; --crowd-dirt T the fill's hue from the sky's
    /// (0) to the ground's (1); --crowd-back B the moon's wrap round the body (BACKLIGHT, shadowed); --crowd-amb A the ambient it keeps (AO); --crowd-dbg the distance-band mask (measuring).</summary>
    /// <summary>Rendering 5 (the r2 judge's numbers, vat.gdshaderinc crowd_lamp2/3): her lamp on the crowd is whole within --crowd-full
    /// metres, then 1 / (1 + k d^2) (--crowd-k), gone at --crowd-zero (--crowd-curve old: the older smoothstep curve and cuts, for A/B);
    /// --crowd-rim the warm rim toward her; --crowd-near-r / --crowd-near-k the radius round her and the lamp's share on the crowd there;
    /// --crowd-dead the floor (a luminance) the dead are lifted to after their darkening. --crowd-top 0.1: the cool top halved.</summary>
    static readonly float CrowdK = SurvivorUnchained.Args.Num("crowd-k", 0.5f), CrowdFull = SurvivorUnchained.Args.Num("crowd-full", 2f), CrowdZero = SurvivorUnchained.Args.Get("crowd-curve") == "old" ? 0f : SurvivorUnchained.Args.Num("crowd-zero", 7f),
        CrowdRimK = SurvivorUnchained.Args.Num("crowd-rim", 0.13f), CrowdNearR = SurvivorUnchained.Args.Num("crowd-near-r", 1.5f), CrowdNearK = SurvivorUnchained.Args.Num("crowd-near-k", 0.17f), CrowdDead = SurvivorUnchained.Args.Num("crowd-dead", 0.03f);
    /// <summary>True unless --crowd-curve old: the Rendering 5 curve and cuts are on (the real lamp light then skips the crowd, PlayerView).</summary>
    public static bool CrowdCurveNew => SurvivorUnchained.Args.Get("crowd-curve") != "old";
    static readonly float CrowdLift = SurvivorUnchained.Args.Num("crowd-lift", 0.04f), CrowdFlat = SurvivorUnchained.Args.Num("crowd-flat", 0.8f),
        CrowdWrap = SurvivorUnchained.Args.Num("crowd-wrap", 0.3f), CrowdTopK = SurvivorUnchained.Args.Num("crowd-top", 0.1f), CrowdDirt = SurvivorUnchained.Args.Num("crowd-dirt", R4 ? 0.3f : 0.7f), CrowdBack = SurvivorUnchained.Args.Num("crowd-back", R4 ? 0.15f : 1f),
        CrowdAmb = SurvivorUnchained.Args.Num("crowd-amb", 0.25f);
    /// <summary>H2 R4 (vat.gdshaderinc crowd_r4, arena nights): --crowd-edge E the moon's and her lamp's rim as a tight edge from
    /// 1 - NdotV = E (0: the older pow 3); --crowd-spec S the crowd's specular; --crowd-grim G Godot's per-light rim (a scale); --crowd-card-edge K the fur cards' share of the edge;
    /// --crowd-edge-k K the moon rim's strength on the edge (a scale of the preset's);
    /// --crowd-r4 off: none of it (the r1_2 crowd exactly, for A/B and --perf).
    /// The defaults (the r4 judge's round 2): a soft edge from 0.5, whole by 0.92 (2-4 px on a body), the moon's rim there 2.5x the
    /// preset's (CrowdRim 0.2 x 2.5; its peak under her pool's), specular 0.15, no Godot rim, the fur cards 0.1 of the edge (they flecked); and
    /// (above) the moon's wrap round the body 1 to 0.15, the fill 0.45 to 0.3 and its hue 0.7 to 0.3 of the ground's, so a body
    /// out of her reach is a dark form lit only along its edge. Nothing here by day or off the arena (CrowdFill 0).</summary>
    static readonly float CrowdEdge = SurvivorUnchained.Args.Num("crowd-edge", 0.5f), CrowdSpec = SurvivorUnchained.Args.Num("crowd-spec", 0.15f),
        CrowdGRim = SurvivorUnchained.Args.Num("crowd-grim", 0f), CrowdCardEdge = SurvivorUnchained.Args.Num("crowd-card-edge", 0.1f),
        CrowdEdgeK = SurvivorUnchained.Args.Num("crowd-edge-k", 2.5f);
    static readonly float CrowdDbg = SurvivorUnchained.Args.Has("crowd-dbg-mode") ? SurvivorUnchained.Args.Num("crowd-dbg-mode", 3) : SurvivorUnchained.Args.Has("crowd-dbg") ? 3 : 0;
    /// <summary>(E9d) How lit the town is (0 by day, 1 at dawn, dusk and night): its lamps burn and some windows glow
    /// (ZoneView.Town, kit.gdshader's town_lit) from a low or a moonlit key.</summary>
    public static float TownLit = 1;
    /// <summary>The camera's own say over the exposure (1: none): the close view by night opens up, as an eye does
    /// on a face near it, so the wood behind her reads (GameCloseUp, E1).</summary>
    public float ViewExposure { get; private set; } = 1;
    /// <summary>The camera's say over the grade's highlight tint (0: the preset's; 1: none). The close view by night takes the
    /// near-white highlight tint off her face, which it left pale and waxy (E1 round 3); in quarter steps, each table made once.</summary>
    public float ViewHighlightsNeutral { get; private set; }
    /// <summary>True: the view grade keeps the preset's highlight tint (the close view by day, Rendering 2: with it neutral the sky went
    /// from cream to a dead grey, Oklab chroma 13.7 to 0.9, and the sunlit town read overcast).</summary>
    public bool ViewKeepHighlightTint { get; private set; }
    public void SetViewHighlights(float k, bool keepTint = false)
    {
        k = Mathf.Round(Mathf.Clamp(k, 0, 1) * 4) / 4;
        if (Mathf.IsEqualApprox(k, ViewHighlightsNeutral) && keepTint == ViewKeepHighlightTint) return;
        ViewHighlightsNeutral = k;
        ViewKeepHighlightTint = keepTint;
        var lut = GradeLut(Cine(ViewGrade(Own(Current))), Mute, SkinGuardFor(Current), ViewShadeHue, ViewSkinCool);
        ShowLut(lut);
    }
    // (#bcbcbc is linear 0.5: the grade adds a tint as its distance from 0.5, so this one adds nothing.)
    // (And the moon's colour off her skin: its weakly coloured parts went grey in patches beside the ember-lit ones.)
    GradeSettings ViewGrade(GradeSettings g) => ViewHighlightsNeutral <= 0 ? g
        : g with
        {
            HighlightTint = ViewKeepHighlightTint ? g.HighlightTint : "#" + new Color(g.HighlightTint).Lerp(new Color("#bcbcbc"), ViewHighlightsNeutral).ToHtml(false),
            Moon = g.Moon * (1 - CloseMoonOff * ViewHighlightsNeutral),
            // (The close view by night takes its own paint grade: art style round 1's, which kept her copper hair.)
            PaintVib = Mathf.Lerp((float)g.PaintVib, CloseVib, ViewHighlightsNeutral),
            PaintVibDark = Mathf.Lerp((float)g.PaintVibDark, CloseVibDark, ViewHighlightsNeutral),
            PaintHi = Mathf.Lerp((float)g.PaintHi, (float)Atmospheres.CloseNightPaint.PaintHi, ViewHighlightsNeutral),
            PaintShadow = Atmospheres.CloseNightPaint.PaintShadow,
            PaintShadowK = Mathf.Lerp((float)g.PaintShadowK, (float)Atmospheres.CloseNightPaint.PaintShadowK, ViewHighlightsNeutral),
            PaintLift = Mathf.Lerp((float)g.PaintLift, (float)Atmospheres.CloseNightPaint.PaintLift, ViewHighlightsNeutral),
            PaintShadowSkin = Mathf.Lerp((float)g.PaintShadowSkin, (float)Atmospheres.CloseNightPaint.PaintShadowSkin, ViewHighlightsNeutral),
        };
    /// <summary>A cinematic's own grade over the preset's (GameCinema's "grade" cue: the moon's colour, the painted shade),
    /// null outside one; SetCineGrade remakes the table at once, and the cinematic's end gives play's back.</summary>
    public Func<GradeSettings, GradeSettings>? CineGrade { get; private set; }
    GradeSettings Cine(GradeSettings g) => CineGrade?.Invoke(g) ?? g;
    public void SetCineGrade(Func<GradeSettings, GradeSettings>? f)
    {
        CineGrade = f;
        var lut = GradeLut(Cine(ViewGrade(Own(Current))), Mute, SkinGuardFor(Current), ViewShadeHue, ViewSkinCool);
        ShowLut(lut);
    }
    /// <summary>--close-vib V, --close-vib-dark D: the close view's paint vibrance and its share in the darks (pictures).</summary>
    static readonly float CloseVib = SurvivorUnchained.Args.Num("close-vib", (float)Atmospheres.CloseNightPaint.PaintVib),
        CloseVibDark = SurvivorUnchained.Args.Num("close-vib-dark", (float)Atmospheres.CloseNightPaint.PaintVibDark);
    /// <summary>The title and the Look (Atmospheres.Front) take the close view's paint grade (G1 r4 judge: it fixed her pale, washed-out
    /// lit face at the Look; identity, freckles and copper held). --front-unpainted: the grade before it (pictures).</summary>
    static readonly bool FrontPaint = !SurvivorUnchained.Args.Has("front-unpainted");
    /// <summary>The title and the Look also take the close view's neutral highlight tint (Face 44, skin B): the night grade's
    /// orange #ffad5c at 0.24 multiplied the chroma of her brightest skin 3.5-4.4x above L .75 and left a flat orange
    /// forehead, which the town close-up already took off (ViewHighlightsNeutral). --front-hi-warm: the tint before it (pictures).</summary>
    static readonly bool FrontHiWarm = SurvivorUnchained.Args.Has("front-hi-warm");
    /// <summary>(--air-tune) Front as tuned: still the title and the Look's, for Own and the skin guard.</summary>
    static AtmospherePreset? FrontTuned;
    static bool IsFront(AtmospherePreset p) => ReferenceEquals(p, Atmospheres.Front) || ReferenceEquals(p, FrontTuned) || ReferenceEquals(p.Source, Atmospheres.Front);
    static GradeSettings Own(AtmospherePreset p) => FrontPaint && IsFront(p) ? p.Grade with
    {
        HighlightTint = FrontHiWarm ? p.Grade.HighlightTint : "#bcbcbc",
        PaintVib = Atmospheres.CloseNightPaint.PaintVib, PaintVibDark = Atmospheres.CloseNightPaint.PaintVibDark, PaintHi = Atmospheres.CloseNightPaint.PaintHi,
        PaintShadow = Atmospheres.CloseNightPaint.PaintShadow, PaintShadowK = Atmospheres.CloseNightPaint.PaintShadowK, PaintLift = Atmospheres.CloseNightPaint.PaintLift,
        PaintShadowSkin = Atmospheres.CloseNightPaint.PaintShadowSkin,
    } : p.Grade;
    /// <summary>--close-moon-off K: how much of the grade's moon colour the close view by night takes off (pictures).</summary>
    static readonly float CloseMoonOff = SurvivorUnchained.Args.Num("close-moon-off", 1f);

    public void SetViewExposure(float k)
    {
        if (Mathf.IsEqualApprox(k, ViewExposure)) return;
        ViewExposure = k;
        Env.TonemapExposure = (float)Current.Exposure * ExposureScale * k * FlareDip;
    }
    double clock;

    const float FogMatchDistance = 60;
    static readonly bool OldAir = SurvivorUnchained.Args.Has("air-old");
    static readonly bool LightLog = SurvivorUnchained.Args.Has("light-log");
    string lightLogged = "";
    // (Colours as sRGB hex, written with '_' for '#'; three numbers as r/g/b.)
    static readonly Dictionary<string, string>? Tune = SurvivorUnchained.Args.Get("air-tune") is string tu
        ? tu.Split(',').Select(kv => kv.Split('=')).ToDictionary(kv => kv[0], kv => kv[1].Replace('_', '#')) : null;
    /// <summary>--grade-off: no colour grade (the frame as AgX leaves it), to design the grade outside the game.</summary>
    static readonly bool GradeOff = SurvivorUnchained.Args.Has("grade-off");

    public Atmosphere()
    {
        Name = "Atmosphere";
        sky = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/sky.gdshader") };
        Env = new Godot.Environment
        {
            BackgroundMode = Godot.Environment.BGMode.Sky,
            Sky = new Sky { SkyMaterial = sky, RadianceSize = Sky.RadianceSizeEnum.Size128 },
            AmbientLightSource = Godot.Environment.AmbientSource.Sky,
            ReflectedLightSource = Godot.Environment.ReflectionSource.Sky,
            AmbientLightSkyContribution = 1,
            TonemapMode = Godot.Environment.ToneMapper.Agx,
            // Ambient occlusion as the web game's N8AO: a wide, soft darkening.
            SsaoEnabled = true, SsaoRadius = 1.6f, SsaoIntensity = 1.6f, SsaoPower = 1.3f, SsaoDetail = 0.4f,
            // Bloom from what is brighter than white (a flame, an ember, a
            // glint), soft-lit and from the tighter levels only: the wide ones,
            // or an additive blend, spread every bright speck into a ball of
            // light (the slice's tuning, by the Hunters' Blind's fire).
            GlowEnabled = true, GlowHdrThreshold = 1.1f, GlowIntensity = 0.7f, GlowBloom = 0.04f,
            GlowBlendMode = Godot.Environment.GlowBlendModeEnum.Softlight,
            FogEnabled = true, FogMode = Godot.Environment.FogModeEnum.Exponential, FogSkyAffect = 0, FogSunScatter = 0,
            // A little air the fires can be seen in (the web game has none); thin,
            // since the camera looks down through thirty metres of it.
            VolumetricFogEnabled = true, VolumetricFogDensity = 0.0012f, VolumetricFogLength = 64, VolumetricFogAnisotropy = 0.3f,
            AdjustmentEnabled = true,
        };
        float[] glow = { 0, 0.6f, 1, 0.5f, 0.15f, 0, 0 };
        for (int i = 0; i < glow.Length; i++) Env.SetGlowLevel(i, glow[i]);
        AddChild(new WorldEnvironment { Environment = Env });
        Key = new DirectionalLight3D
        {
            Name = "Key", ShadowEnabled = true, DirectionalShadowMaxDistance = 70, ShadowBlur = 1.5f,
            DirectionalShadowMode = DirectionalLight3D.ShadowMode.Parallel4Splits, LightVolumetricFogEnergy = 0.6f,
        };
        AddChild(Key);
        Set(Current);
    }

    public override void _Process(double delta)
    {
        clock += delta;
        HazeFadeTick(delta);
        if (FlareDip != dipShown) { dipShown = FlareDip; Env.TonemapExposure = (float)Current.Exposure * ExposureScale * ViewExposure * FlareDip; }
        if (FlareLight != lightShown)
        {
            float r = FlareLight / Mathf.Max(lightShown, 0.05f);
            lightShown = FlareLight;
            Key.LightEnergy *= r;
            Env.AmbientLightEnergy *= r;
        }
        RenderingServer.GlobalShaderParameterSet(SkyTime, (float)clock);
    }

    // (A name made once, not a new one every frame for the collector.)
    static readonly StringName SkyTime = "sky_time";
    static readonly float FrostScale = SurvivorUnchained.Args.Num("frost", 1f);

    static Color C(string hex) => new(hex);

    /// <param name="grade">Rebuild the colour grade too (not every frame of a blend).</param>
    /// <summary>The sun the frost's thaw is baked for under `p` (Set: GroundPaint.SunAt), or null if it has no thaw:
    /// for baking it ahead (GroundPaint.SunAhead). (--air-old and --air-tune are not followed: a bake ahead for a
    /// sun that does not come is only wasted, and the one that does is baked as before.)</summary>
    public static Vector3? ThawSun(AtmospherePreset p)
    {
        if (!(p.Frost * FrostScale > 0 && p.FrostThaw > 0)) return null;
        float el = Mathf.DegToRad((float)(p.ThawElevation >= 0 ? p.ThawElevation : p.KeyElevation)), az = Mathf.DegToRad((float)p.KeyAzimuth);
        return new Vector3(Mathf.Cos(el) * Mathf.Cos(az), Mathf.Sin(el), Mathf.Cos(el) * Mathf.Sin(az)).Normalized();
    }

    public void Set(AtmospherePreset p, bool grade = true)
    {
        // --air-old: play's presets (E1) back to the ones before them, for before-and-after pictures.
        if (OldAir) p = ReferenceEquals(p, Atmospheres.LowFordNight) ? Atmospheres.Night : ReferenceEquals(p, Atmospheres.LowFordDawn) ? Atmospheres.Dawn
            : ReferenceEquals(p, Atmospheres.WaystationDawn) ? Atmospheres.Dawn : ReferenceEquals(p, Atmospheres.WaystationDay) ? Atmospheres.Day : p;
        // (L1 B4) Under the cel model the preset's rig lights it (godot/data/look/rigs.json); --cel off: the preset as it is.
        var orig = p;
        if (CelRigs) { RigsLoad(); p = SurvivorUnchained.Look.Rigs.Lit(p); }
        // (L1 B4r3) the zones' fires and lamps at the rig's share (rigs.json "fires": by day a glow; ZoneView.FireShare)
        ZoneView.FireShare = CelRigs && orig.Rig != "" && SurvivorUnchained.Look.Rigs.Current[orig.Rig] is { } fr ? (float)fr.FireShare : 1f;
        // (L1 lead 14, S1) the rig's standing levels (rigs.json "stand"; SetCel binds them: cel_stand, cel_stand_fire, cel_stand_pal)
        standOf = CelRigs && orig.Rig != "" && SurvivorUnchained.Look.Rigs.Current[orig.Rig] is { Stands: true } sr ? sr.Stand : null;
        // --air-tune "fillc=#..,fill=..,hemi=..,env=..,exposure=..,key=..,elevation=..,azimuth=..,shadow=..,tint=..,toe=..,contrast=..,ember=..,mist=..,haze=..":
        // play's presets (E1) nudged, for a sweep of pictures in one build (under cel, the rig's light nudged).
        if (Tune != null && (ReferenceEquals(orig, Atmospheres.LowFordNight) || ReferenceEquals(orig, Atmospheres.LowFordDawn)
            || ReferenceEquals(orig, Atmospheres.WaystationDawn) || ReferenceEquals(orig, Atmospheres.WaystationDay) || ReferenceEquals(orig, Atmospheres.NightTown)
            || p.CrowdFill > 0 || ReferenceEquals(orig, Atmospheres.Front)   // (H2 R1: an ember arena's night, the only preset with the crowd's fill; R3: the title)
            || ReferenceEquals(orig, Atmospheres.Title) || ReferenceEquals(orig, Atmospheres.CineNight)))   // (L1 lead 9: the title's and the cinematics' night rigs)
        {
            bool front = ReferenceEquals(orig, Atmospheres.Front);
            double T(string k, double v) => Tune.TryGetValue(k, out var x) ? double.Parse(x, System.Globalization.CultureInfo.InvariantCulture) : v;
            ZoneView.FireShare = (float)T("fires", ZoneView.FireShare);   // (L1 lead 9: the fires' share, rigs.json "fires")
            string H(string k, string v) => Tune.TryGetValue(k, out var x) ? x : v;
            double[] V(string k, double[] v) => Tune.TryGetValue(k, out var x)
                ? x.Split('/').Select(n => double.Parse(n, System.Globalization.CultureInfo.InvariantCulture)).ToArray() : v;
            p = p with
            {
                KeyColor = H("keyc", p.KeyColor), CelFillColor = H("fillc", p.CelFillColor), CelFill = T("fill", p.CelFill), HemiSky = H("hemisky", p.HemiSky), HemiGround = H("hemiground", p.HemiGround),
                FogColor = H("fogc", p.FogColor), MistColor = H("mistc", p.MistColor),
                Sky = p.Sky with { Top = H("skytop", p.Sky.Top), Horizon = H("skyhor", p.Sky.Horizon), Glow = H("skyglow", p.Sky.Glow) },
                HemiIntensity = T("hemi", p.HemiIntensity), EnvIntensity = T("env", p.EnvIntensity), Exposure = T("exposure", p.Exposure),
                KeyIntensity = T("key", p.KeyIntensity), KeyElevation = T("elevation", p.KeyElevation), KeyAzimuth = T("azimuth", p.KeyAzimuth),
                ShadowStrength = T("shadow", p.ShadowStrength), Ember = T("ember", p.Ember), Mist = T("mist", p.Mist), Haze = T("haze", p.Haze),
                FogDensity = T("fog", p.FogDensity), CrowdRim = T("crowdrim", p.CrowdRim), CrowdFill = T("crowdfill", p.CrowdFill), RiverLight = T("river", p.RiverLight),
                RiverSky = T("riversky", p.RiverSky), RiverBend = T("bend", p.RiverBend),
                // (S2b-N3: her pool, the moon's give, and the canopy's dapple, for a sweep in one build: pool=a/b/..., give=a/b/c/d)
                EmberPool = V("pool", p.EmberPool ?? []) is { Length: > 0 } tp ? tp : p.EmberPool, EmberGive = V("give", p.EmberGive ?? []) is { Length: > 0 } tg ? tg : p.EmberGive,
                FireGive = V("fgive", p.FireGive ?? []) is { Length: > 0 } tf ? tf : p.FireGive,   // (L1 lead 9, NIGHT2: fgive=key/sky/start/gone)
                EmberEdge = H("edge", p.EmberEdge), EmberSmooth = T("psmooth", p.EmberSmooth ? 1 : 0) > 0, EmberShade = V("pshade", p.EmberShade ?? []) is { Length: > 0 } tsh ? tsh : p.EmberShade,
                MoonTop = V("s3", p.MoonTop ?? []) is { Length: > 0 } ts3 ? ts3 : p.MoonTop, FoeFire = V("ffire", p.FoeFire ?? []) is { Length: > 0 } tff ? tff : p.FoeFire, FoeMoon = V("fmoon", p.FoeMoon ?? []) is { Length: > 0 } tfm ? tfm : p.FoeMoon,   // (L1 lead 12, S3: s3=level/R/G/B/top/up/rimpx/unlit, ffire=level/second/edge1/edge2, fmoon=lum/pull/shade level/R/G/B/residue; s3=0 or ffire=0: off)   // (L1 lead 12, R4 round 4: psmooth=1, pshade=cut/from/to/moon)
                DappleCover = T("dcover", p.DappleCover), DappleStrength = T("dstr", p.DappleStrength), DappleSize = T("dsize", p.DappleSize), DappleFloor = T("dfloor", p.DappleFloor),
                // (L1 lead 11: the dapple's edge (px) and the leaf cookie's shapes: dedge=2,dclusters=300,dleaf=1.2/3.5,dleaves=2/4)
                DappleEdge = T("dedge", p.DappleEdge), DappleClusters = T("dclusters", p.DappleClusters),
                DappleLeaf = V("dleaf", p.DappleLeaf ?? []) is { Length: 2 } tl ? tl : p.DappleLeaf, DappleLeaves = V("dleaves", p.DappleLeaves ?? []) is { Length: 2 } tv ? tv : p.DappleLeaves,
                DappleMass = V("dmass", p.DappleMass ?? []) is { Length: >= 2 and <= 4 } tm ? tm : p.DappleMass,   // (L1 lead 14, D2: the canopy as a field, dmass=1.2/4, dmass=1.2/4/3 (the third the random run) or dmass=1.2/4/0/0.46 (the fourth the lit share))
                Grade = p.Grade with
                {
                    TintStrength = T("tint", p.Grade.TintStrength), Contrast = T("contrast", p.Grade.Contrast), Toe = T("toe", p.Grade.Toe),
                    ShadowTint = H("sh", p.Grade.ShadowTint), HighlightTint = H("hi", p.Grade.HighlightTint), Gain = V("gain", p.Grade.Gain),
                    Lift = V("lift", p.Grade.Lift), Saturation = T("sat", p.Grade.Saturation), Vibrance = T("vib", p.Grade.Vibrance),
                    Moon = T("moon", p.Grade.Moon), MoonHue = T("mhue", p.Grade.MoonHue), MoonSat = T("msat", p.Grade.MoonSat),
                    MoonDrop = T("mdrop", p.Grade.MoonDrop), MoonLo = T("mlo", p.Grade.MoonLo), MoonHi = T("mhi", p.Grade.MoonHi),
                    MoonTop = T("mtop", p.Grade.MoonTop), MoonWidth = T("mw", p.Grade.MoonWidth), MoonSkin = T("mskin", p.Grade.MoonSkin),
                    PaintShadow = H("psh", p.Grade.PaintShadow), PaintShadowK = T("pshk", p.Grade.PaintShadowK), PaintVib = T("pvib", p.Grade.PaintVib),
                    PaintLift = T("plift", p.Grade.PaintLift), PaintHi = T("phi", p.Grade.PaintHi), PaintShadowSkin = T("pshskin", p.Grade.PaintShadowSkin),
                },
            };
            // (L1 lead 11, R3 one shade: under a level shadow the dapple's strength is the shadow's, unless dstr is given)
            if (p.ShadowLevel && !Tune.ContainsKey("dstr")) p = p with { DappleStrength = p.ShadowStrength };
            if (front) FrontTuned = p;
        }
        Current = p;
        float el = Mathf.DegToRad((float)p.KeyElevation), az = Mathf.DegToRad((float)p.KeyAzimuth);
        var dir = new Vector3(Mathf.Cos(el) * Mathf.Cos(az), Mathf.Sin(el), Mathf.Cos(el) * Mathf.Sin(az)).Normalized();
        Key.Basis = Basis.LookingAt(-dir, Mathf.Abs(dir.Y) > 0.99f ? Vector3.Forward : Vector3.Up);
        Key.LightColor = C(p.KeyColor);
        Key.LightEnergy = (float)p.KeyIntensity / Mathf.Pi * lightShown;
        Key.ShadowOpacity = (float)p.ShadowStrength;

        var s = p.Sky;
        // (E8 r2) the far castle stands only under a night sky (C01 s8a's lamp); by day or dawn it would show over the
        // gate's silhouette (C04 A8) in the night's haze
        OwnProps.FarShown(C(s.Top).Luminance < 0.08f);
        OwnProps.SkyHaze(C(s.Horizon));
        sky.SetShaderParameter("top", C(s.Top));
        sky.SetShaderParameter("horizon", C(s.Horizon));
        sky.SetShaderParameter("bottom", C(s.Bottom));
        sky.SetShaderParameter("glow", C(s.Glow));
        sky.SetShaderParameter("glow_power", (float)s.GlowPower);
        sky.SetShaderParameter("stars", (float)s.Stars);
        sky.SetShaderParameter("moon", (float)s.Moon);
        sky.SetShaderParameter("light_dir", dir);
        sky.SetShaderParameter("hemi_sky", C(p.HemiSky));
        sky.SetShaderParameter("hemi_ground", C(p.HemiGround));
        sky.SetShaderParameter("hemi_intensity", (float)p.HemiIntensity);
        sky.SetShaderParameter("env_intensity", (float)p.EnvIntensity);

        Env.FogLightColor = C(p.FogColor);
        Env.FogDensity = (float)(p.FogDensity * p.FogDensity * FogMatchDistance) * fogScale;
        HazeApply();
        Env.VolumetricFogAlbedo = C(p.FogColor).Lightened(0.5f);
        Env.VolumetricFogDensity = (float)p.Haze;
        // An ember arena's own air: smoke or dust hanging in it.
        Key.LightAngularDistance = 0;
        if (air is { } a)
        {
            Env.VolumetricFogDensity = (float)p.Haze * (float)a.Haze;
            Env.VolumetricFogAlbedo = C(a.HazeColor).Lightened(0.35f);
            // Under a canopy the moon's breadth softens a shadow by how far its caster stands
            // over the ground (PCSS): the pools get a soft rim from leaves nine metres up, and
            // the shadows at the living's feet stay sharp.
            // (At 2.5° the pools washed out into a general shading.)
            if (a.Dapple > 0) Key.LightAngularDistance = 1.2f;
        }
        Env.TonemapExposure = (float)p.Exposure * ExposureScale * ViewExposure * FlareDip;
        // (L1 lead 11, R2) --light-log: what the renderer got, one line each time it changes (a shoot's log shows the levels).
        if (LightLog)
        {
            var ci = System.Globalization.CultureInfo.InvariantCulture;
            string line = string.Create(ci, $"LIGHT rig={(p.Rig != "" ? p.Rig : "-")} cel={(CelRigs ? 1 : 0)} place={(airPlace != "" ? airPlace : "-")} mood={(airMood != "" ? airMood : "-")} "
                + $"key={p.KeyColor} {p.KeyIntensity:0.###} (energy {Key.LightEnergy:0.###}) el={p.KeyElevation:0.#} az={p.KeyAzimuth:0.#} shadow={p.ShadowStrength:0.###} "
                + $"fill={p.CelFillColor} {p.CelFill:0.####} hemi={p.HemiSky}/{p.HemiGround} {p.HemiIntensity:0.###} env={p.EnvIntensity:0.###} "
                + $"exposure={p.Exposure:0.###} (tonemap {Env.TonemapExposure:0.###}) hardness={p.CelShadow:0.##} "
                + $"dapple=cover {p.DappleCover:0.##} strength {p.DappleStrength:0.###} size {p.DappleSize:0.#} floor {p.DappleFloor:0.##} edge {p.DappleEdge:0.#} one_shade={(p.ShadowLevel ? 1 : 0)}");
            if (line != lightLogged) { lightLogged = line; GD.Print(line); }
        }
        SurvivorUnchained.View.MistLayers.Tint(C(p.MistColor), (float)p.Mist, C(p.KeyColor).SrgbToLinear() * ((float)p.KeyIntensity / Mathf.Pi));
        EmberGain = (float)p.Ember;
        EmberColor = p.EmberColor != "" ? new Color(p.EmberColor) : null; EmberReach = (float)p.EmberReach;
        var rim = C(p.Rim).SrgbToLinear();
        RenderingServer.GlobalShaderParameterSet("body_rim", new Vector4(rim.R, rim.G, rim.B, (float)p.RimStrength));
        // (S2b-N3, rule 7: under the cel rigs the pack's moon rim is the rig's moon rim, one for every pack and place)
        var crim = CelRigs && p.CelRimColor != "" ? C(p.CelRimColor).SrgbToLinear() : rim;
        RenderingServer.GlobalShaderParameterSet("crowd_rim", new Vector4(crim.R, crim.G, crim.B, (float)(p.RimStrength * p.CrowdRim) * (R4 && CrowdFillOn && p.CrowdFill > 0 ? CrowdEdgeK : 1)));
        RenderingServer.GlobalShaderParameterSet("key_dir", new Vector4(dir.X, dir.Y, dir.Z, 0));
        // Rendering 4: the crowd's own light by night (vat.gdshaderinc): the sky's fill here, her lamp's in PlayerView.
        CrowdFill = CrowdFillOn ? (float)p.CrowdFill : 0;
        // (r2: the fill in the moonlit dirt's hue, at the sky's luminance; the cool sky only on heads and shoulders)
        var hs = C(p.HemiSky).SrgbToLinear();
        var hg = C(p.HemiGround).SrgbToLinear();
        var hue = hs.Lerp(hg * (hs.Luminance / Mathf.Max(hg.Luminance, 1e-4f)), CrowdDirt);
        // (L1 lead 8, S2b-N2: and at the sky's own energy, its intensity over the H2 nights' 2.0 the fill was tuned under: the
        // rigs' sky colors (C6) are bright with a low intensity, #b5d9ff at 0.5 for the Hollow's #2a3c48 at 2.0, and the color
        // alone lifted the crowd's fill about 15 times: pale silver wolves on 09, rule 7)
        float skyK = (float)p.HemiIntensity / CrowdSkyRef;
        var fill = hue * (CrowdFill * CrowdMoonK * skyK);
        var top = hs * (CrowdFill * CrowdTopK * skyK);
        RenderingServer.GlobalShaderParameterSet("crowd_fill", new Vector4(fill.R, fill.G, fill.B, CrowdEmberRange));
        RenderingServer.GlobalShaderParameterSet("crowd_top", new Vector4(top.R, top.G, top.B, CrowdBack));
        RenderingServer.GlobalShaderParameterSet("crowd_lamp2", CrowdFill > 0 ? new Vector4(CrowdK, CrowdFull, CrowdZero, CrowdZero > 0 ? CrowdRimK : 0) : Vector4.Zero);
        RenderingServer.GlobalShaderParameterSet("crowd_lamp3", new Vector4(CrowdNearR, CrowdNearK, CrowdDead, CrowdCardEdge));
        RenderingServer.GlobalShaderParameterSet("crowd_dbg_s", SurvivorUnchained.Args.Num("crowd-dbg-s", 0.3f));
        RenderingServer.GlobalShaderParameterSet("crowd_amb", CrowdFill > 0 ? Mathf.Lerp(1f, CrowdAmb, CrowdFill) : 1f);
        RenderingServer.GlobalShaderParameterSet("crowd_night", CrowdFill > 0 ? new Vector4(CrowdLift * CrowdFill, CrowdFlat, CrowdWrap, CrowdDbg > 0 ? CrowdDbg : 1) : Vector4.Zero);
        RenderingServer.GlobalShaderParameterSet("crowd_r4", CrowdFill > 0 && R4 ? new Vector4(CrowdEdge, CrowdSpec, CrowdGRim, 1) : new Vector4(0, 0.5f, 1, 0));
        // Our own trees' light (kit.gdshader's OWN_FOLIAGE, E4): how much the key is the moon (a blue key)
        // and how much a low warm sun (dawn, dusk): the needles' back light and greens follow them.
        var kc = C(p.KeyColor);
        float moon = Mathf.Clamp((kc.B - kc.R) * 4f, 0f, 1f);
        float lowSun = Mathf.Clamp((kc.R - kc.B) * 3f, 0f, 1f) * (1f - Mathf.SmoothStep(15f, 35f, (float)p.KeyElevation));
        var kl = kc.SrgbToLinear();
        RenderingServer.GlobalShaderParameterSet("flora_light", new Vector4(moon, lowSun, kl.R / Mathf.Max(kl.G, 1e-3f), kl.B / Mathf.Max(kl.G, 1e-3f)));
        TownLit = Mathf.Max(moon, 1f - Mathf.SmoothStep(18f, 26f, (float)p.KeyElevation));
        RenderingServer.GlobalShaderParameterSet("town_lit", TownLit);
        RenderingServer.GlobalShaderParameterSet("water_air", new Vector4((float)p.RiverLight, (float)p.RiverSky, (float)p.RiverBend, (float)p.RiverMoon));
        RenderingServer.GlobalShaderParameterSet("flora_lamp", SurvivorUnchained.Args.Num("grass-lamp-ochre", (float)p.GrassLampOchre));
        RenderingServer.GlobalShaderParameterSet("flora_night", new Vector4(SurvivorUnchained.Args.Num("bush-night-sat", (float)p.BushNightSat), SurvivorUnchained.Args.Num("ground-ember-ochre", (float)p.GroundEmberOchre), 0, 0));
        // Hoar frost on the ground's exposed tops (terrain and grass shaders; GroundPaint's sky exposure), thawed
        // where the sun falls: its shade baked for this key. (--frost K scales it, for sweeps.)
        float frost = (float)p.Frost * FrostScale, thaw = (float)p.FrostThaw;
        RenderingServer.GlobalShaderParameterSet("ground_frost", new Vector4(frost, thaw, 0, 0));
        if (frost > 0 && thaw > 0) GroundPaint.SunAt(ThawSun(p) ?? dir);   // (as ThawSun says)
        // The key's light off the ground (a mid albedo, 0.18), what metal sees below the horizon: the
        // sky's lower half is the hemisphere's dark ground colour, so in shade her plate reflected
        // nothing and read as rubber (look bible, armor metal; metal round 3).
        var key = C(p.KeyColor).SrgbToLinear() * (Key.LightEnergy * Mathf.Max(dir.Y, 0f) * 0.18f);
        RenderingServer.GlobalShaderParameterSet("ground_bounce", new Vector4(key.R, key.G, key.B, 0f));
        keyToward = dir;
        SetCel(p);
        if (grade) { var lut = LutFor(p); if (GradeOff) Env.AdjustmentColorCorrection = null; else ShowLut(lut); }
    }

    /* ------------------------------------------------- the cel model (L1 B1a) -- */

    /// <summary>--cel off|on|0..1 (default on: the preset's CelOn; off lights exactly as before the cel model).</summary>
    static readonly float? CelArg = SurvivorUnchained.Args.Get("cel") is string ca
        ? ca == "off" ? 0f : ca == "on" ? null : float.TryParse(ca, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out var cv) ? Mathf.Clamp(cv, 0f, 1f) : null
        : null;
    /// <summary>--cel-rig hardness,fill,rim,width and --cel-tune band,halftone,spec,form (multipliers): sweeps without edits.</summary>
    static readonly float[]? CelRigArg = SurvivorUnchained.Args.Get("cel-rig") is string ? Floats("cel-rig", 0, 0, 0, 0) : null;
    static readonly float[] CelTune = Floats("cel-tune", 1, 1, 1, 1);
    /// <summary>--cel-dbg band|ink|skin: the key's band level as gray, each material's ink class unlit (0 white, 1 yellow, 2 blue, 3 red), or her skin white (CEL_SKIN; the mask for measuring, L1 B1c).</summary>
    static readonly float CelDbg = SurvivorUnchained.Args.Get("cel-dbg") switch { "band" => 1f, "ink" => 2f, "skin" => 3f, _ => 0f };

    /// <summary>(L1 B4) The rigs light the presets: cel on (not --cel off). --cel-rigs off: cel on, the presets' own light.</summary>
    public static readonly bool CelRigs = (CelArg ?? 1f) > 0f && SurvivorUnchained.Args.Get("cel-rigs") is not ("off" or "0");
    static bool rigsLoaded;
    /// <summary>godot/data/look/rigs.json into Rigs.Current, once. --rigs-file PATH: another rig file in its place (a sweep of
    /// rig variants in one build; B4r3).</summary>
    public static void RigsLoad()
    {
        if (rigsLoaded) return;
        rigsLoaded = true;
        SurvivorUnchained.Look.Rigs.Current = SurvivorUnchained.Look.RigSet.Parse(Godot.FileAccess.GetFileAsString(SurvivorUnchained.Args.Get("rigs-file") ?? "res://data/look/rigs.json"));
    }
    /// <summary>(L1 lead 14, S1) The standing material's tones as a texture, 8 x 3 (a family a row: stone, leaf, bark): texels
    /// 0-6 the tone as scene light (contact, side, body, top, rim, fire mid, fire top: the sRGB color at its largest channel 1
    /// x its level, a the level), texel 7 the family's four numbers as written (LightRig.Stand). Kept: SetCel runs every frame.</summary>
    static ImageTexture StandPal(double[] st)
    {
        if (standPal != null && ReferenceEquals(standPalOf, st)) return standPal;
        const int row = SurvivorUnchained.Look.LightRig.StandRow;
        var img = Image.CreateEmpty(8, 3, false, Image.Format.Rgbaf);
        for (int f = 0; f < 3; f++)
            for (int i = 0; i < 8; i++)
            {
                int k = f * row + i * 4;
                if (i == 7) { img.SetPixel(i, f, new Color((float)st[k], (float)st[k + 1], (float)st[k + 2], (float)st[k + 3])); continue; }
                var c = new Color((float)st[k + 1] / 255f, (float)st[k + 2] / 255f, (float)st[k + 3] / 255f).SrgbToLinear();
                float mx = Mathf.Max(c.R, Mathf.Max(c.G, Mathf.Max(c.B, 1e-4f))), lv = (float)st[k];
                img.SetPixel(i, f, new Color(c.R / mx * lv, c.G / mx * lv, c.B / mx * lv, lv));
            }
        standPalOf = st;
        return standPal = ImageTexture.CreateFromImage(img);
    }
    static double[]? standOf, standPalOf;
    static ImageTexture? standPal;
    /// <summary>(L1 lead 14, K1; docs/design/NIGHT_KIT.md) True when this rig carries the standing material's levels
    /// (rigs.json "stand") under the cel rigs: an arena lit by it draws our own flora (ZoneData), not the kit's.</summary>
    public static bool StandRig(string rig)
    {
        if (!CelRigs || rig == "") return false;
        RigsLoad();
        return SurvivorUnchained.Look.Rigs.Current[rig] is { Stands: true };
    }
    /// <summary>(L1 B4) A camera rig in force (the close-up, the Look: GameCloseUp, GameFront): its fill and rim over the
    /// air's while it is, and the canopy's dapple held off (its key is the lens's, not the moon's). Null: the air's.</summary>
    public SurvivorUnchained.Look.LightRig? CameraRig { get; private set; }
    public void HoldCameraRig(SurvivorUnchained.Look.LightRig? r)
    {
        if (ReferenceEquals(r, CameraRig)) return;
        CameraRig = r;
        SetCel(Current, r);
    }
    /// <summary>(L1 B4) The world key's direction toward the light and the dapple's strength (cel_key; cel.gdshaderinc).</summary>
    Vector3 keyToward = Vector3.Up;

    /// <summary>The cel model's globals (shaders/cel.gdshaderinc) from the preset: its hues taken at luminance 1, so
    /// CelFill and CelRim are how much of the key's light they are. (L1 B4: a camera rig's fill and rim over them; the ink
    /// rig's color (InkPass.SetRig); the canopy's dapple along the key, cel_key and cel_dapple, where a canopy mask stands.)</summary>
    void SetCel(AtmospherePreset p) => SetCel(p, CameraRig);
    void SetCel(AtmospherePreset p, SurvivorUnchained.Look.LightRig? cam)
    {
        if (cam != null && CelRigs)
            p = p with
            {
                CelFillColor = cam.Fill.Color ?? p.CelFillColor, CelFill = cam.Fill.Strength ?? p.CelFill,
                CelRimColor = cam.Rim.Color ?? p.CelRimColor, CelRim = cam.Rim.Strength ?? p.CelRim, CelRimWidth = cam.Rim.Width ?? p.CelRimWidth,
                CelShadow = cam.Hardness ?? p.CelShadow, CelInk = cam.Ink ?? p.CelInk,
            };
        if (CelRigs) InkPass.SetRig(p.CelInk is [var ir, var ig, var ib] ? new Color((float)ir, (float)ig, (float)ib) : InkPass.Night);
        float dap = CelRigs && cam == null && CanopyCookie.Shown && p.DappleCover > 0 ? (float)p.DappleStrength : 0f;
        RenderingServer.GlobalShaderParameterSet("cel_key", new Vector4(keyToward.X, keyToward.Y, keyToward.Z, dap));
        RenderingServer.GlobalShaderParameterSet("cel_dapple", new Vector4((float)p.DappleCover, CanopyCookie.PlaneY + (float)p.DappleHeight, (float)(p.DappleSize > 0 ? p.DappleSize : CanopyCookie.Tile), (float)(CanopyCookie.Floored ? p.DappleFloor : 0)));
        // (L1 lead 11, R3) the key's shadow as a level (cel_oneshade.x: its opacity; 0: the old switch), the dapple's edge (px), and the cookie's shapes
        RenderingServer.GlobalShaderParameterSet("cel_oneshade", new Vector4(CelRigs && cam == null && p.ShadowLevel ? (float)p.ShadowStrength : 0f, (float)p.DappleEdge,
            // (L1 lead 14, D2) z: the cookie is the FIELD tile (covers and leaf stems, CanopyField); its stems' range in the tile's own meters
            CanopyCookie.IsField(p.DappleMass) ? CanopyField.Stem * (float)((p.DappleSize > 0 ? p.DappleSize : CanopyCookie.Tile) / CanopyCookie.Tile) : 0f, 0));
        // (L1 lead 12, R4 round 4) the canopy's leaf shade across her fire: the share of the fire a leaf's shade takes, the canopy's opening over her (m: none inside, whole from), the moon kept under a leaf (--air-tune pshade=a/b/c/d). Zero: the rig has not opted in.
        RenderingServer.GlobalShaderParameterSet("cel_pool_shade", CelRigs && cam == null && p.EmberShade is [var sc, var sf, var st, var sm] ? new Vector4((float)sc, (float)sf, (float)st, (float)sm) : Vector4.Zero);
        // (L1 lead 12, S3, R5) the moon's top band and rim on what stands (cel_s3: the color x level, on; cel_s3_shape: top edge, up lean, rim px, the unlit side's share), and the foes on it
        // (crowd_fire, crowd_moon: her fire from the ground's ramp in two bands, the paint's night luminance). Zero: the rig has not opted in (every rig but arena_night), a camera rig, or the crowd's R4 or fill off.
        bool s3On = CelRigs && cam == null && p.MoonTop is { Length: 8 } && p.MoonTop[0] > 0;
        if (s3On)
        {
            var mt = p.MoonTop!;
            var sc3 = new Color((float)mt[1] / 255f, (float)mt[2] / 255f, (float)mt[3] / 255f).SrgbToLinear();
            float sm3 = Mathf.Max(sc3.R, Mathf.Max(sc3.G, Mathf.Max(sc3.B, 1e-4f))), sl3 = (float)mt[0];
            RenderingServer.GlobalShaderParameterSet("cel_s3", new Vector4(sc3.R / sm3 * sl3, sc3.G / sm3 * sl3, sc3.B / sm3 * sl3, 1));
            RenderingServer.GlobalShaderParameterSet("cel_s3_shape", new Vector4((float)mt[4], (float)mt[5], (float)mt[6], (float)mt[7]));
        }
        else { RenderingServer.GlobalShaderParameterSet("cel_s3", Vector4.Zero); RenderingServer.GlobalShaderParameterSet("cel_s3_shape", Vector4.Zero); }
        // (L1 lead 14, S1; docs/design/NIGHT_KIT.md K1) the standing material (cel.gdshaderinc's cel_stand_*): cel_stand = top edge,
        // side edge, up lean, foot band m; cel_stand_fire = fire edge 1, fire edge 2, rim px, spare; cel_stand_pal = the tones,
        // 8 x 3 (stone, leaf, bark). Zero: the rig has no "stand" (every rig but arena_night) or a camera rig is in force.
        if (CelRigs && cam == null && standOf is { } so)
        {
            int sh = 3 * SurvivorUnchained.Look.LightRig.StandRow;
            RenderingServer.GlobalShaderParameterSet("cel_stand_pal", StandPal(so));
            RenderingServer.GlobalShaderParameterSet("cel_stand", new Vector4((float)so[sh], (float)so[sh + 1], (float)so[sh + 2], (float)so[sh + 3]));
            RenderingServer.GlobalShaderParameterSet("cel_stand_fire", new Vector4((float)so[sh + 4], (float)so[sh + 5], (float)so[sh + 6], (float)so[sh + 7]));
        }
        else { RenderingServer.GlobalShaderParameterSet("cel_stand", Vector4.Zero); RenderingServer.GlobalShaderParameterSet("cel_stand_fire", Vector4.Zero); }
        bool foeOn = CelRigs && cam == null && R4 && CrowdFill > 0 && p.FoeFire is { Length: 4 } && p.FoeFire[0] > 0;
        RenderingServer.GlobalShaderParameterSet("crowd_fire", foeOn ? new Vector4((float)p.FoeFire![0], (float)p.FoeFire[1], (float)p.FoeFire[2], (float)p.FoeFire[3]) : Vector4.Zero);
        // (L1 lead 19, SH2: an eighth value, her own fire shadow's tone against a foe's (one step deeper), rides in crowd_moon.w: crowd_blob_cast)
        if (foeOn && p.FoeMoon is [var fl, var fp, var fsl, var fsr, var fsg, var fsb, var fres, ..])
        {
            var fsc = new Color((float)fsr / 255f, (float)fsg / 255f, (float)fsb / 255f).SrgbToLinear();
            float fsm = Mathf.Max(fsc.R, Mathf.Max(fsc.G, Mathf.Max(fsc.B, 1e-4f))) / (float)fsl;
            RenderingServer.GlobalShaderParameterSet("crowd_moon", new Vector4((float)fl, (float)fp, (float)fres, p.FoeMoon.Length > 7 ? (float)p.FoeMoon[7] : 0));
            RenderingServer.GlobalShaderParameterSet("crowd_shade", fsl > 0 ? new Vector4(fsc.R / fsm, fsc.G / fsm, fsc.B / fsm, 1) : Vector4.Zero);
        }
        else { RenderingServer.GlobalShaderParameterSet("crowd_moon", Vector4.Zero); RenderingServer.GlobalShaderParameterSet("crowd_shade", Vector4.Zero); }
        if (CelRigs) CanopyCookie.Shape((int)p.DappleClusters, p.DappleLeaf, p.DappleLeaves, p.DappleMass);
        static Vector3 Hue(Color c)
        {
            float l = Mathf.Max(c.R * 0.2126f + c.G * 0.7152f + c.B * 0.0722f, 1e-4f);
            var v = new Vector3(c.R, c.G, c.B) / l;
            float m = Mathf.Max(v.X, Mathf.Max(v.Y, v.Z));
            return m > 3f ? v * (3f / m) : v;
        }
        var fill = Hue(C(p.CelFillColor != "" ? p.CelFillColor : p.HemiSky).SrgbToLinear());
        var rim = Hue(C(p.CelRimColor != "" ? p.CelRimColor : p.Rim).SrgbToLinear());
        var rig = CelRigArg ?? [(float)p.CelShadow, (float)p.CelFill, (float)p.CelRim, (float)p.CelRimWidth];
        RenderingServer.GlobalShaderParameterSet("cel_on", CelArg ?? (float)p.CelOn);
        RenderingServer.GlobalShaderParameterSet("cel_rig", new Vector4(rig[0], rig[1], rig[2], rig[3]));
        RenderingServer.GlobalShaderParameterSet("cel_fill", fill);
        // (L1 l9 DAY, rule 6: the metal's broad band in the sky's color, never the fill's: look_day's fill drew a magenta disc on her cup at 08)
        RenderingServer.GlobalShaderParameterSet("cel_sky", Hue(C(p.HemiSky).SrgbToLinear()));
        RenderingServer.GlobalShaderParameterSet("cel_rim", rim);
        RenderingServer.GlobalShaderParameterSet("cel_tune", new Vector4(CelTune[0], CelTune[1], CelTune[2], CelTune[3]));
        RenderingServer.GlobalShaderParameterSet("cel_dbg", CelDbg);
        // (L1 W2) how the moon gives way to her light (the rig's ember_give; her light's point and reach are PlayerView's); not under a camera rig: at the close view by night her lamp is off her, so the moon is her light (r1: night close Lp95 0.49 to 0.34 with it)
        var give = CelRigs && cam == null && p.EmberGive is [var gk, var gs, var g0, var g1] ? new Vector4((float)gk, (float)gs, (float)g0, (float)g1) : Vector4.Zero;
        RenderingServer.GlobalShaderParameterSet("cel_give", give);
        // (L1 lead 9, NIGHT2) how the moon gives way to the zone's fires and lamps (the rig's fire_give; their points: ZoneView.CelFires)
        var fgive = CelRigs && cam == null && p.FireGive is [var fk, var fs, var f0, var f1] ? new Vector4((float)fk, (float)fs, (float)f0, (float)f1) : Vector4.Zero;
        RenderingServer.GlobalShaderParameterSet("cel_fire_give", fgive);
        // (L1 lead 9, B1) her pool as light, a ramp in metres from her light's foot (the rig's ember_pool; cel.gdshaderinc
        // cel_pool_paint, cel_pool_ramp): [the canopy's dapple kept at its edge and at its core, then stops of r (m), level (over her light's energy),
        // color (sRGB 0-255)], FROM targets 09 and 12. Not under a camera rig (the close view's own light).
        var ramp = CelRigs && cam == null ? PoolRamp(p.EmberPool, p.EmberSmooth) : null;
        RenderingServer.GlobalShaderParameterSet("cel_pool_band", ramp is { } pr ? new Vector4(pr.Reach, pr.Core, (float)p.EmberPool![0], (float)p.EmberPool![1]) : Vector4.Zero);
        if (ramp is { } pr2) RenderingServer.GlobalShaderParameterSet("cel_pool_ramp", pr2.Tex);
        // (L1 lead 17, P) her fire on the floor as a turn of the floor's own tone (the rig's ember_floor; cel.gdshaderinc cel_floor_turn). Only with a ramp (what stands and the foes take it).
        var turn = ramp != null ? FloorTurn(p.EmberFloor) : null;
        RenderingServer.GlobalShaderParameterSet("cel_floor_band", turn is { } ft ? new Vector4(ft.Reach, ft.Lit.X, ft.Lit.Y, ft.Lit.Z) : Vector4.Zero);
        RenderingServer.GlobalShaderParameterSet("cel_floor_unit", turn is { } ft1 && p.EmberFloorLift is { Length: >= 1 } efl ? new Vector4(ft1.Paint.X, ft1.Paint.Y, ft1.Paint.Z, 1) * (float)efl[0] : Vector4.Zero);   // (lead 20, MASS, MASS3: the floor's reference paint inside her pool, rgb the table's floor color at the luminance w; cel_floor_paint)
        FireCast.Reach = turn?.Reach ?? 0;   // (L1 lead 19, SH2: a C# copy of the table's reach for --cast-count)
        if (turn is { } ft2) RenderingServer.GlobalShaderParameterSet("cel_floor_turn", ft2.Tex);
        // (L1 lead 19, HER2) the hero figure in her lit pool (the rig's hero_pool, Zone.HeroPool; cel.gdshaderinc CEL_HERO): the
        // pool light's foot beside her (PlayerView reads HeroFoot), and her shade side (away from the foot, and her under
        // planes) in ONE dark warm anchor tone. Not under a camera rig; a rig without the row: the light at (0, 0.4), no anchor.
        var hp = CelRigs && cam == null && p.HeroPool is { Length: >= 8 } hpr ? hpr : null;
        HeroFoot = hp != null ? new Vector2((float)hp[0], (float)hp[1]) : new Vector2(0, 0.4f);
        var toFoot = hp != null && HeroFoot.Length() > 0.05f ? HeroFoot.Normalized() : Vector2.Zero;
        HeroFootRig = hp != null; heroToFoot = toFoot; heroSide = hp != null ? (float)hp[6] : 0;   // (L1 lead 21, FOOT)
        RenderingServer.GlobalShaderParameterSet("cel_hero", hp != null && toFoot != Vector2.Zero ? new Vector4(toFoot.X, toFoot.Y, (float)hp[6], 1) : Vector4.Zero);
        var anchor = hp != null ? new Color((float)hp[3] / 255f, (float)hp[4] / 255f, (float)hp[5] / 255f).SrgbToLinear() * (float)hp[2] : new Color(0, 0, 0);
        RenderingServer.GlobalShaderParameterSet("cel_hero_tone", new Vector4(anchor.R, anchor.G, anchor.B, hp != null ? (float)hp[7] : 0));
        HeroLine(hp, toFoot != Vector2.Zero, anchor);   // (L1 lead 20, HER5) her line: values 8, 9
        // (L1 lead 19, HER3; CEL_HERO_ARM) her held pieces as bodies: row values 10-19 = the body's level, r, g, b, its side edge, the
        // warm light's level, r, g, b, the least screen width in px. A shorter row: both zero, her shield and blade as they were.
        var ha = hp is { Length: >= 20 } ? hp : null;
        Color HeroTone(int i) => ha != null ? new Color((float)ha[i + 1] / 255f, (float)ha[i + 2] / 255f, (float)ha[i + 3] / 255f).SrgbToLinear() * (float)ha[i] : new Color(0, 0, 0);
        Color armTone = HeroTone(10), litTone = HeroTone(15);
        RenderingServer.GlobalShaderParameterSet("cel_hero_arm", new Vector4(armTone.R, armTone.G, armTone.B, ha != null ? (float)ha[14] : 0));
        RenderingServer.GlobalShaderParameterSet("cel_hero_lit", new Vector4(litTone.R, litTone.G, litTone.B, ha != null ? (float)ha[19] : 0));
        // (L1 lead 20, HER4) she is a LIGHT figure: with the light the whole figure is the rig's absolute tones (CEL_HERO_FRAGMENT).
        // Values 20-26 = the mid step's level, r, g, b, its side edge, the share of a material's own hue, of its own value. Value 14
        // is now the held piece's away edge in metres. A row of 20: no mid, every material at the light's one color.
        var hm = ha is { Length: >= 27 } ? ha : null;
        var midTone = hm != null ? HeroTone(20) : new Color(0, 0, 0);
        RenderingServer.GlobalShaderParameterSet("cel_hero_mid", new Vector4(midTone.R, midTone.G, midTone.B, hm != null ? (float)hm[24] : 0));
        RenderingServer.GlobalShaderParameterSet("cel_hero_own", hm != null ? new Vector4((float)hm[25], (float)hm[26], hm.Length >= 29 ? (float)hm[27] : 0, hm.Length >= 29 ? (float)hm[28] : 0) : Vector4.Zero);   // (round 2: value 27 = the least lean the side test normalizes down to, 28 = a held piece's light as a share of hers)
        var hc = SurvivorUnchained.Look.Rigs.HeroChroma(hm);   // (L1 lead 21, CHROMA) values 29-34: the hero chroma rule (cel_hero_gain); zeros without them
        RenderingServer.GlobalShaderParameterSet("cel_hero_chroma", new Vector4((float)hc[0], (float)hc[1], (float)hc[2], (float)hc[3]));
        RenderingServer.GlobalShaderParameterSet("cel_hero_chroma_px", new Vector4((float)hc[4], (float)hc[5], (float)hc[6], 0));
        var hk = SurvivorUnchained.Look.Rigs.HeroClass(hm);   // (L1 lead 22, HERPAIR) values 36-44: her value pairs by material class (cel_hero_land); zeros without them
        RenderingServer.GlobalShaderParameterSet("cel_hero_class_lit", new Vector4((float)hk[0], (float)hk[2], (float)hk[4], (float)hk[6]));
        RenderingServer.GlobalShaderParameterSet("cel_hero_class_shade", new Vector4((float)hk[1], (float)hk[3], (float)hk[5], (float)hk[7]));
        RenderingServer.GlobalShaderParameterSet("cel_hero_class_keep", (float)hk[8]);
    }
    /// <summary>(L1 lead 20, HER5) Her LINE (hero_line.gdshader; CelLib.LineStep hangs it on her meshes): the row's value 8 = its
    /// width in px at 1080p, value 9 = its level against the anchor's tone. On as cel_hero is on; else 0 and nothing is drawn.</summary>
    public static float HeroLinePx;
    static void HeroLine(double[]? hp, bool on, Color anchor)
    {
        HeroLinePx = on && hp is { Length: >= 10 } ? (float)hp[8] : 0;
        var t = HeroLinePx > 0 ? anchor * (float)hp![9] : new Color(0, 0, 0);
        RenderingServer.GlobalShaderParameterSet("cel_hero_line", new Vector4(t.R, t.G, t.B, HeroLinePx));
    }
    /// <summary>(L1 lead 19, HER2) Where her pool light's foot sits, in metres from her (x, z): the rig's hero_pool, else (0, 0.4).</summary>
    public static Vector2 HeroFoot = new(0, 0.4f);
    /// <summary>(L1 lead 21, FOOT) True while the rig has the hero_pool row: HeroFoot is then (dx along screen-right, dz along
    /// screen-down) on the ground of the view, from her ground position, whatever her heading. Without the row HeroFoot is in
    /// her own frame, as before.</summary>
    public static bool HeroFootRig;
    static Vector2 heroToFoot; static float heroSide;
    /// <summary>(L1 lead 21, FOOT) The world xz direction from her to her light's foot, from the one site that places it
    /// (PlayerView's carried light): her shade side (cel_hero.xy) follows the same point under a turned camera. Sets the global
    /// only when the direction moved; nothing without the row or with the foot at her feet.</summary>
    public static void HeroFootWorld(Vector2 toFootWorld)
    {
        if (!HeroFootRig || heroToFoot == Vector2.Zero || toFootWorld.LengthSquared() < 1e-6f) return;
        var d = toFootWorld.Normalized();
        if (d.DistanceSquaredTo(heroToFoot) < 1e-8f) return;
        heroToFoot = d;
        RenderingServer.GlobalShaderParameterSet("cel_hero", new Vector4(d.X, d.Y, heroSide, 1));
    }

    /// <summary>(L1 lead 17, P) The floor's tone table from a rig's ember_floor (Zone.EmberFloor: [the floor's lit tone, its
    /// shade's (Oklab L, C, hue), the floor under one unit of her light (linear rgb), (r m, the moon's return, the gap's tone,
    /// the shade's tone) x n]): 64 x 2 texels over 0..the last stop; row 0 rgb the gap's tone over the floor's lit tone
    /// (linear, per channel: what turns the one into the other), row 1 the shade's over the floor's shade, a the moon's
    /// return. Tones run between stops in Oklab (so orange meets the floor's blue through red and violet, not through the
    /// pink of an RGB sum); the last stop is the floor's own tones (a turn of 1: nothing to meet, so no edge). Lit and Shade:
    /// her light's color x level that shows the floor's own lit tone and its shade's (she stands in for the moon where it
    /// gives way; under a leaf the sky stays whole and she adds nothing). Paint: the color of the floor the table was drawn for
    /// (the unit, at luminance 1; x ember_floor_lift it is the paint the floor takes inside her pool). Null: no table.</summary>
    internal static (ImageTexture Tex, float Reach, Vector3 Lit, Vector3 Paint)? FloorTurn(double[]? ef)
    {
        if (ef is not { Length: >= 25 } || (ef.Length - 9) % 8 != 0) return null;
        if (floorTurnOf != null && floorTurn != null && System.Linq.Enumerable.SequenceEqual(floorTurnOf, ef)) return floorTurn;
        floorTurnOf = (double[])ef.Clone();
        int n = (ef.Length - 9) / 8;
        Vector3 refL = OkLab(ef[0], ef[1], ef[2]), refS = OkLab(ef[3], ef[4], ef[5]);
        Vector3 linL = OkLin(refL), linS = OkLin(refS), unit = new((float)Math.Max(ef[6], 1e-4), (float)Math.Max(ef[7], 1e-4), (float)Math.Max(ef[8], 1e-4));
        var r = new float[n]; var g = new float[n]; var tl = new Vector3[n]; var ts = new Vector3[n];
        for (int i = 0; i < n; i++)
        {
            int k = 9 + i * 8; bool last = i == n - 1;
            r[i] = (float)ef[k]; g[i] = last ? 1f : Mathf.Clamp((float)ef[k + 1], 0, 1);
            tl[i] = last ? refL : OkLab(ef[k + 2], ef[k + 3], ef[k + 4]); ts[i] = last ? refS : OkLab(ef[k + 5], ef[k + 6], ef[k + 7]);
        }
        float reach = Mathf.Max(r[n - 1], 0.1f);
        const int W = 64;
        var img = Image.CreateEmpty(W, 2, false, Image.Format.Rgbaf);
        for (int x = 0; x < W; x++)
        {
            float d = reach * x / (W - 1);
            int j = 0; while (j < n - 2 && d > r[j + 1]) j++;
            float t = Mathf.Clamp((d - r[j]) / Mathf.Max(r[j + 1] - r[j], 1e-4f), 0, 1), a = Mathf.Lerp(g[j], g[j + 1], t);
            Vector3 l = OkLin(tl[j].Lerp(tl[j + 1], t)) / linL, s = OkLin(ts[j].Lerp(ts[j + 1], t)) / linS;
            img.SetPixel(x, 0, new Color(l.X, l.Y, l.Z, a)); img.SetPixel(x, 1, new Color(s.X, s.Y, s.Z, a));
        }
        floorTurn = (ImageTexture.CreateFromImage(img), reach, linL / unit, unit / Mathf.Max(unit.Dot(new Vector3(0.2126f, 0.7152f, 0.0722f)), 1e-4f));   // (Paint: the floor the table was drawn for, at luminance 1)
        return floorTurn;
    }
    static double[]? floorTurnOf;
    static (ImageTexture Tex, float Reach, Vector3 Lit, Vector3 Shade)? floorTurn;
    /// <summary>Oklab (L, a, b) of a tone given as L, chroma, hue (degrees); and its linear sRGB (floored just above 0).</summary>
    static Vector3 OkLab(double l, double c, double h) => new((float)l, (float)(c * Math.Cos(h * Math.PI / 180)), (float)(c * Math.Sin(h * Math.PI / 180)));
    static Vector3 OkLin(Vector3 o)
    {
        float l = o.X + 0.3963377774f * o.Y + 0.2158037573f * o.Z, m = o.X - 0.1055613458f * o.Y - 0.0638541728f * o.Z, s = o.X - 0.0894841775f * o.Y - 1.2914855480f * o.Z;
        l *= l * l; m *= m * m; s *= s * s;
        return new Vector3(Mathf.Max(4.0767416621f * l - 3.3077115913f * m + 0.2309699292f * s, 1e-4f),
            Mathf.Max(-1.2684380046f * l + 2.6097574011f * m - 0.3413193965f * s, 1e-4f), Mathf.Max(-0.0041960863f * l - 0.7034186147f * m + 1.7076147010f * s, 1e-4f));
    }

    /// <summary>(L1 lead 9, B1) Her pool's ramp from a rig's ember_pool ([dapple kept at the edge, at the core, (r m, level, R, G, B 0-255) x n], r rising,
    /// the last stop's level 0): 64 texels over 0..the last stop, rgb the level x the color (linear, largest channel 1), a the
    /// moon's give-way (the level over the core's). Levels and colors linear between stops (a cubic's overshoot would ring).
    /// (L1 lead 12, R4 round 4) smooth (rigs.json "ember_smooth"): the levels on a monotone cubic through the stops (Fritsch and
    /// Carlson: no overshoot, so no ring), flat at her feet and flat where it ends, so the field has no kink a stop could draw
    /// as a contour and its tail meets nothing without an edge. Null: no ramp (fewer than two stops).</summary>
    internal static (ImageTexture Tex, float Reach, float Core)? PoolRamp(double[]? ep, bool smooth = false)
    {
        if (ep is not { Length: >= 12 } || (ep.Length - 2) % 5 != 0) return null;
        // (the last one built, kept: the air's glide sets the cel globals every frame)
        if (poolRampOf != null && poolRamp != null && poolRampSmooth == smooth && System.Linq.Enumerable.SequenceEqual(poolRampOf, ep)) return poolRamp;
        poolRampOf = (double[])ep.Clone(); poolRampSmooth = smooth;
        poolRamp = BuildPoolRamp(ep, smooth);
        return poolRamp;
    }
    static double[]? poolRampOf;
    static bool poolRampSmooth;
    static (ImageTexture Tex, float Reach, float Core)? poolRamp;

    /// <summary>(L1 lead 21 QUIT) The static textures (the pool ramp, the floor's turn table, the stand palette, the grade
    /// LUTs) let go at the quit, in QuitPath's last step before the tree quits: as statics they lived until the .NET
    /// shutdown, after the tree. What still draws with one holds its own reference; a later ask builds it again.</summary>
    internal static void ReleaseStatics()
    {
        var all = new List<Texture?> { poolRamp?.Tex, floorTurn?.Tex, standPal };
        all.AddRange(luts.Values);
        poolRamp = null; poolRampOf = null; floorTurn = null; floorTurnOf = null; standPal = null; luts.Clear();
        foreach (var t in all)
            if (t != null && IsInstanceValid(t)) t.Dispose();
    }
    static (ImageTexture Tex, float Reach, float Core) BuildPoolRamp(double[] ep, bool smooth)
    {
        int n = (ep.Length - 2) / 5;
        var r = new float[n]; var lv = new float[n]; var c = new Color[n];
        for (int i = 0; i < n; i++)
        {
            int k = 2 + i * 5;
            r[i] = (float)ep[k]; lv[i] = (float)ep[k + 1];
            var cl = new Color((float)ep[k + 2] / 255f, (float)ep[k + 3] / 255f, (float)ep[k + 4] / 255f).SrgbToLinear();
            float mx = Mathf.Max(cl.R, Mathf.Max(cl.G, Mathf.Max(cl.B, 1e-4f)));
            c[i] = new Color(cl.R / mx, cl.G / mx, cl.B / mx);
        }
        float reach = Mathf.Max(r[n - 1], 0.1f), core = Mathf.Max(lv[0], 1e-3f);
        // (smooth: each stop's slope, the harmonic mean of its two sides' (0 where they turn), 0 at both ends)
        var sl = new float[n];
        if (smooth)
            for (int i = 1; i < n - 1; i++)
            {
                float h0 = Mathf.Max(r[i] - r[i - 1], 1e-4f), h1 = Mathf.Max(r[i + 1] - r[i], 1e-4f);
                float d0 = (lv[i] - lv[i - 1]) / h0, d1 = (lv[i + 1] - lv[i]) / h1;
                if (d0 * d1 <= 0) continue;
                float w1 = 2 * h1 + h0, w2 = h1 + 2 * h0;
                sl[i] = (w1 + w2) / (w1 / d0 + w2 / d1);
            }
        const int W = 64;
        var img = Image.CreateEmpty(W, 1, false, Image.Format.Rgbaf);
        for (int x = 0; x < W; x++)
        {
            float d = reach * x / (W - 1);
            int j = 0; while (j < n - 2 && d > r[j + 1]) j++;
            float t = Mathf.Clamp((d - r[j]) / Mathf.Max(r[j + 1] - r[j], 1e-4f), 0, 1);
            float l = Mathf.Lerp(lv[j], lv[j + 1], t);
            if (smooth)
            {
                float hh = Mathf.Max(r[j + 1] - r[j], 1e-4f), t2 = t * t, t3 = t2 * t;
                l = Mathf.Max((2 * t3 - 3 * t2 + 1) * lv[j] + (t3 - 2 * t2 + t) * hh * sl[j] + (-2 * t3 + 3 * t2) * lv[j + 1] + (t3 - t2) * hh * sl[j + 1], 0);
            }
            var col = c[j].Lerp(c[j + 1], t);
            img.SetPixel(x, 0, new Color(col.R * l, col.G * l, col.B * l, Mathf.Clamp(l / core, 0, 1)));
        }
        return (ImageTexture.CreateFromImage(img), reach, core);
    }

    /* ---------------------------------------------------- the grade's glide (H4) -- */

    /// <summary>The grade table this air and the view's settings make (what Set shows).</summary>
    public ImageTexture3D LutFor(AtmospherePreset p) => GradeLut(Cine(ViewGrade(Own(p))), Mute, SkinGuardFor(p), ViewShadeHue, ViewSkinCool);

    // A table shown is switched at once, except inside a glide's window (a cinematic's hand-back: GameSeam), when it
    // blends in from what was on screen over the glide's time (a mix of the two tables' bytes, one 3D texture reused).
    double glideFor, glideWindow, blendT, blendDur;
    byte[]? blendFrom, blendTo, blendMix;
    ImageTexture3D? blendTarget, blendTex;
    static readonly Dictionary<ulong, byte[]> lutBytes = new();

    /// <summary>For the next window seconds, a new table blends in over seconds (a blend running is stretched to it).</summary>
    public void GlideLuts(double seconds, double window)
    {
        glideFor = seconds; glideWindow = window;
        if (blendTarget != null) blendDur = Math.Max(blendDur, seconds);
    }

    static byte[] Bytes(ImageTexture3D t)
    {
        if (lutBytes.TryGetValue(t.GetInstanceId(), out var b)) return b;
        var all = new List<byte>();
        foreach (var im in t.GetData()) all.AddRange(im.GetData());
        return lutBytes[t.GetInstanceId()] = all.ToArray();
    }

    /// <summary>The bytes of the table on screen now (a blend's mix as it stands), or null.</summary>
    public byte[]? LutShown() => Env.AdjustmentColorCorrection is ImageTexture3D cur
        ? (cur == blendTex ? (byte[]?)blendMix?.Clone() : Bytes(cur)) : null;

    void ShowLut(ImageTexture3D lut)
    {
        if (GradeOff) return;
        if (blendTarget == lut) return;
        if (glideWindow > 0 && Env.AdjustmentColorCorrection != lut && LutShown() is { } from)
        {
            blendFrom = from; blendTo = Bytes(lut); blendTarget = lut; blendT = 0; blendDur = glideFor;
            WriteMix(0);
            return;
        }
        blendTarget = null;
        Env.AdjustmentColorCorrection = lut;
    }

    /// <summary>A mix of a table as it was (LutShown) and another, k of the way (an atmosphere cue's blend: GameCinema).</summary>
    public void MixLuts(byte[] from, ImageTexture3D to, float k)
    {
        if (GradeOff) return;
        if (k >= 1) { blendTarget = null; Env.AdjustmentColorCorrection = to; return; }
        blendTarget = null; blendFrom = from; blendTo = Bytes(to);
        WriteMix(k);
    }

    void WriteMix(float k)
    {
        var a = blendFrom!; var b = blendTo!;
        if (a.Length != b.Length) { Env.AdjustmentColorCorrection = blendTarget; blendTarget = null; return; }
        blendMix ??= new byte[a.Length];
        if (blendMix.Length != a.Length) blendMix = new byte[a.Length];
        for (int i = 0; i < a.Length; i++) blendMix[i] = (byte)Math.Clamp((int)(a[i] + (b[i] - a[i]) * k + 0.5f), 0, 255);
        int slice = LutSize * LutSize * 3;
        var slices = new Godot.Collections.Array<Image>();
        for (int z = 0; z < LutSize; z++) slices.Add(Image.CreateFromData(LutSize, LutSize, false, Image.Format.Rgb8, blendMix.AsSpan(z * slice, slice).ToArray()));
        if (blendTex == null) { blendTex = new ImageTexture3D(); blendTex.Create(Image.Format.Rgb8, LutSize, LutSize, LutSize, false, slices); }
        else blendTex.Update(slices);
        Env.AdjustmentColorCorrection = blendTex;
    }

    /// <summary>Once a frame: a glide's blend moves on.</summary>
    public void GradeTick(double dt)
    {
        glideWindow = Math.Max(0, glideWindow - dt);
        if (blendTarget == null) return;
        blendT += dt;
        float k = Mathf.SmoothStep(0, 1, (float)Math.Clamp(blendT / Math.Max(blendDur, 1e-3), 0, 1));
        if (k >= 1) { Env.AdjustmentColorCorrection = blendTarget; blendTarget = null; return; }
        WriteMix(k);
    }

    SurvivorUnchained.Maps.ArenaAir? air;
    string airPlace = "", airMood = "";

    /// <summary>A place's own air (an ember arena's), or none; applied with the next Set.</summary>
    public void Air(SurvivorUnchained.Maps.ArenaAir? a, string place = "", string mood = "")
    {
        air = a; airPlace = place; airMood = mood;
        Set(Current);
    }

    /* -------------------------------------------------------------- grade -- */

    const int LutSize = 32;
    static readonly Dictionary<string, ImageTexture3D> luts = new();

    /// <summary>The web game's grade (render/grade.ts) as a lookup table:
    /// sRGB in (what Godot hands its colour correction after tone mapping),
    /// sRGB out.</summary>
    public static ImageTexture3D GradeLut(GradeSettings g, float mute, float skinGuard = 0, float shadeHue = 0, float skinCool = 0)
    {
        if (Try?.Mute is float tm) mute = tm;
        var key = $"{SurvivorUnchained.Core.Json.Write(g)}|{mute}|{skinGuard}|{shadeHue}|{skinCool}";
        if (luts.TryGetValue(key, out var hit)) return hit;
        static Vector3 Hex(string h) { var c = new Color(h); return new Vector3(c.R, c.G, c.B); }
        var lift = new Vector3((float)g.Lift[0], (float)g.Lift[1], (float)g.Lift[2]);
        var gamma = new Vector3((float)g.Gamma[0], (float)g.Gamma[1], (float)g.Gamma[2]);
        var gain = new Vector3((float)g.Gain[0], (float)g.Gain[1], (float)g.Gain[2]);
        // The web game's uniforms take three.js colours: linear.
        var shT = Lin(Hex(g.ShadowTint)); var hiT = Lin(Hex(g.HighlightTint));
        float tintHue = Oklab(shT).Z;
        // --grade-toe X: the toe hold for pictures (0, the grade before it).
        float toe = SurvivorUnchained.Args.Has("grade-toe") ? SurvivorUnchained.Args.Num("grade-toe", 1f) : (float)g.Toe;
        var paint = new Paint(g, Try);
        float tint = (float)g.TintStrength, sat = (float)g.Saturation, vibr = (float)g.Vibrance, con = (float)g.Contrast;
        // (L1 W2: the tone curve on Oklab L, tabled once per grade)
        float[]? tone = null;
        if (g.Curve is { Length: >= 4 } gc)
        {
            tone = new float[257];
            for (int i = 0; i <= 256; i++) tone[i] = (float)SurvivorUnchained.World.Atmospheres.ToneCurve(gc, i / 256.0);
        }
        // (The table is worked out on the worker threads, a blue slice each, into bytes, then made one image per slice:
        // 32^3 Image.SetPixel calls and the sums on the main thread held a frame ~100 ms when a cinematic's
        // atmosphere moved the grade (C04 A at 9 s). Each byte is what SetPixel wrote for RGB8: the channel times 255, clamped, truncated.)
        var data = new byte[LutSize][];
        System.Threading.Tasks.Parallel.For(0, LutSize, b =>
        {
            var px = data[b] = new byte[LutSize * LutSize * 3];
            for (int gi = 0; gi < LutSize; gi++)
                for (int r = 0; r < LutSize; r++)
                {
                    var input = new Vector3((r + 0.5f) / LutSize, (gi + 0.5f) / LutSize, (b + 0.5f) / LutSize);
                    var c = Lin(input);
                    var p = Pow(c, 1 / 2.2f);
                    p = gain * (p + lift * (Vector3.One - p));
                    p = Pow(Max0(p), new Vector3(1 / Mathf.Max(gamma.X, 0.01f), 1 / Mathf.Max(gamma.Y, 0.01f), 1 / Mathf.Max(gamma.Z, 0.01f)));
                    var s = p - new Vector3(0.5f, 0.5f, 0.5f);
                    p = new Vector3(0.5f, 0.5f, 0.5f) + new Vector3(
                        s.X * con / (1 + Mathf.Abs(s.X) * (con - 1) * 1.2f),
                        s.Y * con / (1 + Mathf.Abs(s.Y) * (con - 1) * 1.2f),
                        s.Z * con / (1 + Mathf.Abs(s.Z) * (con - 1) * 1.2f));
                    float l = Luma(p);
                    float sh = 1 - Smooth(0, 0.55f, l), hi = Smooth(0.45f, 1, l);
                    // The shadow tint (the web game's sum) also darkens: in the dark it took an iris, dark hair and
                    // unlit ground to black. In the toe its lightness is held (Toe), so it stays a colour there: the moon's
                    // blue over detail. It fades in from black (true black stays black) to full at a gamma luma of 0.14, and out by 0.35.
                    var shade = (shT - new Vector3(0.5f, 0.5f, 0.5f)) * sh * tint;
                    float held = toe * Smooth(ToeFoot, 0.14f, l) * (1 - Smooth(0.14f, 0.35f, l));
                    p += shade - Vector3.One * Luma(shade) * held;
                    p += (hiT - new Vector3(0.5f, 0.5f, 0.5f)) * hi * tint;
                    l = Luma(p);
                    float spread = Mathf.Max(Mathf.Max(p.X, p.Y), p.Z) - Mathf.Min(Mathf.Min(p.X, p.Y), p.Z);
                    float vib = 1 + vibr * (1 - spread);
                    p = new Vector3(l, l, l).Lerp(p, sat * vib);
                    float peak = Mathf.Max(Mathf.Max(p.X, p.Y), p.Z);
                    float keep = Smooth(0.62f, 0.95f, peak);
                    l = Luma(p);
                    p = new Vector3(l, l, l).Lerp(p, 1 - mute * (1 - keep));
                    var outLin = Pow(p.Clamp(Vector3.Zero, Vector3.One), 2.2f);
                    if (!OldGrade) outLin = KeepHue(c, outLin, tintHue);
                    if (toe > 0) outLin = ToeColour(c, outLin, toe);
                    if (g.Moon > 0 && !(g.SceneColor > 0 && g.SceneMoon > 0)) outLin = Moonlight(c, outLin, g);
                    if (paint.On) outLin = paint.Apply(outLin);
                    if (skinGuard > 0) outLin = SkinGuard(outLin, skinGuard);
                    if (shadeHue > 0) outLin = ShadeHue(outLin, shadeHue);
                    if (skinCool > 0) outLin = SkinCool(c, outLin, skinCool);
                    if (g.WarmKeep > 0) outLin = WarmSource(c, outLin, g);
                    if (tone != null) outLin = Tone(outLin, tone);
                    if (g.SceneColor > 0) outLin = SceneColour(c, outLin, (float)g.SceneColor);
                    // (L1 lead 7, S2: GradeSettings.SceneMoon, the moon's blue (dawn's lilac) over the scene's own color)
                    if (g.SceneColor > 0 && g.SceneMoon > 0 && g.Moon > 0) outLin = Moonlight(c, outLin, g);
                    var o = Srgb(outLin);
                    int at = (gi * LutSize + r) * 3;
                    px[at] = Byte8(o.X); px[at + 1] = Byte8(o.Y); px[at + 2] = Byte8(o.Z);
                }
        });
        var slices = new Godot.Collections.Array<Image>();
        for (int b = 0; b < LutSize; b++) slices.Add(Image.CreateFromData(LutSize, LutSize, false, Image.Format.Rgb8, data[b]));
        // --grade-dump FILE: the table's bytes (blue-major slices, RGB8), to check it outside the game.
        if (SurvivorUnchained.Args.Get("grade-dump") is { } dump)
        {
            var bytes = new List<byte>();
            foreach (var im in slices) bytes.AddRange(im.GetData());
            System.IO.File.WriteAllBytes(dump, bytes.ToArray());
        }
        var tex = new ImageTexture3D();
        tex.Create(Image.Format.Rgb8, LutSize, LutSize, LutSize, false, slices);
        luts[key] = tex;
        return tex;
    }

    /// <summary>Rendering 2 (judge j1 E3, "deep skin goes copper or rust-red under warm keys"): the skin guard. In the red-orange
    /// skin band (Oklab hue SkinGuardHue), the strong chroma a warm key gives skin is taken down, up to SkinGuardCut of it, its hue
    /// and lightness held: copper-red deep skin back to brown; fair skin's low chroma (peach) mostly kept, as the cut fades in over
    /// SkinGuardC. Only where the camera is on her (the close view at night, dawn and dusk; the Look): it would grey the world's
    /// firelit wood and earth. --skin-guard-cut X, --skin-guard-c LO,HI (Oklab chroma), --skin-guard-hue A,B,C,D (the band's ramps).</summary>
    static readonly float SkinGuardCut = SurvivorUnchained.Args.Num("skin-guard-cut", 0.25f);
    static readonly float[] SkinGuardC = Floats("skin-guard-c", 0.05f, 0.11f), SkinGuardHue = Floats("skin-guard-hue", 15f, 30f, 72f, 90f);
    static float[] Floats(string name, params float[] d) => SurvivorUnchained.Args.Get(name) is string v && v.Split(',') is { } p && p.Length == d.Length
        ? Array.ConvertAll(p, x => float.Parse(x, System.Globalization.CultureInfo.InvariantCulture)) : d;
    static Vector3 SkinGuard(Vector3 c, float k)
    {
        var o = Oklab(c);
        float w = Smooth(SkinGuardHue[0], SkinGuardHue[1], o.Z) * (1 - Smooth(SkinGuardHue[2], SkinGuardHue[3], o.Z))
            * Smooth(SkinGuardC[0], SkinGuardC[1], o.Y) * Smooth(0.12f, 0.25f, o.X) * (1 - Smooth(0.9f, 0.98f, o.X));
        if (w <= 0) return c;
        float ch = o.Y * (1 - SkinGuardCut * k * w), h = Mathf.DegToRad(o.Z);
        return FromOklab(o.X, ch * Mathf.Cos(h), ch * Mathf.Sin(h)).Clamp(Vector3.Zero, Vector3.One);
    }
    /// <summary>Face 48 round 4: her shade's hue floor in a cinematic (GameCinemaHer, SetViewShadeHue). The night grade's shadow
    /// tint took her shade's Oklab hue to 37-39 (pink-grey; with the grade off, 43-45), and no light on her moved it. In the skin
    /// band (hue ShadeHueFrom to ShadeHueFloor, chroma 0.02 up, lightness 0.2-0.8) the hue is lifted toward ShadeHueFloor, none
    /// below ShadeHueFrom (her lips, red cloth): her shade reads skin, not lilac. 0 (everywhere but a close cinematic
    /// shot of her by night): as before. --cine-her-shade-hue FROM,FLOOR.</summary>
    static readonly float[] ShadeHueAt = Floats("cine-her-shade-hue", 24f, 44f);
    static Vector3 ShadeHue(Vector3 c, float k)
    {
        var o = Oklab(c);
        float from = ShadeHueAt[0], floor = ShadeHueAt[1];
        if (o.Z <= from || o.Z >= floor) return c;
        float w = k * Smooth(from, from + 6, o.Z) * Smooth(0.015f, 0.03f, o.Y) * Smooth(0.2f, 0.3f, o.X) * (1 - Smooth(0.75f, 0.85f, o.X));
        if (w <= 0) return c;
        float h = Mathf.DegToRad(Mathf.Lerp(o.Z, floor, w));
        return FromOklab(o.X, o.Y * Mathf.Cos(h), o.Y * Mathf.Sin(h)).Clamp(Vector3.Zero, Vector3.One);
    }
    /// <summary>Face 49 (cool-light skin): her skin under a cool key in a close cinematic shot (GameCinemaHer, SetViewSkinCool). The
    /// grade's lifts for the weakly coloured (the saturation's vibrance, the warm highlight tint, the paint grade's vibrance and
    /// highlight boost, which spare skin only at a warm key's chroma) took her moonlit or lantern-lit skin from the render's
    /// Oklab chroma 0.025 back to 0.049 at its warm hue (C02 s8): bronze, the one warm thing in a night frame. Here what the
    /// render made of skin-coloured light (skin's hues, input chroma 0.012 up to SkinCoolC: a fire's glow keeps the grade) takes
    /// the grade's colour at SkinCoolSat of its chroma where lit, SkinCoolShade in the darks (a cool key's shade falls
    /// neutral-dark, not brown), its hue and lightness the grade's. 0 (everywhere but a close shot of her under a cool key): as before.
    /// --cine-her-cool-sat S, --cine-her-cool-shade D, --cine-her-cool-c C0,C1.</summary>
    static readonly float SkinCoolSat = SurvivorUnchained.Args.Num("cine-her-cool-sat", 0.55f), SkinCoolShade = SurvivorUnchained.Args.Num("cine-her-cool-shade", 0.6f);
    static readonly float[] SkinCoolC = Floats("cine-her-cool-c", 0.09f, 0.13f);
    static Vector3 SkinCool(Vector3 inLin, Vector3 outLin, float k)
    {
        var i = Oklab(inLin); var o = Oklab(outLin);
        if (i.X < 0.08f || o.X > 0.97f) return outLin;
        // (skin's hues only: the weakly coloured without one, the moonlit water and sky, keep the grade's moon blue)
        float band = Smooth(5, 15, i.Z) * (1 - Smooth(100, 115, i.Z)) * Smooth(0.006f, 0.012f, i.Y);
        float w = k * band * (1 - Smooth(SkinCoolC[0], SkinCoolC[1], i.Y)) * Smooth(0.08f, 0.16f, i.X) * (1 - Smooth(0.88f, 0.97f, o.X));
        if (w <= 0) return outLin;
        // (the grade's own chroma scaled alike over her face: the render's, taken whole, showed her cheeks' paint as rouge on a pale
        // face, C02 s4; the grade had evened it)
        float f = 1 - w * (1 - Mathf.Lerp(SkinCoolShade, SkinCoolSat, Smooth(0.3f, 0.5f, i.X)));
        float oh = Mathf.DegToRad(o.Z);
        return FromOklab(o.X, o.Y * f * Mathf.Cos(oh), o.Y * f * Mathf.Sin(oh)).Clamp(Vector3.Zero, Vector3.One);
    }
    public float ViewSkinCool { get; private set; }
    public void SetViewSkinCool(float k)
    {
        k = Mathf.Round(Mathf.Clamp(k, 0, 1) * 4) / 4;
        if (Mathf.IsEqualApprox(k, ViewSkinCool)) return;
        ViewSkinCool = k;
        var lut = GradeLut(Cine(ViewGrade(Own(Current))), Mute, SkinGuardFor(Current), ViewShadeHue, ViewSkinCool);
        ShowLut(lut);
    }
    public float ViewShadeHue { get; private set; }
    public void SetViewShadeHue(float k)
    {
        k = Mathf.Round(Mathf.Clamp(k, 0, 1) * 4) / 4;
        if (Mathf.IsEqualApprox(k, ViewShadeHue)) return;
        ViewShadeHue = k;
        var lut = GradeLut(Cine(ViewGrade(Own(Current))), Mute, SkinGuardFor(Current), ViewShadeHue, ViewSkinCool);
        ShowLut(lut);
    }
    /// <summary>The skin guard's share for this air (0 to 1): the Look's (Atmospheres.Front) whole, else the close view's (SetViewSkinGuard).</summary>
    float SkinGuardFor(AtmospherePreset p) => SkinGuardOff ? 0 : IsFront(p) ? 1 : ViewSkinGuard;
    static readonly bool SkinGuardOff = SurvivorUnchained.Args.Has("skin-guard-off");
    /// <summary>The close view's say over the skin guard (0 to 1, in quarter steps, each table made once; GameCloseUp).</summary>
    public float ViewSkinGuard { get; private set; }
    public void SetViewSkinGuard(float k)
    {
        k = Mathf.Round(Mathf.Clamp(k, 0, 1) * 4) / 4;
        if (Mathf.IsEqualApprox(k, ViewSkinGuard)) return;
        ViewSkinGuard = k;
        var lut = GradeLut(Cine(ViewGrade(Own(Current))), Mute, SkinGuardFor(Current), ViewShadeHue, ViewSkinCool);
        ShowLut(lut);
    }

    /// <summary>A channel as Image.SetPixel stores it in RGB8 (Godot: uint8_t(CLAMP(c * 255.0, 0, 255))).</summary>
    static byte Byte8(float c) => (byte)Math.Clamp(c * 255.0, 0.0, 255.0);

    /// <summary>--grade-old: the grade before KeepHue, for before-and-after pictures.</summary>
    static readonly bool OldGrade = SurvivorUnchained.Args.Has("grade-old");

    /// <summary>The shadow tint adds blue in gamma (the web game's sum), and in the dark it outweighs a
    /// colour's own chroma: dark browns (irises, lashes, brows, leather) came out purple. Here the
    /// grade keeps its brightness and its blue on greys, cool colours and greens, but a warm colour's hue may
    /// turn at most 6 degrees (Oklab), and where the grade darkens it, it may not grow more
    /// saturated than it came in (the blue shade reads as a darker, greyer brown, not a purple).</summary>
    /// <summary>--grade-sat-lo, --grade-sat-hi: the saturation band over which mid-tones are held (pictures).</summary>
    static readonly float SatLo = SurvivorUnchained.Args.Num("grade-sat-lo", 0.025f), SatHi = SurvivorUnchained.Args.Num("grade-sat-hi", 0.06f);
    static Vector3 KeepHue(Vector3 inLin, Vector3 outLin, float tintHue)
    {
        var i = Oklab(inLin); var o = Oklab(outLin);
        float sat = i.Y / Mathf.Max(i.X, 1e-4f);
        float side = Mathf.Wrap(i.Z - tintHue, -180, 180);
        // Greys have no hue to keep; colours near the tint's own hue may go bluer, and so may
        // greens, which turn toward it through cyan (moonlit leaves go teal, as before). Only
        // the warm side, whose turn runs through magenta, is held.
        float green = side < 0 ? Smooth(-160, -140, side) : 0;
        float warm = Smooth(45, 90, Mathf.Abs(side)) * (1 - green);
        // Mid-tones (skin in shade, L about 0.45) are held from a lower saturation than the dark
        // near-greys of ground and stone, which keep more of the moon's blue.
        float mid = Smooth(0.3f, 0.42f, i.X);
        float w = Smooth(Mathf.Lerp(0.04f, SatLo, mid), Mathf.Lerp(0.12f, SatHi, mid), sat) * warm;
        // Faintly warm darks (black brows, near-grey browns) still half take the old turn: where
        // it lands on violet (red over blue), the red goes, so they reach the greys' navy.
        float violet = warm * Smooth(0.01f, 0.04f, sat);
        if (w <= 0 && violet <= 0) return outLin;
        float turn = Mathf.Clamp(Mathf.Wrap(o.Z - i.Z, -180, 180), -6, 6);
        // The cap fades in over 0.02 of lightness as the grade starts to darken, so no step shows.
        float chroma = Mathf.Lerp(o.Y, Mathf.Min(o.Y, sat * o.X), Smooth(0, 0.02f, i.X - o.X));
        float h0 = Mathf.DegToRad(o.Z), h1 = Mathf.DegToRad(i.Z + turn);
        float a = Mathf.Lerp(o.Y * Mathf.Cos(h0), chroma * Mathf.Cos(h1), w);
        float b = Mathf.Lerp(o.Y * Mathf.Sin(h0), chroma * Mathf.Sin(h1), w);
        if (a > 0 && b < 0) a *= 1 - violet * Smooth(0, 0.015f, -b);
        return FromOklab(o.X, a, b).Clamp(Vector3.Zero, Vector3.One);
    }

    /// <summary>In the toe the grade keeps a dark's own colour: the shadow tint's blue and the lift's, held off its
    /// darkening there (Toe), would turn black navy, dark brown hair violet-grey and the pupils slate. So a dark keeps the
    /// hue and chroma it came in with (scaled to its new lightness): wholly where it has a colour of its own (hair,
    /// irises, leather, ember ground) and near black; a neutral mid-dark keeps a little over half of the moon's blue.</summary>
    /// <summary>--toe-foot, --toe-own, --toe-chroma: where the hold starts, and ToeColour's neutral share and chroma ramp (pictures).</summary>
    static readonly float ToeFoot = SurvivorUnchained.Args.Num("toe-foot", 0.0f), ToeOwn = SurvivorUnchained.Args.Num("toe-own", 0.45f), ToeChroma = SurvivorUnchained.Args.Num("toe-chroma", 0.04f);
    static Vector3 ToeColour(Vector3 inLin, Vector3 outLin, float toe)
    {
        var i = Oklab(inLin); var o = Oklab(outLin);
        // (whole at any strength of the hold: at half, the blue kept with half the darkening turned dark hair violet)
        float zone = 1 - Smooth(0.35f, 0.55f, i.X);
        if (zone <= 0) return outLin;
        // (gently in chroma: the table's neighbouring points differ by about 0.015 of it, and a steeper step made a neutral
        // ramp's blue zigzag between them)
        float own = ToeOwn + (1 - ToeOwn) * (1 - Smooth(0.12f, 0.3f, i.X));
        float w = zone * (own + (1 - own) * Smooth(0, ToeChroma, i.Y));
        float s = Mathf.Min(o.X / Mathf.Max(i.X, 1e-4f), 1.2f);
        float ih = Mathf.DegToRad(i.Z), oh = Mathf.DegToRad(o.Z);
        float a = Mathf.Lerp(o.Y * Mathf.Cos(oh), i.Y * s * Mathf.Cos(ih), w);
        float b = Mathf.Lerp(o.Y * Mathf.Sin(oh), i.Y * s * Mathf.Sin(ih), w);
        return FromOklab(o.X, a, b).Clamp(Vector3.Zero, Vector3.One);
    }

    /// <summary>GradeSettings.MoonSkin's hue band (Oklab degrees on the input: in over [0]..[1], out over [2]..[3]): her skin in
    /// shade at the Look runs h 34-55 before the grade; the camp's earth behind her 53-87 (p5-p95), which keeps the moon's blue
    /// (at the paint grade's 15-90 band it went warm brown over the Look's lower third). --moon-skin-hue A,B,C,D.</summary>
    static readonly float[] MoonSkinHue = Floats("moon-skin-hue", 15f, 25f, 50f, 62f);
    /// <summary>GradeSettings.Moon: the moon's (or the dawn shade's) cool colour over what is weakly coloured.</summary>
    /// <summary>(L1 W2, bible rules 1, 3, 4) The warm-source term: what a warm light lit (input hue WarmHue +-WarmWidth, its
    /// chroma over 0.10-0.18 of its L, not black) keeps WarmKeep of the chroma (as a share of its L) and the hue the renderer
    /// gave it, at the lightness the grade gave it: her pool, a lamp's and a fire's keep the light's own color past the
    /// grade's mute, moon step and vibrance clamp. The surfaces' dull colors are not touched (no vibrance raise).</summary>
    static Vector3 WarmSource(Vector3 inLin, Vector3 outLin, GradeSettings g)
    {
        var i = Oklab(inLin);
        float dh = Mathf.Abs(Mathf.PosMod(i.Z - (float)g.WarmHue + 180f, 360f) - 180f), wid = (float)g.WarmWidth;
        float w = (float)g.WarmKeep * (1 - Smooth(wid * 0.6f, wid, dh)) * Smooth(0.10f, 0.18f, i.Y / Mathf.Max(i.X, 1e-4f)) * Smooth(0.04f, 0.12f, i.X);
        if (w <= 0) return outLin;
        var o = Oklab(outLin);
        float ct = i.Y * o.X / Mathf.Max(i.X, 1e-4f), c1 = Mathf.Lerp(o.Y, Mathf.Max(o.Y, ct), w);
        float dz = Mathf.PosMod(i.Z - o.Z + 180f, 360f) - 180f, h = Mathf.DegToRad(o.Z + dz * w);
        return InGamut(o.X, c1 * Mathf.Cos(h), c1 * Mathf.Sin(h));
    }

    /// <summary>(L1 lead 7, S1) GradeSettings.SceneColor: the scene's own channel ratios (what AgX was given: Godot 4.5.1's
    /// tonemap_agx run backward from the table's input) at the lightness the grade gave (its Oklab L), chroma taken in only
    /// where that leaves the gamut; k of it over the grade's color.</summary>
    static Vector3 SceneColour(Vector3 inLin, Vector3 outLin, float k)
    {
        var s = AgxBack(inLin);
        var os = OklabAb(s);
        var o = Oklab(outLin);
        if (os.X < 1e-4f || o.X < 1e-4f) return outLin;
        float f = o.X / os.X;  // (Oklab's L, a and b all scale as the cube root of a linear scale: the ratios held)
        var t = InGamut(o.X, os.Y * f, os.Z * f);
        return k >= 1 ? t : outLin.Lerp(t, k);
    }
    /// <summary>Linear sRGB to Oklab as (L, a, b).</summary>
    static Vector3 OklabAb(Vector3 c)
    {
        var o = Oklab(c); float h = Mathf.DegToRad(o.Z);
        return new(o.X, o.Y * Mathf.Cos(h), o.Y * Mathf.Sin(h));
    }
    // Godot 4.5.1's tonemap_agx (servers/rendering/renderer_rd/shaders/effects/tonemap.glsl, read from the engine's own
    // build): the inset and outset matrices (GLSL's column-major mat3, here row-major), the log2 range and the sigmoid's polynomial.
    static readonly float[] AgxInset = { 0.54490813676f, 0.37377945960f, 0.08138497669f, 0.14044005884f, 0.75410959864f, 0.10543358537f, 0.08882741185f, 0.17887712465f, 0.73224999957f };
    static readonly float[] AgxOutset = { 1.96455096027f, -0.85585845118f, -0.10886710827f, -0.29932243391f, 1.32645107415f, -0.02708402098f, -0.16436833806f, -0.23822464069f, 1.40266534714f };
    const float AgxMinEv = -12.4739311883324f, AgxMaxEv = 4.02606881166759f;
    static readonly float[] AgxInsetInv = Inv3(AgxInset), AgxOutsetInv = Inv3(AgxOutset);
    static float AgxSig(float x) { float x2 = x * x, x4 = x2 * x2; return 0.021f * x + 4.0111f * x2 - 25.682f * x2 * x + 70.359f * x4 - 74.778f * x4 * x + 27.069f * x4 * x2; }
    static readonly float[] AgxSigY = BuildSig();
    static float[] BuildSig() { var y = new float[4097]; for (int i = 0; i <= 4096; i++) y[i] = AgxSig(i / 4096f); return y; }
    static float AgxSigInv(float y)
    {
        if (y <= AgxSigY[0]) return 0; if (y >= AgxSigY[4096]) return 1;
        int lo = 0, hi = 4096;
        while (hi - lo > 1) { int m = (lo + hi) >> 1; if (AgxSigY[m] <= y) lo = m; else hi = m; }
        return (lo + (y - AgxSigY[lo]) / Mathf.Max(AgxSigY[hi] - AgxSigY[lo], 1e-9f)) / 4096f;
    }
    /// <summary>AgX's output (linear sRGB, as the grade's table gets it) back to its input (linear sRGB times the exposure).</summary>
    internal static Vector3 AgxBack(Vector3 c)
    {
        var t = Mul3(AgxOutsetInv, c);
        Vector3 v = default;
        for (int i = 0; i < 3; i++)
        {
            float x = AgxSigInv(Mathf.Pow(Mathf.Clamp(t[i], 0, 1), 1 / 2.4f));
            v[i] = Mathf.Pow(2, x * (AgxMaxEv - AgxMinEv) + AgxMinEv);
        }
        return Max0(Mul3(AgxInsetInv, v));
    }
    internal static Vector3 AgxForward(Vector3 c)
    {
        var v = Mul3(AgxInset, Max0(c) + new Vector3(2e-10f, 2e-10f, 2e-10f));
        for (int i = 0; i < 3; i++)
        {
            float x = (Mathf.Clamp(Mathf.Log(Mathf.Max(v[i], 1e-30f)) / Mathf.Log(2), AgxMinEv, AgxMaxEv) - AgxMinEv) / (AgxMaxEv - AgxMinEv);
            v[i] = Mathf.Pow(AgxSig(x), 2.4f);
        }
        return Mul3(AgxOutset, v);
    }
    static Vector3 Mul3(float[] m, Vector3 v) => new(m[0] * v.X + m[1] * v.Y + m[2] * v.Z, m[3] * v.X + m[4] * v.Y + m[5] * v.Z, m[6] * v.X + m[7] * v.Y + m[8] * v.Z);
    static float[] Inv3(float[] m)
    {
        double a = m[0], b = m[1], c = m[2], d = m[3], e = m[4], f = m[5], g = m[6], h = m[7], i = m[8];
        double A = e * i - f * h, B = -(d * i - f * g), C = d * h - e * g, det = a * A + b * B + c * C;
        return new[] { (float)(A / det), (float)(-(b * i - c * h) / det), (float)((b * f - c * e) / det),
            (float)(B / det), (float)((a * i - c * g) / det), (float)(-(a * f - c * d) / det),
            (float)(C / det), (float)(-(a * h - b * g) / det), (float)((a * e - b * d) / det) };
    }

    /// <summary>(L1 W2) The tone curve on Oklab L (GradeSettings.Curve, tabled): a darkened pixel keeps its chroma's share of
    /// its L, a lightened one its chroma.</summary>
    static Vector3 Tone(Vector3 outLin, float[] tone)
    {
        var o = Oklab(outLin);
        float x = Mathf.Clamp(o.X, 0, 1) * 256; int k = Mathf.Min((int)x, 255);
        float l1 = Mathf.Lerp(tone[k], tone[k + 1], x - k);
        float c1 = l1 < o.X ? o.Y * l1 / Mathf.Max(o.X, 1e-4f) : o.Y, h = Mathf.DegToRad(o.Z);
        return InGamut(l1, c1 * Mathf.Cos(h), c1 * Mathf.Sin(h));
    }

    /// <summary>Oklab (L, a, b) to linear rgb, its chroma taken in (hue and L kept) until it is inside the gamut.</summary>
    static Vector3 InGamut(float L, float a, float b)
    {
        static bool In(Vector3 v) => v.X >= -1e-5f && v.Y >= -1e-5f && v.Z >= -1e-5f && v.X <= 1 + 1e-5f && v.Y <= 1 + 1e-5f && v.Z <= 1 + 1e-5f;
        var rgb = FromOklab(L, a, b);
        if (!In(rgb))
        {
            float lo = 0, hi = 1;
            for (int n = 0; n < 12; n++) { float mid = (lo + hi) * 0.5f; if (In(FromOklab(L, a * mid, b * mid))) lo = mid; else hi = mid; }
            rgb = FromOklab(L, a * lo, b * lo);
        }
        return rgb.Clamp(Vector3.Zero, Vector3.One);
    }

    static Vector3 Moonlight(Vector3 inLin, Vector3 outLin, GradeSettings g)
    {
        var i = Oklab(inLin); var o = Oklab(outLin);
        float sat = i.Y / Mathf.Max(i.X, 1e-4f), top = (float)g.MoonTop;
        float m = (float)g.Moon * (1 - Smooth((float)g.MoonLo, (float)g.MoonHi, sat)) * (1 - Smooth(top - (float)g.MoonWidth, top, i.X)) * Smooth(0, 0.06f, i.X);
        // (skin's hues spared MoonSkin of it: P1 R1 round 33, S4, her shaded neck blue-grey at the Look)
        if (g.MoonSkin > 0) m *= 1 - (float)g.MoonSkin * Smooth(MoonSkinHue[0], MoonSkinHue[1], i.Z) * (1 - Smooth(MoonSkinHue[2], MoonSkinHue[3], i.Z)) * Smooth(0.012f, 0.025f, i.Y);
        if (m <= 0) return outLin;
        float h0 = Mathf.DegToRad(o.Z), h1 = Mathf.DegToRad((float)g.MoonHue), keep = 1 - m * (float)g.MoonDrop, add = m * o.X * (float)g.MoonSat;
        return FromOklab(o.X, o.Y * Mathf.Cos(h0) * keep + add * Mathf.Cos(h1), o.Y * Mathf.Sin(h0) * keep + add * Mathf.Sin(h1)).Clamp(Vector3.Zero, Vector3.One);
    }

    /// <summary>Linear sRGB to Oklab as (L, chroma, hue in degrees).</summary>
    static Vector3 Oklab(Vector3 c)
    {
        float l = Mathf.Pow(Mathf.Max(0.4122214708f * c.X + 0.5363325363f * c.Y + 0.0514459929f * c.Z, 0), 1 / 3f);
        float m = Mathf.Pow(Mathf.Max(0.2119034982f * c.X + 0.6806995451f * c.Y + 0.1073969566f * c.Z, 0), 1 / 3f);
        float s = Mathf.Pow(Mathf.Max(0.0883024619f * c.X + 0.2817188376f * c.Y + 0.6299787005f * c.Z, 0), 1 / 3f);
        float L = 0.2104542553f * l + 0.7936177850f * m - 0.0040720468f * s;
        float A = 1.9779984951f * l - 2.4285922050f * m + 0.4505937099f * s;
        float B = 0.0259040371f * l + 0.7827717662f * m - 0.8086757660f * s;
        return new(L, Mathf.Sqrt(A * A + B * B), Mathf.RadToDeg(Mathf.Atan2(B, A)));
    }

    static Vector3 FromOklab(float L, float A, float B)
    {
        float l = L + 0.3963377774f * A + 0.2158037573f * B;
        float m = L - 0.1055613458f * A - 0.0638541728f * B;
        float s = L - 0.0894841775f * A - 1.2914855480f * B;
        l *= l * l; m *= m * m; s *= s * s;
        return new(4.0767416621f * l - 3.3077115913f * m + 0.2309699292f * s,
            -1.2684380046f * l + 2.6097574011f * m - 0.3413193965f * s,
            -0.0041960863f * l - 0.7034186147f * m + 1.7076147010f * s);
    }

    static float Luma(Vector3 c) => c.X * 0.2126f + c.Y * 0.7152f + c.Z * 0.0722f;
    static float Smooth(float a, float b, float x) { float t = Mathf.Clamp((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t); }
    static Vector3 Max0(Vector3 v) => new(Mathf.Max(v.X, 0), Mathf.Max(v.Y, 0), Mathf.Max(v.Z, 0));
    static Vector3 Pow(Vector3 v, float e) => new(Mathf.Pow(Mathf.Max(v.X, 0), e), Mathf.Pow(Mathf.Max(v.Y, 0), e), Mathf.Pow(Mathf.Max(v.Z, 0), e));
    static Vector3 Pow(Vector3 v, Vector3 e) => new(Mathf.Pow(v.X, e.X), Mathf.Pow(v.Y, e.Y), Mathf.Pow(v.Z, e.Z));
    static float Lin1(float c) => c < 0.04045f ? c * 0.0773993808f : Mathf.Pow(c * 0.9478672986f + 0.0521327014f, 2.4f);
    static float Srgb1(float c) => c < 0.0031308f ? c * 12.92f : 1.055f * Mathf.Pow(c, 0.41666f) - 0.055f;
    static Vector3 Lin(Vector3 c) => new(Lin1(c.X), Lin1(c.Y), Lin1(c.Z));
    static Vector3 Srgb(Vector3 c) => new(Srgb1(c.X), Srgb1(c.Y), Srgb1(c.Z));

    /// <summary>--grade-try k=v,...: a trial paint grade over the preset's own (GradeSettings.Paint*), key by key, for style
    /// frames. Keys: mute, vib, skin, shadow (#hex or _hex), shadowk, lift, hi, shskin. Its numpy twin is tools/scratch/art_style/grade_try.py.</summary>
    static readonly GradeTry? Try = GradeTry.Parse(SurvivorUnchained.Args.Get("grade-try"));

    sealed class GradeTry
    {
        public float? Mute, Vib, Skin, ShadowK, Lift, Hi, ShadowSkin;
        public string? Shadow;

        public static GradeTry? Parse(string? spec)
        {
            if (string.IsNullOrWhiteSpace(spec)) return null;
            var t = new GradeTry();
            var inv = System.Globalization.CultureInfo.InvariantCulture;
            foreach (var part in spec.Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries))
            {
                int eq = part.IndexOf('=');
                if (eq < 0) { GD.PushWarning($"--grade-try: no value in '{part}'"); continue; }
                string k = part[..eq].Trim().ToLowerInvariant(), v = part[(eq + 1)..].Trim();
                if (k == "shadow") { t.Shadow = v.StartsWith('_') ? "#" + v[1..] : v; continue; }
                if (!float.TryParse(v, System.Globalization.NumberStyles.Float, inv, out float f)) { GD.PushWarning($"--grade-try: bad number '{part}'"); continue; }
                switch (k)
                {
                    case "mute": t.Mute = f; break;
                    case "vib": t.Vib = f; break;
                    case "skin": t.Skin = f; break;
                    case "shadowk": t.ShadowK = f; break;
                    case "lift": t.Lift = f; break;
                    case "hi": t.Hi = f; break;
                    case "shskin": t.ShadowSkin = f; break;
                    default: GD.PushWarning($"--grade-try: unknown key '{k}'"); break;
                }
            }
            return t;
        }
    }

    /// <summary>The paint grade's terms for one table: the grade's own, each --grade-try key over its own.</summary>
    readonly struct Paint
    {
        readonly float vib, skin, shadowK, lift, hi, vibDark, shadowSkin;
        readonly bool hasShadow;
        readonly float ls, cs, hs;
        public bool On => vib != 0 || hi != 0 || lift != 0 || (hasShadow && shadowK != 0);

        public Paint(GradeSettings g, GradeTry? t)
        {
            vib = t?.Vib ?? (float)g.PaintVib; hi = t?.Hi ?? (float)g.PaintHi; lift = t?.Lift ?? (float)g.PaintLift;
            shadowK = t?.ShadowK ?? (float)g.PaintShadowK; skin = t?.Skin ?? 1; vibDark = (float)g.PaintVibDark;
            shadowSkin = t?.ShadowSkin ?? (float)g.PaintShadowSkin;
            string hex = t?.Shadow ?? g.PaintShadow;
            hasShadow = hex != "";
            ls = cs = hs = 0;
            if (hasShadow)
            {
                var c = new Color(hex);
                var o = Oklab(Lin(new Vector3(c.R, c.G, c.B)));
                ls = o.X; cs = o.Y; hs = o.Z;
            }
        }

        public Vector3 Apply(Vector3 outLin)
        {
            var ok = Oklab(outLin);
            float L = ok.X, C = ok.Y, h = ok.Z;
            float skinHue = Smooth(15, 30, h) * (1 - Smooth(75, 90, h));
            float skinW = skin * skinHue * Smooth(0.025f, 0.05f, C) * Smooth(0.30f, 0.45f, L);
            if (vib != 0)
            {
                // (G1 r2: fades with lightness, a fifth of it below Oklab L 0.44 (a gamma luma of 0.3 is L 0.42): it took the day
                // town's olive-brown mud, puddle decals and grout to rust-orange, chroma 3.1 to 5.0 (x100); 3.6 now, the sunlit setts kept.)
                float dull = 1 - Smooth(0.02f, 0.20f, C), light = Smooth(0.04f, 0.18f, L) * VibDeep(L);
                C *= 1 + vib * dull * light * (1 - skinW);
            }
            // (G1 r2: lit skin mostly kept out of the highlight boost: it took her lit skin's chroma 9 to 11, a spray tan, and
            // yellowed her sunlit arm in the town. Only skin's own chroma, 0.06 up: the sunlit setts' warm stone, 0.05, keeps it.)
            if (hi != 0)
            {
                float skinHi = 0.85f * skin * skinHue * Smooth(0.06f, 0.085f, C) * Smooth(0.30f, 0.45f, L);
                C *= 1 + hi * Smooth(0.55f, 0.90f, L) * Smooth(0.008f, 0.03f, C) * (1 - skinHi);
            }
            float hr = Mathf.DegToRad(h);
            float a = C * Mathf.Cos(hr), b = C * Mathf.Sin(hr);
            if (lift != 0) L = Mathf.Min(L + lift * (1 - Smooth(0, 0.35f, L)), 1);
            if (hasShadow && shadowK != 0)
            {
                float dark = 1 - Smooth(0.12f, 0.45f, L), fadeBlack = Smooth(0, 0.08f, L), own = 1 - Smooth(0.02f, 0.07f, C);
                float w = Mathf.Clamp(shadowK * dark * own * fadeBlack, 0, 1);
                // (skin's hues spared by PaintShadowSkin: the lerp to blue ran her shade through red and violet)
                if (shadowSkin != 0) w *= 1 - shadowSkin * skinHue * Smooth(0.012f, 0.025f, C);
                float ct = cs * Mathf.Min(L / Mathf.Max(ls, 0.05f), 1), hsr = Mathf.DegToRad(hs);
                a = Mathf.Lerp(a, ct * Mathf.Cos(hsr), w);
                b = Mathf.Lerp(b, ct * Mathf.Sin(hsr), w);
            }
            var rgb = FromOklab(L, a, b);
            if (!In(rgb))
            {
                float lo = 0, hiT = 1;
                for (int i = 0; i < 12; i++)
                {
                    float mid = (lo + hiT) * 0.5f;
                    if (In(FromOklab(L, a * mid, b * mid))) lo = mid; else hiT = mid;
                }
                rgb = FromOklab(L, a * lo, b * lo);
            }
            return rgb.Clamp(Vector3.Zero, Vector3.One);
        }

        /// <summary>The vibrance's share by Oklab lightness: PaintVibDark (0.2) up to L 0.44, all of it from L 0.52 (the sunlit stone's).</summary>
        float VibDeep(float L) => Mathf.Lerp(vibDark, 1, Smooth(0.44f, 0.52f, L));

        static bool In(Vector3 v) => v.X >= -1e-5f && v.Y >= -1e-5f && v.Z >= -1e-5f && v.X <= 1 + 1e-5f && v.Y <= 1 + 1e-5f && v.Z <= 1 + 1e-5f;
    }
}
