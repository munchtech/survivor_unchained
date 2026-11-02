// Her Oathblade's sweep (src/Fx/Blades.cs, Blades(oath: true)): one gold crescent at the blade's reach.
// (VFX 10 r3) A true crescent, not a glass bubble: ~0.28 m thick through its leading middle, tapering to points at
// both horns; white-gold on its outer edge toward the lead, saturated gold through its body, fading to clear toward
// her hand. Its streaks run ALONG the arc (radial ones echoed the bash's fan). Premultiplied: the gold body covers
// what is under it a little (so it keeps its saturation in sunlight), the hot edge only adds.
// Revealed along the arc with the swing (3 frames, its peak at f2), then eaten from the trailing horn toward the tip
// (half by f4, gone by f6; on real frames through a hitstop: BattleFx.Update).
//
// One instance per swing: COLOR.rgb its hue (linear, near 1), COLOR.a the inner radius as a share of the outer (the
// basis is scaled by the outer radius); INSTANCE_CUSTOM (head, erode, span in radians, seed): the blade's place along
// the arc (0 its start, 1 its end), how far it is eaten (0 none, 1 gone), the arc it sweeps, a seed.
// The mesh is a unit grid (UV.x along the swing, UV.y from the inner radius out to the reach).
shader_type spatial;
// (never hidden by the bodies it passes through: at 1 m up the crowd's heads covered most of it by day)
render_mode unshaded, blend_premul_alpha, depth_draw_never, depth_test_disabled, cull_disabled, shadows_disabled, fog_disabled;

#include "res://shaders/hero_clear.gdshaderinc"

// The crescent's thickness at its thickest (metres) and how far its gold fades on inward past that (shares of it).
uniform float thick = 0.28;
uniform float fade_in = 0.9;

varying flat vec4 v_custom;
varying flat vec4 v_hue;
varying flat float v_reach;

float h1(float n) { return fract(sin(n * 127.1) * 43758.5453); }
float n1(float x) { float i = floor(x), f = fract(x); f = f * f * (3.0 - 2.0 * f); return mix(h1(i), h1(i + 1.0), f); }

void vertex() {
	v_custom = INSTANCE_CUSTOM;
	v_hue = COLOR;
	v_reach = length(MODEL_MATRIX[2].xyz);
	float a = (UV.x - 0.5) * INSTANCE_CUSTOM.z;
	float r = mix(COLOR.a, 1.0, UV.y);
	// The swing's plane tilts up a little through its middle, as an arm's does.
	float lift = 0.06 * sin(UV.x * PI) * r;
	VERTEX = vec3(sin(a) * r, lift, cos(a) * r);
}

void fragment() {
	float head = v_custom.x, erode = v_custom.y, span = v_custom.z, seed = v_custom.w;
	float u = UV.x, s = UV.y;
	if (u > head + 0.02) discard;
	// 0 at the trailing horn (where the swing began), 1 at the leading tip (the blade).
	float p = clamp(u / max(head, 0.05), 0.0, 1.0);
	float metres = max(v_reach * (1.0 - v_hue.a), 0.1);
	// The crescent's profile: points at both horns, thickest a little ahead of the middle.
	float prof = pow(max(sin(PI * pow(p, 1.3)), 0.0), 0.75);
	float w = thick / metres * prof;
	// 0 at the outer edge, 1 at the crescent's inner edge (past it, the fade toward her hand).
	float d = (1.0 - s) / max(w, 1e-4);
	float outer = 1.0 - smoothstep(0.986, 1.0, s);
	float body = (1.0 - smoothstep(0.55, 1.0 + fade_in, d)) * outer * smoothstep(0.0, 0.02, prof);
	// The tip soft as the blade passes.
	body *= 1.0 - smoothstep(head - 0.01, head + 0.02, u);
	// Streaks ALONG the arc: lanes across the crescent's thickness, each broken along its length by its own noise,
	// running on ahead with the swing.
	float lane = d * 5.0;
	float li = floor(lane), lf = fract(lane);
	float along = u * span * v_reach * 3.2 + h1(li + seed) * 17.0 - head * 1.6;
	float run = smoothstep(0.38, 0.78, n1(along + li * 5.3));
	float streak = run * (1.0 - pow(abs(lf - 0.5) * 2.0, 2.0));
	// Eaten from the trailing horn toward the tip: a ragged front.
	float val = p * 0.78 + n1(u * span * v_reach * 6.0 + seed) * 0.22;
	float thr = erode * 1.14 - 0.06;
	float keep = smoothstep(thr - 0.04, thr + 0.04, val);
	// The colour: saturated gold through the body (hue ~42), white-gold on the outer quarter toward the lead.
	vec3 gold = v_hue.rgb * vec3(1.0, 0.92, 0.55);
	float hot = (1.0 - smoothstep(0.12, 0.32, d)) * mix(0.3, 1.0, smoothstep(0.35, 0.9, p));
	vec3 hotc = vec3(1.0, 0.86, 0.55) * 1.5;
	// Alpha: what the gold covers (strongest in the body's middle, none in the fade), premultiplied below.
	float cover = body * (1.0 - smoothstep(0.2, 1.0 + fade_in, d)) * 0.55 * (0.75 + 0.25 * run);
	float lum = body * (0.62 + 0.55 * streak) * (1.0 - smoothstep(0.3, 1.0 + fade_in, d) * 0.6);
	float clear = hero_clear(VERTEX, VIEW_MATRIX, PROJECTION_MATRIX, VIEWPORT_SIZE);
	float k = keep * clear;
	vec3 col = gold * lum + hotc * hot * body * (0.7 + 0.5 * streak);
	ALBEDO = col * k;
	ALPHA = clamp(cover * k, 0.0, 1.0);
}
