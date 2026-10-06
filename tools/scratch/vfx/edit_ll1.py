p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a191ed81e2df462cf\godot\shaders\loot_beam.gdshader"
s = open(p, encoding="utf-8").read()
start = s.index("void fragment() {")
end = s.index("\t// Seen dimmed behind what stands well in front of it")
new = '''void fragment() {
	float x = at.x, y = at.y;
	float H = max(tall, 0.01);
	float u = clamp(y / H, 0.0, 1.0);
	// Born out of the ground with no line where it meets it.
	float rise = smoothstep(-0.04, 0.12, y);
	float shimmer = 0.86 + 0.14 * sin(y * 1.9 - TIME * 2.6 + seed * 6.28);
	// Coloured light is palest at its heart and deepest where it thins: the line in its band's
	// colour, the glow and the pool round it deeper still (a pale glow by day reads as haze).
	float top = max(max(tint.r, tint.g), max(tint.b, 1e-3));
	vec3 deep = tint * tint / top;
	vec3 light = vec3(0.0);
	float veil = 0.0;

	if (kind < 1.5) {
		// Rare: a low glow, a fine bright line in it, its light pooled at its foot.
		float fade = rise * pow(1.0 - u, 1.5);
		light = (tint * g(x, 0.026) * 1.0 + deep * g(x, 0.13) * 0.45) * fade * shimmer + deep * pool(half_w * 0.6) * 0.32;
		veil = (g(x, 0.05) * 0.3 + g(x, 0.16) * 0.12) * fade + pool(half_w * 0.6) * 0.1;
	} else if (kind < 2.5) {
		// Epic: thinner and taller, a line of light in a narrow glow, a mote climbing it now and then.
		float fade = rise * pow(1.0 - u, 1.25);
		float up = motes(0.1, 1.1, 0.7) * fade;
		light = (tint * (g(x, 0.022) * 1.1 + up * 0.8) + deep * (g(x, 0.1) * 0.42 + g(x, 0.34) * 0.1)) * fade * shimmer
			+ deep * pool(half_w * 0.6) * 0.34;
		veil = (g(x, 0.045) * 0.32 + g(x, 0.14) * 0.12) * fade + pool(half_w * 0.6) * 0.1;
	} else if (kind < 3.5) {
		// Set: two strands twisting about each other, the one in front the brighter (that is what
		// reads as a twist and not as two lines), a faint glow between them.
		float fade = rise * pow(1.0 - u, 1.1);
		float amp = 0.15 * (1.0 - 0.45 * u) * smoothstep(-0.05, 0.35, y);
		float ph = y * 3.3 - TIME * 2.1 + seed * 6.28;
		float s1 = amp * sin(ph);
		float front = cos(ph);
		float w1 = 0.45 + 0.55 * front, w2 = 0.45 - 0.55 * front;
		float lines = g(x - s1, 0.02) * max(w1, 0.08) + g(x + s1, 0.02) * max(w2, 0.08);
		float halo = g(x - s1, 0.07) * max(w1, 0.15) + g(x + s1, 0.07) * max(w2, 0.15);
		light = (tint * lines * 1.15 + deep * (halo * 0.32 + g(x, 0.26) * 0.1)) * fade + deep * pool(half_w * 0.6) * 0.32;
		veil = (g(x - s1, 0.045) + g(x + s1, 0.045)) * fade * 0.16 + pool(half_w * 0.6) * 0.1;
	} else if (kind < 4.5) {
		// The pillar: a hot core, a glow round it and a wide soft halo, rising past the top of the
		// screen, brightest where it stands and thinning as it climbs. Motes ride up it.
		float fade = rise * (1.0 - 0.55 * smoothstep(0.0, 1.0, u));
		float up = motes(0.24, 2.4, 0.8) * (1.0 - u * 0.6);
		// The foot burns brighter: where the light meets the ground.
		float hearth = g(x, 0.22) * g(y, 0.35);
		vec3 amber = mix(tint, deep, 0.5);
		light = (tint * (g(x, 0.045) * 1.2 + up * 0.9) + amber * g(x, 0.16) * 0.5 + deep * g(x, 0.6) * 0.16) * fade * shimmer
			+ amber * hearth * 0.5 + deep * pool(half_w * 0.75) * 0.5;
		veil = (g(x, 0.07) * 0.3 + g(x, 0.3) * 0.1) * fade + pool(half_w * 0.75) * 0.14;
	} else if (kind < 5.5) {
		// The strike: its light falling down the screen onto it, a bright head and a trail, and
		// on landing a flash at its foot.
		float p = param;
		float head = mix(H, 0.0, smoothstep(0.0, 0.45, p));
		float trail = smoothstep(head - 0.1, head + 0.6, y) * exp(-max(y - head, 0.0) / (H * 0.35));
		float fall = 1.0 - smoothstep(0.45, 0.9, p);
		float flash = smoothstep(0.38, 0.5, p) * (1.0 - smoothstep(0.5, 1.0, p));
		light = (tint * g(x, 0.05) * 1.3 + deep * g(x, 0.22) * 0.45) * trail * fall
			+ deep * pool(half_w * 0.8) * flash * 0.9 + tint * g(x, 0.3) * g(y, 0.5) * flash * 0.7;
		veil = g(x, 0.1) * trail * fall * 0.25 + pool(half_w * 0.8) * flash * 0.15;
	} else {
		// A plain short glow.
		float fade = rise * pow(1.0 - u, 1.5);
		light = (tint * g(x, 0.03) * 0.75 + deep * g(x, 0.14) * 0.36) * fade + deep * pool(half_w * 0.55) * 0.26;
		veil = (g(x, 0.06) * 0.2 + g(x, 0.16) * 0.08) * fade + pool(half_w * 0.55) * 0.08;
	}

'''
s = s[:start] + new + s[end:]
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
