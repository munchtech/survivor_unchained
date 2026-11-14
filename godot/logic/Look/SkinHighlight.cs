namespace SurvivorUnchained.Look;

/// <summary>Which skin parts take the cel model's hard highlight (heroine_skin.gdshader CEL_SPEC: a disc of 6 degrees
/// round N.H on the full mapped normal). On the head's small, tightly curved forms (nose, lips, cheekbones) that disc
/// stays a small spark. On the body's broad, near-flat forms (sternum, breast tops, belly, back) the same 6 degrees
/// covers a wide area whose outline follows the normal map: pale, hard-edged patches over the sternum and the tops of
/// the breasts at the chest camera, on her and on every NPC on her base (Marionette R&D x18 w6; isolated 13 Nov with
/// --skin-set "*:cel_spec=6/1/0/0.85": strength 0 and they are gone, the soft sheen kept). So body parts take none.
/// (Tried and judged worse, 13 Nov: a soft, small disc instead (4/3/0.2 on the geometric normal): any disc in degrees round
/// N.H still spreads into a flat patch on near-flat forms, thins to streaks on fingers and pops as glints at night. If the
/// night skin wants more life, the route is a low, wide sheen from the key light only, masked off the hands.)
/// The head's forehead, cheeks, temples and jaw are broad forms too: the same disc drew pale, hard-edged patches there
/// (her Look and close-up, an NPC's jaw; 13 Nov). So on our base head (hers and every NPC's on it) the disc is kept by
/// SparkMap, where the head is tightly curved (nose tip, lips, lids' rims, ears: tools/assets/heroine_spark.py), and
/// gone elsewhere; People.BaseHead sets it as heroine_skin.gdshader's spark_map (spark_mask 1).</summary>
public static class SkinHighlight
{
    /// <summary>Our base head's spark map: 1 where the head keeps the hard highlight, 0 on its broad forms.</summary>
    public const string SparkMap = "res://art/people/head_tex/heroine_spark.png";

    /// <summary>The cel highlight's strength (cel_spec.z) a skin part is given, or null to keep the shader's own (CEL_SPEC).</summary>
    public static float? Strength(string part) => part == "skin_head" ? null : 0f;

    /// <summary>The cel model's stepped rim (cel_rim_k) a skin part is given, or null to keep the shader's own. The head
    /// takes none: its rim, an n.v band on the key's side, lit flat planes inside the face (a stripe down the side of the
    /// nose, a band down the temple and cheek in front of the ear, a notch at the eye's corner, specks along the
    /// hairline) that read as paint or a scar at the Look and dialogue framings (head highlight judge r1, 13 Nov).
    /// Without it the face's outline still reads against hair and background. The body keeps it by day (the owner,
    /// 13 Nov: the cream line "looks good", the Marvel Rivals look). At night skin takes none, via the preset's CelSkinRim
    /// (Atmospheres.Night; the cel_skin_rim global): on her shoulders, neck base and cleavage the moon's rim stepped into
    /// lilac-white specks and lines (the close-up and play) and a pink band on her shoulder at the Look; gone with it 0.</summary>
    public static float? RimShare(string part) => part == "skin_head" ? 0f : null;

    /// <summary>body_p1's fold map (tools/assets/body_fold.py): 1 on the breast's underside, where the stepped rim, an n.v
    /// band on the key's side, drew a cream line inside her form against her ribs (13 Nov, the owner); 0 everywhere else,
    /// so the line stays on her outline, armpit, creases, thighs and elbows. People.NpcSkin sets it as heroine_skin.gdshader's
    /// rim_fold_map (rim_fold 1) on a body skin with body_p1's triangle count (its topology, so its UVs).</summary>
    public const string FoldMap = "res://art/people/body_p1/fold.png";
}
