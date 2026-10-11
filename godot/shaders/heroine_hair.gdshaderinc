// Her hair's shading, for heroine_hair.gdshader (cut to its strands by hashed
// alpha), heroine_hair_coverage.gdshader (cut by a threshold moved every frame:
// COVERAGE), heroine_hair_soft.gdshader (blended: SOFT), and the two blended
// ways tried under FSR 2 (src/Actors/HairDraw.cs): heroine_hair_blend.gdshader
// (blended over a depth prepass of its solid parts: BLEND), and
// heroine_hair_core.gdshader (its solid parts drawn opaque: CORE) under
// heroine_hair_over.gdshader (the whole drawn again over them, blended: OVER);
// and heroine_hair_erase.gdshader drawn last over any of the blended ones, to
// erase FSR 2's reactive mask under them (ERASE).

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
// A leather tie in her hair: dark, no strands.
uniform bool tie = false;
// Her hair's swing (src/Actors/HairSway.cs): how far a mass hung below her
// head has been left behind, and where her head is (both in the mesh's own
// space). Each point is moved by it the more the further it hangs below her
// head and the nearer its tip; and a breath of air through it, always.
uniform vec3 sway = vec3(0.0);
uniform vec3 head = vec3(0.0, 1.6, 0.0);
// A style that hangs on a chain (its second UV: the place along it and how
// much it moves with it): how far each of the chain's points has swung
// from where it hangs at rest, in the mesh's own space.
uniform vec3 chain[8];
// The three as they were last frame, for the motion vectors (motion.gdshaderinc):
// so the temporal smoothing follows the swing, not only her head.
uniform vec3 sway_then = vec3(0.0);
uniform vec3 head_then = vec3(0.0, 1.6, 0.0);
uniform vec3 chain_then[8];
// Her forearms (elbow, past the fist; left then right, in the mesh's own space) and their radius: her hair is
// pushed out of them (a lock by her ear as her throwing arm comes past her head). 0: none.
uniform vec3 arms[4];
uniform vec3 arms_then[4];
uniform float arm_r = 0.0;

#include "res://shaders/motion.gdshaderinc"
#ifdef COVERAGE
#include "res://shaders/coverage.gdshaderinc"
#endif
#ifdef CORE
// (the share of a pixel a strand must cover to be drawn solid, its depth and
// motion written: near 1, so the blended pass over it shows no edge)
uniform float core_cut = 0.9;
#ifdef CORE_A2C
// (under MSAA, at the Look: its own cut, near 1, so the core's samples and the blended
// pass over them don't both cover the edge, which drew it darker and wider)
uniform float a2c_cut = 0.9;
#endif
#endif
#ifdef ERASE
// (how much of the blended alpha under it is kept: heroine_hair_erase.gdshader;
// erased fully only where the strands cover at least erase_from: with "two", the core's
// cut, so only what wrote her hair's own motion is accumulated, and the thin
// fringe stays reactive)
uniform float keep = 0.0;
uniform float erase_from = 0.0;
#endif
// (a bias on the strands' mip level: 0.5 cancels the smoothing's -0.5 on strands
// thinner than a pixel; --hair-bias, HairDraw)
uniform float strand_bias = 0.0;

varying vec3 strand;
varying float sparkle;
varying float fibre;

void vertex() {
	bool past = last_frame(TIME);
	float hang = clamp(((past ? head_then.y : head.y) - VERTEX.y) / 0.35, 0.0, 1.0);
	float tip = (cap || tie) ? 1.0 : smoothstep(0.0, 1.0, UV.y);
	float moves = (cap && COLOR.b < 0.5) ? 0.0 : 1.0;           // (not the cap on her scalp; a braid's strands, yes)
	vec3 air = vec3(sin(TIME * 1.1 + VERTEX.y * 5.0), 0.0, cos(TIME * 0.9 + VERTEX.x * 7.0)) * 0.0025;
	if (UV2.y > 0.0) {
		float s = clamp(UV2.x, 0.0, 1.0) * 7.0;
		int i = min(int(floor(s)), 6);
		vec3 a = past ? chain_then[i] : chain[i];
		vec3 b = past ? chain_then[i + 1] : chain[i + 1];
		VERTEX += (mix(a, b, s - float(i)) + air * UV2.x) * UV2.y;
	} else {
		VERTEX += ((past ? sway_then : sway) + air) * hang * hang * tip * moves;
	}
	if (arm_r > 0.0 && moves > 0.0) {
		for (int k = 0; k < 2; k++) {
			vec3 a = past ? arms_then[2 * k] : arms[2 * k];
			vec3 ab = (past ? arms_then[2 * k + 1] : arms[2 * k + 1]) - a;
			vec3 c = a + ab * clamp(dot(VERTEX - a, ab) / max(dot(ab, ab), 1e-6), 0.0, 1.0);
			vec3 o = VERTEX - c;
			float d = length(o);
			if (d < arm_r && d > 1e-5) VERTEX = c + o * (arm_r / d);
		}
	}
}

void fragment() {
	vec4 t = texture(strands, UV, strand_bias);
	// (its shade kept from going too dark or too light, strand to strand)
	t.r = mix(0.15, 0.85, t.r);
	// Strand by strand (the atlas's green) and lock by lock (the card's green),
	// from a deeper auburn to a lighter copper.
	vec3 dark = colour * vec3(0.62, 0.5, 0.45);
	vec3 light = min(colour * vec3(1.4, 1.5, 1.55), vec3(1.0));
	// (the card's own share small: at 0.12 each card took a flat tone of its own, a block on her crown)
	vec3 tint = mix(colour, mix(dark, light, clamp(t.g * 0.96 + COLOR.g * 0.04, 0.0, 1.0)), variation);
	float depth = COLOR.r;                                        // 1 outermost, darker within
	strand = normalize(BINORMAL);                                 // along its V: root to tip
	sparkle = t.g;
	fibre = t.r * (cap ? 0.35 : 1.0);                            // (the cap's under the hair: little highlight)
	float cover = 1.0;
	if (tie) {
		ALBEDO = vec3(0.055, 0.035, 0.024);
		fibre = 0.6;
	} else if (cap) {
		// (at her hairline, where its strands are seen, as bright as hair; dark under the cards)
		float fade = COLOR.a;
		// (a rope of hair, a braid's strand (its blue), as bright as hair, deep in it darker)
		float rope = COLOR.b;
		// (at her hairline as light as her hair, not a darker band over it;
		// and its strands ending each at its own height, by its number (the
		// atlas's green), a ragged line, not a smooth fade along an arc)
		// (darker only well under the cards (fade 0.85 to 1): from 0.4 it drew a dark band just over her
		// hairline, where the cards do not yet cover; and thinned strand by strand over most of its fade, its
		// cover about 0.3 to 0.9 over 7 to 10 mm, not all in its first 3)
		ALBEDO = tint * t.r * mix(1.0, 0.5, smoothstep(0.85, 1.0, fade) * (1.0 - rope)) * mix(1.0, mix(0.55, 1.0, depth), rope);
		cover = max(fade * fade, t.a * smoothstep(0.0, 0.8, fade + (t.g - 0.5) * 0.35));
	} else {
		float along = UV.y;                                       // 0 at the root, 1 at the tip
		// (layer by layer only a little darker within, and a root dark only
		// where it lies deep: an outer card's root, begun mid-crown, drew a dark
		// band, and an outer card at 1.8 times an inner one's light a block)
		ALBEDO = tint * t.r * mix(1.0 - roots * (1.0 - depth), 1.0, smoothstep(0.0, 0.1, along)) * mix(0.75, 1.0, depth);
		// (the baby hairs at her hairline (their blue): a lighter copper, sunlit fine hair, not grey strokes)
		ALBEDO = mix(ALBEDO, light * mix(0.8, 1.0, t.r), COLOR.b * 0.7);
		// (its root's blunt end softened; the baby hairs at her hairline faint: its vertex alpha)
		cover = t.a * smoothstep(0.0, 0.012, along) * COLOR.a;
	}
#if defined(SOFT) || defined(OVER)
	ALPHA = cover;
#elif defined(BLEND)
	// (its shadow cut at half cover: as much shadow as hashed alpha cast on
	// average, and still; Godot's prepass would cast all over a tenth)
	ALPHA = IN_SHADOW_PASS ? step(0.5, cover) : cover;
#elif defined(CORE)
	ALPHA = cover;
#ifdef CORE_A2C
	// (under MSAA, the cut's edge spread over the samples over a pixel round
	// a2c_cut: alpha to coverage, heroine_hair_core_a2c.gdshader; cut first a
	// quarter below it, as Godot cuts before it spreads. The texture coordinate
	// is the plain UV, whose tiny derivatives turn off Godot's boost of the
	// alpha by a quarter per mip level, which widened the cut)
	float cut0 = max(a2c_cut - 0.25, 0.05);
	ALPHA_SCISSOR_THRESHOLD = IN_SHADOW_PASS ? 0.5 : cut0;
	ALPHA_ANTIALIASING_EDGE = IN_SHADOW_PASS ? 0.0 : a2c_cut - cut0;
	ALPHA_TEXTURE_COORDINATE = UV;
#else
	ALPHA_SCISSOR_THRESHOLD = IN_SHADOW_PASS ? 0.5 : core_cut;
#endif
#elif defined(ERASE)
	// (white, multiplied: the colour kept; the alpha, FSR 2's reactive mask, scaled by keep
	// where the strands cover erase_from or more, eased out over the 0.25 below it)
	ALBEDO = vec3(1.0);
	ALPHA = erase_from > 0.0 ? mix(1.0, keep, smoothstep(erase_from - 0.25, erase_from, cover)) : keep;
#elif defined(COVERAGE)
	// (cut by a threshold moved every frame: coverage.gdshaderinc)
	if (cover < coverage_cut(FRAGCOORD.xy)) discard;
#else
	ALPHA = cover;
	ALPHA_HASH_SCALE = 1.0;
#endif
	ROUGHNESS = 0.7;
	SPECULAR = 0.15;
	AO = mix(0.75, 1.0, depth);
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
