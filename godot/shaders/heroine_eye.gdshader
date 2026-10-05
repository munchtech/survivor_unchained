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
// The iris's light over all (painted or dyed), against her skin's: measured
// in the game against the portraits (at 1, her irises showed two and a half
// times as light against her cheek as her portrait's, and Fey's frost white;
// the colours chosen are dyed for 0.4).
uniform float iris_light = 0.4;
// Where she is looking, each eye's iris slid over its ball (in irises'
// radii: +x to her left, +y down; both eyes' paint the same way round).
uniform vec2 gaze_a = vec2(0.0);
uniform vec2 gaze_b = vec2(0.0);
uniform float lids = 0.7;
// A catchlight: the small soft window every lit eye carries on its cornea
// (what makes a face look alive on screen; larger, it read as a white blob
// and her eyes as staring), up and to one side of the pupil,
// drifting a little as she is seen from elsewhere. Where on the iris (in its
// radii) and how bright. (Her paint's u and v run to her right and up her
// eye, as she is seen: at (-0.34, -0.36) it sat under her pupil, on the far
// side from her key light's own highlight, two white blobs to an eye; here
// it lies with that one, above and to her right.)
uniform vec2 catch_at = vec2(0.32, 0.34);
uniform float catchlight = 0.55;
// How small on screen the eye goes from itself to one dark mark: from a
// pixel covering 2^far_from of its paint's texels to 2^far_to.
uniform float far_from = 4.0;
uniform float far_to = 6.0;

varying float under_lid;
varying float corner;

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
	vec3 ir = texture(iris, vec2(0.5) + dd / max(rr, 1e-4) * src * 0.412).rgb;
	if (recolour > 0.0) {
		float lum = dot(ir, vec3(0.2126, 0.7152, 0.0722));
		vec3 hue = mix(ring_colour, iris_colour, smoothstep(ring - 0.1, ring + 0.12, src));
		// (a little of the paint's own hue left in, so the fibres are not all one dye)
		vec3 own = clamp(ir / max(lum, 1e-4), vec3(0.5), vec3(1.6));
		vec3 dyed = hue * (lum / PAINT_LIGHT) * mix(vec3(1.0), own, 0.15);
		ir = mix(ir, dyed, recolour);
	}
	ir *= iris_light;
	if (rr < pupil) ir = vec3(0.012);
	vec3 col = mix(texture(eye, UV).rgb, ir * tint, in_iris);
	// The limbal ring: the iris's edge dark, as the sclera meets it.
	col *= 1.0 - 0.62 * smoothstep(0.7, 0.98, r) * (1.0 - smoothstep(1.0, 1.1, r));
	// The whites warmer and softer than the paint's, shadowed under the lid and at the corners.
	float white = 1.0 - in_iris;
	col = mix(col, col * vec3(0.9, 0.84, 0.8), white);
	// (pinker toward the corners, where the white is thinner over the blood)
	col = mix(col, col * vec3(1.0, 0.8, 0.78), corner * white * 0.6);
	float shade = (1.0 - lids * under_lid) * (1.0 - 0.5 * corner);
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
	ROUGHNESS = 0.035;
	SPECULAR = 0.42 * mix(1.0, 0.55, under_lid);
	vec2 slope = r < 1.0 ? -2.0 * dome * d : vec2(0.0);
	NORMAL_MAP = normalize(vec3(-slope.x, slope.y, 1.0 / 0.35)) * 0.5 + 0.5;
	NORMAL_MAP_DEPTH = 1.0;
	SSS_STRENGTH = 0.2 * white;
	vec2 at_c = catch_at + v.xy * vec2(0.3, -0.3);
	float glint = 1.0 - smoothstep(0.035, 0.085, length((d - at_c) * vec2(1.0, 1.25)));
	EMISSION = vec3(0.95, 0.97, 1.0) * glint * catchlight * in_iris * (1.0 - under_lid * 0.7);
}
