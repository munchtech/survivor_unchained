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
uniform float lp_duty = 0.56;      // share of each cell a dab fills
uniform float lp_circ = 31.4;      // the circumference (m): the brush runs in meters, never stretched
uniform float lp_half = 0.13;      // the ribbon's half-width (m)
uniform float lp_warm_w = 0.30;    // the warm stroke's half-width (share of lp_half)
uniform float lp_ink_w = 0.62;     // the under-stroke's half-width
uniform float lp_ink_off = 0.16;   // the under-stroke sits this far outward (its dark lip shows on the far side)
uniform vec3 lp_warm = vec3(1.0, 0.945, 0.84);   // #fff1d6 (sRGB display colors, linearized at the end)
uniform vec3 lp_warm2 = vec3(1.0, 0.86, 0.62);   // its loaded-brush edge, a touch warmer
uniform vec3 lp_ink = vec3(0.141, 0.11, 0.071);  // #241c12
uniform float lp_warm_a = 0.85;
uniform float lp_ink_a = 0.5;
uniform float lp_seed = 0.0;

// one painted dab's coverage at `d` (|across| in shares of lp_half) with half-width `w`; s = 0..1 along the dab
float lp_dab(float across, float s, float w, float m, float cell, float soft) {
	// a brush's dab: full body, ends drawn in (a lens with a fat middle), the end a curved dry tip
	float body = pow(clamp(sin(3.14159 * s), 0.0, 1.0), 0.32);
	float wv = fx_gnoise(vec2(m * 1.7, cell * 3.1 + lp_seed)) * 0.18;
	float d = abs(across) / max(w * body * (1.0 + wv), 1e-3);
	// bristles: streaks along the dab (in meters), wavering the edge and thinning the paint at the ends
	float b = fx_gnoise(vec2(across * lp_half * 90.0, m * 2.2 + cell * 7.0 + lp_seed));
	float dv = d + 0.22 * b;
	float aa = max(fwidth(dv) * 0.75, 1e-3) + soft;
	float cov = 1.0 - smoothstep(1.0 - aa, 1.0 + aa, dv);
	float endz = 1.0 - smoothstep(0.0, 0.22, min(s, 1.0 - s));
	return cov * (1.0 - endz * smoothstep(-0.2, 0.5, b) * 0.85);
}

void fragment() {
	float u = UV.x * lp_count;
	float cell = floor(u);
	float jit = fx_hash(vec2(cell, lp_seed + 1.0));
	float duty = lp_duty * (0.88 + 0.24 * jit);
	float s0 = fract(u) / duty;
	float m = UV.x * lp_circ;
	float across = UV.y;
	float inside = step(s0, 1.0);
	float s = clamp(s0, 0.0, 1.0);
	float warm = lp_dab(across + 0.05 * fx_gnoise(vec2(m * 0.6, lp_seed)), s, lp_warm_w, m, cell, 0.02) * inside;
	// the under-stroke: wider, a hair longer (it runs past each dab's ends), set outward
	float si = clamp((fract(u) + 0.03) / (duty + 0.06), 0.0, 1.0);
	float inside_i = step((fract(u) + 0.03) / (duty + 0.06), 1.0);
	float ink = lp_dab(across - lp_ink_off, si, lp_ink_w, m + 3.0, cell + 0.5, 0.08) * inside_i;
	float wa = warm * lp_warm_a, ia = ink * lp_ink_a;
	float a = wa + ia * (1.0 - wa);
	vec3 wc = mix(lp_warm, lp_warm2, smoothstep(0.35, 1.0, abs(across) / lp_warm_w) * 0.7);
	vec3 c = (wc * wa + lp_ink * ia * (1.0 - wa)) / max(a, 1e-4);
	a *= lp_alpha;
	ALBEDO = fx_out(fx_lin(c), a);
	ALPHA = a;
}
