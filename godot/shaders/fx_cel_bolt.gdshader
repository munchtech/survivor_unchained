// The cel bolt (L1 B6's proof of shaders/fx_cel.gdshaderinc): the cinder bolt in flight (BattleFx.Flight's "cinder",
// Cinderfall's) as MB5's FIRE panel draws one: a round white-gold head, flame tongues streaming back in amber and a
// deep red edge with the dark between them, a soft glow off the head, painted sparks shed behind. One quad per bolt,
// laid along its flight and turned to face the lens about that line; its length and width are the instance's basis
// X and Y, COLOR.r a seed, COLOR.a its strength. Under --cel off BattleFx draws the cinder as before.
shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, depth_test_disabled, cull_disabled, shadows_disabled, fog_disabled;

#include "res://shaders/hero_clear.gdshaderinc"
#include "res://shaders/fx_cel.gdshaderinc"

// the head's radius (in half-widths), the tongues' strength at the tail and at the head, their scroll (units a second)
uniform vec4 bolt_shape = vec4(0.55, 0.5, 0.08, 4.0);
// the bias that puts the core at the head: heat += (along - x) * y inside the body
uniform vec2 bolt_bias = vec2(0.62, 0.55);
// sparks: cell (units), density (of cells), length (of the bolt), aspect
uniform vec4 bolt_sparks = vec4(0.35, 0.4, 0.018, 1.6);

varying float span;
varying float seed;
varying float fade;

void vertex() {
	vec3 o = MODEL_MATRIX[3].xyz;
	vec3 ax = MODEL_MATRIX[0].xyz;
	float len = length(ax);
	ax /= max(len, 1e-5);
	float wid = length(MODEL_MATRIX[1].xyz);
	vec3 to_cam = normalize(CAMERA_POSITION_WORLD - o);
	vec3 side = cross(to_cam, ax);
	side = length(side) < 1e-3 ? vec3(0.0, 1.0, 0.0) : normalize(side);
	MODELVIEW_MATRIX = VIEW_MATRIX * mat4(vec4(ax * len, 0.0), vec4(side * wid, 0.0), vec4(cross(ax, side), 0.0), vec4(o, 1.0));
	span = len / max(wid, 1e-5) * 2.0;
	seed = COLOR.r * 61.0;
	fade = COLOR.a;
}

void fragment() {
	float R = bolt_shape.x;
	float x = UV.x * span, y = (UV.y - 0.5) * 2.0;
	float hx = span - 1.0, x0 = 0.12;
	float along = clamp((x - x0) / (hx - x0), 0.0, 1.0);
	float w = R * pow(along, 0.6);
	float d = min(abs(y) - w, length(vec2(x - hx, y)) - R);
	if (x > hx) d = length(vec2(x - hx, y)) - R;
	float t = TIME * bolt_shape.w + seed;
	// the tongues: gradient noise stretched along the flight, its domain warped, scrolled back down it
	vec2 q = vec2(x * 0.85 + t, y * 2.1 + seed);
	q += 0.45 * vec2(fx_gnoise(vec2(x * 0.5 + t * 0.6, y * 1.2 - seed)), fx_gnoise(vec2(x * 0.7 - seed, y * 1.5 + t * 0.4)));
	float n = fx_gnoise(q) * 0.7 + fx_gnoise(q * 2.3 + 5.1) * 0.3;
	float heat = -d / R + n * mix(bolt_shape.y, bolt_shape.z, along);
	if (heat > 0.0) heat = heat + (along - bolt_bias.x) * bolt_bias.y;
	// the tail ends in the licks, never at the quad's edge
	heat -= (1.0 - smoothstep(0.0, 0.9, x)) * 1.2;
	// (the bias can push the tail's body under the cut: those are the dark gaps between its tongues, as MB5's)
	vec4 c = fx_cel(heat, along);
	// painted sparks, shed behind the head, off the hot bands; at least two pixels long whatever the zoom
	float len = max(bolt_sparks.z * span, 2.5 * fwidth(x));
	float s = fx_sparks(vec2(x + t * 0.8, y), vec2(1.0, 0.0), bolt_sparks.x, bolt_sparks.y, len, bolt_sparks.w, seed);
	s *= (1.0 - step(fx_t.y, heat)) * smoothstep(hx + 0.2, hx - 0.4, x) * smoothstep(0.0, 0.5, x) * (1.0 - smoothstep(0.8, 0.98, abs(y)));
	c.rgb = mix(c.rgb, fx_spark_color, s);
	c.a = max(c.a, s);
	ALBEDO = c.rgb;
	ALPHA = clamp(c.a * fade, 0.0, 1.0) * hero_clear(VERTEX, VIEW_MATRIX, PROJECTION_MATRIX, VIEWPORT_SIZE);
}
