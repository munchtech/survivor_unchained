// Her Oathblade's sweep (src/Fx/Blades.cs, Blades(oath: true)): one gold crescent leaving her hand,
// light only (blend_add: it lights what is under it, never darkens it).
// It is revealed along the arc with the swing (2 frames), then eaten from its tail by noise (3-4).
// Its width runs from the whole band at the leading end to about 30% at the trailing end, from the
// reach inward. Its body is the baked streaks (tools/fxsim/oath_streaks.py: 20-40 fine broken runs of
// varied length, scrolled along the arc), never even bands; only its leading 15% is white-hot.
//
// One instance per swing: COLOR.rgb its hue (linear, near 1 so the tone curve keeps it a colour),
// COLOR.a the inner radius as a share of the outer (the basis is scaled by the outer radius);
// INSTANCE_CUSTOM (head, erode, span in radians, seed): the blade's place along the arc (0 its start,
// 1 its end), how far the tail is eaten (0 none, 1 gone), the arc it sweeps, a seed.
// The mesh is a unit grid (UV.x along the swing, UV.y from the inner radius out to the reach).
shader_type spatial;
// (never hidden by the bodies it passes through: at 1 m up the crowd's heads covered most of it by day)
render_mode unshaded, blend_add, depth_draw_never, depth_test_disabled, cull_disabled, shadows_disabled, fog_disabled;

#include "res://shaders/hero_clear.gdshaderinc"

uniform sampler2D streaks : filter_linear_mipmap, repeat_enable;
// The strip's repeats per radian of arc at the reach.
uniform float tile = 1.5;

varying flat vec4 v_custom;
varying flat vec4 v_hue;

void vertex() {
	v_custom = INSTANCE_CUSTOM;
	v_hue = COLOR;
	float a = (UV.x - 0.5) * INSTANCE_CUSTOM.z;
	float r = mix(COLOR.a, 1.0, UV.y);
	// The swing's plane tilts up a little through its middle, as an arm's does.
	float lift = 0.06 * sin(UV.x * PI) * r;
	VERTEX = vec3(sin(a) * r, lift, cos(a) * r);
}

void fragment() {
	float head = v_custom.x, erode = v_custom.y, span = v_custom.z, seed = v_custom.w;
	float u = UV.x, s = UV.y;
	if (u > head + 0.03) discard;
	// 0 at the leading end (the blade), 1 at the trailing end (where the swing began).
	float t = clamp((head - u) / max(head, 0.08), 0.0, 1.0);
	// Width: the whole band at the lead, 30% at the trail, from the reach inward; soft inner edge.
	float inner = 1.0 - mix(1.0, 0.3, pow(t, 0.8));
	float band = smoothstep(inner - 0.04, inner + 0.16, s) * (1.0 - smoothstep(0.94, 1.0, s));
	// The leading end soft, the trailing end to a point.
	float front = 1.0 - smoothstep(head - 0.035, head + 0.03, u);
	float tail = smoothstep(0.0, 0.08, u);
	// The streaks, scrolled along the arc with the swing (they run on ahead as it goes).
	vec2 st = vec2(u * span * tile + fract(seed * 0.618) - head * 0.18, s * 0.94 + 0.03);
	vec4 tx = texture(streaks, st);
	float streak = tx.r;
	// Eaten from the tail as it dies: the noise against a threshold that runs from the tail to the lead.
	float val = (1.0 - t) * 0.55 + tx.g * 0.45;
	float thr = erode * 1.12 - 0.06;
	float keep = smoothstep(thr - 0.05, thr + 0.05, val);
	// Brighter toward the reach (the blade's tip moves fastest) and toward the lead.
	// (steeply: an even fill to her hand read as a solid gold plate, a pie slice, not a crescent)
	float out_k = mix(0.06, 1.0, pow(smoothstep(inner, 1.0, s), 1.6));
	vec3 hue = v_hue.rgb;
	// A low bed in the hue so it reads as one shape; the streaks carry it.
	float body = (0.07 + 1.3 * streak) * out_k * mix(1.0, 0.4, t);
	// The cutting edge at the reach: a thin line in the hue, fading along the tail.
	float ed = (s - 0.955) / 0.025;
	float edge = exp(-ed * ed) * mix(1.0, 0.25, t) * (0.6 + 0.6 * tx.b);
	vec3 col = hue * (body * 1.05 + edge * 0.9);
	// White-hot in the leading 15% only.
	float lead = 1.0 - smoothstep(0.0, 0.15, t);
	// (on the streaks and the edge only: a white bed under them read as a cream fog by her)
	col += vec3(1.0, 0.94, 0.82) * (2.0 * streak * smoothstep(inner + 0.15, 0.8, s) + edge * 1.3) * lead;
	float clear = hero_clear(VERTEX, VIEW_MATRIX, PROJECTION_MATRIX, VIEWPORT_SIZE);
	ALBEDO = col * band * front * tail * keep * clear;
}
