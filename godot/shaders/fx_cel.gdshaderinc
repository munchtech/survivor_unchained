// The FX band rules (L1 B6; docs/design/LOOK_BIBLE.md rule 13; data/look/fx_language.json, read by
// logic/Look/FxLanguage.cs and set by src/Fx/FxCel.cs). A spell is a hard graphic shape drawn in two or three
// stepped bands of a 1D heat gradient (edge, mid, core in rising heat), a soft outer glow past its edge, and
// painted sparks: small hard tears, never soft dots. The bands' colors are each school's (Palette.Of's hues, MB5's
// values), given linear and already multiplied by their emit (the gain that lands them on the board's colors through
// the night's exposure, AgX and grade): the only fully saturated pixels at night are these.
// An effect's shader includes this file, builds its own heat field (its shape), and calls fx_cel():
//   heat >= fx_t.x is the body (fx_t.x is the cut, usually 0); fx_t.y the mid band's start, fx_t.z the core's
//   (fx_t.y = fx_t.z for two bands); below the cut the glow falls off over -heat in fx_glow.x (e-fold) to fx_glow.y.

uniform vec3 fx_edge = vec3(0.6, 0.06, 0.012);
uniform vec3 fx_mid = vec3(0.97, 0.25, 0.017);
uniform vec3 fx_core = vec3(1.0, 0.78, 0.31);
uniform vec4 fx_t = vec4(0.0, 0.34, 0.75, 0.0);
uniform vec3 fx_glow_color = vec3(0.13, 0.02, 0.013);
// width (e-fold), reach (where it ends), strength at the head, strength at the tail (the effect's own 0..1 along it)
uniform vec4 fx_glow = vec4(0.13, 0.35, 0.65, 0.30);
uniform vec3 fx_spark_color = vec3(0.64, 0.16, 0.003);

// A band edge: hard, antialiased over a pixel of the heat's own slope.
float fx_step(float t, float heat) {
	float aa = max(fwidth(heat) * 0.75, 1e-4);
	return smoothstep(t - aa, t + aa, heat);
}

// The bands and the glow at a point of heat; `along` is 0 at the effect's tail and 1 at its head (the glow's strength
// runs between fx_glow.w and fx_glow.z). Returns the color (linear, pre-gained) and its coverage (for blend_mix).
vec4 fx_cel(float heat, float along) {
	float body = fx_step(fx_t.x, heat);
	vec3 c = mix(fx_edge, fx_mid, fx_step(fx_t.y, heat));
	c = mix(c, fx_core, fx_step(fx_t.z, heat));
	float out_d = max(0.0, fx_t.x - heat);
	float g = mix(fx_glow.w, fx_glow.z, clamp(along, 0.0, 1.0)) * exp(-out_d / max(fx_glow.x, 1e-3)) * (1.0 - smoothstep(fx_glow.y * 0.6, fx_glow.y, out_d));
	// The glow is the edge band's light thrown on the dark: its color at the board's glow, its coverage its strength.
	return vec4(mix(fx_glow_color, c, body), max(body, g * (1.0 - body)));
}

float fx_hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }

float fx_noise(vec2 p) {
	vec2 i = floor(p), f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(fx_hash(i), fx_hash(i + vec2(1.0, 0.0)), u.x), mix(fx_hash(i + vec2(0.0, 1.0)), fx_hash(i + vec2(1.0, 1.0)), u.x), u.y);
}

// Gradient noise (-1..1): its contours curve, where value noise's follow its lattice (a band cut through value noise
// steps in squares).
vec2 fx_grad(vec2 i) { float a = fx_hash(i) * 6.2831853; return vec2(cos(a), sin(a)); }
float fx_gnoise(vec2 p) {
	vec2 i = floor(p), f = fract(p);
	vec2 u = f * f * f * (f * (f * 6.0 - 15.0) + 10.0);
	float a = dot(fx_grad(i), f), b = dot(fx_grad(i + vec2(1.0, 0.0)), f - vec2(1.0, 0.0));
	float c = dot(fx_grad(i + vec2(0.0, 1.0)), f - vec2(0.0, 1.0)), d = dot(fx_grad(i + vec2(1.0, 1.0)), f - vec2(1.0, 1.0));
	return mix(mix(a, b, u.x), mix(c, d, u.x), u.y) * 1.6;
}

// Painted sparks: in cells of `cell` (the effect's own units), one in `density` of them holds a small hard tear
// `len` long (aspect `asp`), laid along `flow` (a unit 2D direction). Returns its coverage, antialiased.
float fx_sparks(vec2 p, vec2 flow, float cell, float density, float len, float asp, float seed) {
	vec2 q = p / cell;
	vec2 id = floor(q);
	float cov = 0.0;
	for (int j = -1; j <= 1; j++)
		for (int i = -1; i <= 1; i++) {
			vec2 c = id + vec2(float(i), float(j));
			float h = fx_hash(c + seed);
			if (h > density) continue;
			vec2 at = (c + vec2(fx_hash(c + seed + 7.1), fx_hash(c + seed + 3.3))) * cell;
			float l = len * (0.6 + 0.8 * fx_hash(c + seed + 9.7));
			vec2 d = p - at;
			vec2 r = vec2(dot(d, flow), dot(d, vec2(-flow.y, flow.x)));
			// a tear: round at its head, drawn to a point behind
			float k = clamp(-r.x / l, 0.0, 1.0);
			float w = l / asp * 0.5 * (1.0 - k);
			float sd = r.x > 0.0 ? length(r) - l / asp * 0.5 : abs(r.y) - w;
			sd = max(sd, -r.x - l);
			float aa = max(fwidth(sd), 1e-4);
			cov = max(cov, 1.0 - smoothstep(-aa, aa, sd));
		}
	return cov;
}
