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

    /// <summary>The same for the sky's own light (the ambient) alone (heroine_skin.gdshader sky_skin_amb; over 1 the sky's hue
    /// turns a little warm on her). Where the night sky is her only light, the shaded side of her neck under her jaw at the
    /// Look, SkyKeep's half left her skin a near-neutral grey (Oklab C .012, h 284) under the grade, outside its skin spare
    /// (hue 15-90, chroma .012-.025 up), and its painted moon shadow took that to navy (C .055 h 257). At 1.5 the neck goes in
    /// at skin chroma and comes out a muted violet-grey (C .025 h 281) under a brown jaw shade; by day and in the close-ups
    /// it moves nothing measurable (the sky is a small share of their light). 1.0 left C .050, 1.6 mottled.</summary>
    public const float SkyKeepAmbient = 1.5f;

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

    /// <summary>The close-ups' day rig key (rigs.json close_day key.intensity, times the world's sun, and key.color). At
    /// 1.25 her lit forehead and cheeks clipped under AgX to near white (Oklab L .91, C .053) beside a warm body. With her
    /// head's paint at her body's level (HeadPaintLevel) the orange key (#ffc296) and her warm cel tone turned face and body
    /// alike orange (C .13-.16, h 45-47) with the face still clipping red (R 250+ on 36% of it); the paler key at 0.85 with
    /// CelTone: face R 250+ on 1%, forehead L .78 C .117 h 61, chest L .78 C .135 h 53, one tan skin (13 Nov r2).</summary>
    public const double CloseDayKey = 0.85;
    public const string CloseDayKeyColor = "#ffd8b4";

    /// <summary>Her skin's warmth under cel (People.HerCelTone, the skin shader's cel_tone on her albedo, every part; an NPC's
    /// is derived from it). (1.39, 0.80, 0.54) read spray-tan orange on her body by day (h 45-47) once her face matched it;
    /// this keeps her warm and moves her hue to about 50-55 (13 Nov skin-light r2).</summary>
    public static readonly (float R, float G, float B) CelTone = (1.16f, 0.86f, 0.72f);

    /// <summary>The soft rim (heroine_skin.gdshader `rim`, an n.v lobe stepped hard under cel) a skin part is given, or
    /// null to keep its own. On the body its narrow lobe, stepped, broke on the normal map into small lilac-white specks
    /// along her shoulders at the night close-up (isolated 13 Nov: rim 0 and they are gone; cel_rim_k 0 left them). The
    /// body keeps the cel model's own stepped rim (cel_rim_k) for its outline; the head keeps its soft rim.</summary>
    public static float? SoftRim(string part) => part == "skin_head" ? null : 0f;

    /// <summary>The cel band's half-tone reach on the head (heroine_skin.gdshader cel_band.z, the n.l over the terminator
    /// where the half-tone gives way to the lit level; CEL_BAND's own 0.2 on the body). Her temple's slight hollow sits at
    /// n.l 0.1-0.25 under the Look's key by day, so at 0.2 the half-tone pooled there as a grey smudge on her left temple
    /// (isolated 13 Nov: cel_mid's weight 0 and it is gone; edge_tone, edge_head and the key's shadow bias moved nothing;
    /// a softer step, cel_band.w 0.16, only blurred it). At 0.1 the half-tone stays a band along the terminator.</summary>
    public static readonly (float X, float Y, float Z, float W) HeadCelBand = (0f, 0.06f, 0.1f, 0.08f);

    /// <summary>Her head's paint brought to her body's level where the Look's portrait rig is off (play, the close-ups; the
    /// skin shader's face_world, on her face's paint, the features' blue): her head's paint (heroine_head.jpg, from her
    /// reference photograph) is 1.8-1.9 times her body paint's linear luminance (dbg 13 at the day close-up: forehead
    /// .380, cheek .359, chest .198, belly .208) and paler, and outside the rig nothing took it down, so under the close-ups'
    /// warm key her lit face clipped near white (Oklab L .89 C .063, R 250+ on 77% of it) over an orange body (L .79 C .126),
    /// and its half-tone read as an orange stripe beside the clipped light. Neutral, so her face keeps its own blush against
    /// the body's paint (13 Nov skin-light r2).</summary>
    public const float HeadPaintLevel = 0.58f;

    /// <summary>Her own face's tone at the Look's portrait rig (People.HerFaceTone["own"], the skin shader's face_tone) trimmed
    /// by this: since its fit (chest L + .015, 20 Oct) her face came to sit L .07 over her lit chest and its cheeks C .05 richer
    /// and redder (13 Nov skin-light r2).</summary>
    public static readonly (float R, float G, float B) LookFaceTrim = (0.74f, 0.80f, 0.86f);
}
