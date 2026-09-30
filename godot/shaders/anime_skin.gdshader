// Her skin (Actors/People.cs, a woman in her own body): donizaki's painted
// texture, toned to the skin chosen. Where the paint is her skin's colour it
// takes the choice (as bright as the paint was, so its shading stays); the
// eyes, lips and brows keep their paint. A rim of light at the edge, as on
// everyone.
shader_type spatial;

uniform sampler2D tex : source_color, filter_linear_mipmap_anisotropic;
// The skin chosen (the fair tone by default: People.Fair).
uniform vec3 skin : source_color = vec3(0.949, 0.769, 0.659);
uniform float rim_amount = 0.45;
uniform float rim_tint = 0.35;

void fragment() {
	vec3 t = texture(tex, UV).rgb;
	// Her paint's skin colour, linear.
	vec3 base = pow(vec3(232.0, 216.0, 192.0) / 255.0, vec3(2.2));
	float m = 1.0 - smoothstep(0.035, 0.1, distance(t, base));
	ALBEDO = mix(t, t / base * skin, m);
	ROUGHNESS = 0.62;
	SPECULAR = 0.35;
	RIM = rim_amount;
	RIM_TINT = rim_tint;
}
