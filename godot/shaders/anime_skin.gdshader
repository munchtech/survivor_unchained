// Her skin (Actors/People.cs, a woman in her own body): donizaki's painted
// texture, toned to the skin chosen. What is her skin's paint, lighter or
// darker (the shading in her creases too), takes the choice, as light or
// dark as the paint was; the eyes, lashes, lips and teeth keep their paint,
// the brows take the hair's colour. A rim of light at the edge, as on everyone.
shader_type spatial;

uniform sampler2D tex : source_color, filter_linear_mipmap_anisotropic;
// The skin chosen (the fair tone by default: People.Fair).
uniform vec3 skin : source_color = vec3(0.949, 0.769, 0.659);
// The body's sheet is all skin: its painted strokes of shine become a
// lighter skin, not white.
uniform bool whole = false;
// Her painted brows (two strokes along the top of the face's sheet) take the
// hair's colour, when it has one.
uniform bool dye_brows = false;
uniform vec3 brow : source_color = vec3(0.3, 0.2, 0.12);
uniform float rim_amount = 0.45;
uniform float rim_tint = 0.35;

void fragment() {
	vec3 t = texture(tex, UV).rgb;
	// Her paint's skin colour, linear; a texel as a multiple of it.
	vec3 base = pow(vec3(232.0, 216.0, 192.0) / 255.0, vec3(2.2));
	vec3 r = t / base;
	float spread = max(r.r, max(r.g, r.b)) - min(r.r, min(r.g, r.b));
	float level = (r.r + r.g + r.b) / 3.0;
	// Skin is her skin's colour made lighter or darker (evenly, or a little
	// warmer in the shade); lips, eyes and brows are other colours or darker.
	float is_skin = (1.0 - smoothstep(0.16, 0.26, spread)) * smoothstep(0.3, 0.45, level);
	vec3 toned = skin * mix(vec3(level), r, is_skin);
	ALBEDO = whole ? toned : mix(t, toned, is_skin);
	if (dye_brows && !whole) {
		float is_brow = (1.0 - is_skin) * step(UV.y, 0.125) * step(0.21, UV.x) * step(UV.x, 0.93);
		ALBEDO = mix(ALBEDO, brow * clamp(level * 1.4, 0.35, 1.0), is_brow);
	}
	ROUGHNESS = 0.62;
	SPECULAR = 0.35;
	RIM = rim_amount;
	RIM_TINT = rim_tint;
}
