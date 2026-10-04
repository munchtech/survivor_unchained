// A ribbon of light (src/Fx/Ribbons.cs): a trail behind a thing in flight,
// a bolt of lightning, a beam, a thread. UV.x runs along it (0 the tail, 1
// the head), UV.y across it; COLOR is its colour and how much of it is left
// at that point; UV2 is its strength (above 1 to bloom) and its style:
// 0 glow, 1 flame, 2 bolt, 3 wisp, 4 steel, 5 frost. Soft across, so no
// edge is ever hard; the tail tapers to nothing in the mesh itself. Drawn
// over the crowd: seen from above, bodies would hide a flight at chest height.
shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, depth_test_disabled, cull_disabled, shadows_disabled, fog_disabled;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p) {
	vec2 i = floor(p), f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
}

void fragment() {
	int style = int(UV2.y + 0.5);
	float across = abs(UV.y * 2.0 - 1.0);
	float along = UV.x;
	float strength = UV2.x * COLOR.a;
	vec3 col = COLOR.rgb;
	float body = 1.0 - smoothstep(0.0, 1.0, across);
	float core = exp(-across * across * 22.0);
	float light;
	vec3 tint = col;
	if (style == 1) {
		// Flame: tongues that break up toward the tail and run backwards.
		float n = noise(vec2(along * 9.0 - TIME * 7.0, UV.y * 3.0 + TIME * 2.0));
		float n2 = noise(vec2(along * 21.0 - TIME * 11.0, UV.y * 6.0));
		float flick = smoothstep(0.25 + (1.0 - along) * 0.5, 0.9, n * 0.65 + n2 * 0.45);
		light = body * mix(0.35, 1.25, flick) + core * 1.2 * along;
		// Hotter, paler at the head; the colour's own deeper hue behind.
		tint = mix(col * vec3(1.0, 0.55, 0.3), mix(col, vec3(1.0, 0.92, 0.7), 0.5), smoothstep(0.3, 1.0, along) * core + 0.15);
	} else if (style == 2) {
		// Bolt: a white-hot thread in a coloured haze.
		float thread = exp(-across * across * 90.0);
		light = thread * 2.6 + body * body * 0.55;
		tint = mix(col, vec3(1.0), thread * 0.75);
	} else if (style == 3) {
		// Wisp: smoke-soft, its edges eaten by moving noise.
		float n = noise(vec2(along * 6.0 - TIME * 2.5, UV.y * 2.5 + TIME * 0.8));
		float edge = smoothstep(0.15, 0.85, n + (1.0 - across) * 0.6 - 0.25);
		light = body * edge * 0.95 + core * 0.35;
	} else if (style == 4) {
		// Steel: a thin bright streak, a glint at its head.
		float thread = exp(-across * across * 40.0);
		light = thread * (0.6 + 1.6 * pow(along, 4.0)) + body * 0.12 * along;
		tint = mix(col, vec3(1.0), thread * pow(along, 2.0) * 0.6);
	} else if (style == 5) {
		// Frost: a pale core and glittering points that wink.
		vec2 cellp = vec2(along * 40.0, UV.y * 4.0);
		float h = hash(floor(cellp));
		float glint = step(0.86, h) * (0.5 + 0.5 * sin(TIME * 18.0 + h * 40.0)) * body;
		light = body * 0.55 + core * 0.9 + glint * 2.2;
		tint = mix(col, vec3(1.0), core * 0.4 + glint * 0.6);
	} else {
		light = body * 0.6 + core * 1.1;
	}
	ALBEDO = tint * light * strength;
}
