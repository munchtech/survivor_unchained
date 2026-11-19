// (lane J art-color, 19 Nov) The world's colour per time of day (logic/Look/Palettes.cs; rigs.json "palettes"): each class a
// ramp of three colours (dark, mid, lit; linear) laid over the albedo's own value, the square root of its linear luminance
// from lo to hi, taken by amount (0: the albedo as built). Set by Atmosphere.SetPalette from the air the clock blends.
// pal_<class>0 = (dark rgb, amount), pal_<class>1 = (mid rgb, lo), pal_<class>2 = (lit rgb, hi).
// Only world classes call it: never her skin, hair, eyes or gear.
#ifndef PALETTE_INC
#define PALETTE_INC
global uniform vec4 pal_leaf0;
global uniform vec4 pal_leaf1;
global uniform vec4 pal_leaf2;
global uniform vec4 pal_grass0;
global uniform vec4 pal_grass1;
global uniform vec4 pal_grass2;
global uniform vec4 pal_ground0;
global uniform vec4 pal_ground1;
global uniform vec4 pal_ground2;
global uniform vec4 pal_path0;
global uniform vec4 pal_path1;
global uniform vec4 pal_path2;
global uniform vec4 pal_stone0;
global uniform vec4 pal_stone1;
global uniform vec4 pal_stone2;
global uniform vec4 pal_bark0;
global uniform vec4 pal_bark1;
global uniform vec4 pal_bark2;
// (ember keep) pal_ember = (near m, far m, keep, value): within near m of her light (cel_ember, cel.gdshaderinc: xyz its point, w its
// reach, 0 none) the palette is taken back by keep, eased back in to none at far m: her pool keeps its own ground at night.
global uniform vec4 pal_ember;
// (lead 2) each class its own value keep: pal_vk0 = (leaf, grass, ground, path), pal_vk1 = (stone, bark, -, -)
global uniform vec4 pal_vk0;
global uniform vec4 pal_vk1;
// (lead 3, judge r1 fix 1) the leaf class's two more crown ramps (a: crimson, b: gold by day; .w unused, the leaf ramp's amount and
// range hold), pal_leafm = (share of crowns on a, share on b, per-tree shift, tip shift), pal_leafn = (darken by the lens, from m, to m, -)
global uniform vec4 pal_leafa0;
global uniform vec4 pal_leafa1;
global uniform vec4 pal_leafa2;
global uniform vec4 pal_leafb0;
global uniform vec4 pal_leafb1;
global uniform vec4 pal_leafb2;
global uniform vec4 pal_leafm;
global uniform vec4 pal_leafn;
// (lead 3, judge r1 fix 4) pal_embera = (rgb linear, on): the ground her pool falls on, in place of the albedo as built that
// pal_ember's keep brought back (its brown under her amber read as mud)
global uniform vec4 pal_embera;

vec3 pal_ramp(vec3 albedo, vec4 d, vec4 m, vec4 l, float k, float shift, float vk) {
	if (d.w <= 0.0 || k <= 0.0) return albedo;
	float v = sqrt(max(dot(albedo, vec3(0.2126, 0.7152, 0.0722)), 0.0));
	float t = clamp((v - m.w) / max(l.w - m.w, 1e-3) + shift, 0.0, 1.0);
	vec3 r = t < 0.5 ? mix(d.rgb, m.rgb, t * 2.0) : mix(m.rgb, l.rgb, t * 2.0 - 1.0);
	// (pal_ember.w, the palette's "value": how far the albedo's own luminance is kept, the ramp giving hue and chroma only)
	float lr = dot(r, vec3(0.2126, 0.7152, 0.0722));
	r = mix(r, r * (v * v / max(lr, 1e-4)), vk);
	// (lead 2: never brighter than 1.15 x the ramp's lit stop: a bright-albedo rock by the camera kept its value and blew out
	// to salmon in full sun, k13 (254,168,133) where the ramp's warm grey was meant; the lit stop is each class's ceiling)
	float lc = 1.15 * dot(l.rgb, vec3(0.2126, 0.7152, 0.0722));
	r *= min(1.0, lc / max(dot(r, vec3(0.2126, 0.7152, 0.0722)), 1e-4));
	if (pal_embera.w <= 0.0) return mix(albedo, r, d.w * k);
	// (lead 3: within her pool the keep takes the pool's own ground, its value turned by the albedo's)
	return mix(mix(albedo, r, d.w), pal_embera.rgb * clamp(v / 0.45, 0.6, 1.3), (1.0 - k) * d.w);
}
float pal_keep(vec3 wp) {
	if (pal_ember.z <= 0.0 || cel_ember.w <= 0.0) return 1.0;
	return 1.0 - pal_ember.z * (1.0 - smoothstep(pal_ember.x, max(pal_ember.y, pal_ember.x + 1e-3), distance(wp.xz, cel_ember.xz)));
}
vec3 pal_leaf(vec3 a) { return pal_ramp(a, pal_leaf0, pal_leaf1, pal_leaf2, 1.0, 0.0, pal_vk0.x); }
// (a tree its own place on the ramp: s -1..1, a per-copy hash, moves t by up to 0.3: one tree crimson, the next orange or gold)
vec3 pal_leaf(vec3 a, vec3 wp, float s) { return pal_ramp(a, pal_leaf0, pal_leaf1, pal_leaf2, pal_keep(wp), 0.3 * s, pal_vk0.x); }
// (lead 3) a crown's own ramp by its hash h (0..1): the first pal_leafm.x of them on ramp a, the last pal_leafm.y on ramp b,
// the rest on the leaf ramp; h2 (0..1) its place on it (shift pal_leafm.z), tip the spray's sky-facing (-1..1, shift pal_leafm.w)
// dist: the frame radius (0 the frame's centre, about 1 its corners; m5: by metres from the lens nothing darkened, the play
// camera stands far off): toward the frame's edges (pal_leafn: darken, from, to) the crown slides down its ramp and darkens
// (m6: by the frame radius alone the crown nearest the lens, low in the frame, was missed: also by metres, none past pal_leafn.w m, whole inside 0.55 of it)
float pal_near_w(float edge, float dist) {
	if (pal_leafn.x <= 0.0) return 0.0;
	float e = smoothstep(pal_leafn.y, max(pal_leafn.z, pal_leafn.y + 1e-3), edge);
	return pal_leafn.w > 0.0 ? max(e, 1.0 - smoothstep(0.55 * pal_leafn.w, pal_leafn.w, dist)) : e;
}
vec3 pal_leaf3(vec3 a, vec3 wp, float h, float h2, float tip, float edge, float dist) {
	float nw = pal_near_w(edge, dist);
	float sh = pal_leafm.z * (h2 * 2.0 - 1.0) + pal_leafm.w * tip - 0.2 * nw;
	vec4 d = pal_leaf0, m = pal_leaf1, l = pal_leaf2;
	if (h < pal_leafm.x) { d = vec4(pal_leafa0.rgb, pal_leaf0.w); m = vec4(pal_leafa1.rgb, pal_leaf1.w); l = vec4(pal_leafa2.rgb, pal_leaf2.w); }
	else if (h > 1.0 - pal_leafm.y) { d = vec4(pal_leafb0.rgb, pal_leaf0.w); m = vec4(pal_leafb1.rgb, pal_leaf1.w); l = vec4(pal_leafb2.rgb, pal_leaf2.w); }
	if (nw > 0.0 && h >= pal_leafm.x) { d = vec4(pal_leafa0.rgb, pal_leaf0.w); m = vec4(mix(m.rgb, pal_leafa1.rgb, nw), pal_leaf1.w); }   // (by the lens toward ramp a's hue: crimson by day)
	return pal_ramp(a, d, m, l, pal_keep(wp), sh, pal_vk0.x) * (1.0 - pal_leafn.x * nw);
}
vec3 pal_leaf(vec3 a, vec3 wp) { return pal_ramp(a, pal_leaf0, pal_leaf1, pal_leaf2, pal_keep(wp), 0.0, pal_vk0.x); }
vec3 pal_grass(vec3 a) { return pal_ramp(a, pal_grass0, pal_grass1, pal_grass2, 1.0, 0.0, pal_vk0.y); }
vec3 pal_grass(vec3 a, vec3 wp) { return pal_ramp(a, pal_grass0, pal_grass1, pal_grass2, pal_keep(wp), 0.0, pal_vk0.y); }
vec3 pal_ground(vec3 a) { return pal_ramp(a, pal_ground0, pal_ground1, pal_ground2, 1.0, 0.0, pal_vk0.z); }
vec3 pal_ground(vec3 a, vec3 wp) { return pal_ramp(a, pal_ground0, pal_ground1, pal_ground2, pal_keep(wp), 0.0, pal_vk0.z); }
vec3 pal_path(vec3 a) { return pal_ramp(a, pal_path0, pal_path1, pal_path2, 1.0, 0.0, pal_vk0.w); }
vec3 pal_path(vec3 a, vec3 wp) { return pal_ramp(a, pal_path0, pal_path1, pal_path2, pal_keep(wp), 0.0, pal_vk0.w); }
vec3 pal_stone(vec3 a) { return pal_ramp(a, pal_stone0, pal_stone1, pal_stone2, 1.0, 0.0, pal_vk1.x); }
vec3 pal_stone(vec3 a, vec3 wp) { return pal_ramp(a, pal_stone0, pal_stone1, pal_stone2, pal_keep(wp), 0.0, pal_vk1.x); }
vec3 pal_bark(vec3 a) { return pal_ramp(a, pal_bark0, pal_bark1, pal_bark2, 1.0, 0.0, pal_vk1.y); }
vec3 pal_bark(vec3 a, vec3 wp) { return pal_ramp(a, pal_bark0, pal_bark1, pal_bark2, pal_keep(wp), 0.0, pal_vk1.y); }
#endif
