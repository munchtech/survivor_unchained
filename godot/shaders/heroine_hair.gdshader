// Her hair (tools/assets/heroine_hair.py's cards): the strands' atlas, grey,
// dyed her colour, each strand and each lock a little lighter or darker than
// the next; darker at the root and deep in the hair (its vertex colour); cut
// to its strands by hashed alpha (smoothed over frames by the TAA). Lit as
// hair is, not as a surface: light along a strand, not across it (Kajiya-Kay),
// a white highlight off its outside and a second, her colour, from light gone
// through it, shifted apart along the strand; light wrapping round it and
// through it from behind (red hair glows against the light).
shader_type spatial;
render_mode cull_disabled, depth_draw_opaque;

uniform sampler2D strands : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform vec3 colour : source_color = vec3(0.56, 0.17, 0.07);
uniform float roots = 0.4;
uniform float variation = 0.35;
uniform vec3 shine_colour : source_color = vec3(1.0, 0.93, 0.86);
uniform float shine = 0.1;
uniform float shine_width = 140.0;
uniform float shine2 = 0.35;
uniform float shine2_width = 40.0;
uniform float shift = 0.06;
uniform float shift2 = -0.1;
uniform float through = 0.5;
// Her scalp under the hair (its cap): fine strands lying the way her hair is
// combed, dark (under the hair), thinning out at her hairline (its vertex
// alpha) to bare skin. A braid's strands are drawn so too.
uniform bool cap = false;

varying vec3 strand;
varying float sparkle;
varying float fibre;

void fragment() {
	vec4 t = texture(strands, UV);
	// (its shade kept from going too dark or too light, strand to strand)
	t.r = mix(0.15, 0.85, t.r);
	// Strand by strand (the atlas's green) and lock by lock (the card's green),
	// from a deeper auburn to a lighter copper.
	vec3 dark = colour * vec3(0.62, 0.5, 0.45);
	vec3 light = min(colour * vec3(1.4, 1.5, 1.55), vec3(1.0));
	vec3 tint = mix(colour, mix(dark, light, clamp(t.g * 0.88 + COLOR.g * 0.12, 0.0, 1.0)), variation);
	float depth = COLOR.r;                                        // 1 outermost, darker within
	strand = normalize(BINORMAL);                                 // along its V: root to tip
	sparkle = t.g;
	fibre = t.r * (cap ? 0.35 : 1.0);                            // (the cap's under the hair: little highlight)
	if (cap) {
		// (at her hairline, where its strands are seen, as bright as hair; dark under the cards)
		float fade = COLOR.a;
		// (a rope of hair, a braid's strand (its blue), as bright as hair, deep in it darker)
		float rope = COLOR.b;
		ALBEDO = tint * t.r * mix(0.85, 0.5, smoothstep(0.4, 1.0, fade) * (1.0 - rope)) * mix(1.0, mix(0.55, 1.0, depth), rope);
		ALPHA = max(fade * fade, t.a * smoothstep(0.0, 0.7, fade));
	} else {
		float along = UV.y;                                       // 0 at the root, 1 at the tip
		ALBEDO = tint * t.r * mix(1.0 - roots, 1.0, smoothstep(0.0, 0.1, along)) * mix(0.55, 1.0, depth);
		ALPHA = t.a * smoothstep(0.0, 0.012, along);             // (its root's blunt end softened)
	}
	ALPHA_HASH_SCALE = 1.0;
	ROUGHNESS = 0.7;
	SPECULAR = 0.15;
	AO = mix(0.5, 1.0, depth);
}

float along_strand(vec3 t, vec3 h, float width) {
	float th = dot(t, h);
	return smoothstep(-1.0, 0.0, th) * pow(sqrt(max(1.0 - th * th, 0.0)), width);
}

void light() {
	vec3 lc = LIGHT_COLOR * ATTENUATION / PI;
	float nl = dot(NORMAL, LIGHT);
	DIFFUSE_LIGHT += lc * clamp((nl + 0.45) / 1.45, 0.0, 1.0);
	DIFFUSE_LIGHT += lc * through * pow(clamp(dot(-LIGHT, VIEW), 0.0, 1.0), 3.0);
	vec3 h = normalize(LIGHT + VIEW);
	// (each strand's highlight a little up or down it from the next's: the
	// highlight broken into strands, not one smooth band)
	float jitter = (sparkle - 0.5) * 0.5;
	float s1 = along_strand(normalize(strand + NORMAL * (shift + jitter)), h, shine_width);
	float s2 = along_strand(normalize(strand + NORMAL * (shift2 + jitter)), h, shine2_width);
	float seen = clamp(nl * 0.6 + 0.4, 0.0, 1.0);
	SPECULAR_LIGHT += lc * seen * fibre * fibre * (shine_colour * shine * s1 + ALBEDO * shine2 * s2 * (0.4 + 1.2 * sparkle));
}
