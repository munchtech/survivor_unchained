// A story place's shut gate on the ground (View/ArenaEdge.Gate): the ring's
// lip drawn across a way. One white-hot thread wandering along it, broken in
// places, in a red breath; coals either side. UV: x metres along, y across
// (0..1, the thread at the middle).
shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;

uniform sampler2D noise_tex : filter_linear_mipmap, repeat_enable;
uniform vec3 ember : source_color = vec3(1.0, 0.35, 0.13);

vec2 hash2(vec2 p) {
	p = vec2(dot(p, vec2(127.1, 311.7)), dot(p, vec2(269.5, 183.3)));
	return fract(sin(p) * 43758.5453);
}

void fragment() {
	float x = UV.x;
	// Metres across from the middle (the strip is a metre and a half wide).
	float y = (UV.y - 0.5) * 1.5;
	float wander = (texture(noise_tex, vec2(x * 0.11, 0.3)).r - 0.5) * 0.5 + (texture(noise_tex, vec2(x * 0.37, 0.7)).g - 0.5) * 0.18;
	float d = abs(y - wander);
	float px = fwidth(y) * 0.8;
	float on = smoothstep(0.25, 0.5, texture(noise_tex, vec2(x * 0.09 + 0.5, 0.11)).b + 0.1);
	float core = 0.03 + 0.03 * texture(noise_tex, vec2(x * 0.5, 0.9)).r;
	float line = (1.0 - smoothstep(core * 0.5, core + px, d)) * on;
	float halo = exp(-d / 0.18) * (0.4 + 0.6 * on);
	// Coals either side of it, flickering.
	vec2 cell = floor(vec2(x, y) * 3.0);
	vec2 h = hash2(cell + 4.1);
	float cd = length(fract(vec2(x, y) * 3.0) - 0.3 - h * 0.4);
	float coal = step(0.82, hash2(cell + 9.7).x) * (1.0 - smoothstep(0.04, 0.09 + px * 3.0, cd / 3.0)) * exp(-abs(y) * 2.5);
	float breathe = 0.7 + 0.3 * sin(TIME * 1.1 + x * 0.7) * sin(TIME * 0.43 + x * 0.21);
	float flick = 0.6 + 0.4 * sin(TIME * (1.7 + h.x * 2.0) + h.y * 30.0);
	// Faded to nothing at the strip's long edges.
	float edge = 1.0 - smoothstep(0.55, 0.75, abs(y));
	vec3 white = mix(ember, vec3(1.0, 0.86, 0.6), 0.6);
	ALBEDO = (white * line * 2.6 + ember * (halo * 0.6 + coal * 1.6 * flick)) * breathe * edge;
}
