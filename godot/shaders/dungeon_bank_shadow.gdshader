// The soft contact shadow of the den's bank decals (alpha 0.2-0.58 of bank_decals.png): a darkening of what lies under it,
// x0.55 at alpha 0.5. Roots (alpha >= 0.6) are the other surface.
shader_type spatial;
render_mode cull_disabled, unshaded, blend_mul, depth_draw_never;

uniform sampler2D atlas : source_color, filter_linear_mipmap_anisotropic, repeat_disable;

void fragment() {
	float a = texture(atlas, UV).a;
	if (a < 0.2 || a >= 0.58) discard;
	ALBEDO = vec3(mix(1.0, 0.55, clamp((a - 0.2) / 0.3, 0.0, 1.0)));
	ALPHA = 1.0;
}
