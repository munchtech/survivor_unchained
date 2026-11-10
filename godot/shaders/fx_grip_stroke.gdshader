// Her held grip's cut (src/Fx/BattleFx.Grip.cs): ONE painted stroke (L1's fx_stroke, fx_cel.gdshaderinc) bent round
// the blade's path. Its outer edge rides the blade's reach; the head (the blade now) is the widest and hottest, the
// tail thins inward to a point. Drawn after the grade in the steel family's bands (FxCel.Apply), never added light.
// The mesh is a unit grid (UV.x along the cut 0..1, UV.y from R_IN out past the reach), bent here as blade.gdshader's.
shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;
#include "res://shaders/fx_cel.gdshaderinc"

uniform float grip_span = 2.2;  // radians the blade crosses
uniform float grip_head = 1.0;  // the blade's place along the cut, 0..1
uniform float grip_len = 0.6;   // the stroke's length behind the head, a share of the cut
uniform float grip_life = 0.0;  // 0 whole .. 1 gone (stepped by the caller: core, gold, amber)
uniform float grip_hw = 0.14;   // the head's half-width, a share of the reach
const float R_IN = 0.5;
const float R_OUT = 1.1;
// where the hot line sits across the stroke: 0 its middle, 1 its outer edge
const float GRIP_EDGE = 0.45;

void vertex() {
	float a = (UV.x - 0.5) * grip_span;
	float r = mix(R_IN, R_OUT, UV.y);
	// the cut's plane tilts up through its middle, as an arm's does
	float lift = 0.16 * sin(UV.x * PI) * r;
	VERTEX = vec3(sin(a) * r, lift, cos(a) * r);
}

void fragment() {
	float r = mix(R_IN, R_OUT, UV.y);
	float al = 1.0 - (grip_head - UV.x) / max(grip_len, 1e-3);
	if (al < 0.0 || al > 1.0) discard;
	// the stroke's width here (it thins to a point at the tail); its outer edge stays on the reach from tail to head
	float wf = mix(fx_stroke_shape.z, 1.0, pow(al, 0.7));
	float rc = 1.0 - grip_hw * wf;
	float an = (r - rc) / (grip_hw * wf);
	// steel first: the hot line rides near the outer edge (the blade's edge) and takes more of the width, the gold
	// and the amber trail inward behind it
	float d = an > GRIP_EDGE ? (an - GRIP_EDGE) / (1.0 - GRIP_EDGE) : (GRIP_EDGE - an) / (1.0 + GRIP_EDGE);
	d = pow(clamp(d, 0.0, 4.0), 1.6);
	float across = sign(an - GRIP_EDGE) * d * wf * fx_stroke_shape.x;
	vec4 c = fx_stroke(across, al, grip_life);
	if (c.a < 0.004) discard;
	ALBEDO = fx_out(c.rgb, c.a);
	ALPHA = c.a;
}
