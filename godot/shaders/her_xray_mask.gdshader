// The x-ray's first pass (lane E lead 3, 16 Nov; lane A's movement judge, leg 10: "the see-through outline breaks behind
// the slab"): her solid meshes drawn WITH the depth test, nudged `bias` m toward the camera, writing stencil 7 and no
// colour wherever her own surface is what the camera sees. The fill (her_xray) and the outline (her_xray_rim) pass only
// where the stencil is not 7, so they skip every pixel where she is in plain sight, her own limbs behind her torso
// included. That is what the capsule round her feet did (her_r 0.8 m, -0.3..2.2 m up), and the capsule was the break:
// a slab she stood against had its face inside it, so the x-ray took the slab for her own body and drew nothing there.
// Drawn before every fill (render_priority -1, PlayerView.xray).
shader_type spatial;
render_mode unshaded, depth_draw_never, cull_back, blend_mix, shadows_disabled, fog_disabled;
stencil_mode write, compare_always, 7;

uniform float bias = 0.06;

void vertex() {
	vec4 vp = MODELVIEW_MATRIX * vec4(VERTEX, 1.0);
	vp.xyz += normalize(-vp.xyz) * bias;
	POSITION = PROJECTION_MATRIX * vp;
}

void fragment() {
	ALBEDO = vec3(0.0);
	ALPHA = 0.0;
}
