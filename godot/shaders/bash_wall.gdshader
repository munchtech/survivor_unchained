// Shield Bash's wave front standing up (BattleFx.StepWedges, VFX 10 r3): a soft bronze face 0.4 m tall riding the
// wedge's front (bash_wedge.gdshader), so the shove is not only a mark on the ground. Weighted forward as the wedge,
// brightest at its foot and gone by its top, its top edge ragged. Light only.
// The mesh (BattleFx.WallMesh): UV.x the angle (-1..1 across +-1.2 rad), UV.y up it (0..1).
// COLOR.r its strength (lower by night); COLOR.a its age, 0..1.
shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;

#include "res://shaders/hero_clear.gdshaderinc"

float h1(float n) { return fract(sin(n * 91.345) * 47453.5453); }
float n1(float x) { float i = floor(x), f = fract(x); f = f * f * (3.0 - 2.0 * f); return mix(h1(i), h1(i + 1.0), f); }

void fragment() {
	float p = COLOR.a, k = COLOR.r;
	float y = UV.x, h = UV.y, ay = abs(y);
	float fwd = exp(-pow(ay / 0.55, 2.0)) * smoothstep(1.0, 0.85, ay);
	float top = 0.55 + 0.45 * n1(y * 11.0 + 5.0);
	float rise = (1.0 - smoothstep(0.0, top, h)) * smoothstep(0.0, 0.08, h);
	float life = smoothstep(0.0, 0.1, p) * pow(1.0 - p, 1.5);
	vec3 c = vec3(0.86, 0.46, 0.13);
	ALBEDO = c * rise * fwd * life * k * 0.75 * hero_clear(VERTEX, VIEW_MATRIX, PROJECTION_MATRIX, VIEWPORT_SIZE);
}
