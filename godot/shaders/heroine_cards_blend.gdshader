// Her lashes (and brow cards, on the faces that have them) blended to their
// paint's own alpha, not cut: soft and still in every frame under FSR 2 without
// MSAA, and the paint's soft tips shown as painted. Far off, where a card is
// thinner than its texels, the alpha is raised a quarter for each mip level, so
// the lashes keep their weight at play distance (as alpha to coverage did).
// (src/Actors/HairDraw.cs)
shader_type spatial;
render_mode blend_mix, depth_prepass_alpha, cull_disabled;

uniform sampler2D albedo_tex : source_color, filter_linear_mipmap, repeat_enable;
uniform vec4 albedo_color : source_color = vec4(1.0);
// Lashes lit as her lid's skin is (1; brows 0, as they lie): a lash card stands off the lid edge-on to the
// light, its own normals down and back, and it took almost none (its dark brown paint rendered black, a
// drawn eyeliner). Its normal turned to face the camera and a little up, as the lid's skin under it does.
uniform float skin_lit = 0.0;

void fragment() {
	vec4 c = texture(albedo_tex, UV) * albedo_color;
	if (c.a < 0.004) discard;
	vec2 tc = UV * vec2(textureSize(albedo_tex, 0));
	vec2 dx = dFdx(tc), dy = dFdy(tc);
	float mip = max(0.0, 0.5 * log2(max(dot(dx, dx), dot(dy, dy))));
	ALPHA = clamp(c.a * (1.0 + mip * 0.25), 0.0, 1.0);
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
