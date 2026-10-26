// (E9d) A chimney's plume (ZoneView.Town.Plume): soft lumpy puffs, painterly, lit by the key on one side (a puff
// shaded as a ball, the key's tint on its lit side, the sky's cool on the other), fading as they open. Unshaded
// and cheap: no texture, no shadow, a few particles per stack.
shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, cull_disabled, shadows_disabled;

global uniform vec4 key_dir;
global uniform vec4 flora_light;
global uniform vec4 survivor;   // her chest (xyz), w 1 while she is in the world
// (E9d r2) smoke between the camera and her fades out: nearer the camera than she is by near_gap it thins, gone by
// near_gap + near_soft (plumes hung over the cut rooms and beside a cut house; the house fade's cut is hers, and the
// smoke over it must go with it)
uniform float near_gap = 1.5;
uniform float near_soft = 4.0;
uniform float near_side = 2.5;   // (m) smoke this far off her line of sight stays
uniform vec3 lit_col : source_color = vec3(0.86, 0.83, 0.78);
uniform vec3 shade_col : source_color = vec3(0.46, 0.48, 0.53);
uniform float density = 0.55;
uniform float warm_key = 1.0;   // how much the key's own tint (a low sun's) colours the lit side

varying flat float v_seed;

float h21(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float vn(vec2 p) {
	vec2 i = floor(p), f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(h21(i), h21(i + vec2(1.0, 0.0)), f.x), mix(h21(i + vec2(0.0, 1.0)), h21(i + vec2(1.0, 1.0)), f.x), f.y);
}

void vertex() {
	// (a particle billboard keeping its scale and its spin, as the standard material's)
	mat4 w = mat4(normalize(INV_VIEW_MATRIX[0]), normalize(INV_VIEW_MATRIX[1]), normalize(INV_VIEW_MATRIX[2]), MODEL_MATRIX[3]);
	w = w * mat4(vec4(cos(INSTANCE_CUSTOM.x), -sin(INSTANCE_CUSTOM.x), 0.0, 0.0), vec4(sin(INSTANCE_CUSTOM.x), cos(INSTANCE_CUSTOM.x), 0.0, 0.0), vec4(0.0, 0.0, 1.0, 0.0), vec4(0.0, 0.0, 0.0, 1.0));
	MODELVIEW_MATRIX = VIEW_MATRIX * w;
	MODELVIEW_MATRIX = MODELVIEW_MATRIX * mat4(vec4(length(MODEL_MATRIX[0].xyz), 0.0, 0.0, 0.0), vec4(0.0, length(MODEL_MATRIX[1].xyz), 0.0, 0.0), vec4(0.0, 0.0, length(MODEL_MATRIX[2].xyz), 0.0), vec4(0.0, 0.0, 0.0, 1.0));
	MODELVIEW_NORMAL_MATRIX = mat3(MODELVIEW_MATRIX);
	v_seed = float(INSTANCE_ID) * 7.31;
}

void fragment() {
	vec2 p = UV * 2.0 - 1.0;
	// a lumpy edge: two octaves of noise, its own per puff
	float n = 0.65 * vn(p * 2.2 + v_seed) + 0.35 * vn(p * 5.1 - v_seed * 1.7);
	float r = length(p) + 0.6 * (n - 0.5);
	float a = (1.0 - smoothstep(0.15, 0.95, r)) * (0.55 + 0.45 * smoothstep(0.25, 0.7, n));
	// shaded as a ball: the view-space normal of a sphere under the quad
	float z = sqrt(max(1.0 - dot(p, p), 0.0));
	vec3 nrm = normalize(TANGENT * p.x - BINORMAL * p.y + NORMAL * (z + 0.35));
	vec3 L = normalize((VIEW_MATRIX * vec4(key_dir.xyz, 0.0)).xyz);
	float lam = clamp(dot(nrm, L) * 0.6 + 0.45 + 0.25 * (n - 0.5), 0.0, 1.0);
	vec3 key = mix(vec3(1.0), clamp(vec3(flora_light.z, 1.0, flora_light.w), vec3(0.6), vec3(1.6)), warm_key);
	ALBEDO = mix(shade_col, lit_col * key, lam) * COLOR.rgb;
	float clear = 1.0;
	if (survivor.w > 0.5) {
		vec3 her_v = (VIEW_MATRIX * vec4(survivor.xyz, 1.0)).xyz;
		float her_d = -her_v.z;
		clear = smoothstep(her_d - near_gap - near_soft, her_d - near_gap, -VERTEX.z);
		// (E9d r3: only smoke on the line from the camera to her: its distance from that line at its own depth; before,
		// every plume nearer the camera than her went, so an uncut house's chimney up the frame stood bare)
		float side = length(VERTEX.xy - her_v.xy * (VERTEX.z / min(her_v.z, -0.1)));
		clear = mix(clear, 1.0, smoothstep(near_side, near_side + 2.5, side));
		// (only smoke well over her head: a cook fire's or a brazier's low plume on the street before her stays)
		float wy = (INV_VIEW_MATRIX * vec4(VERTEX, 1.0)).y;
		clear = mix(1.0, clear, smoothstep(2.5, 4.5, wy - survivor.y));
	}
	ALPHA = clamp(a * COLOR.a * density * clear, 0.0, 1.0);
}
