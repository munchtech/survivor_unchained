// Our own grass (E4h): a painted clump card (3-5 blades, tools/assets/env_trees.py's grass atlas) per cell
// of a wrapped grid (World/Grass.cs Own), facing the camera (turned up to `yaw` off it, flipped at random),
// so the play camera sees each clump side-on: a tuft leaning its own way, never a star. Which cells grow
// is drifts: the ground's clump field (terrain.gdshader's noise) between drift.x and drift.y, so the
// meadow comes in irregular drifts and bare patches, not an even scatter; then the ground's masks (the
// road, setts, mud, crowns, fire pits). The root takes the ground's own colour, darkened (`base`), so the
// clump sits in the ground; the tips the atlas's painted olive to blue-green, bluer in the lows and by
// night (`night`). Wind, her pushing through, frost and the Flare as the kit grass (grass.gdshader).
shader_type spatial;
render_mode cull_disabled, diffuse_burley, world_vertex_coords;

#include "res://shaders/flare_world.gdshaderinc"

uniform sampler2D atlas : source_color, filter_linear_mipmap_anisotropic, repeat_disable;
uniform sampler2D noise_tex : filter_linear_mipmap, repeat_enable;
uniform sampler2D splat : filter_linear_mipmap, repeat_disable;
uniform sampler2D paint_mask : filter_linear, repeat_disable, hint_default_black;
uniform sampler2DArray g_alb : source_color, filter_linear_mipmap, repeat_enable;
uniform float meadow_scale = 0.5;
uniform float zone_size = 290.0;
uniform float leaves = 0.3;
uniform float heal = 0.0;
uniform float density = 1.0;
// (flora_species.json "grass": a kind's card, drifts and colour)
uniform vec2 card = vec2(0.55, 0.5);
uniform float yaw = 35.0;
// (the card's top leaned away from the camera by this much of its height, so it faces the steep play camera: the clump, not its edge)
uniform float tilt = 0.35;
uniform vec2 drift = vec2(0.4, 0.6);
uniform float flower_share = 0.04;
uniform float flower_cells = 2.0;
uniform vec3 warm = vec3(1.04, 1.0, 0.86);
uniform vec3 cool = vec3(0.88, 1.0, 1.0);
uniform vec3 night_tint = vec3(0.8, 1.0, 1.04);
uniform float base = 0.6;
uniform float clear = 3.5;
// (the tips' colour held toward their grey: muted, never lime)
uniform float sat = 0.75;
uniform float tone = 1.0;
uniform vec3 wind = vec3(1.0, 0.35, 1.0);
uniform vec4 pusher = vec4(0.0, 0.0, 0.0, 0.0);
uniform vec2 centre = vec2(0.0);
uniform float span = 80.0;
uniform sampler2D heights : filter_linear, repeat_disable;
uniform float h_size = 290.0;
uniform float h_res = 256.0;
uniform sampler2D expo_tex : filter_linear, repeat_disable, hint_default_white;
global uniform vec4 ground_frost;
global uniform vec4 flora_light;
uniform float frost_tone = 1.7;
uniform float frost_cap = 0.1;
uniform vec4 warm_at[4];
uniform float meadow_amt = 1.0;
uniform int debug_view = 0;
uniform vec4 bare_at[4];

varying float v_t;
varying vec3 v_tint;
varying vec3 v_ground;
varying float v_frost;
varying vec2 v_cell;
varying vec3 v_wp;

float gh(vec2 p) { vec3 p3 = fract(vec3(p.xyx) * 0.1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }

float ground_at(vec2 p) {
	vec2 f = clamp((p + h_size * 0.5) / h_size * (h_res - 1.0), vec2(0.0), vec2(h_res - 1.0));
	return textureLod(heights, (f + 0.5) / h_res, 0.0).r;
}

void vertex() {
	vec3 root = MODEL_MATRIX[3].xyz;
	vec3 off = VERTEX - root;
	vec2 wp = root.xz + span * round((centre - root.xz) / span);
	float edge = 1.0 - smoothstep(span * 0.36, span * 0.5, length(wp - centre));
	float h1 = gh(wp * 7.1), h3 = gh(wp * 3.3 + 11.0), h4 = gh(wp * 5.7 + 4.0), h5 = gh(wp * 9.3 + 2.0), h6 = gh(wp * 4.1 + 7.0);
	vec2 zuv = (wp + zone_size * 0.5) / zone_size;
	vec4 sp = texture(splat, zuv);
	sp.b *= 1.0 - heal * 0.85;
	vec4 nz = texture(noise_tex, wp * 0.035);
	// None on setts, mud or blight; over trodden earth it thins (grass.gdshader's masks).
	float hard = max(sp.g, max(sp.b, sp.a));
	float dens = (1.0 - smoothstep(0.12, 0.45, hard + (nz.g - 0.5) * 0.35))
		* (1.0 - smoothstep(0.15, 0.8, sp.r + (nz.g - 0.5) * 0.35) * 0.85);
	// Drifts: the ground's clump field (terrain.gdshader, the same noise), cut between drift.x and drift.y, so a
	// drift is grass to its heart and thins to single clumps at its edge, with bare ground between; the ground's
	// bare patches bare.
	vec4 nF = texture(noise_tex, wp * 0.29 + 0.71), nM = texture(noise_tex, wp * 0.061 + 0.37);
	vec4 nC = texture(noise_tex, wp * 0.0213 + 0.13), nL = texture(noise_tex, wp * 0.011);
	float bare_p = smoothstep(0.62, 0.76, nM.b * 0.45 + nC.b * 0.55) * smoothstep(0.45, 0.68, nL.b) * meadow_amt;
	// (half the ground's own clump field, so a drift lies on the ground's darker green hearts, half a field with more
	// contrast, 4 m blobs and 6 m swells; lo-hi 0.46-0.54 covers 48% of an open meadow, 39% bare: env10's drift_sim.py)
	float clump = (nM.r * 0.45 + nM.g * 0.35 + nF.r * 0.2) * 0.5 + (nM.r * 0.55 + nC.g * 0.3 + nF.r * 0.15) * 0.5;
	float cover = smoothstep(drift.x, drift.y, clump) * (1.0 - bare_p);
	dens *= mix(1.0, cover, meadow_amt);
	vec4 pm = textureLod(paint_mask, zuv, 0.0);
	dens *= max(1.0 - smoothstep(0.5, 0.75, pm.r), smoothstep(0.86, 0.97, pm.r) * 0.6) * (1.0 - smoothstep(0.1, 0.4, pm.g));
	float leafy = smoothstep(0.42, 0.78, nL.g * 0.7 + nM.a * 0.3 + leaves - 0.5);
	dens *= 1.0 - leafy * 0.5;
	dens *= mix(1.0, 0.3, smoothstep(0.82, 0.42, textureLod(expo_tex, zuv, 0.0).r));
	float keep = step(h3, dens * density * edge);
	// (a fire's pit bare, the camp round it thinning out to `clear` times its radius)
	for (int i = 0; i < 4; i++) keep *= step(h4, smoothstep(bare_at[i].z, bare_at[i].z * clear, length(wp - bare_at[i].xy)));
	// Size: smaller at a drift's edge, each clump its own.
	float sz = mix(0.55, 1.2, smoothstep(0.0, 0.8, cover)) * (0.7 + 0.6 * gh(wp * 6.3 + 1.0)) * keep;
	// Facing the camera (its forward, flattened), turned up to `yaw` off it; half of them mirrored.
	vec3 fwd = -INV_VIEW_MATRIX[2].xyz;
	vec2 f = normalize(-fwd.xz + vec2(1e-4, 0.0));
	// (turned by a slow field and a little each: neighbours lean alike, as a drift combed by the wind does)
	float ya = radians(yaw) * ((nF.g * 2.0 - 1.0) * 1.2 + (h1 * 2.0 - 1.0) * 0.4);
	f = vec2(f.x * cos(ya) - f.y * sin(ya), f.x * sin(ya) + f.y * cos(ya));
	vec2 r = vec2(-f.y, f.x) * (h5 * 0.6 + nF.b * 0.8 < 0.7 ? 1.0 : -1.0);
	float t = clamp(off.y, 0.0, 1.0);
	v_t = t;
	float asp = 0.8 + 0.4 * gh(wp * 8.7 + 3.0);
	vec3 p = vec3(r.x, 0.0, r.y) * off.x * card.x * sz * asp + vec3(0.0, off.y * card.y * sz / asp, 0.0);
	p.xz -= f * off.y * card.y * sz * tilt;
	// (its foot a hair behind, toward the camera's far side, so it stands in the ground, not on it)
	p.xz -= f * 0.03 * sz;
	// Wind: a slow travelling swell and gusts; the survivor parts it.
	float swell = sin(TIME * 1.6 + dot(wp, wind.xy) * 0.55 + nz.a * 5.0) * 0.5 + 0.5;
	float gust = texture(noise_tex, wp * 0.018 - TIME * vec2(0.035, 0.012)).r;
	vec2 bend = normalize(wind.xy) * (swell * 0.3 + gust * gust * 0.9) * wind.z;
	vec2 a = wp - pusher.xy;
	float pd = length(a);
	bend += (pd > 0.001 ? a / pd : vec2(0.0)) * (1.0 - smoothstep(0.0, pusher.z, pd)) * pusher.w * 1.6;
	float bl = min(length(bend), 1.4);
	bend = bl > 0.0 ? normalize(bend) * bl : vec2(0.0);
	float tt = t * t;
	p.xz += bend * tt * card.y * sz * 0.45;
	p.y -= bl * tt * card.y * sz * 0.15;
	VERTEX = vec3(wp.x, ground_at(wp) - 0.02, wp.y) + p;
	v_wp = VERTEX;
	NORMAL = vec3(0.0, 1.0, 0.0);
	// The atlas cell: one of the grass clumps, or (flower_share of them, in a drift's heart) a flowering one.
	float nc = 8.0 - flower_cells;
	float c = h6 < flower_share * smoothstep(0.3, 0.8, cover) ? nc + floor(h4 * flower_cells * 0.999) : floor(gh(wp * 2.7 + 5.0) * nc * 0.999);
	v_cell = vec2(mod(c, 4.0), floor(c / 4.0));
	// The ground under it (its meadow's colour, as grass.gdshader), for the root.
	vec3 g = textureLod(g_alb, vec3(wp * meadow_scale, 0.0), 5.0).rgb;
	g *= 0.8 + 0.2 * nL.r;
	v_ground = g;
	// The tips: olive on the rises, blue-green in the lows (the ground's lie), each clump its own tone.
	vec4 ex4 = textureLod(expo_tex, zuv, 0.0);
	float low = ex4.b * 2.0 - 1.0;
	float lush = clamp(smoothstep(-0.1, 0.5, low + (nM.r - 0.5) * 0.4), 0.0, 1.0);
	v_tint = mix(warm, cool, lush) * tone * (0.8 + 0.3 * gh(wp * 3.9 + 8.0));
	v_frost = 0.0;
	if (ground_frost.x > 0.001) {
		v_frost = ground_frost.x * ex4.r * (1.0 - ground_frost.y * ex4.g * 0.92) * (0.6 + 0.4 * h1);
		for (int i = 0; i < 4; i++) if (warm_at[i].z > 0.0) v_frost *= smoothstep(warm_at[i].z, warm_at[i].z + 2.5, length(wp - warm_at[i].xy));
	}
}

void fragment() {
	float t = clamp(v_t, 0.0, 1.0);
	vec2 uv = (v_cell + vec2(UV.x, 1.0 - UV.y)) / vec2(4.0, 2.0);
	vec4 tx = texture(atlas, uv);
	vec3 gb = tx.rgb * v_tint;
	gb = mix(vec3(dot(gb, vec3(0.2126, 0.7152, 0.0722))), gb, sat);
	// The root in the ground: the ground's colour, darkened, up the first part of the clump.
	gb = mix(v_ground * base, gb, smoothstep(0.0, 0.3, t));
	// By night the moonlit tips blue-green.
	gb *= mix(vec3(1.0), night_tint, flora_light.x);
	// (a flower's pale head no brighter than the moonlit road: dimmed by night)
	gb *= 1.0 - 0.5 * flora_light.x * smoothstep(0.2, 0.4, dot(tx.rgb, vec3(0.2126, 0.7152, 0.0722)));
	float fr = v_frost * smoothstep(mix(1.0, 0.35, v_frost), 1.0, t);
	float fl = min(dot(gb, vec3(0.2126, 0.7152, 0.0722)) * frost_tone, frost_cap);
	gb = mix(gb, vec3(0.86, 0.93, 1.0) * fl, fr * 0.8);
	ALBEDO = debug_view == 4 ? vec3(fr * 0.8, 0.0, 1.0 - fr * 0.8) : gb;
	// (the blades' coverage kept down the mips: thin blades fade out of an averaged alpha, so it is raised with the mip
	// the texel footprint picks)
	vec2 ts = vec2(textureSize(atlas, 0));
	vec2 dx = dFdx(uv * ts), dy = dFdy(uv * ts);
	float lod = max(0.5 * log2(max(dot(dx, dx), dot(dy, dy))), 0.0);
	ALPHA = tx.a * (1.0 + lod * 0.35);
	ALPHA_SCISSOR_THRESHOLD = 0.5;
	NORMAL = normalize((VIEW_MATRIX * vec4(0.0, 1.0, 0.0, 0.0)).xyz);
	ROUGHNESS = 0.92;
	SPECULAR = 0.2;
	BACKLIGHT = gb * 0.25;
	if (flare_live()) {
		vec3 fl_a = ALBEDO; float fl_r = ROUGHNESS; vec3 fl_e = EMISSION;
		flare_blade(v_wp, t, fl_a, fl_r, fl_e);
		ALBEDO = fl_a; ROUGHNESS = fl_r; EMISSION = fl_e;
	}
}
