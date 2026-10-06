import io, sys
from ed import edit
P = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad059388f00c19f9f\godot\shaders\loot_beam.gdshader"
pairs = []
def rep(a, b):
    pairs.append((a, b))
rep("""//   7 Shaft: a moment's column of light (BattleFx.Pillar: a strike, a level, an evolution, a chest,
//     the night won), its height given.
""", """//   7 Shaft: a moment's column of light (BattleFx.Pillar: a strike, a level, an evolution, a chest,
//     the night won), its height given; the fraction, how thick the motes riding up it.
//   8 Band: a band of light lying on the ground at its reach (the way out), breathing.
//   9 Room: a fire's light lying on the ground out to its reach and no further (a fed deadfall).
""")
rep("""	// A pillar reaches the top of the screen at the item's depth, and a little past it.
	if (kind > 3.5 && kind < 5.5)
		tall = max(tall, -foot.z / abs(PROJECTION_MATRIX[1][1]) - foot.y + half_w);
	// Below the foot by the pool's reach (a circle on the ground seen from 56 degrees up).
	float down = half_w * 0.85;
""", """	// A pillar reaches the top of the screen at the item's depth, and a little past it.
	if (kind > 3.5 && kind < 5.5)
		tall = max(tall, -foot.z / abs(PROJECTION_MATRIX[1][1]) - foot.y + half_w);
	// Below the foot by the pool's reach (a circle on the ground seen from 56 degrees up); what lies
	// on the ground all round it, as far above.
	float down = half_w * 0.85;
	if (kind > 7.5) tall = down;
""")
rep("""// Motes of light climbing it: a few at a time, each in its own lane.
float motes(float spread, float speed, float gap) {
	float y = at.y - TIME * speed;
	float cell = floor(y / gap);
	float fy = fract(y / gap);
	float mx = (hash(cell) - 0.5) * spread;
	float my = 0.25 + 0.5 * hash(cell + 5.0);
	return g(at.x - mx, 0.03) * g((fy - my) * gap, 0.045) * step(0.45, hash(cell + 9.0));
}
""", """// Motes of light climbing it: a few at a time, each in its own lane, `size` across.
float motes_of(float spread, float speed, float gap, float size) {
	float y = at.y - TIME * speed;
	float cell = floor(y / gap);
	float fy = fract(y / gap);
	float mx = (hash(cell) - 0.5) * spread;
	float my = 0.25 + 0.5 * hash(cell + 5.0);
	return g(at.x - mx, size) * g((fy - my) * gap, size * 1.5) * step(0.45, hash(cell + 9.0));
}
float motes(float spread, float speed, float gap) { return motes_of(spread, speed, gap, 0.03); }
""")
rep("""		float w = half_w;
		float fade = rise * pow(1.0 - u, 0.9);
		light = (tint * g(x, w * 0.09) * 1.2 + mix(tint, deep, 0.5) * g(x, w * 0.28) * 0.5 + deep * g(x, w * 0.7) * 0.14) * fade
			+ deep * pool(w * 0.55) * 0.4;
		veil = (g(x, w * 0.14) * 0.25 + g(x, w * 0.4) * 0.08) * fade;
	} else {""", """		float w = half_w;
		float fade = rise * pow(1.0 - u, 0.9);
		// Motes riding up it (the night won: the ember leaving what ruled it), two lanes' worth.
		float up = param > 0.01 ? (motes_of(w * 0.55, 3.2, 0.55, w * 0.025) + motes_of(w * 0.3, 2.1, 0.8, w * 0.02)) * param : 0.0;
		light = (tint * (g(x, w * 0.09) * 1.2 + up * 1.4) + mix(tint, deep, 0.5) * g(x, w * 0.28) * 0.5 + deep * g(x, w * 0.7) * 0.14) * fade
			+ deep * pool(w * 0.55) * 0.4;
		veil = (g(x, w * 0.14) * 0.25 + g(x, w * 0.4) * 0.08) * fade;
	} else if (kind > 8.5) {
		// A fire's light on the ground, even out to its reach and falling away there (the room the
		// pack will not cross), a little stronger toward its heart. Never a line at its edge.
		vec2 e = vec2(x / half_w, y / (half_w * 0.83));
		float r = length(e);
		float lit = smoothstep(1.08, 0.86, r) * (0.55 + 0.45 * exp(-r * r * 2.5));
		light = deep * lit * 0.22;
		veil = 0.0;
	} else if (kind > 7.5) {
		// A band of light lying on the ground at its reach, soft on both sides, breathing; a faint
		// light within it. (A decal's band with a hard edge read as a cream hoop.)
		vec2 e = vec2(x / half_w, y / (half_w * 0.83));
		float r = length(e);
		float breath = 0.72 + 0.28 * sin(TIME * 2.2 + seed * 6.28);
		float band = exp(-pow((r - 0.92) / 0.075, 2.0)) * breath;
		float within = smoothstep(1.0, 0.2, r) * 0.1;
		light = (mix(tint, deep, 0.35) * band + deep * within) * rise;
		veil = band * 0.05;
	} else {""")
edit(r"shaders\loot_beam.gdshader", pairs)
