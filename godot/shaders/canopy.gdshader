// The wood's canopy over an arena (View/ArenaEdge.Canopy): never seen, only its
// shadow. A sheet high over the ground, cut by a slow world-space noise into
// crowns and the gaps between them, and drawn into the moon's shadow alone, so
// the moon comes down through it in pools that fall on the ground, the dead,
// her and the Pack alike, and sway a little with the wind. Clearings (the
// place's open sky, splat3 A) are cut out where their shadow would fall.
shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_opaque;

uniform sampler2D noise_tex : filter_linear_mipmap, repeat_enable;
uniform sampler2D open_tex : filter_linear, repeat_disable;
uniform float zone_size = 300.0;
// Metres from a point of the sheet to where its shadow lands (the moon's way, flat).
uniform vec2 moon_off = vec2(0.0);
// How much of the sky the crowns close (0 none, 1 all).
uniform float cover = 0.55;

varying vec3 w_pos;

void vertex() {
	w_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec2 p = w_pos.xz;
	vec2 sway = vec2(sin(TIME * 0.35 + p.y * 0.05), cos(TIME * 0.29 + p.x * 0.05)) * 0.25;
	// Crowns a few metres across, their edges torn into leaf clusters. (No finer: clusters
	// under a metre are finer than the moon's shadow map draws, and the pools' edges came
	// out stepped. Their soft rim is the moon's own breadth, Atmosphere.Set.)
	float crowns = texture(noise_tex, (p + sway) * 0.045).g * 0.68 + texture(noise_tex, (p + sway * 2.0) * 0.16 + 0.31).b * 0.32;
	float open = texture(open_tex, (p + moon_off + zone_size * 0.5) / zone_size).a;
	// (The noise's sum sits about a half, spread narrowly: cover is mapped onto that spread.)
	float leaf = step(0.62 - cover * 0.24, crowns) * (1.0 - step(0.5, open));
	ALBEDO = vec3(0.0);
	ALPHA = leaf;
	ALPHA_SCISSOR_THRESHOLD = 0.5;
}
