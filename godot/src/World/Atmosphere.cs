using System;
using System.Collections.Generic;
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
    double clock;

    const float FogMatchDistance = 60;

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
        RenderingServer.GlobalShaderParameterSet("sky_time", (float)clock);
    }

    static Color C(string hex) => new(hex);

    /// <param name="grade">Rebuild the colour grade too (not every frame of a blend).</param>
    public void Set(AtmospherePreset p, bool grade = true)
    {
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
        Env.VolumetricFogDensity = 0.0012f;
        // An ember arena's own air: smoke or dust hanging in it.
        if (air is { } a)
        {
            Env.VolumetricFogDensity = 0.0012f * (float)a.Haze;
            Env.VolumetricFogAlbedo = C(a.HazeColor).Lightened(0.35f);
        }
        Env.TonemapExposure = (float)p.Exposure * ExposureScale;
        var rim = C(p.Rim).SrgbToLinear();
        RenderingServer.GlobalShaderParameterSet("body_rim", new Vector4(rim.R, rim.G, rim.B, (float)p.RimStrength));
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
                    p += (shT - new Vector3(0.5f, 0.5f, 0.5f)) * sh * tint;
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
                    var o = Srgb(outLin);
                    img.SetPixel(r, gi, new Color(o.X, o.Y, o.Z));
                }
            slices.Add(img);
        }
        var tex = new ImageTexture3D();
        tex.Create(Image.Format.Rgb8, LutSize, LutSize, LutSize, false, slices);
        luts[key] = tex;
        return tex;
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
