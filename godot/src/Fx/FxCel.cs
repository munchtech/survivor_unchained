using Godot;
using SurvivorUnchained.Look;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.View;

/// <summary>
/// (L1 B6) The FX language in the game: data/look/fx_language.json (logic/Look/FxLanguage.cs) set on a material of
/// shaders/fx_cel.gdshaderinc. On with --fx-cel on under cel (never at --cel off: today's effects exactly); opt-in until
/// the proof passes its judge, then the default (B6, 5 Nov: the bolt's shape is not yet MB5's). The proof is
/// the cinder bolt (BattleFx.Flight, shaders/fx_cel_bolt.gdshader); other effects adopt the include school by school.
/// </summary>
public static class FxCel
{
    public static readonly bool On = SurvivorUnchained.Args.Get("cel") != "off" && SurvivorUnchained.Args.Get("fx-cel") == "on";
    static FxLanguage? lang;
    public static FxLanguage Lang => lang ??= FxLanguage.Parse(Godot.FileAccess.GetFileAsString("res://data/look/fx_language.json"));

    static Vector3 V(float[] a) => new(a[0], a[1], a[2]);

    /// <summary>Sets a material's fx_cel uniforms from its school's family (--fx-gain K scales every band, for calibrating).</summary>
    public static ShaderMaterial Apply(ShaderMaterial m, School school)
    {
        if (Lang[school.ToString()] is not { } s) return m;
        float k = (float)SurvivorUnchained.Args.Num("fx-gain", 1f);
        Vector3 Band(FxBand b) => V(FxLanguage.Linear(b.Hex, b.Emit)) * k;
        m.SetShaderParameter("fx_edge", Band(s.Edge));
        m.SetShaderParameter("fx_mid", Band(s.Mid));
        m.SetShaderParameter("fx_core", Band(s.Core));
        m.SetShaderParameter("fx_t", new Vector4(s.Edge.T, s.Mid.T, s.Core.T, 0));
        m.SetShaderParameter("fx_glow_color", V(FxLanguage.Linear(s.Glow.Hex, s.Edge.Emit)) * k);
        m.SetShaderParameter("fx_glow", new Vector4(s.Glow.Width, s.Glow.Reach, s.Glow.Head, s.Glow.Tail));
        m.SetShaderParameter("fx_spark_color", V(FxLanguage.Linear(s.Sparks.Hex, s.Mid.Emit)) * k);
        return m;
    }

    /// <summary>The cel bolt's material for a school; its sparks' density from the family's count (one quad's cells).</summary>
    public static ShaderMaterial Bolt(School school)
    {
        var m = Apply(new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/fx_cel_bolt.gdshader") }, school);
        if (Lang[school.ToString()] is { } s)
        {
            // the quad behind the head is about (span - 1) x 2 units at span 3.4: its cells of 0.35 units
            float cells = (BoltSpan - 1) * 2 / (0.35f * 0.35f);
            m.SetShaderParameter("bolt_sparks", new Vector4(0.35f, Mathf.Clamp(s.Sparks.Count / cells, 0.05f, 0.9f), s.Sparks.Length, s.Sparks.Aspect));
        }
        return m;
    }

    /// <summary>The quad's length over its half-width (the shader's span): MB5's bolt body is 2.56 times as long as tall.</summary>
    public const float BoltSpan = 3.4f;

    /// <summary>A bolt's instance: its head at `head`, flying along `fwd`, `size` its width (m); the quad laid along the
    /// flight (basis X its length, Y its width) and centred so the head sits on the projectile.</summary>
    public static Transform3D BoltAt(Vector3 head, Vector3 fwd, float size)
    {
        fwd = fwd.LengthSquared() < 1e-6f ? Vector3.Forward : fwd.Normalized();
        float wid = size, len = BoltSpan * wid / 2;
        var side = fwd.Cross(Vector3.Up);
        if (side.LengthSquared() < 1e-6f) side = Vector3.Right;
        var at = head - fwd * (BoltSpan / 2 - 1) * wid / 2;
        return new Transform3D(new Godot.Basis(fwd * len, Vector3.Up * wid, side.Normalized()), at);
    }
}
