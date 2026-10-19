// The flame kit's card (FlameKit.cs; look bible 10_props_flames, "The trick"). A simulated flame
// (art/fx/fb/flame_kit: grey heat, tools/fxsim/flame_sim.py + flame_pack.py) played round its
// seamless loop with motion vectors: between two frames, the first is pushed forward along its
// optical flow and the next pulled back along it, then the two blended, so it flows and never steps.
// The heat is coloured by a ramp here, warm or the Warden's cold blue from one atlas; only the core
// rises past the glow's threshold (1.1, Atmosphere.cs). Upright, turned to the camera about the
// vertical only; `phase` keeps neighbours out of step; it fades softly where it meets the ground.
// `procedural` draws the same flame from noise instead (a teardrop of heat torn by two octaves of
// noise climbing it), with no atlas.
shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;

uniform sampler2D atlas : source_color, filter_linear, repeat_disable;
uniform sampler2D mv_atlas : filter_linear, repeat_disable;
uniform sampler2D depth_tex : hint_depth_texture, filter_nearest;
uniform sampler2D noise_tex : filter_linear_mipmap, repeat_enable;
uniform int grid = 8;
uniform int frames = 64;
uniform float fps = 24.0;
uniform float mv_scale = 0.05;
uniform vec2 cell_px = vec2(128.0, 256.0);
uniform float phase = 0.0;
uniform float cold = 0.0;
uniform float intensity = 1.0;
// The core's brightness (linear, before exposure): above the glow threshold; the body stays under 1.
uniform float core_hdr = 1.8;
uniform float sway = 0.035;
uniform float soft = 0.15;
uniform bool procedural = false;

void vertex() {
	vec3 to_cam = INV_VIEW_MATRIX[3].xyz - MODEL_MATRIX[3].xyz;
	vec3 right = normalize(cross(vec3(0.0, 1.0, 0.0), to_cam));
	vec3 s = vec3(length(MODEL_MATRIX[0].xyz), length(MODEL_MATRIX[1].xyz), 1.0);
	MODELVIEW_MATRIX = VIEW_MATRIX * mat4(vec4(right * s.x, 0.0), vec4(0.0, s.y, 0.0, 0.0), vec4(cross(right, vec3(0.0, 1.0, 0.0)), 0.0), MODEL_MATRIX[3]);
}

vec2 cell_uv(int i, vec2 uv) {
	vec2 lo = 0.5 / cell_px;
	uv = clamp(uv, lo, 1.0 - lo);
	return (vec2(float(i % grid), float(i / grid)) + uv) / float(grid);
}

float sim_heat(vec2 uv) {
	float n = float(frames);
	float f = mod(TIME * fps + phase * n, n);
	int a = int(floor(f));
	int b = (a + 1) % frames;
	float t = fract(f);
	vec2 flow = (texture(mv_atlas, cell_uv(a, uv)).rg * 2.0 - 1.0) * mv_scale;
	float ha = texture(atlas, cell_uv(a, uv - flow * t)).r;
	float hb = texture(atlas, cell_uv(b, uv + flow * (1.0 - t))).r;
	return mix(ha, hb, t);
}

float proc_heat(vec2 uv) {
	float tt = TIME + phase * 37.0;
	// y up from the base, x from the middle.
	vec2 p = vec2(uv.x - 0.5, 1.0 - uv.y);
	float n1 = texture(noise_tex, vec2(p.x * 1.6 + phase, p.y * 1.2 - tt * 1.1)).r;
	float n2 = texture(noise_tex, vec2(p.x * 3.7 - phase, p.y * 2.9 - tt * 2.3)).r;
	float n = n1 * 0.65 + n2 * 0.35 - 0.5;
	p.x += n * 0.22 * p.y;
	// A teardrop: wide at a fifth of the way up, a point at the top.
	float w = 0.34 * smoothstep(0.0, 0.18, p.y) * pow(max(1.0 - p.y, 0.0), 0.8);
	float d = abs(p.x) / max(w, 1e-3);
	float h = (1.0 - d) * (1.0 - p.y * 0.6) + n * 0.5 * p.y;
	return clamp(h, 0.0, 1.0);
}

vec3 ramp(float h) {
	// Linear colour; warm: ember red, orange, yellow, a near-white core; cold: deep blue, #4a7dff, pale blue-white.
	vec3 w0 = vec3(0.35, 0.03, 0.005), w1 = vec3(0.95, 0.28, 0.03), w2 = vec3(1.0, 0.62, 0.17), w3 = vec3(1.0, 0.86, 0.6);
	vec3 c0 = vec3(0.02, 0.05, 0.35), c1 = vec3(0.07, 0.2, 1.0), c2 = vec3(0.35, 0.55, 1.0), c3 = vec3(0.78, 0.88, 1.0);
	vec3 a = mix(w0, c0, cold), b = mix(w1, c1, cold), c = mix(w2, c2, cold), d = mix(w3, c3, cold);
	vec3 col = mix(a, b, smoothstep(0.0, 0.35, h));
	col = mix(col, c, smoothstep(0.35, 0.7, h));
	col = mix(col, d, smoothstep(0.7, 0.92, h));
	return col;
}

void fragment() {
	vec2 uv = UV;
	float up = 1.0 - uv.y;
	// The tip sways, the base stays put.
	float tt = TIME + phase * 17.0;
	uv.x += (sin(tt * 1.7) * 0.6 + sin(tt * 2.9 + 1.3) * 0.4) * sway * up * up;
	float h = procedural ? proc_heat(uv) : sim_heat(uv);
	// Heat to light: the body's edge fades out, the body sits under 1, the core alone climbs to core_hdr.
	float body = smoothstep(0.02, 0.45, h);
	float core = smoothstep(0.8, 0.98, h);
	vec3 col = ramp(h) * body * 0.85 + ramp(1.0) * core * (core_hdr - 0.85);
	float d = textureLod(depth_tex, SCREEN_UV, 0.0).r;
	vec4 behind = INV_PROJECTION_MATRIX * vec4(SCREEN_UV * 2.0 - 1.0, d, 1.0);
	behind.xyz /= behind.w;
	float fade = clamp((VERTEX.z - behind.z) / soft, 0.0, 1.0);
	ALBEDO = col * intensity * fade;
}
