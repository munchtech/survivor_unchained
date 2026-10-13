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
	// The band: a metre and a half, mostly just behind the line, where the air is hottest.
	float x = (dl - radius + 0.35) / 0.8;
	float band = exp(-x * x) * strength;
	if (band < 0.01) discard;
	// It churns: rising cells, bending more across the band than along it.
	vec2 q = v_w.xz * 0.9 + vec2(0.0, -age * 6.0);
	float n1 = texture(flare_noise, q * 0.5).r - 0.5;
	float n2 = texture(flare_noise, q * 1.3 + 0.3).g - 0.5;
	vec2 dir = d / max(dl, 1e-3);
	vec2 off = (dir * n1 * 1.2 + vec2(n2, -n1) * 0.7) * band * 0.016;
	// (screen space: x across, y down; the ground's outward roughly maps to the screen's)
	ALBEDO = texture(screen_tex, SCREEN_UV + off).rgb;
	ALPHA = smoothstep(0.01, 0.12, band);
}
