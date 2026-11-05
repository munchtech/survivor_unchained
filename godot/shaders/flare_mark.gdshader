shader_type spatial;
// The marks (H7; Fx/Flare/FlareMarksView.cs): light on the ground (LOOK_BIBLE row 8), soft pools of light, never a vector line or a stroke;
// flare_mark.gdshaderinc. r2 (the lead's f2e shoot: the pools merged into one blown-out yellow sheet over the pack, 1.6x the
// fight's mean in the stop): a pool is LIGHT on what lies under it, not paint over it. It reads the opaque frame under it
// (the graded ground, the feet) and lifts it by its light in the school's hue (x what is there, as the band and the peak
// light the ground x its albedo), plus a faint floor so a pool still shows on near-black ground. One pass, premultiplied:
// a pool's alpha is its light over the cap and its colour the ground lit at the cap, so overlapping pools converge on
// "the ground x (1 + cap)" and never on white; a pack reads as many lit bodies on a lit floor. The soft shade round a
// pool (by day) is alpha alone, tied to the same envelope (a fade takes it with the light).
// (r2: depth-tested, the quad lifted the data's "above" over HeightAt: a pool's heart is under its foe and the body hides it)
render_mode unshaded, blend_premul_alpha, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;
#include "res://shaders/flare_mark.gdshaderinc"
uniform sampler2D under_tex : hint_screen_texture, filter_linear, repeat_disable;
uniform float main_cap = 2.0;       // the Main's cap x the pools' (marks.main)
uniform float floor_light = 0.012;   // the light a pool adds at the cap where the ground is black (linear)

void fragment() {
	vec3 m = flare_mark_at(UV);
	float g = max(mk_col.r, max(mk_col.g, mk_col.b));
	vec3 hue = g > 1e-4 ? mk_col.rgb / g : vec3(0.0);
	// The heart leans toward her ember's warmth (the light's hot middle), the pool keeps the school's hue.
	vec3 heart_hue = mix(mix(hue, vec3(1.0), 0.25), warm_hue, warm);
	float k = (m.x + m.y) * g;                       // the pool's lift here (x the ground)
	vec3 h = (hue * m.x + heart_hue * m.y) / max(m.x + m.y, 1e-4);
	// (the Main converges on its own cap, main_cap x the pools': twice the size AND the value, with its core over it)
	float c = max(cap, 1e-3) * (mk.x > 0.5 && mk.x < 1.5 ? main_cap : 1.0);
	float a = clamp(k / c, 0.0, 1.0);
	vec3 under = textureLod(under_tex, SCREEN_UV, 0.0).rgb;
	vec3 lit = under * (1.0 + c * h) + floor_light * c * h;
	float ds = mk_col.a * m.z * (1.0 - a);
	ALBEDO = lit * a;
	ALPHA = clamp(a + ds, 0.0, 1.0);
}
