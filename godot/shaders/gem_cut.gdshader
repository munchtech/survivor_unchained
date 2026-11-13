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
uniform float glow = 0.0;       // the ground stone's own light: 0.6 of its bright at the table, no facet darker than its body (a lit jewel, not a dark rock)
uniform float bright_share = 0.24; // the share of the pavilion's wedges that catch the light (a garnet on the ground takes more)
uniform float tab_lo = 0.75;    // how far down the crown the stone's own light reaches (a garnet's reaches the kites and stars)
uniform float floor_k = 0.6;    // the ground stone's darkest facet as a fraction of its body
uniform float lit_min = 0.3;    // how much of the light the non-table facets take
uniform float glow_b = -1.0;    // the B half's own glow when it differs (bicolor: garnet 0.9, sapphire 0.6)
uniform float split_turn = 0.0; // the split plane's turn about the axis, so a photograph's turned stone splits down the screen
uniform bool split_view = false; // the ground stone: split down the screen through its own centre, whatever its turn (round 2: a local split went edge-on as it spun)

varying vec3 lpos;
varying vec3 lnorm;
varying vec3 vpos;
varying vec3 tcen;  // the table's centre and the stone's scale in view space (the table strip is laid in screen terms)
varying float sc;

void vertex() {
	lpos = VERTEX; lnorm = NORMAL;
	vec3 mid0 = (MODELVIEW_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
	vpos = (MODELVIEW_MATRIX * vec4(VERTEX, 1.0)).xyz - mid0;
	tcen = (MODELVIEW_MATRIX * vec4(0.0, 0.25, 0.0, 1.0)).xyz - mid0;
	sc = length(MODELVIEW_MATRIX[0].xyz);
}

void fragment() {
	vec3 n = normalize((INV_VIEW_MATRIX * vec4(NORMAL, 0.0)).xyz);
	vec3 v = normalize((INV_VIEW_MATRIX * vec4(VIEW, 0.0)).xyz);
	// A little curve in each flat facet (its place on the stone), so a strip sweeps across a big one.
	n = normalize(n + ripple * (MODEL_MATRIX * vec4(lpos.x, lpos.y * 0.6, lpos.z, 0.0)).xyz);
	vec3 r = reflect(-v, n);

	bool b = split && (split_view ? vpos.x > 0.0 : lpos.x * cos(split_turn) + lpos.z * sin(split_turn) > 0.0);
	vec3 c_body = b ? body_b : body, c_bright = b ? bright_b : bright, c_dark = b ? dark_b : dark;

	// The studio, as what a direction sees.
	float cards = max(step(0.66, abs(r.x)), step(r.y, -0.6));
	float box = step(0.15, r.y) * step(abs(r.x), 0.5) * step(-0.4, r.z);
	vec3 col = c_body;
	col = mix(col, c_bright, box);
	col = mix(col, c_dark, cards * (1.0 - box));
	// The body colour is a touch lit by where the facet faces, so no two read the same.
	float h = fract(dot(n, vec3(3.1, 7.3, 5.7)));
	// The pavilion, seen through the crown, alternates facet by facet.
	float low = step(n.y, 0.0);
	// (By the pavilion's eight mains, a wedge each, and not facet by facet: the thin lower-girdle facets between them made venetian blinds.)
	float sector = floor(atan(lpos.z, lpos.x) / 0.7853982);
	float hp = fract(sector * 0.381966 + 0.17);
	float hh = low > 0.5 ? hp : h;
	col = mix(col, hh < 0.3 ? c_dark : (hh < 1.0 - bright_share ? c_body : c_bright), max(low * 0.9, alt));
	col *= 0.9 + 0.2 * h;
	// Lit from inside (the ground stone): the table glows, nothing is darker than the body.
	float tab = smoothstep(tab_lo, tab_lo + 0.2, normalize(lnorm).y);
	float gl = (b && glow_b >= 0.0) ? glow_b : glow;
	col = max(col, c_body * floor_k * step(0.001, gl));   // (the floor: how dark a facet may go; a garnet's is low so its #5E0B16 facets show)
	col = mix(col, c_bright, gl * (lit_min + (1.0 - lit_min) * tab));
	vec3 white = mix(c_bright, vec3(1.0), 0.72);
	// One strip on the pavilion (two made venetian-blind stripes there), both on the crown.
	// W24: one soft strip across the table at 60% (two crossed as a white X on the stone); pure white lives only in the glint.
	// Laid across the table on screen, 30 degrees up to the right, soft-edged.
	vec2 tp = (vpos.xy - tcen.xy) / sc;
	float tdist = tp.y - 0.577 * tp.x + 0.03;
	float tabm = smoothstep(0.85, 0.95, normalize(lnorm).y);
	col = mix(col, mix(c_bright, vec3(1.0), 0.3), tabm * smoothstep(0.075, 0.025, abs(tdist)) * 0.6);
	ALBEDO = col;
}
