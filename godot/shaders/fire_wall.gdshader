// The wall of flame riding the rise's fire front (Cold, Then Not): tongues of flame standing all
// the way round her, each its own height, licking and flickering upward, yellow at their roots
// through orange to a dark red at their torn tips, with dark between them. The ground under it
// (fire_ring.gdshader) is its bed and its char.
//
// Drawn on a ring of cards (BattleFx.Rise: FireCards), each stood on the ring and turned about the
// upright to face the camera, two spacings wide and blended into its neighbours. On one cylinder
// the ring's left and right, seen edge-on from 56 degrees up, pressed into a thin smooth band (the
// "flame edge"); turned cards show their tongues at full width wherever they stand. Flame seen
// along the ring there stacks thicker, as real fire does.
//
// UV.x runs across a card (-1..1), UV.y up it; UV2.x is the card's place round the ring (0..1).
// The node's scale is (reach, height, reach). cells: tongues round the ring (an integer, so the
// noise wraps with no seam); segs: cards round it; burn: how strongly it burns (0..1).
shader_type spatial;
render_mode unshaded, blend_premul_alpha, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled, skip_vertex_transform;

#include "res://shaders/hero_clear.gdshaderinc"

uniform sampler2D depth_tex : hint_depth_texture, filter_nearest;
uniform float cells = 60.0;
uniform float segs = 144.0;
uniform float burn = 1.0;
uniform float seed = 0.0;
uniform float soft = 0.3;
// Held below the tone curve's knee: hotter, flame reads as cream (the last wall read as tan).
// (Measured: at 0.95, 0.5, 0.1 a wide wall came out (236, 155, 88), apricot. Deeper and redder
// still, so its body reads orange and only its hearts yellow.)
uniform vec3 hot = vec3(0.78, 0.33, 0.05);
uniform vec3 mid = vec3(0.5, 0.1, 0.01);
uniform vec3 deep = vec3(0.17, 0.012, 0.0);

vec2 grad(vec2 i) {
	float a = fract(sin(dot(i, vec2(127.1, 311.7)) + seed) * 43758.5453) * 6.2831853;
	return vec2(cos(a), sin(a));
}
// Gradient noise wrapping every `period` cells along x. About -0.7..0.7.
float gnoise(vec2 p, float period) {
	vec2 i = floor(p), f = fract(p);
	vec2 u = f * f * f * (f * (f * 6.0 - 15.0) + 10.0);
	float x0 = mod(i.x, period), x1 = mod(i.x + 1.0, period);
	float a = dot(grad(vec2(x0, i.y)), f);
	float b = dot(grad(vec2(x1, i.y)), f - vec2(1.0, 0.0));
	float c = dot(grad(vec2(x0, i.y + 1.0)), f - vec2(0.0, 1.0));
	float d = dot(grad(vec2(x1, i.y + 1.0)), f - vec2(1.0, 1.0));
	return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}
float fbm(vec2 p, float period) {
	float s = 0.0, a = 0.5;
	for (int i = 0; i < 4; i++) { s += a * gnoise(p, period); p *= 2.0; period *= 2.0; a *= 0.5; }
	return clamp(s * 1.1 + 0.5, 0.0, 1.0);
}

varying float round_s;
varying float up;
varying float across;

void vertex() {
	float a = UV2.x * TAU;
	vec3 foot = (MODEL_MATRIX * vec4(cos(a), 0.0, sin(a), 1.0)).xyz;
	float high = length(MODEL_MATRIX[1].xyz);
	float reach = length(MODEL_MATRIX[0].xyz);
	vec3 to_cam = INV_VIEW_MATRIX[3].xyz - foot;
	to_cam.y = 0.0;
	vec3 side = normalize(cross(vec3(0.0, 1.0, 0.0), to_cam) + vec3(1e-4, 0.0, 0.0));
	// Across the card the way the ring runs, so its tongues carry on into its neighbours'.
	vec3 along = vec3(-sin(a), 0.0, cos(a));
	if (dot(side, along) < 0.0) side = -side;
	float spacing = TAU * reach / segs;
	vec3 w = foot + side * UV.x * spacing + vec3(0.0, UV.y * high, 0.0);
	VERTEX = (VIEW_MATRIX * vec4(w, 1.0)).xyz;
	round_s = (UV2.x * segs + UV.x) * cells / segs;
	up = UV.y;
	across = UV.x;
}

void fragment() {
	float u = clamp(up, 0.0, 1.0);
	float x = round_s;
	float t = TIME;
	// The air rising through it licks every tongue sideways as it climbs.
	float lick = fbm(vec2(x * 1.5, u * 2.2 - t * 2.3), cells * 1.5) - 0.5;
	float xs = x + lick * 0.9 * u;
	// Each tongue rises to a point, its own height, the tall ones few, some guttering low.
	float n = fbm(vec2(xs * 1.25, t * 0.85), cells * 1.25);
	float ridge = 1.0 - abs(2.0 * n - 1.0);
	float high = 0.1 + 0.9 * pow(ridge, 1.6) * (0.85 + 0.15 * sin(t * 13.0 + xs * 2.7));
	// Torn as it climbs: the turbulence opens dark gaps toward the tips.
	float tear = fbm(vec2(xs * 2.8, u * 4.2 - t * 3.8), cells * 2.8);
	float body = 1.0 - u / max(0.05, high);
	float f = clamp(body * 1.3 - (1.0 - tear) * 0.65 * sqrt(u), 0.0, 1.0);
	// Its roots burn along the ground, but broken: never one smooth line.
	float roots = (1.0 - smoothstep(0.0, 0.14, u)) * smoothstep(0.25, 0.7, fbm(vec2(x * 2.1, t * 1.4), cells * 2.1));
	f = max(f, roots * 0.8);
	// Bright and dim within a tongue as it burns (the last wall's body was one flat tan).
	// The tall tongues burn hottest at their hearts; the low ones and the edges deep red.
	float flick = 0.65 + 0.55 * fbm(vec2(xs * 3.4, u * 3.0 - t * 5.0), cells * 3.4);
	float heat = f * mix(0.45, 1.1, pow(ridge, 1.5)) * flick;
	vec3 col = mix(deep, mid, smoothstep(0.12, 0.55, heat));
	col = mix(col, hot, smoothstep(0.7, 1.1, heat));
	float a = smoothstep(0.02, 0.32, f);
	// Blended into its neighbours: the windows of two cards always sum to one.
	float win = cos(across * 1.5707963);
	win *= win;
	// Where it stands in the ground it fades into it, so its foot is never a line.
	float d = textureLod(depth_tex, SCREEN_UV, 0.0).r;
	vec4 behind = INV_PROJECTION_MATRIX * vec4(SCREEN_UV * 2.0 - 1.0, d, 1.0);
	behind.xyz /= behind.w;
	float fade = clamp((VERTEX.z - behind.z) / soft, 0.0, 1.0) * burn * win;
	float clear = hero_clear(VERTEX, VIEW_MATRIX, PROJECTION_MATRIX, VIEWPORT_SIZE);
	// Mostly light, a little dark laid under it, as real flame does over what is behind it; the
	// torn tips darker (smoke-dark red) than the body.
	// Enough of what is behind is covered that flame seen along the ring, card behind card, comes
	// to its own colour and stops there, never past the knee to cream.
	ALBEDO = col * a * fade * clear;
	ALPHA = a * 0.62 * fade * clear;
}
