// HUD A2 "Lamps Are Lit": her life lamp (LifeLamp.cs). One quad: the painted lamp (art/ui/lamp_life, cut by
// tools/uiforge/lamp_life_cut.py) with her life twice over: the oil in its font (blood-red, lit at its
// surface, deep at the foot, the empty glass above dark and see-through) and the flame on its wick (tall and
// steady when full, smaller at half, guttering blue at the root at 30% and under, out with a curl of smoke at
// 0). The flame's light mixes the lamp from its cold painting to its lit one. The oil's motion is
// Vessel.Flow's (the same uniforms as hud_vessel: level, tilt, wave, film, heal, beat, frost, crack); the
// flame's state is LampState's (flame, gutter, out_t, flick). Nothing on the CPU redraws: uniforms and TIME.
shader_type canvas_item;
render_mode blend_premul_alpha;

uniform sampler2D lit : source_color, filter_linear_mipmap;
uniform sampler2D cold : source_color, filter_linear_mipmap;
uniform sampler2D mask : hint_default_black, filter_linear_mipmap;   // R oil, G font highlights, B glass
uniform sampler2D flame_tex : source_color, filter_linear_mipmap;     // light-keyed flame, foot at the bottom

// the canvas in 1080 px, and its places (lamp_geo.json)
uniform vec2 canvas = vec2(160.0, 340.0);
uniform vec2 wick = vec2(79.2, 195.8);
uniform float oil_top = 258.9;
uniform float oil_bot = 318.0;
uniform vec2 font_x = vec2(14.0, 146.0);
uniform float chim_top = 81.8;
uniform float flame_aspect = 3.16;
uniform float flame_full = 64.0;   // the flame's height at full life (1080 px)

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
uniform float flick = 1.0;   // its light now (the ground light's too)

uniform vec4 oil_hi : source_color = vec4(0.62, 0.05, 0.06, 1.0);
uniform vec4 oil_lo : source_color = vec4(0.09, 0.005, 0.01, 1.0);
uniform vec4 lip : source_color = vec4(1.0, 0.50, 0.40, 1.0);
uniform vec4 warm : source_color = vec4(1.0, 0.69, 0.38, 1.0);
uniform vec4 frost_col : source_color = vec4(0.80, 0.90, 1.0, 1.0);

float h21(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float vnoise(vec2 p)
{
	vec2 i = floor(p), f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(h21(i), h21(i + vec2(1, 0)), u.x), mix(h21(i + vec2(0, 1)), h21(i + vec2(1, 1)), u.x), u.y);
}
float fbm(vec2 p) { return 0.55 * vnoise(p) + 0.3 * vnoise(p * 2.1 + 3.7) + 0.15 * vnoise(p * 4.3 + 9.1); }

void fragment()
{
	vec2 px = UV * canvas;
	vec4 L = texture(lit, UV), C = texture(cold, UV);
	vec3 m = texture(mask, UV).rgb;
	float t = TIME;
	float on = out_t < 0.0 ? 1.0 : 0.0;
	float light = flame * flick * on;   // how much the flame lights the lamp
	// the flame's light on the lamp: the lit painting near the flame, falling off down the font
	float dw = length((px - wick + vec2(0.0, flame_full * 0.45 * flame)) * vec2(1.0, 0.8));
	float reach = exp(-dw / 70.0) * 0.6 + 0.4 * smoothstep(oil_top + 20.0, wick.y, px.y);
	vec3 col = mix(C.rgb, L.rgb, clamp(light * reach * 1.15, 0.0, 1.0));
	float a = C.a;

	// ---- the oil
	float cxf = 0.5 * (font_x.x + font_x.y), half_w = 0.5 * (font_x.y - font_x.x);
	float u = (px.x - cxf) / half_w;   // -1..1 across the font
	float span = oil_bot - oil_top;
	float surf = oil_bot - level * span + tilt * u * span * 0.9 + wave * span * sin(u * 3.1 + t * 7.0);
	// the empty glass: dark and see-through (the painting's own glass, dimmed)
	if (m.r > 0.01)
	{
		float below = smoothstep(surf - 0.6, surf + 0.6, px.y);
		float depth = clamp((px.y - surf) / max(span, 1.0), 0.0, 1.0);
		// the oil's body: deep at the foot, brighter under the surface, slow swirls, darker at the font's sides
		float sw = fbm(vec2(px.x * 0.07, px.y * 0.09 - t * 0.12) + vec2(t * 0.05, 0.0));
		vec3 oil = mix(oil_hi.rgb, oil_lo.rgb, pow(depth, 0.7)) * (0.7 + 0.6 * sw);
		oil *= 1.0 - 0.55 * smoothstep(0.55, 1.0, abs(u));
		// healing: fresh blood swirling up from the foot
		float hs = heal * smoothstep(0.0, 0.4, heal_t) * (1.0 - smoothstep(0.6, 1.4, heal_t));
		float rise = oil_bot - heal_t * span * 1.1;
		oil += vec3(0.9, 0.12, 0.10) * hs * exp(-abs(px.y - rise) / 9.0) * (0.5 + sw);
		// the heartbeat: the oil swells bright
		oil *= 1.0 + 0.85 * beat;
		// the flame's warmth on the oil's top
		oil += warm.rgb * 0.10 * light * exp(-(px.y - surf) / 10.0);
		// the meniscus: the surface seen from a little above: a lit lip, a dark line under it
		float d = px.y - surf;
		float lipk = exp(-d * d / 1.6) * (1.0 - 0.5 * abs(u));
		oil = mix(oil, lip.rgb * (0.8 + 0.5 * beat), clamp(lipk * 0.9, 0.0, 1.0));
		oil *= 1.0 - 0.45 * exp(-pow((d - 3.0) / 1.6, 2.0));
		// the font glass's own light over the oil, and the inner rim lit red
		oil += vec3(1.0, 0.86, 0.82) * m.g * 0.65;
		float fill = m.r * below;
		col = mix(col, oil, fill);
		a = mix(a, 1.0, fill);
		// the empty glass above: a little darker, its own highlights kept
		float emp = m.r * (1.0 - below);
		col = mix(col, col * 0.62 + vec3(0.02, 0.0, 0.0), emp * 0.6);
		// the hurt film: blood clinging to the glass from where it stood, running down
		float ftop = oil_bot - mix(film_top, level, film_t * film_t) * span;
		float film = emp * step(ftop, px.y) * (1.0 - film_t) * (0.55 + 0.45 * vnoise(vec2(px.x * 0.4, px.y * 0.05 - t * 2.0)));
		col = mix(col, vec3(0.45, 0.02, 0.03), film * 0.7);
		a = max(a, film * 0.85);
		// the shield: a pale frost in the font glass, from its top as far down as the shield holds; once broken,
		// it cracks off and falls
		float fr = crack < 1.0 ? crack_reach : frost;
		if (fr > 0.001)
		{
			vec2 fp = px;
			float fade = 1.0;
			if (crack < 1.0)
			{
				float cell = h21(floor(px / 7.0));
				fp.y -= (8.0 + 26.0 * cell) * crack * crack;
				fade = 1.0 - smoothstep(0.2, 1.0, crack);
			}
			float ice = fbm(fp * 0.22) * 0.6 + 0.4 * vnoise(fp * 0.9);
			float edge = oil_top + fr * span * 1.05;
			float fz = smoothstep(edge + 3.0, edge - 3.0 - 6.0 * ice, fp.y) * m.r * fade;
			col = mix(col, frost_col.rgb * (0.75 + 0.35 * ice), fz * 0.62);
			a = max(a, fz * 0.75);
		}
	}

	// ---- the warm glow inside the glass round the flame
	float gd = length((px - wick + vec2(0.0, flame_full * 0.42 * flame)) * vec2(1.0, 0.75));
	col += warm.rgb * m.b * light * (0.55 * exp(-gd / 16.0) + 0.18 * exp(-gd / 40.0));

	// ---- the flame: the painted one, its height her life's, swaying; guttering, low, leaning and blue at its root
	vec4 outc = vec4(col * a, a);   // premultiplied
	if (on > 0.5 && flame > 0.01)
	{
		float fh = flame_full * flame * (1.0 - 0.18 * gutter * (0.5 + 0.5 * sin(t * 13.0 + 2.0 * sin(t * 5.3))));
		fh *= 0.94 + 0.06 * flick;
		float fw = fh / flame_aspect * (1.0 + 0.35 * gutter);
		vec2 q = vec2((px.x - wick.x) / fw + 0.5, (px.y - (wick.y - fh)) / fh);
		float up = 1.0 - q.y;   // 0 at the foot, 1 at the tip
		float sway = (0.05 + 0.18 * gutter) * up * up * sin(t * (3.1 + 6.0 * gutter) + up * 3.0)
			+ 0.03 * up * sin(t * 11.0 + up * 9.0);
		q.x -= sway;
		if (q.x > 0.0 && q.x < 1.0 && q.y > 0.0 && q.y < 1.0)
		{
			vec4 f = texture(flame_tex, q);
			vec3 fl = f.rgb;
			// the gutter: the blue root climbs, the gold thins
			float root = smoothstep(0.55, 1.0, q.y);
			fl = mix(fl, fl * vec3(0.45, 0.6, 1.25) + vec3(0.0, 0.05, 0.25) * f.a, gutter * root);
			fl *= mix(1.0, 0.75, gutter * (1.0 - root));
			fl *= 0.9 + 0.15 * flick;
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
			dens *= smoothstep(travel, travel - 25.0, rise) * (1.0 - smoothstep(1.5, 4.5, out_t)) * (1.0 - smoothstep(0.0, 160.0, rise));
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
