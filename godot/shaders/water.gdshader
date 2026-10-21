// Every river and pond (E6, docs/art/look_bible/04_water_shore.md): one material, its looks as data (a zone's
// water.json "look", Water.cs). What it does, all from the scene depth under the surface (no extra passes):
// - colour by depth: the bed seen clear through the shallows, bent by the ripples and dimmed per channel by how much
//   water the light crosses (clarity), the water's own body (color, murk past deep) lit by the scene's lights;
// - no line where it meets land: at depth zero it is the bed itself, the sky's sheen and the body fading in over 'shore' m;
// - foam where anything breaks the surface (a bank, a stone, a leg: the depth difference), and a wake downstream of it
//   (the depth looked up upstream, along the flow);
// - the flow: ripples and foam streaks carried downstream ('flow', m/s) in two scales at two speeds;
// - reflection: the sky by fresnel (water's 2% looking down, all of it at a grazing angle), and the lights' own glints on
//   the rippled normals (SPECULAR/ROUGHNESS), so a lamp put out takes its glint with it.
// Stream mode (the Verge's ribbon, export_zone.mjs): the ripples run in the stream's own coordinates (UV: across, along)
// and UV2.x is the bank's distance; the rest is the same.
shader_type spatial;
render_mode blend_mix, depth_draw_never, cull_disabled, diffuse_burley, specular_schlick_ggx;

uniform sampler2D noise_tex : filter_linear_mipmap, repeat_enable;
uniform sampler2D screen_tex : hint_screen_texture, filter_linear_mipmap;
uniform sampler2D depth_tex : hint_depth_texture, filter_nearest;
uniform bool stream = true;
// The body: color its scattered light where deep, murk past 'deep' m, shallow the tint the bed takes through it.
uniform vec3 color : source_color = vec3(0.165, 0.29, 0.118);
uniform vec3 murk : source_color = vec3(0.047, 0.118, 0.024);
uniform vec3 shallow : source_color = vec3(0.306, 0.353, 0.165);
uniform vec3 foam_color : source_color = vec3(0.722, 0.784, 0.565);
uniform vec3 sky : source_color = vec3(0.18, 0.29, 0.188);
// Downstream, m/s (world x, z; stream mode: across, along).
uniform vec2 flow = vec2(0.0, 0.6);
uniform float glow = 0.45;
// m of water the bed fades through to about a third (the light's path, so a grazing look sees less of it).
uniform float clarity = 0.6;
// m: the body full and dark past it.
uniform float deep = 1.6;
// m: the sheen and body fade in over this depth from the shore (0: the bed itself, no line).
uniform float shore = 0.12;
// Foam: how deep a surface breaks it (m), how much of it, the wake's length behind a stone or a leg (m, 0: none).
uniform float foam_depth = 0.07;
uniform float foam_amt = 1.0;
uniform float wake = 1.6;
// Ripples: their size (m), how far they bend the normal, how far they bend the bed seen through.
uniform float ripple_size = 1.4;
uniform float ripple_bend = 0.55;
uniform float refract = 0.03;
// The glints' sharpness (roughness at the ripples' crests).
uniform float gloss = 0.06;
// The whole river's light scaled, for a cinematic's grade (GameCinema "water"); 1 as built.
uniform float level = 1.0;
// 1 foam, 2 depth (m, 1 = white), 3 the wake, 4 the bed through (no body), unlit.
uniform int debug_view = 0;
// The air's say over the river (Atmosphere.Set, play's presets, E1): x its light, y the sky in it, z how far the
// ripples bend it (under 1 the moon's glints gather into a band toward it); (1, 1, 1) as built.
global uniform vec4 water_air;

varying vec3 w_pos;

void vertex() {
	w_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

// The surface's height (0-1) at p (m, in the flow's frame), drifting downstream: a swell and a quicker cross-swell.
// (The noise is tiled ripple_size x 4 m, so a texel is 2 cm: its bilinear facets stay under a pixel at the play camera.)
float wh(vec2 p, vec2 v, float t) {
	float s = 1.0 / (ripple_size * 4.0);
	float a = texture(noise_tex, (p - v * t) * s).r;
	float b = texture(noise_tex, (p - v * t * 1.6) * s * 0.83 + vec2(0.37, 0.71)).g;
	return a * 0.6 + b * 0.4;
}

// The view-space point the depth buffer holds at uv.
vec3 view_at(vec2 uv, mat4 inv_proj, sampler2D dt) {
	vec4 p = inv_proj * vec4(uv * 2.0 - 1.0, texture(dt, uv).r, 1.0);
	return p.xyz / p.w;
}

void fragment() {
	vec3 wv = w_pos;
	// The ripples' frame: the world (x, z), or the stream's (across, along).
	vec2 rp = stream ? vec2(UV.x, -UV.y) : wv.xz;
	vec2 v = flow;
	float t = TIME;
	float e = ripple_size * 4.0 / 256.0 * 2.5;
	float h0 = wh(rp, v, t), hx = wh(rp + vec2(e, 0.0), v, t), hz = wh(rp + vec2(0.0, e), v, t);
	// The chop that breaks the lights' glints: finer, quicker.
	float cs = 1.0 / (ripple_size * 4.0);
	vec2 cp = (rp - v * t * 1.3) * cs + vec2(0.53, 0.19);
	float ce = e * cs;
	float c0 = texture(noise_tex, cp).b, cx = texture(noise_tex, cp + vec2(ce, 0.0)).b, cz = texture(noise_tex, cp + vec2(0.0, ce)).b;
	float bend = ripple_bend * water_air.z;
	vec2 g = vec2(hx - h0, hz - h0) / e * 0.3 + vec2(cx - c0, cz - c0) / e * 0.05;
	vec3 n_w = normalize(vec3(-g.x * bend, 1.0, -g.y * bend));
	NORMAL = normalize((VIEW_MATRIX * vec4(n_w, 0.0)).xyz);
	vec3 vdir = normalize(-VERTEX);
	float ndv = clamp(dot(vdir, NORMAL), 0.0, 1.0);
	float fres = 0.02 + 0.98 * pow(1.0 - ndv, 5.0);

	// The bed under this point (straight down the view), and through the ripples.
	vec3 bed_s = view_at(SCREEN_UV, INV_PROJECTION_MATRIX, depth_tex);
	vec3 bed_ws = (INV_VIEW_MATRIX * vec4(bed_s, 1.0)).xyz;
	// How deep the water is over what is under it, here (m, straight down): 0 at a bank, a stone's foot, a leg.
	float wd = max(wv.y - bed_ws.y, 0.0);
	vec2 bent = SCREEN_UV + (VIEW_MATRIX * vec4(n_w.x, 0.0, n_w.z, 0.0)).xy * refract * smoothstep(0.0, 0.3, wd);
	vec3 bed = view_at(bent, INV_PROJECTION_MATRIX, depth_tex);
	if (bed.z > VERTEX.z) { bent = SCREEN_UV; bed = bed_s; }
	float path = max(VERTEX.z - bed.z, 0.0);

	// Light through the water: per channel, the shallow tint deepening with the path.
	vec3 tint = shallow / max(max(shallow.r, max(shallow.g, shallow.b)), 1e-3);
	vec3 ext = (1.0 + 1.6 * (1.0 - tint)) / max(clarity, 0.05);
	vec3 trans = exp(-path * ext);
	float sh = stream ? 1.0 - smoothstep(0.0, 0.55, UV2.x) : 0.0;
	vec3 under = texture(screen_tex, bent).rgb;

	// The body: its colour deepening to murk, lit by the scene (ALBEDO); in by the shore's band.
	float in_k = smoothstep(0.0, shore, wd);
	vec3 body = mix(color, murk, smoothstep(0.3, deep, wd));
	body = mix(body, shallow * 0.6, sh * 0.5);
	float opaque = 1.0 - dot(trans, vec3(0.3333));

	// Foam: where something breaks the surface (the depth difference), torn by the flow.
	vec2 fdir = stream ? vec2(0.0, 1.0) : normalize(flow + vec2(1e-5));
	vec2 fside = vec2(-fdir.y, fdir.x);
	vec2 fp = vec2(dot(wv.xz, fdir), dot(wv.xz, fside));
	float fspeed = length(flow);
	float fn = texture(noise_tex, vec2(fp.x - t * fspeed, fp.y * 2.2) * 0.11).g * 0.6 + texture(noise_tex, vec2(fp.x * 1.8 - t * fspeed * 1.8, fp.y * 3.0) * 0.23 + 0.5).a * 0.4;
	float touch = 1.0 - smoothstep(foam_depth * 0.3, foam_depth * (0.7 + 0.8 * fn), wd);
	// A stone's foot or a leg (what it meets is steep) rings whole; a shelving bank only in lace, here and there, so the
	// shore is a soft wet edge and never a drawn line.
	vec3 bn = cross(dFdx(bed_ws), dFdy(bed_ws));
	float steep = 1.0 - smoothstep(0.55, 0.85, abs(bn.y) / max(length(bn), 1e-6));
	float lace = smoothstep(0.5, 0.75, fn) * smoothstep(0.35, 0.65, texture(noise_tex, wv.xz * 0.045 + 0.3).r);
	float ring = touch * mix(lace * 0.6, smoothstep(0.35, 0.65, fn + touch * 0.25), steep);

	// The wake: anything breaking the surface upstream of here (a stone, a leg) trails foam down the current.
	float wk = 0.0;
	if (wake > 0.0 && !stream && wd > foam_depth * 0.5) {
		mat4 vp = PROJECTION_MATRIX * VIEW_MATRIX;
		// Four looks upstream, their spacing wobbled by the flow's noise so the breaker's outline never repeats in stamps.
		for (int i = 1; i <= 4; i++) {
			// (each look's spacing dithered by bubbles a few cm across, drifting with the flow: the stamps melt into froth)
			float bub = fract(sin(dot(floor(vec2(fp.x - t * fspeed, fp.y) * 28.0) + float(i) * 7.1, vec2(12.9898, 78.233))) * 43758.5453);
			float L = wake * (float(i) - 1.0 + bub) / 4.0;
			// Wider the further behind (the wake spreads), wobbling with the flow.
			float wob = (fn - 0.5) * 0.5 * L / wake;
			vec3 up = vec3(wv.x, wv.y, wv.z) - vec3(fdir.x, 0.0, fdir.y) * L + vec3(fside.x, 0.0, fside.y) * wob;
			vec4 cl = vp * vec4(up, 1.0);
			vec2 uv = cl.xy / cl.w * 0.5 + 0.5;
			if (uv.x < 0.0 || uv.x > 1.0 || uv.y < 0.0 || uv.y > 1.0) continue;
			vec3 b = (INV_VIEW_MATRIX * vec4(view_at(uv, INV_PROJECTION_MATRIX, depth_tex), 1.0)).xyz;
			// Something there stands within a hand of the surface, or above it: a breaker.
			// (only what stands there: a post or a body nearer the camera that hides the spot is not in the river)
			float brk = (1.0 - smoothstep(0.02, 0.1, up.y - b.y)) * (1.0 - smoothstep(0.25, 0.45, length(b.xz - up.xz)));
			float fade = 1.0 - (float(i) - 1.0 + bub) / 4.0;
			wk = max(wk, brk * fade * fade);
		}
		float streaks = smoothstep(0.5, 0.8, texture(noise_tex, vec2(fp.x * 0.7 - t * fspeed * 0.7, fp.y * 4.0) * 0.3).b + fn * 0.4);
		wk *= streaks;
	}
	float foam = clamp(max(ring, wk * 0.55) * foam_amt, 0.0, 1.0);

	// The shore's wet lip: the bed darkens as the water takes it, under the sheen's own fade.
	vec3 seen = under * trans * mix(1.0, 0.82, in_k);
	float lv = level * water_air.x;
	vec3 skyr = sky * water_air.y * fres * in_k;
	vec3 sick = murk * glow * (0.6 + 0.4 * h0);

	ALBEDO = (mix(body * opaque * in_k, foam_color * 0.55, foam * 0.8)) * lv;
	EMISSION = (seen * (1.0 - fres * in_k) * (1.0 - foam * 0.8) + skyr * (1.0 - foam) + sick + foam_color * foam * 0.05) * lv;
	ROUGHNESS = mix(gloss, 0.7, foam);
	// Water's 2% straight on (Godot's dielectric F0 is 0.08 x SPECULAR), none where it thins to nothing at the shore.
	SPECULAR = 0.25 * in_k * (1.0 - foam) * level;
	METALLIC = 0.0;

	if (debug_view > 0) {
		float m = debug_view == 1 ? foam : debug_view == 2 ? wd : wk;
		ALBEDO = vec3(0.0);
		SPECULAR = 0.0;
		EMISSION = debug_view == 4 ? seen : vec3(clamp(m, 0.0, 1.0)) * 4.0;
	}
}
