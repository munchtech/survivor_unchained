// The ultimate's marks (H7; Fx/Flare/FlareMarksView.cs; data/content/flare_family.json "marks"), for flare_mark.gdshader.
// H7 r2 (judge r1 fix 5: "rings to light POOLS"): each mark is a soft radial pool of the school's light on the ground, no
// stroke and no edge (FLARE_LOOK §3.5: a gaussian never makes an edge; LOOK_BIBLE row 8: light on the ground hugging the
// feet), the light the foe stands in. The Main is twice the pool with a hot inner core, so it reads with no ray.
// COLOR: rgb the light (Palette.Of(the Flare's school) x the data's gain and the mark's envelope), a its shade's strength.
// INSTANCE_CUSTOM: x the kind (0 a pool, 1 the Main's pool, 2 a line Flare's path seam); y unused; z the pulse 0..1;
// w a seed (the seam: its length, m).
varying flat vec4 mk;
varying flat vec4 mk_col;
uniform float cap = 0.75;        // the most the marks sum to (their light's max channel)
uniform float pool_k = 2.4;      // the pool's falloff's power (2 a gaussian; higher a flatter top, still no edge)
uniform float core = 0.32;       // the Main's core's radius (x the pool's) ...
uniform float core_gain = 1.4;   // ... and its light (x the pool's peak)
uniform float warm = 0.3;        // how far the pool's heart leans to warm_hue (light she casts with it)
uniform vec3 warm_hue = vec3(1.0, 0.62, 0.32);
uniform float seam_core = 0.2;   // the seam's core and glow half-widths (x the strip's half-width)
uniform float seam_glow = 0.4;

void vertex() {
	mk = INSTANCE_CUSTOM;
	mk_col = COLOR;
	// (writing POSITION in any branch makes Godot drop the default transform for every vertex, so it is written for all)
	POSITION = PROJECTION_MATRIX * (VIEW_MATRIX * (MODEL_MATRIX * vec4(VERTEX, 1.0)));
}

// The quad's half is 2.2 of the pool's sigma: its light is under 1% there, and a window takes the last of it.
const float MK_SIG = 1.0 / 2.2;

// x: the pool's light, y: its warm heart's light, z: the soft shade.
vec3 flare_mark_at(vec2 uv) {
	vec2 p = uv * 2.0 - 1.0;
	float light = 0.0, heart = 0.0, shade = 0.0;
	if (mk.x < 1.5) {
		float d = length(p);
		float x = d / MK_SIG;
		float win = 1.0 - smoothstep(0.85, 1.0, d);
		light = exp(-pow(x, pool_k)) * win;
		// The Main: a hot core in its pool, breathing slowly.
		if (mk.x > 0.5) {
			float c = d / (MK_SIG * core);
			heart = exp(-c * c) * core_gain * (0.85 + 0.15 * sin(mk.z * 6.283));
		}
		heart += light * warm * exp(-x * x * 2.0);
		// The soft shade: wider than the light and fainter, so the pool sits in a little dark by day (never a ring).
		shade = exp(-pow(x / 1.5, 2.0)) * win;
	} else {
		// The path: a thin lit seam, a narrow core in a soft falloff, faded in from her and out at its end, a slow
		// shimmer running outward along it.
		float across = abs(uv.x - 0.5) * 2.0;
		float v = uv.y;
		float co = exp(-pow(across / max(seam_core, 1e-3), 2.0));
		float glow = exp(-across / max(seam_glow, 1e-3)) * (1.0 - smoothstep(0.7, 1.0, across));
		light = (co + 0.35 * glow) * smoothstep(0.0, 0.04, v) * (1.0 - smoothstep(0.8, 1.0, v));
		light *= 0.7 + 0.3 * sin(v * mk.w * 0.9 - mk.z * 6.283);
	}
	return vec3(light, heart, shade);
}
