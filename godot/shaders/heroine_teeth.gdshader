// Her teeth (People.HerPart): their paint, in the mouth's own shade.
// Her side teeth stand in the cheeks' shade (the buccal corridor): the mesh's grey vertex colour
// (tools/assets/heroine_teethshade.py, 1 over the front teeth, down to 0.2 at the sides; white where a
// mesh has none) is how much light her mouth lets in to them; with her lips closed, the whole row's is low
// (lit, set each frame by HerFaceLife.TeethLight from how far her lips part).
// In the shade they go from ivory to a warm dark, and the light is cut there, not their colour greyed: the
// sky's light (the ambient: AO) as the square of it, and the lamps (AO_LIGHT_AFFECT) as far as her mouth is
// shut, as the lamps without a shadow reached them through her lips. Her paint is a neutral grey-white;
// darkened toward the old pink-red (the inner cheek) it read lavender-grey beside her lips (judge rj2v), and at
// her mouth's corner, lit through her shut lips, a pale bead (Sunborn at a turn: the teeth-green test lit it).
// With her lips shut, what a corner of them shows (side teeth or gum) is the inside of her mouth: one warm dark
// (shade, not times the paint), lit by a share (seep) of all the light on her, flat (her normal turned to the
// eye: no tooth's shape, no sheen, so no bead). Cut to nothing, the side teeth and red gum there read as a pure
// black wedge at Sunborn's corner (judge rj3). It eases out as her lips part (shut 1 to 0.6, by mouth_open 0.05),
// so the teeth from there on are as before.
shader_type spatial;
render_mode cull_disabled;

uniform sampler2D paint : source_color, filter_linear_mipmap, hint_default_white;
uniform float lit : hint_range(0.0, 1.0) = 1.0;
uniform vec3 ivory : source_color = vec3(1.0, 0.97, 0.92);   // (her paint's enamel warmed to ivory, sRGB)
uniform vec3 shade : source_color = vec3(0.45, 0.33, 0.22);  // (where no light comes in: a warm dark, sRGB)
uniform float closed = 0.2;      // (her lips closed: how much of the front teeth's light is left)
uniform float shut = 1.0;        // (how far the lamps are cut in the shade: 1 lips shut, 0.6 parted; HerFaceLife.TeethLight)
uniform float seep = 0.12;       // (her lips shut: the share of the light on her that reaches her mouth's inside)
uniform float roughness = 0.35;
uniform float debug = 0.0;       // (1: her teeth green, emitted, for finding them in a picture; 2: hidden)

void fragment() {
	if (debug > 1.5) discard;
	float k = COLOR.r * mix(closed, 1.0, lit);
	// (her lips shut, 1, to parted, 0: shut runs from 1 to 0.6 by mouth_open 0.05)
	float c = clamp((shut - 0.6) / 0.4, 0.0, 1.0);
	ALBEDO = mix(texture(paint, UV).rgb * mix(shade, ivory, k), shade, c);
	SPECULAR = 0.5 * k * k * (1.0 - c);
	ROUGHNESS = mix(mix(0.75, roughness, k), 1.0, c);
	AO = mix(k * k, seep, c);
	AO_LIGHT_AFFECT = mix(shut * (1.0 - k), 1.0, c);
	NORMAL = normalize(mix(NORMAL, VIEW, c));
	if (debug > 0.5) { ALBEDO = vec3(0.0); SPECULAR = 0.0; AO = 0.0; AO_LIGHT_AFFECT = 1.0; EMISSION = vec3(0.0, 2.0, 0.0); }
}
