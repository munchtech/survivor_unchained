// (lane J art-color, night glow) The glowing mushrooms at tree and rock feet (NightGlow.cs; the palette's "glow" in rigs.json).
// A cap is lit from within, cel: its core near white at the top centre, stepping to the cap colour at its rim in two hard bands
// (the top's normal gives the band); a stem is the stem colour, dim. All times the global glow_k (0 by day: nothing shows).
// The ink class is 1 (cel.gdshaderinc cel_tag; lead 5: the reference's caps are inked shapes, the brightest thing).
shader_type spatial;
render_mode unshaded, cull_back, shadows_disabled;

global uniform float glow_k;
uniform vec3 cap_col : source_color = vec3(0.75, 0.97, 1.0);
uniform vec3 stem_col : source_color = vec3(0.37, 0.82, 0.88);
uniform float is_stem = 0.0;
uniform float cap_emit = 1.0;   // (lead 2: 1.6 bloomed into soft puffs, coordinator k19)
uniform vec3 ink_col : source_color = vec3(0.05, 0.03, 0.12);
uniform float ink_w = 0.38;   // (lead 2: the cap's silhouette inked, as every form in the reference: where the surface turns from the eye)
uniform float stem_emit = 0.55;
uniform vec2 bands = vec2(0.82, 0.42);   // the normal's up at which the core ends, and the mid band ends

uniform float gills = 4.0;    // (lead 6) gill strokes a cap (0 none)
uniform float gill_px = 2.0;
uniform float gill_top = 0.9; // the normal's up they stop at

varying vec3 v_n;

void vertex() { v_n = NORMAL; }

void fragment() {
	vec3 c;
	if (is_stem > 0.5) {
		c = stem_col * stem_emit;
	} else {
		float up = normalize(v_n).y;
		vec3 core = mix(cap_col, vec3(1.0), 0.3);   // (lead 2: 0.8 read as white blobs; the reference's caps are cyan through; lead 4: 0.55 still white, 0.3)
		c = (up > bands.x ? core : up > bands.y ? mix(cap_col, core, 0.35) : cap_col) * cap_emit;
		// (lane J lead 6, judge r4 cel fix 3/7: the den's caps carry gill strokes) gills strokes from the rim toward the top,
		// a fixed screen width (gill_px), stopping short of the core
		if (gills > 0.5) {
			vec3 nn = normalize(v_n);
			float t = atan(nn.z, nn.x) / 6.2831853 * gills;
			vec3 ndx = dFdx(nn), ndy = dFdy(nn);
			float rr = max(nn.x * nn.x + nn.z * nn.z, 1e-4);   // (the angle's change, without atan's jump)
			float fw = gills / 6.2831853 * (abs(nn.x * ndx.z - nn.z * ndx.x) + abs(nn.x * ndy.z - nn.z * ndy.x)) / rr;
			float d = abs(fract(t) - 0.5) / max(fw, 1e-4);
			float g = (1.0 - smoothstep(gill_px * 0.5 - 0.5, gill_px * 0.5 + 0.5, d)) * (1.0 - smoothstep(gill_top - 0.06, gill_top, up));
			c = mix(c, ink_col * cap_emit, g);
		}
	}
	if (dot(normalize(NORMAL), VIEW) < ink_w) c = ink_col;
	ALBEDO = c * glow_k;
	ROUGHNESS = 1.0 / 127.0;   // (lead 5: ink class 1, the world's contour from the screen pass round each cap: an inked shape)
}
