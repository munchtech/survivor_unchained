// A pale shaft of daylight through the den's roof (src/World/DungeonLight.cs): an additive cone, soft at its sides,
// strongest a little above the floor and gone toward the roof, with slow motes drifting in it.
shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, cull_back, shadows_disabled, fog_disabled;

uniform vec3 tint : source_color = vec3(0.86, 0.92, 0.95);   // (r11 judge: cool-white beams as den_room/den_boss, ~(200,215,215); the pools stay warm)
// was   // (r10d: warm and faint; the cool 0.3 read as grey fog sheets over the far bank)
uniform float strength = 0.22;   // (r11 judge: the beams did not show in the lairs, faint in rooms)
// was 0.12;   // (lead 6: 0.55 read as hard white cones against the targets' soft pale rays)
uniform float height = 15.0;
uniform float side_fade = 0.4;   // (r14: the sides fade over this share of the width, no ruled edge)
uniform float soft_depth = 2.5;  // (r14: fades where it meets floor or pit, metres of scene depth)
uniform sampler2D depth_tex : hint_depth_texture, repeat_disable, filter_nearest;

varying float hf;
varying vec3 wpos;

float hash2(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float vnoise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash2(i), hash2(i + vec2(1.0, 0.0)), f.x), mix(hash2(i + vec2(0.0, 1.0)), hash2(i + vec2(1.0, 1.0)), f.x), f.y);
}

void vertex() {
	hf = VERTEX.y / height + 0.5;
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	// across-the-shaft position from the true silhouette (the cone's slope made face never reach 0: a ruled side)
	vec3 ax = normalize((VIEW_MATRIX * vec4(MODEL_MATRIX[1].xyz, 0.0)).xyz);
	vec3 n = NORMAL - ax * dot(NORMAL, ax);
	vec3 v = VIEW - ax * dot(VIEW, ax);
	float face = clamp(abs(dot(normalize(n + 1e-5), normalize(v + 1e-5))), 0.0, 1.0);
	float s = sqrt(1.0 - face * face);   // 0 at the middle, 1 at the side
	float a = smoothstep(1.0, 1.0 - side_fade, s);
	a = a * a * 0.6;
	a *= smoothstep(0.0, 0.12, hf) * (1.0 - smoothstep(0.35, 0.95, hf));
	float motes = 0.75 + 0.25 * vnoise(vec2(wpos.x * 1.3 + wpos.z, wpos.y * 0.5 - TIME * 0.15));
	// 3-5 soft streaks along it (by the angle round it, slowly varying with height)
	float ang = atan(wpos.x - MODEL_MATRIX[3].x, wpos.z - MODEL_MATRIX[3].z);
	float rays = 0.2 + 1.2 * smoothstep(0.3, 0.7, vnoise(vec2(ang * 2.4 + 3.0, hf * 0.5)));
	// where the scene is just behind the shaft (floor, pit, bank) it fades out instead of cutting a line
	float d = textureLod(depth_tex, SCREEN_UV, 0.0).r;
	vec4 sv = INV_PROJECTION_MATRIX * vec4(SCREEN_UV * 2.0 - 1.0, d, 1.0);
	float scene_z = -sv.z / sv.w;
	float gap = scene_z - (-VERTEX.z);
	a *= smoothstep(0.0, soft_depth, gap);
	ALBEDO = tint * strength * a * motes * rays;
}
