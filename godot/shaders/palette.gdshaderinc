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

vec3 pal_ramp(vec3 albedo, vec4 d, vec4 m, vec4 l) {
	if (d.w <= 0.0) return albedo;
	float v = sqrt(max(dot(albedo, vec3(0.2126, 0.7152, 0.0722)), 0.0));
	float t = clamp((v - m.w) / max(l.w - m.w, 1e-3), 0.0, 1.0);
	vec3 r = t < 0.5 ? mix(d.rgb, m.rgb, t * 2.0) : mix(m.rgb, l.rgb, t * 2.0 - 1.0);
	return mix(albedo, r, d.w);
}
vec3 pal_leaf(vec3 a) { return pal_ramp(a, pal_leaf0, pal_leaf1, pal_leaf2); }
vec3 pal_grass(vec3 a) { return pal_ramp(a, pal_grass0, pal_grass1, pal_grass2); }
vec3 pal_ground(vec3 a) { return pal_ramp(a, pal_ground0, pal_ground1, pal_ground2); }
vec3 pal_path(vec3 a) { return pal_ramp(a, pal_path0, pal_path1, pal_path2); }
vec3 pal_stone(vec3 a) { return pal_ramp(a, pal_stone0, pal_stone1, pal_stone2); }
vec3 pal_bark(vec3 a) { return pal_ramp(a, pal_bark0, pal_bark1, pal_bark2); }
#endif
