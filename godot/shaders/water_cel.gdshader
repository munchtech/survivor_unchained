// (L1 W2 C5) Water as bands of the sky (bible rules 6 and 9; MB4 WATER; data/look/water.json, set by Water.cs and
// ArenaEdge.Stream under cel). The color is the rig's sky: ALBEDO is a reflectance and the light is Godot's ambient (the
// zone's sky, the light the cel world's shade takes), so the bands follow every rig and carry no color of their own.
// - bands: s = depth from the bank (0..1 over 'deep' m) x depth_w + (1 - N.V) x view_w, cut into three stepped bands;
//   the shallow band lets the bed show through (shallow_alpha);
// - a few soft painted strokes a step lighter: long dashes across the view, drifting with the flow;
// - the shore's foam: one flat band where the scene behind is within foam depth of the surface, lit by the key in one step;
// - light (light()): no diffuse but the foam's; the key a scatter of soft dashes where its reflection falls (never a disc);
//   point lights (her ember, a fire, a lamp) soft vertical strokes, a column of dashes toward the viewer: no pool;
// - mode 1 (the arena's stream: UV.x m across from its middle, UV.y m downstream, UV2.x 0 at a bank to 1 in its middle):
//   the Dig's slurry as two or three long soft strokes down its deep middle. Mode 0 (Water.cs): UV the flow (m/s, x z) or,
//   for a stream, across/along; UV2.x the depth (m) or the bank's distance.
// No normal map, no reflection probe, no ink (depth_draw_never: the ink pass never sees it).
shader_type spatial;
render_mode blend_mix, depth_draw_never, cull_disabled, shadows_disabled;

uniform sampler2D noise_tex : filter_linear_mipmap, repeat_enable;
uniform sampler2D depth_tex : hint_depth_texture, filter_nearest;
uniform int mode = 0;
uniform bool stream = false;
// deep (m), depth_w, view_w, shallow_alpha
uniform vec4 bands = vec4(1.6, 1.0, 0.8, 0.55);
uniform vec2 cuts = vec2(0.22, 0.6);
// mode 1: its 0..1 across read as this much depth
uniform float stream_depth = 0.55;
// shallow, mid, deep reflectance of the sky's light
uniform vec3 reflect = vec3(1.0, 0.62, 0.33);
uniform vec3 tint : source_color = vec3(0.83, 0.89, 1.0);
// strokes: size across, size along (m), cover, lift
uniform vec4 strokes = vec4(3.2, 0.32, 0.1, 0.55);
uniform float drift = 0.35;
// foam: depth (m), reflect, key
uniform vec3 foam = vec3(0.09, 0.9, 0.35);
// the key's dashes: lobe across, along; dash size across, along (m)
uniform vec4 key_lobe = vec4(0.35, 0.6, 1.6, 0.16);
// the key's dashes' cover, their gain; the lights' column across, along
uniform vec4 key_k = vec4(0.12, 0.9, 0.06, 0.5);
// the lights' gain
uniform float light_gain = 0.5;
uniform vec3 slurry : source_color = vec3(0.48, 0.58, 0.07);
// slurry: glow, cover, size across, size along (m)
uniform vec4 slurry_k = vec4(0.12, 0.22, 0.9, 9.0);

varying vec3 w_pos;
varying vec2 w_uv;
varying float w_bank;
varying float wv_foam;
varying float wv_dash;

void vertex() {
	w_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	w_uv = UV;
	w_bank = UV2.x;
}

// soft dashes of noise (its features an eighth of its tile: q in dash sizes x 0.125): long across the view (t), thin along it (b), a share `cover` of the water, edges soft
float dashes(vec2 q, float cover, float soft) {
	float n = texture(noise_tex, q).r * 0.7 + texture(noise_tex, q * 2.3 + 0.37).r * 0.3;
	float th = 1.0 - cover;
	return smoothstep(th - soft, th + soft, n);
}

void fragment() {
	vec3 n_w = vec3(0.0, 1.0, 0.0);
	vec3 v_w = normalize(CAMERA_POSITION_WORLD - w_pos);
	float ndv = clamp(dot(n_w, v_w), 0.0, 1.0);
	// across the view on the water's plane, and along it
	vec3 t_w = normalize(cross(n_w, v_w) + vec3(1e-4, 0.0, 0.0));
	vec3 b_w = cross(t_w, n_w);
	vec2 pq = vec2(dot(w_pos, t_w), dot(w_pos, b_w));
	// the depth from the bank (0..1)
	float d01 = mode == 1 ? clamp(w_bank, 0.0, 1.0) * stream_depth : clamp(w_bank / max(bands.x, 1e-3), 0.0, 1.0);
	float s = d01 * bands.y + (1.0 - ndv) * bands.z * (1.0 - d01 * 0.5);
	// the flow's drift (world x z), for the strokes
	vec2 flow = mode == 0 && !stream ? w_uv : vec2(0.0, 0.0);
	vec2 dq = vec2(dot(vec3(flow.x, 0.0, flow.y), t_w), dot(vec3(flow.x, 0.0, flow.y), b_w)) * TIME * drift;
	if (mode != 0 || stream) dq = vec2(0.0, TIME * 0.05);
	// the bands: shallow (the bed through it), mid, deep
	float aa = max(fwidth(s), 1e-4);
	float b1 = smoothstep(cuts.x - aa, cuts.x + aa, s), b2 = smoothstep(cuts.y - aa, cuts.y + aa, s);
	float r = mix(mix(reflect.x, reflect.y, b1), reflect.z, b2);
	float alpha = mix(bands.w, 1.0, b1);
	// a few soft strokes a step lighter
	float st = dashes((pq + dq) / vec2(strokes.x, strokes.y) * 0.125, strokes.z, 0.06);
	r *= 1.0 + strokes.w * st;
	// the key's dashes (for light()): a finer pattern of the same kind
	wv_dash = dashes((pq + dq * 1.6) / vec2(key_lobe.z, key_lobe.w) * 0.125 + 0.5, key_k.x, 0.05);
	// the shore's foam: within foam.x m of what is behind the surface
	float zd = textureLod(depth_tex, SCREEN_UV, 0.0).r;
	vec4 behind = INV_PROJECTION_MATRIX * vec4(SCREEN_UV * 2.0 - 1.0, zd, 1.0);
	behind.xyz /= behind.w;
	float thick = VERTEX.z - behind.z;
	float fa = max(fwidth(thick), 1e-4);
	float fm = 1.0 - smoothstep(foam.x - fa, foam.x + fa, thick);
	wv_foam = fm;
	vec3 body = tint * r;
	if (mode == 1) {
		// the slurry's long soft strokes down the deep middle (UV: across, along)
		float sl = dashes(vec2(w_uv.x / slurry_k.z, (w_uv.y - TIME * 0.25) / slurry_k.w) * 0.125, slurry_k.y, 0.08) * smoothstep(0.4, 0.75, d01);
		body = mix(body, slurry * r, sl * 0.6);
		EMISSION = slurry * slurry_k.x * sl;
	}
	ALBEDO = mix(body, vec3(foam.y), fm);
	ALPHA = mix(alpha, 1.0, fm);
	ROUGHNESS = 1.0;
	SPECULAR = 0.0;
}

void light() {
	vec3 h = normalize(VIEW + LIGHT);
	vec3 n = NORMAL;
	vec3 t = normalize(cross(n, VIEW) + vec3(1e-4, 0.0, 0.0));
	vec3 b = cross(t, n);
	float dt = dot(h, t), db = dot(h, b);
	float facing = step(0.0, dot(n, LIGHT));
	if (LIGHT_IS_DIRECTIONAL) {
		// the foam takes the key in one step
		DIFFUSE_LIGHT += LIGHT_COLOR * ATTENUATION * facing * wv_foam * foam.z;
		float lobe = exp(-(dt * dt) / (key_lobe.x * key_lobe.x) - (db * db) / (key_lobe.y * key_lobe.y));
		SPECULAR_LIGHT += LIGHT_COLOR * ATTENUATION * key_k.y * smoothstep(0.25, 0.45, lobe) * wv_dash * (1.0 - wv_foam);
	} else {
		float lobe = exp(-(dt * dt) / (key_k.z * key_k.z) - (db * db) / (key_k.w * key_k.w));
		SPECULAR_LIGHT += LIGHT_COLOR * ATTENUATION * light_gain * smoothstep(0.2, 0.5, lobe) * mix(0.35, 1.0, wv_dash) * (1.0 - wv_foam);
	}
}
