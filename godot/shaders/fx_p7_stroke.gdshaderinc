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

vec4 p7_stroke(float across, float along, float life) {
	float lf = floor(clamp(life, 0.0, 1.0) * 3.0 + 1e-4) / 3.0;
	return fx_stroke(across * fx_stroke_shape.x, along, lf);
}

// p7_wave (round 3, 9 Nov; the r2 judge's ONE CHANGE): the travelling wavefront. A ring is never a band: a hot three-band
// leading edge `lead` wide whose outer side is the front, and a feathered trailing band `trail` deep behind it (across: the
// radial offset; along: closeness to the front, 1 at the leading edge), gold stepping to amber and breaking into dry-brush
// streaks toward its end. Width and coverage run to 0 as it reaches its reach (`fall` 0..1: how far it has run). The brush
// wanders round the ring (the front a pixel uneven, the width and the core breathing, the bristles' streaks broken along
// it), so it never reads as a stamped circle.
//   p      the pixel in the quad (-1..1; the quad is the reach, 2R wide); front, lead, trail in the same units (shares of R)
//   life   stepped (p7_stroke); tip 0..1 scales the along (an arc's ends taper to points; 1 for a whole ring)
vec4 p7_wave(vec2 p, float front, float lead, float trail, float fall, float life, float tip) {
	float r = length(p), a = atan(p.y, p.x);
	float k = clamp(1.0 - fall, 0.0, 1.0);
	float n1 = fx_gnoise(vec2(a * 2.3 + fx_stroke_seed * 1.3, fx_stroke_seed * 0.7));
	float n2 = fx_gnoise(vec2(a * 6.1 + fx_stroke_seed * 2.9, 3.1 + fx_stroke_seed));
	float n3 = fx_gnoise(vec2(a * 17.0 + fx_stroke_seed * 5.3, 7.7));
	float L = lead * k * (1.0 + 0.16 * n1);
	float T = trail * k * (1.0 + 0.35 * n2);
	if (L < 1e-5) return vec4(0.0);
	float f = front + lead * 0.1 * n2;
	float al = clamp(tip, 0.0, 1.0) * clamp(0.82 + 0.05 * n1 + 0.03 * n3, 0.7, 0.9); // (under the head cap, 0.92+)
	vec4 o = p7_stroke((r - (f - 0.5 * L)) / (0.5 * L), al, life);
	float u = (f - 0.8 * L - r) / max(T, 1e-5);
	if (u > 0.0 && u < 1.0 && T > 1e-5) {
		float at = al * mix(0.95, 0.3, u);
		float taper = mix(fx_stroke_shape.z, 1.0, pow(max(at, 1e-3), 0.7));
		vec4 t = p7_stroke((0.3 + 0.7 * u) * taper, at, life);
		t.a *= 1.0 - 0.5 * u;
		if (t.a > o.a) o = t;
	}
	o.a *= 1.0 - fall * fall;
	return o;
}
