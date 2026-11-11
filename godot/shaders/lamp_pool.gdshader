// (L1 lead 26, M4 row b) The held lamp's pool edge: a ring of painted dashes on the ground round a caught, lit lamp while
// she stands outside it (logic/Ui/LampPoolEdge.cs; src/Fx/BattleFx.LampPool.cs builds the terrain-following ribbon).
// The place to hold: warm-white dabs, each with soft dry-brush ends, laid over a dark under-stroke so it holds on light
// and dark ground; never the unbroken amber ring of a blow. Drawn after the grade (FxAfter, unlit: it reads at night) and
// behind the world (FxWorldDepth: a canopy in front covers it, she and the firs stand over it).
// UV.x: 0..1 round the ring; UV.y: -1 (lamp side) .. 1 (outside) across the ribbon (lp_half meters).
shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;
#include "res://shaders/fx_cel.gdshaderinc"

uniform float lp_alpha = 1.0;      // the fade (0..1, stepped by the caller)
uniform float lp_count = 24.0;     // dabs round the ring
uniform float lp_duty = 0.62;      // share of each cell a dab fills
uniform float lp_circ = 31.4;      // the circumference (m): the brush runs in meters, never stretched
uniform float lp_half = 0.22;      // the ribbon's half-width (m; BattleFx.LampPool.cs sets it)
uniform float lp_warm_w = 0.40;    // the warm stroke's half-width at its loaded head (share of lp_half): ~8 px at 09
uniform float lp_ink_w = 0.80;     // the ink bed's half-width (share of lp_half): wider than the stroke, under all of it
uniform float lp_ink_off = 0.03;   // the bed sits this far outward (share of lp_half): a lip of shade on the far side
uniform float lp_wob = 0.022;      // the hand: the centerline wanders this far (m), slow round the circle
uniform vec3 lp_warm = vec3(1.0, 0.945, 0.84);   // #fff1d6 (sRGB display colors, linearized at the end)
uniform vec3 lp_warm2 = vec3(1.0, 0.90, 0.72);   // its thin edge and dry tail, a touch warmer (never amber)
uniform vec3 lp_ink = vec3(0.141, 0.11, 0.071);  // #241c12
uniform float lp_warm_a = 0.9;
uniform float lp_ink_a = 0.5;
uniform float lp_seed = 0.0;

const float LP_TAU = 6.2831853;

// noise sampled ON the circle (radius R m, `f` features per meter): it closes on itself, never atan's or UV.x's seam
float lp_ring(vec2 cs, float R, float f, float o) {
	return fx_gnoise(cs * R * f + vec2(o * 3.1 + lp_seed, o * 1.7 - lp_seed));
}

void fragment() {
	float th = UV.x * LP_TAU;
	vec2 cs = vec2(cos(th), sin(th));
	float R = lp_circ / LP_TAU;
	float u = UV.x * lp_count;
	float cell = floor(u), fu = fract(u);
	float jit = fx_hash(vec2(cell, lp_seed + 1.0));
	float duty = lp_duty * (0.8 + 0.4 * jit);
	float e = 0.035;                                   // the bed runs this share of a cell past each end of the stroke
	float len = lp_circ / lp_count * duty;            // the stroke's length (m)
	float s0 = (fu - e) / duty;
	float s = clamp(s0, 0.0, 1.0);
	float am = s * len;                               // meters along the stroke (local: no seam)
	float acr = UV.y * lp_half;                       // meters across, + outward
	// the hand: the centerline wanders slowly round the circle, and each stroke sits a touch in or out
	float wob = lp_wob * (lp_ring(cs, R, 0.35, 3.0) + 0.5 * (fx_hash(vec2(cell, lp_seed + 9.0)) - 0.5));
	float x = acr - wob;
	// the load round the circle: some strokes fat and full, some leaner (0..1)
	float load = clamp(0.5 + 0.6 * lp_ring(cs, R, 0.55, 11.0), 0.0, 1.0);
	// bristle streaks laid along the stroke (~4 cm across: the brush, never sub-pixel grain)
	float br = fx_gnoise(vec2(x * 22.0, am * 0.8 + cell * 7.0 + lp_seed));
	float br2 = fx_gnoise(vec2(x * 41.0 + 3.0, am * 1.9 + cell * 5.0 + lp_seed));

	// the stroke: a pressed loaded head, an even body, a tail that narrows a little and splits into bristles (no point)
	float head = sqrt(smoothstep(0.0, 0.10, s));
	float tail = 1.0 - 0.5 * smoothstep(0.6, 1.0, s);
	float ww = lp_warm_w * lp_half * head * tail * mix(1.0, 0.88, s) * (0.86 + 0.28 * load)
		* (1.0 + 0.14 * fx_gnoise(vec2(am * 2.6, cell * 3.1 + lp_seed)));
	float d = abs(x) / max(ww, 1e-4) + 0.15 * br;
	float aa = max(fwidth(d) * 0.75, 0.16);           // a soft painted edge (~1 px), never a vector line
	float cov = 1.0 - smoothstep(1.0 - aa, 1.0 + 0.4 * aa, d);
	// dry brush: from mid-stroke the bristles part, the paint left only on the high streaks by the tail
	float paint = 1.1 - 0.9 * smoothstep(0.4, 1.0, s) * (1.15 - 0.45 * load);
	float streak = 0.5 + 0.38 * br + 0.17 * br2;
	float dry = smoothstep(-0.1, 0.1, paint - (1.0 - streak));
	// the bristles leave the ground one by one: a ragged end, each streak its own length
	dry *= 1.0 - smoothstep(0.86 + 0.12 * streak, 0.98 + 0.1 * streak, s);
	float inside = step(0.0, s0) * step(s0, 1.0);
	float warm = cov * dry * inside * smoothstep(0.0, 0.05, s);

	// the ink bed: a soft dark ground under the whole stroke, wider and a little longer, low alpha
	float si0 = fu / (duty + 2.0 * e);
	float si = clamp(si0, 0.0, 1.0);
	float ib = smoothstep(0.0, 0.18, si) * (1.0 - smoothstep(0.6, 1.0, si));
	float wi = lp_ink_w * lp_half * (0.55 + 0.45 * sqrt(ib)) * (0.9 + 0.2 * load);
	float di = abs(x - lp_ink_off * lp_half) / max(wi, 1e-4) + 0.08 * br;
	float ink = (1.0 - smoothstep(0.25, 1.0, di)) * ib * step(si0, 1.0) * (0.8 + 0.2 * load);

	float wa = warm * lp_warm_a * (0.82 + 0.18 * clamp(paint, 0.0, 1.0)), ia = ink * lp_ink_a;
	float a = wa + ia * (1.0 - wa);
	// a value step inside the paint: the thin edge and the dry tail a touch warmer, the loaded core the pale warm-white
	float edge_t = smoothstep(0.45, 1.0, abs(x) / max(ww, 1e-4)) * 0.6 + smoothstep(0.55, 1.0, s) * 0.35;
	edge_t += 0.18 * clamp(-br, 0.0, 1.0);             // the brush's own streaks: a faint value play inside the paint
	vec3 wc = mix(lp_warm, lp_warm2, clamp(edge_t, 0.0, 0.7));
	vec3 c = (wc * wa + lp_ink * ia * (1.0 - wa)) / max(a, 1e-4);
	a *= lp_alpha;
	ALBEDO = fx_out(fx_lin(c), a);
	ALPHA = a;
}
