// Shield Bash's wedge (BattleFx.ShieldBash, HitKit.cs; VFX 10 r3): a bronze front of force driven forward over the
// ground from the shield's face (0.5 m) across exactly what the bash strikes (Arts.ShieldBash: +-1.2 rad round her
// facing, out to 3.4 m). Weighted forward, not a folding fan: 100% on the facing line, ~50% at +-35 degrees, under
// 15% at the sides (+-69). Its rim is ragged, ~10 px thick at the centre tapering to ~2 px at the sides; 6-9 irregular
// rays behind it, mostly within +-35 degrees. Core #E0A050, rim #FFD9A0. The front runs out over 4 frames (fast first),
// its standing face is bash_wall.gdshader. Light only.
// The mesh (BattleFx.WedgeMesh): UV.x from the shield (0) to the reach (1), UV.y the angle, -1..1 across +-1.2 rad.
// COLOR.r its strength (lower by night, so the rim never clips); COLOR.a its age, 0..1 over its life.
shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, depth_test_disabled, cull_disabled, shadows_disabled, fog_disabled;

#include "res://shaders/hero_clear.gdshaderinc"

float h1(float n) { return fract(sin(n * 91.345) * 47453.5453); }
float n1(float x) { float i = floor(x), f = fract(x); f = f * f * (3.0 - 2.0 * f); return mix(h1(i), h1(i + 1.0), f); }

const vec3 CORE = vec3(0.745, 0.352, 0.080);   // #E0A050
const vec3 RIM = vec3(1.0, 0.693, 0.352);      // #FFD9A0

void fragment() {
	float p = COLOR.a, k = COLOR.r;
	float x = UV.x, y = UV.y, ay = abs(y);
	// Forward weight: a bell on the facing line (50% at |y| 0.51 = 35 degrees, 7% at the sides).
	float fwd = exp(-pow(ay / 0.612, 2.0)) * smoothstep(1.0, 0.9, ay);
	// The front, ragged across it.
	float front = mix(0.04, 1.08, 1.0 - pow(1.0 - p, 2.2)) + (n1(y * 9.0 + 3.1) - 0.5) * 0.045 + (n1(y * 23.0) - 0.5) * 0.015;
	float d = front - x;
	// The rim: ~0.053 of the reach (~10 px) thick on the facing line, ~0.011 (~2 px) at the sides.
	float lw = mix(0.011, 0.053, exp(-pow(ay / 0.5, 2.0)));
	float lip = smoothstep(-0.006, 0.004, d) * (1.0 - smoothstep(lw * 0.5, lw, d));
	float wake = d > 0.0 ? exp(-d * 4.5) : 0.0;
	// Rays: 8 irregular radial runs behind the front, clustered within +-35 degrees.
	float rays = 0.0;
	for (int i = 0; i < 8; i++) {
		float fi = float(i);
		float hy = h1(fi * 7.13 + 1.7) * 2.0 - 1.0;
		float yi = sign(hy) * pow(abs(hy), 1.6) * 0.75;
		float wi = 0.012 + 0.03 * h1(fi * 3.7 + 9.1);
		float len = 0.18 + 0.45 * h1(fi * 5.9 + 2.3);
		float r = exp(-pow((y - yi) / wi, 2.0)) * (0.5 + 0.5 * h1(fi * 11.3));
		rays += r * smoothstep(0.0, 0.03, d) * (1.0 - smoothstep(len * 0.4, len, d));
	}
	// Fading as it goes, the near end first (it has left the shield).
	float fade = pow(1.0 - p, 1.3) * smoothstep(0.0, 0.08, x + 0.04 - p * 0.3);
	vec3 e = CORE * (wake * 0.55 + rays * 0.9) + RIM * lip * 1.15;
	ALBEDO = e * k * fwd * fade * hero_clear(VERTEX, VIEW_MATRIX, PROJECTION_MATRIX, VIEWPORT_SIZE);
}
