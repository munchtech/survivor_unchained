// An eye colour to choose, as an iris (Ui/CreateLook.cs's beads): her own
// iris's paint, dyed as her eye shader dyes it (shaders/heroine_eye.gdshader:
// its light and dark kept, the iris's colour outside and the ring's round the
// pupil), cut to a circle, a catchlight up and to the left.
shader_type canvas_item;

uniform float recolour = 1.0;
uniform vec3 iris_colour : source_color = vec3(0.3, 0.42, 0.22);
uniform vec3 ring_colour : source_color = vec3(0.62, 0.42, 0.16);
uniform float ring = 0.56;
const float PAINT_LIGHT = 0.12;

vec3 to_linear(vec3 c) { return mix(c / 12.92, pow((c + 0.055) / 1.055, vec3(2.4)), step(0.04045, c)); }
vec3 to_srgb(vec3 c) { return mix(c * 12.92, 1.055 * pow(c, vec3(1.0 / 2.4)) - 0.055, step(0.0031308, c)); }

void fragment() {
	// (the paint's iris fills 0.824 of its square)
	vec2 d = (UV - 0.5) * 2.0;
	float r = length(d);
	vec2 uv = vec2(0.5) + d * 0.412;
	vec3 ir = to_linear(texture(TEXTURE, uv).rgb);
	if (recolour > 0.0) {
		float lum = dot(ir, vec3(0.2126, 0.7152, 0.0722));
		vec3 hue = mix(to_linear(ring_colour), to_linear(iris_colour), smoothstep(ring - 0.1, ring + 0.12, r));
		vec3 own = clamp(ir / max(lum, 1e-4), vec3(0.5), vec3(1.6));
		ir = mix(ir, hue * (lum / PAINT_LIGHT) * mix(vec3(1.0), own, 0.15), recolour);
	}
	vec3 col = to_srgb(clamp(ir, 0.0, 1.0));
	// The pupil, the dark ring at the iris's edge, a catchlight.
	col *= 1.0 - smoothstep(0.26, 0.24, r);
	col *= 1.0 - 0.45 * smoothstep(0.8, 1.0, r);
	col += vec3(0.9) * (1.0 - smoothstep(0.08, 0.13, length(d - vec2(-0.32, -0.36))));
	COLOR = vec4(col, 1.0 - smoothstep(0.95, 1.0, r));
}
