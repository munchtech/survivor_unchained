// M4 (docs/design/M4_HUD.md section 2): Resolve, heat rising through the Drowned Girl's hair. One quad over her figure
// (LifeLamp's own transform), light drawn over the bronze: unshaded, stepped bands, a soft outer glow only.
// veins (tools/uiforge/dg_resolve_veins.py, lamp_veins.png at the figure's 2x): R the hair's ridges (the veins), G the
// gauge g (1 the crown, 0 the tips: a geodesic along the locks), B the soft hair mask. A vein with g <= level is lit:
// mid gold; the last core_w of g under the front core white-gold; the tips edge amber. A faint warm underglow fills
// the hair below the front. ResolveVeins.cs drives every motion through the uniforms below, set only on change.
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
uniform float under = 0.10;                         // the warm underglow's strength below the front
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

float vein_at(vec2 uv) { return texture(veins, uv).r; }

void fragment()
{
	vec3 V = texture(veins, UV).rgb;
	float v = V.r, g = V.g, m = V.b;
	vec2 tp = 1.0 / tex_px;
	float lit = step(g, level) * step(0.001, level);
	// the bands, stepped: tips edge amber, the body mid gold, the last core_w under the front core
	vec3 band = g < tip_w ? c_edge.rgb : c_mid.rgb;
	float coreb = step(level - core_w - 0.02 * flare, g) * lit;
	band = mix(band, c_core.rgb, coreb);
	// Faded: cool toward edge, then bronze (dark: the light goes out)
	vec3 bronze = vec3(0.30, 0.20, 0.10);
	band = cool < 0.5 ? mix(band, c_edge.rgb, cool * 2.0) : mix(c_edge.rgb, bronze, (cool - 0.5) * 2.0);
	float glow_k = 1.0 - smoothstep(0.5, 1.0, cool);
	// the front's flare: the core brighter for a moment
	band += c_core.rgb * 0.35 * flare * coreb;
	// the packet: a bump of its color running up the lit veins
	float pk = pkt_k * exp(-pow((g - pkt_g) / pkt_w, 2.0)) * step(g, max(level, pkt_g) + 0.01);
	// Drained: embers (bright dashes) scrolling down along g on the lit veins
	float em = drain * smoothstep(0.80, 0.97, fract(g * 9.0 + TIME * 1.6)) * step(g, level + 0.08);
	// Full: the shimmer, a soft band running down the veins
	float sh = shimmer_g < -0.5 ? 0.0 : exp(-pow((g - shimmer_g) / 0.05, 2.0)) * lit;
	vec3 col = band;
	col = mix(col, pkt_c.rgb, clamp(pk, 0.0, 1.0));
	col = mix(col, c_spark.rgb, clamp(em, 0.0, 1.0));
	col = mix(col, c_core.rgb, sh * 0.7);
	float va = clamp(v * 1.15, 0.0, 1.0) * max(lit, clamp(pk + em, 0.0, 1.0));
	// Spent: the band just spent flashes core, then goes dark
	float sp = spent_k * step(spent.x, g) * step(g, spent.y) * step(0.001, spent.y - spent.x);
	col = mix(col, c_core.rgb, sp);
	va = max(va, clamp(v * 1.15, 0.0, 1.0) * sp);
	// the soft outer glow: the lit veins blurred (8 taps at 3 and 6 tex px), added only
	float gl = 0.0;
	for (int i = 0; i < 8; i++) {
		float an = float(i) * 0.785398;
		vec2 o = vec2(cos(an), sin(an)) * tp;
		gl += vein_at(UV + o * 3.0) + 0.6 * vein_at(UV + o * 6.0);
	}
	gl = gl / 12.8 * max(lit, sp) * glow_k;
	// the warm underglow in the hair below the front
	float ug = under * m * lit * glow_k * (0.6 + 0.4 * smoothstep(0.0, max(level, 0.01), g));
	vec3 addc = c_mid.rgb * (gl * 0.55 + sp * 0.3) + c_edge.rgb * ug + pkt_c.rgb * pk * 0.35 * m;
	// Full: the four-point glint at the crown, and the warm rim on her profile
	vec2 px = UV * canvas;
	vec2 d = abs(px - crown);
	float star = glint * (exp(-d.x / 1.6) * exp(-d.y / 14.0) + exp(-d.y / 1.6) * exp(-d.x / 14.0) + exp(-dot(d, d) / 18.0));
	addc += c_core.rgb * star * 1.4;
	if (rim > 0.0) {
		float a0 = texture(cold, UV).a;
		float an = min(min(texture(cold, UV + vec2(-2.0, 0.0) * tp).a, texture(cold, UV + vec2(0.0, -2.0) * tp).a),
			texture(cold, UV + vec2(-2.0, -2.0) * tp).a);
		addc += c_edge.rgb * rim * 0.45 * clamp(a0 - an, 0.0, 1.0) * a0;
	}
	// premultiplied: the veins cover the bronze (va); the glow, underglow, glint and rim add (alpha 0)
	float a = va * alpha * glow_k + va * alpha * (1.0 - glow_k) * 0.6;
	COLOR = vec4((col * a + addc * alpha), a);
}
