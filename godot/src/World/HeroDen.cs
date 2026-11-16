using Godot;

namespace SurvivorUnchained.View;

/// <summary>(demo-look r2 her, 16 Nov; judge 1: "the look stops at the set") Her figure in the den, from the rig's hero_den row
/// (Zone.HeroDen): her cast shadow (shaders/hero_cast.gdshader, Actors/HerShadow.cs), her line where no hero_pool row draws it
/// (hero_line.gdshader through Atmosphere.HeroLinePx), and her hair's chroma and her skin and hair steps (cel_her_den). A rig
/// without the row: every global zero, nothing drawn, her look as before.</summary>
public static class HeroDen
{
    /// <summary>The trail's world direction (x, z) and whether her shadow shows (HerShadow reads them each frame).</summary>
    public static Vector2 CastDir = new(0.77f, 0.64f);
    public static bool CastOn;

    static double V(double[] d, int i, double or) => d.Length > i ? d[i] : or;

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
        // her hair's chroma and value gain (values 15-16), her skin and hair steps (value 17)
        RenderingServer.GlobalShaderParameterSet("cel_her_den", d is { Length: >= 18 } ? new Vector4((float)d[15], (float)d[16], (float)d[17], 0) : Vector4.Zero);
    }
}
