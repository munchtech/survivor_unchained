// (L1 lead 12, B4) Each foe on its own shadow inside her fire (Actors/Vat.cs: the blobs' second pass). The moon's cast
// shadow of a foe is real (the crowd casts) and lands on the one shade through the ground's cel model, but inside her fire
// the moon has given way and her light casts none: there a foe stood on a soft olive patch (crowd_blob's multiplied dark
// over the orange). This pass paints the fire's shadow instead: one hard-edged shape per body, long, pointing AWAY from her
// light's foot, at the night's ONE shade as an authored level and hue (rigs.json "foe_moon": [.., shade level, R, G, B,
// residue]; crowd_shade rgb the color x level as scene light, a 1: on) plus the fire's residue there (crowd_moon.z of the
// ground's ramp: the same violet-brown as a leaf's shade in her pool, never olive, never black). Whole where her fire is
// the stronger light (inside the middle of the moon's return, cel_give z to w), none past it: there the moon's own shadow
// stands. Zero crowd_shade: nothing draws (every rig but arena_night).
// (L1 lead 18, SH) Under a rig with the floor's tone table (rigs.json "ember_floor": cel_floor_band x over 0) the shadow's
// tone is the FLOOR'S OWN at that distance: the night's one shade (crowd_shade, what the floor's shade is away from the
// fire) times the table's leaf-shade turn there (cel_floor_turn row 1), so a body's shadow DIMS the glow to exactly what a
// leaf's shade shows at that ring and is the floor's plain shade where the table ends; and it gives way as her fire's
// share does (1 - the moon's return, the table's a), per fragment, so it has no outer rim. (Before: the one shade plus a
// residue of the old ramp, whole to 3.6 m: on the table's floor the pack's discs merged into one foot_on-black mass with a
// hard edge against the orange from 2 m.) No tone lives here: the rig's table.
shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;

uniform float strength = 0.6;
global uniform vec4 crowd_ember;
global uniform vec4 crowd_shade;
global uniform vec4 crowd_moon;
global uniform vec4 cel_give;
global uniform vec4 cel_pool_band;
global uniform sampler2D cel_pool_ramp : filter_linear, repeat_disable;
global uniform vec4 cel_floor_band;
global uniform sampler2D cel_floor_turn : filter_linear, repeat_disable;
#define CAST_LONG 1.7
#define CAST_AWAY 0.12
#define CAST_R 0.78
varying float pool;
varying float foot_on;
varying vec3 wp;

void vertex() {
	pool = 0.0; foot_on = 0.0;
	if (crowd_shade.a > 0.0 && crowd_ember.w > 0.0 && cel_pool_band.x > 0.0) {
		vec3 o = (MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
		vec2 away = o.xz - crowd_ember.xz;
		float d = length(away);
		float rx = mix(cel_give.z, cel_give.w, 0.5);
		foot_on = smoothstep(0.3, 0.6, d);
		pool = (1.0 - smoothstep(rx - 0.3, rx + 0.3, d)) * foot_on;
		vec2 a = d > 1e-3 ? away / d : vec2(1.0, 0.0);
		VERTEX.xz += a * (dot(VERTEX.xz, a) * (CAST_LONG - 1.0) + 0.5 * (CAST_LONG - 1.0) + CAST_AWAY);
	}
	wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	bool table = cel_floor_band.x > 0.0;
	float gate = table ? foot_on : pool;
	if (gate <= 0.0) discard;
	float d = length(UV - 0.5) * 2.0;
	float w = fwidth(d) * 0.75 + 1e-3;
	float r = length(wp.xz - crowd_ember.xz);
	if (table) {
		vec4 ts = texture(cel_floor_turn, vec2((clamp(r / cel_floor_band.x, 0.0, 1.0) * 63.0 + 0.5) / 64.0, 0.75));
		ALBEDO = crowd_shade.rgb * ts.rgb;
		gate *= 1.0 - ts.a;
	} else {
		vec3 ramp = texture(cel_pool_ramp, vec2((clamp(r / cel_pool_band.x, 0.0, 1.0) * 63.0 + 0.5) / 64.0, 0.5)).rgb;
		ALBEDO = crowd_shade.rgb + ramp * (crowd_ember.w * crowd_moon.z);
	}
	ALPHA = (1.0 - smoothstep(CAST_R - w, CAST_R + w, d)) * gate * COLOR.a * step(0.001, strength);
}
