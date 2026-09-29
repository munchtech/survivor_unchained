// Smoke and dust: a sprite facing the camera (a puff of the effects'
// sprites, turned; or a soft round spot), blended over what is behind it,
// shaded darker where it is thin (spark.gdshader's twin).
shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, cull_disabled, shadows_disabled;

uniform sampler2DArray sprites : filter_linear_mipmap;

varying vec4 tint;
varying float sprite;

void vertex() {
	tint = COLOR;
	sprite = INSTANCE_CUSTOM.x;
	float s = length(MODEL_MATRIX[0].xyz);
	float a = INSTANCE_CUSTOM.y;
	vec3 right = INV_VIEW_MATRIX[0].xyz * cos(a) + INV_VIEW_MATRIX[1].xyz * sin(a);
	vec3 up = -INV_VIEW_MATRIX[0].xyz * sin(a) + INV_VIEW_MATRIX[1].xyz * cos(a);
	MODELVIEW_MATRIX = VIEW_MATRIX * mat4(vec4(right * s, 0.0), vec4(up * s, 0.0), vec4(INV_VIEW_MATRIX[2].xyz * s, 0.0), MODEL_MATRIX[3]);
}

void fragment() {
	if (sprite < 0.5) {
		ALBEDO = tint.rgb;
		ALPHA = tint.a * smoothstep(1.0, 0.25, length(UV * 2.0 - 1.0));
	} else {
		vec4 t = texture(sprites, vec3(UV, sprite - 1.0));
		ALBEDO = tint.rgb * mix(0.6, 1.1, t.r);
		ALPHA = tint.a * t.a;
	}
}
