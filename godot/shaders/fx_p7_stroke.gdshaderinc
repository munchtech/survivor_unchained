// The painted stroke (P7 lead 2, 9 Nov): ONE light primitive for every P7 shape (the judge r1's "one change"). It is the
// stand-in for L1's fx_stroke (fx_cel.gdshaderinc, fx-lang): same arguments, so the swap is this function's body.
//   across  -1..1 across the stroke's width at this point (0 its centerline; |across| > 1 is outside it)
//   along   0 its tail .. 1 its head (the leading edge: hottest and widest)
//   life    0 born .. 1 dead
// Three bands across the width: a thin white-gold core on the centerline, the gold body, and the amber edge, whose
// outer part feathers to nothing in COVERAGE (the hex stays the band's; never an edge made by a gaussian of color).
// The life curve: the head is hottest and widest; toward the tail the stroke thins (to a point) and cools (the core
// gives out first, then the gold); with life it thins and dies by stepping: holes open and the bands erode core, then
// mid, then edge, and only in the last third does its coverage fall away.
// Needs fx_cel.gdshaderinc included first (fx_t, fx_cel, fx_noise).

uniform vec4 p7_sw = vec4(0.14, 0.52, 0.42, 0.75); // core half-width share, mid share, feather share, taper power
uniform float p7_sseed = 0.0;                    // the stroke's own hole pattern

const float P7_STEP = 0.3333333;

vec4 p7_stroke(float across, float along, float life) {
	along = clamp(along, 0.0, 1.0);
	life = clamp(life, 0.0, 1.0);
	float st = floor(life / P7_STEP + 1e-4);            // 0 whole, 1 core gone, 2 gold gone, 3 dead
	// the width: full at the head, to a point at the tail; a third thinner by the end of its life
	float w = pow(along, p7_sw.w) * (1.0 - 0.33 * life);
	float a = abs(across) / max(w, 1e-4);
	// the bands' boundaries across it (shares of the half-width); the core cools away toward the tail
	float c = p7_sw.x * smoothstep(0.25, 0.7, along) * step(st, 0.5);
	float m = p7_sw.y * mix(0.55, 1.0, along) * step(st, 1.5);
	// piecewise heat so the bands land on c, m and 1 whatever the school's cuts are
	float heat;
	if (a < c) heat = mix(1.0, fx_t.z, a / max(c, 1e-4));
	else if (a < m) heat = mix(fx_t.z - 0.001, fx_t.y, (a - c) / max(m - c, 1e-4));
	else heat = mix(fx_t.y - 0.001, fx_t.x, (a - m) / max(1.0 - m, 1e-4));
	if (a >= 1.0) heat = fx_t.x - (a - 1.0) * 0.35;  // the glow beyond
	// stepped holes as it dies (a painted break-up, larger toward the tail)
	float holes = fx_noise(vec2(across * 2.5 + p7_sseed * 7.0, along * 13.0 + p7_sseed * 3.0));
	float hk = st * 0.22 + (1.0 - along) * 0.12 * step(0.5, st + 0.5 * step(0.001, life));
	if (holes < hk) heat = min(heat, fx_t.x - 0.5);
	if (st >= 3.0) heat = -9.0;
	vec4 o = fx_cel(heat, along);
	// the feathered amber edge: its outer part falls to nothing in coverage
	float f = p7_sw.z;
	o.a *= 1.0 - smoothstep(1.0 - f, 1.0, a) * step(m, a);
	// the tail's last few percent feather too, and the last third of its life loses coverage
	o.a *= smoothstep(0.0, 0.06, along);
	o.a *= 1.0 - smoothstep(0.66, 1.0, life);
	return o;
}
