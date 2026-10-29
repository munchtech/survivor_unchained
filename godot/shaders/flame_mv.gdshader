// The flame kit's card (FlameKit.cs; look bible 10_props_flames, "The trick"). A simulated flame
// (art/fx/flame/flame_kit: grey heat, tools/fxsim/flame_sim.py + flame_pack.py) played round its
// seamless loop with motion vectors: between two frames, the first is pushed forward along its
// optical flow and the next pulled back along it, then the two blended, so it flows and never steps.
// The heat is coloured by a ramp here, warm or the Warden's cold blue from one atlas; only the core
// rises past the glow's threshold (1.1, Atmosphere.cs). Upright, turned to the camera about the
// vertical only; `phase` keeps neighbours out of step; it fades softly where it meets the ground.
// `procedural` draws the same flame from noise instead (a teardrop of heat torn by two octaves of
// noise climbing it), with no atlas.
shader_type spatial;
render_mode unshaded, blend_premul_alpha, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;

uniform sampler2D atlas : source_color, filter_linear_mipmap, repeat_disable;
uniform sampler2D mv_atlas : filter_linear_mipmap, repeat_disable;
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
// The body's brightness and the core's added on top (linear, before exposure): the body stays well
// under the glow's threshold, the core alone crosses it.
uniform float body_k = 1.1;
uniform float core_k = 1.4;
uniform float sway = 0.035;
uniform float soft = 0.15;
uniform bool procedural = false;

// A small flame seen from high up (a lamp's, at the play camera) leans its card back toward the camera by `tilt`
// (0: upright, 1: facing it square), so it isn't foreshortened to a sliver; it still stands on its base.
uniform float tilt = 0.0;
// Where the core begins in heat: lower for a flame that must read as a bright point from far off.
uniform float core_lo = 0.86;
uniform float pull = 0.0;
// A cold flame's core pulled from blue-white toward blue (0..1), so the tonemapper doesn't clip it to pure white.
uniform float core_blue = 0.0;
// How much the flame's body covers what is behind it (0: purely added light, as a lamp's; the blend is premultiplied, so 0
// is exactly the old additive look). A big flame's middle hides the log behind it rather than letting its edge show through.
uniform float occlude = 0.0;
// The body's fall-off with heat (higher: dimmer edges and tips) and how far the warm ramp is pushed toward deep orange and red
// (0: the old ramp; 1: the camp fire's, so the tonemapper doesn't wash its body to peach and cream).
uniform float body_pow = 1.6;
uniform float warm_sat = 0.0;
// A carried flame (a torch in a hand) grows toward this many times its size from far off (full from 16 m): at the play camera
// its few pixels otherwise read as a glint, not a flame (FlameKit, carried).
uniform float far_grow = 1.0;
// A carried flame's inner card, near the camera only (full within 4 m, none from 10 m, so the play camera's flame is as it was):
// a solid teardrop of hot, saturated yellow-orange under the simulated heat, so at chest-up the flame has a glowing core, not a
// pale wisp (NPC 18). `tear` its share, `tear_k` its brightness (linear, before exposure).
uniform float tear = 0.0;
uniform float tear_k = 2.0;
uniform float tear_lod = 3.0;
uniform float tear_lo = 0.1;
uniform float tear_sat = 1.0;
varying float cam_d;

void vertex() {
	vec3 to_cam = INV_VIEW_MATRIX[3].xyz - MODEL_MATRIX[3].xyz;
	cam_d = length(to_cam);
	vec3 up = normalize(mix(vec3(0.0, 1.0, 0.0), INV_VIEW_MATRIX[1].xyz, tilt));
	vec3 right = normalize(cross(up, to_cam));
	vec3 s = vec3(length(MODEL_MATRIX[0].xyz), length(MODEL_MATRIX[1].xyz), 1.0);
	s.xy *= mix(1.0, far_grow, smoothstep(6.0, 16.0, length(to_cam)));
	// Drawn a little toward the camera from far off (`pull` m, none within 6 m): a lamp's flame then clears its
	// cage's top bar and hood, which from the play camera's height stand just in front of it.
	vec3 o = MODEL_MATRIX[3].xyz + normalize(to_cam) * pull * smoothstep(6.0, 12.0, length(to_cam));
	MODELVIEW_MATRIX = VIEW_MATRIX * mat4(vec4(right * s.x, 0.0), vec4(up * s.y, 0.0), vec4(cross(right, up), 0.0), vec4(o, 1.0));
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

float sim_heat_lod(vec2 uv, float lod) {
	float n = float(frames);
	float f = mod(TIME * fps + phase * n, n);
	int a = int(floor(f));
	int b = (a + 1) % frames;
	float t = fract(f);
	return mix(textureLod(atlas, cell_uv(a, uv), lod).r, textureLod(atlas, cell_uv(b, uv), lod).r, t);
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
	vec3 w0 = mix(vec3(0.3, 0.02, 0.003), vec3(0.4, 0.012, 0.0), warm_sat), w1 = mix(vec3(0.9, 0.16, 0.01), vec3(0.95, 0.09, 0.003), warm_sat);
	vec3 w2 = mix(vec3(1.0, 0.42, 0.05), vec3(1.0, 0.3, 0.015), warm_sat), w3 = mix(vec3(1.0, 0.7, 0.32), vec3(1.0, 0.62, 0.16), warm_sat);
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
	// Heat-weighted: the edges a dim red, the middle bright, so the tongue keeps its inner shape.
	float body = smoothstep(0.0, 0.25, h) * pow(h, body_pow);
	float core = smoothstep(core_lo, 1.0, h);
	vec3 core_col = mix(ramp(1.0), vec3(0.2, 0.45, 1.0), core_blue * cold);
	vec3 col = ramp(h) * body * body_k + core_col * core * core_k;
	float d = textureLod(depth_tex, SCREEN_UV, 0.0).r;
	vec4 behind = INV_PROJECTION_MATRIX * vec4(SCREEN_UV * 2.0 - 1.0, d, 1.0);
	behind.xyz /= behind.w;
	float fade = clamp((VERTEX.z - behind.z) / soft, 0.0, 1.0);
	float alpha = occlude * smoothstep(0.08, 0.45, h);
	float tn = tear * (1.0 - smoothstep(4.0, 10.0, cam_d));
	if (tn > 0.0) {
		// The core follows the flame: its heat blurred (a coarse mip of the same frames), so it is one solid, rounded body that
		// moves with the tongue, held inside a teardrop (widest a quarter of the way up, gone by 0.85) so it never fills the card.
		float hs = procedural ? h : sim_heat_lod(uv, tear_lod);
		vec2 p = vec2(uv.x - 0.5, 1.0 - uv.y);
		float w = 0.42 * sqrt(clamp(p.y / 0.22, 0.0, 1.0)) * pow(max(1.0 - max(p.y - 0.22, 0.0) / 0.63, 0.0), 1.2);
		float env = clamp(1.0 - pow(abs(p.x) / max(w, 1e-3), 2.0), 0.0, 1.0);
		float t = hs * env;
		float m = smoothstep(tear_lo, tear_lo + 0.3, t) * tn;
		vec3 edge = mix(vec3(1.0, 0.24, 0.02), vec3(0.9, 0.12, 0.005), tear_sat), hot = mix(vec3(1.0, 0.56, 0.1), vec3(1.0, 0.42, 0.03), tear_sat);
		vec3 tc = mix(edge, hot, smoothstep(tear_lo + 0.1, tear_lo + 0.5, t)) * tear_k;
		col = mix(col, tc, m);
		alpha = mix(alpha, 1.0, m);
	}
	ALBEDO = col * intensity * fade;
	ALPHA = alpha * fade * min(intensity, 1.0);
}
