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
// (and by night held further: a lamp's pool lights the clumps, never a glowing cyan)
uniform float night_sat = 0.55;
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

// (the warmest hue a sunlit tip may take under a low sun, sRGB degrees, as the trees' hue_floor: sun x olive went yellow)
uniform float hue_floor = 95.0;
// (E5, judge E4i: the key's light on a clump's upper part warmed toward olive by this, by day and under a low sun, not the
// moon nor a lamp: a drift in sun takes the lit ground's warmth, not pasted on; its shade keeps the sky's blue-green)
uniform vec3 sun_tip = vec3(1.0);
// (E5b, judge E5: the key's light on the whole blade, root to tip, by day and dawn: its sunlit body turned from teal toward
// green (hue ~90-100), its shade and the night untouched)
uniform vec3 sun_body = vec3(1.0);
// (each clump's card size within +-size_var of its own, half white noise and half a 3 m field, so a dense drift is not stamped)
uniform float size_var = 0.3;
// (lf3b, judge lf2 #4: the clumps read as one stamp on an even grid) 0 each: as before. cluster: how far each clump is
// drawn toward the heart of its own cluster (one a cluster_cell m square, its heart jittered), so they stand in tufts of
// three to six with ground between; cluster_gap thins the clumps out toward a cluster's rim; big_share/small_share the
// share of clumps 1.3-1.65x and 0.5-0.78x; tilt_var each clump's lean within +-tilt_var of tilt; trod: bare trodden
// patches (a 7-8 m field, about trod_share of the ground), their rims thin and short.
uniform float cluster = 0.0;
uniform float cluster_cell = 1.6;
uniform float cluster_gap = 0.0;
uniform float big_share = 0.0;
uniform float small_share = 0.0;
uniform float tilt_var = 0.0;
uniform float trod = 0.0;
uniform float trod_share = 0.12;
// (lf3b r2: a lattice of clusters read as a new grid of tufts) fine: a 1.5-2 m noise field thins the drift in places
// (to 1 - fine), so the tufts gather unevenly, with no cell to repeat
uniform float fine = 0.0;
// (Low Ford lf5p, judge lf4 #9: one tuft at one value everywhere; #7: by dawn the tufts' teal ignored the warm key)
// dry_share of the clumps (in patches, a field of a few metres) a second kind, dry and straw-tipped (dry_tint over the
// green); val_spread: each clump's and each patch's value plus or minus this; day_cool: the share of the lows' cool tint
// kept by day and dawn (by night whole). 0, 0, 1: as before.
uniform float dry_share = 0.0;
uniform vec3 dry_tint = vec3(1.35, 1.1, 0.62);
uniform float val_spread = 0.0;
uniform float day_cool = 1.0;
// ...and the blades by day and dawn times day_warm (by night untouched); 1: as before.
uniform vec3 day_warm = vec3(1.0);

float hue_of(vec3 c) {
	float mx = max(c.r, max(c.g, c.b)), mn = min(c.r, min(c.g, c.b)), d = mx - mn;
	if (d < 1e-5) return 120.0;
	float h = mx == c.r ? mod((c.g - c.b) / d, 6.0) : mx == c.g ? (c.b - c.r) / d + 2.0 : (c.r - c.g) / d + 4.0;
	return h * 60.0;
}

vec3 hue_turn(vec3 c, float a) {
	vec3 k = vec3(0.57735);
	float ca = cos(a);
	return c * ca + cross(k, c) * sin(a) + k * dot(k, c) * (1.0 - ca);
}

float gh(vec2 p) { vec3 p3 = fract(vec3(p.xyx) * 0.1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }

float ground_at(vec2 p) {
	vec2 f = clamp((p + h_size * 0.5) / h_size * (h_res - 1.0), vec2(0.0), vec2(h_res - 1.0));
	return textureLod(heights, (f + 0.5) / h_res, 0.0).r;
}

void vertex() {
	vec3 root = MODEL_MATRIX[3].xyz;
	vec3 off = VERTEX - root;
	vec2 wp = root.xz + span * round((centre - root.xz) / span);
	float cl_r = 0.0;
	if (cluster > 0.0) {
		vec2 cc = (floor(wp / cluster_cell) + 0.5) * cluster_cell;
		cc += (vec2(gh(cc * 1.37 + 3.1), gh(cc * 2.11 + 7.7)) - 0.5) * cluster_cell * 0.7;
		vec2 dv = cc - wp;
		cl_r = length(dv) / cluster_cell;
		wp += dv * cluster * (0.55 + 0.45 * gh(wp * 4.9 + 2.0));
	}
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
	float tr = 0.0;
	if (trod > 0.0) {
		float tn = texture(noise_tex, wp * 0.13 + 0.53).r * 0.7 + nF.a * 0.3;
		tr = smoothstep(0.66 - trod_share * 0.9, 0.74 - trod_share * 0.9, tn) * trod;
	}
	if (cluster > 0.0) dens *= 1.0 - cluster_gap * smoothstep(0.32, 0.62, cl_r);
	if (fine > 0.0) {
		vec4 nf2 = texture(noise_tex, wp * 0.53 + 0.21);
		dens *= 1.0 - fine * smoothstep(0.62, 0.38, nf2.r * 0.65 + nf2.g * 0.35);
	}
	float keep = step(h3, dens * density * edge * (1.0 - tr));
	// (a fire's pit bare, the camp round it thinning out to `clear` times its radius; a prop's patch (OwnProps "bare")
	// thins out to its own w times its radius)
	for (int i = 0; i < 4; i++) keep *= step(h4, smoothstep(bare_at[i].z, bare_at[i].z * (bare_at[i].w > 0.0 ? bare_at[i].w : clear), length(wp - bare_at[i].xy)));
	// Size: smaller at a drift's edge, each clump its own.
	float sz = mix(0.5, 1.15, smoothstep(0.0, 0.8, cover)) * (1.0 + size_var * (2.0 * (0.6 * gh(wp * 6.3 + 1.0) + 0.4 * nF.a) - 1.0) * 1.3) * keep;
	{
		float hb = gh(wp * 6.9 + 13.0);
		sz *= hb < big_share ? mix(1.3, 1.65, hb / max(big_share, 1e-4)) : (hb > 1.0 - small_share ? mix(0.78, 0.5, (hb - 1.0 + small_share) / max(small_share, 1e-4)) : 1.0);
		sz *= 1.0 - 0.45 * tr;
		if (cluster > 0.0) sz *= mix(1.0, 1.18 - 0.5 * cl_r, cluster);
	}
	// Facing the camera (its forward, flattened), turned up to `yaw` off it; half of them mirrored.
	vec3 fwd = -INV_VIEW_MATRIX[2].xyz;
	vec2 f = normalize(-fwd.xz + vec2(1e-4, 0.0));
	// (turned by a slow field and a little each: neighbours lean alike, as a drift combed by the wind does)
	float ya = radians(yaw) * ((nF.g * 2.0 - 1.0) * 1.2 + (h1 * 2.0 - 1.0) * 0.4);
	f = vec2(f.x * cos(ya) - f.y * sin(ya), f.x * sin(ya) + f.y * cos(ya));
	vec2 r = vec2(-f.y, f.x) * (h5 * 0.6 + nF.b * 0.8 < 0.7 ? 1.0 : -1.0);
	float t = clamp(off.y, 0.0, 1.0);
	v_t = t;
	float asp = 0.75 + 0.5 * gh(wp * 8.7 + 3.0);
	vec3 p = vec3(r.x, 0.0, r.y) * off.x * card.x * sz * asp + vec3(0.0, off.y * card.y * sz / asp, 0.0);
	p.xz -= f * off.y * card.y * sz * tilt * (1.0 + tilt_var * (2.0 * gh(wp * 5.3 + 9.0) - 1.0));
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
	v_tint = mix(warm, cool, lush * mix(day_cool, 1.0, flora_light.x)) * tone * (0.8 + 0.3 * gh(wp * 3.9 + 8.0));
	if (dry_share > 0.0) {
		float dk = step(gh(wp * 8.3 + 17.0), dry_share * (0.4 + 1.2 * smoothstep(0.35, 0.7, nM.b * 0.6 + nC.r * 0.4)));
		v_tint *= mix(vec3(1.0), dry_tint, dk);
	}
	v_tint *= 1.0 + val_spread * ((gh(wp * 2.9 + 21.0) * 2.0 - 1.0) * 0.6 + (nM.g - 0.5) * 2.0 * 0.6);
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
	gb = mix(vec3(dot(gb, vec3(0.2126, 0.7152, 0.0722))), gb, mix(sat, night_sat, flora_light.x));
	// The root in the ground: the ground's colour, darkened, up the first part of the clump.
	gb = mix(v_ground * base, gb, smoothstep(0.0, 0.3, t));
	// By night the moonlit tips blue-green.
	// under a low sun the tips no warmer than hue_floor (the key's hue on them turned back up to it)
	vec3 key = flora_light.z > 0.0 ? clamp(vec3(flora_light.z, 1.0, flora_light.w), vec3(0.2), vec3(5.0)) : vec3(1.0);
	float hl = hue_of(sqrt(max(gb * key, vec3(0.0))));
	gb = max(hue_turn(gb, radians(clamp(hue_floor - hl, 0.0, 60.0) * flora_light.y)), vec3(0.0));
	gb *= mix(vec3(1.0), night_tint, flora_light.x);
	gb *= mix(day_warm, vec3(1.0), flora_light.x);
	// (a flower's pale head no brighter than the moonlit road: dimmed by night)
	gb *= 1.0 - 0.5 * flora_light.x * smoothstep(0.2, 0.4, dot(tx.rgb, vec3(0.2126, 0.7152, 0.0722)));
	float fr = v_frost * smoothstep(mix(1.0, 0.35, v_frost), 1.0, t);
	float fl = min(dot(gb, vec3(0.2126, 0.7152, 0.0722)) * frost_tone, frost_cap);
	gb = mix(gb, vec3(0.86, 0.93, 1.0) * fl, fr * 0.8);
	ALBEDO = debug_view == 4 ? vec3(fr * 0.8, 0.0, 1.0 - fr * 0.8) : gb;
	// (--ground-debug 5: the grass alone, flat magenta, a mask for measuring its pixels in a frame shot the same)
	if (debug_view == 5) { ALBEDO = vec3(0.0); EMISSION = vec3(1.0, 0.0, 1.0) * 4.0; }
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
	BACKLIGHT = gb * 0.25 * (1.0 - 0.6 * flora_light.x);
	if (flare_live()) {
		vec3 fl_a = ALBEDO; float fl_r = ROUGHNESS; vec3 fl_e = EMISSION;
		flare_blade(v_wp, t, fl_a, fl_r, fl_e);
		ALBEDO = fl_a; ROUGHNESS = fl_r; EMISSION = fl_e;
	}
}

// The key's light on the blades as the built-in gives it (Burley, and the back light through them), its sunlit upper
// part warmed by sun_tip (the key alone, by day and dawn; never the moon or a lamp).
// (Low Ford r3, judge r2: under every lamp, fire and her ember the blades went lime: green times a warm light is yellow-green)
// A warm near light's share on the blades turned toward ochre, its lightness kept: flora_lamp of the way (the air's
// GrassLampOchre; 0 as built), by how warm the light is (red over blue); the moon and the sun untouched.
global uniform float flora_lamp;
uniform vec3 lamp_ochre = vec3(1.0, 0.74, 0.40);
void light() {
	float cnl = max(dot(NORMAL, LIGHT), 0.0);
	float cnv = max(dot(NORMAL, VIEW), 1e-3);
	float clh = max(dot(LIGHT, normalize(LIGHT + VIEW)), 0.0);
	float fd90m1 = 2.0 * clh * clh * ROUGHNESS - 0.5;
	float fl = 1.0 + fd90m1 * pow(1.0 - cnl, 5.0), fv = 1.0 + fd90m1 * pow(1.0 - cnv, 5.0);
	float d = fl * fv * cnl;
	vec3 lc = LIGHT_COLOR * ATTENUATION;
	if (LIGHT_IS_DIRECTIONAL) lc *= mix(vec3(1.0), sun_body * mix(vec3(1.0), sun_tip, smoothstep(0.3, 0.85, v_t)), 1.0 - flora_light.x);
	vec3 add = lc * (d + BACKLIGHT * max(1.0 - d, 0.0)) / PI;
	if (!LIGHT_IS_DIRECTIONAL && flora_lamp > 0.0) {
		float warmth = clamp((lc.r - lc.b) / max(lc.r, 1e-4) * 2.0, 0.0, 1.0);
		vec3 lum = vec3(0.2126, 0.7152, 0.0722);
		vec3 a = max(ALBEDO, vec3(0.02));
		vec3 lit = a * add;
		vec3 och = lamp_ochre * (dot(lit, lum) / dot(lamp_ochre, lum));
		add = mix(lit, och, flora_lamp * warmth) / a;
	}
	DIFFUSE_LIGHT += add;
}
