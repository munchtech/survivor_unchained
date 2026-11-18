// (lane E lead 5, 17 Nov; judge 3: an elite's rim "a glittering stick", 45 bits) The den elite's outline: ONE solid
// bone-ivory stroke round its OUTER silhouette. Every band from n.v inside the body (vat.gdshaderinc's den rim) lit each
// leg's, fur card's and fold's own grazing edge too, an ivory squiggle per interior contour. This pass is the elite's solid
// surfaces grown `rim_px` screen pixels along their normals (as her_xray_rim), drawn only where the stencil is not the
// elite's own (vat_elite_mask.gdshader wrote 3 wherever its body is seen), so it shows only outside the body: the dark
// line inside (vat.gdshaderinc), then this stroke. Depth-tested, nudged `bias` m toward the camera so the floor at its
// paws does not cut it; it writes depth so the crowd's ground blob (blend_mul, drawn later) does not dim it. Struck (the
// hit kit's rim, 8 frames), it leans `hit` of the way to the kit's gold, one stroke (the kit's own gold edge is off on a
// live den elite, vat.gdshaderinc).
shader_type spatial;
render_mode unshaded, depth_draw_always, cull_back, blend_mix, shadows_disabled, fog_disabled;
stencil_mode read, compare_not_equal, 3;

#include "res://shaders/vat_elite.gdshaderinc"
global uniform vec4 flare_mark_rim;
// (linear; Oklab .72/.09/64 on screen after the den's grade)
uniform vec3 rim_color = vec3(0.50, 0.39, 0.29);
uniform float rim_px = 1.75;
uniform float bias = 0.05;
uniform float hit = 0.35;
varying flat float vel_hit;

void vertex() {
	vec3 p, n;
	vel_hit = 0.0;
	if (!vel_pose(VERTEX_ID, INSTANCE_CUSTOM, COLOR, p, n)) { POSITION = vec4(2.0, 2.0, 2.0, 1.0); }
	else {
		vec4 vp = MODELVIEW_MATRIX * vec4(p, 1.0);
		vp.xyz += normalize(-vp.xyz) * bias;
		vec4 clip = PROJECTION_MATRIX * vp;
		vec2 dir = (PROJECTION_MATRIX * vec4(mat3(MODELVIEW_MATRIX) * n, 0.0)).xy;
		float l = length(dir);
		if (l > 1e-5) clip.xy += dir / l * rim_px * 2.0 / VIEWPORT_SIZE * clip.w;
		POSITION = clip;
		int w = int(INSTANCE_CUSTOM.w + 0.5);
		vel_hit = float((w >> 6) & 1) * clamp((INSTANCE_CUSTOM.y - floor(INSTANCE_CUSTOM.y + 0.5)) / 0.45, 0.0, 1.0);
	}
}

void fragment() {
	vec3 gold = mix(vec3(1.0, 0.479, 0.069), flare_mark_rim.rgb, flare_mark_rim.a) * 1.2;
	ALBEDO = mix(rim_color, gold, hit * vel_hit);
	ALPHA = 1.0;
}
