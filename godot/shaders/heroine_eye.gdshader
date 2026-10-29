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
// (the catchlight's own colour, and how much of the iris's albedo it takes out under it: a window's reflection
// replaces what is behind it, it is not added to it, and added it read pink-warm over a brown iris)
uniform vec3 catch_colour = vec3(0.95, 0.97, 1.0);
uniform float catch_dim = 0.0;
// (its shape: 0 round; 1 a soft-cornered window, wider than tall, as a softbox or a window shows in the portraits)
uniform float catch_window = 0.0;
// The iris's fibres and crypts, their light and dark about the paint's mean
// (1 as painted; less, softer: a painted iris's blotches read as a render).
uniform float iris_contrast = 1.0;
// (a dark swatch's pattern at this share of iris_contrast: a near-black brown's spokes stood out as a regular rosette
// where her portraits' dark irises read velvety, judge j1, 11 October 2026; full by a swatch of linear lightness 0.04)
uniform float dark_contrast = 0.5;
// Where the paint's amber (inside `ring`) gives way to its green, as seen (in
// the iris's radii; 0 as painted): smaller, a thinner collarette.
uniform float ring_to = 0.0;
// The collarette's light against the outer iris's (1 as painted or dyed): in every portrait the outer iris is
// the lighter (0.64 to 0.93 of it at the collarette), and an iris lighter round the pupil read as an amber starburst.
uniform float ring_light = 1.0;
// The pupil's own darkness (never black: the lens behind it holds a little light).
uniform float pupil_dark = 0.012;
// The whites' colour over the paint's, and how much pinker toward the corners.
uniform vec3 white_tint = vec3(0.9, 0.84, 0.8);
uniform float corner_pink = 0.6;
// The whites lit from below as a portrait's are (the lid shades their top): how much lighter half an iris's radius
// below its middle than at it. 0: flat.
uniform float white_grad = 0.0;
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
// (and the wet line's own light: its albedo lifted so, as the tear film catches the room, not only the lights)
uniform float low_lift = 0.0;
// How small on screen the eye goes from itself to one dark mark: from a
// pixel covering 2^far_from of its paint's texels to 2^far_to.
uniform float far_from = 4.0;
uniform float far_to = 6.0;
// (the catchlight dimmed as the eye gets small on screen: at the town close-up her iris is ~7 px and the full window,
// spread by the glow, washed the whole iris a pale icy grey, the owner's "glassy eyes"; face 38. 0 = as before)
uniform float catch_far = 0.0;
// (small on screen, face 38: how much of the white is taken to the iris's darkness (1 as before: at the close-up
// it left iris and white one grey, Oklab C 0.02, L within 0.03 of each other); the iris's chroma raised and its
// light lowered, so it reads its own colour, darker than the white; the catchlight shrunk)
uniform float far_white = 1.0;
uniform float far_sat = 0.0;
// (the iris's chroma at any size: below 1 less saturated)
uniform float iris_sat = 1.0;
uniform float far_iris = 0.0;
uniform float catch_far_size = 0.0;
// (face 38 r2: the parallax's view slope capped (turned 40 the iris smeared into streaks and the pupil to a sliver;
// 4 = the old floor); the cornea's sheen and sky over the pupil (navy over the black); the skin's depth, 0 to 1
// (set from her skin), with how much it lowers and warms the whites and darkens the iris)
uniform float par_max = 4.0;
uniform float pupil_wet = 1.0;
uniform float skin_deep = 0.0;
uniform float deep_white = 1.0;
uniform float deep_iris = 0.0;
// (face 38 r3: the iris seen through the cornea, as a real eye's is: turned away, its pattern and pupil
// foreshortened far less than the white round it (the cornea's lens), so a pupil read as a cat's slit at 40
// degrees. `cornea_round` 0 as before; 1 the pupil round on screen at any angle (its outline kept as it is);
// measured by the eye's own UV footprint on screen, so it also squares the paint's UV stretch (~4%) head-on.
// `catch_round`: the catchlight round on screen (1) rather than drawn on the ball (0); `catch_drift` how far it
// slides with the view (0.3 as before); `far_iso` the eye's size on screen taken from its footprint's short side
// (1), not its long one (0, as before: turned, the eye counted as far off and its catchlight was put out))
uniform float cornea_round = 0.0;
uniform float catch_round = 0.0;
uniform float catch_drift = 0.3;
uniform float far_iso = 0.0;
// (developer's view: 1 the iris's regions as laid on the ball (red pupil, blue to half, green to its edge); 2 as seen)
uniform float dbg = 0.0;
// By night (People.HerEyesNight, the game's night close-up: 0 by day, 1 at night), her lids' and corners'
// shade on the eye eased by `night_lid` of itself: under the key's low, warm light the shade took the iris to
// near black (fair cun r3: iris 10-30 of 255, one dark disc with the pupil) and the far eye's outer white to a
// hard black wedge at the lash line.
uniform float night_ease = 0.0;
uniform float night_lid = 0.5;
// A catchlight light (Face 48 round 3, GameCinemaHer's HerEye): a light whose specular is 15.5 (SPECULAR_AMOUNT 31)
// lights the cornea's sheen only, at `eye_light_rough` and times `eye_light_gain`, and nothing of the eye's diffuse:
// faint enough not to light her skin, it puts a small crisp window in each open eye from just above the lens.
uniform float eye_light_rough = 0.3;
uniform float eye_light_gain = 1500.0;
// (and her iris lifted by night: green under the fire's orange read near black beside its whites even unshaded,
// iris 22 of 255 to the whites' 66, where by day it is about half the white)
uniform float night_iris = 1.0;
// (its colour held by night to `night_sat` of itself, so lifted it reads a dark olive, not a lit green; and none of
// it on deep skin, whose eyes stay as dark as its face by night: lifted they glowed out of its shadow side)
uniform float night_sat = 1.0;
// (warmed toward olive by `night_warm`: the night grade's blue took a lifted green to teal)
uniform float night_warm = 0.0;

varying float under_lid;
varying float corner;
// The cornea's reflectance for the lights on her (fragment() to light()).
varying float sheen;
// (the cornea, for the catchlight light: the iris and a little round it)
varying float cornea;

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
	cornea = 1.0 - smoothstep(1.0, 1.2, r);
	// The view, in the paint's own directions, for the iris seen through the
	// cornea (its directions made square to the eye's surface: a ball's
	// tangents from a flat projection of it lean).
	vec3 n = normalize(NORMAL);
	vec3 tu = normalize(TANGENT - n * dot(TANGENT, n));
	vec3 tv = normalize(BINORMAL - n * dot(BINORMAL, n) - tu * dot(BINORMAL, tu));
	vec3 v = normalize(vec3(dot(VIEW, tu), dot(VIEW, -tv), dot(VIEW, n)));
	vec2 tv2 = v.xy / max(v.z, 0.25);
	tv2 /= max(1.0, length(tv2) / par_max);
	vec2 shift = tv2 * depth * iris_r * (1.0 - r * r) * in_iris;
	vec2 uv = UV - shift;
	// (the pupil opened or closed: the iris's paint stretched about its middle)
	vec2 dd = (uv - c) / iris_r;
	// (the eye's UV footprint on screen: `ax` the UV direction squeezed most, `asq` how much (1 round))
	vec2 ux = dFdx(UV), uy = dFdy(UV);
	float jxx = ux.x * ux.x + uy.x * uy.x, jxy = ux.x * ux.y + uy.x * uy.y, jyy = ux.y * ux.y + uy.y * uy.y;
	float jh = 0.5 * (jxx + jyy), jd = sqrt(max(0.25 * (jxx - jyy) * (jxx - jyy) + jxy * jxy, 0.0));
	float jmax = jh + jd, jmin = max(jh - jd, 1e-12);
	vec2 ax = abs(jxy) > 1e-12 ? normalize(vec2(jmax - jyy, jxy)) : (jxx >= jyy ? vec2(1.0, 0.0) : vec2(0.0, 1.0));
	float asq = sqrt(jmin / max(jmax, 1e-12));
	// (the pattern within the outline drawn out along it, fully at the middle, none at the edge)
	float st = mix(pow(max(asq, 0.15), cornea_round), 1.0, min(dot(dd, dd), 1.0));
	dd += ax * dot(dd, ax) * (st - 1.0);
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
		float dk = recolour > 0.0 ? 1.0 - smoothstep(0.018, 0.04, dot(iris_colour, vec3(0.2126, 0.7152, 0.0722))) : 0.0;
		ir *= max(PAINT_LIGHT + (l0 - PAINT_LIGHT) * iris_contrast * mix(1.0, dark_contrast, dk), 0.0) / max(l0, 1e-4);
	}
	if (recolour > 0.0) {
		float lum = dot(ir, vec3(0.2126, 0.7152, 0.0722));
		vec3 hue = mix(ring_colour, iris_colour, smoothstep(ring - 0.1, ring + 0.12, src));
		// (a little of the paint's own hue left in, so the fibres are not all one dye)
		vec3 own = clamp(ir / max(lum, 1e-4), vec3(0.5), vec3(1.6));
		vec3 dyed = hue * (lum / PAINT_LIGHT) * mix(vec3(1.0), own, 0.15);
		ir = mix(ir, dyed, recolour);
	}
	// (the collarette's light: the paint inside `ring` (as laid, `src`) against the rest)
	if (ring_light != 1.0) ir *= mix(ring_light, 1.0, smoothstep(ring - 0.1, ring + 0.12, src));
	ir *= iris_light;
	vec2 tx = UV * vec2(textureSize(eye, 0));
	float lod = 0.5 * log2(max(dot(dFdx(tx), dFdx(tx)), dot(dFdy(tx), dFdy(tx))));
	lod = mix(lod, 0.5 * log2(jmin * dot(vec2(textureSize(eye, 0)), vec2(textureSize(eye, 0))) * 0.5), far_iso);
	float far = smoothstep(far_from, far_to, lod);
	if (far_sat > 0.0 || far_iris > 0.0 || iris_sat != 1.0) {
		float fl = dot(ir, vec3(0.2126, 0.7152, 0.0722));
		ir = max(vec3(fl) + (ir - vec3(fl)) * (iris_sat + far_sat * far), vec3(0.0)) * (1.0 - far_iris * far);
	}
	ir *= 1.0 - deep_iris * skin_deep;
	float nk = night_ease * (1.0 - skin_deep);
	ir *= mix(1.0, night_iris, nk) * mix(vec3(1.0), vec3(1.0, 0.92, 0.6), night_warm * nk);
	ir = max(mix(vec3(dot(ir, vec3(0.2126, 0.7152, 0.0722))), ir, mix(1.0, night_sat, nk)), vec3(0.0));
	// (the pupil laid after the iris's tint, so its darkness is its own on a painted iris too; its edge a
	// little soft, as a lens's is)
	float pup_in = (1.0 - smoothstep(pupil - 0.02, pupil + 0.015, rr)) * in_iris;
	vec3 irt = mix(vec3(pupil_dark), ir * tint, 1.0 - pup_in / max(in_iris, 1e-4));
	vec3 col = mix(texture(eye, UV).rgb, irt, in_iris);
	// The limbal ring: the iris's edge dark, as the sclera meets it.
	col *= 1.0 - limbal * smoothstep(limbal_from, 0.98, r) * (1.0 - smoothstep(1.0, 1.1, r));
	// The whites warmer and softer than the paint's, shadowed under the lid and at the corners.
	float white = 1.0 - in_iris;
	vec2 d0 = (UV - c0) / iris_r;
	float lit_below = 1.0 - 0.23 * white_grad + white_grad * smoothstep(-0.05, 0.5, d0.y);
	col = mix(col, col * white_tint * mix(vec3(1.0), vec3(0.784, 0.735, 0.69), skin_deep * deep_white) * lit_below, white);
	// (pinker toward the corners, where the white is thinner over the blood)
	col = mix(col, col * vec3(1.0, 0.8, 0.78), corner * white * corner_pink);
	float ease = 1.0 - nk * night_lid;
	float shade = (1.0 - lids * ease * under_lid) * (1.0 - 0.5 * ease * corner);
	// (the upper lid's own shadow along its margin, on white and iris alike;
	// held to the eyeball, so the iris moves under it as she looks about)
	float margin = lid_y + 0.25 * d0.x * d0.x;
	shade *= 1.0 - lid_shadow * ease * (1.0 - smoothstep(margin, margin + lid_fade, d0.y));
	// Small on screen (the game's camera, her eye a pixel or two), the eye
	// read as one dark mark, as an eye at a distance does (lashes and the
	// shadow of the lid over it), not a white fleck: the white darkened
	// toward the iris's own darkness, the more the smaller (by how many of
	// the paint's texels a pixel covers).
	col = mix(col, ir * tint * 0.6, far * white * far_white);
	// (the tear film pooled along the lower lid: a thin brighter wet line, in its light and its sheen)
	float lw = low_y + 0.2 * d0.x * d0.x;
	float wet_line = smoothstep(lw - 0.12, lw - 0.03, d0.y) * (1.0 - smoothstep(lw - 0.03, lw + 0.04, d0.y));
	vec2 at_c = catch_at + v.xy * vec2(catch_drift, -catch_drift);
	vec2 dq = d - at_c;
	dq += ax * dot(dq, ax) * (mix(1.0, asq, catch_round) - 1.0);
	vec2 dc = abs(dq * vec2(1.0, 1.25));
	float cr = mix(length(dc), pow(pow(dc.x, 4.0) + pow(dc.y, 4.0), 0.25), catch_window);
	float cs = catch_size * (1.0 - catch_far_size * far);
	float glint = 1.0 - smoothstep((0.06 - 0.025 * catch_soft) * cs, (0.06 + 0.025 * catch_soft) * cs, cr);
	glint *= in_iris * (1.0 - under_lid * 0.7);
	ALBEDO = col * shade * (1.0 - 0.35 * far) * (1.0 + low_lift * wet_line) * (1.0 - catch_dim * glint);
	ALPHA = texture(eye, UV).a;
	ALPHA_SCISSOR_THRESHOLD = 0.5;
	// Wet: a sharp highlight off the cornea's dome over the iris (no brighter:
	// the portrait's broad key light made it a second blob).
	ROUGHNESS = wet_rough;
	sheen = wet * mix(1.0, 0.55, under_lid) * mix(1.0, pupil_wet, pup_in);
	sheen *= 1.0 + low_wet * wet_line;
	SPECULAR = sky_wet * mix(1.0, 0.55, under_lid) * mix(1.0, pupil_wet, pup_in);
	vec2 slope = r < 1.0 ? -2.0 * dome * d : vec2(0.0);
	NORMAL_MAP = normalize(vec3(-slope.x, slope.y, 1.0 / 0.35)) * 0.5 + 0.5;
	NORMAL_MAP_DEPTH = 1.0;
	SSS_STRENGTH = 0.2 * white;
	EMISSION = catch_colour * glint * catchlight * (1.0 - catch_far * far);
	if (dbg > 2.5) { ALBEDO = vec3(0.0); EMISSION = vec3(asq, abs(ax.x) * asq, abs(ax.y) * asq) * 0.3 * in_iris; }
	else if (dbg > 0.0) {
		vec2 q = dbg > 1.5 ? dd : d;
		ALBEDO = vec3(0.0);
		float lq = length(q); EMISSION = (lq < pupil ? vec3(1.0, 0.0, 0.0) : lq < 0.5 ? vec3(0.0, 0.0, 1.0) : lq < 1.0 ? vec3(0.0, 1.0, 0.0) : vec3(0.0)) * 0.25;
	}
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
	bool eye_only = abs(SPECULAR_AMOUNT - 31.0) < 0.3 || abs(SPECULAR_AMOUNT - 15.5) < 0.15;
	if (!eye_only) DIFFUSE_LIGHT += LIGHT_COLOR * (c_ndl * burley / PI) * ATTENUATION;
	if (c_ndl > 0.0) {
		float rough = eye_only ? eye_light_rough : ROUGHNESS;
		float a = rough * rough;
		float da = c_ndh * a;
		float k = a / (1.0 - c_ndh * c_ndh + da * da);
		float d_ggx = k * k / PI;
		float v_ggx = 0.5 / mix(2.0 * c_ndl * c_ndv, c_ndl + c_ndv, a);
		float f0 = 0.16 * sheen * sheen;
		float f = f0 + (clamp(f0 * 50.0, 0.0, 1.0) - f0) * schlick(c_ldh);
		SPECULAR_LIGHT += c_ndl * d_ggx * f * v_ggx * LIGHT_COLOR * ATTENUATION * (eye_only ? eye_light_gain * cornea : SPECULAR_AMOUNT);
	}
}
