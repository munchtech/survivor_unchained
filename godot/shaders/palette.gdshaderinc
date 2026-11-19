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
	return mix(albedo, r, d.w * k);
}
float pal_keep(vec3 wp) {
	if (pal_ember.z <= 0.0 || cel_ember.w <= 0.0) return 1.0;
	return 1.0 - pal_ember.z * (1.0 - smoothstep(pal_ember.x, max(pal_ember.y, pal_ember.x + 1e-3), distance(wp.xz, cel_ember.xz)));
}
vec3 pal_leaf(vec3 a) { return pal_ramp(a, pal_leaf0, pal_leaf1, pal_leaf2, 1.0, 0.0, pal_vk0.x); }
// (a tree its own place on the ramp: s -1..1, a per-copy hash, moves t by up to 0.3: one tree crimson, the next orange or gold)
vec3 pal_leaf(vec3 a, vec3 wp, float s) { return pal_ramp(a, pal_leaf0, pal_leaf1, pal_leaf2, pal_keep(wp), 0.3 * s, pal_vk0.x); }
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
