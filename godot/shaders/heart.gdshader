// The Warden's heart (E7c, look bible 10 "The trick" 4): a fist-sized wet stone with cold light in its cracks.
// The mesh (tools/assets/env_heart.py) carries the broad chipped faces and the bake (COLOR: r edge wear, g cavity,
// b broad occlusion); everything finer is drawn here in the stone's own space, so it stays sharp at an 85 mm close-up:
//   the stone: the one stone sheet (stone_albedo, E5) triplanar, darkened cool, its grain a bump;
//   the veins: cracks along the borders of a warped 3D cell pattern, broken where a slow noise says (cracks that run
//     and stop, a few finer ones off them); each a groove in the surface, only its thin core over the glow threshold,
//     a faint light in the stone either side and a scorched dark rim between;
//   the water: a wet film (dark albedo, low roughness) with streaks running DOWN the world as the stone turns.
// beat (0..1, the heartbeat's shape) and level (the orb's Light) come from OrbView each frame, so the veins and the
// light pulse together, the same in every run (no TIME).
shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_back, diffuse_burley, specular_schlick_ggx;

uniform sampler2D stone_tex : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform float tex_rep = 1.3;                 // the sheet's repeats across the unit stone
uniform vec3 tint : source_color = vec3(0.64, 0.68, 0.74);  // the heart's stone: a cool dark slate
uniform float grain_bump = 0.004;            // the grain's relief (unit-stone lengths)
uniform vec3 vein_color : source_color = vec3(0.62, 0.86, 1.0);
uniform float vein_scale = 0.9;              // crack cells across the unit stone
uniform float vein_warp = 0.22;
uniform float vein_core = 0.010;             // the bright core's half-width (unit-stone lengths)
uniform float vein_glow_w = 0.035;           // the light in the stone either side
uniform float vein_energy = 7.0;             // the core's emission at level 1, beat mid
uniform float vein_glow = 0.2;               // the light in the stone's emission (kept under the glow threshold)
uniform float vein_gate = 0.6;               // how much of the cell border network is a crack (higher: fewer)
uniform float vein_fine = 0.25;              // the finer cracks' share
uniform float groove = 0.012;                // a crack's depth (unit-stone lengths)
uniform float scorch = 0.55;                 // the dark rim either side of a crack
uniform float beat_amp = 0.38;               // the veins' swing about their mean (+-)
uniform float beat = 0.5;
uniform float level = 1.0;
uniform float wet = 1.0;
uniform float flow_t = 0.0;
uniform float unit = 0.05;                   // world metres per unit-stone length (OrbView: its scale)

varying vec3 op;
varying vec3 on;
varying vec3 wd;   // world direction from the stone's middle, in unit-stone lengths (streaks run down this)

// An integer hash of a lattice point (its coordinates are whole numbers): exact, so two neighbouring pixels that
// reach the same point by different sums hash it alike (a sin() hash flips on one ulp: blocks in the cracks, E7c).
vec3 hash3(vec3 p) {
	uvec3 q = uvec3(ivec3(floor(p + 0.5)) + 65536);
	q = q * uvec3(1597334673u, 3812015801u, 2798796415u);
	q = uvec3(q.x ^ q.y ^ q.z) * uvec3(1597334673u, 3812015801u, 2798796415u);
	return vec3(q) * (1.0 / 4294967295.0);
}

float vnoise(vec3 p) {
	vec3 i = floor(p), f = fract(p);
	vec3 u = f * f * (3.0 - 2.0 * f);
	float a = hash3(i).x, b = hash3(i + vec3(1, 0, 0)).x, c = hash3(i + vec3(0, 1, 0)).x, d = hash3(i + vec3(1, 1, 0)).x;
	float e = hash3(i + vec3(0, 0, 1)).x, g = hash3(i + vec3(1, 0, 1)).x, h = hash3(i + vec3(0, 1, 1)).x, k = hash3(i + vec3(1, 1, 1)).x;
	return mix(mix(mix(a, b, u.x), mix(c, d, u.x), u.y), mix(mix(e, g, u.x), mix(h, k, u.x), u.y), u.z);
}

// Distance to the nearest cell border (iq's exact voronoi borders), in cell units.
float border(vec3 x) {
	vec3 n = floor(x), f = fract(x);
	vec3 mg = vec3(0.0), mr = vec3(0.0);
	float md = 8.0;
	for (int k = -1; k <= 1; k++) for (int j = -1; j <= 1; j++) for (int i = -1; i <= 1; i++) {
		vec3 g = vec3(float(i), float(j), float(k));
		vec3 r = g + hash3(n + g) - f;
		float d = dot(r, r);
		if (d < md) { md = d; mr = r; mg = g; }
	}
	md = 8.0;
	// (the second pass over 5x5x5 about the nearest: 3x3x3 jogs the borders where a farther pair is nearer)
	for (int k = -2; k <= 2; k++) for (int j = -2; j <= 2; j++) for (int i = -2; i <= 2; i++) {
		vec3 g = mg + vec3(float(i), float(j), float(k));
		vec3 r = g + hash3(n + g) - f;
		if (dot(mr - r, mr - r) > 1e-5) md = min(md, dot(0.5 * (mr + r), normalize(r - mr)));
	}
	return md;
}

void vertex() {
	op = VERTEX;
	on = NORMAL;
	wd = (mat3(MODEL_MATRIX) * VERTEX) / max(unit, 1e-4);
}

void fragment() {
	// --- the veins: the borders' distance in unit-stone lengths, warped, gated, a finer set off them
	vec3 w = op + vein_warp * (vec3(vnoise(op * 2.3), vnoise(op * 2.3 + 17.1), vnoise(op * 2.3 + 41.7)) - 0.5);
	float d1 = border(w * vein_scale) / vein_scale;
	float d2 = border(w * vein_scale * 2.6 + 7.3) / (vein_scale * 2.6);
	// (the gate's noise is slow, so a crack goes whole or fades out along a long run, never in dashes)
	float g1 = smoothstep(vein_gate - 0.15, vein_gate + 0.15, vnoise(op * 0.85 + 3.1));
	float g2 = smoothstep(vein_gate, vein_gate + 0.25, vnoise(op * 1.3 + 11.3)) * vein_fine;
	// (a crack's width breathes along it)
	float wv = 0.7 + 0.6 * vnoise(op * 3.0 + 5.0);
	float c1 = g1 * (1.0 - smoothstep(vein_core * wv * 0.35, vein_core * wv, d1));
	float c2 = g2 * (1.0 - smoothstep(vein_core * wv * 0.2, vein_core * wv * 0.6, d2));
	float core = max(c1, c2);
	float glow = max(g1 * exp(-d1 / vein_glow_w), g2 * 0.6 * exp(-d2 / (vein_glow_w * 0.6)));
	float rim = max(g1 * smoothstep(vein_core * 3.5, vein_core, d1), g2 * smoothstep(vein_core * 2.0, vein_core * 0.5, d2)) * (1.0 - core);

	// --- the stone: the sheet triplanar in its own space, cool and dark, the bake's rims and cavities
	vec3 bw = pow(abs(normalize(on)), vec3(4.0));
	bw /= bw.x + bw.y + bw.z;
	vec3 q = op * tex_rep;
	vec4 st = texture(stone_tex, q.yz) * bw.x + texture(stone_tex, q.zx + 0.31) * bw.y + texture(stone_tex, q.xy + 0.67) * bw.z;
	float lum = dot(st.rgb, vec3(0.333));
	vec3 col = mix(vec3(lum), st.rgb, 0.35) * tint * 1.6;
	col *= 1.0 + 0.45 * COLOR.r - 0.5 * COLOR.g - 0.3 * COLOR.b;
	col *= 1.0 - scorch * rim;
	// (the light in the stone either side of a crack tints its face, as light through a thin edge)
	col = mix(col, col * 0.7 + vein_color * 0.12, glow * 0.4);

	// --- the water: a film over it, streaks running down the world
	float streak = smoothstep(0.45, 0.85, vnoise(vec3(wd.x * 9.0, wd.y * 1.6 + flow_t * 1.4, wd.z * 9.0)));
	float film = wet * (0.7 + 0.3 * streak);
	col *= mix(1.0, 0.55, film);
	ALBEDO = col * (1.0 - core);
	ROUGHNESS = mix(0.8, mix(0.38, 0.12, streak), film);
	SPECULAR = mix(0.5, 0.7, film);
	METALLIC = 0.0;

	// --- the relief: the cracks' grooves, the grain, the streaks' ripple, by screen-space derivatives (metres)
	float h = (-groove * (1.0 - smoothstep(0.0, vein_core * 3.0, min(d1 + (1.0 - g1), d2 + (1.0 - g2) + 0.004))) + grain_bump * lum
		+ 0.0015 * streak * wet) * unit;
	vec3 dpx = dFdx(VERTEX), dpy = dFdy(VERTEX);
	vec3 nn = normalize(NORMAL);
	vec3 r1 = cross(dpy, nn), r2 = cross(nn, dpx);
	float det = dot(dpx, r1);
	vec3 grad = sign(det) * (dFdx(h) * r1 + dFdy(h) * r2);
	NORMAL = normalize(abs(det) * nn - grad);

	// --- the light: only the cores cross the glow threshold; the light in the stone stays well under it
	float b = (1.0 - beat_amp) + 2.0 * beat_amp * beat;
	EMISSION = vein_color * level * b * (core * vein_energy + glow * vein_glow * (1.0 - core));
}
