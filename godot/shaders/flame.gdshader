// A tongue of flame on a particle (one of the effects' sprites, Kenney's
// Particle Pack: its flame tongues, chosen per particle): its edge licked by
// rising noise, hot yellow at the heart, orange, then red at the ragged edge, dying
// darker as it rises. Premultiplied blending: tongues stacked on each other
// settle at their colour (at most twice it) instead of adding to white, and
// the red edges darken what is behind them a little, as a real flame does.
shader_type spatial;
render_mode unshaded, blend_premul_alpha, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;

uniform sampler2DArray sprites : filter_linear_mipmap;
// The layers of the tongues in the sprites: the first, and how many.
uniform float first_tongue = 0.0;
uniform float tongues = 1.0;
uniform sampler2D noise_tex : filter_linear_mipmap, repeat_enable;
uniform vec3 hot = vec3(1.0, 0.62, 0.2);
uniform vec3 warm = vec3(0.95, 0.3, 0.05);
uniform vec3 edge = vec3(0.4, 0.06, 0.01);
uniform float glow = 1.0;

varying float v_life;
varying float v_seed;
varying float v_shape;

void vertex() {
	// Face the camera, keep the particle's size and turn (what a
	// StandardMaterial3D's particle billboard does).
	mat4 w = mat4(normalize(INV_VIEW_MATRIX[0]), normalize(INV_VIEW_MATRIX[1]), normalize(INV_VIEW_MATRIX[2]), MODEL_MATRIX[3]);
	float a = INSTANCE_CUSTOM.x;
	w = w * mat4(vec4(cos(a), -sin(a), 0.0, 0.0), vec4(sin(a), cos(a), 0.0, 0.0), vec4(0.0, 0.0, 1.0, 0.0), vec4(0.0, 0.0, 0.0, 1.0));
	MODELVIEW_MATRIX = VIEW_MATRIX * w * mat4(vec4(length(MODEL_MATRIX[0].xyz), 0.0, 0.0, 0.0), vec4(0.0, length(MODEL_MATRIX[1].xyz), 0.0, 0.0), vec4(0.0, 0.0, length(MODEL_MATRIX[2].xyz), 0.0), vec4(0.0, 0.0, 0.0, 1.0));
	v_life = INSTANCE_CUSTOM.y;
	v_seed = fract(MODEL_MATRIX[3].x * 7.13 + MODEL_MATRIX[3].z * 3.71 + float(INSTANCE_ID) * 0.618);
	v_shape = first_tongue + floor(fract(float(INSTANCE_ID) * 0.618 + 0.3) * tongues);
}

void fragment() {
	// UV.y is 0 at the tip, 1 at the root: the tip licks most.
	float tip = 1.0 - UV.y;
	vec2 n = texture(noise_tex, UV * vec2(0.6, 0.35) + vec2(v_seed, TIME * 0.9 + v_seed)).rg - 0.5;
	vec4 t = texture(sprites, vec3(UV + n * vec2(0.22, 0.14) * tip, v_shape));
	float s = t.a * mix(0.55, 1.0, t.r);
	// Thinner and cooler as it rises and ages.
	float heat = s * (1.0 - smoothstep(0.35, 1.0, v_life)) * smoothstep(0.0, 0.12, v_life);
	heat *= 1.0 - 0.45 * tip;
	vec3 col = mix(edge, warm, smoothstep(0.08, 0.45, heat));
	col = mix(col, hot, smoothstep(0.5, 0.95, heat));
	float cover = smoothstep(0.02, 0.3, heat);
	ALBEDO = col * cover * glow;
	// Half as much cover as colour: a little light is added, not all of it.
	ALPHA = cover * 0.5;
}
