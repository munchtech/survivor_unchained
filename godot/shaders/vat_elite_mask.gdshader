// (lane E lead 5, 17 Nov) The den elite outline's first pass: the elite's solid surfaces drawn WITH the depth test, nudged
// `bias` m toward the camera, writing stencil 3 and no colour wherever its own body is what the camera sees (as her_xray_mask
// does for her). Only elites write it, so the pack and the boss never cut an elite's outline. Drawn before the outline
// (render_priority -3, then -2: Vat.Build) and before her x-ray (-1 to 1), which keeps its own 7.
shader_type spatial;
render_mode unshaded, depth_draw_never, cull_back, blend_mix, shadows_disabled, fog_disabled;
stencil_mode write, compare_always, 3;

#include "res://shaders/vat_elite.gdshaderinc"
uniform float bias = 0.04;

void vertex() {
	vec3 p, n;
	if (!vel_pose(VERTEX_ID, INSTANCE_CUSTOM, COLOR, p, n)) { POSITION = vec4(2.0, 2.0, 2.0, 1.0); }
	else {
		vec4 vp = MODELVIEW_MATRIX * vec4(p, 1.0);
		vp.xyz += normalize(-vp.xyz) * bias;
		POSITION = PROJECTION_MATRIX * vp;
	}
}

void fragment() {
	ALBEDO = vec3(0.0);
	ALPHA = 0.0;
}
