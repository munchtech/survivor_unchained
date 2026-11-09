// The painted stroke (P7, 9 Nov): every P7 light shape draws through p7_stroke, which is now L1's primitive
// fx_stroke (fx_cel.gdshaderinc, fx-lang@a278b6482: three bands across the width, the dry-brush edge, the life curve;
// read its header). This wrapper only adapts P7's conventions:
//   across  -1..1 where |across| = 1 is the stroke's outer edge at its head (P7's shapes were sized so); fx_stroke's
//           head half-width is fx_stroke_shape.x, so across is scaled by it.
//   life    stepped per sample here (0, 1/3, 2/3, 1 -> whole, core gone, gold gone, dead), as FX_LANGUAGE §4 asks of
//           the caller.
// Per material: fx_stroke_seed (each instance its own bristles) and fx_bristle.x (about one bristle per 2-4 px of the
// stroke's width at the play camera), set by BattleFx.P7Brush. The stand-in body it replaced is in git history
// (456025e87..f465d3e95); its p7_sw / p7_sseed are gone (the wedge's taper is fx_stroke_shape.z, the seed
// fx_stroke_seed).
// Needs fx_cel.gdshaderinc included first.

vec4 p7_stroke_at(float across, float along, float life, vec2 grain_at) {
	float lf = floor(clamp(life, 0.0, 1.0) * 3.0 + 1e-4) / 3.0;
	return fx_stroke_at(across * fx_stroke_shape.x, along, lf, grain_at);
}
vec4 p7_stroke(float across, float along, float life) { return p7_stroke_at(across, along, life, vec2(0.0)); }

// the lead's band map: depth behind the front (a share of the lead) -> the stroke's distance from its centerline, through
// the core's end (0.3), the gold's end (0.75) and the stroke's edge (1), straight on past it
float p7_wave_g(float x, float kc, float km) {
	if (x < 0.3) return x / 0.3 * kc;
	if (x < 0.75) return mix(kc, km, (x - 0.3) / 0.45);
	return mix(km, 1.0, (x - 0.75) / 0.25);
}

// p7_wave (round 3 fix 2, 9 Nov: the r3 fix still read as a selection ring, an even band): the travelling wavefront as a
// few painted ARCS, never a circle. Each arc (p7_arc[j]: its centre angle, half-length, radial offset in leads, the side its
// head is on) is a brush swipe: its width swells to 1.3 x the lead and tapers to points at both ends (blunt at the head, a
// long dry tail), its tail drifting in by a lead so the arcs shingle, its front wobbling a third of a lead; the hot lip (core)
// runs only on its head half (the stroke's along is tail 0 .. head 1), gold, then amber. Its back edge tears into a radial
// DRAG mask (noise stretched along the travel, laid on circles so it is seamless, re-laid once per doubling of the radius so
// it never crawls or shimmers) that runs on as the TRAIL: one amber stroke 1.3 x `trail` deep whose coverage is that mask
// with its threshold rising with depth (dry-brush streaks of uneven length, no inner edge), dying first. As it runs, width
// goes 1 - fall^1.5, the arcs shorten by 30% (gaps open) and from fall 0.5 an erosion breaks them into pieces (their thin
// ends first); the core steps out past fall 0.6, the gold past 0.86. The target (mode 0) stands at front 1 with p7_shrink
// its cover. All arcs come from the view (BattleFx.P7Arcs); p7_narc 0 lays four even ones.
//   p      the pixel in the quad (-1..1; the quad is the reach); front, lead, trail in shares of it; rpx: the reach in px
//   life   stepped (p7_stroke); tip: unused (kept for the signature)
uniform vec4 p7_arc[12];
uniform int p7_narc = 0;
uniform vec2 p7_span = vec2(0.0, 6.2831853); // the arcs' first angle and their span (2 pi: a whole ring)
uniform float p7_shrink = -1.0;              // the arcs' length share (the target's cover); < 0: 1 - 0.3 fall^1.5
const float P7W_TAU = 6.2831853;
float p7_wrap(float x) { return x - P7W_TAU * floor((x + 3.14159265) / P7W_TAU); }
float p7_env(float u) { u = clamp(u, 0.0, 1.0); return pow(u, 0.7) * pow(1.0 - u, 0.3) / 0.5429; }
vec4 p7_arc_at(int j, float sec) {
	if (p7_narc > 0) return p7_arc[j];
	return vec4(p7_span.x + (float(j) + 0.5) * sec, 0.55 * sec, 0.0, 1.0);
}

vec4 p7_wave(vec2 p, float front, float lead, float trail, float fall, float life, float tip, float rpx) {
	float r = length(p), th = atan(p.y, p.x);
	vec2 dr = vec2(cos(th), sin(th));
	float rp = r * rpx;
	float fl = clamp(fall, 0.0, 1.0), kw = 1.0 - pow(fl, 1.5);
	float shrink = p7_shrink >= 0.0 ? p7_shrink : 1.0 - 0.3 * pow(fl, 1.5);
	float r0 = front * rpx, L0 = lead * rpx, L = L0 * kw * 1.3, T = trail * rpx * (1.0 - pow(fl, 1.2)) * 1.3;
	// (far from the front nothing reaches: the margin is past the widest the strokes and their trail go)
	if (rp > r0 + 0.9 * L0 + 6.0 || rp < r0 - 2.6 * L0 - 1.5 * T - 8.0) return vec4(0.0);
	float lf = max(life, fl > 0.86 ? 0.67 : (fl > 0.6 ? 0.34 : 0.0));
	float lev = floor(log2(max(P7W_TAU * r0 / 28.0, 1.0)));
	float rk = 28.0 * exp2(lev) / P7W_TAU, sd = fx_stroke_seed + lev * 17.3;
	float rad = 8.0 * exp2(lev) / P7W_TAU + (r0 - rp) / 22.0;
	vec2 q = dr * rad + vec2(3.3 + sd, 1.7);
	float nz = 0.5 + 0.38 * fx_gnoise(q) + 0.2 * fx_gnoise(q * 2.3 + vec2(7.1, 2.9));
	int n = p7_narc > 0 ? min(p7_narc, 12) : 4;
	float span = p7_span.y, sec = span / float(n);
	float a = mod(th - p7_span.x, P7W_TAU);
	bool full = span > P7W_TAU - 1e-3;
	float kf = floor(a / sec);
	if (!full && a > span) kf = a > span + (P7W_TAU - span) * 0.5 ? 0.0 : float(n - 1);
	int k = clamp(int(kf), 0, n - 1);
	float thr = smoothstep(0.5, 1.0, fl) * 1.25 - 0.12;
	vec4 o = vec4(0.0);
	float benv = 0.0, bf = -1e9, bw = 0.0;
	for (int i = -1; i <= 1; i++) {
		int j = k + i;
		if (full) j = (j + n) % n;
		float valid = (j >= 0 && j < n) ? 1.0 : 0.0;
		j = clamp(j, 0, n - 1);
		vec4 ac = p7_arc_at(j, sec);
		float fj = float(j);
		float dth = p7_wrap(th - ac.x);
		float s = dth / max(ac.y * shrink, 1e-4) * ac.w, u = (s + 1.0) * 0.5;
		float inside = valid * step(abs(s), 1.0);
		float env = p7_env(u) * inside;
		float f = r0 + ac.z * L0 - L0 * kw * pow(clamp(1.0 - u, 0.0, 1.0), 1.6)
			+ 0.35 * L0 * fx_gnoise(vec2(dth * 4.0 + fj * 5.1, fj * 1.3 + fx_stroke_seed));
		float W = max(L * env * (1.0 + 0.3 * fx_gnoise(vec2(dth * 7.0 + fj * 3.3, 7.7 + fx_stroke_seed))), 1e-3);
		float d = f - rp;
		float al = 0.06 + 0.86 * pow(clamp(u, 0.0, 1.0), 0.9);
		float hot = smoothstep(0.15, 1.0, al);
		float g = d < 0.0 ? -d / 1.3 : p7_wave_g(d / W, 0.24 * hot, mix(0.48, 0.66, hot));
		vec4 c = p7_stroke_at(g * mix(fx_stroke_shape.z, 1.0, pow(al, 0.7)), al, lf, vec2(fj * 7.31 + 3.1, dth * rk / 22.0));
		// its back edge torn into the drag mask
		float tl = mix(-0.25, 0.3, clamp((d / W - 0.55) / 0.45, 0.0, 1.0));
		c.a *= d / W > 0.55 ? smoothstep(tl - 0.05, tl + 0.05, nz) : 1.0;
		float ne = 0.5 + 0.5 * fx_gnoise(vec2(dth * 10.0 + fj * 2.9, fj * 3.7 + 1.1)) + 0.35 * (env - 0.5)
			+ 0.12 * fx_gnoise(vec2(dth * rk / 9.0, d / 4.0));
		c.a *= inside * smoothstep(thr - 0.04, thr + 0.04, ne);
		if (c.a > o.a) o = c;
		if (inside > 0.5 && env > benv) { benv = env; bf = f; bw = W; }
	}
	// the trail: an amber stroke behind the arc that owns the angle, its coverage the drag mask
	float Tk = T * smoothstep(0.0, 0.35, benv) * (1.0 + 0.45 * fx_gnoise(dr * 1.3 + vec2(fx_stroke_seed, 0.0)));
	float dd = bf - rp - 0.55 * bw;
	float uu = dd / max(Tk, 1e-3), uc = clamp(uu, 0.0, 1.0);
	float tt = 0.85 * pow(uc, 0.8);
	float alT = 0.6 - 0.45 * uc;
	vec4 t = p7_stroke_at((0.5 + 0.45 * uc) * mix(fx_stroke_shape.z, 1.0, pow(alT, 0.7)), alT, lf, vec2(q.x * 0.5, dd / 6.0));
	float erT = smoothstep(thr + 0.16, thr + 0.24, 0.5 + 0.5 * fx_gnoise(dr * 5.0 + vec2(3.3, dd / 30.0)));
	t.a *= smoothstep(tt - 0.05, tt + 0.05, nz) * mix(0.85, 0.3, uc) * step(0.0, uu) * step(uu, 1.0) * step(1e-4, benv) * erT * sqrt(1.0 - fl);
	if (t.a > o.a) o = t;
	o.a *= 1.0 - pow(fl, 3.0);
	return o;
}
