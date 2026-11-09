// P7 shapes, part B (Bladestorm and Iron Vow: storm, scar, shell, store, pulse, streak), included by fx_p7.gdshaderinc
// before p7_frag. Split from fx_p7.gdshaderinc on 9 Nov (P7 lead 2) so the two rebuilds edit separate files.

vec4 p7_storm(vec2 p) {
	float r = length(p), a = atan(p.y, p.x);
	float n = clamp(p7_count, 1.0, 6.0), trail = max(0.05, p7_trail * p7_prog);
	float heat = -1.0, along = 0.0;
	for (int k = 0; k < 6; k++) {
		if (float(k) >= n) break;
		float h = p7_spin + float(k) * P7_TAU / n;
		// behind the head along its way: 0 at the head, 1 at the trail's end; a short round nose ahead of it
		float d = mod((h - a) * p7_dir, P7_TAU);
		float u = d > P7_TAU - 0.16 ? (d - P7_TAU) / trail : d / trail;
		if (u > 1.0) continue;
		float rc = mix(0.88, 0.72, clamp(u, 0.0, 1.0));
		float w0 = 0.075;
		float w = u < 0.0 ? w0 * sqrt(max(0.0, 1.0 - pow(u / (0.13 / trail), 2.0))) : w0 * pow(1.0 - u, 0.85);
		w *= 1.0 + 0.22 * (fx_gnoise(vec2(u * 6.0 + float(k) * 3.1, p7_seed)) - 0.5);
		float prof = 1.0 - abs(r - rc) / max(w, 1e-4);
		// the gold carries the crescent (its heat under the core's cut); the white-gold is only the thin leading lip: the
		// nose and the first few percent of the arc, on the blade's outer half
		float body = (prof > 0.0 ? min(prof / 0.45, 1.0) : prof * 0.35);
		float lip = (1.0 - smoothstep(0.0, 0.07, u)) * smoothstep(0.35, 0.75, prof);
		float hk = body * mix(0.62, 0.2, pow(clamp(u, 0.0, 1.0), 0.75)) + lip * 0.5;
		// painted bites in the tail, holes as it erodes
		hk -= 0.16 * fx_noise(vec2(u * 11.0, r * 24.0) + p7_seed + float(k)) * clamp(u, 0.0, 1.0);
		hk -= p7_fade * 0.9 + p7_fade * 0.6 * fx_noise(p * 10.0 + p7_seed);
		if (hk > heat) { heat = hk; along = 1.0 - clamp(u, 0.0, 1.0); }
	}
	return fx_cel(heat, along);
}

vec4 p7_scar(vec2 uv) {
	float x = uv.x, y = uv.y * 2.0 - 1.0;
	float cy = 0.34 * (fx_gnoise(vec2(x * 7.0, p7_seed)) - 0.5) + 0.12 * (fx_noise(vec2(x * 23.0, p7_seed + 4.0)) - 0.5);
	float ends = smoothstep(0.0, 0.04, x) * (1.0 - smoothstep(0.93, 1.0, x));
	float pw = 0.07 * (0.75 + 0.5 * fx_noise(vec2(x * 31.0, p7_seed + 9.0)));
	float lvl = 0.6, w = pw;
	if (p7_prog >= 0.0 && x <= p7_prog) {
		// split: the crack opens behind the front; the front itself is the hottest
		float behind = p7_prog - x;
		w = mix(pw * 2.2, 0.24, clamp(behind * 5.0, 0.0, 1.0));
		lvl = p7_lvl + max(0.0, 0.5 - behind * 6.0) * step(p7_prog, 0.999);
	} else if (p7_prog < 0.0) lvl = p7_lvl;
	float prof = 1.0 - abs(y - cy) / w;
	float heat = (prof > 0.0 ? min(prof / 0.5, 1.0) : prof * 0.3) * lvl * ends;
	heat -= p7_fade * 0.9 + p7_fade * 0.6 * fx_noise(uv * vec2(40.0, 4.0) + p7_seed);
	return fx_cel(heat, 0.5 + 0.5 * x);
}

vec4 p7_shell(vec2 p) {
	float r = length(p), a = atan(p.y, p.x) + p7_t * 0.9 + p7_seed;
	float w = p7_width * (1.0 + 0.3 * fx_gnoise(vec2(a * 3.0, p7_seed)));
	float prof = 1.0 - abs(r - 0.86) / w;
	// four arcs, ragged gaps between that close a step at each store level (never shut: it stays four arcs)
	float seg = fract(a / P7_TAU * 4.0);
	float gap = mix(0.12, 0.05, p7_prog) * (1.0 + 0.4 * fx_noise(vec2(a * 5.0, r * 30.0))) - min(seg, 1.0 - seg);
	prof -= max(0.0, gap) * 12.0;
	float heat = (prof > 0.0 ? min(prof / 0.5, 1.0) : prof * 0.25) * p7_lvl;
	heat -= p7_fade * 0.9 + p7_fade * 0.6 * fx_noise(p * 9.0 + p7_seed);
	vec4 o = fx_cel(heat, 0.4);
	o.a *= p7_alpha;
	return o;
}

vec4 p7_store(vec2 p) {
	float r = length(p), a = atan(p.y, p.x);
	float lv = p7_prog;
	float hit = p7_t < P7_SAMPLE ? 0.22 : 0.0;
	// the disc: a white-gold heart ringed in gold, an amber lip
	float rad = 0.14 + 0.18 * lv + hit * 0.2;
	float heat = lv > 0.001 ? (1.0 - r / rad) * (1.0 + 0.35 * lv) : -1.0;
	// the flare: four thin spikes off it, longer a step at each level (gold along their length, white only at the root)
	float len = 0.3 + 0.62 * lv + hit;
	float arms = max(1.0 - abs(p.y) * 22.0 - abs(p.x) / len, 1.0 - abs(p.x) * 22.0 - abs(p.y) / len);
	if (lv > 0.001) heat = max(heat, arms * 0.95 - 0.05);
	vec4 o = fx_cel(heat, 1.0);
	// the stored blow: tears pulled inward to the shield's heart, 3 samples
	if (p7_t < 3.0 * P7_SAMPLE) {
		vec2 q = vec2(r + p7_t * 4.5, a * 0.6);
		float sp = fx_sparks(q, vec2(-1.0, 0.0), 0.12, 0.5, 0.18, 3.5, p7_seed * 13.0 + floor(p7_t * 0.0));
		sp *= smoothstep(0.12, 0.3, r) * (1.0 - smoothstep(0.8, 1.0, r));
		float body = fx_step(fx_t.x, heat);
		o = vec4(mix(o.rgb, fx_spark_color, sp * (1.0 - body)), max(o.a, sp));
	}
	o.a *= 1.0 - p7_fade;
	return o;
}

vec4 p7_pulse(vec3 n, vec3 v) {
	float y = (p7_wy - p7_y0) / max(p7_h, 0.1);
	float front = p7_t / (3.0 * P7_SAMPLE) * 1.15;
	float d = front - y;
	if (d < 0.0 || d > 0.2 || front > 1.25) return vec4(0.0);
	// a flat gold band, its trailing lip the edge band, at the figure's silhouette the edge too
	float rim = 1.0 - clamp(abs(dot(normalize(n), normalize(v))), 0.0, 1.0);
	float heat = (d > 0.13 || rim > 0.7) ? 0.15 : 0.5;
	vec4 o = fx_cel(heat, 0.5);
	o.a *= p7_alpha;
	return o;
}

vec4 p7_streak(vec2 p) {
	vec2 f = normalize(p7_dir2);
	vec2 q = p - f * p7_t * 5.0;
	float sp = fx_sparks(q, f, 0.16, 0.55, 0.32, 4.0, p7_seed * 7.0);
	// a cone along the flight, gone by the third sample
	float cone = smoothstep(0.35, 0.7, dot(normalize(p + 1e-4), f)) * (1.0 - smoothstep(0.75, 1.0, length(p)));
	sp *= cone * step(p7_t, 3.0 * P7_SAMPLE);
	float hot = 1.0 - smoothstep(0.0, 2.0 * P7_SAMPLE, p7_t);
	return vec4(mix(fx_spark_color, fx_core, hot), sp);
}
