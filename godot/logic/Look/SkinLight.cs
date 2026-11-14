namespace SurvivorUnchained.Look;

/// <summary>How the cel model's light lands on skin (hers, A or B, and every NPC's on her base): the rules a skin-lighting
/// judge found broken at 1:1 on 13 Nov, each isolated with --skin-set before it was set here. People.Skin applies them
/// to every skin part it makes (before the --skin-set switch, which still wins).</summary>
public static class SkinLight
{
    /// <summary>How much of the sky's and the fill's own hue skin hands back (heroine_skin.gdshader sky_skin: the hue's
    /// pull divided out by this power, luminance kept). Under cel the sky's light in her shade keeps its own hue (L1 B1c),
    /// and the night sky's saturated indigo, with the rig's blue fill on top, read as hard navy under her nose and lip
    /// and down her shaded neck at the Look and the close-up at night (Oklab h 262-264, C .050-.051), and grey-navy on
    /// an NPC's shaded cheek; by day the lavender fill on a yellower NPC paint read grey-olive. Isolated 13 Nov: with
    /// the key off the shade is still navy; cel_fill_tone 0 takes only part. At 0.5 the night shade sits in the bible's
    /// night band as a muted cool (h 270, C .031); 0.75 turned it brown.</summary>
    public const float SkyKeep = 0.5f;

    /// <summary>The cel half-tone's level on every skin part (heroine_skin.gdshader face_mid, eased in whole, face_mid_mask 0),
    /// the head's since NPC skin r1. The skin's own CEL_MID (0.85, 0.45, 0.38) times her warm paint drew a saturated
    /// orange-red line along every shadow's edge on her body in the sun: round her arm's cast shadow on her side, under her
    /// breasts, at her neck (the day close-up; isolated 13 Nov: cel_mid's weight 0 and it is gone). With the head's cooler
    /// level the edge steps from lit to shade through a muted brown, as her face's does.</summary>
    public static readonly (float R, float G, float B) HalfTone = (0.45f, 0.55f, 0.65f);

    /// <summary>The camera key's shadow bias (GameCloseUp's CelRigKey, the Look's and the close-up's one key on her). At
    /// 0.03 her jaw's shadow fell short of the jaw: a small lit wedge on her neck under her jaw on the shade side at the
    /// Look by day (isolated 13 Nov: 0.01 and it is gone, no acne on her lids; 0.005 put acne under her upper lid).</summary>
    public const float KeyShadowBias = 0.01f;

    /// <summary>The close-ups' day rig key (rigs.json close_day key.intensity, times the world's sun). At 1.25 her lit
    /// forehead and cheeks clipped under AgX to near white (Oklab L .91, C .053) beside a warm body; at 0.8 her face is
    /// L .84, C .10, warm tan as her sheet, and her hair still reads.</summary>
    public const double CloseDayKey = 0.8;

    /// <summary>The soft rim (heroine_skin.gdshader `rim`, an n.v lobe stepped hard under cel) a skin part is given, or
    /// null to keep its own. On the body its narrow lobe, stepped, broke on the normal map into small lilac-white specks
    /// along her shoulders at the night close-up (isolated 13 Nov: rim 0 and they are gone; cel_rim_k 0 left them). The
    /// body keeps the cel model's own stepped rim (cel_rim_k) for its outline; the head keeps its soft rim.</summary>
    public static float? SoftRim(string part) => part == "skin_head" ? null : 0f;
}
