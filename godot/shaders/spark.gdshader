// A spark, a mote, a flare: a sprite facing the camera (a layer of the
// effects' sprites, turned; or a soft round spot), its size the instance's
// scale and its colour the instance's (above 1 to bloom). The additive kind,
// for light (sparks, cores, trails); smoke.gdshader is its mixed twin.
shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;

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
	float a;
	if (sprite < 0.5) a = pow(max(0.0, 1.0 - length(UV * 2.0 - 1.0)), 1.6);
	// Round, whatever the sprite: the pack's forks of lightning run to the edge
	// of their square and would show it as they turn.
	else { vec4 t = texture(sprites, vec3(UV, sprite - 1.0)); a = t.r * t.a * (1.0 - smoothstep(0.82, 0.98, length(UV * 2.0 - 1.0))); }
	ALBEDO = tint.rgb * a * tint.a;
}
