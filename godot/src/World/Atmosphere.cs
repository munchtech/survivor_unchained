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
    public (float Begin, float End, float Curve, float Amount, float Sky, Color? Tint)? Haze { get => haze; set { haze = value; HazeApply(); } }
    (float Begin, float End, float Curve, float Amount, float Sky, Color? Tint)? haze;

    void HazeApply()
    {
        if (haze is { } h)
        {
            Env.FogMode = Godot.Environment.FogModeEnum.Depth;
            Env.FogDepthBegin = h.Begin; Env.FogDepthEnd = h.End; Env.FogDepthCurve = h.Curve;
            Env.FogDensity = h.Amount; Env.FogAerialPerspective = h.Sky;
            if (h.Tint is Color tc) Env.FogLightColor = tc;
            if (System.Environment.GetEnvironmentVariable("FLORA_STATS") != null) GD.Print($"haze: depth {h.Begin}-{h.End} m, amount {h.Amount}, sky {h.Sky}; fog on {Env.FogEnabled}");
        }
        else if (Env.FogMode != Godot.Environment.FogModeEnum.Exponential)
        {
            Env.FogMode = Godot.Environment.FogModeEnum.Exponential; Env.FogAerialPerspective = 0;
            Env.FogLightColor = C(Current.FogColor);
            Env.FogDensity = (float)(Current.FogDensity * Current.FogDensity * FogMatchDistance);
        }
    }
    /// <summary>A touch less exposure at low quality keeps the mood (the web
    /// game's exposureScale).</summary>
    public float ExposureScale = 1;
    /// <summary>The eye stopping down after a Flare's BOOM (Fx/Flare/FlareFx.Dip): 1 none.</summary>
    public float FlareDip = 1;
    float dipShown = 1;
    /// <summary>How much colour the world keeps below the brights (0 all, 1
    /// none): the grade's worn world.</summary>
    public float Mute = 0.16f;
    /// <summary>Her carried light's gain under the air in force (AtmospherePreset.Ember).</summary>
    public static float EmberGain = 1;
    /// <summary>(E9d) How lit the town is (0 by day, 1 at dawn, dusk and night): its lamps burn and some windows glow
    /// (ZoneView.Town, kit.gdshader's town_lit) from a low or a moonlit key.</summary>
    public static float TownLit = 1;
    /// <summary>The camera's own say over the exposure (1: none): the close view by night opens up, as an eye does
    /// on a face near it, so the wood behind her reads (GameCloseUp, E1).</summary>
    public float ViewExposure { get; private set; } = 1;
    /// <summary>The camera's say over the grade's highlight tint (0: the preset's; 1: none). The close view by night takes the
    /// near-white highlight tint off her face, which it left pale and waxy (E1 round 3); in quarter steps, each table made once.</summary>
    public float ViewHighlightsNeutral { get; private set; }
    public void SetViewHighlights(float k)
    {
        k = Mathf.Round(Mathf.Clamp(k, 0, 1) * 4) / 4;
        if (Mathf.IsEqualApprox(k, ViewHighlightsNeutral)) return;
        ViewHighlightsNeutral = k;
        var lut = GradeLut(Cine(ViewGrade(Own(Current))), Mute, SkinGuardFor(Current));
        if (!GradeOff) Env.AdjustmentColorCorrection = lut;
    }
    // (#bcbcbc is linear 0.5: the grade adds a tint as its distance from 0.5, so this one adds nothing.)
    // (And the moon's colour off her skin: its weakly coloured parts went grey in patches beside the ember-lit ones.)
    GradeSettings ViewGrade(GradeSettings g) => ViewHighlightsNeutral <= 0 ? g
        : g with
        {
            HighlightTint = "#" + new Color(g.HighlightTint).Lerp(new Color("#bcbcbc"), ViewHighlightsNeutral).ToHtml(false),
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
        var lut = GradeLut(Cine(ViewGrade(Own(Current))), Mute, SkinGuardFor(Current));
        if (!GradeOff) Env.AdjustmentColorCorrection = lut;
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
    static GradeSettings Own(AtmospherePreset p) => FrontPaint && ReferenceEquals(p, Atmospheres.Front) ? p.Grade with
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
        if (FlareDip != dipShown) { dipShown = FlareDip; Env.TonemapExposure = (float)Current.Exposure * ExposureScale * ViewExposure * FlareDip; }
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
        float el = Mathf.DegToRad((float)p.KeyElevation), az = Mathf.DegToRad((float)p.KeyAzimuth);
        return new Vector3(Mathf.Cos(el) * Mathf.Cos(az), Mathf.Sin(el), Mathf.Cos(el) * Mathf.Sin(az)).Normalized();
    }

    public void Set(AtmospherePreset p, bool grade = true)
    {
        // --air-old: play's presets (E1) back to the ones before them, for before-and-after pictures.
        if (OldAir) p = ReferenceEquals(p, Atmospheres.LowFordNight) ? Atmospheres.Night : ReferenceEquals(p, Atmospheres.LowFordDawn) ? Atmospheres.Dawn
            : ReferenceEquals(p, Atmospheres.WaystationDawn) ? Atmospheres.Dawn : ReferenceEquals(p, Atmospheres.WaystationDay) ? Atmospheres.Day : p;
        // --air-tune "hemi=..,env=..,exposure=..,key=..,elevation=..,azimuth=..,shadow=..,tint=..,toe=..,contrast=..,ember=..,mist=..,haze=..":
        // play's presets (E1) nudged, for a sweep of pictures in one build.
        if (Tune != null && (ReferenceEquals(p, Atmospheres.LowFordNight) || ReferenceEquals(p, Atmospheres.LowFordDawn)
            || ReferenceEquals(p, Atmospheres.WaystationDawn) || ReferenceEquals(p, Atmospheres.WaystationDay)))
        {
            double T(string k, double v) => Tune.TryGetValue(k, out var x) ? double.Parse(x, System.Globalization.CultureInfo.InvariantCulture) : v;
            string H(string k, string v) => Tune.TryGetValue(k, out var x) ? x : v;
            double[] V(string k, double[] v) => Tune.TryGetValue(k, out var x)
                ? x.Split('/').Select(n => double.Parse(n, System.Globalization.CultureInfo.InvariantCulture)).ToArray() : v;
            p = p with
            {
                KeyColor = H("keyc", p.KeyColor), HemiSky = H("hemisky", p.HemiSky), HemiGround = H("hemiground", p.HemiGround),
                FogColor = H("fogc", p.FogColor), MistColor = H("mistc", p.MistColor),
                Sky = p.Sky with { Top = H("skytop", p.Sky.Top), Horizon = H("skyhor", p.Sky.Horizon), Glow = H("skyglow", p.Sky.Glow) },
                HemiIntensity = T("hemi", p.HemiIntensity), EnvIntensity = T("env", p.EnvIntensity), Exposure = T("exposure", p.Exposure),
                KeyIntensity = T("key", p.KeyIntensity), KeyElevation = T("elevation", p.KeyElevation), KeyAzimuth = T("azimuth", p.KeyAzimuth),
                ShadowStrength = T("shadow", p.ShadowStrength), Ember = T("ember", p.Ember), Mist = T("mist", p.Mist), Haze = T("haze", p.Haze),
                FogDensity = T("fog", p.FogDensity), CrowdRim = T("crowdrim", p.CrowdRim), RiverLight = T("river", p.RiverLight),
                RiverSky = T("riversky", p.RiverSky), RiverBend = T("bend", p.RiverBend),
                Grade = p.Grade with
                {
                    TintStrength = T("tint", p.Grade.TintStrength), Contrast = T("contrast", p.Grade.Contrast), Toe = T("toe", p.Grade.Toe),
                    ShadowTint = H("sh", p.Grade.ShadowTint), HighlightTint = H("hi", p.Grade.HighlightTint), Gain = V("gain", p.Grade.Gain),
                    Lift = V("lift", p.Grade.Lift), Saturation = T("sat", p.Grade.Saturation), Vibrance = T("vib", p.Grade.Vibrance),
                    Moon = T("moon", p.Grade.Moon), MoonHue = T("mhue", p.Grade.MoonHue), MoonSat = T("msat", p.Grade.MoonSat),
                    MoonDrop = T("mdrop", p.Grade.MoonDrop), MoonLo = T("mlo", p.Grade.MoonLo), MoonHi = T("mhi", p.Grade.MoonHi),
                    MoonTop = T("mtop", p.Grade.MoonTop), MoonWidth = T("mw", p.Grade.MoonWidth),
                    PaintShadow = H("psh", p.Grade.PaintShadow), PaintShadowK = T("pshk", p.Grade.PaintShadowK), PaintVib = T("pvib", p.Grade.PaintVib),
                    PaintLift = T("plift", p.Grade.PaintLift), PaintHi = T("phi", p.Grade.PaintHi),
                },
            };
        }
        Current = p;
        float el = Mathf.DegToRad((float)p.KeyElevation), az = Mathf.DegToRad((float)p.KeyAzimuth);
        var dir = new Vector3(Mathf.Cos(el) * Mathf.Cos(az), Mathf.Sin(el), Mathf.Cos(el) * Mathf.Sin(az)).Normalized();
        Key.Basis = Basis.LookingAt(-dir, Mathf.Abs(dir.Y) > 0.99f ? Vector3.Forward : Vector3.Up);
        Key.LightColor = C(p.KeyColor);
        Key.LightEnergy = (float)p.KeyIntensity / Mathf.Pi;
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
        Env.FogDensity = (float)(p.FogDensity * p.FogDensity * FogMatchDistance);
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
        SurvivorUnchained.View.MistLayers.Tint(C(p.MistColor), (float)p.Mist, C(p.KeyColor).SrgbToLinear() * Key.LightEnergy);
        EmberGain = (float)p.Ember;
        var rim = C(p.Rim).SrgbToLinear();
        RenderingServer.GlobalShaderParameterSet("body_rim", new Vector4(rim.R, rim.G, rim.B, (float)p.RimStrength));
        RenderingServer.GlobalShaderParameterSet("crowd_rim", new Vector4(rim.R, rim.G, rim.B, (float)(p.RimStrength * p.CrowdRim)));
        RenderingServer.GlobalShaderParameterSet("key_dir", new Vector4(dir.X, dir.Y, dir.Z, 0));
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
        if (frost > 0 && thaw > 0) GroundPaint.SunAt(dir);   // (as ThawSun says)
        // The key's light off the ground (a mid albedo, 0.18), what metal sees below the horizon: the
        // sky's lower half is the hemisphere's dark ground colour, so in shade her plate reflected
        // nothing and read as rubber (look bible, armor metal; metal round 3).
        var key = C(p.KeyColor).SrgbToLinear() * (Key.LightEnergy * Mathf.Max(dir.Y, 0f) * 0.18f);
        RenderingServer.GlobalShaderParameterSet("ground_bounce", new Vector4(key.R, key.G, key.B, 0f));
        if (grade) { var lut = GradeLut(Cine(ViewGrade(Own(p))), Mute, SkinGuardFor(p)); Env.AdjustmentColorCorrection = GradeOff ? null : lut; }
    }

    SurvivorUnchained.Maps.ArenaAir? air;

    /// <summary>A place's own air (an ember arena's), or none; applied with the next Set.</summary>
    public void Air(SurvivorUnchained.Maps.ArenaAir? a)
    {
        air = a;
        Set(Current);
    }

    /* -------------------------------------------------------------- grade -- */

    const int LutSize = 32;
    static readonly Dictionary<string, ImageTexture3D> luts = new();

    /// <summary>The web game's grade (render/grade.ts) as a lookup table:
    /// sRGB in (what Godot hands its colour correction after tone mapping),
    /// sRGB out.</summary>
    public static ImageTexture3D GradeLut(GradeSettings g, float mute, float skinGuard = 0)
    {
        if (Try?.Mute is float tm) mute = tm;
        var key = $"{SurvivorUnchained.Core.Json.Write(g)}|{mute}|{skinGuard}";
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
                    if (g.Moon > 0) outLin = Moonlight(c, outLin, g);
                    if (paint.On) outLin = paint.Apply(outLin);
                    if (skinGuard > 0) outLin = SkinGuard(outLin, skinGuard);
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
    /// <summary>The skin guard's share for this air (0 to 1): the Look's (Atmospheres.Front) whole, else the close view's (SetViewSkinGuard).</summary>
    float SkinGuardFor(AtmospherePreset p) => SkinGuardOff ? 0 : ReferenceEquals(p, Atmospheres.Front) ? 1 : ViewSkinGuard;
    static readonly bool SkinGuardOff = SurvivorUnchained.Args.Has("skin-guard-off");
    /// <summary>The close view's say over the skin guard (0 to 1, in quarter steps, each table made once; GameCloseUp).</summary>
    public float ViewSkinGuard { get; private set; }
    public void SetViewSkinGuard(float k)
    {
        k = Mathf.Round(Mathf.Clamp(k, 0, 1) * 4) / 4;
        if (Mathf.IsEqualApprox(k, ViewSkinGuard)) return;
        ViewSkinGuard = k;
        var lut = GradeLut(Cine(ViewGrade(Own(Current))), Mute, SkinGuardFor(Current));
        if (!GradeOff) Env.AdjustmentColorCorrection = lut;
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

    /// <summary>GradeSettings.Moon: the moon's (or the dawn shade's) cool colour over what is weakly coloured.</summary>
    static Vector3 Moonlight(Vector3 inLin, Vector3 outLin, GradeSettings g)
    {
        var i = Oklab(inLin); var o = Oklab(outLin);
        float sat = i.Y / Mathf.Max(i.X, 1e-4f), top = (float)g.MoonTop;
        float m = (float)g.Moon * (1 - Smooth((float)g.MoonLo, (float)g.MoonHi, sat)) * (1 - Smooth(top - (float)g.MoonWidth, top, i.X)) * Smooth(0, 0.06f, i.X);
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
