// A cut gem's look (bd-ui W16), lit by no light of the scene: each facet shows what it would reflect
// in a studio of black cards, one broad soft box and two hard white strips, so the facets alternate
// near-black / body colour / bright / white as a jewel's do. The same stone in the photograph, on the
// ground and in the panel: the picture is the stone, turned. Bicolor: split down its axis, B on the +x half.
shader_type spatial;
render_mode unshaded, cull_back;

uniform vec3 body : source_color = vec3(0.37, 0.04, 0.09);
uniform vec3 bright : source_color = vec3(0.89, 0.2, 0.27);
uniform vec3 dark : source_color = vec3(0.02, 0.0, 0.01);
uniform vec3 body_b : source_color = vec3(0.05, 0.16, 0.5);
uniform vec3 bright_b : source_color = vec3(0.35, 0.58, 1.0);
uniform vec3 dark_b : source_color = vec3(0.0, 0.01, 0.04);
uniform bool split = false;
uniform float ripple = 0.3;
uniform float alt = 0.0;        // 1: every facet alternates dark / body / bright by its own hash (the clear stone)
uniform float split_turn = 0.0; // the split plane's turn about the axis, so a photograph's turned stone splits down the screen

varying vec3 lpos;

void vertex() { lpos = VERTEX; }

void fragment() {
	vec3 n = normalize((INV_VIEW_MATRIX * vec4(NORMAL, 0.0)).xyz);
	vec3 v = normalize((INV_VIEW_MATRIX * vec4(VIEW, 0.0)).xyz);
	// A little curve in each flat facet (its place on the stone), so a strip sweeps across a big one.
	n = normalize(n + ripple * (MODEL_MATRIX * vec4(lpos.x, lpos.y * 0.6, lpos.z, 0.0)).xyz);
	vec3 r = reflect(-v, n);

	bool b = split && lpos.x * cos(split_turn) + lpos.z * sin(split_turn) > 0.0;
	vec3 c_body = b ? body_b : body, c_bright = b ? bright_b : bright, c_dark = b ? dark_b : dark;

	// The studio, as what a direction sees.
	float strip1 = step(0.0, r.z + 0.1) * step(abs(r.x * 0.94 - r.y * 0.34 + 0.3), 0.05);
	float strip2 = step(-0.3, r.z) * step(abs(r.y + 0.3 * r.x - 0.5), 0.045);
	float cards = max(step(0.66, abs(r.x)), step(r.y, -0.6));
	float box = step(0.15, r.y) * step(abs(r.x), 0.5) * step(-0.4, r.z);
	vec3 col = c_body;
	col = mix(col, c_bright, box);
	col = mix(col, c_dark, cards * (1.0 - box));
	// The body colour is a touch lit by where the facet faces, so no two read the same.
	float h = fract(dot(n, vec3(3.1, 7.3, 5.7)));
	// The pavilion, seen through the crown, alternates facet by facet.
	float low = step(n.y, 0.0);
	col = mix(col, h < 0.38 ? c_dark : (h < 0.76 ? c_body : c_bright), max(low * 0.9, alt));
	col *= 0.9 + 0.2 * h;
	vec3 white = mix(c_bright, vec3(1.0), 0.72);
	col = mix(col, white, max(strip1, strip2));
	ALBEDO = col;
}
