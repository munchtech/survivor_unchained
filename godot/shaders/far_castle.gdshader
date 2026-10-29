// (E8) The far castle (C01 s8a; OwnProps.Far): the props atlas times the vertex colours, the zone's depth fog off
// and a haze of its own in its place (at that range Godot's fog left a flat fog-coloured shape with its windows
// gone); the lit window (vertex alpha 0) glows its own colour, unhazed.
// (E8 r2) Restaged 650 m off on a ridge: a heavier haze (a pale shape, just under the sky), and a valley mist that
// thickens below mist_top (world y) so the ridge under it fades into the air and the castle stands clear of the gate.
shader_type spatial;
render_mode fog_disabled;

uniform sampler2D albedo_tex : source_color, filter_linear_mipmap_anisotropic;
uniform vec3 haze_color : source_color = vec3(0.13, 0.17, 0.27);
uniform float haze : hint_range(0.0, 1.0) = 0.74;
uniform vec3 mist_color : source_color = vec3(0.15, 0.21, 0.34);
uniform float mist_top = 112.0;
uniform float mist_depth = 30.0;
uniform float glow_energy = 5.0;
uniform float shown = 1.0;  // (E8 r2) 0 by day and dawn (OwnProps.FarShown)

varying float wy;

void vertex() {
	wy = (MODEL_MATRIX * vec4(VERTEX, 1.0)).y;
}

void fragment() {
	if (shown < 0.5) discard;
	float win = 1.0 - COLOR.a;
	float h = mix(haze, 0.97, clamp((mist_top - wy) / mist_depth, 0.0, 1.0));
	vec3 base = texture(albedo_tex, UV).rgb * COLOR.rgb;
	ALBEDO = base * (1.0 - win) * (1.0 - h);
	ROUGHNESS = 0.92;
	float m = clamp((mist_top - wy) / mist_depth, 0.0, 1.0);
	EMISSION = mix(haze_color, mist_color, m) * h * (1.0 - win) + COLOR.rgb * win * glow_energy;
}
