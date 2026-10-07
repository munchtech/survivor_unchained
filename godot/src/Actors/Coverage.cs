using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// Her hair, brows and lashes cut by a threshold that moves every frame
/// (shaders/coverage.gdshaderinc), in place of Godot's own cuts: her hair's
/// hashed alpha and her brows' and lashes' alpha to coverage. A temporal
/// smoothing (FSR 2, TAA) sums the frames' cuts into the true coverage, soft and
/// still. Godot's hashed alpha keeps one threshold for each point of the surface,
/// noise that stands still: FSR 2 cannot average it away (her hair and lashes
/// crawled at the Look) and TAA only blurs it; alpha to coverage needs MSAA.
/// For now a developer's switch (--coverage), for the rendering lead's comparisons.
/// </summary>
public static class Coverage
{
    public static readonly bool On = SurvivorUnchained.Args.Has("coverage");

    static Shader? hair, cards;
    static readonly StringName AlbedoTex = "albedo_tex", AlbedoColour = "albedo_color";

    /// <summary>Her hair's cards (all but the blended cap and fine hairs).</summary>
    public static Shader Hair => hair ??= GD.Load<Shader>("res://shaders/heroine_hair_coverage.gdshader");

    /// <summary>Brows or lashes (cards Godot cuts by alpha to coverage), cut by the moving
    /// threshold instead when it is on; as they are when it is off.</summary>
    public static Material Cards(StandardMaterial3D m)
    {
        if (!On) return m;
        cards ??= GD.Load<Shader>("res://shaders/heroine_cards.gdshader");
        var c = new ShaderMaterial { Shader = cards, ResourceName = m.ResourceName };
        c.SetShaderParameter(AlbedoTex, m.AlbedoTexture);
        c.SetShaderParameter(AlbedoColour, m.AlbedoColor);
        return c;
    }

    /// <summary>The brows' colour (a shade of her hair) on their card material.</summary>
    public static void Colour(ShaderMaterial m, Color colour) => m.SetShaderParameter(AlbedoColour, colour);
}
