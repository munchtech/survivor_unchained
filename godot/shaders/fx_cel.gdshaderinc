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
// (L1 W2 C5) 1: drawn after the grade (src/Fx/FxAfter.cs): the colors above are the board's displayed colors (linear, no
// emit), and fx_out() hands the pass each one premultiplied in display space.
uniform float fx_after = 0.0;

vec3 fx_srgb(vec3 c) { c = clamp(c, 0.0, 1.0); return mix(c * 12.92, 1.055 * pow(c, vec3(1.0 / 2.4)) - 0.055, step(0.0031308, c)); }
vec3 fx_lin(vec3 s) { return mix(s / 12.92, pow((s + 0.055) / 1.055, vec3(2.4)), step(0.04045, s)); }
// What ALBEDO takes for a color c at coverage a: c itself in the frame; after the grade, linear(srgb(c) x a) / a, so the
// pass's linear blend over the clear (c x a) stores srgb(c) x a, the premultiplied display color FxAfter composites.
vec3 fx_out(vec3 c, float a) { return fx_after < 0.5 ? c : fx_lin(fx_srgb(c) * a) / max(a, 1e-4); }

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

// (L1 lead 7) The painted stroke: the one shared shape every skill's light is drawn in (FX_LANGUAGE §4: a crescent, a
// ribbon, a streak, a ring are all strokes). P7's signature:
//   across: -1..1 across the stroke's width (0 its centerline); along: 0 at the tail, 1 at the head; life: 0 born, 1 dead.
// Three bands of the school's family across the width (fx_edge outside, fx_mid, fx_core inside: on the steel a feathered
// amber edge, gold, a thin white-gold core), hard steps with a narrow soft edge (LOOK_BIBLE rule 13), and fx_cel's glow
// past the edge. The head is hottest: the core widens toward it, the width thins toward the tail and with life, and
// death steps the bands out core, then mid, then edge (FX_LANGUAGE §4, never an alpha fade). What makes it painted
// (rule 5, one brush): a dry-brush edge. A small bristle field in stroke space (fine across, long streaks along) breaks
// the feathered edge and the tail into bristle streaks, wavers every band boundary like a loaded brush and puts a little
// value inside each band. Everything is in stroke space, so nothing crawls as the stroke moves.
// The stroke's shape: half-width (share of across's 1 at the head), feather (the edge's dry-brush zone, a share of the
// half-width), the tail's width (share of the head's), the head's round cap (a share of along).
uniform vec4 fx_stroke_shape = vec4(0.72, 0.3, 0.12, 0.08);
// The brush: bristles across the full width, streak length (bristle cycles over along 0..1), the dryness (how far the
// paint runs out toward the tail and with life), the boundaries' waver (a share of the half-width).
uniform vec4 fx_bristle = vec4(28.0, 12.0, 0.55, 0.2);
// Each stroke's own brush marks (set it per instance so two strokes never share bristles).
uniform float fx_stroke_seed = 0.0;

// a hard step with a narrow soft edge: one pixel of x's own slope plus `soft`
float fx_hard(float edge, float x, float soft) {
	float aa = max(fwidth(x) * 0.75, 1e-4) + soft;
	return smoothstep(edge - aa, edge + aa, x);
}

vec4 fx_stroke(float across, float along, float life) {
	// (clamped into locals: Godot 4.5 resolves an assigned argument to a same-named uniform of the including shader)
	float al = clamp(along, 0.0, 1.0);
	float lf = clamp(life, 0.0, 1.0);
	vec2 sp = vec2(across * fx_bristle.x * 0.5, al * fx_bristle.y);
	// the bristle field: gradient noise stretched along the stroke (each bristle a streak, its dry end a curved tip,
	// not value noise's lattice square), two octaves, about 0..1
	float b = clamp(0.5 + 0.42 * (fx_gnoise(sp + vec2(fx_stroke_seed * 17.3, fx_stroke_seed * 5.1)) * 0.65
		+ fx_gnoise(sp * vec2(2.3, 1.7) + vec2(3.7, fx_stroke_seed * 9.3)) * 0.35), 0.0, 1.0);
	// the brush's slow wander: the whole stroke's boundaries swell and pinch along its length
	float wander = fx_gnoise(vec2(al * 4.0 + fx_stroke_seed * 3.1, 0.5 + fx_stroke_seed));

	// the width: thins toward the tail and with life; a round cap at the head
	float w = fx_stroke_shape.x * mix(fx_stroke_shape.z, 1.0, pow(al, 0.7)) * (1.0 - 0.45 * lf);
	float cap = clamp((al - (1.0 - fx_stroke_shape.w)) / max(fx_stroke_shape.w, 1e-3), 0.0, 1.0);
	w *= sqrt(1.0 - cap * cap);
	w = max(w, 1e-4);
	// the distance from the centerline in half-widths, wavered by the bristles and the wander (a loaded brush's edge)
	float d = abs(across) / w;
	float dv = d + fx_bristle.w * ((b - 0.5) * 1.6 + wander * 0.6);

	// the bands' starts (in half-widths from the edge inward): the core widens toward the head; death steps them out,
	// the core by life 0.3, the mid by 0.6, the edge by 1 (the caller steps life per sample: the bands go in steps)
	float hot = smoothstep(0.15, 1.0, al);
	float k_core = 0.24 * hot * (1.0 - smoothstep(0.18, 0.3, lf));
	float k_mid = mix(0.48, 0.66, hot) * (1.0 - smoothstep(0.45, 0.6, lf));
	float soft = 0.02;
	float mid = fx_hard(1.0 - k_mid, 1.0 - dv, soft);
	float core = fx_hard(1.0 - k_core, 1.0 - dv, soft) * step(1e-3, k_core);

	// the dry-brush coverage: inside the feather zone (and toward the tail, and with life) a bristle holds paint only if
	// it is loaded enough: streaks of uneven length, never a smooth gradient
	float edge_in = clamp((dv - (1.0 - fx_stroke_shape.y)) / max(fx_stroke_shape.y, 1e-3), 0.0, 1.0);
	float dry = max(edge_in, fx_bristle.z * (1.0 - smoothstep(0.0, 0.35, al)));
	dry = max(dry, fx_bristle.z * smoothstep(0.55, 1.0, lf) * 1.4);
	float body = fx_hard(dry, b * 0.98 + 0.01, 0.0) * fx_hard(-1.0, -dv, 0.0) * step(lf, 0.999);

	vec3 c = mix(fx_edge, fx_mid, mid);
	c = mix(c, fx_core, core);
	// a little value inside each band: the paint's own load, along the bristles
	float load = fx_gnoise(sp * vec2(0.37, 0.53) + vec2(11.3, fx_stroke_seed * 2.3)) + 0.5 * fx_gnoise(sp * vec2(0.9, 1.3) + vec2(4.1, 7.7));
	c *= 1.0 + 0.06 * load;

	// fx_cel's glow past the edge (and in the dry brush's gaps: the light under the paint), fading with life
	float out_d = max(0.0, (abs(across) - w) / max(fx_stroke_shape.x, 1e-3));
	float g = mix(fx_glow.w, fx_glow.z, al) * (1.0 - lf) * exp(-out_d / max(fx_glow.x, 1e-3))
		* (1.0 - smoothstep(fx_glow.y * 0.6, fx_glow.y, out_d));
	return vec4(mix(fx_glow_color, c, body), max(body, g * (1.0 - body)));
}
