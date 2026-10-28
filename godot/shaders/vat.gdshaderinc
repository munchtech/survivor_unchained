#include "res://shaders/flare_world.gdshaderinc"
// The crowd's vertex animation, shared by vat.gdshader (solid bodies, one
// side) and vat_cut.gdshader (fur and hair cards: two sides, cut by alpha).
// See vat.gdshader for what it does.

uniform sampler2D vat_pos : filter_nearest, repeat_disable;
uniform sampler2D vat_nor : filter_nearest, repeat_disable;
uniform int vat_width = 1;
uniform int vat_rows = 1;
// Where this surface's vertices start among all the bake's.
uniform int vat_offset = 0;

uniform sampler2D albedo_tex : source_color, filter_linear_mipmap, repeat_enable;
uniform bool use_tex = false;
uniform vec4 albedo : source_color = vec4(1.0);
uniform float roughness = 0.8;
uniform float metallic = 0.0;
uniform vec3 glow_color = vec3(0.0);
uniform float rim_amount = 0.45;
uniform float rim_tint = 0.35;
uniform float alpha_cut = 0.45;
// Play's moon rim on the crowd (Atmosphere.Set, E1): the key's colour times its strength (rgb), and which way the
// key lies (key_dir, world, toward the light). Godot's RIM is lit by the key, so in the wood's shade a mob had none.
global uniform vec4 crowd_rim;
global uniform vec4 key_dir;
// Moving foes keep about a frame of FSR 2's history, so each frame must be smooth on its own
// (the wolf's fur sparkled): a moving body's paint is read up to this many mips softer, and shine and rim fade
// where the normal turns faster than a pixel can show. (Fading cards edge-on thinned the fur's
// outline and gained nothing at 1.5 mips: dropped.)
// (fading them, not widening the lobe: a rougher lobe spread the sparkle over more pixels).
uniform float tex_bias = 0.0;
uniform float shine_aa = 0.0;

// The cloth's dye, as the person shader has it (shaders/person.gdshader).
uniform bool use_dye = false;
uniform vec3 dye_color = vec3(1.0);
uniform vec3 dye_h = vec3(0.0, 1.0, 0.05);
uniform vec3 dye_s = vec3(0.0, 1.0, 0.05);
uniform vec3 dye_v = vec3(0.0, 1.0, 0.05);
uniform float dye_lum = 0.25;

float dye_band(float x, vec3 r) { return smoothstep(r.x - r.z, r.x, x) * (1.0 - smoothstep(r.y, r.y + r.z, x)); }

vec3 dye_hsv(vec3 c) {
	vec4 K = vec4(0.0, -1.0 / 3.0, 2.0 / 3.0, -1.0);
	vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
	vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));
	float d = q.x - min(q.w, q.y);
	return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + 1e-10)), d / (q.x + 1e-10), q.x);
}

varying flat vec4 fx;
varying flat float fx_crit;
varying vec3 vat_local;
// How fast the body moves (0 still, 1 fast): FSR 2 keeps little history on it.
varying flat float vat_pace;

// Value noise on the body's own shape (its bake space), so a status's patches stay on the body as
// it moves rather than swimming over it.
float vat_hash(vec3 p) { return fract(sin(dot(p, vec3(12.9898, 78.233, 37.719))) * 43758.5453); }
float vat_noise(vec3 p) {
	vec3 i = floor(p), f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(mix(vat_hash(i), vat_hash(i + vec3(1.0, 0.0, 0.0)), f.x), mix(vat_hash(i + vec3(0.0, 1.0, 0.0)), vat_hash(i + vec3(1.0, 1.0, 0.0)), f.x), f.y),
		mix(mix(vat_hash(i + vec3(0.0, 0.0, 1.0)), vat_hash(i + vec3(1.0, 0.0, 1.0)), f.x), mix(vat_hash(i + vec3(0.0, 1.0, 1.0)), vat_hash(i + vec3(1.0, 1.0, 1.0)), f.x), f.y), f.z);
}

ivec2 vat_coord(int frame, int vid) {
	int row = vid / vat_width;
	return ivec2(vid - row * vat_width, frame * vat_rows + row);
}

void vertex() {
	int vid = vat_offset + VERTEX_ID;
	int f0 = int(INSTANCE_CUSTOM.x + 0.5);
	vat_pace = clamp(fract(INSTANCE_CUSTOM.x) / 0.45, 0.0, 1.0);
	int f1 = int(INSTANCE_CUSTOM.y + 0.5);
	float k = INSTANCE_CUSTOM.z;
	vec3 p0 = texelFetch(vat_pos, vat_coord(f0, vid), 0).xyz;
	vec3 p1 = texelFetch(vat_pos, vat_coord(f1, vid), 0).xyz;
	vec3 n0 = texelFetch(vat_nor, vat_coord(f0, vid), 0).xyz * 2.0 - 1.0;
	vec3 n1 = texelFetch(vat_nor, vat_coord(f1, vid), 0).xyz * 2.0 - 1.0;
	VERTEX = mix(p0, p1, k);
	NORMAL = normalize(mix(n0, n1, k));
	vat_local = VERTEX;
	int w = int(INSTANCE_CUSTOM.w + 0.5);
	fx = vec4(float(w & 127) / 127.0, float((w >> 8) & 255) / 255.0, float((w >> 16) & 15) / 15.0, float((w >> 20) & 15) / 15.0);
	fx_crit = float((w >> 7) & 1);
}

void fragment() {
	// Dissolve: the dead go back to the dark in ragged flakes.
	float dn = fract(sin(dot(floor(vat_local * 18.0), vec3(12.9898, 78.233, 37.719))) * 43758.5453);
	if (fx.y > 0.0 && dn < fx.y) discard;
	vec3 c = albedo.rgb;
	vec4 tex = use_tex ? texture(albedo_tex, UV, tex_bias * vat_pace) : vec4(1.0);
	c *= tex.rgb;
#ifdef VAT_CUT
	// Fur and hair cards: cut where the paint is clear.
	ALPHA = tex.a * albedo.a;
	ALPHA_SCISSOR_THRESHOLD = alpha_cut;
#endif
	if (use_dye) {
		vec3 hsv = dye_hsv(pow(max(c, vec3(0.0)), vec3(1.0 / 2.2)));
		float m = dye_band(hsv.x, dye_h) * dye_band(hsv.y, dye_s) * dye_band(hsv.z, dye_v);
		float lum = dot(c, vec3(0.2126, 0.7152, 0.0722));
		c = mix(c, min(dye_color * (lum / dye_lum), vec3(1.0)), m);
	}
	c *= COLOR.rgb;
	float rim = 1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0);
	vec3 sky = (VIEW_MATRIX * vec4(0.0, 1.0, 0.0, 0.0)).xyz;
	float up = clamp(dot(NORMAL, sky), 0.0, 1.0);
	// A status reads on the body in patches and at its edge, never as a wash over the whole of it.
	// Washes turned a crowd of pale risen white in Hoarfrost and cream in Cinderfall: AgX folds a
	// bright hue to white past about 1, and the glow blooms what is over 1.1. So the ice is darker
	// and bluer than a pale body, not paler, and every status light stays under 1.
	float rough = roughness;
	vec3 e = glow_color;
	// Burns Twice's glaze takes the rime's place in its reach (flare_world.gdshaderinc): the fight freezes the
	// whole reach at once, but a body glazes only as the frost's front reaches it (t10: all rimed by frost +0.1 s).
	float fz = fx.z > 0.0 && flare_live() && flare_frosting((INV_VIEW_MATRIX * vec4(VERTEX, 1.0)).xyz) ? 0.0 : fx.z;
	if (fz > 0.001) {
		// Frozen (chill to half): rime grows in patches on what faces up, a cold blue at a
		// middle value that a pale body shows against; the ice is glossy, with a thin cold rim
		// and a few glints.
		float lum = dot(c, vec3(0.2126, 0.7152, 0.0722));
		float rime = smoothstep(0.42, 0.62, vat_noise(vat_local * 5.0) * 0.75 + up * 0.45) * smoothstep(0.0, 0.5, fz);
		vec3 ice = vec3(0.16, 0.36, 0.62) * (0.7 + 0.6 * clamp(lum, 0.0, 0.6));
		c = mix(c, vec3(lum) * vec3(0.9, 0.97, 1.08), fz * 0.3);
		c = mix(c, ice, rime * 0.85);
		rough = mix(rough, 0.22, rime);
		float glint = step(0.992, vat_hash(floor(vat_local * 16.0) + floor(TIME * 3.0)));
		e += vec3(0.28, 0.62, 1.0) * fz * pow(rim, 4.0) * 0.85 + vec3(0.55, 0.8, 1.0) * rime * glint * 0.8;
	}
	if (fx.w > 0.0) {
		// Burning: thin tongues of fire licking up the body from its edges over char, soot where
		// they have been; the flame is deep orange over near-black, so it stays orange (over a pale
		// body's own light it read as peach). The rest of the body is its own colour.
		float lick = vat_noise(vec3(vat_local.x * 4.5, vat_local.y * 1.6 - TIME * 3.4, vat_local.z * 4.5));
		float tongue = smoothstep(0.52, 0.8, lick * 0.75 + rim * 0.5) * fx.w;
		float soot = smoothstep(0.28, 0.56, lick * 0.75 + rim * 0.35) * fx.w;
		c *= (1.0 - soot * 0.72) * (1.0 - tongue * 0.9);
		e += vec3(1.0, 0.3, 0.03) * tongue + vec3(1.0, 0.42, 0.08) * pow(rim, 3.0) * fx.w * 0.5;
	}
	// Struck past the crowd's rim-only flare (a champion's, a few at once): the body's paint is lifted, lit
	// by the scene's own light, so the flash keeps its shading and is as bright as the place allows. An
	// added light lit it as if by day: at night the Barrow Knight went a flat cream cut-out, struck after
	// struck, and read as a model glitch (Experience 9's judge, 27 October).
	// (half the old falloff's power: at s^3 a champion's blow was gone before a frame at 1:1 caught it)
	float struck = pow(max(fx.x - 0.12, 0.0) / 0.88, 1.5);
	// A critical's is bigger and warmer, for the two or three frames its flash is high: 1.6x the lift and the rim's pop,
	// and a warm breath that reaches the darks (a grey hood lifted x2.6 of its own paint stayed grey; round 3's judge).
	float crit_k = 1.0 + 0.6 * fx_crit;
	// (its own hue only, and warm: a lift toward white, even shaded, read as an untextured clay body; at x2.3
	// a grey hood under firelight still went white)
	c = min(c * (1.0 + 1.6 * crit_k * struck * vec3(1.0, 0.85, 0.7)) + vec3(0.16, 0.08, 0.04) * fx_crit * struck, vec3(0.85 + 0.05 * fx_crit));
	ALBEDO = c;
	vec3 dnx = dFdx(NORMAL), dny = dFdy(NORMAL);
	float busy = shine_aa * smoothstep(0.02, 0.3, 0.5 * (dot(dnx, dnx) + dot(dny, dny)));
	// Never fully rough: Godot's RIM falls off as pow(1 - NdotV, (1 - ROUGHNESS) * 16), so at roughness 1 (an imported
	// texture's default: the lamplings' and the skeletons' bodies) the "rim" is 1 everywhere and RIM lays every light's
	// colour over the whole body, mostly white (rim_tint 0.35). Grimtunnel's dark mauve hide read as glowing cyan in C03's
	// ford lamps. At 0.9 it is a rim again ((1 - NdotV)^1.6) and the sheen barely moves.
	ROUGHNESS = min(rough, 0.9);
	SPECULAR = 0.5 * (1.0 - busy);
	METALLIC = metallic;
	RIM = rim_amount * (1.0 - busy);
	RIM_TINT = rim_tint;
	// Struck: a warm flare that lives at the rim, so the body keeps its shape
	// from thirty metres up, with only an instant's glow across the whole of it
	// (a full white-hot body bloomed the pale risen into blobs).
	float hot = fx.x * fx.x;
	// (At 0.75 across the whole body a pale body lost its paint and read as a ghost.)
	// The rim-only flare (the crowd's, up to 0.12) as it was. Past it, the lifted paint above and a hot
	// edge, never a flat wash: from the play camera most of a body is "rim", so rim^2 x 1.1 plus 0.38
	// over all of it was a flat unlit cream body.
	float low = min(fx.x, 0.12), high = max(fx.x - 0.12, 0.0) / 0.88;
	// (the rim's breath gives way as the struck lift comes: at night it alone was a pale wash)
	e += vec3(1.0, 0.86, 0.72) * low * (1.0 - high) * (0.1 + rim * rim * 1.1);
	// (and a breath of warm light in its own paint: no rim term, which covers the whole body from up here,
	// and no more, or the night's dark body goes pale)
	e += vec3(1.0, 0.62, 0.38) * c * struck * 0.25 * crit_k;
	// (and a pop at its edge, in its own paint: scaled by c, or from up here the rim covers the whole body
	// and it is the old cream cut-out again)
	e += c * 0.6 * crit_k * struck * pow(rim, 3.0 - fx_crit);
	e += c * COLOR.a;
	// The moon's rim, in shade as in its light: strongest on the side toward the key, a breath on the far side.
	if (crowd_rim.a > 0.0) {
		vec3 kv = normalize((VIEW_MATRIX * vec4(key_dir.xyz, 0.0)).xyz);
		float side = 0.3 + 0.7 * clamp(dot(NORMAL, kv) * 0.5 + 0.5, 0.0, 1.0);
		e += crowd_rim.rgb * crowd_rim.a * pow(rim, 3.0) * side * (1.0 - busy);
	}
	// Ember at the dissolve's edge.
	if (fx.y > 0.0) e += vec3(1.0, 0.45, 0.12) * smoothstep(fx.y + 0.12, fx.y, dn) * 3.0;
	EMISSION = e;

	// The Flare's drain and glaze (flare_world.gdshaderinc).
	if (flare_live()) {
		vec3 fl_a = ALBEDO; float fl_r = ROUGHNESS; vec3 fl_e = EMISSION;
		flare_body((INV_VIEW_MATRIX * vec4(VERTEX, 1.0)).xyz, NORMAL, INV_VIEW_MATRIX, rim, fl_a, fl_r, fl_e);
		ALBEDO = fl_a; ROUGHNESS = fl_r; EMISSION = fl_e;
		// The BOOM's line reaching a statue: the fire through its cracks before it bursts.
		EMISSION += vec3(1.0, 0.32, 0.05) * flare_crack((INV_VIEW_MATRIX * vec4(VERTEX, 1.0)).xyz) * (0.45 + 0.9 * rim);
		// The fireball on the statues (judge 5b fix 3): their faces toward it mixed to its colour (amber added on cyan
		// came out grey), the far faces left cyan, so each statue is two-tone.
		if (flare_fire.w > 0.0) {
			float fw = clamp(flare_fire_w((INV_VIEW_MATRIX * vec4(VERTEX, 1.0)).xyz, normalize((INV_VIEW_MATRIX * vec4(NORMAL, 0.0)).xyz)), 0.0, 1.0);
			vec3 fc = flare_fire_col();
			// Only the ice takes the fire's colour (judge 7 (1): a charred body painted fc * 0.55 by it read as a beige
			// mannequin until the fire went); the char keeps its black and catches the fire at its rim only.
			float ice = clamp(fx.z * 2.0, 0.0, 1.0);
			ALBEDO = mix(ALBEDO, fc * 0.55, fw * 0.8 * ice);
			EMISSION = mix(EMISSION, fc * fire_rim, fw * ice) + fc * fire_rim * fw * (1.0 - ice) * pow(rim, 3.0) * 0.35;
		}
	}
}
