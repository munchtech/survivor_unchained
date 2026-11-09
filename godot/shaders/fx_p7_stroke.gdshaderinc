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

// p7_wave (round 3 fix, 9 Nov: r3 read as a selection circle, an even gold tube): the travelling wavefront, asymmetric.
// The LEAD is one stroke whose core is the front itself: a white-gold lip (its outer side 1.3 px, so the front is crisp),
// gold to 75% of `lead`, amber to its end; the TRAIL behind it is a second stroke in the amber band running out into dry
// brush over `trail`, its bristles RADIAL (dragged outward: the travel) where the lead's run round the ring. The brush is
// seamless round the ring (noise on circles, never an angle seam): the width and the heat swell, the front wobbles a
// pixel, the trail's depth varies by half, and a few stretches run thinner, cooler and drier (broken coverage). Width
// goes 1 - fall^1.5 and coverage 1 - fall^2.2 (to nothing at the reach); the core steps out past fall 0.6, the gold past
// 0.86. No branch round the strokes (fx_stroke's antialiasing takes derivatives).
//   p      the pixel in the quad (-1..1; the quad is the reach); front, lead, trail in shares of it; rpx: the reach in px
//   life   stepped (p7_stroke); tip 0..1 scales the heat (an arc's ends taper to points; 1 for a whole ring)
vec4 p7_wave(vec2 p, float front, float lead, float trail, float fall, float life, float tip, float rpx) {
	float r = length(p);
	vec2 dr = p / max(r, 1e-5);
	float sd = fx_stroke_seed;
	float n1 = fx_gnoise(dr * 1.1 + vec2(sd * 0.37, sd * 0.11));
	float n2 = fx_gnoise(dr * 2.6 + vec2(5.3 + sd * 0.21, sd * 0.53));
	float n3 = fx_gnoise(dr * 0.8 + vec2(9.1 + sd * 0.17, 2.2));
	float fl = clamp(fall, 0.0, 1.0);
	float kw = 1.0 - pow(fl, 1.5);
	float L = max(lead * rpx * kw * (1.0 + 0.18 * n1), 0.05);
	float T = max(trail * rpx * kw * (1.0 + 0.45 * n2), 0.0);
	float r0 = front * rpx;
	float d = r0 - r * rpx + lead * rpx * 0.12 * n2;
	float al = clamp(tip, 0.0, 1.0) * clamp(0.86 + 0.05 * n1 - 0.9 * max(0.0, n3 - 0.35), 0.15, 0.9);
	float lf = max(life, fl > 0.86 ? 0.67 : (fl > 0.6 ? 0.34 : 0.0));
	float mref = mix(fx_stroke_shape.z, 1.0, pow(0.86, 0.7));
	float hot = smoothstep(0.15, 1.0, 0.86);
	float g = d < 0.0 ? -d / 1.3 : p7_wave_g(d / L, 0.24 * hot, mix(0.48, 0.66, hot));
	vec4 o = p7_stroke_at(g * mref, al, lf, dr * (r0 / 22.0));
	float t0 = 0.75 * L;
	float ut = (d - t0) / max(L + T - t0, 1e-3);
	float uc = clamp(ut, 0.0, 1.0);
	float at = al * mix(0.62, 0.3, uc);
	float mt = mix(fx_stroke_shape.z, 1.0, pow(max(at, 1e-3), 0.7));
	float rho = r0 / 3.5 - d / 9.0;
	vec4 t = p7_stroke_at(mix(0.5, 1.0, uc) * mt, at, lf, dr * rho + vec2(17.0, 3.0));
	t.a *= (1.0 - 0.3 * uc) * step(0.0, ut) * step(ut, 1.0) * step(1e-3, T);
	if (t.a > o.a) o = t;
	o.a *= 1.0 - pow(fl, 2.2);
	return o;
}
