// Her Sunderer greatsword (tools/assets/sunder_blade.py, LampIron.SunderBlade): clean bright steel, gilt fittings, a dark
// leather grip. The mesh's vertex colour says which part (G: 0.05 the blade's edge bevel, 0.15 its flats, 0.25 its fuller,
// 0.5 the gilt, 1.0 the leather), where the edges are (R: 0.5 flat, toward 1 a sharp outer edge, toward 0 a crease) and a
// per-part random (B). Everything is drawn in the model's own space (pommel end at y = 0, the tip up +y, the guard along x),
// so it stays on the piece however Arms scales it: the steel brushed lengthwise (streaks in its roughness and a slow run of
// light to dark along the flat), the fuller a darker, rougher channel, a gilt etched panel just below the guard (a frame,
// a sun, a running double scroll), the leather in a lapped spiral.
shader_type spatial;
render_mode blend_mix, cull_back, depth_draw_opaque;
// (the material library, godot/data/look/materials.json: this shader's default class, iron: her greatsword's steel, its gilt and grip under the same class; L1 B2r2)
#define CEL_SPEC vec4(7.0, 1.0, 1.0, 1.0)
#define CEL_NMAP 0.20   // (L1 C2: the class's cel_nmap)
#define CEL_EXACT_ROUGH
#include "res://shaders/cel.gdshaderinc"

uniform sampler2D masks : filter_linear_mipmap_anisotropic, repeat_enable;

// steel
uniform vec3 steel = vec3(0.34, 0.34, 0.333);
uniform float steel_rough = 0.32;
uniform float streak_k = 0.10;      // the brushed streaks' share of the flat's roughness
uniform float run_k = 0.18;         // the slow light-to-dark run along the flat (albedo)
uniform float ramp_k = 0.11;        // the whole blade this much darker toward the point (root = 0, tip = 1)
uniform float panel_warm = 0.12;     // the etched ground's warm cast (cuts the sky's blue on it)
uniform vec3 bevel = vec3(0.92, 0.92, 0.90);
uniform float bevel_rough = 0.06;
uniform float bevel_glow = 0.23;     // the bevel's own bright line (emission, the share of its albedo): a mirror edge reflects the dark valley, not light
uniform float fuller_k = 0.50;      // the fuller's albedo against the flat's
uniform float fuller_rough = 0.40;
// gilt (oathbrand's metal_gold: its base colour texture's linear mean times its factor)
uniform vec3 gilt = vec3(0.56, 0.39, 0.125);
uniform float gilt_rough = 0.22;
uniform float gilt_recess = 0.55;   // the gilt's creases (round the pommel's sun) darkened to this
// leather
uniform vec3 leather = vec3(0.040, 0.026, 0.017);
uniform float leather_rough = 0.72;
uniform float wrap_pitch = 0.012;
uniform float wrap_groove = 0.82;   // the groove between turns, against the strip
// the etched panel (model metres): from the blade's root up, its half-width
uniform float panel_y0 = 0.384;
uniform float panel_len = 0.15;
uniform float panel_hw = 0.0165;
uniform float panel_line = 0.0011;
uniform float panel_ground = 0.55;  // the etched ground inside the frame (frosted, darker), so the gilt reads on it
uniform float debug_view = 0.0;

varying vec3 opos;
varying vec3 onrm;

void vertex() {
	opos = VERTEX;
	onrm = NORMAL;
}

float line_mask(float d, float w) {
	float aa = max(fwidth(d), 1e-5);
	return 1.0 - smoothstep(w * 0.5 - aa, w * 0.5 + aa, d);
}

float seg_dist(vec2 p, vec2 a, vec2 b) {
	vec2 pa = p - a, ba = b - a;
	float h = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0);
	return length(pa - ba * h);
}

// The etched panel's gilt lines at (x, y in the panel, 0 at its top under the guard, growing toward the tip).
float panel(vec2 q) {
	float hw = panel_hw, L = panel_len, w = panel_line;
	float m = 0.0;
	// the frame: sides, a top bar, a pointed foot
	float foot = L - 0.020;
	if (q.y > 0.004 && q.y < foot) m = max(m, line_mask(abs(abs(q.x) - hw), w));
	if (abs(q.x) < hw + w) m = max(m, line_mask(abs(q.y - 0.004), w));
	m = max(m, line_mask(seg_dist(vec2(abs(q.x), q.y), vec2(hw, foot), vec2(0.0, L - 0.002)), w));
	// the sun: a disc, a ring, twelve rays
	vec2 c = q - vec2(0.0, 0.027);
	float r = length(c);
	m = max(m, 1.0 - smoothstep(0.0034 - fwidth(r), 0.0034 + fwidth(r), r));
	m = max(m, line_mask(abs(r - 0.0068), w * 0.9));
	float th = atan(c.y, c.x);
	float a = mod(th + 3.14159265 / 12.0, 3.14159265 / 6.0) - 3.14159265 / 12.0;
	float ray_len = mod(floor((th + 3.14159265 / 12.0) / (3.14159265 / 6.0)), 2.0) < 0.5 ? 0.0140 : 0.0118;
	float rw = w * mix(1.2, 0.35, clamp((r - 0.0085) / (ray_len - 0.0085), 0.0, 1.0));
	if (r > 0.0085 && r < ray_len) m = max(m, line_mask(abs(r * sin(a)), rw));
	// the running double scroll below it, and a dot in each loop
	float y0 = 0.045, y1 = foot - 0.008;
	if (q.y > y0 && q.y < y1) {
		float ph = (q.y - y0) / 0.034 * 6.28318;
		float A = hw * 0.62, s = sin(ph), sl = A * cos(ph) * 6.28318 / 0.034;
		float k = 1.0 / sqrt(1.0 + sl * sl);
		m = max(m, line_mask(abs(q.x - A * s) * k, w));
		m = max(m, line_mask(abs(q.x + A * s) * k, w));
		float cell = floor((q.y - y0) / 0.017);
		vec2 dc = vec2(abs(q.x) - A * 0.55, q.y - (y0 + (cell + 0.5) * 0.017));
		if (cell >= 0.0) m = max(m, 1.0 - smoothstep(0.0012 - fwidth(dc.y), 0.0012 + fwidth(dc.y), length(dc)));
	}
	return m;
}

void fragment() {
	vec3 w3 = pow(abs(normalize(onrm)), vec3(4.0));
	w3 /= (w3.x + w3.y + w3.z);
	float conv = clamp((COLOR.r - 0.5) * 2.0, 0.0, 1.0);
	float cav = clamp((0.5 - COLOR.r) * 2.0, 0.0, 1.0);
	vec3 col;
	float metal = 1.0, rough, spec = 0.5;
	vec3 dbg = vec3(1.0);
	vec3 glow = vec3(0.0);
	if (COLOR.g > 0.75) {
		// the leather: a lapped spiral, low contrast
		float ph = fract(opos.y / wrap_pitch + atan(opos.z / 0.84, opos.x) / 6.28318);
		float strip = smoothstep(0.0, 0.18, ph) * (1.0 - smoothstep(0.86, 0.97, ph));
		float g = texture(masks, opos.xy * vec2(40.0, 40.0) + COLOR.b * 3.7).g;
		col = leather * (0.92 + 0.16 * g) * mix(wrap_groove, 1.0, strip) * (0.95 + 0.08 * ph);
		metal = 0.0;
		rough = leather_rough + 0.06 * g;
		spec = 0.3;
		dbg = vec3(1.0, 0.85, 0.0);
	} else if (COLOR.g > 0.35) {
		// the gilt: even, bright on its edges, darker only in its creases
		float g = texture(masks, opos.xy * 9.0 + COLOR.b * 3.7).g;
		col = gilt * (0.96 + 0.08 * g);
		col = mix(col, gilt * 1.18, smoothstep(0.55, 0.9, conv) * 0.7);
		col *= mix(1.0, gilt_recess, smoothstep(0.1, 0.6, cav));
		rough = mix(gilt_rough + 0.04 * (g - 0.5), gilt_rough - 0.08, smoothstep(0.55, 0.9, conv));
		dbg = vec3(1.0, 0.5, 0.0);
	} else {
		// the steel: brushed lengthwise
		float bev = 1.0 - smoothstep(0.08, 0.12, COLOR.g);
		float ful = smoothstep(0.18, 0.22, COLOR.g);
		float st = texture(masks, vec2(opos.x * 55.0, opos.y * 0.6) + COLOR.b).g;
		float st2 = texture(masks, vec2(opos.x * 190.0, opos.y * 1.7) + 0.37).b;
		float streak = (st - 0.5) * 0.7 + (st2 - 0.5) * 0.5;
		float run = texture(masks, vec2(0.13, opos.y * 0.9)).g - 0.5;
		vec3 flat_col = steel * (1.0 + run * run_k * 2.0) * (1.0 + streak * 0.06);
		float flat_r = steel_rough + streak * streak_k;
		vec3 ful_col = steel * fuller_k * (1.0 + streak * 0.05);
		float ful_r = fuller_rough + streak * streak_k * 0.5;
		col = mix(flat_col, ful_col, ful);
		rough = mix(flat_r, ful_r, ful);
		col = mix(col, bevel * (1.0 + streak * 0.04), bev);
		rough = mix(rough, bevel_rough + streak * 0.03, bev);
		col = mix(col, bevel * 1.2, bev * smoothstep(0.75, 0.95, COLOR.r));
		col *= 1.0 - ramp_k * clamp((opos.y - 0.372) / 1.04, 0.0, 1.0);
		glow = bevel * bevel_glow * bev;
		// the etched panel: gilt lines in the flat and the fuller, just below the guard
		vec2 q = vec2(opos.x, opos.y - panel_y0);
		if (bev < 0.5 && q.y > 0.0 && q.y < panel_len) {
			float pm = panel(q);
			float inside = step(abs(q.x), panel_hw) * step(0.004, q.y) * step(q.y, panel_len - 0.002 - (panel_len - 0.022) * 0.0)
				* step(abs(q.x) / panel_hw * 0.018 + (q.y - (panel_len - 0.020)), 0.018);
			col *= mix(vec3(1.0), vec3(1.0 + panel_warm, 1.0, 1.0 - panel_warm * 1.6) * panel_ground, inside);
			rough = mix(rough, 0.55, inside);
			col = mix(col, gilt * 0.95, pm);
			rough = mix(rough, gilt_rough + 0.04, pm);
		}
		dbg = bev > 0.5 ? vec3(1.0, 0.0, 0.0) : ful > 0.5 ? vec3(0.0, 0.0, 1.0) : vec3(0.0, 1.0, 0.0);
	}
	ALBEDO = col;
	EMISSION = glow;
	METALLIC = metal;
	ROUGHNESS = clamp(rough, 0.05, 1.0);
	SPECULAR = spec;
	if (debug_view > 0.5) { ALBEDO = vec3(0.0); EMISSION = dbg * 0.5; ROUGHNESS = 1.0; SPECULAR = 0.0; METALLIC = 0.0; }
	CEL_FRAGMENT;
}
