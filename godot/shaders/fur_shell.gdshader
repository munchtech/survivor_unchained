// Fur by shells: the piece drawn again and again, each pass a little further
// out along its normals, keeping only the strands that reach that far, so
// the surface grows a pile of hairs that thin toward their tips and catch
// the light at their edges. Each pass is one of a chain of next_pass
// materials (People.Fur), `layer` from 0 at the skin to 1 at the tips.
shader_type spatial;
render_mode cull_back, depth_draw_opaque;

uniform sampler2D albedo_tex : source_color, filter_linear_mipmap, repeat_enable;
uniform vec4 tint : source_color = vec4(1.0);
uniform bool test_flat = false;   // (the legal motion check: flat grey, coverage unchanged)
uniform float layer = 0.0;
uniform float fur_length = 0.008;
uniform float density = 260.0;
uniform float clump = 0.35;
uniform vec3 gravity = vec3(0.0, -1.0, 0.0);
uniform float root_dark = 0.45;   // (how dark the roots are, shadowed by the pile)
uniform float backlight = 0.25;   // (light through the strands)
uniform float droop = 0.35;       // (how far the tips bend down)
// A pelt (armor 16, the reaver's fur: "plush felt, not a pelt"): the strands grow in pointed
// tufts that part as they rise (the edge broken, not a felt dome), a dense short underfur
// under sparse long guard hairs, combed down along the surface, dark at the root and
// lighter, a little frosted, at the tip. 0 = the plain pile above, bit for bit (the down).
uniform float pelt = 0.0;
uniform float tuft = 0.11;        // (tufts per strand cell: one tuft about 9 strands across)
uniform float guard = 0.22;       // (share of strands that are long guard hairs)
uniform float under_len = 0.5;    // (the underfur's height, of the guard hairs')
uniform float tip_light = 1.35;   // (the tips' value, of the texture's)
uniform float frost = 0.12;       // (the guard hairs' pale tips)
uniform float comb = 0.9;         // (how far the strands lean down along the surface, of their length)
// (armor 16 N4, OJ1: "color and length are uniform": by the piece's edge distance (UV2.x, metres, 0.05 = far), its
// middle (the pelt's spine) darker, its fringe longer and lighter, its hem's length uneven so the outline is ragged)
uniform float body_len = 1.0;     // (the pile's height away from the fringe, of fur_length; 1 = even)
uniform float fringe_w = 0.02;    // (how far in from the edge the fringe reaches, metres)
uniform float fringe_light = 1.0; // (the fringe's value, of the pile's)
uniform float spine_dark = 1.0;   // (the middle's value, of the pile's)
uniform float hem_vary = 0.0;     // (how unevenly long the fringe's hairs are: locks of their own length)
uniform float hem_scale = 9.0;    // (locks per UV unit)
varying float v_edge;

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

void vertex() {
	v_edge = UV2.x;
	// Strands bend down a little toward their tips.
	vec3 g = (inverse(MODEL_MATRIX) * vec4(gravity, 0.0)).xyz;
	VERTEX += NORMAL * fur_length * layer + g * fur_length * droop * layer * layer;
	if (pelt > 0.0) {
		// combed: laid along the surface toward the ground, more toward the tips
		vec3 gt = g - NORMAL * dot(g, NORMAL);
		VERTEX += gt * fur_length * comb * pow(layer, 1.3);
	}
}

vec2 hash2(vec2 p) {
	return fract(sin(vec2(dot(p, vec2(127.1, 311.7)), dot(p, vec2(269.5, 183.3)))) * 43758.5453);
}

void fragment() {
	vec2 cell = UV * density;
	vec2 id = floor(cell);
	vec2 f = fract(cell) - 0.5;
	float h = hash(id);
	if (pelt > 0.0) {
		// The tuft: nearest of jittered centres (strand cells / tuft across), its own height and shade.
		vec2 tc = UV * density * tuft;
		vec2 ti = floor(tc);
		float best = 9.0;
		vec2 bid = ti;
		for (int y = -1; y <= 1; y++) for (int x = -1; x <= 1; x++) {
			vec2 o = vec2(float(x), float(y));
			vec2 d = o + hash2(ti + o) * 0.9 + 0.05 - fract(tc);
			float dd = dot(d, d);
			if (dd < best) { best = dd; bid = ti + o; }
		}
		float td = sqrt(best);                                   // (0 at its centre, ~0.5-0.7 at its edge)
		float tt = mix(0.7, 1.0, hash(bid + 3.7));               // (the tuft's height)
		bool is_guard = hash(id + 11.3) < guard;
		float tall = is_guard ? mix(0.8, 1.0, h) * mix(0.85, 1.0, tt) : mix(0.7, 1.0, h) * under_len * tt;
		// (the fringe: full length at the edge, in locks of uneven length; the rest of the pile body_len)
		float fringe = 1.0 - smoothstep(0.0, fringe_w, v_edge);
		vec2 lc = UV * hem_scale;
		vec2 li = floor(lc), lf = fract(lc); lf = lf * lf * (3.0 - 2.0 * lf);
		float lock = mix(mix(hash(li), hash(li + vec2(1.0, 0.0)), lf.x), mix(hash(li + vec2(0.0, 1.0)), hash(li + vec2(1.0, 1.0)), lf.x), lf.y);
		tall *= mix(body_len, 1.0 - hem_vary * (1.0 - lock), fringe);
		float radius = 0.5 * (1.0 - layer / max(tall, 0.001));
		// the tuft parts as it rises: past half its height only its core holds strands
		float core = 0.8 * (1.0 - smoothstep(0.1 * tt, 0.85 * tt, layer)) + 0.1;
		if (layer > 0.0 && (layer > tall || length(f) > radius || (!is_guard && td > core) || (is_guard && td > core + 0.3))) discard;
		vec3 c = texture(albedo_tex, UV).rgb * tint.rgb;
		float shade = mix(0.7, 1.15, hash(bid + 9.1));
		shade *= mix(1.0, spine_dark, smoothstep(0.02, 0.045, v_edge)) * mix(1.0, fringe_light, fringe * smoothstep(0.2, 0.8, layer));
		float up = pow(layer, 0.75);
		vec3 a = c * shade * mix(root_dark, tip_light, up);
		if (is_guard) a = mix(a, vec3(dot(c, vec3(0.3, 0.5, 0.2))) * 1.9, frost * smoothstep(0.6, 1.0, layer / tall));
		// (the tuft's outer strands in its own shadow, its core catching the light)
		a *= mix(1.0, 0.72, smoothstep(0.0, 0.7, td) * (1.0 - layer));
		ALBEDO = layer > 0.0 ? a : c * root_dark * 0.55;
		ROUGHNESS = is_guard ? 0.62 : 0.85;
		SPECULAR = 0.3;
		BACKLIGHT = c * backlight;
		if (test_flat) {
			ALBEDO = vec3(0.0);
			METALLIC = 0.0;
			ROUGHNESS = 1.0;
			SPECULAR = 0.0;
			EMISSION = vec3(0.5);
			BACKLIGHT = vec3(0.0);
		}
	} else {
	// Each strand a cone: wide at the root, a point at its own height.
	float tall = mix(0.55, 1.0, h) * mix(1.0, hash(floor(UV * density * 0.12)), clump);
	float radius = 0.5 * (1.0 - layer / max(tall, 0.001));
	if (layer > 0.0 && (layer > tall || length(f) > radius)) discard;
	vec3 c = texture(albedo_tex, UV).rgb * tint.rgb;
	// Darker at the roots (shadowed by the pile), lighter at the tips.
	ALBEDO = c * mix(root_dark, 1.15, layer);
	ROUGHNESS = 0.9;
	SPECULAR = 0.25;
	BACKLIGHT = c * backlight;
	if (test_flat) {
		ALBEDO = vec3(0.0);
		METALLIC = 0.0;
		ROUGHNESS = 1.0;
		SPECULAR = 0.0;
		EMISSION = vec3(0.5);
		BACKLIGHT = vec3(0.0);
	}
	}
}
