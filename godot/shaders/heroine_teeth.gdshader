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
// (her lower row behind its canines, deep in her mouth (heroine_teethshade.py: the green channel, its light as a share
// of the canine's, 1 elsewhere): its paint warmed to deep_tint (linear) and its sheen cut to deep_spec there. From the
// Look her far lower molars read blue-grey, blue at or over red (the sky on their enamel), solver int3)
uniform vec3 deep_tint = vec3(1.0, 1.07, 0.96);
// (judge a05fb157: at deep_tint, green over red, they read a cool green stone grey on all ten (worst Hard-won, Fey):
// deep_warm 1 takes deep_tint_warm instead, warmer and darker, so they recede into the mouth's warm shade.
// Judge a00723b7: still olive-khaki in the laugh (Fey, Hard-won most), her near side teeth blue-grey. Not the sky:
// at the Look its light off (--look-ambient 0), the reflections off, SSAO off or the fill and edge lamps off left
// those teeth's colour as it was (solver interior, ia). Ivory darkened is olive beside her mouth's red, and her side
// teeth, lit more by the white fill than the warm key, lose their ivory's yellow (hue 54 to 32, b* 14 to 4). So with
// deep_warm, her far lower row goes on to deep_dark (a dim red-brown, the light that reaches it off her cheeks and
// tongue), and every tooth by its shade (1 - its light, k^2.2, times the lower row's own share) toward shade_warm, so
// her side teeth keep the ivory's warmth as they darken)
uniform vec3 deep_tint_warm = vec3(0.8, 0.6, 0.45);
uniform vec3 deep_dark = vec3(0.5, 0.32, 0.29);
uniform vec3 shade_warm = vec3(1.0, 0.82, 0.55);
uniform float deep_warm = 1.0;
uniform float deep_spec = 0.15;
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
	float dw = 1.0 - clamp(COLOR.g, 0.0, 1.0);
	vec3 dt = mix(vec3(1.0), mix(deep_tint, deep_tint_warm, deep_warm), dw);
	dt = mix(dt, deep_dark, dw * deep_warm);
	dt *= mix(vec3(1.0), shade_warm, deep_warm * clamp(1.0 - f * clamp(COLOR.g, 0.0, 1.0), 0.0, 1.0));
	ALBEDO = mix(texture(paint, UV).rgb * ivory * dt, shade, c);
	SPECULAR = 0.5 * f * (1.0 - c) * mix(1.0, deep_spec, min(1.0, 2.0 * dw));
	ROUGHNESS = mix(mix(0.6, roughness, k), 1.0, c);
	AO = mix(f, seep, c);
	AO_LIGHT_AFFECT = 1.0;
	NORMAL = normalize(mix(NORMAL, VIEW, c));
	// (on her gums and palate alone, by their paint's red: lit so, her side teeth read as brown blocks (g1))
	vec3 p = texture(paint, UV).rgb;
	EMISSION = inside * fill * (1.0 - k) * (1.0 - c) * smoothstep(0.08, 0.25, p.r - p.b);
	if (debug > 0.5) { ALBEDO = vec3(0.0); SPECULAR = 0.0; AO = 0.0; AO_LIGHT_AFFECT = 1.0; EMISSION = vec3(0.0, 2.0, 0.0); }
}
