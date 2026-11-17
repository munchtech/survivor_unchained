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
// (den r16 B2) the lair's painted hollows are no holes (DungeonDress.DenHollows): masked by circle, x, z, radius (m)
uniform vec4 holl[8];
uniform int holl_n = 0;
uniform float haze = 0.3;     // (den r16 B2) the fan's soft glow between its rays, against a ray's core
uniform vec3 gap_tint : source_color = vec3(0.93, 0.92, 0.89);   // (den r16 B2) the gap near-white, not the rays' cool
// (den r17 L, R16 item 2) 1: the rays run down to the foot and end in its pool (DungeonLight --den-shaft-foot); 0: r16, gone
// over the lower half (each pool sat ~250 px below its shaft's end)
uniform float foot_k = 0.0;
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
	for (int k = 0; k < 8; k++) { if (k >= holl_n) break; pit *= smoothstep(holl[k].z + 0.2, holl[k].z + 1.2, distance(sw.xz, holl[k].xy)); }
	// 1. the rays: bars across the fan, soft-edged, each breathing a little along its length; the fan widens to the floor
	float vn = v / src_h;
	float wv = mix(w_foot, w_src, clamp(vn, 0.0, 1.0));
	float un = u / wv + 0.5;
	// (den r16 B2: B's flat bars read as ruled stripes) each ray a soft bell whose edge and width wander along it, its light
	// broken by dust; a faint haze fills the fan between the rays, and fine filaments run down the whole fan
	float fan = 0.0;
	for (int k = 0; k < 5; k++) {
		if (k >= ray_n) break;
		vec4 r = rays[k];
		float hw = r.y * (0.75 + 0.5 * vnoise(vec2(r.w * 13.0 + 4.0, v * 0.55)));
		float d = (un - r.x - (vnoise(vec2(r.w * 31.0, v * 0.8)) - 0.5) * 0.5 * r.y) / hw;
		float n = 0.45 + 0.55 * vnoise(vec2(r.w * 17.0 + v * 0.7, r.w * 3.0 + TIME * 0.05));
		fan += exp(-2.2 * d * d) * r.z * n;
	}
	float env = smoothstep(-0.02, 0.2, un) * (1.0 - smoothstep(0.8, 1.02, un));
	float fil = 0.7 + 0.3 * vnoise(vec2(un * 26.0, v * 0.18 + 5.0));
	fan = env * fil * (haze + (1.0 - haze) * min(fan, 1.1));
	// brightest by the gap, half as bright midway, gone over the last stretch to the floor (the pool takes it there)
	float along = smoothstep(0.04, 0.5, vn) * mix(0.45, 1.0, smoothstep(0.25, 0.95, vn)) * (1.0 - smoothstep(0.96, 1.01, vn));
	float along_f = smoothstep(-0.01, 0.06, vn) * mix(0.6, 1.0, smoothstep(0.15, 0.95, vn)) * (1.0 - smoothstep(0.96, 1.01, vn));
	along = mix(along, along_f, foot_k);
	float motes = 0.85 + 0.15 * vnoise(vec2(wpos.x * 1.3 + wpos.z, wpos.y * 0.5 - TIME * 0.15));
	float ray_a = fan * along * motes * vis * pit;
	// 2. the gap: a bright ragged slit where the rays start
	// (den r16 B2: a round cyan blob) a long soft slit across the fan's top, ragged, broken by the roots' dark
	vec2 gq = vec2(u / (w_src * 0.85), (v - src_h) / 0.22);
	float ge = length(gq) * (0.8 + 0.4 * vnoise(vec2(u * 6.0 + 5.0, v * 3.0)));
	float gap = (1.0 - smoothstep(0.15, 1.0, ge)) * vis * pit * (0.55 + 0.45 * vnoise(vec2(u * 9.0, 7.0)));
	gap *= gap;
	// 3. the pool: on the ground at the foot (not on her, not on a log: only what lies at the foot's own height)
	vec2 q = sw.xz - foot.xz;
	vec2 lean = normalize(axis_up.xz + vec2(1e-5, 0.0));
	float pa = dot(q, lean) / (pool_r * 1.15), pb = dot(q, vec2(-lean.y, lean.x)) / pool_r;
	float pd = length(vec2(pa, pb)) * (0.88 + 0.24 * vnoise(sw.xz * 1.6 + 7.0));
	float pool = (1.0 - smoothstep(0.25, 1.0, pd)) * (1.0 - smoothstep(0.3, 0.7, abs(sw.y - foot.y))) * pit;
	pool *= pool;
	ALBEDO = tint * strength * ray_a + gap_tint * strength * gap_gain * gap + pool_tint * pool_strength * pool;
	ALPHA = clamp(ext * ray_a + gap_ext * gap + pool_ext * pool, 0.0, 1.0);
}
