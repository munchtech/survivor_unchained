// Her eyes (tools/assets/heroine_eyes.py's paint on MakeHuman's eyeballs).
// The iris lies behind the clear dome of the cornea: seen from the side it
// shifts against the white (parallax, as through the lens), the dome bulges
// over it (so the light's highlight sits on it, sharp and wet), and its edge
// is ringed dark. The whites are not white but a warm, soft ivory, shadowed
// under the upper lid and toward the corners, where the lids close over them.
// The clear cornea's own patch of the paint is empty: cut away.
shader_type spatial;
render_mode depth_draw_opaque;

uniform sampler2D eye : source_color, filter_linear_mipmap_anisotropic;
// The iris alone (its edge at 0.412 of the square, from its middle).
uniform sampler2D iris : source_color, filter_linear_mipmap_anisotropic, repeat_disable;
// Each eye's iris in the paint (its middle) and how big (one for both).
uniform vec2 iris_a = vec2(0.7064, 0.2959);
uniform vec2 iris_b = vec2(0.2933, 0.7015);
uniform float iris_r = 0.12;
// How far behind the cornea the iris lies (in irises' radii), how high the
// cornea's dome stands, and its pupil's size (0 to 1, 0.28 as painted).
uniform float depth = 0.12;
uniform float dome = 0.55;
uniform float pupil = 0.28;
// The limbal ring: how dark the iris's edge goes, and from where (in its radii).
uniform float limbal = 0.62;
uniform float limbal_from = 0.7;
// Her iris's colour, over its paint's (white keeps it as painted).
uniform vec3 tint : source_color = vec3(1.0);
// Her eyes' colour chosen (People.EyeColour): the paint's fibres and crypts,
// its light and dark, kept, and its colour taken from the iris's (outside)
// and the ring's (round the pupil, as real eyes have: a blue eye's amber
// collarette), softly from one to the other at `ring` (in the paint's own
// radii, where its amber gives way to green). 0 keeps the paint's colour.
uniform float recolour = 0.0;
uniform vec3 iris_colour : source_color = vec3(0.30, 0.42, 0.22);
uniform vec3 ring_colour : source_color = vec3(0.62, 0.42, 0.16);
uniform float ring = 0.56;
// The paint's mean light (linear), so a colour chosen comes out as itself.
const float PAINT_LIGHT = 0.12;
// The iris's light over all (painted or dyed): a colour chosen is the iris's
// own albedo (Lore's eye swatches, fitted under a white light so each face's
// irises stand to its cheek as its portrait's do). (It was 0.3 while the
// sky's reflection on the cornea lit every iris; with that dimmed, at 0.3
// every iris rendered a third to a fiftieth as light as its portrait's, the
// brown ones black.)
uniform float iris_light = 1.0;
// The cornea's wet sheen: its roughness and its reflectance, for the lights
// on her (light(), below); `sky_wet` the reflectance of the sky round her.
// (Her sky's radiance is bright where its glow is, and on a cornea that
// sharp, even at a tenth of `wet`, its reflection was a white blob as big as
// her pupil low on each iris with every light on her put out: the eye's
// tell of a render. The lights' own highlights are the small crisp windows.)
uniform float wet_rough = 0.035;
uniform float wet = 0.42;
uniform float sky_wet = 0.04;
// Where she is looking, each eye's iris slid over its ball (in irises'
// radii: +x to her left, +y down; both eyes' paint the same way round).
uniform vec2 gaze_a = vec2(0.0);
uniform vec2 gaze_b = vec2(0.0);
uniform float lids = 0.7;
// A catchlight: the small soft window every lit eye carries on its cornea
// (what makes a face look alive on screen; larger, it read as a white blob
// and her eyes as staring), up and to one side of the pupil,
// drifting a little as she is seen from elsewhere. Where on the iris (in its
// radii) and how bright.
uniform vec2 catch_at = vec2(-0.34, -0.36);
uniform float catchlight = 0.55;
uniform float catch_size = 1.0;
// (how soft its edge: 1 as it was, smaller crisper)
uniform float catch_soft = 1.0;
// The iris's fibres and crypts, their light and dark about the paint's mean
// (1 as painted; less, softer: a painted iris's blotches read as a render).
uniform float iris_contrast = 1.0;
// Where the paint's amber (inside `ring`) gives way to its green, as seen (in
// the iris's radii; 0 as painted): smaller, a thinner collarette.
uniform float ring_to = 0.0;
// The pupil's own darkness (never black: the lens behind it holds a little light).
uniform float pupil_dark = 0.012;
// The whites' colour over the paint's, and how much pinker toward the corners.
uniform vec3 white_tint = vec3(0.9, 0.84, 0.8);
uniform float corner_pink = 0.6;
// The upper lid's shadow on the eye: how dark at its margin, and where that
// margin rests (in irises' radii from the iris's painted middle, +y down;
// arched, lower toward the corners), fading over `lid_fade` below it. 0: none.
uniform float lid_shadow = 0.0;
uniform float lid_y = -0.75;
uniform float lid_fade = 0.5;
// The wet line along the lower lid: the cornea's sheen raised in a thin band
// at `low_y` (in irises' radii). 0: none.
uniform float low_wet = 0.0;
uniform float low_y = 0.95;
// How small on screen the eye goes from itself to one dark mark: from a
// pixel covering 2^far_from of its paint's texels to 2^far_to.
uniform float far_from = 4.0;
uniform float far_to = 6.0;

varying float under_lid;
varying float corner;
// The cornea's reflectance for the lights on her (fragment() to light()).
varying float sheen;

void vertex() {
	// (the eyeball's own normal: up under the upper lid, out to the side at the corners)
	under_lid = smoothstep(-0.05, 0.55, NORMAL.y);
	corner = smoothstep(0.35, 0.85, 1.0 - NORMAL.z);
}

void fragment() {
	vec2 c0 = UV.x > UV.y ? iris_a : iris_b;                     // (where its iris is painted)
	vec2 c = c0 + (UV.x > UV.y ? gaze_a : gaze_b) * iris_r;     // (where it is looking)
	vec2 d = (UV - c) / iris_r;
	float r = length(d);
	float in_iris = 1.0 - smoothstep(0.97, 1.02, r);
	// The view, in the paint's own directions, for the iris seen through the
	// cornea (its directions made square to the eye's surface: a ball's
	// tangents from a flat projection of it lean).
	vec3 n = normalize(NORMAL);
	vec3 tu = normalize(TANGENT - n * dot(TANGENT, n));
	vec3 tv = normalize(BINORMAL - n * dot(BINORMAL, n) - tu * dot(BINORMAL, tu));
	vec3 v = normalize(vec3(dot(VIEW, tu), dot(VIEW, -tv), dot(VIEW, n)));
	vec2 shift = v.xy / max(v.z, 0.25) * depth * iris_r * (1.0 - r * r) * in_iris;
	vec2 uv = UV - shift;
	// (the pupil opened or closed: the iris's paint stretched about its middle)
	vec2 dd = (uv - c) / iris_r;
	float rr = length(dd);
	float t = clamp((rr - pupil) / (1.0 - pupil), 0.0, 1.0);
	float src = mix(0.28, 1.0, t);
	// (the amber drawn in to `ring_to`: the paint inside `ring` laid from the
	// pupil out to it, the rest from there to the edge)
	if (ring_to > 0.0)
		src = rr < ring_to ? mix(0.28, ring, clamp((rr - pupil) / max(ring_to - pupil, 1e-3), 0.0, 1.0))
			: mix(ring, 1.0, clamp((rr - ring_to) / (1.0 - ring_to), 0.0, 1.0));
	vec3 ir = texture(iris, vec2(0.5) + dd / max(rr, 1e-4) * src * 0.412).rgb;
	if (iris_contrast != 1.0) {
		float l0 = dot(ir, vec3(0.2126, 0.7152, 0.0722));
		ir *= max(PAINT_LIGHT + (l0 - PAINT_LIGHT) * iris_contrast, 0.0) / max(l0, 1e-4);
	}
	if (recolour > 0.0) {
		float lum = dot(ir, vec3(0.2126, 0.7152, 0.0722));
		vec3 hue = mix(ring_colour, iris_colour, smoothstep(ring - 0.1, ring + 0.12, src));
		// (a little of the paint's own hue left in, so the fibres are not all one dye)
		vec3 own = clamp(ir / max(lum, 1e-4), vec3(0.5), vec3(1.6));
		vec3 dyed = hue * (lum / PAINT_LIGHT) * mix(vec3(1.0), own, 0.15);
		ir = mix(ir, dyed, recolour);
	}
	ir *= iris_light;
	if (rr < pupil) ir = vec3(pupil_dark);
	vec3 col = mix(texture(eye, UV).rgb, ir * tint, in_iris);
	// The limbal ring: the iris's edge dark, as the sclera meets it.
	col *= 1.0 - limbal * smoothstep(limbal_from, 0.98, r) * (1.0 - smoothstep(1.0, 1.1, r));
	// The whites warmer and softer than the paint's, shadowed under the lid and at the corners.
	float white = 1.0 - in_iris;
	col = mix(col, col * white_tint, white);
	// (pinker toward the corners, where the white is thinner over the blood)
	col = mix(col, col * vec3(1.0, 0.8, 0.78), corner * white * corner_pink);
	float shade = (1.0 - lids * under_lid) * (1.0 - 0.5 * corner);
	// (the upper lid's own shadow along its margin, on white and iris alike;
	// held to the eyeball, so the iris moves under it as she looks about)
	vec2 d0 = (UV - c0) / iris_r;
	float margin = lid_y + 0.25 * d0.x * d0.x;
	shade *= 1.0 - lid_shadow * (1.0 - smoothstep(margin, margin + lid_fade, d0.y));
	// Small on screen (the game's camera, her eye a pixel or two), the eye
	// read as one dark mark, as an eye at a distance does (lashes and the
	// shadow of the lid over it), not a white fleck: the white darkened
	// toward the iris's own darkness, the more the smaller (by how many of
	// the paint's texels a pixel covers).
	vec2 tx = UV * vec2(textureSize(eye, 0));
	float lod = 0.5 * log2(max(dot(dFdx(tx), dFdx(tx)), dot(dFdy(tx), dFdy(tx))));
	float far = smoothstep(far_from, far_to, lod);
	col = mix(col, ir * tint * 0.6, far * white);
	ALBEDO = col * shade * (1.0 - 0.35 * far);
	ALPHA = texture(eye, UV).a;
	ALPHA_SCISSOR_THRESHOLD = 0.5;
	// Wet: a sharp highlight off the cornea's dome over the iris (no brighter:
	// the portrait's broad key light made it a second blob).
	ROUGHNESS = wet_rough;
	sheen = wet * mix(1.0, 0.55, under_lid);
	// (the tear film pooled along the lower lid: a thin brighter wet line)
	float lw = low_y + 0.2 * d0.x * d0.x;
	sheen *= 1.0 + low_wet * smoothstep(lw - 0.12, lw - 0.03, d0.y) * (1.0 - smoothstep(lw - 0.03, lw + 0.04, d0.y));
	SPECULAR = sky_wet * mix(1.0, 0.55, under_lid);
	vec2 slope = r < 1.0 ? -2.0 * dome * d : vec2(0.0);
	NORMAL_MAP = normalize(vec3(-slope.x, slope.y, 1.0 / 0.35)) * 0.5 + 0.5;
	NORMAL_MAP_DEPTH = 1.0;
	SSS_STRENGTH = 0.2 * white;
	vec2 at_c = catch_at + v.xy * vec2(0.3, -0.3);
	float glint = 1.0 - smoothstep((0.06 - 0.025 * catch_soft) * catch_size, (0.06 + 0.025 * catch_soft) * catch_size, length((d - at_c) * vec2(1.0, 1.25)));
	EMISSION = vec3(0.95, 0.97, 1.0) * glint * catchlight * in_iris * (1.0 - under_lid * 0.7);
}

float schlick(float u) {
	float m = clamp(1.0 - u, 0.0, 1.0);
	float m2 = m * m;
	return m2 * m2 * m;
}

// Each light on her eye as Godot's own (Burley's diffuse, GGX's sheen), the
// sheen at the cornea's own reflectance (`sheen`), not the sky's.
void light() {
	float c_ndl = clamp(dot(NORMAL, LIGHT), 0.0, 1.0);
	float c_ndv = max(dot(NORMAL, VIEW), 1e-4);
	vec3 h = normalize(VIEW + LIGHT);
	float c_ndh = clamp(dot(NORMAL, h), 0.0, 1.0);
	float c_ldh = clamp(dot(LIGHT, h), 0.0, 1.0);
	float fd90 = 2.0 * c_ldh * c_ldh * ROUGHNESS - 0.5;
	float burley = (1.0 + fd90 * schlick(c_ndv)) * (1.0 + fd90 * schlick(c_ndl));
	DIFFUSE_LIGHT += LIGHT_COLOR * (c_ndl * burley / PI) * ATTENUATION;
	if (c_ndl > 0.0) {
		float a = ROUGHNESS * ROUGHNESS;
		float da = c_ndh * a;
		float k = a / (1.0 - c_ndh * c_ndh + da * da);
		float d_ggx = k * k / PI;
		float v_ggx = 0.5 / mix(2.0 * c_ndl * c_ndv, c_ndl + c_ndv, a);
		float f0 = 0.16 * sheen * sheen;
		float f = f0 + (clamp(f0 * 50.0, 0.0, 1.0) - f0) * schlick(c_ldh);
		SPECULAR_LIGHT += c_ndl * d_ggx * f * v_ggx * LIGHT_COLOR * ATTENUATION * SPECULAR_AMOUNT;
	}
}
