// A spark, a mote, a flare: a sprite facing the camera (a layer of the
// effects' sprites, turned; or a soft round spot), its size the instance's
// scale and its colour the instance's (above 1 to bloom). The additive kind,
// for light (sparks, cores, trails); smoke.gdshader is its mixed twin.
shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;

#include "res://shaders/hero_clear.gdshaderinc"

uniform sampler2DArray sprites : filter_linear_mipmap;

varying vec4 tint;
varying float sprite;
varying float streak;

void vertex() {
	tint = COLOR;
	sprite = INSTANCE_CUSTOM.x;
	float s = length(MODEL_MATRIX[0].xyz);
	float a = INSTANCE_CUSTOM.y;
	vec3 right = INV_VIEW_MATRIX[0].xyz * cos(a) + INV_VIEW_MATRIX[1].xyz * sin(a);
	vec3 up = -INV_VIEW_MATRIX[0].xyz * sin(a) + INV_VIEW_MATRIX[1].xyz * cos(a);
	streak = INSTANCE_CUSTOM.w;
	if (streak > 0.5) {
		// A streak along its velocity (Sparks.P.Stretch): its axis in the model's Y, its width the X's length,
		// turned about the axis to face the camera.
		vec3 ax = MODEL_MATRIX[1].xyz;
		vec3 to_cam = normalize(INV_VIEW_MATRIX[3].xyz - MODEL_MATRIX[3].xyz);
		vec3 side = cross(ax, to_cam);
		side = length(side) > 1e-5 ? normalize(side) : INV_VIEW_MATRIX[0].xyz;
		// (at least as long as it is wide, so one seen end-on is a dot, never nothing)
		vec3 axl = length(ax) > s ? ax : (length(ax) > 1e-5 ? normalize(ax) * s : INV_VIEW_MATRIX[1].xyz * s);
		MODELVIEW_MATRIX = VIEW_MATRIX * mat4(vec4(side * s, 0.0), vec4(axl, 0.0), vec4(to_cam * s, 0.0), MODEL_MATRIX[3]);
	} else
	MODELVIEW_MATRIX = VIEW_MATRIX * mat4(vec4(right * s, 0.0), vec4(up * s, 0.0), vec4(INV_VIEW_MATRIX[2].xyz * s, 0.0), MODEL_MATRIX[3]);
}

void fragment() {
	float a;
	if (streak > 0.5) {
		// Full at its head (the quad's top, UV.y 0, is the head: At), thinning to nothing at the tail; soft across.
		float x = abs(UV.x * 2.0 - 1.0), y = 1.0 - UV.y;
		float w = mix(0.25, 1.0, y);
		a = (1.0 - smoothstep(0.15 * w, w, x)) * smoothstep(0.0, 0.7, y) * (1.0 - smoothstep(0.93, 1.0, y));
	}
	else if (sprite < 0.5) a = pow(max(0.0, 1.0 - length(UV * 2.0 - 1.0)), 1.6);
	// Round, whatever the sprite: the pack's forks of lightning run to the edge
	// of their square and would show it as they turn.
	else { vec4 t = texture(sprites, vec3(UV, sprite - 1.0)); a = t.r * t.a * (1.0 - smoothstep(0.82, 0.98, length(UV * 2.0 - 1.0))); }
	// Over her, a third of its light: a crowd of hits round her summed to a blob that hid her.
	ALBEDO = tint.rgb * a * tint.a * hero_clear(VERTEX, VIEW_MATRIX, PROJECTION_MATRIX, VIEWPORT_SIZE);
}
