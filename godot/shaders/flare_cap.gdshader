// Burns Twice's last word (Fx/Flare/FlareFx.Boom.cs): the dark smoke cap on top of the pillar, mushrooming out
// (from above, a bloom). A sphere torn into billows; dark warm smoke, its underside and its rolling lip lit
// orange by the fire under it while the fire burns; it thins from its edge as it rises. Unshaded and mixed.
shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, cull_back, shadows_disabled, fog_disabled;

global uniform sampler2D flare_noise : filter_linear_mipmap, repeat_enable;

uniform float age = 0.0;    // real seconds since the last word
uniform float burn = 1.0;   // the fire under it: 1 full .. 0 out
uniform float thin = 0.0;   // 0 dense .. 1 gone
uniform float seed = 0.0;

varying vec3 v_l;
varying float v_bill;

void vertex() {
	v_l = VERTEX;
	// Billows: big rolls and small ones, churning outward.
	vec3 q = normalize(VERTEX);
	float ang = atan(q.z, q.x) * 0.15915;
	float b1 = texture(flare_noise, vec2(ang * 3.0 + seed, q.y * 0.5 + age * 0.3)).r;
	float b2 = texture(flare_noise, vec2(ang * 7.0 + seed + 0.4, q.y * 1.2 - age * 0.5)).g;
	float b3 = texture(flare_noise, vec2(ang * 15.0 + seed + 0.7, q.y * 2.6 + age * 0.8)).b;
	float bill = (b1 - 0.5) * 0.7 + (b2 - 0.5) * 0.4 + (b3 - 0.5) * 0.22;
	v_bill = bill;
	VERTEX += NORMAL * bill;
	// The lip rolls under: the lower half pulled in and up (a mushroom's cap, not a ball).
	VERTEX.y *= mix(0.5, 1.0, step(0.0, VERTEX.y));
}

void fragment() {
	vec3 nw = (INV_VIEW_MATRIX * vec4(NORMAL, 0.0)).xyz;
	float rim = 1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0);
	float s = texture(flare_noise, v_l.xz * 0.9 + vec2(seed, age * 0.25)).b;
	// Dark warm smoke, its rolls shaded by their own folds.
	float fold = clamp(0.5 + v_bill * 2.2, 0.0, 1.0);
	vec3 c = vec3(0.05, 0.04, 0.034) * (0.55 + 0.9 * fold) * (0.8 + 0.4 * s);
	// Lit from below by the fire: its underside, and from above the rim of the bloom where it rolls over.
	float under = smoothstep(0.3, -0.7, nw.y) * (0.6 + 0.8 * (1.0 - fold));
	float lip = pow(rim, 2.5) * (0.5 + 0.5 * s);
	c += vec3(0.9, 0.3, 0.06) * (under * 0.8 + lip * 0.55) * burn;
	// Its edge thins to nothing (no hard ball outline), and it all thins as it goes.
	float a = (1.0 - smoothstep(0.5, 1.0, rim + (s - 0.5) * 0.7)) * (1.0 - thin);
	a *= smoothstep(0.0, 0.3, 1.0 - thin * (0.5 + 0.9 * s));
	if (a < 0.01) discard;
	ALBEDO = c;
	ALPHA = clamp(a * 1.1, 0.0, 0.96);
}
