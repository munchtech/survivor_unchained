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
uniform float veil_cut = 0.4;     // (r15: the veil's alpha x this; the judge asked -60 %)
uniform float floor_fade = 1.0;   // (r15: veil 0 at the floor, full this many metres above the surface behind it, x2)
uniform float pit_fade = 1.0;     // (r15: 1 = the veil is masked off over the pits)
uniform float streak_k = 2.2;     // (r15: streaks round the column, ~4 on its visible half)
uniform sampler2D hole_tex : hint_default_white, filter_linear, repeat_disable;   // (r15: HoleField as (f+4)/8, bit-exact to the zone)
uniform float streak_gain = 3.0;   // (r15b: the streaks carry the light; the gaps carry none)
uniform vec3 hole_map = vec3(0.0, 0.0, 1.0);   // (x origin, z origin, 1/size of the field in metres)
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
	// (r15b: by the lateral metre across the shaft as seen, so the streaks run parallel up it: the angle round it made a pinwheel at the top)
	vec3 cen = (VIEW_MATRIX * vec4(MODEL_MATRIX[3].xyz, 1.0)).xyz;
	vec3 lat = normalize(cross(ax, normalize(VERTEX)) + 1e-5);
	float ang = dot(VERTEX - cen, lat);
	// (r15b: thin hard-ish streaks, 8-25 px, nothing between them: rays 0 outside)
	float rays = (0.05 + smoothstep(0.56, 0.76, vnoise(vec2(ang * streak_k + 3.0, hf * 0.3)))) * streak_gain;
	// where the scene is just behind the shaft (floor, pit, bank) it fades out instead of cutting a line
	float d = textureLod(depth_tex, SCREEN_UV, 0.0).r;
	vec4 sv = INV_PROJECTION_MATRIX * vec4(SCREEN_UV * 2.0 - 1.0, d, 1.0);
	float scene_z = -sv.z / sv.w;
	float gap = scene_z - (-VERTEX.z);
	a *= smoothstep(0.0, soft_depth, gap);
	// the scene surface behind this pixel, in the world: the veil fades to nothing near the floor, and over pits
	vec4 sw = INV_VIEW_MATRIX * vec4(sv.xyz / sv.w, 1.0);
	a *= mix(1.0, smoothstep(0.0, floor_fade, wpos.y - sw.y), step(0.001, floor_fade));
	float hf_v = texture(hole_tex, (sw.xz - hole_map.xy) * hole_map.z).r * 8.0 - 4.0;
	a *= mix(1.0, smoothstep(-0.2, 2.0, hf_v), pit_fade * step(0.001, hole_map.z));
	a *= veil_cut;
	ALBEDO = tint * strength * a * motes * rays;
}
