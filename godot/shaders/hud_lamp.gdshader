// HUD A2 "Lamps Are Lit": her life lamp (LifeLamp.cs). One quad: the painted lamp (art/ui/lamp_life, cut by
// tools/uiforge/lamp_life_cut.py) with her life twice over: the oil in its font (blood-red, lit at its
// surface, deep at the foot, the empty glass above dark and see-through) and the flame on its wick (tall and
// steady when full, smaller at half, guttering blue at the root at 30% and under, out with a curl of smoke at
// 0). The flame is a meter of its own (round 2): its height, its glow in the chimney glass (white-gold full,
// half and orange at 55%, nearly dark guttering) and its light on the collar and the font's top: the lamp is lit
// by its flame only (the cold painting where its light doesn't reach). The empty glass reads as glass (a flame-lit
// rim on its upper curve, a faint smoky fill), the level is a pale line across the whole font, and the shield is
// an arc of silver-blue light round the font's rim. The pool of light on the ground is hud_lamp_pool's. The oil's motion is
// Vessel.Flow's (the same uniforms as hud_vessel: level, tilt, wave, film, heal, beat, frost, crack); the
// flame's state is LampState's (flame, gutter, out_t, flick). Nothing on the CPU redraws: uniforms and TIME.
shader_type canvas_item;
render_mode blend_premul_alpha;

uniform sampler2D lit : source_color, filter_linear_mipmap;
uniform sampler2D cold : source_color, filter_linear_mipmap;
uniform sampler2D mask : hint_default_black, filter_linear_mipmap;   // R oil, G font highlights, B glass, A 1 - inside/2
uniform sampler2D flame_tex : source_color, filter_linear_mipmap;     // light-keyed flame, foot at the bottom

// the canvas in 1080 px, and its places (lamp_geo.json)
uniform vec2 canvas = vec2(176.0, 196.0);
uniform vec2 wick = vec2(88.38, 85.35);
uniform float oil_top = 129.5;
uniform float oil_bot = 169.25;
uniform vec2 font_x = vec2(18.18, 158.18);
uniform float chim_top = 55.05;
uniform float flame_aspect = 3.16;
uniform float flame_full = 34.0;   // the flame's height at full life (1080 px)
uniform vec2 skip = vec2(0.0);     // an iron band across the glass (its rows): the level never rests behind it
uniform float halo_row = 46.2;     // the instrument's top line in the quad (nothing of the halo over it)

// Vessel.Flow
uniform float level : hint_range(0.0, 1.0) = 1.0;
uniform float tilt = 0.0;
uniform float wave = 0.0;
uniform float film_top = 0.0;
uniform float film_t = 1.0;
uniform float heal = 0.0;
uniform float heal_t = 0.0;
uniform float beat = 0.0;
uniform float frost = 0.0;
uniform float crack = 1.0;
uniform float crack_reach = 0.0;
// LampState
uniform float flame = 1.0;   // the flame's height, 0..1 of full
uniform float gutter = 0.0;  // 0 steady .. 1 guttering
uniform float out_t = -1.0;  // seconds since it went out (-1 lit)
uniform float flick = 1.0;   // its flicker now (1 steady)
uniform float glow = 1.0;    // its light now (LampState.Light: Glow(flame) x flicker; 0 out)
uniform int oil_off = 0;     // debug (--lamp-no-oil): the font drawn empty, so the flame's read is measured alone

uniform vec4 oil_hi : source_color = vec4(0.62, 0.05, 0.06, 1.0);
uniform vec4 oil_lo : source_color = vec4(0.09, 0.005, 0.01, 1.0);
uniform vec4 lip : source_color = vec4(1.0, 0.50, 0.40, 1.0);
uniform vec4 warm : source_color = vec4(1.0, 0.69, 0.38, 1.0);
uniform vec4 frost_col : source_color = vec4(0.66, 0.82, 1.0, 1.0);

float h21(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float vnoise(vec2 p)
{
	vec2 i = floor(p), f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(h21(i), h21(i + vec2(1, 0)), u.x), mix(h21(i + vec2(0, 1)), h21(i + vec2(1, 1)), u.x), u.y);
}
float fbm(vec2 p) { return 0.55 * vnoise(p) + 0.3 * vnoise(p * 2.1 + 3.7) + 0.15 * vnoise(p * 4.3 + 9.1); }
// the glass's whole inside (the iron over it included): its outer edge is the rim
float inside_at(vec2 uv) { return clamp(2.0 * (1.0 - texture(mask, uv).a), 0.0, 1.0); }
// her life's level as a row: up the glass from its foot, jumping the iron band (skip) if there is one
float level_row(float lv)
{
	float sh = skip.y - skip.x;
	float r = oil_bot - lv * (oil_bot - oil_top - sh);
	return r < skip.y ? r - sh : r;
}

void fragment()
{
	vec2 px = UV * canvas;
	vec4 L = texture(lit, UV), C = texture(cold, UV);
	vec3 m = texture(mask, UV).rgb;
	float t = TIME;
	float on = out_t < 0.0 ? 1.0 : 0.0;
	float g = clamp(glow, 0.0, 1.3) * on;     // the flame's light (steep: 1 full, ~0.46 at 55%, ~0.12 at 18%)
	float gs = clamp(g, 0.0, 1.0);
	// the flame's heart: half way up the flame
	vec2 heart = wick - vec2(0.0, flame_full * 0.42 * max(flame, 0.15));
	// its warmth: white-gold at full, orange as it sinks
	vec3 fire = mix(vec3(1.0, 0.46, 0.14), vec3(1.0, 0.80, 0.52), smoothstep(0.15, 0.9, gs));
	// ---- the lamp lit by its flame: the lit painting where the light reaches (the collar, the font's top), the
	// cold one beyond; plus the flame's warm light laid on the iron and glass close to it
	float dw = length((px - heart) * vec2(1.0, 0.7));
	float reach = exp(-dw / 38.0);
	vec3 col = mix(C.rgb, L.rgb, clamp(gs * (0.25 + 1.1 * reach), 0.0, 1.0));
	float a = C.a;
	// (the mask's glass is the chimney's and the font's: the chimney's is the glass over the wick)
	float chim = m.b * (1.0 - smoothstep(wick.y + 1.0, wick.y + 6.0, px.y));
	// the chimney's glass unlit is dark (a cold lamp at night), lit it fills with the flame
	col *= 1.0 - 0.5 * chim * (1.0 - gs);
	col += fire * a * g * 0.42 * exp(-dw / 22.0) * (1.0 - chim);

	// ---- the oil font
	float cxf = 0.5 * (font_x.x + font_x.y), half_w = 0.5 * (font_x.y - font_x.x);
	float u = (px.x - cxf) / half_w;   // -1..1 across the font
	float span = oil_bot - oil_top;
	float cyf = 0.5 * (oil_top + oil_bot);
	vec2 tx = vec2(1.0) / canvas;
	// the font glass's rim: the edge of its inside (up and down; to the sides only at its ends, not at the strap)
	float rim = 0.0;
	if (m.r > 0.01)
	{
		float up = inside_at(UV - vec2(0.0, 2.5) * tx), dn = inside_at(UV + vec2(0.0, 2.5) * tx);
		float sd = min(inside_at(UV - vec2(2.5, 0.0) * tx), inside_at(UV + vec2(2.5, 0.0) * tx));
		rim = max(max(1.0 - up, 1.0 - dn), (1.0 - sd) * smoothstep(0.55, 0.7, abs(u))) * m.r;
	}
	if (m.r > 0.01)
	{
		float lv = oil_off == 1 ? 0.0 : level;
		float surf = level_row(lv) + tilt * u * span * 0.9 + wave * span * sin(u * 3.1 + t * 7.0);
		float below = smoothstep(surf - 0.6, surf + 0.6, px.y) * step(0.002, lv);
		float depth = clamp((px.y - surf) / max(span, 1.0), 0.0, 1.0);
		// the oil: liquid lit by its own flame: deep red, darker at the glass's edges and its foot, warm on its top
		float sw = fbm(vec2(px.x * 0.07, px.y * 0.09 - t * 0.12) + vec2(t * 0.05, 0.0));
		vec3 oil = mix(oil_hi.rgb, oil_lo.rgb, pow(depth, 0.6)) * (0.75 + 0.5 * sw);
		oil *= 1.0 - 0.6 * smoothstep(0.45, 1.0, abs(u));
		float edge = max(1.0 - texture(mask, UV + vec2(0.0, 5.0) * tx).r,
			(1.0 - min(texture(mask, UV - vec2(6.0, 0.0) * tx).r, texture(mask, UV + vec2(6.0, 0.0) * tx).r)) * step(0.55, abs(u)));
		oil *= 1.0 - 0.45 * edge;
		// healing: fresh blood swirling up from the foot
		float hs = heal * smoothstep(0.0, 0.4, heal_t) * (1.0 - smoothstep(0.6, 1.4, heal_t));
		float rise = oil_bot - heal_t * span * 1.1;
		oil += vec3(0.9, 0.12, 0.10) * hs * exp(-abs(px.y - rise) / 9.0) * (0.5 + sw);
		// the heartbeat: the oil swells bright
		oil *= 1.0 + 0.85 * beat;
		// the flame's light on the oil's top, strongest under the wick
		float d = px.y - surf;
		oil += fire * vec3(1.0, 0.5, 0.32) * 0.16 * gs * exp(-max(d, 0.0) / 5.0) * (1.0 - 0.6 * abs(u));
		// the level (UI 15 fix 1): a bright line 1-2 px across the whole font, even at the glass's dark edges (behind
		// the cage's iron, as the oil is), a dark line under it so it reads on night grass and brown ground alike
		float lipk = exp(-d * d / 1.1);
		oil = mix(oil, vec3(1.0, 0.86, 0.74) * (1.05 + 0.15 * gs + 0.4 * beat), clamp(lipk * 1.15, 0.0, 1.0));
		oil *= 1.0 - 0.55 * exp(-pow((d - 2.8) / 1.2, 2.0));
		// the font glass's own light over the oil, toned down (the oil is liquid, not lacquer)
		oil += vec3(1.0, 0.86, 0.82) * m.g * 0.28;
		float fill = m.r * below;
		// the empty glass above: neutral smoky glass at every life (UI 15 fix 1: the painting's red under it read as
		// thin oil): the painting's light only, its colour dropped; the flame's warmth amber at its top only; its
		// highlight streak always there
		float emp = m.r * (1.0 - below);
		float lum = dot(col, vec3(0.299, 0.587, 0.114));
		float topw = smoothstep(cyf, oil_top - 2.0, px.y);
		vec3 smoke = vec3(0.15, 0.155, 0.165) + vec3(0.97, 0.99, 1.03) * lum * 0.5 + vec3(1.0, 0.66, 0.30) * 0.12 * gs * topw;
		col = mix(col, smoke, emp * 0.92);
		col += vec3(0.86, 0.89, 0.94) * m.g * emp * 0.34;
		// a line of light on the glass just over the oil (the surface's own glint through the glass)
		col += vec3(1.0, 0.88, 0.74) * 0.35 * exp(-pow((d + 1.6) / 0.8, 2.0)) * emp * step(0.002, lv);
		// the rim of the empty glass on its upper curve, lit by the flame (a cool glint where it is out)
		float top_curve = rim * smoothstep(cyf + 4.0, oil_top - 2.0, px.y);
		col += mix(vec3(0.35, 0.38, 0.42), fire * 1.1, gs) * top_curve * emp * (0.35 + 0.65 * gs);
		col = mix(col, oil, fill);
		a = mix(a, 1.0, max(fill, emp * 0.85));
		// the hurt film: blood clinging to the glass from where it stood, running down
		float ftop = level_row(mix(film_top, lv, film_t * film_t));
		float film = emp * step(ftop, px.y) * (1.0 - film_t) * (0.55 + 0.45 * vnoise(vec2(px.x * 0.4, px.y * 0.05 - t * 2.0)));
		col = mix(col, vec3(0.45, 0.02, 0.03), film * 0.7);
		a = max(a, film * 0.85);
	}
	// ---- the shield: an arc of silver-blue light round the font's rim, from its top round both sides as far as
	// the shield holds; broken, it shatters off and falls
	float fr = crack < 1.0 ? crack_reach : frost;
	if (fr > 0.001)
	{
		vec2 fp = px;
		float fade = 1.0;
		float rimS = rim;
		if (crack < 1.0)
		{
			float cell = h21(floor(px / vec2(9.0, 40.0)));
			fp.y -= (6.0 + 22.0 * cell) * crack * crack;
			fade = 1.0 - smoothstep(0.2, 1.0, crack);
			vec2 fu = fp / canvas;
			float up = inside_at(fu - vec2(0.0, 2.5) * tx), dn = inside_at(fu + vec2(0.0, 2.5) * tx);
			rimS = max(1.0 - up, 1.0 - dn) * texture(mask, fu).r;
		}
		vec2 rs = (fp - vec2(cxf, cyf)) / vec2(half_w, 0.5 * span + 3.0);
		float ang = abs(atan(rs.x, -rs.y)) / 3.14159265;   // 0 at the top, 1 at the foot
		float held = 1.0 - smoothstep(fr - 0.006, fr + 0.006, ang);
		float sh = clamp(rimS * 1.6, 0.0, 1.0) * held * fade;
		col = mix(col, frost_col.rgb, sh);
		a = max(a, sh);
	}

	// ---- the glow inside the chimney glass round the flame: the glass filled with its light
	float gd = length((px - heart) * vec2(1.0, 0.8));
	col += fire * chim * g * (0.55 * exp(-gd / 8.0) + 0.42 * exp(-gd / 22.0) + 0.10);
	vec4 outc = vec4(col * a, a);   // premultiplied
	// a soft halo out into the air round the chimney (light: added, no cover)
	// (none of it over the top line: 904 at 1080 for the squat lamp, 900 for the UI 15 shapes: halo_row)
	outc.rgb += fire * g * 0.30 * exp(-gd / 16.0) * (1.0 - a * 0.6) * smoothstep(halo_row + 0.3, halo_row + 7.8, px.y);

	// ---- the flame: the painted one, its height her life's, swaying; guttering, low, leaning and blue at its root
	if (on > 0.5 && flame > 0.01)
	{
		float fh = flame_full * flame * (1.0 - 0.18 * gutter * (0.5 + 0.5 * sin(t * 13.0 + 2.0 * sin(t * 5.3))));
		fh *= 0.94 + 0.06 * min(flick, 1.0);
		float fw = fh / flame_aspect * (1.0 + 0.35 * gutter) * mix(1.25, 1.0, flame);
		vec2 q = vec2((px.x - wick.x) / fw + 0.5, (px.y - (wick.y - fh)) / fh);
		float up = 1.0 - q.y;   // 0 at the foot, 1 at the tip
		float sway = (0.05 + 0.18 * gutter) * up * up * sin(t * (3.1 + 6.0 * gutter) + up * 3.0)
			+ 0.03 * up * sin(t * 11.0 + up * 9.0);
		q.x -= sway;
		if (q.x > 0.0 && q.x < 1.0 && q.y > 0.0 && q.y < 1.0)
		{
			vec4 f = texture(flame_tex, q);
			vec3 fl = f.rgb;
			// white-gold core, amber body; orange as it sinks
			float core = smoothstep(0.55, 0.95, dot(fl, vec3(0.33)));
			fl = mix(fl * fire * 1.3, vec3(1.0, 0.95, 0.82) * f.a, core * (0.4 + 0.6 * gs));
			// the gutter: the blue root climbs, the gold thins
			float root = smoothstep(0.55, 1.0, q.y);
			fl = mix(fl, fl * vec3(0.45, 0.6, 1.25) + vec3(0.0, 0.08, 0.35) * f.a, gutter * root);
			fl *= mix(1.0, 0.75, gutter * (1.0 - root));
			fl *= (0.95 + 0.25 * clamp(flick, 0.6, 1.4)) * (0.9 + 0.7 * gs);
			outc.rgb += fl;   // light: added
			outc.a = max(outc.a, f.a * 0.9);
		}
	}
	// ---- out: a curl of smoke from the wick, up the chimney and out of its top
	if (out_t >= 0.0 && out_t < 4.5)
	{
		float rise = wick.y - px.y;   // px above the wick
		float travel = 30.0 + out_t * 120.0;
		if (rise > -2.0 && rise < travel)
		{
			float k = rise / 60.0;
			float cx = wick.x + sin(rise * 0.075 - out_t * 2.2) * (2.0 + rise * 0.10) + (vnoise(vec2(rise * 0.05, out_t)) - 0.5) * rise * 0.12;
			float w = 1.6 + rise * 0.07;
			float dens = exp(-pow((px.x - cx) / w, 2.0)) * (0.55 + 0.45 * fbm(vec2(px.x * 0.15, rise * 0.08 - out_t * 1.5)));
			dens *= smoothstep(travel, travel - 25.0, rise) * (1.0 - smoothstep(1.5, 4.5, out_t)) * (1.0 - smoothstep(0.0, 90.0, rise));
			vec3 sc = vec3(0.62, 0.60, 0.58);
			float sa = clamp(dens * 0.7, 0.0, 0.8);
			outc = vec4(sc * sa + outc.rgb * (1.0 - sa), sa + outc.a * (1.0 - sa));
			// the wick's last ember
			float e = exp(-length(px - wick) / 1.6) * (1.0 - smoothstep(0.0, 1.2, out_t));
			outc.rgb += vec3(1.0, 0.35, 0.1) * e;
			outc.a = max(outc.a, e);
		}
	}
	COLOR = outc;
}
