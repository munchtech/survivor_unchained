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

varying vec3 wpos;

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec4 a = texture(atlas, UV);
	vec2 f = texture(field, ((wpos.xz + half_size) / step + 0.5) / res).rg;
	vec3 col = a.rgb;
	float l = dot(col, vec3(0.299, 0.587, 0.114));
	float sat = (max(col.r, max(col.g, col.b)) - min(col.r, min(col.g, col.b))) / max(max(col.r, max(col.g, col.b)), 1e-3);
	col *= mix(1.0, bone_k, smoothstep(0.3, 0.6, l) * (1.0 - smoothstep(0.25, 0.5, sat)));
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
