// An effect filmed and cut into an atlas (tools/comfy/flipbook.py): fire,
// smoke, blasts, lightning, magic. Each instance plays the atlas once over
// its life, blending between neighbouring frames so a short atlas still
// moves smoothly. Its colour is stored premultiplied, so one atlas can be
// drawn anywhere between additive light (`add` 1) and smoke laid over the
// world (`add` 0). Lying flat (a blast seen from above, a shockwave on the
// ground) or facing the camera (a flame, a puff), turned by its own angle;
// a camera-facing one fades where it meets what is behind it, so it never
// shows a hard line through the ground.
//
// Per instance: COLOR is the tint (rgb, above 1 to bloom) and the fade (a);
// INSTANCE_CUSTOM is (life 0..1, angle, flat 0/1, unused).
shader_type spatial;
render_mode unshaded, blend_premul_alpha, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;

#include "res://shaders/hero_clear.gdshaderinc"

uniform sampler2D atlas : source_color, filter_linear_mipmap, repeat_disable;
uniform sampler2D depth_tex : hint_depth_texture, filter_nearest;
uniform int grid = 8;
uniform int frames = 64;
uniform float add = 0.7;
uniform float soft = 0.6;

varying vec4 tint;
varying float life;
varying float lie;

void vertex() {
	tint = COLOR;
	life = INSTANCE_CUSTOM.x;
	lie = INSTANCE_CUSTOM.z;
	float s = length(MODEL_MATRIX[0].xyz);
	float a = INSTANCE_CUSTOM.y;
	vec3 right, up, out_;
	if (lie > 0.5) {
		right = vec3(cos(a), 0.0, sin(a));
		up = vec3(-sin(a), 0.0, cos(a));
		out_ = vec3(0.0, 1.0, 0.0);
	} else {
		right = INV_VIEW_MATRIX[0].xyz * cos(a) + INV_VIEW_MATRIX[1].xyz * sin(a);
		up = -INV_VIEW_MATRIX[0].xyz * sin(a) + INV_VIEW_MATRIX[1].xyz * cos(a);
		out_ = INV_VIEW_MATRIX[2].xyz;
	}
	MODELVIEW_MATRIX = VIEW_MATRIX * mat4(vec4(right * s, 0.0), vec4(up * s, 0.0), vec4(out_ * s, 0.0), MODEL_MATRIX[3]);
}

// Sampled no further down the mip chain than a cell of 32 texels: below
// that, neighbouring frames in the atlas bleed into one another and the
// effect shows the square of its cell.
vec4 cell(int i, vec2 uv, float lod) {
	vec2 at = vec2(float(i % grid), float(i / grid));
	return textureLod(atlas, (at + uv) / float(grid), lod);
}

void fragment() {
	float f = clamp(life, 0.0, 1.0) * float(frames - 1);
	int i0 = int(floor(f));
	int i1 = min(i0 + 1, frames - 1);
	vec2 texels = UV * vec2(textureSize(atlas, 0)) / float(grid);
	float lod = clamp(log2(max(length(dFdx(texels)), length(dFdy(texels)))), 0.0, 3.0);
	vec4 c = mix(cell(i0, UV, lod), cell(i1, UV, lod), fract(f));
	// Premultiplied colour is never brighter than its alpha. Compression is
	// free to put anything under a fully clear texel, and that would show
	// the square of the cell; this keeps only what the alpha allows.
	c.rgb = min(c.rgb, vec3(c.a));
	// And round, whatever the atlas holds: the tool refuses a cell with light
	// at its edge, and this makes sure no square can show at any turn or size.
	c *= 1.0 - smoothstep(0.86, 0.99, length(UV * 2.0 - 1.0));
	float fade = tint.a;
	if (lie < 0.5 && soft > 0.0) {
		float d = textureLod(depth_tex, SCREEN_UV, 0.0).r;
		vec4 behind = INV_PROJECTION_MATRIX * vec4(SCREEN_UV * 2.0 - 1.0, d, 1.0);
		behind.xyz /= behind.w;
		fade *= clamp((VERTEX.z - behind.z) / soft, 0.0, 1.0);
	}
	// Its light over her held to a third, as every effect's is (hero_clear), and its smoke too:
	// a burst laid over her tinted her as well as lighting her.
	float clear = hero_clear(VERTEX, VIEW_MATRIX, PROJECTION_MATRIX, VIEWPORT_SIZE);
	ALBEDO = c.rgb * tint.rgb * fade * clear;
	ALPHA = c.a * fade * (1.0 - add) * clear;
}
