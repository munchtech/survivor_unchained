// UI 17, The Drowned Girl (--hud drowned), piece 4: the Flare as a live coal in the river's eddy (DgCoal).
// The coal is painted (art/ui/dg_river/coal_map.png, tools/uiforge/dg_coal.py): R the charcoal plates' light,
// G the cracks (how deep), B the plates' edges the cracks light. The heat rises from the coal's foot with the
// meter (the concept's flare_level read: hot below a soft wavering front, dark above, a few dull embers deep in
// the cracks); full, it blazes and breathes (about 2.6 s) with a halo on the bronze round it, which says
// "press Q". A press (burst: seconds since it) flashes it white-hot, throws a ring of light out over the river,
// and the coal goes dark, cooling through its last embers, to refill from the foot. Premultiplied: inside the
// coal is opaque, the light outside it is added.
shader_type canvas_item;
render_mode blend_premul_alpha;

uniform sampler2D coal : filter_linear_mipmap, repeat_disable;
uniform float level = 0.0;
/// the rect's half size, in coal radii (room for the halo and the flare-out's ring)
uniform float ext = 2.6;
/// seconds since the press; < 0 none
uniform float burst = -1.0;
/// the coal's radius in screen px (its edge's antialiasing)
uniform float px = 57.0;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p)
{
	vec2 i = floor(p), f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), f.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), f.x), f.y);
}

// heat 0..1.4 -> the fire's colour: dull red, red, orange, gold, white
vec3 ramp(float t)
{
	t = clamp(t, 0.0, 1.4);
	vec3 c0 = vec3(0.11, 0.012, 0.0), c1 = vec3(0.72, 0.10, 0.01), c2 = vec3(1.0, 0.42, 0.05), c3 = vec3(1.0, 0.78, 0.36), c4 = vec3(1.0, 0.97, 0.86);
	if (t < 0.3) return mix(c0, c1, t / 0.3);
	if (t < 0.6) return mix(c1, c2, (t - 0.3) / 0.3);
	if (t < 0.95) return mix(c2, c3, (t - 0.6) / 0.35);
	return mix(c3, c4, (t - 0.95) / 0.45);
}

void fragment()
{
	vec4 tint = COLOR;  // (the instrument's modulate: a callout's dimming)
	vec2 p = (UV * 2.0 - 1.0) * ext;
	float d = length(p);
	float t = TIME;
	float full = step(0.999, level);
	float breath = 0.5 + 0.5 * sin(t * 2.4);
	float bt = burst;
	float flash = bt >= 0.0 ? exp(-bt * 2.6) : 0.0;
	float cooling = bt >= 0.0 ? smoothstep(0.05, 0.25, bt) * (1.0 - smoothstep(0.6, 1.8, bt)) : 0.0;

	vec4 m = texture(coal, clamp(p * 0.5 + 0.5, 0.0, 1.0));
	float rock = m.r, crack = m.g, edge = m.b;

	// the heat front, rising from the foot with the level, its edge wavering
	float s = 1.0 - 2.0 * level;
	float wob = (noise(vec2(p.x * 3.0 + 7.0, t * 0.7)) - 0.5) * 0.12;
	float y = p.y + wob;
	float below = smoothstep(s - 0.05, s + 0.12, y);
	below = level >= 0.999 ? 1.0 : level <= 0.001 ? 0.0 : below;
	float depth = clamp((y - s) / 0.7, 0.0, 1.0);
	float flick = 0.82 + 0.18 * noise(p * 4.0 + vec2(0.0, -t * 0.9));
	float heat = below * (0.64 + 0.30 * depth) * flick;
	heat += full * (0.10 + 0.16 * breath);
	float front = exp(-pow((y - s) / 0.08, 2.0)) * step(0.001, level) * (1.0 - full);
	heat += front * 0.45;
	// above it the coal is dark: a few dull embers deep in the cracks
	heat = max(heat, 0.05 * smoothstep(0.55, 0.85, noise(p * 5.0 + vec2(t * 0.15, 3.0))));
	heat += flash * 1.25 + cooling * 0.30 * smoothstep(0.4, 0.9, noise(p * 6.0 + vec2(0.0, t * 2.0)));

	vec3 col = vec3(rock) * vec3(0.34, 0.31, 0.30);
	col += edge * ramp(heat) * 0.55 * clamp(heat, 0.0, 1.0);
	col = mix(col, ramp(heat * (0.55 + 0.5 * crack)), smoothstep(0.10, 0.55, crack));
	col += flash * vec3(1.0, 0.70, 0.35) * 0.55 * (1.0 - crack);

	// round, its edge sunk in the bronze
	float aa = 1.4 / px;
	float inside = 1.0 - smoothstep(1.0 - aa, 1.0 + aa, d);
	col *= 1.0 - 0.6 * smoothstep(0.80, 1.0, d);

	// outside: its light on the bronze round it, breathing when full; the flare-out's ring
	float glow = (0.08 + 0.6 * level * level) * (1.0 + full * (0.25 + 0.55 * breath)) + flash * 2.2;
	vec3 add = vec3(1.0, 0.46, 0.11) * glow * exp(-max(d - 1.0, 0.0) / 0.20) * 0.5 * (1.0 - inside);
	if (bt >= 0.0)
	{
		float rr = 1.0 + bt * 3.4;
		float ring = exp(-pow((d - rr) / (0.10 + 0.22 * bt), 2.0)) * exp(-bt * 2.2) * 1.6;
		add += vec3(1.0, 0.74, 0.38) * ring * (1.0 - inside);
	}
	add += inside * full * breath * vec3(0.20, 0.08, 0.015);
	add *= 1.0 - smoothstep(ext - 0.5, ext, d);
	COLOR = vec4((col * inside + add) * tint.rgb * tint.a, inside * tint.a);
}
