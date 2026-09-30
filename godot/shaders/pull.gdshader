// Pulled into an ember arena (the old battle swirl, our way): the world
// twists in on itself toward the survivor and is drawn in, its colours
// splitting, while an ember burn eats it from the edges along a ragged
// front with a hot rim, leaving the dark (where the arena's name comes up).
// progress runs 0 to 1.
shader_type canvas_item;

uniform sampler2D screen : hint_screen_texture, filter_linear_mipmap;
uniform float progress = 0.0;
uniform float aspect = 1.7778;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }

float noise(vec2 p)
{
	vec2 i = floor(p), f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), u.x), mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), u.x), u.y);
}

float fbm(vec2 p)
{
	float v = 0.0, a = 0.5;
	for (int k = 0; k < 4; k++) { v += a * noise(p); p *= 2.03; a *= 0.5; }
	return v;
}

void fragment()
{
	float p = clamp(progress, 0.0, 1.0);
	vec2 d = SCREEN_UV - vec2(0.5);
	d.x *= aspect;
	float r = length(d);
	// The swirl, tighter toward the middle, and the world drawn in after it.
	float twist = p * p * 5.5 * (1.0 - smoothstep(0.0, 1.1, r));
	float s = sin(twist), c = cos(twist);
	vec2 dd = vec2(d.x * c - d.y * s, d.x * s + d.y * c) * (1.0 - 0.45 * p * p);
	dd.x /= aspect;
	vec2 uv = vec2(0.5) + dd;
	float split = 0.012 * p;
	vec3 col = vec3(texture(screen, uv + vec2(split, 0.0)).r, texture(screen, uv).g, texture(screen, uv - vec2(split, 0.0)).b);
	// A flash as it takes hold.
	col += vec3(1.0, 0.75, 0.45) * (1.0 - smoothstep(0.0, 0.12, p)) * 0.35;
	// The burn: in from the edges, ragged, a hot rim before the dark.
	float n = fbm(d * 6.0 + vec2(0.0, p * 2.0));
	float k = r * 1.15 + n * 0.4;
	float t = 1.65 - p * 2.0;
	float burned = smoothstep(t, t + 0.02, k);
	float rim = smoothstep(t - 0.14, t, k) * (1.0 - burned);
	vec3 ember = mix(vec3(1.0, 0.35, 0.06), vec3(1.0, 0.85, 0.5), rim * rim);
	col = mix(col, ember * 2.2, rim * 0.9);
	col *= (1.0 - burned) * (1.0 - 0.35 * p);
	COLOR = vec4(col, 1.0);
}
