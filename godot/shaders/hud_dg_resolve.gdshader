// M4 (docs/design/M4_HUD.md section 2): Resolve, heat rising through the Drowned Girl's hair. One quad over her figure
// (LifeLamp's own transform), light drawn over the bronze: unshaded.
// veins (tools/uiforge/dg_resolve_veins.py, lamp_veins.png at the figure's 2x): R the hair's ridges (the veins), G the
// gauge g (1 the crown, 0 the tips: a geodesic along the locks), B the soft hair mask, A the weight clamp (1 a vein's
// bright middle, 0 a wide ridge's ember edge). A vein with g <= level is lit,
// and graded as heated metal is (M4 lead 8, the judge's "line art, not heat"): edge amber at the tips and the cold end,
// mid gold up the fill, a paler hot gold in the last hot_w under the front, core white-gold only in the last core_w.
// The bronze round a lit vein is warmed (rings of the lit veins, hotter by the front) and the hair under the front
// takes an ember underglow. No vein is drawn wider than the bake's clamp_px: a wide ridge keeps a bright middle and an
// ember edge (A).
// An unlit ridge falls cold_k toward plain bronze, so 0 is cold metal. ResolveVeins.cs drives every motion through
// the uniforms below, set only on change.
shader_type canvas_item;
render_mode blend_premul_alpha, unshaded;

uniform sampler2D veins : hint_default_black, filter_linear;
uniform sampler2D cold : source_color, filter_linear;   // her figure (the warm rim on her profile when full)
uniform vec2 canvas = vec2(474.67, 258.0);
uniform vec2 tex_px = vec2(949.0, 516.0);
// the steel bands (fx_language.json schools.physical): edge, mid, core; the steel spark
uniform vec4 c_edge : source_color = vec4(0.792, 0.431, 0.024, 1.0);
uniform vec4 c_mid : source_color = vec4(0.976, 0.698, 0.078, 1.0);
uniform vec4 c_core : source_color = vec4(0.984, 0.945, 0.847, 1.0);
uniform vec4 c_spark : source_color = vec4(0.992, 0.820, 0.443, 1.0);

uniform float level : hint_range(0.0, 1.0) = 0.0;   // the front (eased)
uniform float alpha = 1.0;                          // 1, or the 0.6 hold when her figure fades (Behind)
uniform float core_w = 0.06;                        // the core band's reach in g under the front
uniform float tip_w = 0.14;                         // the tips' edge-amber band (g under this)
uniform float under = 0.19;                         // the ember underglow's strength below the front
uniform float hot_w = 0.16;                         // the hot gold's reach in g under the core band
// a packet running up from the tips (Landed core, Taken edge, Blocked spark and smaller): its g, size, color
uniform float pkt_g = -1.0;
uniform float pkt_k = 0.0;
uniform float pkt_w = 0.07;
uniform vec4 pkt_c : source_color = vec4(1.0);
uniform float flare = 0.0;                          // the front's flare (after a packet arrives)
uniform vec2 spent = vec2(0.0);                     // Spent: the band of g just spent (lo, hi)
uniform float spent_k = 0.0;                        // its flash (core) going dark
uniform float drain = 0.0;                          // Drained: embers running down the veins (a scroll along g)
uniform float cool = 0.0;                           // Faded: the lit veins cool, mid (0) -> edge (0.5) -> bronze (1)
uniform float shimmer_g = -1.0;                     // Full: a slow shimmer down the veins (its g)
uniform float glint = 0.0;                          // Full: the four-point glint at the crown
uniform vec2 crown = vec2(253.5, 9.5);              // the crown in the quad (1080 px)
uniform float rim = 0.0;                            // Full: the faint warm rim on her profile
// the vein's coverage from R (the ridge strength): only the ridges light, the bronze shows between them
uniform float r_lo = 0.5;
uniform float r_hi = 0.85;
// the gauge as seen: the tips under g_floor sit behind the flask plate (and below the frame), so g is read from there,
// and 25 / 60 / 100% light about that share of the veins she shows (measured at 1:1, M4 fix round)
uniform float g_floor = 0.18;
uniform float glow_k = 1.0;                         // the warmed bronze round a lit vein (added, hair-bound)
// (a vein's greatest bright width is the bake's: clamp_px 7.5 of the texture's px, 2.7 of them to a screen px at the
// HUD's 0.85, about 3 px; A holds it)
// an unlit ridge's fall toward plain bronze (the bronze between her ridges, measured at 1:1 by day)
uniform float cold_k = 0.30;
uniform vec4 c_bronze : source_color = vec4(0.215, 0.176, 0.133, 1.0);

float gauge(float G) { return clamp((G - g_floor) / (1.0 - g_floor), 0.0, 1.0); }
// Spent's band at g (its flash)
float spent_at(float g) { return spent_k * step(spent.x, g) * step(g, spent.y) * step(0.001, spent.y - spent.x); }
// the heat a neighbor gives off: a lit vein there (or one in Spent's flash), hotter the nearer the front
float heat_at(vec2 uv)
{
	vec3 t = texture(veins, uv).rgb;
	float g = gauge(t.g);
	float l = max(step(g, level) * step(0.001, level), spent_at(g));
	return smoothstep(r_lo, r_hi, t.r) * smoothstep(0.15, 0.6, t.b) * l * mix(0.55, 1.5, smoothstep(0.45, 0.0, level - g));
}

void fragment()
{
	vec3 V = texture(veins, UV).rgb;
	float g = gauge(V.g), m = V.b;
	// the vein's cover and its bright middle (the baked clamp, A), averaged over the screen px: 3 x 3 taps across the
	// px's own footprint in the mask. One tap at the px center lit a vein thinner than a screen px (the back of her head:
	// 2.8 mask px, 2.7 of them to a screen px) in beads; the average draws it as one even line at any HUD scale.
	vec2 fx = dFdx(UV) / 3.0, fy = dFdy(UV) / 3.0;
	float s0 = 0.0, s = 0.0;
	for (int j = -1; j <= 1; j++) {
		for (int i = -1; i <= 1; i++) {
			vec4 t = texture(veins, UV + fx * float(i) + fy * float(j));
			float v = smoothstep(r_lo, r_hi, t.r);
			s0 += v;
			s += v * t.a;
		}
	}
	s0 /= 9.0;
	s /= 9.0;
	vec2 tp = 1.0 / tex_px;
	float on = step(0.001, level);
	float lit = step(g, level) * on;
	// the warmth round the lit veins (three rings: 4, 9 and 16 tex px, about 1.5, 3.3 and 6 px on screen), and the hair
	// mask grown 4 tex px: every added term lives in the hair (a few px beyond it), never outside (g means nothing there)
	float gl = 0.0, mg = m;
	for (int i = 0; i < 8; i++) {
		float an = float(i) * 0.785398;
		vec2 o = vec2(cos(an), sin(an)) * tp;
		vec2 o2 = vec2(cos(an + 0.392699), sin(an + 0.392699)) * tp;
		gl += heat_at(UV + o * 4.0) + 0.7 * heat_at(UV + o2 * 9.0) + 0.45 * heat_at(UV + o * 16.0);
		mg = max(mg, texture(veins, UV + o * 4.0).b);
	}
	gl /= 17.2;
	float hair = smoothstep(0.15, 0.6, m);
	float near = smoothstep(0.15, 0.6, mg);
	// the grade along the fill: amber at the tips and the cold end, mid gold up the fill, hot gold under the front,
	// core white-gold only in the last core_w
	float df = level - g;
	float amber = max(1.0 - smoothstep(0.25, 0.62, g / max(level, 0.001)), 1.0 - smoothstep(tip_w, tip_w + 0.10, g));
	vec3 band = mix(c_mid.rgb, c_edge.rgb, amber);
	band = mix(band, mix(c_mid.rgb, c_core.rgb, 0.45), smoothstep(core_w + hot_w, core_w, df));
	float coreb = step(level - core_w - 0.02 * flare, g) * lit;
	band = mix(band, c_core.rgb, coreb);
	// Faded: cool toward edge, then bronze (dark: the light goes out)
	vec3 bronze = vec3(0.30, 0.20, 0.10);
	band = cool < 0.5 ? mix(band, c_edge.rgb, cool * 2.0) : mix(c_edge.rgb, bronze, (cool - 0.5) * 2.0);
	float warm = 1.0 - smoothstep(0.5, 1.0, cool);
	// the packet: a bump of its color running up the lit veins
	float pk = pkt_k * exp(-pow((g - pkt_g) / pkt_w, 2.0)) * step(g, max(level, pkt_g) + 0.01);
	// Drained: embers (bright dashes) scrolling down along g on the lit veins
	float em = drain * smoothstep(0.80, 0.97, fract(g * 9.0 + TIME * 1.6)) * step(g, level + 0.08);
	// Full: the shimmer, a soft band running down the veins
	float sh = shimmer_g < -0.5 ? 0.0 : exp(-pow((g - shimmer_g) / 0.05, 2.0)) * lit;
	// Spent: the band just spent flashes core, then goes dark
	float sp = spent_at(g);
	vec3 col = band;
	col = mix(col, c_core.rgb, 0.5 * flare * coreb);
	col = mix(col, pkt_c.rgb, clamp(pk, 0.0, 1.0));
	col = mix(col, c_spark.rgb, clamp(em, 0.0, 1.0));
	col = mix(col, c_core.rgb, sh * 0.7);
	col = mix(col, c_core.rgb, sp);
	// the vein covers the bronze by its strength: on screen a fully lit vein IS the band's color (no additive on top)
	float shown = max(max(lit, sp), clamp(pk + em, 0.0, 1.0));
	float va = s * hair * shown;
	// a wide ridge's edge outside the clamp: ember over the ridge's own highlight (a hot middle, a red edge)
	vec3 ember = c_edge.rgb * vec3(1.0, 0.62, 0.6);
	float ea = (s0 - s) * hair * lit * 0.55 * warm;
	// an unlit ridge: its highlight falls toward plain bronze (cold metal above the front, and at 0)
	float ca = s0 * hair * (1.0 - shown) * cold_k;
	// added light, all hair-bound: the bronze warmed round the lit veins (not on them), the underglow (ember, piled
	// under the front, feathered over the last 0.14 of g: a warmth rising, never a cut-out fill), the packet
	float front = smoothstep(0.45, 0.0, df);
	gl *= warm * (1.0 - s * shown) * near;
	float ug = under * hair * warm * on * smoothstep(level, level - 0.14, g) * (0.5 + 0.6 * front);
	vec3 addc = mix(ember, c_edge.rgb, clamp(gl * 2.0, 0.0, 1.0)) * gl * glow_k + ember * ug
		+ pkt_c.rgb * pk * 0.08 * hair + c_core.rgb * sp * 0.12 * gl;
	// Full: the four-point glint at the crown (small, 2-3 frames), and the warm rim on her hair's profile
	vec2 px = UV * canvas;
	vec2 d = abs(px - crown);
	float star = glint * (exp(-d.x / 1.2) * exp(-d.y / 9.0) + exp(-d.y / 1.2) * exp(-d.x / 9.0) + exp(-dot(d, d) / 10.0));
	addc += c_core.rgb * star * 1.2;
	if (rim > 0.0) {
		float a0 = texture(cold, UV).a;
		float an = min(min(texture(cold, UV + vec2(-2.0, 0.0) * tp).a, texture(cold, UV + vec2(0.0, -2.0) * tp).a),
			texture(cold, UV + vec2(-2.0, -2.0) * tp).a);
		addc += c_edge.rgb * rim * 0.35 * clamp(a0 - an, 0.0, 1.0) * a0 * near;
	}
	// premultiplied: the veins, the ember edges and the cold ridges cover the bronze; the warmth, underglow, glint and
	// rim add (alpha 0). Faded to bronze, the veins hold at 0.6 of their cover.
	float a = va * alpha * (warm + (1.0 - warm) * 0.6);
	float e = ea * alpha, c = ca * alpha;
	COLOR = vec4(col * a + ember * e + c_bronze.rgb * c + addc * alpha, a + e + c);
}
