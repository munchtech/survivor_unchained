// P7 shapes, part B (Bladestorm and Iron Vow), included by fx_p7.gdshaderinc before p7_frag. Round 3 (9 Nov, against
// judge r2): every light shape here only works out where the pixel sits on its stroke and calls p7_stroke (the rings are
// p7_wave, mode 16 in fx_p7.gdshaderinc; the stars mode 17 = p7_star); on top only coverage caps (p7_alpha).
//   6 smear   Bladestorm's blade smear: a strip mesh swept on the blade's own path at its reach (UV.x 0 tail .. 1 head at
//             the blade, UV.y across); the core only in its leading quarter, its coverage p7_alpha at the head -> 0 at the
//             tail; life p7_fade.
//   7 seam    a Sunder line's seam in its crack: a strip mesh no wider than the crack's gap (UV.x 0 her end .. 1 the far
//             end); hot at her end, tapering out; it flares in heat (life p7_fade), never in width; p7_alpha the pulse.
//   8 dome    Iron Vow's shell: a hemisphere mesh, its interior clear; a rim p7_width px in from its outline (the
//             silhouette, and where it meets the ground at p7_y0 on its near half only), hot at the outline and feathering
//             inward; life p7_lvl.
//   9 glow    the vow's store on the shield's face (camera-facing): a round stroke seen end-on, core at its heart; life
//             p7_lvl (the view grows the quad).
//  10 nick    a blade's nick on a struck foe (or a blow on her shield): one short three-band stroke along p7_dir2 (screen),
//             both ends tapered; life p7_fade.
//  11 pulse   (kept for its callers) a band climbing her pose, through the stroke.

// the smear
vec4 p7_storm(vec2 p) {
	float al = clamp(p.x * 0.5 + 0.5, 0.0, 1.0);
	bool lead = al > 0.75;
	// the core lives only in the leading quarter: behind it the stroke runs a life step on (its core out), its across
	// held so its width does not step where the core ends
	float lf = lead ? p7_fade : max(p7_fade, 0.34);
	float k = lead ? 1.0 : (1.0 - 0.45 * floor(lf * 3.0 + 1e-4) / 3.0) / (1.0 - 0.45 * floor(p7_fade * 3.0 + 1e-4) / 3.0);
	vec4 o = p7_stroke(p.y * k, al, lf);
	o.a *= p7_alpha * smoothstep(0.0, 0.85, al);
	return o;
}

// the seam
vec4 p7_scar(vec2 uv) {
	float x = uv.x;
	float along = mix(0.9, 0.35, x) * smoothstep(0.0, 0.05, x);
	vec4 o = p7_stroke(uv.y * 2.0 - 1.0, along, p7_fade);
	o.a *= p7_alpha;
	return o;
}

// (lane E lead 7, 17 Nov) mode 18, the fissure: the storm's Sunder line as a painted ground fissure (it replaces the crack
// decals' soft dark smear and the 1 px seam the den judge saw, 17 Nov). A strip mesh laid on the line's path: UV.x px along
// from her end, UV.y px across, both at the play camera (1080 lines); p7_rpx the line's length in px. Every edge is hard
// (one pixel's antialias), nothing feathers outside it:
//   gap     jagged: knots about every p7_jag.x px (jittered p7_jag.y), the centre swinging p7_jag.z of the gap's width
//           (a zigzag, a few runs on one side), each edge chipped on its own finer knots (p7_jag.w of the width); its
//           width p7_gap.x px at her end tapering (power p7_gap.z) to p7_gap.y at the far end, then to a point over the
//           last p7_gap.w px, each knot 0.75-1.25 of that (uneven). Two flat warm darks (the line row): p7_deep, and the
//           lit wall p7_wall along the lit side (p7_lit: the across sign facing the screen's lower right) over p7_lip.z
//           of the width where the gap is 3 px or more.
//   lip     a broken lit lip p7_lip.x px outside the lit edge (p7_lipc) on p7_lip.y of its knots, pointed at both ends.
//   branch  hairline cracks off the gap's edges at p7_brn.x of the knots (half that at the far end), p7_brn.y px long,
//           p7_brn.z px at the root tapering to a point, one kink.
//   seam    in the gap's middle: p7_seam.x px at her end to p7_seam.y at p7_seam.z of the length (then out), never wider
//           than the gap less a dark margin each side; broken on its own knots (unbroken at her end .. p7_seam.w of them
//           off at its end). The school's bands by heat p7_fade: 0 white-hot (core, gold, amber), 1/3 gold over amber,
//           2/3 amber at 0.7 of the width, 1 out; p7_alpha its pulse.
//   life    p7_open the share laid from her end; p7_erode 0..1 breaks it into pieces where it lies, the far end first.
uniform vec4 p7_gap = vec4(10.0, 1.5, 1.0, 6.0);
uniform vec4 p7_jag = vec4(14.0, 0.6, 0.35, 0.3);
uniform vec4 p7_seam = vec4(3.5, 0.8, 0.86, 0.3);
uniform vec4 p7_brn = vec4(0.35, 14.0, 1.6, 0.0);
uniform vec4 p7_lip = vec4(1.5, 0.55, 0.38, 0.0);
uniform vec3 p7_deep = vec3(0.012, 0.008, 0.005);
uniform vec3 p7_wall = vec3(0.03, 0.02, 0.012);
uniform vec3 p7_lipc = vec3(0.3, 0.22, 0.14);
uniform float p7_lit = 1.0;
uniform float p7_open = 1.0;
uniform float p7_erode = 0.0;

float p7_kh(float i, float k) { return fx_hash(vec2(i * 1.731 + k * 17.17, k * 3.11 + p7_seed * 5.71)); }
float p7_kpos(float i, float S, float J, float k) { return (i + J * (p7_kh(i, k) - 0.5)) * S; }
// the knot segment holding `a` (knots about every S px, jittered by J < 1, salt k): its index, its ends q0 q1
float p7_kseg(float a, float S, float J, float k, out float q0, out float q1) {
	float i0 = floor(a / S), i = i0;
	q0 = p7_kpos(i0, S, J, k); q1 = p7_kpos(i0 + 1.0, S, J, k);
	if (a < q0) { i = i0 - 1.0; q1 = q0; q0 = p7_kpos(i, S, J, k); }
	else if (a >= q1) { i = i0 + 1.0; q0 = q1; q1 = p7_kpos(i + 1.0, S, J, k); }
	return i;
}
float p7_gapw(float a) { return mix(p7_gap.y, p7_gap.x, pow(clamp(1.0 - a / max(p7_rpx, 1.0), 0.0, 1.0), p7_gap.z)); }
// a main knot's width and centre (px)
float p7_kw(float i) { return p7_gapw(p7_kpos(i, p7_jag.x, p7_jag.y, 1.0)) * (0.75 + 0.5 * p7_kh(i, 4.0)); }
float p7_kc(float i) {
	float s = (mod(i, 2.0) < 1.0 ? -1.0 : 1.0) * (p7_kh(i, 3.0) < 0.22 ? -1.0 : 1.0);
	return s * (0.3 + 0.7 * p7_kh(i, 2.0)) * p7_jag.z * p7_kw(i);
}
// a hard coverage: d px inside its edge, antialiased over one pixel
float p7_cov(float d, float aa) { return clamp(d / aa + 0.5, 0.0, 1.0); }
float p7_sdseg(vec2 q, vec2 a, vec2 b, out float s) {
	vec2 ab = b - a;
	s = clamp(dot(q - a, ab) / max(dot(ab, ab), 1e-4), 0.0, 1.0);
	return length(q - a - ab * s);
}

vec4 p7_fissure(vec2 uv) {
	float a = uv.x, x = uv.y, L = max(p7_rpx, 1.0), t = a / L;
	if (a < 0.0 || a > p7_open * L || t > 1.0) return vec4(0.0);
	float aa = clamp(fwidth(x), 0.5, 1.5);
	float S = p7_jag.x, J = p7_jag.y;
	// the gap: its knot segment, width and centre
	float q0, q1;
	float i = p7_kseg(a, S, J, 1.0, q0, q1);
	float u = clamp((a - q0) / max(q1 - q0, 1e-3), 0.0, 1.0);
	float W = mix(p7_kw(i), p7_kw(i + 1.0), u);
	W *= clamp((L - a) / max(p7_gap.w, 0.5), 0.0, 1.0) * clamp(0.4 + 0.12 * a, 0.4, 1.0);
	float C = mix(p7_kc(i), p7_kc(i + 1.0), u);
	// each edge chipped on its own finer knots
	float r0, r1;
	float il = p7_kseg(a, 0.45 * S, 0.7, 5.0, r0, r1);
	float el = mix(p7_kh(il, 15.0), p7_kh(il + 1.0, 15.0), clamp((a - r0) / max(r1 - r0, 1e-3), 0.0, 1.0)) * 2.0 - 1.0;
	float ir = p7_kseg(a, 0.45 * S, 0.7, 6.0, r0, r1);
	float er = mix(p7_kh(ir, 16.0), p7_kh(ir + 1.0, 16.0), clamp((a - r0) / max(r1 - r0, 1e-3), 0.0, 1.0)) * 2.0 - 1.0;
	float left = C - 0.5 * W * (1.0 + p7_jag.w * el), right = C + 0.5 * W * (1.0 + p7_jag.w * er);
	float dl = x - left, dr = right - x;
	float gcov = p7_cov(min(dl, dr), aa);
	// the lit wall: a flat lighter dark along the lit side's inside
	float dlit = p7_lit > 0.0 ? dr : dl;
	float wall = W >= 3.0 ? p7_cov(p7_lip.z * W - dlit, aa) : 0.0;
	vec3 gc = mix(p7_deep, p7_wall, wall);
	// the lip: a broken lit sliver outside the lit edge, pointed at both ends of each piece
	float lq0, lq1;
	float jl = p7_kseg(a, 0.8 * S, 0.6, 7.0, lq0, lq1);
	float lu = clamp((a - lq0) / max(lq1 - lq0, 1e-3), 0.0, 1.0);
	float lw = p7_lip.x * sqrt(sin(3.14159265 * lu)) * step(p7_kh(jl, 17.0), p7_lip.y) * clamp(W - 2.0, 0.0, 1.0);
	float lcov = lw > 0.05 ? p7_cov(lw + dlit, aa) * step(-0.5 * aa, -dlit) : 0.0;
	// hairline branches off the edges at some knots, each with one kink
	float bcov = 0.0;
	for (int d = -2; d <= 1; d++) {
		float j = i + float(d);
		float pj = p7_kpos(j, S, J, 1.0), tj = clamp(pj / L, 0.0, 1.0);
		if (p7_kh(j, 8.0) >= p7_brn.x * mix(1.0, 0.5, tj) || pj < 4.0 || pj > L - 8.0 || pj > p7_open * L) continue;
		float Wj = p7_kw(j), kw = clamp(Wj / max(p7_gap.x, 1.0), 0.0, 1.0);
		float sb = p7_kh(j, 9.0) < 0.5 ? -1.0 : 1.0;
		float th = radians(25.0 + 35.0 * p7_kh(j, 10.0)), th2 = th + (p7_kh(j, 12.0) - 0.5) * 0.9;
		float Lb = p7_brn.y * (0.6 + 0.6 * p7_kh(j, 11.0)) * mix(0.55, 1.0, kw);
		vec2 b0 = vec2(pj, p7_kc(j) + sb * 0.45 * Wj);
		vec2 b1 = b0 + 0.55 * Lb * vec2(cos(th), sb * sin(th));
		vec2 b2 = b1 + 0.45 * Lb * vec2(cos(th2), sb * sin(th2));
		float s1, s2;
		float d1 = p7_sdseg(vec2(a, x), b0, b1, s1), d2 = p7_sdseg(vec2(a, x), b1, b2, s2);
		float ub = d1 < d2 ? 0.55 * s1 : 0.55 + 0.45 * s2;
		float hb = 0.5 * p7_brn.z * mix(0.6, 1.0, kw) * (1.0 - ub) + 0.2;
		bcov = max(bcov, p7_cov(hb - min(d1, d2), aa));
	}
	// the seam: hot in the gap's middle, broken toward its end, the school's bands by heat
	float scov = 0.0;
	vec3 sc = fx_edge;
	float lf = floor(clamp(p7_fade, 0.0, 1.0) * 3.0 + 1e-4);
	if (lf < 3.0 && t < p7_seam.z) {
		float ts = t / max(p7_seam.z, 1e-3);
		float sw = mix(p7_seam.y, p7_seam.x, pow(1.0 - ts, p7_gap.z)) * clamp((1.0 - ts) / 0.07, 0.0, 1.0);
		sw = min(sw, W - 2.0 * max(0.8, 0.25 * W)) * (lf > 1.5 ? 0.7 : 1.0);
		float sq0, sq1;
		float js = p7_kseg(a, 1.7 * S, 0.6, 13.0, sq0, sq1);
		float off = p7_seam.w * smoothstep(0.15, 1.0, ts);
		bool on = p7_kh(js, 18.0) >= off;
		if (on && sw > 0.3) {
			if (p7_kh(js - 1.0, 18.0) < off) sw *= clamp((a - sq0) / 3.0, 0.0, 1.0);
			if (p7_kh(js + 1.0, 18.0) < off) sw *= clamp((sq1 - a) / 3.0, 0.0, 1.0);
			float m = 0.5 * (left + right), hs = 0.5 * sw, dm = abs(x - m);
			scov = p7_cov(hs - dm, aa) * p7_alpha;
			float r = dm / max(hs, 1e-3);
			if (lf < 0.5) sc = mix(mix(fx_edge, fx_mid, p7_cov((0.78 - r) * hs, aa)), fx_core, p7_cov((0.42 - r) * hs, aa));
			else if (lf < 1.5) sc = mix(fx_edge, fx_mid, p7_cov((0.6 - r) * hs, aa));
		}
	}
	// one painted layer: the lip, the dark over it, the seam in the dark
	vec3 col = mix(p7_lipc, gc, gcov);
	col = mix(col, p7_deep, bcov * (1.0 - gcov));
	float al = max(lcov, max(gcov, bcov));
	col = mix(col, sc, scov);
	// the erosion: pieces broken out where it lies, the far end first (hard, stepped by the caller)
	if (p7_erode > 0.0) {
		float v = 0.72 * (0.5 + 0.5 * fx_gnoise(vec2(a / 9.0, x / 5.0) + vec2(p7_seed * 3.7, 1.3))) + 0.28 * (1.0 - t);
		al *= clamp((v - p7_erode) / max(fwidth(v), 1e-3) + 0.5, 0.0, 1.0) * step(p7_erode, 0.999);
	}
	return vec4(col, al);
}

// the dome's rim: px in from its outline (the silhouette's facing term over its own slope; the ground line's height over
// its slope), the stroke's centerline at the outline so its hot middle sits on it and its inner half feathers inward
vec4 p7_shell(vec2 uv, vec3 n, vec3 v) {
	n = normalize(n);
	float f = abs(dot(n, normalize(v)));
	float px = f / max(fwidth(f), 1e-4);
	// (r3 fix) nothing at or under the ground line: the hemisphere mesh's bottom cap (Godot flattens its lower rings onto
	// y 0) sat there as a flat disc whose height above the line, 0, made it the stroke's centerline: the opaque disc under her
	if (p7_wy <= p7_y0) return vec4(0.0);
	float hb = p7_wy - p7_y0;
	// (fight-ring, 13 Nov) the ground line only where it IS the dome's outline: its near half. From the play camera (near
	// top-down) the far half of the line showed through the clear interior a dome's height below the silhouette, and the
	// two read as an untraced orange double ring on her in every fight; the silhouette (far) and the ground line (near)
	// now close into one outline, eased over the sides where they meet.
	// So is the far wall's foot: from that height its steep inner wall is nearly edge-on, so the facing term alone drew
	// the same far line (thinner); on the far half nothing is drawn in the lowest 0.3 m (the true far silhouette sits
	// well above it, about a third of the way up).
	float nearK = smoothstep(-0.15, 0.2, p7_near);
	px = mix(1e4, px, max(nearK, smoothstep(0.12, 0.3, hb)));
	float gl = hb / max(fwidth(p7_wy), 1e-5);
	px = min(px, mix(1e4, gl, nearK));
	float ang = atan(n.y, n.x);
	// (M4 lead 14, r3d: every angle-driven term sampled on a circle, so it closes on itself; atan's jump at -x cut the band)
	vec2 cs = vec2(cos(ang), sin(ang));
	float along = 0.8 + 0.06 * fx_gnoise(cs * 3.0 + vec2(p7_seed, 0.0)) + 0.04 * fx_gnoise(cs * 11.0 + vec2(p7_seed + 2.0, 0.0));
	vec4 o = p7_stroke(px / max(p7_width, 0.5), along, p7_lvl);
	o.a *= p7_alpha;
	return o;
}

// the store's glow on the shield
vec4 p7_store(vec2 p) {
	float r = length(p), a = atan(p.y, p.x);
	float along = 0.82 + 0.08 * fx_noise(vec2(cos(a), sin(a)) * 1.3 + vec2(p7_seed, 0.0)); // (M4 lead 14: on a circle, no seam at -x)
	vec4 o = p7_stroke(r, along, p7_lvl);
	o.a *= p7_alpha;
	return o;
}

vec4 p7_pulse(vec3 n, vec3 v) {
	float y = (p7_wy - p7_y0) / max(p7_h, 0.1);
	float front = p7_t / (3.0 * P7_SAMPLE) * 1.15;
	float d = front - y;
	if (d < 0.0 || d > 0.2 || front > 1.25) return vec4(0.0);
	vec4 o = p7_stroke((d - 0.1) / 0.1, 1.0 - d * 3.0, 0.4);
	o.a *= p7_alpha;
	return o;
}

// the nick
vec4 p7_nick(vec2 p) {
	vec2 f = normalize(p7_dir2);
	float u = dot(p, f), v = dot(p, vec2(-f.y, f.x));
	vec4 o = p7_stroke(v / 0.24, 0.9 * (1.0 - abs(u)), p7_fade);
	o.a *= p7_alpha;
	return o;
}
