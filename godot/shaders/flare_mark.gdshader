shader_type spatial;
// The marks (H7; Fx/Flare/FlareMarksView.cs): light on the ground (LOOK_BIBLE row 8), soft pools of light, never a vector line or a stroke;
// flare_mark.gdshaderinc. One pass, premultiplied: a mark's light adds while its alpha (its light over the cap) lays the
// ground under it back by as much, so overlapping pools converge on the cap and never stack to white; the soft shade round
// a pool is alpha alone, tied to the same envelope as its light (a fade takes it with the light).
// (r2: depth-tested, the quad lifted the data's "above" over HeightAt (the arena ground stands a little above it): a pool's
// heart is under its foe, and drawn over the body it laid the body back to a flat disc of light; now the body hides it)
render_mode unshaded, blend_premul_alpha, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;
#include "res://shaders/flare_mark.gdshaderinc"

void fragment() {
	vec3 m = flare_mark_at(UV);
	float g = max(mk_col.r, max(mk_col.g, mk_col.b));
	vec3 hue = g > 1e-4 ? mk_col.rgb / g : vec3(0.0);
	// The heart leans toward her ember's warmth and white (the light's hot middle), the pool keeps the school's hue.
	vec3 heart_hue = mix(mix(hue, vec3(1.0), 0.35), warm_hue, warm);
	vec3 light = (hue * m.x + heart_hue * m.y) * g;
	ALBEDO = light;
	float lum = max(light.r, max(light.g, light.b));
	ALPHA = clamp(lum / max(cap, 1e-3) + mk_col.a * m.z, 0.0, 1.0);
}
