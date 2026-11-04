// The ultimate's marks (H7; Fx/Flare/FlareMarksView.cs), shared by flare_mark.gdshader (the light, added) and
// flare_mark_shade.gdshader (the soft shade just outside a ring, drawn first). COLOR: rgb the light (Palette.Of(the Flare's
// school), the data's gain), a its shade's strength. INSTANCE_CUSTOM: x the kind (0 a ring, 1 the Main's ring, 2 a line
// Flare's path strip, 3 the Main's thin light up its body); y a struck ring's pop 0..1; z the pulse 0..1; w a seed.
varying flat vec4 mk;
varying flat vec4 mk_col;

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

// x: the light, y: the soft shade.
vec2 flare_mark_at(vec2 uv) {
	vec2 p = uv * 2.0 - 1.0;
	float light = 0.0, shade = 0.0;
	if (mk.x < 1.5) {
		float d = length(p);
		float pop = mk.y;
		float r = 0.66 + 0.3 * pop;
		// A painted ring: a soft band whose weight wanders a little round it (a brush, not a compass).
		float a = atan(p.y, p.x);
		float brush = 0.86 + 0.14 * sin(a * 3.0 + mk.w * 6.283) * sin(a * 5.0 - mk.w * 3.1);
		light = soft_ring(d, r, 0.085 + 0.05 * pop) * brush;
		// A faint pool inside it, the light it throws on the ground under the foe.
		light += 0.16 * (1.0 - smoothstep(0.0, r, d));
		if (mk.x > 0.5) {
			// The Main: a second, inner ring and a slow breath.
			light += 0.75 * soft_ring(d, r * 0.62, 0.06) * brush;
			light *= 0.82 + 0.18 * sin(mk.z * 6.283);
		}
		// The shade just outside (it holds by day over a pale ground).
		shade = soft_ring(d, r + 0.17, 0.11) * (1.0 - pop);
		light *= 1.0 - smoothstep(0.9, 1.0, d);
		shade *= 1.0 - smoothstep(0.88, 1.0, d);
	} else if (mk.x < 2.5) {
		// The path: soft across, faded in from her and out at its end, a slow shimmer running down it.
		float across = (uv.x - 0.5) * 2.0;
		float v = uv.y;
		light = exp(-across * across * 4.0) * smoothstep(0.0, 0.05, v) * (1.0 - smoothstep(0.8, 1.0, v));
		light *= 0.8 + 0.2 * sin(v * mk.w - mk.z * 6.283);
		shade = 0.0;
	} else {
		// The Main's thin light up its body: brightest at its feet, gone by its crown.
		float across = (uv.x - 0.5) * 2.0;
		float up = 1.0 - uv.y;
		light = exp(-across * across * 6.0) * pow(1.0 - up, 1.6) * smoothstep(0.0, 0.08, up);
		light *= 0.75 + 0.25 * sin(up * 9.0 - mk.z * 6.283 * 2.0);
	}
	return vec2(light, shade);
}
