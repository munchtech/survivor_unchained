using Godot;

namespace SurvivorUnchained.View;

/// <summary>(demo-look r2 her, 16 Nov; judge 1: "the look stops at the set") Her figure in the den, from the rig's hero_den row
/// (Zone.HeroDen): her cast shadow (shaders/hero_cast.gdshader, Actors/HerShadow.cs), her line where no hero_pool row draws it
/// (hero_line.gdshader through Atmosphere.HeroLinePx), her hair's chroma and her skin and hair steps (cel_her_den), and her
/// held steel (Actors/HerSteel.cs, shaders/hero_steel.gdshader), her steps' painted direction (toward the den key, cel_key)
/// and levels (cel_her_den2, cel_her_den3), her ember's height over her feet (PlayerView reads EmberH) and its own energy on
/// the ground (PoolK), her rim (hero_ink.gdshader through cel_hero_rim, cel_hero_rim2). A rig
/// without the row: every global zero, nothing drawn, her look as before.</summary>
public static class HeroDen
{
    /// <summary>The trail's world direction (x, z) and whether her shadow shows (HerShadow reads them each frame).</summary>
    public static Vector2 CastDir = new(0.77f, 0.64f);
    public static bool CastOn;
    /// <summary>Whether her held steel wears the den's painted steel (HerSteel, each frame from PlayerView).</summary>
    public static bool SteelOn;
    /// <summary>Her ember's (the pool light's) height over her feet in the den, m (value 33); 0: PlayerView's own (--ember-h, 1.7).</summary>
    public static float EmberH;
    /// <summary>(lane E polish) Her ember's (the pool light's) own energy in the den, a share (value 38; 0 or absent: 1): the
    /// ground's pool only. Her folk light, which follows the pool's energy, and her lamp on the crowd are given it back
    /// (PlayerView.PoolDen), so her skin, her hair and the foes stay as they were while the ground by her darkens.</summary>
    public static float PoolK;
    /// <summary>(lead 3, row 1: "she nearly vanishes under the roots") Her rim light (PlayerView.RimLight, RimStep), values
    /// 47-56: its energy where it is full (0 or absent: off), its colour R, G, B (sRGB 0-255), its height over her feet and its
    /// offset behind her (m, away from the camera along the ground), its range (m), the den's own light at her feet
    /// (PlayerView.DenLightAt) at or under which it is full and at or over which it is gone, its fall (OmniAttenuation).</summary>
    public static float RimEnergy, RimH, RimBack, RimRange, RimLo, RimHi, RimAtt;
    public static Color RimColor = new("#ffd4a8");
    /// <summary>The rim light's tag, its light_specular: her skin's and hair's light() know it by SPECULAR_AMOUNT (twice this,
    /// cel_her_den3.y while the rim is on) and keep it out of the den's painted steps, which would spread it over her as a fill.</summary>
    public const float RimTag = 0.17f;

    static double V(double[] d, int i, double or) => d.Length > i ? d[i] : or;
    static readonly bool RimDebug = SurvivorUnchained.Args.Dev && !string.IsNullOrEmpty(System.Environment.GetEnvironmentVariable("SU_HERO_RIM_DEBUG"));

    /// <summary>After Atmosphere's hero rows: d the rig's hero_den (null under a camera rig or another rig); heroPool true when
    /// the hero_pool row already draws her line.</summary>
    public static void Apply(double[]? d, bool heroPool)
    {
        CastOn = d != null && V(d, 0, 0) > 0;
        if (CastOn)
        {
            float a = Mathf.DegToRad((float)V(d!, 5, 40));
            CastDir = new Vector2(Mathf.Cos(a), Mathf.Sin(a));
        }
        RenderingServer.GlobalShaderParameterSet("hero_cast_shape", CastOn ? new Vector4((float)V(d!, 1, 0.5), (float)V(d!, 2, 0.35), (float)V(d!, 3, 0.8), (float)V(d!, 4, 0.2)) : Vector4.Zero);
        RenderingServer.GlobalShaderParameterSet("hero_cast_mul", CastOn ? new Vector4((float)V(d!, 6, 0.4), (float)V(d!, 7, 0.45), (float)V(d!, 8, 0.55), (float)V(d!, 9, 0.8)) : Vector4.One);
        // her line (values 10-14) where the hero_pool row does not draw it
        if (!heroPool && d is { Length: >= 15 } && d[10] > 0)
        {
            Atmosphere.HeroLinePx = (float)d[10];
            var t = new Color((float)d[11] / 255f, (float)d[12] / 255f, (float)d[13] / 255f).SrgbToLinear() * (float)d[14];
            RenderingServer.GlobalShaderParameterSet("cel_hero_line", new Vector4(t.R, t.G, t.B, Atmosphere.HeroLinePx));
        }
        // her hair's chroma and value gain (values 15-16), her skin and hair steps (value 17: the shade step's share of the lit;
        // 0 off), the lit step's chroma (value 32, its light's chroma kept: 1 as is)
        RenderingServer.GlobalShaderParameterSet("cel_her_den", d is { Length: >= 18 } ? new Vector4((float)d[15], (float)d[16], (float)d[17], (float)V(d, 32, 0)) : Vector4.Zero);
        // (round 2 her, the D judge: "pasty") the steps' painted direction: toward the den key (cel_key), value 31 of the way
        // from her ember's own (heroine_skin, heroine_hair light()); the steps' n.l (34, 0: 0.42), the lit step's level (35, 0:
        // 0.7), the shade step's warmth (36: the light's own hue again, share) and her hair's shade step (37, share of the lit)
        RenderingServer.GlobalShaderParameterSet("cel_her_den2", d != null ? new Vector4((float)V(d, 31, 0), (float)V(d, 34, 0), (float)V(d, 35, 0), (float)V(d, 36, 0)) : Vector4.Zero);
        RimEnergy = d != null ? (float)V(d, 47, 0) : 0;
        if (RimEnergy > 0)
        {
            RimColor = new Color((float)V(d!, 48, 255) / 255f, (float)V(d!, 49, 212) / 255f, (float)V(d!, 50, 168) / 255f);
            RimH = (float)V(d!, 51, 0.9); RimBack = (float)V(d!, 52, 0.6); RimRange = (float)V(d!, 53, 2.5);
            RimLo = (float)V(d!, 54, 0); RimHi = (float)V(d!, 55, 1); RimAtt = (float)V(d!, 56, 1);
        }
        // (x her hair's shade step (37); y the rim light's tag as SPECULAR_AMOUNT while it is on, 0 off)
        RenderingServer.GlobalShaderParameterSet("cel_her_den3", d != null ? new Vector4((float)V(d, 37, 0), RimEnergy > 0 ? 2 * RimTag : 0, 0, 0) : Vector4.Zero);
        // (demo-look lead 3, row 1: "she nearly vanishes under the roots") her rim in her line's ink pass (hero_ink.gdshader):
        // values 39-46: its width (px at 1080p; 0 or absent: off), its tone R, G, B (sRGB 0-255) and level, the ground's
        // cube-root luminance where it is full and where it is gone, and its share on edges facing screen-down (her feet).
        // SU_HERO_RIM_DEBUG (dev): the edge it finds painted magenta at full strength, the ground's gate off.
        bool rimOn = d != null && V(d, 39, 0) > 0 && d.Length >= 47;
        var rc = rimOn ? new Color((float)d![40] / 255f, (float)d[41] / 255f, (float)d[42] / 255f).SrgbToLinear() * (float)d[43] : new Color(0, 0, 0);
        RenderingServer.GlobalShaderParameterSet("cel_hero_rim", new Vector4(rc.R, rc.G, rc.B, rimOn ? (float)d![39] : 0));
        RenderingServer.GlobalShaderParameterSet("cel_hero_rim2", rimOn ? new Vector4((float)d![44], (float)d[45], (float)d[46], RimDebug ? 1 : 0) : Vector4.Zero);
        EmberH = d != null ? (float)V(d, 33, 0) : 0;
        PoolK = d != null ? (float)V(d, 38, 0) : 0;   // her pool's own energy (38)
        // her held steel (values 18-30: its level, lit R, G, B, shade R, G, B, glint R, G, B (sRGB 0-255), the glint's place
        // along the piece (0-1) and half length (share), the grip's light): shaders/hero_steel.gdshader through HerSteel
        SteelOn = d is { Length: >= 31 } && d[18] > 0;
        Color T(int i) => SteelOn ? new Color((float)d![i] / 255f, (float)d[i + 1] / 255f, (float)d[i + 2] / 255f).SrgbToLinear() * (float)d[18] : new Color(0, 0, 0);
        Color lit = T(19), shade = T(22), glint = T(25);
        RenderingServer.GlobalShaderParameterSet("hero_steel_lit", new Vector4(lit.R, lit.G, lit.B, SteelOn ? (float)d![28] : 0));
        RenderingServer.GlobalShaderParameterSet("hero_steel_shade", new Vector4(shade.R, shade.G, shade.B, SteelOn ? (float)d![29] : 0));
        RenderingServer.GlobalShaderParameterSet("hero_steel_glint", new Vector4(glint.R, glint.G, glint.B, SteelOn ? (float)d![30] : 0));
    }
}
