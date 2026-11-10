// P7 shapes, part B (Bladestorm and Iron Vow), included by fx_p7.gdshaderinc before p7_frag. Rebuilt 9 Nov (P7 lead 2,
// solver B) through the one primitive p7_stroke(across, along, life): every light shape here only works out where the
// pixel sits on its stroke and calls it; nothing is added on top but coverage caps (p7_alpha) and sparks.
//   6 smear   Bladestorm's blade smear: a strip mesh swept behind the blade (UV.x 0 tail .. 1 head at the blade,
//             UV.y across); life p7_fade; coverage cap p7_alpha.
//   7 seam    a Sunder line's seam in its crack: a strip mesh laid on the crack's centre (UV.x 0 her end .. 1 the far
//             end, UV.y across its widest); p7_width the share of the strip it fills; hot at her end, tapering out;
//             life p7_fade; p7_alpha the pulse.
//   8 dome    Iron Vow's shell: a hemisphere mesh; only a rim from the silhouette inward (across = 1 - fresnel over
//             p7_width); life p7_lvl; p7_alpha.
//   9 glow    the vow's store on the shield's face (camera-facing): a round stroke seen end-on, core at its heart;
//             life p7_lvl; a stored blow's sparks pulled inward for 3 samples (p7_t since it).
//  10 streak  tears flung along p7_dir2 (screen), 3 samples (sparks only).
//  11 pulse   (kept for its callers) a band climbing her pose, through the stroke.
//  16 ring    a ring running out (flat, the quad 2R wide): its centre at p7_prog (share of R), half-width p7_width,
//             along p7_lvl (the caller's closeness to the front: 1 hot and wide .. 0 nothing), life p7_fade.
//  17 star    one bold star: p7_count tapered spikes (root hot and thick, tip to a point, lengths varied by p7_seed)
//             round a solid core disc; life p7_fade; flat on the ground or camera-facing (p7_bill).

// the smear
vec4 p7_storm(vec2 p) {
	float along = p.x * 0.5 + 0.5;
	vec4 o = p7_stroke(p.y, along, p7_fade);
	o.a *= p7_alpha;
	return o;
}

// the seam
vec4 p7_scar(vec2 uv) {
	float x = uv.x;
	// hot at her end, a long taper to the far end, the near end drawn to a point too
	float along = mix(1.0, 0.35, x) * smoothstep(0.0, 0.05, x);
	along *= 0.9 + 0.1 * fx_noise(vec2(x * 9.0, p7_seed));
	vec4 o = p7_stroke((uv.y * 2.0 - 1.0) / max(p7_width, 0.05), along, p7_fade);
	o.a *= p7_alpha;
	return o;
}

// the dome
vec4 p7_shell(vec3 n, vec3 v) {
	n = normalize(n);
	float f = abs(dot(n, normalize(v)));
	float ang = atan(n.y, n.x);
	float along = 0.72 + 0.28 * fx_noise(vec2(ang * 1.6 + p7_t * 0.7, p7_seed));
	// the silhouette is the stroke's centerline: its outer half falls off the mesh, the inner half runs inward
	vec4 o = p7_stroke(f / max(p7_width, 0.02), along, p7_lvl);
	o.a *= p7_alpha;
	return o;
}

// the store's glow on the shield
vec4 p7_store(vec2 p) {
	float r = length(p), a = atan(p.y, p.x);
	float along = 0.86 + 0.14 * fx_noise(vec2(a * 1.3, p7_seed));
	vec4 o = p7_stroke(r, along, p7_lvl);
	if (p7_t < 3.0 * P7_SAMPLE) {
		vec2 q = vec2(r + p7_t * 4.5, a * 0.6);
		float sp = fx_sparks(q, vec2(-1.0, 0.0), 0.12, 0.5, 0.18, 3.5, p7_seed * 13.0);
		sp *= smoothstep(0.3, 0.5, r) * (1.0 - smoothstep(0.85, 1.0, r));
		o = vec4(mix(o.rgb, fx_spark_color, sp * (1.0 - o.a)), max(o.a, sp));
	}
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

vec4 p7_streak(vec2 p) {
	vec2 f = normalize(p7_dir2);
	vec2 q = p - f * p7_t * 5.0;
	float sp = fx_sparks(q, f, 0.16, 0.55, 0.32, 4.0, p7_seed * 7.0);
	float cone = smoothstep(0.35, 0.7, dot(normalize(p + 1e-4), f)) * (1.0 - smoothstep(0.75, 1.0, length(p)));
	sp *= cone * step(p7_t, 3.0 * P7_SAMPLE);
	float hot = 1.0 - smoothstep(0.0, 2.0 * P7_SAMPLE, p7_t);
	return vec4(mix(fx_spark_color, fx_core, hot), sp);
}

// the ring
vec4 p7_bring(vec2 p) {
	float r = length(p), a = atan(p.y, p.x);
	float front = p7_prog * (1.0 + 0.012 * (fx_noise(vec2(a * 4.0, p7_seed)) - 0.5));
	float along = p7_lvl * (0.82 + 0.18 * fx_noise(vec2(a * 2.2, p7_seed + 3.0)));
	float x = (r - front) / max(p7_width, 1e-3);
	vec4 o = p7_stroke(x, along, p7_fade);
	// M4 lead 14 (HUD judge r3c, 21/22: "flat hard orange, dashed"): the stroke's outer lip feathered, and a soft wash
	// falling off inward behind the front (the air the vow threw out), in the stroke's own heart color at its life, so
	// the ring reads as a front on the ground and not as a hard painted hoop. Occlusion stays the one world rule
	// (FxWorldDepth): a canopy in front covers it; the top shader was tried and drew it over her and the firs alike.
	// the band's real half-width in x (fx_stroke thins it toward the tail and with its stepped life)
	float lf = floor(clamp(p7_fade, 0.0, 1.0) * 3.0 + 1e-4) / 3.0;
	float we = max(mix(fx_stroke_shape.z, 1.0, pow(clamp(along, 0.0, 1.0), 0.7)) * (1.0 - 0.45 * lf), 0.05);
	o.a *= (1.0 - smoothstep(0.15 * we, we, x)) * smoothstep(-we, -0.25 * we, x);
	vec4 h = p7_stroke(0.0, along * 0.6, p7_fade);
	float behind = max(front - r, 0.0) / max(front, 1e-3);
	float wash = h.a * 0.42 * exp(-behind * 20.0) * smoothstep(0.1 * we, -0.5 * we, x) * (0.7 + 0.3 * fx_noise(vec2(a * 3.0, p7_seed + 7.0)));
	// the front's lip runs hot (the core's pale gold), its body the mid, then the wash: a value ramp, never one flat band
	o.rgb = mix(o.rgb, fx_core, 0.6 * smoothstep(-0.1 * we, 0.55 * we, x));
	float al = max(o.a, wash);
	vec3 rgb = mix(h.rgb, o.rgb, al > 1e-4 ? o.a / al : 1.0);
	return vec4(rgb, al * p7_alpha);
}

// the star
vec4 p7_bstar(vec2 p) {
	float r = length(p), a = atan(p.y, p.x);
	float n = clamp(p7_count, 3.0, 9.0);
	// the core disc first: a round stroke seen end-on
	float bestq = r / 0.16;
	float bx = r / 0.16, ba = 1.0;
	for (int k = 0; k < 9; k++) {
		if (float(k) >= n) break;
		float h0 = fx_hash(vec2(float(k), p7_seed));
		float h1 = fx_hash(vec2(float(k) + 3.7, p7_seed));
		float ak = (float(k) + 0.35 * (h0 - 0.5)) * P7_TAU / n + p7_seed;
		float len = mix(0.55, 1.0, h1) * (k % 2 == 0 ? 1.0 : 0.72);
		float d = mod(a - ak + 3.14159265, P7_TAU) - 3.14159265;
		float along = 1.0 - r / len;
		if (along <= 0.0 || abs(d) > 1.2) continue;
		float across = r * sin(d) / 0.075;
		float q = abs(across) / max(pow(along, 0.75), 1e-3);
		if (q < bestq) { bestq = q; bx = across; ba = along; }
	}
	vec4 o = p7_stroke(bx, ba, p7_fade);
	o.a *= p7_alpha;
	return o;
}
