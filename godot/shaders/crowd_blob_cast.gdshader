// (L1 lead 12, B4) Each foe on its own shadow inside her fire (Actors/Vat.cs: the blobs' second pass). The moon's cast
// shadow of a foe is real (the crowd casts) and lands on the one shade through the ground's cel model, but inside her fire
// the moon has given way and her light casts none: there a foe stood on a soft olive patch (crowd_blob's multiplied dark
// over the orange). This pass paints the fire's shadow instead: one hard-edged shape per body, long, pointing AWAY from her
// light's foot. Zero crowd_shade: nothing draws (every rig but arena_night).
// (L1 lead 18, SH) Under a rig with the floor's tone table (rigs.json "ember_floor": cel_floor_band x over 0) the shadow
// gives way as her fire's share does (1 - the moon's return, the table's a), per fragment, so it has no outer rim.
// (L1 lead 19, SH2) The TONE is the night's floor with her fire taken away: the floor's own LIT tone out past the table,
// authored in the rig (crowd_shade: rigs.json "foe_moon" values 3-6, level and color as an unshaded pass writes it; the
// ember_floor row's first tone, L 0.33 C 0.085 h 260), the same at every distance: a dark violet-navy on the orange, one
// step lighter than a foe's own body, and what the floor turns into where the table ends. (Lead 18's tone, the table's leaf-shade turn at the fragment's distance, is what a LEAF's shade shows there:
// a leaf cuts the moon and leaves the fire, so inside 2.5 m it is the glow itself, L 0.48 C 0.16 h 30 at 2 m and L 0.60
// gold at her feet: shot as l19_01, the casts were red and lighter than the floor beside them.) No tone lives here.
// (L1 lead 19, SH2) The SHAPE, one rule for three users (a foe: Vat.cs; what stands: Dressing.cs; her: PlayerView.cs; the
// last two through World/FireCast.cs): a tapered trail from the feet, away from her light's foot. Per instance, the origin
// is the feet and COLOR is r: the body's height m, g: its width at the feet m, b: 0 or a fixed length m, a: how much it
// shows. The trail is as wide as the body at the feet and CAST_TIP of that at its tip, round at both ends, and
// L = d x h / (H - h) long (d the feet's ground distance from the light's foot, H the light's height over the feet: where
// the top of the body's shadow falls), held between CAST_MIN and CAST_MAX body heights and under CAST_FAR m. The edge is
// hard (one pixel by fwidth of the shape's own distance in metres: analytic, so it neither blurs nor shimmers as the pack
// moves). A FIXED cast (b over 0) is the light's own bearer: the light is over her, the rule gives nothing, so her shadow is
// b long, away from the light's foot as every cast is (along the instance's own z axis when she stands on the foot itself),
// and one step deeper in tone, the rig's (foe_moon value 8, crowd_moon.w).
shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled, world_vertex_coords;

uniform float strength = 0.6;
global uniform vec4 crowd_ember;
global uniform vec4 crowd_shade;
global uniform vec4 crowd_moon;
global uniform vec4 cel_give;
global uniform vec4 cel_pool_band;
global uniform sampler2D cel_pool_ramp : filter_linear, repeat_disable;
global uniform vec4 cel_ember;
global uniform vec4 cel_floor_band;
global uniform sampler2D cel_floor_turn : filter_linear, repeat_disable;
// (the shape's numbers; no tone)
#define CAST_TIP 0.3
#define CAST_MIN 1.5
#define CAST_MAX 3.2
#define CAST_FAR 4.0
// (the far end's rise per metre, so a gentle slope does not cut the trail; and the quad's margin round the shape, m)
#define CAST_LIFT 0.02
#define CAST_PAD 0.06
varying vec3 wp;
varying flat vec4 seg;
varying flat vec3 dim;
varying flat vec2 gt;

void vertex() {
	vec3 o = MODEL_MATRIX[3].xyz;
	wp = o;
	seg = vec4(o.xz, 1.0, 0.0); dim = vec3(1.0, 0.1, 0.03); gt = vec2(0.0, 1.0);
	// (her light's foot is the cel model's point, cel_ember, the one the floor's table is laid round: never her own place)
	vec2 away = o.xz - cel_ember.xz;
	float d = length(away);
	bool table = cel_floor_band.x > 0.0;
	bool bearer = COLOR.b > 0.0;
	// (past the fire's reach nothing is drawn at all: the four corners stay on the feet)
	float reach = table ? cel_floor_band.x : cel_give.w + 0.3;
	if (crowd_shade.a > 0.0 && crowd_ember.w > 0.0 && cel_ember.w > 0.0 && cel_pool_band.x > 0.0 && COLOR.a > 0.0 && (bearer || d < reach)) {
		float h = COLOR.r;
		float r1 = max(0.5 * COLOR.g, 0.02), r2 = r1 * CAST_TIP;
		float g = COLOR.a, tone = 1.0, len;
		vec2 a;
		if (bearer) {
			vec2 z = MODEL_MATRIX[2].xz;
			a = d > 0.05 ? away / d : (dot(z, z) > 1e-6 ? normalize(z) : vec2(0.0, -1.0));
			len = COLOR.b;
			if (crowd_moon.w > 0.0) tone = crowd_moon.w;
		} else {
			a = d > 1e-3 ? away / d : vec2(1.0, 0.0);
			float top = crowd_ember.y - o.y;
			len = clamp(d * h / max(top - h, 0.05), CAST_MIN * h, min(CAST_MAX * h, CAST_FAR));
			g *= smoothstep(0.3, 0.6, d);
			if (!table) { float rx = mix(cel_give.z, cel_give.w, 0.5); g *= 1.0 - smoothstep(rx - 0.3, rx + 0.3, d); }
		}
		// (the two circles' centres are len apart: the far end of the trail is len + the tip's radius from the feet)
		len = max(len - r2, r1);
		seg = vec4(o.xz, a); dim = vec3(len, r1, r2); gt = vec2(g, tone);
		float along = mix(-r1 - CAST_PAD, len + r2 + CAST_PAD, UV.y);
		float across = (UV.x - 0.5) * 2.0 * (r1 + CAST_PAD);
		vec2 xz = o.xz + a * along + vec2(-a.y, a.x) * across;
		wp = vec3(xz.x, o.y + CAST_LIFT * max(along, 0.0), xz.y);
	}
	VERTEX = wp;
}

void fragment() {
	if (gt.x <= 0.0) discard;
	// (the shape's distance, m: two circles and their outer tangents, along the trail from the feet)
	vec2 q = wp.xz - seg.xy;
	vec2 p = vec2(abs(q.x * seg.w - q.y * seg.z), dot(q, seg.zw));
	float b = (dim.y - dim.z) / dim.x;
	float c = sqrt(max(1.0 - b * b, 0.0));
	float k = dot(p, vec2(-b, c));
	float sd = k < 0.0 ? length(p) - dim.y : (k > c * dim.x ? length(p - vec2(0.0, dim.x)) - dim.z : dot(p, vec2(c, b)) - dim.y);
	float w = fwidth(sd) * 0.75 + 1e-4;
	float gate = gt.x;
	float r = length(wp.xz - cel_ember.xz);
	if (cel_floor_band.x > 0.0) {
		// (L1 lead 19, SH3: the tone is the table's leaf-shade tone at ONE ring, the pool's edge (crowd_moon.z x the reach:
		// rigs.json "foe_moon" value 7; crowd_shade is the table's own far shade, so this is the table's tone there exactly):
		// the glow dimmed, a dark warm violet, the same at every distance. Not the fragment's own ring (the glow itself
		// inside 2.5 m) and not the far lit floor (blue).
		float ring = crowd_moon.z > 0.0 ? clamp(crowd_moon.z, 0.0, 1.0) : 1.0;
		ALBEDO = crowd_shade.rgb * texture(cel_floor_turn, vec2((ring * 63.0 + 0.5) / 64.0, 0.75)).rgb * gt.y;
		gate *= 1.0 - texture(cel_floor_turn, vec2((clamp(r / cel_floor_band.x, 0.0, 1.0) * 63.0 + 0.5) / 64.0, 0.75)).a;
	} else {
		vec3 ramp = texture(cel_pool_ramp, vec2((clamp(r / cel_pool_band.x, 0.0, 1.0) * 63.0 + 0.5) / 64.0, 0.5)).rgb;
		ALBEDO = (crowd_shade.rgb + ramp * (crowd_ember.w * crowd_moon.z)) * gt.y;
	}
	ALPHA = (1.0 - smoothstep(-w, w, sd)) * gate * step(0.001, strength);
}
