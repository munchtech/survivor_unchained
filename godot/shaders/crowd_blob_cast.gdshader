// (L1 lead 12, B4) Each foe on its own shadow inside her fire (Actors/Vat.cs: the blobs' second pass). The moon's cast
// shadow of a foe is real (the crowd casts) and lands on the one shade through the ground's cel model, but inside her fire
// the moon has given way and her light casts none: there a foe stood on a soft olive patch (crowd_blob's multiplied dark
// over the orange). This pass paints the fire's shadow instead: one hard-edged shape per body, long, pointing AWAY from her
// light's foot, at the night's ONE shade as an authored level and hue (rigs.json "foe_moon": [.., shade level, R, G, B,
// residue]; crowd_shade rgb the color x level as scene light, a 1: on) plus the fire's residue there (crowd_moon.z of the
// ground's ramp: the same violet-brown as a leaf's shade in her pool, never olive, never black). Whole where her fire is
// the stronger light (inside the middle of the moon's return, cel_give z to w), none past it: there the moon's own shadow
// stands. Zero crowd_shade: nothing draws (every rig but arena_night).
shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;

uniform float strength = 0.6;
global uniform vec4 crowd_ember;
global uniform vec4 crowd_shade;
global uniform vec4 crowd_moon;
global uniform vec4 cel_give;
global uniform vec4 cel_pool_band;
global uniform sampler2D cel_pool_ramp : filter_linear, repeat_disable;
#define CAST_LONG 1.7
#define CAST_AWAY 0.12
#define CAST_R 0.78
varying float pool;
varying vec3 wp;

void vertex() {
	pool = 0.0;
	if (crowd_shade.a > 0.0 && crowd_ember.w > 0.0 && cel_pool_band.x > 0.0) {
		vec3 o = (MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
		vec2 away = o.xz - crowd_ember.xz;
		float d = length(away);
		float rx = mix(cel_give.z, cel_give.w, 0.5);
		pool = (1.0 - smoothstep(rx - 0.3, rx + 0.3, d)) * smoothstep(0.3, 0.6, d);
		vec2 a = d > 1e-3 ? away / d : vec2(1.0, 0.0);
		VERTEX.xz += a * (dot(VERTEX.xz, a) * (CAST_LONG - 1.0) + 0.5 * (CAST_LONG - 1.0) + CAST_AWAY);
	}
	wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	if (pool <= 0.0) discard;
	float d = length(UV - 0.5) * 2.0;
	float w = fwidth(d) * 0.75 + 1e-3;
	vec3 ramp = texture(cel_pool_ramp, vec2((clamp(length(wp.xz - crowd_ember.xz) / cel_pool_band.x, 0.0, 1.0) * 63.0 + 0.5) / 64.0, 0.5)).rgb;
	ALBEDO = crowd_shade.rgb + ramp * (crowd_ember.w * crowd_moon.z);
	ALPHA = (1.0 - smoothstep(CAST_R - w, CAST_R + w, d)) * pool * COLOR.a * step(0.001, strength);
}
