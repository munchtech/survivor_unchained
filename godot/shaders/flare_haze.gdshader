// Burns Twice's ring (Fx/Flare/FlareFx.Boom.cs): the heat riding its line for its first third of a second, a
// band of shimmer that bends the ground and the statues behind it (the screen's own picture, refracted: an
// engine tool; the band, its width and its churn are ours). A flat disc laid over the reach, drawn first of
// the see-through things so the fire's own bits stay over it.
shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, depth_test_disabled, cull_disabled, shadows_disabled, fog_disabled;

global uniform sampler2D flare_noise : filter_linear_mipmap, repeat_enable;
uniform sampler2D screen_tex : hint_screen_texture, filter_linear_mipmap;

uniform vec3 center = vec3(0.0);
uniform float radius = 0.0;   // the ring's line (m)
uniform float strength = 0.0; // 0..1
uniform float age = 0.0;

varying vec3 v_w;

void vertex() {
	v_w = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec2 d = v_w.xz - center.xz;
	float dl = length(d);
	// The skirt (judge 4 fix 7): heat and kicked-up dust 1-1.5 m ahead of the line, the blast before its fire,
	// and a breath of it just behind the line where the air is hottest.
	float ah = dl - radius;
	float x = (ah - 0.6) / 0.6;
	float band = (exp(-x * x) + 0.5 * exp(-pow((ah + 0.25) / 0.4, 2.0))) * strength;
	band = min(band, 1.0);
	if (band < 0.01) discard;
	// It churns: rising cells, bending more across the band than along it.
	vec2 q = v_w.xz * 0.9 + vec2(0.0, -age * 6.0);
	float n1 = texture(flare_noise, q * 0.5).r - 0.5;
	float n2 = texture(flare_noise, q * 1.3 + 0.3).g - 0.5;
	vec2 dir = d / max(dl, 1e-3);
	vec2 off = (dir * n1 * 1.2 + vec2(n2, -n1) * 0.7) * band * 0.016;
	// (screen space: x across, y down; the ground's outward roughly maps to the screen's)
	vec3 bent = texture(screen_tex, SCREEN_UV + off).rgb;
	// The dust: a warm brown veil, thickest at the skirt's front, torn by the churn.
	float dust = exp(-x * x) * strength * smoothstep(0.35, 0.7, n1 + 0.5 + n2 * 0.6);
	ALBEDO = mix(bent, bent * vec3(0.78, 0.66, 0.52) + vec3(0.025, 0.017, 0.008), dust * 0.55);
	ALPHA = smoothstep(0.01, 0.12, band);
}
