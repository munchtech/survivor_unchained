// The ultimate's marks (H7; Fx/Flare/FlareMarksView.cs; data/content/flare_family.json "marks"), for flare_mark.gdshader.
// COLOR: rgb the light (Palette.Of(the Flare's school) x the data's gain and the mark's envelope), a its shade's strength.
// INSTANCE_CUSTOM: x the kind (0 a ring, 1 the Main's ring, 2 a line Flare's path seam, 3 the Main's thin light up its
// body); y a struck ring's pop 0..1; z the pulse 0..1; w a seed (the seam: its length, m).
varying flat vec4 mk;
varying flat vec4 mk_col;
uniform float cap = 0.75;        // the most the marks sum to (their light's max channel)
uniform float band = 0.07;       // the ring's band (x the ring's radius)
uniform float pool = 0.14;       // the pool inside it (x the ring's light)
uniform float warm = 0.45;       // how far the pool leans to warm_hue
uniform vec3 warm_hue = vec3(1.0, 0.62, 0.32);
uniform float pop_grow = 0.45;   // a pop's growth (x the ring)
uniform float seam_core = 0.2;   // the seam's core and glow half-widths (x the strip's half-width)
uniform float seam_glow = 0.4;

void vertex() {
	mk = INSTANCE_CUSTOM;
	mk_col = COLOR;
	if (mk.x > 2.5) {
		// The pillar faces the camera about the world's up, standing on its foot.
		vec3 org = (MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
		float w = length(MODEL_MATRIX[0].xyz), h = length(MODEL_MATRIX[1].xyz);
		vec3 right = normalize(vec3(INV_VIEW_MATRIX[0].x, 0.0, INV_VIEW_MATRIX[0].z));
		vec3 world = org + right * VERTEX.x * w + vec3(0.0, 1.0, 0.0) * (VERTEX.y + 0.5) * h;
		POSITION = PROJECTION_MATRIX * (VIEW_MATRIX * vec4(world, 1.0));
	} else {
		// (writing POSITION in any branch makes Godot drop the default transform for every vertex: the flat marks, the
		// rings and the strip, must write it too, or they collapse to one point and never show)
		POSITION = PROJECTION_MATRIX * (VIEW_MATRIX * (MODEL_MATRIX * vec4(VERTEX, 1.0)));
	}
}

float soft_ring(float d, float r, float w) { float x = (d - r) / w; return exp(-x * x); }

// x: the band's light, y: the pool's light, z: the soft shade. (The quad's half is the popped ring's outer edge, 1.)
vec3 flare_mark_at(vec2 uv) {
	vec2 p = uv * 2.0 - 1.0;
	float light = 0.0, pl = 0.0, shade = 0.0;
	if (mk.x < 1.5) {
		float d = length(p);
		float pop = mk.y;
		float r0 = 1.0 / (1.0 + pop_grow + 0.25);
		float r = r0 * (1.0 + pop_grow * pop);
		// One soft band whose weight wanders a little round it (a brush, not a compass), thinning as it pops.
		float a = atan(p.y, p.x);
		float brush = 0.8 + 0.2 * sin(a * 3.0 + mk.w * 6.283) * sin(a * 5.0 - mk.w * 3.1);
		light = soft_ring(d, r, band * r0 * (1.0 + 0.6 * pop)) * brush;
		// The pool: the light it throws on the ground under the foe, gone as the ring pops out.
		pl = pool * (1.0 - smoothstep(0.0, r0, d)) * (1.0 - pop);
		if (mk.x > 0.5) light *= 0.8 + 0.2 * sin(mk.z * 6.283);
		// The shade just outside the band, only while the ring stands (a pop takes it at once).
		shade = soft_ring(d, r0 * (1.0 + 2.5 * band), band * r0 * 1.6) * (1.0 - smoothstep(0.0, 0.25, pop));
		float edge = 1.0 - smoothstep(0.92, 1.0, d);
		light *= edge; shade *= edge;
	} else if (mk.x < 2.5) {
		// The path: a thin lit seam, a narrow core in a soft falloff, faded in from her and out at its end, a slow
		// shimmer running outward along it.
		float across = abs(uv.x - 0.5) * 2.0;
		float v = uv.y;
		float core = exp(-pow(across / max(seam_core, 1e-3), 2.0));
		float glow = exp(-across / max(seam_glow, 1e-3)) * (1.0 - smoothstep(0.7, 1.0, across));
		light = (core + 0.35 * glow) * smoothstep(0.0, 0.04, v) * (1.0 - smoothstep(0.8, 1.0, v));
		light *= 0.7 + 0.3 * sin(v * mk.w * 0.9 - mk.z * 6.283);
	} else {
		// The Main's thin light up its body: brightest at its feet, gone by its crown.
		float across = (uv.x - 0.5) * 2.0;
		float up = 1.0 - uv.y;
		light = exp(-across * across * 6.0) * pow(1.0 - up, 1.6) * smoothstep(0.0, 0.08, up);
		light *= 0.75 + 0.25 * sin(up * 9.0 - mk.z * 6.283 * 2.0);
	}
	return vec3(light, pl, shade);
}
