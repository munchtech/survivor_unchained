// Her skin: her paint, warmed to her tone, with light carried under it
// (subsurface scattering, reddened as through flesh); its fine relief, pores
// and the creases between them (tools/assets/skin_pores.py, tiled a pore's
// size whatever her UVs' scale, so the same on her face as on her body),
// bending the light at a glance; its sheen soft and uneven, duller in the
// pores, never the even gloss of plastic; a soft rim at her edges, as the
// fine down on skin catches the light; light through her where she is thin.
shader_type spatial;
render_mode sss_mode_skin, cull_disabled;
// (both sides drawn for her head alone (mouth_in), and only inside her mouth (mouth_c): its inside, seen through her
// open mouth, is the dark of her throat; elsewhere (under her jaw) a back face drew a dark red speck (lips B3 sheet);
// culled, what lay behind it showed through (the smile pass, a2). Every other part's back faces are
// discarded, as culled before.)

uniform sampler2D paint : source_color, filter_linear_mipmap_anisotropic;
uniform vec3 tone : source_color = vec3(1.0, 0.86, 0.74);
// Her pores' tile (RGB its normals, A how rough), and how many tiles to a
// UV unit (People.cs works it out from the mesh: one tile every 9 mm; at
// 1.5 cm they read as large and even on her hands).
uniform sampler2D pores : hint_default_white, filter_linear_mipmap_anisotropic, repeat_enable;
uniform float pore_scale = 30.0;
uniform float pore_depth = 0.6;
// Her skin's own fine grain (tools/assets/heroine_grain.py: her face paint's
// high frequencies, a 2.8 cm tile; 0.5 as she is, 0.25 a 6% change) up her
// neck, whose paint is smooth: against her face it read as another's skin,
// finer and flatter (her portrait's neck has nearly half her face's grain).
// Not on her face (the features' blue), which has its own, and not from her
// collarbones down (her freckles' map's blue): over her body it read as a
// speckle on her breasts, whose skin is smooth but for its pores and
// freckles. Two reads at two sizes, so the tile never shows.
uniform sampler2D grain : hint_default_white, filter_linear_mipmap_anisotropic, repeat_enable;
uniform float grain_amount = 0.0;
uniform float rough = 0.5;
// A package's roughness map (Marionette NPCs: People.NpcSkin), ABSOLUTE roughness in rough_channel (0 R, 1 G, 2 B, 3 A, else R as grey);
// it multiplies `rough`, so NpcSkin sets rough 1.0 with it. Unset it is white (1.0): hers is unchanged.
uniform sampler2D rough_map : hint_default_white, filter_linear_mipmap;
uniform int rough_channel = 1;
uniform float shine = 0.42;
uniform float scatter = 0.38;
// The soft rim the fine down on skin gives against a light from behind.
uniform float rim = 0.25;
// Where her lit side ends, light carried under the skin reaches a little
// past where the surface turns from the lamp, red furthest, so the edge is
// soft and warm, never a hard grey line: each channel's reach past it, in
// N.L (beyond it her light is Godot's own). (Under the portraits' side key
// her lit side's edge ran straight down the middle of her throat as a dark
// line; Godot's screen-space scattering spreads a few pixels at a close-up,
// and spread wider it blurred away her skin's grain.)
uniform vec3 terminator = vec3(0.32, 0.15, 0.1);
// Her skin's colour in the sky's light (the ambient) against the lamps': her colour times this there, the lamps'
// light on her as before (light() divides it back out). Light from all round goes deeper into skin and comes out
// redder than a lamp's from one side; without it, the night sky's blue in her jaw's shadow, the only light there,
// made her neck under it grey-violet (Oklab hue 31° against her portraits' 51°) on every face (the owner,
// 10 October 2026). 1 (his) as before.
uniform vec3 ambient_tint = vec3(1.0);
// Her share of the sky's light (the ambient), every lamp's light on her kept (light() divides it back out). The town's
// close view by day (GameCloseUp, face 34): the waystation's grey-blue sky (hemi 0.9, env 0.8) was the largest light on
// her face, level on every plane (it lifted the shade side of her jaw 31.7 to 45 Oklab L), so her face read flat, pale
// and grey, as under a flash. 1 everywhere else.
uniform float sky_share = 1.0;
// Her sheen's strength (SPECULAR), for her light() to read.
varying float sheen;
// Rougher where the skin is seen edge on: there a light from behind
// glanced off it as a hard white band (the Fresnel peak a matte skin's fine
// hairs and pores break up).
uniform float edge_rough = 0.0;
// Her face's features drawn bold (tools/assets/heroine_features.py: red her
// eyes and brows, green her lips), deepened the smaller her face is on
// screen: from the game's camera her face is a few pixels across, and her
// paint's mipmaps average her eyes, brows and lips into her skin. Measured
// as how many of her paint's texels a pixel covers (2^far_from to 2^far_to):
// none at the book's view (her face 100 pixels tall, where it read as a
// shadow round her eyes), all of it at play's (8 to 16 pixels).
uniform sampler2D features : hint_default_black, filter_linear_mipmap;
// Her head's own shade where light reaches it less (tools/assets/heroine_features.py's
// heroine_ao.png: under her jaw and chin, her nostrils, the corners of her mouth),
// on the light round her and on some of her lights' too (as a soft shadow).
uniform sampler2D ao_map : hint_default_white, filter_linear_mipmap;
uniform float ao_light = 0.0;
// (her lips parted (HerFaceLife.MouthShade, 0 shut to 1 by mouth_open 0.3): the shade ao_map bakes where her lips
// meet, right for them shut, is eased up to lip_ao_open on her lips (features' green): opened, the inner faces of her
// lips came out of that bake near black, her lower lip's top a black band under her teeth (c04a A5, judge F1, face 29))
uniform float lips_apart = 0.0;
uniform float lip_ao_open = 0.9;
// (and her paint there lifted to at least lip_floor (linear, times her tone's lightness), up to lip_gain times, as they
// part: her portrait paints a dark line where her lips meet and darker inner faces (about half the lips' lightness),
// and with the bake eased her lower lip's top still read as a black band under her teeth (c04a A5, judge F1, face 30).
// Both over her lips and the strip between them, which the features' green leaves out: that green blurred (its mip
// lip_mip) past lip_zone; lip_ao_open eased over it too. lip_gain 1: as face 29's, on the features' green alone)
uniform float lip_floor = 0.15;
uniform float lip_gain = 5.0;
uniform float lip_mip = 4.0;
uniform float lip_zone = 0.3;
// (all of it eased out from mouth_open 0.3 to 0.6 (HerFaceLife.MouthShade): wide open, her paint's line lifted read as a
// red rim inside her lower lip, so there, as face 29's)
uniform float lips_narrow = 0.0;
// (lip_tone 1: the lift ends at her own lip colour in shade instead (her paint blurred to its mip lip_cmip, times her
// tone: her lips' mean colour, their dark line averaged in), eased lip_sat of the way to its grey, times lip_dark where
// her paint is darker than that, and times lip_bake where the bake shades her lips' meeting (ao_map, 1 - its red from
// lip_bake_from to lip_bake_to), there whatever the paint, so the lamps shade it as her lip (and lip_glow of that emitted: the light
// her teeth throw back on it); her lips' sheen there cut to lip_spec.
// Lifted by lip_floor alone her paint's dark line kept its own hue: a lit red band along her lower lip's top (own),
// and with the sheen the lifted AO let back, a pale grey-lavender strip (Sunborn) (c04a A5, judge F1 r2, face 30))
uniform float lip_tone = 1.0;
uniform float lip_cmip = 5.0;
uniform float lip_sat = 0.7;
uniform float lip_dark = 0.8;
uniform float lip_spec = 0.25;
uniform float lip_bake = 1.2;
uniform float lip_glow = 0.0;
uniform float lip_bake_from = 0.15;
uniform float lip_bake_to = 0.5;
// Her ears' hollows, a shade of their own (heroine_ear_ao.png, tools/assets/heroine_ear_ao.py; white elsewhere):
// multiplied into AO, dimming her lamps there by ear_light (not ao_light), and warming her paint by it (ear_tint).
// The cool fill and sky reached into her ear's bowl, grey-white in a warm ear (judge rj5v). Off at ear_amount 0.
uniform sampler2D ear_ao : hint_default_white, filter_linear_mipmap;
uniform float ear_amount = 0.0;
uniform float ear_light = 0.0;
uniform vec3 ear_tint = vec3(1.0);
// Her head's own skin eased into her graft's over the 3 cm above her neck's seam (SPLIT), by ao_map's green
// (1 on her head, 0 at SPLIT: tools/assets/heroine_ao_seam.py): side on, her head's more matte, deeper-pored,
// grained skin met the graft's as a stair-stepped line across her neck (judge n1, 11 October 2026).
uniform bool seam_ease = false;
uniform float seam_rough = 0.5;
uniform float seam_shine = 0.42;
uniform float seam_depth = 0.4;
// (her grain's tiles to a UV unit, over pore_scale: a surface's own, set by People.Skin, as a mesh's pore_scale is
// the mean of its surfaces' and on her graft, a small part of her body's mesh, put her grain's tile at 9 mm, not 28)
uniform float grain_scale = 0.0;
// Her freckles, a layer of their own (tools/assets/heroine_freckles.py: red
// each freckle, soft at its edge; green its rank), none to heavy: at an
// amount, those ranked under it show, deeper the more there are, in a warm
// brown laid over her skin's own colour.
uniform sampler2D freckles : hint_default_black, filter_linear_mipmap;
uniform float freckle_amount = 0.0;
uniform vec3 freckle_colour = vec3(0.62, 0.45, 0.33);
uniform float far_from = 4.5;
uniform float far_to = 6.5;
uniform float far_dark = 0.86;
uniform vec3 far_lips : source_color = vec3(0.62, 0.16, 0.15);
// The features' mask read at this pixel's own level of detail, but never
// coarser than far_mip of its own mipmaps, and drawn far_bold times as
// strong: at play zoom (her face 8 pixels across) a mip that fits the pixel
// averages each eye into a texel of skin, and her face was a blank. Coarser
// than this the marks blur into one another; finer, they flicker.
uniform float far_mip = 3.0;
uniform float far_bold = 3.0;
// Her face's own colour against her portrait's (People.HerFaceTone, in
// linear light), laid where her face's paint is (the features' blue): each
// face's paint a few per cent off its portrait, her neck and body untouched.
uniform vec3 face_tone = vec3(1.0);
// Her lit neck and body paler than her face (People.HerBodyLift): her portraits' lit necks and upper chests sit
// 0.05-0.1 lighter (Oklab L) than their cheeks, ours level with them. The key's light only (every lamp but the soft
// ones, as shade_by_soft tells them): laid on her paint, it lit the shade under her chin too (0.05-0.14 over the
// portraits'). Her head takes it below the 3 cm over her neck's seam (ao_map's green), so her face and ears keep
// their fitted tone.
uniform float body_lift = 1.0;
// (none where she faces down (world normal's y under lift_from, all over lift_to): lit from the front, the shade
// under her chin took it too. From -0.45: from -0.15 her neck's upright skin took half of it and the notch's upper
// wall none, so at today's neck length it sat .03-.08 short of the portraits' (judge j6))
uniform float lift_from = -0.45;
uniform float lift_to = 0.15;
// Her shade's own colour off her face (People.HerSoftTone, linear): the soft lamps' light (shade_by_soft) on her neck
// and under her jaw, outside her face's paint (the features' blue), times this: under her jaw her portraits' shade is
// richer, and on the fairest faces darker, than her head's own skin there shows (judge j5).
uniform vec3 soft_tone = vec3(1.0);
// Her neck's and body's colour in every lamp but the soft ones (People.HerKeyTone, linear), outside her face's paint,
// its lightness kept. Her body's tone (People.HerBodyTone) was fitted where the key and the warm fill meet on her lit
// neck; the fill shows her paint without it, so the key's share was driven to grey (white-lit neck Oklab C .015): where
// the fill can't reach, the far side of her neck under her jaw went blue-grey (hue -61), and in the moon her whole body
// lavender under a peach face (the owner, 10 October 2026; face 21). 1 as before.
uniform vec3 key_tone = vec3(1.0);
// Her neck and body richer where she turns from the lens (People.HerEdgeTone, linear, on key_tone, its lightness kept):
// her portraits' neck sides are richer than their lit fronts (Oklab C 1.6 times), ours were 0.7-0.8 times at every
// key_tone, the far side of her neck lit by the key at 0.8 of her lit neck's light (face 22). Weighted by
// 1 - smoothstep(edge_from, edge_to, n.v), below her head (ao_map's seam ease), so her face and ears keep theirs.
uniform vec3 edge_tone = vec3(1.0);
uniform float edge_from = 0.2;
uniform float edge_to = 0.7;
// (kept to her neck by her freckles' map's blue, 0 from her collarbones down and on parts without the map: on her
// limbs' silhouettes it turned her thighs and arms a richer, bluer pink in the whole frame, judge j7 (f); 0 as r11)
uniform float edge_neck = 1.0;
// The lamps behind her (the Look's cool rim and the fire's edge lamp, neither with a shadow) shaded by her head's own
// shade (ao_map's red), back_occ of it: her jaw never shaded the rim, which lit the far side of her neck under her jaw
// as brightly as the key, a cool grey-lilac band there on the fair faces (the owner, 10 October 2026; skin r12: with
// the rim off, own's row .15 hue -21 to -8). 0 none (r12). (Tried at 1, skin r13 B1: own's row .15 -25 to -23, no
// help: ao_map is white there, its bake has no shade under her far jaw. Wants a shadow on the rim, or a map that has it.)
uniform float back_occ = 0.0;
// Her neck's and body's colour under the sun and the moon (directional lamps), in place of key_tone, outside her face's
// paint, its lightness kept (People.HerSkyTone). HerBodyTone's blue was fitted against the Look's warm key; under the
// moon nothing warms it back, and in the whole frame her body read lavender-blue under her face (judge j7 (f)).
// 0: as key_tone (r12).
uniform vec3 sky_tone = vec3(0.0);
// Her body's tone (People.BodyTone, linear), which `tone` carries and ambient_tint and shade_tint take back out: with
// body_gate 1, kept on her head and up her neck, where it was fitted, and from her collarbones down taken out of the
// lamps' light on her, with the key's and the soft lamps' tones fitted with it (key_tone, sky_tone, soft_tone), by her
// freckles' map's blue (neck_w: 0 on parts without the map; her head keeps it all, as that map's blue dips under her
// jaw). Its blue was fitted on her lit neck against the Look's warm key; over her chest, arms and thighs it read a cold
// lilac-grey beside the fire and in the moon, where they were warm peach (judge s1, 12 October 2026). The sky's light
// on her (ambient_tint) is as before. body_gate 0: as before (--body-gate off).
uniform vec3 body_tone = vec3(1.0);
uniform float body_gate = 0.0;
// How much of the Look's portrait rig lights her (GameFront's portrait light, 0 for her whole figure, 1 from head and
// shoulders in; 0 in play). Her head's tones above (body_tone kept up her neck, key, sky, soft and edge tones, and her
// face's face_tone) were all fitted under that rig, its key with the soft fill showing her paint without body_tone; under
// the fire, the moon and the sun alone (every lamp a key) her head and neck kept body_tone's blue, pale blue-white over a
// warm firelit body in the Look's whole frame (judge rj1v, 12 October 2026: neck Oklab hue -86 against her chest's +8).
// Outside the rig her head takes her body's treatment and her face face_world (People.HerFaceToneUntrimmed, her face's
// own tone against its portrait, before the rig's fit). 1: as fitted, in every light (--head-rig off).
uniform float look_rig = 0.0;
uniform vec3 face_world = vec3(1.0);
// (the factor her paint takes for it, 1 where it is kept and 1 / body_tone where it is taken out, and how much of the
// tones fitted on her neck she takes, 1 on her head and neck, 0 from her collarbones down)
varying vec3 body_back;
varying float neck_w;
// A body's own relief, baked from its sculpt (the hero's: every muscle and
// vein his reduced mesh has only in paint), the pores laid over it.
uniform sampler2D relief : hint_normal, filter_linear_mipmap_anisotropic;
uniform bool has_relief = false;
// A man's shaved shadow (the hero's: People.HisShadow): where his beard and
// his hair grow (shadow_mask, red his beard's ground, green his scalp's),
// each as dark as chosen, of the hair's own colour; stubble, not a stain:
// the darkening broken into the stubs of hairs.
uniform sampler2D shadow_mask : hint_default_black, filter_linear_mipmap;
uniform float beard_shadow = 0.0;
uniform float scalp_shadow = 0.0;
// (his scalp shaved, its shadow the stubs of hairs; hers under her hair, an
// even shade: broken into dots, her hairline read as speckled)
uniform float scalp_stubs = 1.0;
uniform vec3 shadow_colour : source_color = vec3(0.16, 0.12, 0.1);
// (how far her scalp's shade goes to shadow_colour where its mask is full: 0.85 as his stubble; hers 1.0
// (People.HerScalp), as what stayed of her head's paint under it, a pale grey-cream, greyed the shade at her
// hairline to Oklab C 0.06 against her hair's and forehead's 0.09: face 32, 20 October)
uniform float scalp_max = 0.85;
// (and its hue ahead of its dark, where it thins out at her hairline: its tint (shadow_colour at a luminance of 1) and
// its dark laid one after the other, the tint at ws^scalp_lead, the dark at ws, so the same where it's full but
// half-way her skin already her hair's hue, not darkened toward grey. 0: one mix, as before (his). Hers 1.0
// (People.ScalpLead): her hairline's band C 0.061-0.073 at the Look, front, to 0.088-0.091; under 1 overshot, a
// saturated rim at C 0.11.)
uniform float scalp_lead = 0.0;
// (its tint by her skin's lightness against her own fair's (tone's luminance over scalp_hue_ref): red
// hair's tint is over 1 in red, and on Sunborn's brown and on deep skin it left a red-orange rim under her front hair
// and down her temples, face 32 r2; her own fair as it was. scalp_hue 0: the tint at full on every skin, as round 1)
uniform float scalp_hue = 1.0;
uniform float scalp_hue_ref = 0.75;
// (and its dark the same way, down to this much of it on the darkest skin: on deep skin her scalp's shade laid a darker
// band beside the pale curve down her temple (face 32 r2), and her own skin, dark already, has no pale scalp to hide)
uniform float scalp_dark_min = 0.4;
// His brows (painted with his face; the blue of shadow_mask) dyed his
// hair's colour: their paint scaled from its own colour (brow_paint) to
// brow_colour, every hair of it kept.
// Paint on her face (People.HerPaint: art/people/paint/ID.png, laid out on her head's paint by
// tools/assets/heroine_paint.py), drawn in her skin, so it takes her skin's light exactly (her key, soft, edge
// and sky tones, her shade's tint, the Look's rig): as a pass of its own, under Godot's light, the woad read lit
// from within beside her skin (face 31). Laid over her paint after her tone, so it keeps its own colour; her
// skin's grain and a little of her pores through it; its own roughness and sheen, and the gilt's metal.
uniform sampler2D face_paint : source_color, hint_default_transparent, filter_linear_mipmap_anisotropic;
uniform bool has_face_paint = false;
// (where no paint may go, whatever it is: her nostrils, her nose's wings and their creases, white elsewhere;
// tools/assets/heroine_nostril_mask.py. Every paint looked off where it reached her nostrils: the owner, 20 Oct)
uniform sampler2D face_paint_keep : hint_default_white, filter_linear_mipmap;
uniform float paint_rough = 0.7;
uniform float paint_metal = 0.0;
uniform float paint_shine = 0.5;
// (how much of her pores' relief is kept under it, and of her light carried under the skin)
uniform float paint_pores = 0.6;
uniform float paint_scatter = 0.5;
// (the paint's share of a texel, for light(): it takes her light's strength, its softness at the terminator, her
// shade and AO, but not her skin's colour fits (ambient_tint, key/sky/edge/soft tones, shade_tint), which are
// fitted to her skin against her portrait: through them a grey ash came out her skin's own peach and vanished)
varying float paint_w;
uniform float brow_dye = 0.0;
uniform vec3 brow_paint : source_color = vec3(0.2, 0.15, 0.12);
uniform vec3 brow_colour : source_color = vec3(0.2, 0.15, 0.12);

// Her skin under her outfit's fitted pieces, tucked up to 8 mm in, and a
// nipple's tip under a plate 10 (less let it through for a pixel as she
// swung an axe)
// (heroine_outfits.py marks it, graded from a piece's edge, in the channel
// of her vertex colours tuck_channel names): it never shows through what
// she wears, and as nothing of her is cut away no gap opens in her where a
// piece swings off her.
// A full tuck is marked 0.98 (0.973 and over reads as all of it); a mark of
// 1 is skin not drawn at all, inside a piece that closes round her: her hands
// in the Arcanist's gloves, which no tuck keeps in (a finger is thinner than
// it) and whose wrist came through the glove's back as it bent.
// tuck_channel -2: the tuck read from tuck_map instead, a value a vertex (VERTEX_ID, row by row,
// tuck_map_width wide): the largest of the tucks of the pieces she wears (HerWear), marked as above.
uniform int tuck_channel = -1;
uniform float tuck = 0.010;
uniform sampler2D tuck_map : filter_nearest, repeat_disable;
uniform int tuck_map_width = 1;
varying float tuck_gone;

// The light through her (BACKLIGHT): how much, its colour, and how far it is kept to lamps behind her (it has no
// thickness mask: from a lamp in front it lit the underside of her jaw, away from it, red).
uniform float backlight = 0.18;
uniform vec3 backlight_colour = vec3(1.0, 0.45, 0.35);
uniform float backlight_behind = 0.0;
// (how far the light through her is kept to where she is thin, by ao_map's blue (heroine_thin.py: her ears, the
// wings of her nose): unmasked, the underside of her jaw, turned from the key, took a salmon line along its edge.
// Under the Look's rig only (look_rig), as is her head's rim kept to lamps behind her: the rig has its own fill and
// bounce, but outside it (play, cinematics, the Look's whole frame) these two were her head's only light on the side
// turned from a lamp, as they are her body's; without them, by the overhead lantern at night, her lower face, jaw
// and nostrils fell to the night sky's blue-black under a lit neck (judge rj2v, 12 October 2026).)
uniform float thin_map = 0.0;
// (her head's rim from every lamp, as her paint's light through her: her head outside the rig, eased out over the
// 3 cm above SPLIT (ao_map's green); her body keeps it to lamps behind)
varying float front_rim;
// Her shade richer (a lamp's light where it reaches her at a low angle, ndl shade_from to shade_to, times shade_tint,
// its lightness kept): where she faces down (shade_down, world normal's -y from down_from to down_to) and where
// ao_map's alpha says (shade_zone). (Tried 11 October 2026: ungated it misses the shade under her jaw, lit there
// by the fill at a high ndl; a test switch, 1 none.)
uniform vec3 shade_tint = vec3(1.0);
uniform float shade_from = -0.2;
uniform float shade_to = 0.5;
uniform float shade_down = 0.0;
uniform float down_from = 0.0;
uniform float down_to = 0.6;
uniform float shade_zone = 0.0;
// (shade_by_light 1: the gate is each lamp's own light at the point (its colour's luminance times ndl and attenuation,
// shadow included), not ndl: under her jaw the fill reaches her at a high ndl but weakly, and the key's soft shadow
// falls there, so ndl called it lit and her body's tone (set for lit skin) greyed it; the key at a low angle on her
// lower cheek is still strong, so that stays as fitted)
uniform float shade_by_light = 0.0;
// (shade_by_soft 1: the gate is the lamp's own sheen (SPECULAR_AMOUNT, 2x its light_specular): the Look's fill (0.1)
// and bounce (0) are its soft lamps, and her shade is theirs, so they show her paint's own colour and the key (0.3)
// her body's tone at every angle; by light, the key's weak light at her jaw's edge took her paint's colour, an
// orange band along it)
uniform float shade_by_soft = 0.0;
// (thinned, shade_thin of it, on her jaw's underside, where she faces down (world normal's -y thin_from to thin_to):
// lit there by the soft lamps alone, the warm bounce from below most, it showed her paint's own colour at full, an
// orange-brown wedge from her jaw's angle to her chin with her head turned (Oklab C 1.6 times her lit skin's, own at
// 80 degrees; face lead 19, 13 October 2026). Her cheeks face down 0.36-0.47 at the Look, her jaw's shade on her neck
// under 0.4, and keep it all. (Tried: its saturation capped at 1.4 times her paint's own took the fill's warmth too,
// the front view's jaw shade C 0.035 to 0.028; by ao_map's shade, it is as deep on her neck. 0: as before.)
uniform float shade_thin = 0.75;
uniform float thin_from = 0.4;
uniform float thin_to = 0.75;
// Her rim (`rim`) kept to where the lamp reaches her (rim_gate: smoothstep(0, 0.3, ndl)), and how much of her colour.
uniform float rim_gate = 0.0;
uniform float rim_tint = 0.6;
// The sheen a lamp behind her gives, against one in front (People.HerBackSpec): skin's fine relief breaks up a light
// that grazes it from behind; at full, the cool rim lamp lay over her collarbones and upper chest as a lilac sheen.
uniform float back_spec = 1.0;
// (a developer's view, --skin-set *:dbg_gate=1 with --look-ambient 0 --tonemap linear --grade off: each lamp's light at
// the point, shadow and its angle in (ATTENUATION times ndl, times dbg_gate), red the key's path in front of her, green
// the soft lamps, blue the lamps behind her)
uniform float dbg_gate = 0.0;
varying float shade_w;
varying float lift_w;
varying float soft_w;
varying float edge_w;
varying float back_ao;
// The inside of her mouth (heroine_mouth.py: her head's vertex colour's alpha, 1 outside, falling to 0 deep in her
// mouth): her paint there (a lilac-grey island, an orange-brown cheek wall) and every lamp's light, unshadowed at
// this scale, showed it as a lit box with an orange glow (judge rj3). There it takes mouth_colour, a wet dark red,
// and the light falls off with depth to mouth_occ of none (all of it: the sky's by AO, the lamps', its rim, the
// light through her and its sheen). mouth_in 1 for her head only (People.HerPart); 0, as before.
uniform float mouth_in = 0.0;
uniform vec3 mouth_colour : source_color = vec3(0.42, 0.15, 0.14);
uniform float mouth_occ = 0.93;
// (a little of its own colour given off, so the shade inside reads as a deep red, not a black hole; less with depth)
uniform float mouth_fill = 0.2;
// (her mouth's corners, the crease where her lips meet (heroine_mouth.py: her head's vertex colour's red, 1 or down
// to 0 there): in her smile it folds in, and the lamps behind her lit it, an orange-brown wedge through her skin's
// light (the smile pass, e3); shadows at this scale don't reach it. corner_shade of the lamps behind her cut there:
// all of them made a grey smudge on her cheek by the corners, f2)
uniform float corner_shade = 1.0;
// (how far her smile folds her corners in, 0 to 1, from her smile's blend shape (HerFaceLife.MouthShade): the cut by it)
uniform float fold = 1.0;
// (the most one lamp's sheen gives, in linear light: 0.2 took the c02 s8 cheek from 877-4176 clipped pixels to 0-74, the
// Look by day and night and the town close-up unchanged (face 30 cine; 0.3 left 252, 0.12 dulled her cheek 8 L))
uniform float spec_cap = 0.2;
// (and a metal's: the gilt's leaf, half metal; at 1.5 its full-metal glint clipped to a lemon-yellow spot on her right
// cheek at the Look, face 32 r2: a gold sheen under 0.8)
uniform float metal_cap = 0.8;
varying float crease;
// (her inner cheeks beside her lower back teeth (heroine_mouth.py: her head's vertex colour's green, 1 or down to 0
// there): the mouth's colour there darkened by wall_dark and greyed by wall_grey (linear), so they don't read as a
// saturated red-pink lit wall beside her far lower row (solver int3))
uniform float wall_dark = 0.3;
uniform float wall_grey = 0.8;
uniform vec3 wall_tint = vec3(1.0, 0.88, 0.78);   // (the grey it goes to, warmed: blue under green, a dark maroon like the cavity, judge r4)
varying float mouth_w;
varying float mouth_c;
varying float mouth_f;

void vertex() {
	mouth_c = mouth_in * (1.0 - COLOR.a);
	crease = mouth_in * (1.0 - COLOR.r);
	mouth_w = mouth_in * (1.0 - COLOR.g);
	tuck_gone = 0.0;
	if (tuck_channel >= 0) {
		float h = tuck_channel == 0 ? COLOR.r : tuck_channel == 1 ? COLOR.g : tuck_channel == 2 ? COLOR.b : COLOR.a;
		tuck_gone = step(0.995, h);
		VERTEX -= NORMAL * tuck * (h > 0.973 ? 1.0 : h);
	} else if (tuck_channel == -2) {
		float h = texelFetch(tuck_map, ivec2(VERTEX_ID % tuck_map_width, VERTEX_ID / tuck_map_width), 0).r;
		tuck_gone = step(0.995, h);
		VERTEX -= NORMAL * tuck * (h > 0.973 ? 1.0 : h);
	}
}

void fragment() {
	if (tuck_gone > 0.5 || (!FRONT_FACING && (mouth_in < 0.5 || mouth_c <= 0.0))) {
		discard;
	}
	vec2 tx = UV * vec2(textureSize(paint, 0));
	float lod = 0.5 * log2(max(dot(dFdx(tx), dFdx(tx)), dot(dFdy(tx), dFdy(tx))));
	float far = smoothstep(far_from, far_to, lod);
	float fl = clamp(lod - log2(float(textureSize(paint, 0).x) / float(max(textureSize(features, 0).x, 1))), 0.0, far_mip);
	vec3 fm = textureLod(features, UV, fl).rgb;
	vec4 aot = texture(ao_map, UV);
	float hw = seam_ease ? aot.g : 1.0;
	float rig_w = clamp(look_rig, 0.0, 1.0);
	ALBEDO = texture(paint, UV).rgb * tone * mix(vec3(1.0), mix(face_world, face_tone, rig_w), fm.b);
	float lip_w = lip_gain > 1.0 ? lips_apart * lips_narrow * smoothstep(lip_zone, lip_zone + 0.25, textureLod(features, UV, lip_mip).g) : 0.0;
	if (lip_w > 0.0) {
		float lum0 = max(dot(ALBEDO, vec3(0.2126, 0.7152, 0.0722)), 1e-4);
		if (lip_tone > 0.0) {
			vec3 lc = textureLod(paint, UV, lip_cmip).rgb * tone * mix(vec3(1.0), mix(face_world, face_tone, rig_w), fm.b);
			float ll = dot(lc, vec3(0.2126, 0.7152, 0.0722));
			vec3 lt = mix(vec3(ll), lc, lip_sat) * lip_dark;
			float lum_t = max(ll * lip_dark, 1e-4);
			ALBEDO = mix(ALBEDO, lt, clamp(4.0 * (1.0 - lum0 / lum_t), 0.0, 1.0) * lip_w * lip_tone);
			float lip_b = smoothstep(lip_bake_from, lip_bake_to, 1.0 - aot.r) * lip_w * lip_tone;
			ALBEDO = mix(ALBEDO, lt * lip_bake / lip_dark, lip_b);
			EMISSION += lt * lip_bake / lip_dark * lip_glow * lip_b;
		} else
			ALBEDO *= mix(1.0, clamp(lip_floor * dot(tone, vec3(0.2126, 0.7152, 0.0722)) / lum0, 1.0, lip_gain), lip_w);
	}
	vec3 fk = texture(freckles, UV).rgb;
	neck_w = mix(1.0, seam_ease ? 1.0 : fk.b, body_gate) * rig_w;
	body_back = pow(max(body_tone, vec3(1e-3)), vec3(neck_w - 1.0));
	ALBEDO *= body_back;
	if (freckle_amount > 0.001) {
		float fv = fk.r * (1.0 - smoothstep(freckle_amount - 0.04, freckle_amount + 0.04, fk.g));
		ALBEDO = mix(ALBEDO, ALBEDO * freckle_colour, fv * mix(0.5, 1.0, freckle_amount));
	}
	if (brow_dye > 0.0) {
		// (the hairs' own lightness kept, their black core lifted a little,
		// so a fair or red man's brows are not black ones tinted)
		float bm = texture(shadow_mask, UV).b * brow_dye;
		vec3 lw = vec3(0.3, 0.59, 0.11);
		float l = dot(ALBEDO, lw) / max(dot(brow_paint * tone, lw), 0.02);
		ALBEDO = mix(ALBEDO, brow_colour * tone * pow(clamp(l, 0.0, 1.15), 0.5), bm);
	}
	float pa = 0.0;
	if (has_face_paint) {
		vec4 fp = texture(face_paint, UV);
		pa = fp.a * texture(face_paint_keep, UV).r;
		ALBEDO = mix(ALBEDO, fp.rgb, pa);
	}
	paint_w = pa;
	vec2 f = fm.rg;
	if (far > 0.0) {
		// (the marks grown to the pixel: the most of them anywhere in it, from its
		// corners, so an eye a third of a pixel high still darkens a whole one;
		// sampled at its middle, her eyes at play zoom were missed one frame in two)
		vec2 hx = 0.5 * dFdx(UV), hy = 0.5 * dFdy(UV);
		f = max(max(f, textureLod(features, UV + hx + hy, fl).rg), max(textureLod(features, UV + hx - hy, fl).rg,
			max(textureLod(features, UV - hx + hy, fl).rg, textureLod(features, UV - hx - hy, fl).rg)));
	}
	f = clamp(f * far_bold, 0.0, 1.0) * far;
	ALBEDO *= 1.0 - far_dark * f.x;
	ALBEDO = mix(ALBEDO, far_lips * tone, 0.75 * f.y * (1.0 - pa));
	// (two offset tiles, so no grid shows, their depth varying over her in
	// soft patches as real pores do)
	vec4 q = mix(texture(pores, UV * pore_scale), texture(pores, UV * pore_scale * 0.77 + vec2(0.53, 0.19)), 0.35);
	float patchy = smoothstep(0.2, 0.8, texture(pores, UV * pore_scale * 0.07 + vec2(0.31, 0.67)).a);
	float depth = mix(seam_depth, pore_depth, hw) * mix(0.35, 1.0, patchy) * mix(1.0, paint_pores, pa);
	// (where her freckles' map says, its blue: her head and up her neck, none from her collarbones down)
	float ga = grain_amount * (1.0 - fm.b) * fk.b;
	if (ga > 0.0) {
		// (a tile every 28 mm: pore_scale is a tile every 9; the two reads' mean has
		// 0.71 of one's spread, given back)
		vec2 gu = UV * (grain_scale > 0.0 ? grain_scale : pore_scale * 0.321);
		float gr = texture(grain, gu + vec2(0.37, 0.11)).r + texture(grain, gu * 0.71 + vec2(0.83, 0.59)).r - 1.0;
		ALBEDO *= 1.0 + ga * gr * 0.707 * 0.24;
	}
	float stubble = 0.0;
	if (beard_shadow > 0.0 || scalp_shadow > 0.0) {
		vec2 g = texture(shadow_mask, UV).rg;
		// (the stubs: the pore tile's grain, finer, as dots)
		float stubs = smoothstep(0.3, 0.7, texture(pores, UV * pore_scale * 1.62 + vec2(0.37, 0.11)).a);
		float dots = mix(0.55, 1.0, stubs);
		stubble = clamp(g.r * beard_shadow * dots + g.g * scalp_shadow * mix(1.0, dots, scalp_stubs), 0.0, 1.0);
		float wb = g.r * beard_shadow * dots * 0.85, ws = g.g * scalp_shadow * mix(1.0, dots, scalp_stubs) * scalp_max;
		vec3 sc = shadow_colour * 2.4;
		if (scalp_lead <= 0.0) ALBEDO = mix(ALBEDO, ALBEDO * sc, clamp(wb + ws, 0.0, 0.85));        // (as before: stubble * 0.85)
		else {
			// (her scalp's shade: its hue ahead of its dark, so where it thins out at her hairline her skin goes
			// toward her hair's colour before it darkens, not grey; all of it, the same, where it's full)
			ALBEDO = mix(ALBEDO, ALBEDO * sc, clamp(wb, 0.0, 1.0));
			float ls = max(dot(sc, vec3(0.2126, 0.7152, 0.0722)), 1e-4);
			ws = clamp(ws, 0.0, 1.0);
			float tk = mix(1.0, clamp(dot(tone, vec3(0.2126, 0.7152, 0.0722)) / scalp_hue_ref, 0.0, 1.0), scalp_hue);
			ALBEDO = min(ALBEDO * mix(vec3(1.0), sc / ls, pow(ws, scalp_lead) * tk) * mix(1.0, ls, ws * mix(scalp_dark_min, 1.0, tk)), vec3(1.0));
		}
	}
	if (has_relief) {
		// The two reliefs as one (each from its x and y, as Godot keeps a
		// normal map): the pores' slopes added to the body's, at their depth.
		vec2 a = texture(relief, UV).xy * 2.0 - 1.0;
		vec2 b = (q.xy * 2.0 - 1.0) * depth;
		vec3 n = normalize(vec3(a + b, sqrt(max(0.0, 1.0 - dot(a, a)))));
		NORMAL_MAP = vec3(n.xy * 0.5 + 0.5, 1.0);
		NORMAL_MAP_DEPTH = 1.0;
	} else {
		NORMAL_MAP = q.rgb;
		NORMAL_MAP_DEPTH = depth;
	}
	float edge = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 3.0);
	vec4 rm = texture(rough_map, UV);
	float rmv = rough_channel == 0 ? rm.r : (rough_channel == 1 ? rm.g : (rough_channel == 2 ? rm.b : (rough_channel == 3 ? rm.a : rm.r)));
	ROUGHNESS = clamp(mix(seam_rough, rough * rmv, hw) + (q.a - 0.5) * 0.3 + stubble * 0.15 + edge_rough * edge, 0.0, 1.0);
	ROUGHNESS = mix(ROUGHNESS, clamp(paint_rough + (q.a - 0.5) * 0.1, 0.0, 1.0), pa);
	METALLIC = paint_metal * pa;
	// (no sheen where her head's own shade is deep: in the crease where her
	// lips meet and the mouth behind, the rim light's reflection on her lips'
	// inner linings showed as white slivers along their line at a turn)
	float ea = mix(1.0, texture(ear_ao, UV).r, ear_amount);
	ALBEDO *= mix(ear_tint, vec3(1.0), ea);
	float ao = mix(aot.r, max(aot.r, lip_ao_open), max(lip_w, lips_apart * (1.0 - lips_narrow) * smoothstep(0.6, 0.95, fm.g))) * ea;
	SPECULAR = mix(seam_shine, shine, hw) * smoothstep(0.45, 0.95, ao);
	SPECULAR *= mix(1.0, lip_spec, lip_w * lip_tone);
	SPECULAR = mix(SPECULAR, paint_shine * smoothstep(0.45, 0.95, ao), pa);
	sheen = SPECULAR;
	AO = ao;
	AO_LIGHT_AFFECT = mix(ao_light, ear_light, smoothstep(0.0, 0.15, 1.0 - ea));
	back_ao = mix(1.0, ao, back_occ);
	SSS_STRENGTH = scatter * mix(1.0, paint_scatter, pa);
	BACKLIGHT = ALBEDO * backlight_colour * backlight * mix(1.0, aot.b, thin_map * rig_w);
	front_rim = seam_ease ? aot.g * (1.0 - rig_w) : 0.0;
	float wd = (INV_VIEW_MATRIX * vec4(NORMAL, 0.0)).y;
	shade_w = mix(1.0, smoothstep(down_from, down_to, -wd), shade_down) * mix(1.0, aot.a, shade_zone)
		* (1.0 - shade_thin * smoothstep(thin_from, thin_to, -wd));
	soft_w = 1.0 - fm.b;
	// (her head as r11, by its seam ease alone: its freckles' map's blue dips under her jaw, and gated by it there
	// the far side of her neck under her jaw went bluer, own's row .15 hue -21 to -31)
	edge_w = (seam_ease ? 1.0 - aot.g : mix(1.0, fk.b, edge_neck)) * (1.0 - smoothstep(edge_from, edge_to, dot(NORMAL, VIEW))) * rig_w;
	// (under the Look's rig only, where it was fitted: in play every lamp is a key, and it lit her chest 4-5 L* over
	// BEFORE's, own and Sunborn alike, by day and at night; judge rj2v fix 4, 13 October 2026)
	lift_w = (seam_ease ? 1.0 - aot.g : 1.0) * smoothstep(lift_from, lift_to, wd) * rig_w;
	// (the sky's light on her as before: ambient_tint takes her body's tone out of it already)
	ALBEDO *= mix(ambient_tint / body_back, vec3(1.0), pa);
	mouth_f = FRONT_FACING ? mouth_c : 1.0;
	if (mouth_f > 0.0) {
		float mc = smoothstep(0.0, 0.35, mouth_f), mo = smoothstep(0.1, 1.0, mouth_f);
		vec3 mcol = mix(mouth_colour, vec3(dot(mouth_colour, vec3(0.2126, 0.7152, 0.0722))) * wall_tint, wall_grey * mouth_w) * (1.0 - wall_dark * mouth_w);
		ALBEDO = mix(ALBEDO, mcol, mc);
		BACKLIGHT *= 1.0 - mc;
		SPECULAR *= 1.0 - mo;
		AO = min(AO, 1.0 - mouth_occ * mo);
		EMISSION += mcol * mouth_fill * mc * (1.0 - 0.6 * mo);
	}
	ALBEDO *= sky_share;   // (after the mouth's own colour: light() divides every lamp's light by it, the mouth's too)
	SPECULAR *= sky_share;   // (the sky's sheen on her too: her lamps' sheen is light()'s own, from `sheen`)
	vec3 alb_dbg = ALBEDO / max(sky_share, 1e-3);
	if (dbg_gate > 0.0) { ALBEDO = vec3(1.0); SPECULAR = 0.0; BACKLIGHT = vec3(0.0); }
	// (dbg_gate 3+: her maps instead, emitted: red ao_map's shade, green its seam ease, blue the face's paint (features' blue))
	if (dbg_gate > 2.5) { ALBEDO = vec3(0.0); EMISSION = (dbg_gate - 3.0) * vec3(aot.r, aot.g, fm.b); }
	// (dbg_gate 9: her UV, emitted, to find a picture's point on her mesh, with --tonemap linear --grade off)
	if (dbg_gate > 8.5) { EMISSION = vec3(UV, 0.0); }
	// (dbg_gate 10 and 11: her UV unclipped, blue the scale: 10 its whole, red/blue and green/blue; 11 its sixteenths)
	if (dbg_gate > 9.5 && dbg_gate < 11.5) { EMISSION = 0.25 * vec3(dbg_gate > 10.5 ? fract(UV * 16.0) : UV, 1.0); }
	// (dbg_gate 12: her albedo as toned, emitted; 13: her paint alone, emitted (with --tonemap linear --grade off; face 35))
	if (dbg_gate > 11.5) { ALBEDO = vec3(0.0); SPECULAR = 0.0; BACKLIGHT = vec3(0.0); EMISSION = dbg_gate > 12.5 ? texture(paint, UV).rgb : alb_dbg; }
}

// Each lamp's light on her, as Godot's own (Burley's diffuse, GGX's sheen,
// the rim, the light through her) but for where her lit side ends (see
// `terminator`).
float schlick(float u) {
	float m = clamp(1.0 - u, 0.0, 1.0);
	float m2 = m * m;
	return m2 * m2 * m;
}

void light() {
	float mouth_lit = (1.0 - mouth_occ * smoothstep(0.1, 1.0, mouth_f));
	float ndl = dot(NORMAL, LIGHT);
	float c_ndl = max(ndl, 0.0);
	if (dbg_gate > 0.0) {
		float kw = mix(1.0, smoothstep(shade_from, shade_to, SPECULAR_AMOUNT), shade_by_soft);
		float bh = step(0.25, dot(-LIGHT, VIEW));
		DIFFUSE_LIGHT += (dbg_gate > 1.5 ? (dbg_gate - 2.0) * vec3(c_ndl * kw * (1.0 - bh), ATTENUATION * kw * (1.0 - bh), 0.0)
			: dbg_gate * ATTENUATION * c_ndl * vec3(kw * (1.0 - bh), 1.0 - kw, kw * bh));
	} else {
	float c_ndv = max(dot(NORMAL, VIEW), 1e-4);
	vec3 h = normalize(VIEW + LIGHT);
	float c_ndh = clamp(dot(NORMAL, h), 0.0, 1.0);
	float c_ldh = clamp(dot(LIGHT, h), 0.0, 1.0);
	// (the edge eased over each channel's reach, C1 with the light either side:
	// (n + w)^2 / 4w from -w to w, n itself beyond)
	vec3 w = max(terminator, vec3(1e-4));
	vec3 n = vec3(ndl);
	vec3 t = clamp(n + w, vec3(0.0), 2.0 * w);
	vec3 soft = mix(t * t / (4.0 * w), n, step(w, n));
	float fd90 = 2.0 * c_ldh * c_ldh * ROUGHNESS - 0.5;
	float burley = (1.0 + fd90 * schlick(c_ndv)) * (1.0 + fd90 * schlick(c_ndl));
	vec3 diffuse = soft * burley / PI;
	vec3 un = 1.0 / (mix(max(ambient_tint, vec3(1e-3)) / body_back, vec3(1.0), paint_w) * max(sky_share, 1e-3));        // (the lamps' light on her as without the tint)
	vec3 rich = vec3(1.0);
	vec3 st = shade_tint / body_back;        // (where her body's tone is taken out, none to take out of her shade)
	if (shade_w > 0.0 && any(notEqual(st, vec3(1.0)))) {
		vec3 al = ALBEDO * un;
		vec3 lw = vec3(0.2126, 0.7152, 0.0722);
		vec3 tn = st * dot(al, lw) / max(dot(al * st, lw), 1e-4);
		float lit = mix(mix(ndl, dot(LIGHT_COLOR * vec3(ATTENUATION), lw) * c_ndl, shade_by_light), SPECULAR_AMOUNT, shade_by_soft);
		rich = mix(vec3(1.0), tn, shade_w * (1.0 - smoothstep(shade_from, shade_to, lit)));
	}
	float key_w = mix(1.0, smoothstep(shade_from, shade_to, SPECULAR_AMOUNT), shade_by_soft);
	// (lamps behind her take no lift: the Look's cool rim and the fire's edge lamp lifted the far side of her neck too,
	// judge j6)
	float behind = smoothstep(-0.1, 0.6, dot(-LIGHT, VIEW));
	mouth_lit *= 1.0 - corner_shade * fold * crease * behind;
	vec3 kt = vec3(1.0);
	// (from her collarbones down none: fitted on her neck with her body's tone, which is taken out there; body_tone)
	vec3 ktone = mix(vec3(1.0), LIGHT_IS_DIRECTIONAL && sky_tone.x > 0.0 ? sky_tone : key_tone, neck_w);
	if (any(notEqual(ktone, vec3(1.0)))) {
		vec3 ka = ALBEDO * un;
		vec3 klw = vec3(0.2126, 0.7152, 0.0722);
		kt = mix(vec3(1.0), ktone * dot(ka, klw) / max(dot(ka * ktone, klw), 1e-4), key_w * soft_w);
	}
	if (any(notEqual(edge_tone, vec3(1.0)))) {
		vec3 ea = ALBEDO * un * kt;
		vec3 elw = vec3(0.2126, 0.7152, 0.0722);
		kt *= mix(vec3(1.0), edge_tone * dot(ea, elw) / max(dot(ea * edge_tone, elw), 1e-4), key_w * soft_w * edge_w);
	}
	rich = mix(rich, vec3(1.0), paint_w);
	kt = mix(kt, vec3(1.0), paint_w);
	DIFFUSE_LIGHT += mouth_lit * LIGHT_COLOR * diffuse * ATTENUATION * un * rich * kt * mix(1.0, body_lift, key_w * lift_w * (1.0 - behind)) * mix(1.0, back_ao, behind)
		* mix(vec3(1.0), soft_tone, (1.0 - key_w) * soft_w * shade_by_soft * neck_w * (1.0 - paint_w));
	// the fine down at her edges, against a light from behind her only (lit
	// from the front, it brightened every edge of her: a pale ribbon down her
	// cheek where her dark hair met it, her temples white)
	float rim_light = pow(max(1e-4, 1.0 - c_ndv), max(0.0, (1.0 - ROUGHNESS) * 16.0));
	rim_light *= mix(1.0, smoothstep(0.0, 0.3, ndl), rim_gate);
	DIFFUSE_LIGHT += mouth_lit * rim_light * mix(behind, 1.0, front_rim) * rim * mix(vec3(1.0), ALBEDO * un, rim_tint) * LIGHT_COLOR * ATTENUATION * un;
	// light through her where she is thin
	DIFFUSE_LIGHT += mouth_lit * LIGHT_COLOR * max(vec3(1.0 / PI) - diffuse, vec3(0.0)) * BACKLIGHT * ATTENUATION * un * mix(1.0, behind, backlight_behind);
	if (c_ndl > 0.0) {
		float a = ROUGHNESS * ROUGHNESS;
		float da = c_ndh * a;
		float k = a / (1.0 - c_ndh * c_ndh + da * da);
		float d_ggx = k * k / PI;
		float v_ggx = 0.5 / mix(2.0 * c_ndl * c_ndv, c_ndl + c_ndv, a);
		// (a metal's sheen its own colour: the gilt's gold leaf; METALLIC 0 everywhere else)
		vec3 f0 = mix(vec3(0.16 * sheen * sheen), ALBEDO * un, METALLIC);
		vec3 f90 = clamp(f0 * 50.0, 0.0, 1.0);
		vec3 f = f0 + (f90 - f0) * schlick(c_ldh);
		vec3 spec = mouth_lit * c_ndl * d_ggx * f * v_ggx * LIGHT_COLOR * ATTENUATION * SPECULAR_AMOUNT * mix(1.0, back_spec, behind);
		// (each lamp's sheen held under spec_cap, its colour kept: a lamp held a hand from her cheek (c02 s8) blew it white)
		float sl = max(max(spec.r, spec.g), spec.b);
		// (gold leaf's glint let through: held under her skin's cap, the gilt read as dull olive, never gold)
		float cap = mix(spec_cap, metal_cap, METALLIC);
		SPECULAR_LIGHT += sl > cap ? spec * (cap / sl) : spec;
	}
	}
}
