namespace SurvivorUnchained.Look;

/// <summary>Which skin parts take the cel model's hard highlight (heroine_skin.gdshader CEL_SPEC: a disc of 6 degrees
/// round N.H on the full mapped normal). On the head's small, tightly curved forms (nose, lips, cheekbones) that disc
/// stays a small spark. On the body's broad, near-flat forms (sternum, breast tops, belly, back) the same 6 degrees
/// covers a wide area whose outline follows the normal map: pale, hard-edged patches over the sternum and the tops of
/// the breasts at the chest camera, on her and on every NPC on her base (Marionette R&D x18 w6; isolated 13 Nov with
/// --skin-set "*:cel_spec=6/1/0/0.85": strength 0 and they are gone, the soft sheen kept). So body parts take none.
/// (Tried and judged worse, 13 Nov: a soft, small disc instead (4/3/0.2 on the geometric normal): any disc in degrees round
/// N.H still spreads into a flat patch on near-flat forms, thins to streaks on fingers and pops as glints at night. If the
/// night skin wants more life, the route is a low, wide sheen from the key light only, masked off the hands.)</summary>
public static class SkinHighlight
{
    /// <summary>The cel highlight's strength (cel_spec.z) a skin part is given, or null to keep the shader's own (CEL_SPEC).</summary>
    public static float? Strength(string part) => part == "skin_head" ? null : 0f;
}
