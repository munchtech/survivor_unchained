// UI 17, The Drowned Girl (--hud drowned): the Flare as a live coal held in the river's eddy (DgCoal). Round 2: a
// banked ember of real charcoal (art/ui/dg_meters/coal_map.png, tools/uiforge/dg_coal.py): R the plates' light, G the
// cracks (how deep: the wide fissures near 1, the hairlines low), B the plate edges and faces the cracks light, A its
// lumpy silhouette. It sits low in the eddy's hole (k: its map's half size, off: its middle, in hole radii); round it,
// the hole is the eddy's dark cup, lit by the coal from below.
// The heat rises from the coal's foot with the meter (hot below a soft wavering front, dark above with a few dull
// embers deep in the fissures). Hotter means the deep fissures go gold then white at their cores while the hairlines
// stay red, and the plate edges glow. Full, it breathes (about 2.6 s) and lays orange light on the eddy's bronze,
// heaviest on the lip below it: "press Q" (its sparks are DgSparks). A press (burst: seconds since it) flashes it
// white, the light bursting out over the bronze, then it goes dark, its last embers cooling, to refill from the foot
// (the embers and ash it throws are DgSparks'). Premultiplied: inside the hole it is opaque, the light outside added.
shader_type canvas_item;
render_mode blend_premul_alpha;

uniform sampler2D coal : filter_linear_mipmap, repeat_disable;
uniform float level = 0.0;
/// the rect's half size, in hole radii (room for the light it lays on the bronze)
uniform float ext = 2.6;
/// seconds since the press; < 0 none
uniform float burst = -1.0;
/// the hole's radius in screen px (its edge's antialiasing)
uniform float px = 57.0;
uniform float k = 0.98;
uniform vec2 off = vec2(0.0, 0.2);

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
	vec3 c0 = vec3(0.10, 0.010, 0.0), c1 = vec3(0.66, 0.08, 0.01), c2 = vec3(1.0, 0.38, 0.04), c3 = vec3(1.0, 0.74, 0.30), c4 = vec3(1.0, 0.97, 0.88);
	if (t < 0.3) return mix(c0, c1, t / 0.3);
	if (t < 0.62) return mix(c1, c2, (t - 0.3) / 0.32);
	if (t < 0.98) return mix(c2, c3, (t - 0.62) / 0.36);
	return mix(c3, c4, (t - 0.98) / 0.42);
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
	float flash = bt >= 0.0 ? exp(-bt * 4.5) : 0.0;
	float cooling = bt >= 0.0 ? smoothstep(0.05, 0.3, bt) * (1.0 - smoothstep(0.7, 2.0, bt)) : 0.0;

	vec2 q = (p - off) / k;            // the coal's own space: -1..1 across its map
	vec2 cuv = q * 0.5 + 0.5;
	bool onmap = all(greaterThanEqual(cuv, vec2(0.0))) && all(lessThanEqual(cuv, vec2(1.0)));
	vec4 m = onmap ? texture(coal, cuv) : vec4(0.0);
	float rock = m.r, crack = m.g, edge = m.b, sil = m.a;
	// the coal's light reaching round it: its silhouette blurred (a coarse mip)
	float near = onmap ? textureLod(coal, cuv, 4.0).a : 0.0;
	near = max(near, onmap ? textureLod(coal, cuv, 5.5).a * 0.8 : 0.0);

	// the heat front, rising from the coal's foot with the level, its edge wavering (the coal's own height: q.y)
	float s = 1.0 - 2.0 * level;
	float wob = (noise(vec2(q.x * 3.0 + 7.0, t * 0.7)) - 0.5) * 0.14;
	float y = q.y * 1.15 + wob;
	float below = smoothstep(s - 0.05, s + 0.14, y);
	below = level >= 0.999 ? 1.0 : level <= 0.001 ? 0.0 : below;
	float depth = clamp((y - s) / 0.8, 0.0, 1.0);
	float flick = 0.84 + 0.16 * noise(q * 4.0 + vec2(0.0, -t * 0.9));
	float heat = below * (0.46 + 0.22 * depth) * flick;
	heat += full * (0.50 + 0.18 * breath);
	float front = exp(-pow((y - s) / 0.09, 2.0)) * step(0.001, level) * (1.0 - full);
	heat += front * 0.35;
	// above it the coal is dark: a few dull embers deep in the fissures
	heat = max(heat, 0.10 * smoothstep(0.5, 0.85, noise(q * 5.0 + vec2(t * 0.15, 3.0))) * smoothstep(0.5, 0.9, crack));
	heat += flash * 1.3 + cooling * 0.32 * smoothstep(0.4, 0.9, noise(q * 6.0 + vec2(0.0, t * 2.0)));

	// the plates: charcoal and ash; the edges the cracks light; the cracks, deeper = hotter (white cores in the wide)
	vec3 col = vec3(rock) * vec3(0.36, 0.33, 0.32);
	float glow = clamp(heat, 0.0, 1.0);
	col += edge * ramp(heat * 0.62) * 0.75 * glow;
	float cheat = heat * (0.42 + 0.78 * crack);
	col = mix(col, ramp(cheat), smoothstep(0.08, 0.45, crack) * smoothstep(0.0, 0.12, heat));
	col += flash * vec3(1.0, 0.86, 0.66) * 0.75;
	// its foot sinks into the cup's shadow
	col *= 1.0 - 0.55 * smoothstep(0.55, 1.0, (p.y - off.y) / k + 0.15) * (1.0 - flash);

	// the eddy's cup round it: dark weathered bronze, deeper toward the middle, lit by the coal from below
	float lit = (0.10 + 0.9 * level * level) * (1.0 + full * (0.2 + 0.4 * breath)) + flash * 2.5;
	vec3 cup = mix(vec3(0.020, 0.030, 0.028), vec3(0.075, 0.070, 0.055), smoothstep(0.5, 1.0, d));
	cup += vec3(1.0, 0.42, 0.10) * near * lit * 0.32 * (0.6 + 0.4 * smoothstep(-0.6, 0.8, p.y));
	cup *= 1.0 - 0.5 * smoothstep(0.86, 1.0, d);

	float aa = 1.4 / px;
	float inside = 1.0 - smoothstep(1.0 - aa, 1.0 + aa, d);
	vec3 hole = mix(cup, col, sil);

	// outside: its light on the eddy's bronze, heaviest on the lip below it; the press's light bursting out
	float halo = (0.06 + 0.55 * level * level) * (1.0 + full * (0.7 + 0.6 * breath));
	float fall = exp(-max(d - 1.0, 0.0) / (0.28 + 0.10 * full)) * (0.55 + 0.45 * smoothstep(-0.8, 0.9, p.y));
	vec3 add = vec3(1.0, 0.45, 0.10) * halo * fall * 0.55;
	add += vec3(1.0, 0.80, 0.55) * flash * 1.5 * exp(-max(d - 1.0, 0.0) / (0.25 + 0.9 * bt));
	add *= 1.0 - inside;
	add *= 1.0 - smoothstep(ext - 0.6, ext, d);
	COLOR = vec4((hole * inside + add) * tint.rgb * tint.a, inside * tint.a);
}
