// Her brows and lashes: cards cut to their alpha as alpha to coverage cut them
// under MSAA (Godot's scene_forward_aa_inc.glsl: nothing under 0.35, the edge a
// pixel soft round 0.65, thin cards kept their weight far off), by a threshold
// that moves every frame (coverage.gdshaderinc), so a temporal smoothing (FSR 2)
// draws them soft and still without MSAA (src/View/Coverage.cs).
shader_type spatial;
render_mode cull_disabled;

uniform sampler2D albedo_tex : source_color, filter_linear_mipmap, repeat_enable;
uniform vec4 albedo_color : source_color = vec4(1.0);
// Lashes lit as her lid's skin is (1; brows 0, as they lie): a lash card stands off the lid edge-on to the
// light, its own normals down and back, and it took almost none (its dark brown paint rendered black, a
// drawn eyeliner). Its normal turned to face the camera and a little up, as the lid's skin under it does.
uniform float skin_lit = 0.0;
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
	// (turned to the camera and a little up, as the lid under them, so the light from above reaches them as
	// it reaches the lid (to the camera alone they took only the sky's light, a purple-black line); and little
	// sheen, a lash's is a fine hair's (at 0.5 a grey-lilac film over the band))
	if (skin_lit > 0.0) {
		vec3 up = (VIEW_MATRIX * vec4(0.0, 1.0, 0.0, 0.0)).xyz;
		NORMAL = normalize(mix(NORMAL, normalize(VIEW + up * 0.5), skin_lit));
	}
	ROUGHNESS = 0.8;
	SPECULAR = mix(0.5, 0.1, skin_lit);
}
