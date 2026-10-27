// (E8) The far castle (C01 s8a, about 265 m off; OwnProps.Far): the props atlas times the vertex colours, the
// zone's depth fog off and a haze of its own in its place (at that range Godot's fog left a flat fog-coloured
// shape with its windows gone), so the silhouette stays a value step above the foreground's darks and under the
// sky; the lit windows (vertex alpha 0) glow their own colour, unhazed.
shader_type spatial;
render_mode fog_disabled;

uniform sampler2D albedo_tex : source_color, filter_linear_mipmap_anisotropic;
uniform vec3 haze_color : source_color = vec3(0.13, 0.17, 0.27);
uniform float haze : hint_range(0.0, 1.0) = 0.55;
uniform float glow_energy = 5.0;

void fragment() {
	float win = 1.0 - COLOR.a;
	vec3 base = texture(albedo_tex, UV).rgb * COLOR.rgb;
	ALBEDO = base * (1.0 - win) * (1.0 - haze);
	ROUGHNESS = 0.92;
	EMISSION = haze_color * haze * (1.0 - win) + COLOR.rgb * win * glow_energy;
}
