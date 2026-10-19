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
    /// <summary>A touch less exposure at low quality keeps the mood (the web
    /// game's exposureScale).</summary>
    public float ExposureScale = 1;
    /// <summary>How much colour the world keeps below the brights (0 all, 1
    /// none): the grade's worn world.</summary>
    public float Mute = 0.16f;
    /// <summary>Her carried light's gain under the air in force (AtmospherePreset.Ember).</summary>
    public static float EmberGain = 1;
    double clock;

    const float FogMatchDistance = 60;
    static readonly bool OldAir = SurvivorUnchained.Args.Has("air-old");
    static readonly Dictionary<string, double>? Tune = SurvivorUnchained.Args.Get("air-tune") is string tu
        ? tu.Split(',').Select(kv => kv.Split('=')).ToDictionary(kv => kv[0], kv => double.Parse(kv[1], System.Globalization.CultureInfo.InvariantCulture)) : null;

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
        RenderingServer.GlobalShaderParameterSet(SkyTime, (float)clock);
    }

    // (A name made once, not a new one every frame for the collector.)
    static readonly StringName SkyTime = "sky_time";

    static Color C(string hex) => new(hex);

    /// <param name="grade">Rebuild the colour grade too (not every frame of a blend).</param>
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
            double T(string k, double v) => Tune.TryGetValue(k, out var x) ? x : v;
            p = p with
            {
                HemiIntensity = T("hemi", p.HemiIntensity), EnvIntensity = T("env", p.EnvIntensity), Exposure = T("exposure", p.Exposure),
                KeyIntensity = T("key", p.KeyIntensity), KeyElevation = T("elevation", p.KeyElevation), KeyAzimuth = T("azimuth", p.KeyAzimuth),
                ShadowStrength = T("shadow", p.ShadowStrength), Ember = T("ember", p.Ember), Mist = T("mist", p.Mist), Haze = T("haze", p.Haze),
                Grade = p.Grade with { TintStrength = T("tint", p.Grade.TintStrength), Contrast = T("contrast", p.Grade.Contrast), Toe = T("toe", p.Grade.Toe) },
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
        Env.TonemapExposure = (float)p.Exposure * ExposureScale;
        SurvivorUnchained.View.MistLayers.Tint(C(p.MistColor), (float)p.Mist);
        EmberGain = (float)p.Ember;
        var rim = C(p.Rim).SrgbToLinear();
        RenderingServer.GlobalShaderParameterSet("body_rim", new Vector4(rim.R, rim.G, rim.B, (float)p.RimStrength));
        // The key's light off the ground (a mid albedo, 0.18), what metal sees below the horizon: the
        // sky's lower half is the hemisphere's dark ground colour, so in shade her plate reflected
        // nothing and read as rubber (look bible, armor metal; metal round 3).
        var key = C(p.KeyColor).SrgbToLinear() * (Key.LightEnergy * Mathf.Max(dir.Y, 0f) * 0.18f);
        RenderingServer.GlobalShaderParameterSet("ground_bounce", new Vector4(key.R, key.G, key.B, 0f));
        if (grade) Env.AdjustmentColorCorrection = GradeLut(p.Grade, Mute);
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
    public static ImageTexture3D GradeLut(GradeSettings g, float mute)
    {
        var key = $"{SurvivorUnchained.Core.Json.Write(g)}|{mute}";
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
        float tint = (float)g.TintStrength, sat = (float)g.Saturation, vibr = (float)g.Vibrance, con = (float)g.Contrast;
        var slices = new Godot.Collections.Array<Image>();
        for (int b = 0; b < LutSize; b++)
        {
            var img = Image.CreateEmpty(LutSize, LutSize, false, Image.Format.Rgb8);
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
                    var o = Srgb(outLin);
                    img.SetPixel(r, gi, new Color(o.X, o.Y, o.Z));
                }
            slices.Add(img);
        }
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
}
