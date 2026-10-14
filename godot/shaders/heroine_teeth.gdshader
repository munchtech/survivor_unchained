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
// (her mouth open, its inside (the side teeth, her palate and gums, out of the lamps) gives off a little of the
// mouth's own dark red, so it reads as a shaded mouth and not a black hole (the smile pass, f1-f4, with the skin's mouth_fill); 0 none)
uniform vec3 inside : source_color = vec3(0.42, 0.15, 0.14);
uniform float fill = 0.2;
uniform float debug = 0.0;       // (1: her teeth green, emitted, for finding them in a picture; 2: hidden)

void fragment() {
	if (debug > 1.5) discard;
	// (k: the share of her front teeth's brightness on screen this tooth keeps, by how far it stands behind them
	// (heroine_teethshade.py: 1 to about 0.35), and as light, k^2.2. Her lips parted, the light is cut evenly (sky and
	// lamps alike, the paint kept ivory): her side teeth read as shaded ivory. Until the smile pass's j2 the shade cut
	// the lamps by 1 - k^3 and the sky to k^2, with the paint browned toward shade: her canines and every tooth behind
	// them read black, and her far side's lower back teeth a black column through her open mouth)
	float k = COLOR.r * mix(closed, 1.0, lit);
	float f = pow(k, 2.2);
	// (her lips shut, 1, to parted, 0: shut runs from 1 to 0.6 by mouth_open 0.05)
	float c = clamp((shut - 0.6) / 0.4, 0.0, 1.0);
	ALBEDO = mix(texture(paint, UV).rgb * ivory, shade, c);
	SPECULAR = 0.5 * f * (1.0 - c);
	ROUGHNESS = mix(mix(0.6, roughness, k), 1.0, c);
	AO = mix(f, seep, c);
	AO_LIGHT_AFFECT = 1.0;
	NORMAL = normalize(mix(NORMAL, VIEW, c));
	// (on her gums and palate alone, by their paint's red: lit so, her side teeth read as brown blocks (g1))
	vec3 p = texture(paint, UV).rgb;
	EMISSION = inside * fill * (1.0 - k) * (1.0 - c) * smoothstep(0.08, 0.25, p.r - p.b);
	if (debug > 0.5) { ALBEDO = vec3(0.0); SPECULAR = 0.0; AO = 0.0; AO_LIGHT_AFFECT = 1.0; EMISSION = vec3(0.0, 2.0, 0.0); }
}
