// (L1 W2 C5) The camp fire's stepped flame (bible rule 13; MB5 CAMPFIRE; data/look/fx_language.json "campfire"): the
// flame kit's card (FlameKit, flame_mv.gdshader's atlas and motion vectors, played the same way and turned to the camera
// the same way) drawn in the FX language: the simulated heat, read at a coarser mip (big graphic tongues, not the sim's
// wisps), cut into the fire school's three stepped bands (a white-gold core, amber, a deep red edge; fx_cel()), a soft
// outer glow below the cut, and painted sparks rising off the tips (fx_sparks()). Hard-edged and opaque inside: no
// additive haze. The light it throws on the logs and the ground stays the rig's (rigs.json "fires", the zone's light).
// Set by Campfire.FilmedFlames under cel (FxCel.On); --cel off or --fx-cel off: flame_mv as before.
shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;

#include "res://shaders/world_clock.gdshaderinc"
#include "res://shaders/fx_cel.gdshaderinc"

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
uniform float intensity = 1.0;
uniform float sway = 0.035;
uniform float soft = 0.15;
// leaned back toward the camera (flame_mv's: the camp fire's from the play camera, FlameKit's CampTilt)
uniform float tilt = 0.0;
uniform bool procedural = false;
// the sim heat where the body starts; the mip the shape is read at; the sim heat below the cut the glow reaches over
uniform vec3 flame_cut = vec3(0.2, 1.5, 0.12);
// sparks: cell (of the card's height), density (of cells), length (of the card's height), aspect
uniform vec4 flame_sparks = vec4(0.09, 0.12, 0.035, 2.2);
// (W2 C5b) the heat where the mid and core bands start (x, y) mapped onto the school's t (z, w), piecewise linear, 0 and 1
// kept (fx_language.json campfire "steps"); x = z, y = w: no change
uniform vec4 flame_steps = vec4(0.34, 0.75, 0.34, 0.75);

varying float cam_d;

void vertex() {
	vec3 to_cam = INV_VIEW_MATRIX[3].xyz - MODEL_MATRIX[3].xyz;
	cam_d = length(to_cam);
	vec3 up = normalize(mix(vec3(0.0, 1.0, 0.0), INV_VIEW_MATRIX[1].xyz, tilt));
	vec3 right = normalize(cross(up, to_cam));
	vec3 s = vec3(length(MODEL_MATRIX[0].xyz), length(MODEL_MATRIX[1].xyz), 1.0);
	MODELVIEW_MATRIX = VIEW_MATRIX * mat4(vec4(right * s.x, 0.0), vec4(up * s.y, 0.0), vec4(cross(right, up), 0.0), vec4(MODEL_MATRIX[3].xyz, 1.0));
}

vec2 cell_uv(int i, vec2 uv) {
	vec2 lo = 0.5 / cell_px;
	uv = clamp(uv, lo, 1.0 - lo);
	return (vec2(float(i % grid), float(i / grid)) + uv) / float(grid);
}

// flame_mv's sim_heat, read at a mip (the shape's scale)
float sim_heat(vec2 uv, float lod) {
	float n = float(frames);
	float f = mod(WORLD_TIME * fps + phase * n, n);
	int a = int(floor(f));
	int b = (a + 1) % frames;
	float t = fract(f);
	vec2 flow = (textureLod(mv_atlas, cell_uv(a, uv), lod).rg * 2.0 - 1.0) * mv_scale;
	float ha = textureLod(atlas, cell_uv(a, uv - flow * t), lod).r;
	float hb = textureLod(atlas, cell_uv(b, uv + flow * (1.0 - t)), lod).r;
	return mix(ha, hb, t);
}

float proc_heat(vec2 uv) {
	float tt = WORLD_TIME + phase * 37.0;
	vec2 p = vec2(uv.x - 0.5, 1.0 - uv.y);
	float n1 = texture(noise_tex, vec2(p.x * 1.6 + phase, p.y * 1.2 - tt * 1.1)).r;
	float n2 = texture(noise_tex, vec2(p.x * 3.7 - phase, p.y * 2.9 - tt * 2.3)).r;
	float n = n1 * 0.65 + n2 * 0.35 - 0.5;
	p.x += n * 0.22 * p.y;
	float w = 0.34 * smoothstep(0.0, 0.18, p.y) * pow(max(1.0 - p.y, 0.0), 0.8);
	float d = abs(p.x) / max(w, 1e-3);
	return clamp((1.0 - d) * (1.0 - p.y * 0.6) + n * 0.5 * p.y, 0.0, 1.0);
}

void fragment() {
	vec2 uv = UV;
	float up = 1.0 - uv.y;
	float tt = WORLD_TIME + phase * 17.0;
	uv.x += (sin(tt * 1.7) * 0.6 + sin(tt * 2.9 + 1.3) * 0.4) * sway * up * up;
	float h = procedural ? proc_heat(uv) : sim_heat(uv, flame_cut.y);
	// the language's heat: 0 at the cut, 1 at the sim's full heat; below the cut, the glow's distance in the language's
	// units (its e-fold fx_glow.x of the body's heat range)
	float cut = flame_cut.x;
	float heat = h >= cut ? (h - cut) / (1.0 - cut) : -(cut - h) / max(flame_cut.z, 1e-3) * fx_glow.y;
	if (heat > 0.0) heat = heat < flame_steps.x ? heat / flame_steps.x * flame_steps.z
		: heat < flame_steps.y ? mix(flame_steps.z, flame_steps.w, (heat - flame_steps.x) / (flame_steps.y - flame_steps.x))
		: mix(flame_steps.w, 1.0, (heat - flame_steps.y) / max(1.0 - flame_steps.y, 1e-3));
	vec4 c = fx_cel(heat, up);
	// painted sparks rising off the tongues: small hard tears in the card's upper half, never on the body
	float ar = cell_px.x / cell_px.y;
	vec2 sp = vec2((uv.x - 0.5) * ar, up);
	float s = fx_sparks(sp + vec2(0.0, -WORLD_TIME * 0.35 - phase), vec2(0.0, 1.0), flame_sparks.x, flame_sparks.y, flame_sparks.z, flame_sparks.w, phase * 31.0);
	s *= (1.0 - step(0.0, heat)) * smoothstep(0.25, 0.5, up) * (1.0 - smoothstep(0.85, 0.98, up)) * (1.0 - smoothstep(0.3, 0.45, abs(uv.x - 0.5)));
	c.rgb = mix(c.rgb, fx_spark_color, s);
	c.a = max(c.a, s);
	// soft where it meets the ground (flame_mv's)
	float d = textureLod(depth_tex, SCREEN_UV, 0.0).r;
	vec4 behind = INV_PROJECTION_MATRIX * vec4(SCREEN_UV * 2.0 - 1.0, d, 1.0);
	behind.xyz /= behind.w;
	float fade = clamp((VERTEX.z - behind.z) / soft, 0.0, 1.0);
	// every card opaque inside its bands (the kit's back cards at intensity 0.75 would show the logs through them)
	float a = clamp(c.a * fade * step(0.01, intensity), 0.0, 1.0);
	ALBEDO = fx_out(c.rgb, a);
	ALPHA = a;
}
