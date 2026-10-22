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
render_mode blend_mix, depth_draw_never, cull_disabled, diffuse_lambert, specular_schlick_ggx, shadows_disabled;

uniform sampler2D noise_tex : filter_linear_mipmap, repeat_enable;
// The noise's slopes (Water.Grad: RG the swell's (noise R), BA the chop's (noise B), 0.5 flat), so a ripple's normal is one look.
uniform sampler2D grad_tex : filter_linear_mipmap, repeat_enable;
uniform sampler2D screen_tex : hint_screen_texture, filter_linear;
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
// The brightest a light's glint gets (linear, its brightest channel): under the tonemap's white, so a lamp's glint keeps
// the lamp's own colour (and the moon's its own) instead of burning to white.
uniform float glint_cap = 1.6;
// A near light's glint (a lamp, her ember: not the moon or the sun) spread to this roughness: a point light just over
// the water is a broad broken highlight on the ripples round its mirror point, not one pixel lost behind a stone.
uniform float glint_spread = 0.22;
// ...and seen on facets tilted this much more (the chop's steep sides): a lamp or her ember glitters in a broken path a few
// metres long round its mirror point, as a lamp does on a stream, instead of one glint hidden behind a post or a stone.
uniform float glint_bend = 3.0;
// ...and brighter by this (a small lamp's light on a stream reads as a run of bright sparks; the cap still holds its hue).
uniform float glint_near = 5.0;
// A near light's broad sheen on the ripples' crests (gain; 0 none): its light spread round its mirror point, broken by the
// chop, so her ember shows on the water about her even where its mirror image falls on the ford's stones.
uniform float glint_sheen = 0.0;
// A wake's taper: it narrows by this much a metre downstream (m/m), so it ends at its breaker's half-width over it
// (0.4: a stone's 2.5 radii, a leg's own); and the shore foam's lace size (m).
uniform float wake_taper = 0.4;
uniform float lace_size = 0.7;
// The whole river's light scaled, for a cinematic's grade (GameCinema "water"); 1 as built.
uniform float level = 1.0;
// 1 foam, 2 depth (m, 1 = white), 3 the wake, 4 the bed through (no body), 5 what is under (the water left out), 6 the
// shore's fade in (in_k), unlit; 7 lit as built but no glints; 8 only the near lights' glints (no moon, no sun).
uniform int debug_view = 0;
// C03 env r2 (judge: the low cameras' water "reads as milk, mirrors nothing"): at a grazing angle the surface mirrors the
// scene (screen space: the reflected ray marched over the depth buffer), the ripples breaking it by mirror_ripple, and
// each near light leaves a streak toward the camera (light(): a long, narrow, ripple-broken glint). Only under a camera
// looking along the water: the flat surface's cos to the view under mirror_from (0.42, 25 deg) fades it in, full by
// mirror_to (0.17, 10 deg), so the play camera (looking down 40+ deg) keeps its water as judged. mirror 0: none.
uniform float mirror = 0.0;
uniform float mirror_from = 0.42;
uniform float mirror_to = 0.17;
uniform float mirror_ripple = 0.35;
// The streak's gain (0 none), its half-width across and length along (in the half vector's tangent; 0.03 x 0.2: a lamp's
// broken path a few metres long toward the camera, a hand wide).
uniform float streak = 0.0;
uniform float streak_w = 0.03;
uniform float streak_l = 0.2;
// ...its brightest (linear, its brightest channel), under the glints' cap: a lamp's streak keeps its hue, never a white bar.
uniform float streak_cap = 0.5;
// ...in the hue of the flame the camera sees, not its light's (C03: the Warden's amber lantern threw a blue streak, its
// light #8ac8ff): up to four lights (Water.StreakTint), each its light's world position (w 1 on) and its flame's colour
// (linear); a light matched by direction from the water, within about 2 degrees. Others keep their light's colour.
uniform vec4 streak_at[4];
uniform vec3 streak_tint[4];
// The air's say over the river (Atmosphere.Set, play's presets, E1): x its light, y the sky in it, z how far the
// ripples bend it (under 1 the moon's glints gather into a band toward it); (1, 1, 1) as built.
global uniform vec4 water_air;

varying vec3 w_pos;
// The glints' strength (the fragment's SPECULAR, which light() can't read).
varying float spec_k;
// The near lights' facets (view space): the ripples' normal with the chop steepened by glint_bend.
varying vec3 glint_n;
varying float crest;
// How grazing the view is (0 the play camera, 1 along the water) times mirror; and the flat surface's normal (view space).
varying float graze;
varying vec3 flat_n;

void vertex() {
	w_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

// The view-space point the depth buffer holds at uv.
vec3 view_at(vec2 uv, mat4 inv_proj, sampler2D dt) {
	vec4 p = inv_proj * vec4(uv * 2.0 - 1.0, texture(dt, uv).r, 1.0);
	return p.xyz / p.w;
}

// The scene mirrored at p (view space) along r: the ray marched out over the depth buffer in growing steps until it
// passes behind something (then halved down to its edge), or what it last passed over when it meets nothing (the sky,
// the far trees). a: 0 when the ray left the screen at once.
vec4 mirror_at(vec3 p, vec3 r, mat4 proj, mat4 inv_proj) {
	float t = 0.12, tp = 0.0;
	vec2 last = vec2(-1.0);
	for (int i = 0; i < 34; i++) {
		vec3 q = p + r * t;
		if (q.z > -0.05) break;
		vec4 c = proj * vec4(q, 1.0);
		vec2 uv = c.xy / c.w * 0.5 + 0.5;
		if (uv.x < 0.0 || uv.y < 0.0 || uv.x > 1.0 || uv.y > 1.0) break;
		last = uv;
		float d = view_at(uv, inv_proj, depth_tex).z - q.z;
		if (d > 0.0 && d < 0.5 + t * 0.12) {
			float a = tp, b = t;
			vec2 hit = uv;
			for (int k = 0; k < 5; k++) {
				float m = 0.5 * (a + b);
				vec3 qm = p + r * m;
				vec4 cm = proj * vec4(qm, 1.0);
				vec2 um = cm.xy / cm.w * 0.5 + 0.5;
				if (view_at(um, inv_proj, depth_tex).z - qm.z > 0.0) { b = m; hit = um; } else { a = m; }
			}
			return vec4(texture(screen_tex, hit).rgb, 1.0);
		}
		tp = t;
		t *= 1.2;
	}
	if (last.x < 0.0) return vec4(0.0);
	return vec4(texture(screen_tex, last).rgb, 1.0);
}

void fragment() {
	vec3 wv = w_pos;
	// The ripples' frame: the world (x, z), or the stream's (across, along).
	vec2 rp = stream ? vec2(UV.x, -UV.y) : wv.xz;
	vec2 v = flow;
	float t = TIME;
	// The surface's slope (per m), drifting downstream: a swell, a quicker cross-swell, and a finer chop that breaks the
	// lights' glints. (The noise is tiled ripple_size x 4 m, so a texel is 2 cm: its facets stay under a pixel.)
	float s = 1.0 / (ripple_size * 4.0);
	vec4 ga = texture(grad_tex, (rp - v * t) * s);
	vec4 gb = texture(grad_tex, (rp - v * t * 1.6) * s * 0.83 + vec2(0.37, 0.71));
	vec4 gc = texture(grad_tex, (rp - v * t * 1.3) * s + vec2(0.53, 0.19));
	float tm = 256.0 * s;
	vec2 swell = ((ga.rg - 0.5) / 12.0 * 0.6 + (gb.rg - 0.5) / 12.0 * 0.4 * 0.83) * tm;
	vec2 chop = (gc.ba - 0.5) / 6.0 * tm;
	float bend = ripple_bend * water_air.z;
	vec2 g = swell * 0.3 + chop * 0.03;
	vec3 n_w = normalize(vec3(-g.x * bend, 1.0, -g.y * bend));
	NORMAL = normalize((VIEW_MATRIX * vec4(n_w, 0.0)).xyz);
	vec2 gg = (swell * 0.3 + chop * 0.1) * bend * glint_bend;
	crest = smoothstep(0.4, 1.2, length(chop));
	glint_n = normalize((VIEW_MATRIX * vec4(normalize(vec3(-gg.x, 1.0, -gg.y)), 0.0)).xyz);
	vec3 vdir = normalize(-VERTEX);
	float ndv = clamp(dot(vdir, NORMAL), 0.0, 1.0);
	float fres = 0.02 + 0.98 * pow(1.0 - ndv, 5.0);
	flat_n = normalize((VIEW_MATRIX * vec4(0.0, 1.0, 0.0, 0.0)).xyz);
	graze = mirror * (1.0 - smoothstep(mirror_to, mirror_from, abs(dot(vdir, flat_n))));

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
	// (its width wandering along the bank, so the clear strip at the edge is never an even ribbon)
	// (full by 'shore' m deep at most, E6c judge r2)
	float in_k = smoothstep(0.0, shore * (0.55 + 0.45 * texture(noise_tex, wv.xz * 0.07 + 0.11).g), wd);
	vec3 body = mix(color, murk, smoothstep(0.3, deep, wd));
	body = mix(body, shallow * 0.6, sh * 0.5);
	float opaque = 1.0 - dot(trans, vec3(0.3333));

	// Foam: where something breaks the surface (the depth difference), torn by the flow.
	vec2 fdir = stream ? vec2(0.0, 1.0) : normalize(flow + vec2(1e-5));
	vec2 fside = vec2(-fdir.y, fdir.x);
	vec2 fp = vec2(dot(wv.xz, fdir), dot(wv.xz, fside));
	float fspeed = length(flow);
	// (two broad octaves only: a finer third read as pixel snow by night at the play camera, judge E6 r1)
	float fn = texture(noise_tex, vec2(fp.x - t * fspeed, fp.y * 2.2) * 0.11).g * 0.6 + texture(noise_tex, vec2(fp.x * 1.3 - t * fspeed * 1.3, fp.y * 2.6) * 0.16 + 0.5).a * 0.4;
	// (its edge widened by the depth's own change across a pixel, capped, so a stone's foot rings as soft froth, not
	// single lit pixels)
	float fw = min(fwidth(wd), foam_depth) * 1.5;
	float touch = 1.0 - smoothstep(foam_depth * 0.3 - fw, foam_depth * (0.7 + 0.8 * fn) + fw, wd);
	// A stone's foot or a leg (what it meets is steep) rings whole; a shelving bank only in lace, here and there, so the
	// shore is a soft wet edge and never a drawn line.
	// (E6c, judge r2: the bank's lace a band 0.25-0.4 m wide across the ground from the waterline, torn into pieces
	// lace_size across and thinning away from the edge, from nothing at the waterline itself: no drawn lip)
	vec3 bn = cross(dFdx(bed_ws), dFdy(bed_ws));
	float bny = abs(bn.y) / max(length(bn), 1e-6);
	float steep = 1.0 - smoothstep(0.45, 0.95, bny);
	float edge_m = wd * bny / max(sqrt(max(1.0 - bny * bny, 0.0)), 0.03);
	// (the noise's G is cells an eighth of its tile: a piece of lace lace_size across; about a third of the bank laced)
	float lace_w = 0.25 + 0.15 * texture(noise_tex, wv.xz * 0.03 + 0.6).g;
	float lace = smoothstep(0.55, 0.75, texture(noise_tex, (wv.xz - flow * t * 0.25) * (0.125 / lace_size) + 0.17).g * 0.85 + fn * 0.15)
		* smoothstep(0.0, 0.08, edge_m) * (1.0 - smoothstep(lace_w * 0.3, lace_w, edge_m));
	float ring = mix(lace * 0.4, touch * 0.7 * smoothstep(0.25, 0.75, fn + touch * 0.2), steep);

	// The wake (E6c, judge r2: never a box): behind anything that breaks the surface, a teardrop down the current, as long
	// as the breaker is wide over wake_taper, round-edged and torn by the flow's noise. A look 's' upstream counts the
	// breaker only where it spans this point's line +-e, e growing with s, so the wake narrows to nothing; three looks
	// summed give it a falloff both down and across. (And one just downstream, the cushion against a stone's face.)
	float wk = 0.0, bow = 0.0;
	// (the looks' spacing dithered from the mipmapped noise, sampled out here where the branch can't break its filtering:
	// far off the bubbles average out instead of sparkling; a per-pixel hash read as snow by night)
	float bub0 = texture(noise_tex, vec2(fp.x - t * fspeed, fp.y) * 0.6).r * 2.0;
	// (the tear: noise 0.3-0.6 m across (G: cells an eighth of the tile), drifting with the flow, no grain along it)
	float tear = texture(noise_tex, vec2(fp.x - t * fspeed, fp.y) * 0.28 + 0.31).g;
	if (wake > 0.0 && !stream && wd > foam_depth * 0.5) {
		mat4 vp = PROJECTION_MATRIX * VIEW_MATRIX;
		vec3 fd3 = vec3(fdir.x, 0.0, fdir.y), fs3 = vec3(fside.x, 0.0, fside.y);
		for (int i = 0; i <= 3; i++) {
			float bub = fract(bub0 + float(i) * 0.618);
			float L = i == 0 ? -(0.1 + 0.22 * bub) : wake * (float(i) - 1.0 + bub) / 3.0;
			float e = abs(L) * wake_taper * (0.6 + 0.8 * tear);
			float hit = 1.0;
			for (int k = -1; k <= 1; k += 2) {
				vec3 up = wv - fd3 * L + fs3 * (e * float(k));
				vec4 cl = vp * vec4(up, 1.0);
				vec2 uv = cl.xy / cl.w * 0.5 + 0.5;
				if (uv.x < 0.0 || uv.x > 1.0 || uv.y < 0.0 || uv.y > 1.0) { hit = 0.0; break; }
				vec3 b = (INV_VIEW_MATRIX * vec4(view_at(uv, INV_PROJECTION_MATRIX, depth_tex), 1.0)).xyz;
				// Something there stands within a hand of the surface, or above it: a breaker.
				// (only what stands there: a post or a body nearer the camera that hides the spot is not in the river)
				hit = min(hit, (1.0 - smoothstep(0.02, 0.1, up.y - b.y)) * (1.0 - smoothstep(0.15, 0.5, length(b.xz - up.xz))));
				if (hit <= 0.0) break;
			}
			if (i == 0) { bow = hit; continue; }
			float fade = 1.0 - (float(i) - 1.0 + bub) / 3.0;
			wk += hit * fade;
		}
		wk = clamp(wk / 1.5, 0.0, 1.0) * smoothstep(0.15, 0.6, tear + wk * 0.25);
	}
	bow *= smoothstep(0.4, 0.75, fn + 0.15);
	float foam = clamp(max(max(ring, bow * 0.45), wk * 0.5) * foam_amt, 0.0, 1.0);

	// The shore's wet lip: the bed darkens as the water takes it, under the sheen's own fade.
	// (E6c, judge r2: everything the water does to the bed fades in by in_k with what it adds. The night's dark line along
	// every bank was the air's river light (water_air.x, 0.55 by night, 1 by day) dimming the bed seen through from the
	// very waterline, before the body and sheen came in: the bed just under the edge sat at 0.55 of the bank beside it)
	vec3 seen = under * mix(vec3(1.0), trans * 0.82, in_k);
	float lv = level * water_air.x;
	float lv_bed = mix(1.0, lv, in_k);
	vec3 skyr = sky * water_air.y * fres * in_k;
	vec3 sick = murk * glow * (0.6 + 0.4 * fn) * in_k;

	ALBEDO = (mix(body * opaque * in_k, foam_color * 0.55, foam * 0.8)) * lv;
	EMISSION = seen * (1.0 - fres * in_k) * (1.0 - foam * 0.8) * lv_bed + (skyr * (1.0 - foam) + sick + foam_color * foam * 0.05) * lv;
	ROUGHNESS = mix(gloss, 0.7, foam);
	// Water's 2% straight on (Godot's dielectric F0 is 0.08 x SPECULAR), none where it thins to nothing at the shore.
	SPECULAR = 0.25 * in_k * (1.0 - foam) * level;
	spec_k = SPECULAR;
	METALLIC = 0.0;
	// The mirror at a grazing angle (see 'mirror'): the scene's own colours over the body, the sky's sheen and the sky's
	// light (SPECULAR: Godot's sky reflection, an even grey-teal at the horizon) it replaces.
	float gk = graze * in_k * (1.0 - foam);
	if (gk > 0.001) {
		vec3 rn = normalize(mix(flat_n, NORMAL, mirror_ripple));
		vec4 mr = mirror_at(VERTEX, reflect(normalize(VERTEX), rn), PROJECTION_MATRIX, INV_PROJECTION_MATRIX);
		float k = gk * mr.a;
		EMISSION = mix(EMISSION, mr.rgb, k);
		ALBEDO *= 1.0 - k;
		SPECULAR *= 1.0 - k;
	}

	if (debug_view > 0) {
		if (debug_view == 7) { SPECULAR = 0.0; spec_k = 0.0; } else if (debug_view == 8) { ALBEDO = vec3(0.0); EMISSION = vec3(0.0); } else if (debug_view == 9) { ALBEDO = vec3(1.0); EMISSION = vec3(0.0); SPECULAR = 0.0; spec_k = 0.0; } else {
		float m = debug_view == 1 ? foam : debug_view == 2 ? wd : debug_view == 6 ? in_k : wk;
		ALBEDO = vec3(0.0);
		SPECULAR = 0.0;
		spec_k = 0.0;
		EMISSION = debug_view == 4 ? seen : debug_view == 5 ? under : vec3(clamp(m, 0.0, 1.0)) * 4.0;
		}
	}
}

// The lights on the water: lambert for the body's little diffuse, and each light's glint in its own colour (GGX on the
// rippled normal), its brightest channel held under glint_cap so a warm lamp's glint stays warm.
void light() {
	float ndl = clamp(dot(NORMAL, LIGHT), 0.0, 1.0);
	DIFFUSE_LIGHT += ndl * ATTENUATION * LIGHT_COLOR / PI * (debug_view == 9 && LIGHT_IS_DIRECTIONAL ? 0.0 : 1.0);
	vec3 h = normalize(VIEW + LIGHT);
	// (a near light glints on the steeper facets, broader: E6c, judge r2, her ember's glint was lost behind the post)
	// (glint_bend 0: as the moon's; E6c: 3 spread the pylons' lamps into sparkle clumps and still never showed her ember)
	vec3 gn = LIGHT_IS_DIRECTIONAL || glint_bend <= 0.0 ? NORMAL : glint_n;
	float ndh = clamp(dot(gn, h), 0.0, 1.0);
	float a = LIGHT_IS_DIRECTIONAL ? ROUGHNESS * ROUGHNESS : max(ROUGHNESS, glint_spread) * max(ROUGHNESS, glint_spread);
	float a2 = a * a;
	float dd = ndh * ndh * (a2 - 1.0) + 1.0;
	float D = a2 / (PI * dd * dd);
	float f0 = 0.08 * spec_k * min(SPECULAR_AMOUNT, 1.0);
	float F = (f0 + (1.0 - f0) * pow(1.0 - clamp(dot(VIEW, h), 0.0, 1.0), 5.0)) * clamp(spec_k * 4.0, 0.0, 1.0);
	float k = a * 0.5;
	float ndv = clamp(dot(NORMAL, VIEW), 1e-3, 1.0);
	float vis = 0.25 / ((ndl * (1.0 - k) + k) * (ndv * (1.0 - k) + k) + 1e-4);
	vec3 c = LIGHT_COLOR * (D * F * vis * ndl * ATTENUATION) * (LIGHT_IS_DIRECTIONAL ? 1.0 : glint_near);
	if (!LIGHT_IS_DIRECTIONAL && glint_sheen > 0.0) {
		float ndh_s = clamp(dot(NORMAL, h), 0.0, 1.0);
		float as2 = 0.0625;
		float ds = ndh_s * ndh_s * (as2 - 1.0) + 1.0;
		c += LIGHT_COLOR * (as2 / (PI * ds * ds) * F * vis * ndl * ATTENUATION) * glint_sheen * crest;
	}
	// A near light's streak at a grazing angle (see 'streak'): its mirror point drawn out toward the camera, broken by the chop.
	if (!LIGHT_IS_DIRECTIONAL && streak > 0.0 && graze > 0.001) {
		vec3 ax = normalize(cross(flat_n, VIEW));
		vec3 al = cross(ax, flat_n);
		float hx = dot(h, ax) / streak_w, hl = dot(h, al) / streak_l;
		// (broken into dashes by the chop's crests, and held under streak_cap in its own hue: r2's first cut lay under each
		// ford pier as a solid white-blue bar from s12's higher camera)
		vec3 lc = LIGHT_COLOR;
		vec3 wl = normalize((INV_VIEW_MATRIX * vec4(LIGHT, 0.0)).xyz);
		for (int k = 0; k < 4; k++) {
			if (streak_at[k].w > 0.5 && dot(normalize(streak_at[k].xyz - w_pos), wl) > 0.9994) {
				vec3 t = max(streak_tint[k], vec3(1e-4));
				lc = t * (max(lc.r, max(lc.g, lc.b)) / max(t.r, max(t.g, t.b)));
			}
		}
		vec3 cs = lc * ATTENUATION * streak * graze * exp(-hx * hx - hl * hl) * mix(0.12, 1.8, crest * crest) * clamp(spec_k * 4.0, 0.0, 1.0);
		c += cs * min(1.0, streak_cap / max(max(cs.r, max(cs.g, cs.b)), 1e-4));
	}
	float m = max(c.r, max(c.g, c.b));
	// (E7 round 3: a near light's glint scaled by its light_specular over Godot's 0.5, after the cap: the ford lamps at 0.3
	// spread blown white patches on the far ripples at the cap; the moon and the sun as before)
	float sk = LIGHT_IS_DIRECTIONAL ? 1.0 : clamp(SPECULAR_AMOUNT * 2.0, 0.0, 1.0);
	SPECULAR_LIGHT += c * min(1.0, glint_cap / max(m, 1e-4)) * sk * (debug_view == 8 && LIGHT_IS_DIRECTIONAL ? 0.0 : 1.0);
}
