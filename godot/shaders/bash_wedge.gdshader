// Shield Bash's wedge (BattleFx.ShieldBash, HitKit.cs): a bronze-gold front of force driven forward over the
// ground from the shield, across exactly what the bash strikes (Arts.ShieldBash: +-1.2 rad round her facing,
// out to 3.4 m), its weight on the facing line and thinning toward the sides. The front runs out over 4
// frames (fast first, easing), a hot lip at its leading edge, a trail of broken plow-streaks behind it,
// all fading as it goes. No ring round her: the mesh starts at the shield (0.65 m, where the wedge is
// 1.2 m across). Light only.
// The mesh (BattleFx.WedgeMesh): UV.x from the shield (0) to the reach (1), UV.y the angle, -1..1 across +-1.2 rad.
// COLOR.rgb its hue; COLOR.a its age, 0..1 over its life (on the frame's own clock: a hitstop holds the
// bodies, not the shove).
shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, depth_test_disabled, cull_disabled, shadows_disabled, fog_disabled;

#include "res://shaders/hero_clear.gdshaderinc"

float hash(float n) { return fract(sin(n * 91.345) * 47453.5453); }

void fragment() {
	float p = COLOR.a;
	float x = UV.x;
	float y = UV.y;
	float ay = abs(y);
	// The front: out from the shield to past the reach, fast at first.
	float front = mix(0.04, 1.08, 1.0 - pow(1.0 - p, 2.2));
	float d = front - x;
	float lip = exp(-pow(d / 0.045, 2.0));
	float wake = d > 0.0 ? exp(-d * 3.2) : 0.0;
	// Plow streaks: broken radial runs across the wedge, each its own length and strength.
	float col = floor((y + 1.0) * 26.0);
	float h = hash(col), h2 = hash(col + 17.0);
	float lane = 1.0 - abs(fract((y + 1.0) * 26.0) - 0.5) * 2.0;
	float streak = smoothstep(0.15, 0.75, lane) * step(0.25, h) * (0.55 + 0.45 * h2) * smoothstep(0.0, 0.25, d) * exp(-d * (2.0 + 4.0 * h));
	// Its weight forward: full on the facing line, a third at the sides, soft at the edges.
	float fwd = (0.33 + 0.67 * pow(1.0 - ay, 1.6)) * smoothstep(1.0, 0.82, ay);
	// Fading as it goes, the near end first (it has left the shield).
	float fade = pow(1.0 - p, 1.4) * smoothstep(0.0, 0.08, x + 0.04 - p * 0.3);
	float lum = max(COLOR.r, max(COLOR.g, COLOR.b));
	vec3 hot = vec3(1.0, 0.9, 0.7) * lum;
	vec3 e = COLOR.rgb * (wake * 0.75 + streak * 1.2) + mix(COLOR.rgb, hot, 0.6) * lip * 1.3;
	ALBEDO = e * fwd * fade * hero_clear(VERTEX, VIEW_MATRIX, PROJECTION_MATRIX, VIEWPORT_SIZE);
}
