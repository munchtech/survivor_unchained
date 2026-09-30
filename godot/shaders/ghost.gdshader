// A person made of light and glass: a reflection left behind, an echo, a
// survivor walking half a ghost. Bright at the rim, faint through the body,
// bands of light climbing it; cracks spread across it as it is broken.
shader_type spatial;
render_mode unshaded, blend_add, cull_back, depth_draw_never, shadows_disabled;

uniform vec4 tint : source_color = vec4(0.55, 0.8, 1.0, 1.0);
uniform float fade = 1.0;
uniform float body = 0.12;
uniform float rim = 1.3;
uniform float crack = 0.0;
uniform float seed = 0.0;

varying vec3 wpos;

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

vec3 hash3(vec3 p) {
	p = vec3(dot(p, vec3(127.1, 311.7, 74.7)), dot(p, vec3(269.5, 183.3, 246.1)), dot(p, vec3(113.5, 271.9, 124.6)));
	return fract(sin(p) * 43758.5453);
}

// Distance to the nearest edge between cells: small along the cracks.
float cells(vec3 p) {
	vec3 i = floor(p), f = fract(p);
	float d1 = 8.0, d2 = 8.0;
	for (int x = -1; x <= 1; x++)
	for (int y = -1; y <= 1; y++)
	for (int z = -1; z <= 1; z++) {
		vec3 g = vec3(float(x), float(y), float(z));
		vec3 o = hash3(i + g);
		float d = length(g + o - f);
		if (d < d1) { d2 = d1; d1 = d; } else if (d < d2) { d2 = d; }
	}
	return d2 - d1;
}

void fragment() {
	float f = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 2.4);
	float bands = 0.5 + 0.5 * sin(wpos.y * 22.0 - TIME * 4.0 + seed * 6.0);
	float glint = smoothstep(0.94, 1.0, sin(wpos.y * 2.6 + wpos.x * 1.7 + wpos.z * 1.3 - TIME * 2.0 + seed * 3.0));
	float c = 0.0;
	if (crack > 0.01) {
		float e = cells(wpos * 4.0 + seed * 11.0);
		c = (1.0 - smoothstep(0.0, 0.06, e)) * smoothstep(0.0, 0.6, crack);
	}
	float a = body + f * rim + bands * 0.06 + glint * 0.5 + c * 1.6;
	ALBEDO = tint.rgb * a * fade;
}
