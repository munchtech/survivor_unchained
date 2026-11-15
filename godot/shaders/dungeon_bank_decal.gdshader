// The den's painted root clusters on the banks (src/World/DungeonDress.BankDecals.cs): the roots of bank_decals.png
// (alpha >= 0.6, scissor) in the floor's own shade, cel-lit as the floor is. The soft contact shadow is the other
// surface (dungeon_bank_shadow.gdshader).
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

varying vec3 wpos;

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec4 a = texture(atlas, UV);
	vec2 f = texture(field, ((wpos.xz + half_size) / step + 0.5) / res).rg;
	vec3 col = a.rgb;
	col *= mix(0.45, 1.0, smoothstep(0.0, 2.2, f.x));
	col *= mix(1.0, 0.05, 1.0 - smoothstep(0.0, 0.45, f.y));
	NORMAL = normalize((VIEW_MATRIX * vec4(0.0, 1.0, 0.0, 0.0)).xyz);
	ALBEDO = col * decal_lift;
	ALPHA = a.a;
	ALPHA_SCISSOR_THRESHOLD = 0.6;
	ROUGHNESS = 0.95;
	CEL_FRAGMENT;
}
