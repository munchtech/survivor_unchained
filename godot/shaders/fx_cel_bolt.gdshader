// The cel bolt (L1 B6's proof of shaders/fx_cel.gdshaderinc): the cinder bolt in flight (BattleFx.Flight's "cinder",
// Cinderfall's) as MB5's FIRE panel draws one: a round white-gold head, flame tongues streaming back in amber and a
// deep red edge with the dark between them, a soft glow off the head, painted sparks shed behind. One quad per bolt,
// laid along its flight and turned to face the lens about that line; its length and width are the instance's basis
// X and Y, COLOR.r a seed, COLOR.a its strength. Under --cel off BattleFx draws the cinder as before.
shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, depth_test_disabled, cull_disabled, shadows_disabled, fog_disabled;

#include "res://shaders/hero_clear.gdshaderinc"
#include "res://shaders/fx_cel.gdshaderinc"

// The shape (B6 round 2: tools/style/fx_bolt_proto.py's field, designed beside MB5's FIRE bolt): in the quad's units
// (x 0 at the tail to span at the front, y -1..1 across) a round white-gold ball near the front, a body that fans out
// behind it, flame tongues along flow lanes that converge on the head (gradient noise stretched along the flight and
// swept back toward the outside), long dark gaps that split the tail into tongues and dark smoke bites; all scrolled
// back down the bolt. One heat field, cut into the school's stepped bands by fx_cel().
// head radius, the body's half-width at the tail (of the head's), its taper power, the heat's rise toward the head (power)
// (L1 W2 C5, the B6 verdict "shrink the head to about 0.6x": R 0.6 to 0.36, the tail's half-width held at 0.87 (1.45 x 0.6
// = 2.4 x 0.36); the ball 1.0 of the head and stretched 2.2 along, the head's heat 1.05, so the core keeps its share of the
// body (fx_bolt_proto.py with fx_measure.py bolt: head 0.172 to 0.133 of the length, MB5 0.156; bites 11 to 12, the
// verdict's 10-12; e/m/c shares 0.47/0.30/0.23 to 0.44/0.32/0.24, MB5 0.34/0.41/0.25))
uniform vec4 bolt_shape = vec4(0.36, 2.4, 0.8, 2.0);
// heat at the tail, at the head; the cross profile's power; the sweep (noise sheared back by |lane|)
uniform vec4 bolt_heat = vec4(0.7, 1.05, 2.0, 0.9);
// the ball: its centre back from the head's, its stretch along, its radius (of the head's), its heat
// (W2 C5b) its heat 0.7 -> 0.5: at the play camera (a 110-140 px bolt) the tail's thin tongues fall under a pixel and the
// head's ball held 0.37 of the bands against MB5's 0.25 (lookdev r3, fx_measure shot: e/m/c 0.25/0.38/0.37; MB5 0.34/0.41/0.25)
uniform vec4 bolt_ball = vec4(0.25, 2.2, 1.0, 0.5);
// the tongues: frequency along, across (per lane), strength at the tail, at the head
uniform vec4 bolt_licks = vec4(0.8, 2.6, 0.6, 0.12);
// the gaps: frequency along, across, strength, power of its fall toward the head; the bites' frequency along, across
uniform vec4 bolt_gaps = vec4(0.45, 3.2, 2.0, 0.7);
uniform vec4 bolt_bites = vec4(1.0, 3.2, 3.0, 2.0);
// the bites' threshold at the tail, at the head; the lanes' bend; the scroll (units a second)
uniform vec4 bolt_flow = vec4(-0.05, 1.0, 0.5, 3.0);
// sparks: cell (units), density (of cells), length (of the bolt), aspect
uniform vec4 bolt_sparks = vec4(0.35, 0.4, 0.018, 1.6);
// (W2 C5b) the quad's room across for the sparks, in body half-widths: MB5's sparks fly up to about 1.5x the tail's
// half-height off its axis (the board crop: tail 0.86 of the quad, sparks to its rim and past it); at 1 the tail filled the
// quad and left the sparks a strip under a pixel (B6r2: 0-1 sparks). The body's size on screen is unchanged.
uniform float bolt_room = 1.5;

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
	MODELVIEW_MATRIX = VIEW_MATRIX * mat4(vec4(ax * len, 0.0), vec4(side * wid * bolt_room, 0.0), vec4(cross(ax, side), 0.0), vec4(o, 1.0));
	span = len / max(wid, 1e-5) * 2.0;
	seed = COLOR.r * 61.0;
	fade = COLOR.a;
}

void fragment() {
	float R = bolt_shape.x;
	float x = UV.x * span, y = (UV.y - 0.5) * 2.0 * bolt_room;
	float hx = span - 1.0, x0 = 0.15;
	float along = clamp((x - x0) / (hx - x0), 0.0, 1.0);
	float t = TIME * bolt_flow.w;
	float w = R * mix(bolt_shape.y, 1.0, pow(along, bolt_shape.z));
	float v = y / w;
	v += bolt_flow.z * (1.0 - along) * fx_gnoise(vec2(x * 0.35 + 2.0, 0.5 + seed));
	float inside = x < hx ? abs(v) : length(vec2(x - hx, y)) / R;
	float hot = mix(bolt_heat.x, bolt_heat.y, pow(along, bolt_shape.w));
	float heat = (inside < 1.0 ? 1.0 - pow(inside, bolt_heat.z) : (1.0 - inside) * bolt_heat.z) * hot;
	float ball = length(vec2((x - (hx - bolt_ball.x)) / bolt_ball.y, y)) / (R * bolt_ball.z);
	heat += bolt_ball.w * sqrt(clamp(1.0 - ball, 0.0, 1.0));
	// the noise's domain, swept back toward the outside
	float xs = x + bolt_heat.w * abs(v);
	float n = fx_gnoise(vec2((xs + t) * bolt_licks.x, v * bolt_licks.y + seed)) * 0.65
		+ fx_gnoise(vec2((xs + t) * bolt_licks.x * 2.3 + 5.1, v * bolt_licks.y * 2.1 - seed)) * 0.35;
	heat += n * mix(bolt_licks.z, bolt_licks.w, along);
	float g = fx_gnoise(vec2((xs + t * 0.8) * bolt_gaps.x + 3.7, v * bolt_gaps.y + seed * 0.7));
	heat -= bolt_gaps.z * pow(1.0 - along, bolt_gaps.w) * max(g, 0.0);
	float b = fx_gnoise(vec2((xs + t * 0.6) * bolt_bites.x + 11.0, v * bolt_bites.y + seed * 1.3));
	heat = min(heat, (mix(bolt_flow.x, bolt_flow.y, pow(along, bolt_bites.w)) - b) * bolt_bites.z);
	// the tail ends in the licks, never at the quad's edge
	heat -= (1.0 - smoothstep(0.0, 0.9, x)) * 1.2;
	vec4 c = fx_cel(heat, along);
	// painted sparks, shed behind the head, off the hot bands; at least two pixels long whatever the zoom
	float len = max(bolt_sparks.z * span, 2.5 * fwidth(x));
	float s = fx_sparks(vec2(x + t * 0.8, y), vec2(1.0, 0.0), bolt_sparks.x, bolt_sparks.y, len, bolt_sparks.w, seed);
	s *= (1.0 - step(fx_t.x, heat)) * smoothstep(hx + 0.2, hx - 0.4, x) * smoothstep(0.0, 0.5, x) * (1.0 - smoothstep(0.8 * bolt_room, 0.98 * bolt_room, abs(y)));
	c.rgb = mix(c.rgb, fx_spark_color, s);
	c.a = max(c.a, s);
	float a = clamp(c.a * fade, 0.0, 1.0) * hero_clear(VERTEX, VIEW_MATRIX, PROJECTION_MATRIX, VIEWPORT_SIZE);
	ALBEDO = fx_out(c.rgb, a);
	ALPHA = a;
}
