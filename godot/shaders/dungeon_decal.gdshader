// The den's floor decals (src/World/DungeonDress.Decals.cs): the painted atlas (tools/look/den_decals.py) cut by its
// alpha, in the floor's own shade (darker at the walls' feet, gone into the pits' dark), cel-lit as the floor is.
shader_type spatial;
render_mode cull_disabled;
#define CEL_INK 1
#include "res://shaders/cel.gdshaderinc"

uniform sampler2D atlas : source_color, filter_linear_mipmap_anisotropic, repeat_disable;
uniform sampler2D field : filter_linear, repeat_disable;   // r: metres inside the walkable edge; g: metres outside the holes
uniform float half_size = 100.0;
uniform float step = 1.0;
uniform float res = 200.0;
uniform float decal_lift = 1.0;
// (round 8) the pale litter (bone, skull, pale fur) a step down from white: the even white sprinkle read as noise; the
// targets' bones sit at a dirty ivory, about the lit floor's own value. --den-bone sets it.
uniform float bone_k = 0.62;
// (den r17 D3) the bone kinds' grade (DungeonDress.Decals.cs BoneGrade; COLOR.r 1 marks them): x Oklab L scale, y chroma
// scale, z hue turn in degrees, w on. The bone_k branch above gated on the LINEAR atlas (bones' body at L .17) and missed them.
uniform vec4 bone_grade = vec4(1.0, 1.0, 0.0, 0.0);
// (and its highlight knee: x the Oklab L above which the rise is kept at y; the lit bones rendered at the tonemap's top, the shaded ones need their value)
uniform vec2 bone_knee = vec2(1.0, 1.0);

varying vec3 wpos;
varying float bone_m;

vec3 dd_oklab(vec3 c) {
	vec3 lms = pow(max(mat3(vec3(0.4122214708, 0.2119034982, 0.0883024619), vec3(0.5363325363, 0.6806995451, 0.2817188376),
		vec3(0.0514459929, 0.1073969566, 0.6299787005)) * max(c, vec3(0.0)), vec3(0.0)), vec3(1.0 / 3.0));
	return mat3(vec3(0.2104542553, 1.9779984951, 0.0259040371), vec3(0.7936177850, -2.4285922050, 0.7827717662),
		vec3(-0.0040720468, 0.4505937099, -0.8086757660)) * lms;
}
vec3 dd_linear(vec3 o) {
	vec3 m = mat3(vec3(1.0, 1.0, 1.0), vec3(0.3963377774, -0.1055613458, -0.0894841775), vec3(0.2158037573, -0.0638541728, -1.2914855480)) * o;
	m = m * m * m;
	return clamp(mat3(vec3(4.0767416621, -1.2684380046, -0.0041960863), vec3(-3.3077115913, 2.6097574011, -0.7034186147),
		vec3(0.2309699292, -0.3413193965, 1.7076147010)) * m, vec3(0.0), vec3(1.0));
}

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	bone_m = bone_grade.w > 0.0 ? COLOR.r : 0.0;
}

void fragment() {
	vec4 a = texture(atlas, UV);
	vec2 f = texture(field, ((wpos.xz + half_size) / step + 0.5) / res).rg;
	vec3 col = a.rgb;
	float l = dot(col, vec3(0.299, 0.587, 0.114));
	float sat = (max(col.r, max(col.g, col.b)) - min(col.r, min(col.g, col.b))) / max(max(col.r, max(col.g, col.b)), 1e-3);
	col *= mix(1.0, bone_k, smoothstep(0.3, 0.6, l) * (1.0 - smoothstep(0.25, 0.5, sat)) * (1.0 - bone_m));
	if (bone_m > 0.5) {
		vec3 o = dd_oklab(col);
		float hr = radians(bone_grade.z), cs = cos(hr), sn = sin(hr);
		vec2 ab = vec2(o.y * cs - o.z * sn, o.y * sn + o.z * cs) * bone_grade.y;
		float lk = o.x - max(o.x - bone_knee.x, 0.0) * (1.0 - bone_knee.y);
		col = dd_linear(vec3(lk * bone_grade.x, ab));
	}
	col *= mix(vec3(1.0), vec3(0.98, 0.94, 0.86), smoothstep(0.3, 0.6, l));
	col *= mix(0.45, 1.0, smoothstep(0.0, 2.2, f.x));
	// (den r15 D) pale litter in the shade warms toward umber (it read grey-violet, hue ~210): its own material, not the grade
	col *= mix(mix(vec3(1.0), vec3(1.08, 0.94, 0.74), smoothstep(0.25, 0.5, l)), vec3(1.0), smoothstep(0.0, 2.2, f.x));
	col *= mix(1.0, 0.05, 1.0 - smoothstep(0.0, 0.45, f.y));
	// (both faces lit as the floor: the normal is the world's up whichever side the camera sees)
	NORMAL = normalize((VIEW_MATRIX * vec4(0.0, 1.0, 0.0, 0.0)).xyz);
	ALBEDO = col * decal_lift;
	ALPHA = a.a;
	ALPHA_SCISSOR_THRESHOLD = 0.5;
	ROUGHNESS = 0.95;
	CEL_FRAGMENT;
}
