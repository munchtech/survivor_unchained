// The ground darkened softly under a crowd body (Actors/Vat.cs, VatCrowd): the crowd casts no shadow in play
// (E1: shadow draws), and without one a mob floated over moonlit ground beside her long shadow. One flat quad per
// body in one MultiMesh per kind, multiplied over what is drawn: no shadow map, a few pixels each. The instance's
// colour alpha is how much it shows (a dissolving body's fades with it).
shader_type spatial;
render_mode unshaded, blend_mul, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;

uniform float strength = 0.6;
// Rendering 4 r2: by night in the arena (vat.gdshaderinc's crowd_night), inside her lamp's pool the dark under a body is
// a quarter wider, a little darker and a hand away from her, so the bodies she lights stand on the ground; past her pool
// as before. (No long shadows: a ring of them would draw the starburst again.)
global uniform vec4 crowd_ember;
global uniform vec4 crowd_fill;
global uniform vec4 crowd_lamp;
global uniform vec4 crowd_night;
// (L1 lead 12, B4: under a rig with "foe_moon" the soft dark is off: each foe stands on its own hard shadow, the moon's cast one
// outside her fire and crowd_blob_cast.gdshader's inside it; a soft multiplied dark over leaf shade was a product, rule R3)
global uniform vec4 crowd_shade;
#define BLOB_WIDE 0.25
#define BLOB_DARK 0.2
#define BLOB_AWAY 0.25
varying float pool;

void vertex() {
	pool = 0.0;
	if (crowd_night.w > 0.5 && crowd_ember.w > 0.0) {
		vec3 o = (MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
		vec2 away = o.xz - crowd_ember.xz;
		float d = length(away);
		pool = 1.0 - smoothstep(crowd_lamp.a, crowd_fill.a, d);
		float w = max(length(MODEL_MATRIX[0].xyz), 1e-3);
		VERTEX.xz = VERTEX.xz * (1.0 + BLOB_WIDE * pool) + (d > 1e-3 ? away / d : vec2(0.0)) * BLOB_AWAY * pool / w;
	}
}

void fragment() {
	float d = length(UV - 0.5) * 2.0;
	float a = 1.0 - smoothstep(0.0, 1.0, d);
	a *= a;
	if (crowd_shade.a > 0.0) a = 0.0;
	ALBEDO = vec3(1.0 - a * min(strength * (1.0 + BLOB_DARK * pool), 0.95) * COLOR.a);
}
