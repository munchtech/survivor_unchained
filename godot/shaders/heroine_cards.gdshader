// Her brows and lashes: cards cut to their alpha as alpha to coverage cut them
// under MSAA (Godot's scene_forward_aa_inc.glsl: nothing under 0.35, the edge a
// pixel soft round 0.65, thin cards kept their weight far off), by a threshold
// that moves every frame (coverage.gdshaderinc), so a temporal smoothing (FSR 2)
// draws them soft and still without MSAA (src/View/Coverage.cs).
shader_type spatial;
render_mode cull_disabled;

uniform sampler2D albedo_tex : source_color, filter_linear_mipmap, repeat_enable;
uniform vec4 albedo_color : source_color = vec4(1.0);
uniform float cut = 0.35;
uniform float edge = 0.3;

#include "res://shaders/coverage.gdshaderinc"

void fragment() {
	vec4 c = texture(albedo_tex, UV) * albedo_color;
	if (c.a < cut) discard;
	vec2 tc = UV * vec2(textureSize(albedo_tex, 0));
	vec2 dx = dFdx(tc), dy = dFdy(tc);
	float mip = max(0.0, 0.5 * log2(max(dot(dx, dx), dot(dy, dy))));
	float a = c.a * (1.0 + mip * 0.25);
	float cover = clamp((a - (cut + edge)) / max(fwidth(a), 0.0001) + 0.5, 0.0, 1.0);
	if (cover < coverage_cut(FRAGCOORD.xy)) discard;
	ALBEDO = c.rgb;
	ROUGHNESS = 0.8;
}
