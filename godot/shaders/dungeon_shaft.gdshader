// A pale shaft of daylight through the den's roof (src/World/DungeonLight.cs): an additive cone, soft at its sides,
// strongest a little above the floor and gone toward the roof, with slow motes drifting in it.
shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, cull_back, shadows_disabled, fog_disabled;

uniform vec3 tint : source_color = vec3(0.86, 0.9, 0.94);
uniform float strength = 0.3;   // (lead 6: 0.55 read as hard white cones against the targets' soft pale rays)
uniform float height = 15.0;

varying float hf;
varying vec3 wpos;

float hash2(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float vnoise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash2(i), hash2(i + vec2(1.0, 0.0)), f.x), mix(hash2(i + vec2(0.0, 1.0)), hash2(i + vec2(1.0, 1.0)), f.x), f.y);
}

void vertex() {
	hf = VERTEX.y / height + 0.5;
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	float face = abs(dot(normalize(NORMAL), normalize(VIEW)));
	float a = pow(face, 4.0);
	a *= smoothstep(0.0, 0.12, hf) * (1.0 - smoothstep(0.35, 0.95, hf));
	float motes = 0.75 + 0.25 * vnoise(vec2(wpos.x * 1.3 + wpos.z, wpos.y * 0.5 - TIME * 0.15));
	// rays: streaks along the shaft (by the angle round it), so it reads as light through a ragged hole, not a tube
	float ang = atan(wpos.x - MODEL_MATRIX[3].x, wpos.z - MODEL_MATRIX[3].z);
	float rays = 0.45 + 0.9 * smoothstep(0.35, 0.8, vnoise(vec2(ang * 5.0, hf * 1.5)));
	ALBEDO = tint * strength * a * motes * rays;
}
