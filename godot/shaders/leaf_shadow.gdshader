// (Env 22 r1c, the triage judge: crown shadows on the land many-sided and straight-edged, block-shaped at night) A tree's
// shadow-only proxy (env_trees.py shadow_proxy / alder_proxy) cast through a leaf mask: each face's own place in its mass
// rides in its uv (u < 0.74: x = (u - 0.35) / 0.35, y = |v - 0.5| * 2; an alder's clump mass: its flattened disc, 0 at the
// middle, 1 at its rim; a spruce blade: across it -1..1 and along it 0..1; the trunk keeps the bark strip, u >= 0.75, and
// always casts). Near the rim a noise of leaf clumps eats the mass, so the outline is lobed and ragged, with a few gaps of
// light inside. The noise lies in the light's own plane (the world position on the shadow camera's x and y), so the
// faces one behind another along a ray drop together and a hole is a hole; the same for every cascade. Shadow pass only
// (Dressing.cs sets it on the ShadowsOnly proxies), so no draw is added; the cost is a discard in the shadow pass.
shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_opaque;

// mode 0: a disc (an alder's clump), rim = its radius; 1: a blade (a spruce's), rim = across it, more toward its tip.
uniform int mode = 0;
// The clumps' size (m: the big lobes; a second octave at a third of it) and how much is eaten: at the middle and at the rim.
uniform float lobe = 0.75;
uniform float hole = 0.1;
uniform float eat = 0.62;
uniform float rim_from = 0.45;

float h21(vec2 p) { vec3 p3 = fract(vec3(p.xyx) * 0.1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
float vnoise(vec2 p) {
	vec2 i = floor(p), f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(h21(i), h21(i + vec2(1.0, 0.0)), f.x), mix(h21(i + vec2(0.0, 1.0)), h21(i + vec2(1.0, 1.0)), f.x), f.y);
}

void fragment() {
	ALBEDO = vec3(0.0);
	if (UV.x < 0.74) {
		float x = (UV.x - 0.35) / 0.35, y = abs(UV.y - 0.5) * 2.0;
		float rim = mode == 0 ? length(vec2(x, y)) : max(abs(x) * (0.45 + 0.55 * y), y * y);
		vec3 wp = (INV_VIEW_MATRIX * vec4(VERTEX, 1.0)).xyz;
		vec2 lp = vec2(dot(wp, INV_VIEW_MATRIX[0].xyz), dot(wp, INV_VIEW_MATRIX[1].xyz));
		float n = vnoise(lp / lobe) * 0.6 + vnoise(lp / lobe * 2.9 + 17.3) * 0.28 + vnoise(lp / lobe * 7.3 + 41.1) * 0.12;
		float thr = mix(hole, eat, smoothstep(rim_from, 1.0, rim));
		if (n < thr) discard;
	}
}
