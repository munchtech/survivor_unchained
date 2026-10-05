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
varying vec3 vat_local;

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
	fx = vec4(float(w & 255) / 255.0, float((w >> 8) & 255) / 255.0, float((w >> 16) & 15) / 15.0, float((w >> 20) & 15) / 15.0);
}

void fragment() {
	// Dissolve: the dead go back to the dark in ragged flakes.
	float dn = fract(sin(dot(floor(vat_local * 18.0), vec3(12.9898, 78.233, 37.719))) * 43758.5453);
	if (fx.y > 0.0 && dn < fx.y) discard;
	vec3 c = albedo.rgb;
	vec4 tex = use_tex ? texture(albedo_tex, UV) : vec4(1.0);
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
	if (fx.z > 0.0) {
		// Frozen (chill to half): rime grows in patches on what faces up, a cold blue at a
		// middle value that a pale body shows against; the ice is glossy, with a thin cold rim
		// and a few glints.
		float lum = dot(c, vec3(0.2126, 0.7152, 0.0722));
		float rime = smoothstep(0.42, 0.62, vat_noise(vat_local * 5.0) * 0.75 + up * 0.45) * smoothstep(0.0, 0.5, fx.z);
		vec3 ice = vec3(0.16, 0.36, 0.62) * (0.7 + 0.6 * clamp(lum, 0.0, 0.6));
		c = mix(c, vec3(lum) * vec3(0.9, 0.97, 1.08), fx.z * 0.3);
		c = mix(c, ice, rime * 0.85);
		rough = mix(rough, 0.22, rime);
		float glint = step(0.992, vat_hash(floor(vat_local * 16.0) + floor(TIME * 3.0)));
		e += vec3(0.28, 0.62, 1.0) * fx.z * pow(rim, 4.0) * 0.85 + vec3(0.55, 0.8, 1.0) * rime * glint * 0.8;
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
	ALBEDO = c;
	ROUGHNESS = rough;
	METALLIC = metallic;
	RIM = rim_amount;
	RIM_TINT = rim_tint;
	// Struck: a warm flare that lives at the rim, so the body keeps its shape
	// from thirty metres up, with only an instant's glow across the whole of it
	// (a full white-hot body bloomed the pale risen into blobs).
	float hot = fx.x * fx.x;
	// (At 0.75 across the whole body a pale body lost its paint and read as a ghost.)
	e += vec3(1.0, 0.86, 0.72) * (hot * hot * 0.38 + fx.x * (0.1 + rim * rim * 1.1));
	e += c * COLOR.a;
	// Ember at the dissolve's edge.
	if (fx.y > 0.0) e += vec3(1.0, 0.45, 0.12) * smoothstep(fx.y + 0.12, fx.y, dn) * 3.0;
	EMISSION = e;
}
