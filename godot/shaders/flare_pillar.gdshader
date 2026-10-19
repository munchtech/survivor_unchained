// Burns Twice's last word (Fx/Flare/FlareFx.Boom.cs): ONE pillar of fire driven up out of the crater, a single
// continuous shape (judge 2, s4: comets and billows read as a bead chain). An open cylinder: its radius torn by
// noise scrolled up its length, its fire turbulent orange round a yellow core (the core is the middle of the
// pillar as the eye sees it, from any height), its edges eaten red and away as it dies. Its top is under the
// smoke cap (flare_cap). Unshaded and mixed, never added: its punch is its size, not its light (§1.6).
shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, cull_back, shadows_disabled;

global uniform sampler2D flare_noise : filter_linear_mipmap, repeat_enable;

uniform float age = 0.0;    // real seconds since the last word
uniform float grow = 1.0;   // how much of its height has risen (0..1)
uniform float burn = 1.0;   // 1 at full fire .. 0 burnt out
uniform float seed = 0.0;

varying float v_y;
varying float v_a;

void vertex() {
	float y = VERTEX.y + 0.5;
	v_y = y;
	float a = atan(VERTEX.z, VERTEX.x);
	v_a = a;
	// Torn by the fire's own turbulence, climbing: big slow lobes and fast small ones.
	float u = a * 0.15915 + seed;
	float n1 = texture(flare_noise, vec2(u * 2.0, y * 0.55 - age * 1.6)).r;
	float n2 = texture(flare_noise, vec2(u * 5.0 + 0.37, y * 1.7 - age * 4.2)).g;
	float r = 1.0 + (n1 - 0.5) * 0.55 + (n2 - 0.5) * 0.3;
	// A tight root, the body full, swelling into the cap.
	r *= mix(0.55, 1.0, smoothstep(0.0, 0.16, y)) * (1.0 + 0.45 * smoothstep(0.72, 1.0, y));
	VERTEX.xz *= r;
	// It sways a little as one shape.
	VERTEX.x += (texture(flare_noise, vec2(seed + 0.1, y * 0.3 - age * 0.7)).b - 0.5) * 0.5 * y;
}

void fragment() {
	// Only what has risen; its head ragged.
	float u = v_a * 0.15915 + seed;
	float hn = texture(flare_noise, vec2(u * 3.0, age * 2.0)).r;
	if (v_y > grow * (0.92 + 0.12 * hn)) discard;
	vec3 nw = (INV_VIEW_MATRIX * vec4(NORMAL, 0.0)).xyz;
	vec3 vw = (INV_VIEW_MATRIX * vec4(VIEW, 0.0)).xyz;
	vec2 nh = normalize(nw.xz + vec2(1e-4, 0.0));
	vec2 vh = normalize(vw.xz + vec2(0.0, 1e-4));
	// Across the pillar as the eye sees it (-1..1, 0 down its middle), from any camera height.
	float x = dot(nh, vec2(-vh.y, vh.x));
	// The fire: its middle line thrown from side to side as it climbs, torn by flames climbing at two speeds.
	float y = v_y * 7.5;
	float sway = (texture(flare_noise, vec2(seed + 0.3, y * 0.09 - age * 1.9)).r - 0.5) * 0.7 + (texture(flare_noise, vec2(seed + 0.6, y * 0.23 - age * 4.0)).g - 0.5) * 0.4;
	float f1 = texture(flare_noise, vec2(x * 0.35 + u * 0.2, y * 0.11 - age * 2.6)).r;
	float f2 = texture(flare_noise, vec2(x * 0.8 + 0.5, y * 0.27 - age * 5.5)).g;
	float f3 = texture(flare_noise, vec2(x * 1.7 + 0.2, y * 0.6 - age * 9.0)).b;
	float f = (f1 * 0.5 + f2 * 0.32 + f3 * 0.18 - 0.5) * 2.0;
	float xs = abs(x + sway * 0.6);
	// Burning out: thinner from its sides and eaten through, the root first.
	float eat = (1.0 - burn) * (0.9 + 0.5 * (1.0 - smoothstep(0.0, 0.5, v_y)));
	float d = 1.0 - xs * 1.05 + f * 0.75 - eat;
	// The root dims into the flash; the top dims into the cap's smoke.
	d -= (1.0 - smoothstep(0.0, 0.05, v_y)) * 0.4 + smoothstep(0.82, 1.0, v_y) * 0.35;
	float a = smoothstep(0.05, 0.35, d);
	if (a < 0.01) discard;
	// Red at its torn edges, orange through its body, a yellow core down its swaying middle.
	float core = smoothstep(0.62, 1.05, d) * (1.0 - smoothstep(0.35, 0.7, xs)) * (1.0 - 0.7 * smoothstep(0.55, 1.0, v_y));
	vec3 c = mix(vec3(0.36, 0.045, 0.01), vec3(0.88, 0.28, 0.045), smoothstep(0.1, 0.55, d));
	c = mix(c, vec3(0.98, 0.62, 0.2), core * burn);
	// Cooler and darker as it burns out (embers, not a fading glow).
	c *= mix(0.4, 1.0, burn);
	ALBEDO = c;
	ALPHA = a * mix(0.85, 1.0, burn);
}
