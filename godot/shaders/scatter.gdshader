// The small things lying on the ground (World/Scatter.cs): pebbles, small stones, fallen
// leaves and twigs along the roads, crumbs and weeds at a wall's foot. Vertex colour is
// the piece's own muted colour; COLOR.a is 0 for stone, 1 for leaf, twig and weed (a
// little rougher for the dead plant). Hoar frost settles on tops as the ground's does.
shader_type spatial;
render_mode diffuse_burley, cull_disabled;

#include "res://shaders/flare_world.gdshaderinc"

// Hoar frost on the tops (GroundPaint's exposure; Atmosphere's amount and thaw), as the ground's.
uniform sampler2D expo_tex : filter_linear, repeat_disable, hint_default_white;
global uniform vec4 ground_frost;
// The rime: the piece's colour lifted by frost_tone, greyed and cooled, never past frost_cap (look bible 1c).
uniform float frost_tone = 1.7;
uniform float frost_cap = 0.1;
uniform vec4 warm_at[4];
uniform float zone_size = 300.0;
// 1: each piece lit white (measure_d.py counts what shows at the close-up: --scatter-debug 1).
uniform int debug_view = 0;

void fragment() {
	vec3 alb = COLOR.rgb;
	vec3 wp = (INV_VIEW_MATRIX * vec4(VERTEX, 1.0)).xyz;
	if (ground_frost.x > 0.001) {
		vec2 ex = textureLod(expo_tex, (wp.xz + zone_size * 0.5) / zone_size, 0.0).rg;
		float cover = ground_frost.x * ex.r * (1.0 - ground_frost.y * ex.g * 0.92);
		for (int i = 0; i < 4; i++) if (warm_at[i].z > 0.0) cover *= smoothstep(warm_at[i].z, warm_at[i].z + 2.5, length(wp.xz - warm_at[i].xy));
		float up = normalize((INV_VIEW_MATRIX * vec4(NORMAL, 0.0)).xyz).y;
		float amount = cover * smoothstep(0.55, 0.9, up);
		float fl = min(dot(alb, vec3(0.2126, 0.7152, 0.0722)) * frost_tone, frost_cap);
		alb = mix(alb, vec3(0.86, 0.93, 1.0) * fl, 0.8 * amount);
	}
	ALBEDO = alb;
	ROUGHNESS = mix(0.82, 0.9, COLOR.a);
	SPECULAR = 0.3;
	if (debug_view == 1) { ALBEDO = vec3(0.0); EMISSION = vec3(50.0); }

	// The Flare's drain and frost (flare_world.gdshaderinc).
	if (flare_live()) {
		vec3 fl_a = ALBEDO; float fl_r = ROUGHNESS; vec3 fl_e = EMISSION;
		flare_prop(wp, NORMAL, INV_VIEW_MATRIX, fl_a, fl_r, fl_e);
		ALBEDO = fl_a; ROUGHNESS = fl_r; EMISSION = fl_e;
	}
}
