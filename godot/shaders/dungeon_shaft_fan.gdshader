// (den r16 B, R15f item 2) A shaft of daylight through a gap in the den's roof (src/World/DungeonLight.cs AddFan), after
// den_room.png: a fan of 3-5 soft rays from a bright gap up the shaft, brightest by the gap and gone before the floor, where
// the light lands as a soft pool. One quad in the shaft's plane turned to the camera; the pool is read off the depth (the
// ground's own place behind each pixel), so it lies on the floor whatever its bumps. Nothing over the pits.
// The colour: premultiplied, the rays add a cool light and take a share (ext) of what is behind them, so over the warm dirt
// the change stays neutral-cool (r15's plain add came out pink over the floor through the den's grade: delta hue 18-39).
shader_type spatial;
render_mode unshaded, blend_premul_alpha, depth_draw_never, depth_test_disabled, cull_disabled, shadows_disabled, fog_disabled;

uniform vec3 axis_up = vec3(0.0, 1.0, 0.0);   // up the shaft, world, unit (DungeonLight.Axis turned round)
uniform float src_h = 8.5;     // the gap, metres up the shaft from the foot
uniform float w_foot = 2.0;    // the fan's width where it lands (m)
uniform float w_src = 0.9;     // and at the gap
uniform float pool_r = 1.0;    // the pool's reach (m); a little longer along the lean
uniform vec4 rays[5];          // per ray: centre across the fan (0..1), half-width (share of the fan), gain, phase
uniform int ray_n = 4;
uniform vec3 tint : source_color = vec3(0.78, 0.86, 0.9);
uniform float strength = 0.3;  // the rays' light
uniform float ext = 0.3;       // the share of what is behind a ray's core it takes away (the rest of the change is the add)
uniform float gap_gain = 2.0;  // the gap against a ray's core
uniform float gap_ext = 0.5;
uniform vec3 pool_tint : source_color = vec3(0.86, 0.88, 0.9);
uniform float pool_strength = 0.16;
uniform float pool_ext = 0.15;
uniform float soft_depth = 1.2;   // the rays fade where they meet what is behind them (m)
uniform sampler2D hole_tex : hint_default_white, filter_linear, repeat_disable;   // HoleField as (f+4)/8 (DungeonLight)
uniform vec3 hole_map = vec3(0.0, 0.0, 0.0);   // x origin, z origin, 1/size (0: no field)
uniform sampler2D depth_tex : hint_depth_texture, repeat_disable, filter_nearest;

varying vec3 wpos;

float hash2(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float vnoise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash2(i), hash2(i + vec2(1.0, 0.0)), f.x), mix(hash2(i + vec2(0.0, 1.0)), hash2(i + vec2(1.0, 1.0)), f.x), f.y);
}

vec3 side_of(vec3 foot, vec3 cam) { return normalize(cross(axis_up, cam - foot) + vec3(1e-5, 0.0, 0.0)); }

void vertex() {
	// UV.x across (-1..1), UV.y along (0 below the foot, for the pool, to 1 above the gap); the model matrix is the foot.
	vec3 foot = MODEL_MATRIX[3].xyz;
	vec3 side = side_of(foot, INV_VIEW_MATRIX[3].xyz);
	float half_w = max(max(w_foot, w_src) * 0.5, pool_r) * 1.5 + 0.3;
	float v = mix(-pool_r * 1.7, src_h + 1.2, UV.y);
	wpos = foot + axis_up * v + side * (UV.x * half_w);
	VERTEX = wpos - foot;
}

void fragment() {
	vec3 foot = MODEL_MATRIX[3].xyz;
	vec3 side = side_of(foot, INV_VIEW_MATRIX[3].xyz);
	vec3 rel = wpos - foot;
	float v = dot(rel, axis_up), u = dot(rel, side);
	// what is behind this pixel: its depth and its place in the world
	float d = textureLod(depth_tex, SCREEN_UV, 0.0).r;
	vec4 sv = INV_PROJECTION_MATRIX * vec4(SCREEN_UV * 2.0 - 1.0, d, 1.0);
	vec3 sview = sv.xyz / sv.w;
	vec3 sw = (INV_VIEW_MATRIX * vec4(sview, 1.0)).xyz;
	float vis = smoothstep(0.0, soft_depth, (-sview.z) - (-VERTEX.z));   // 0 where the scene is in front of the shaft
	float pit = 1.0;
	if (hole_map.z > 0.0) pit = smoothstep(-0.2, 2.0, texture(hole_tex, (sw.xz - hole_map.xy) * hole_map.z).r * 8.0 - 4.0);
	// 1. the rays: bars across the fan, soft-edged, each breathing a little along its length; the fan widens to the floor
	float vn = v / src_h;
	float wv = mix(w_foot, w_src, clamp(vn, 0.0, 1.0));
	float un = u / wv + 0.5;
	float fan = 0.0;
	for (int k = 0; k < 5; k++) {
		if (k >= ray_n) break;
		vec4 r = rays[k];
		float prof = 1.0 - smoothstep(r.y * 0.45, r.y, abs(un - r.x));
		float n = 0.72 + 0.28 * vnoise(vec2(r.w * 17.0 + v * 0.45, r.w * 3.0 + TIME * 0.05));
		fan = max(fan, prof * r.z * n);
	}
	// brightest by the gap, half as bright midway, gone over the last stretch to the floor (the pool takes it there)
	float along = smoothstep(0.04, 0.5, vn) * mix(0.45, 1.0, smoothstep(0.25, 0.95, vn)) * (1.0 - smoothstep(0.96, 1.01, vn));
	float motes = 0.85 + 0.15 * vnoise(vec2(wpos.x * 1.3 + wpos.z, wpos.y * 0.5 - TIME * 0.15));
	float ray_a = fan * along * motes * vis * pit;
	// 2. the gap: a bright ragged slit where the rays start
	vec2 gq = vec2(u / (w_src * 0.62), (v - src_h) / 0.4);
	float ge = length(gq) * (0.82 + 0.36 * vnoise(vec2(atan(gq.y, gq.x) * 1.6 + 5.0, 2.0)));
	float gap = (1.0 - smoothstep(0.2, 1.0, ge)) * vis;
	gap *= gap;
	// 3. the pool: on the ground at the foot (not on her, not on a log: only what lies at the foot's own height)
	vec2 q = sw.xz - foot.xz;
	vec2 lean = normalize(axis_up.xz + vec2(1e-5, 0.0));
	float pa = dot(q, lean) / (pool_r * 1.15), pb = dot(q, vec2(-lean.y, lean.x)) / pool_r;
	float pd = length(vec2(pa, pb)) * (0.88 + 0.24 * vnoise(sw.xz * 1.6 + 7.0));
	float pool = (1.0 - smoothstep(0.25, 1.0, pd)) * (1.0 - smoothstep(0.3, 0.7, abs(sw.y - foot.y))) * pit;
	pool *= pool;
	ALBEDO = tint * strength * (ray_a + gap_gain * gap) + pool_tint * pool_strength * pool;
	ALPHA = clamp(ext * ray_a + gap_ext * gap + pool_ext * pool, 0.0, 1.0);
}
