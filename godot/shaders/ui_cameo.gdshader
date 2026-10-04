// A cameo's picture (creation's cuts, faces and paints: Ui/CreateLook.cs):
// cut to a circle, darker toward its rim as a portrait in a deep frame; a
// cut's hair, painted grey, takes the colour chosen (its mask), as her hair's
// own shader dyes it; the one chosen a touch warmer.
shader_type canvas_item;

uniform sampler2D mask : hint_default_black;
uniform vec3 dye : source_color = vec3(1.0);
uniform float dyed = 0.0;
uniform float lit = 0.0;

void fragment() {
	vec4 c = texture(TEXTURE, UV);
	float m = texture(mask, UV).r * dyed;
	// (grey a half: the colour as it is; lighter and darker about it)
	c.rgb = mix(c.rgb, clamp(c.rgb * dye * 2.1, 0.0, 1.0), m);
	float r = length(UV - 0.5) * 2.0;
	c.a *= 1.0 - smoothstep(0.965, 1.0, r);
	c.rgb *= mix(1.0, 0.6, smoothstep(0.6, 1.0, r));
	c.rgb = mix(c.rgb, c.rgb * vec3(1.08, 1.0, 0.9), lit);
	COLOR = c;
}
