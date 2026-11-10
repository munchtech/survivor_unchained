// P7 shapes, part B (Bladestorm and Iron Vow), included by fx_p7.gdshaderinc before p7_frag. Round 3 (9 Nov, against
// judge r2): every light shape here only works out where the pixel sits on its stroke and calls p7_stroke (the rings are
// p7_wave, mode 16 in fx_p7.gdshaderinc; the stars mode 17 = p7_star); on top only coverage caps (p7_alpha).
//   6 smear   Bladestorm's blade smear: a strip mesh swept on the blade's own path at its reach (UV.x 0 tail .. 1 head at
//             the blade, UV.y across); the core only in its leading quarter, its coverage p7_alpha at the head -> 0 at the
//             tail; life p7_fade.
//   7 seam    a Sunder line's seam in its crack: a strip mesh no wider than the crack's gap (UV.x 0 her end .. 1 the far
//             end); hot at her end, tapering out; it flares in heat (life p7_fade), never in width; p7_alpha the pulse.
//   8 dome    Iron Vow's shell: a hemisphere mesh, its interior clear; a rim p7_width px in from its outline (the
//             silhouette and where it meets the ground at p7_y0), hot at the outline and feathering inward; life p7_lvl.
//   9 glow    the vow's store on the shield's face (camera-facing): a round stroke seen end-on, core at its heart; life
//             p7_lvl (the view grows the quad).
//  10 nick    a blade's nick on a struck foe (or a blow on her shield): one short three-band stroke along p7_dir2 (screen),
//             both ends tapered; life p7_fade.
//  11 pulse   (kept for its callers) a band climbing her pose, through the stroke.

// the smear
vec4 p7_storm(vec2 p) {
	float al = clamp(p.x * 0.5 + 0.5, 0.0, 1.0);
	bool lead = al > 0.75;
	// the core lives only in the leading quarter: behind it the stroke runs a life step on (its core out), its across
	// held so its width does not step where the core ends
	float lf = lead ? p7_fade : max(p7_fade, 0.34);
	float k = lead ? 1.0 : (1.0 - 0.45 * floor(lf * 3.0 + 1e-4) / 3.0) / (1.0 - 0.45 * floor(p7_fade * 3.0 + 1e-4) / 3.0);
	vec4 o = p7_stroke(p.y * k, al, lf);
	o.a *= p7_alpha * smoothstep(0.0, 0.85, al);
	return o;
}

// the seam
vec4 p7_scar(vec2 uv) {
	float x = uv.x;
	float along = mix(0.9, 0.35, x) * smoothstep(0.0, 0.05, x);
	vec4 o = p7_stroke(uv.y * 2.0 - 1.0, along, p7_fade);
	o.a *= p7_alpha;
	return o;
}

// the dome's rim: px in from its outline (the silhouette's facing term over its own slope; the ground line's height over
// its slope), the stroke's centerline at the outline so its hot middle sits on it and its inner half feathers inward
vec4 p7_shell(vec2 uv, vec3 n, vec3 v) {
	n = normalize(n);
	float f = abs(dot(n, normalize(v)));
	float px = f / max(fwidth(f), 1e-4);
	// (r3 fix) nothing at or under the ground line: the hemisphere mesh's bottom cap (Godot flattens its lower rings onto
	// y 0) sat there as a flat disc whose height above the line, 0, made it the stroke's centerline: the opaque disc under her
	if (p7_wy <= p7_y0) return vec4(0.0);
	float hb = p7_wy - p7_y0;
	px = min(px, hb / max(fwidth(p7_wy), 1e-5));
	float ang = atan(n.y, n.x);
	// (M4 lead 14, r3d: every angle-driven term sampled on a circle, so it closes on itself; atan's jump at -x cut the band)
	vec2 cs = vec2(cos(ang), sin(ang));
	float along = 0.8 + 0.06 * fx_gnoise(cs * 3.0 + vec2(p7_seed, 0.0)) + 0.04 * fx_gnoise(cs * 11.0 + vec2(p7_seed + 2.0, 0.0));
	vec4 o = p7_stroke(px / max(p7_width, 0.5), along, p7_lvl);
	o.a *= p7_alpha;
	return o;
}

// the store's glow on the shield
vec4 p7_store(vec2 p) {
	float r = length(p), a = atan(p.y, p.x);
	float along = 0.82 + 0.08 * fx_noise(vec2(cos(a), sin(a)) * 1.3 + vec2(p7_seed, 0.0)); // (M4 lead 14: on a circle, no seam at -x)
	vec4 o = p7_stroke(r, along, p7_lvl);
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

// the nick
vec4 p7_nick(vec2 p) {
	vec2 f = normalize(p7_dir2);
	float u = dot(p, f), v = dot(p, vec2(-f.y, f.x));
	vec4 o = p7_stroke(v / 0.24, 0.9 * (1.0 - abs(u)), p7_fade);
	o.a *= p7_alpha;
	return o;
}
