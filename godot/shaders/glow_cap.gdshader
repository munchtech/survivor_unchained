// (lane J art-color, night glow) The glowing mushrooms at tree and rock feet (NightGlow.cs; the palette's "glow" in rigs.json).
// A cap is lit from within, cel: its core near white at the top centre, stepping to the cap colour at its rim in two hard bands
// (the top's normal gives the band); a stem is the stem colour, dim. All times the global glow_k (0 by day: nothing shows).
// The ink class is none (class 2, cel.gdshaderinc cel_tag): a lamp is not inked.
shader_type spatial;
render_mode unshaded, cull_back, shadows_disabled;

global uniform float glow_k;
uniform vec3 cap_col : source_color = vec3(0.75, 0.97, 1.0);
uniform vec3 stem_col : source_color = vec3(0.37, 0.82, 0.88);
uniform float is_stem = 0.0;
uniform float cap_emit = 1.6;
uniform float stem_emit = 0.55;
uniform vec2 bands = vec2(0.82, 0.42);   // the normal's up at which the core ends, and the mid band ends

varying vec3 v_n;

void vertex() { v_n = NORMAL; }

void fragment() {
	vec3 c;
	if (is_stem > 0.5) {
		c = stem_col * stem_emit;
	} else {
		float up = normalize(v_n).y;
		vec3 core = mix(cap_col, vec3(1.0), 0.8);
		c = (up > bands.x ? core : up > bands.y ? mix(cap_col, core, 0.35) : cap_col) * cap_emit;
	}
	ALBEDO = c * glow_k;
	ROUGHNESS = 2.0 / 127.0;
}
