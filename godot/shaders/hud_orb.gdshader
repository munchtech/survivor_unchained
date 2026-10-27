// UI 16 (27 Oct, the owner: "the typical orbs that these games have, but lets have what they are encased in show
// our themes"): her life as a classic orb (LifeLamp.cs with --life-orb link|ember|lamp). One quad: a glass sphere
// of blood drawn here (deep red, a flat level across the round glass with a bright meniscus, a slow swell under
// 2 px, the glass's speculars from the upper left, the shield a pale silver film over the glass, the hurt's blood
// running down the glass), under its painted casing (art/ui/lamp_life/<theme>, tools/uiforge/lamp_life_cut.py
// ORBS): the Broken Link (theme 0), the Held Dead's Warmth (1: embers glow through the cradle's grille, dimming
// as her life falls, never brighter than the blood) and Lamps Are Lit (2: the flame on its crown is a second
// meter, LampState's). The blood's motion is Vessel.Flow's uniforms (level, tilt, wave, film, heal, beat, frost,
// crack); nothing on the CPU redraws: uniforms and TIME.
shader_type canvas_item;
render_mode blend_premul_alpha;

uniform sampler2D lit : source_color, filter_linear_mipmap;
uniform sampler2D cold : source_color, filter_linear_mipmap;
uniform sampler2D mask : hint_default_black, filter_linear_mipmap;   // R embers, G the iron near the flame
uniform sampler2D flame_tex : source_color, filter_linear_mipmap;
uniform int theme = 0;

uniform vec2 canvas = vec2(160.0, 162.0);
uniform vec2 orb_c = vec2(80.0, 80.0);
uniform float orb_r = 48.0;     // the glass drawn (it runs on under the iron)
uniform float orb_vis = 46.0;   // the opening: the level runs from its foot to its top
uniform vec2 wick = vec2(80.0, 20.0);
uniform float flame_full = 15.0;
uniform float flame_aspect = 3.16;
uniform float halo_row = 0.0;

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
// LampState (theme 2)
uniform float flame = 1.0;
uniform float gutter = 0.0;
uniform float out_t = -1.0;
uniform float flick = 1.0;
uniform float glow = 1.0;

// the danger red's family (#e0282c): bright at the surface, near black in the depths
uniform vec4 blood_hi : source_color = vec4(0.80, 0.10, 0.11, 1.0);
uniform vec4 blood_lo : source_color = vec4(0.17, 0.004, 0.012, 1.0);

// (an integer hash: the sine hash gave a cell's two sides different values where the compiler fused its dot
// product differently, and the blood showed 1 px steps at the noise's cell edges)
float h21(vec2 p)
{
	uvec2 q = uvec2(ivec2(floor(p)) + 32768);
	uint n = q.x * 1597334677u ^ q.y * 3812015801u;
	n = (n ^ (n >> 16u)) * 2246822519u;
	return float(n >> 8u) / 16777215.0;
}
float vnoise(vec2 p)
{
	vec2 i = floor(p), f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(h21(i), h21(i + vec2(1, 0)), u.x), mix(h21(i + vec2(0, 1)), h21(i + vec2(1, 1)), u.x), u.y);
}
float fbm(vec2 p) { return 0.55 * vnoise(p) + 0.3 * vnoise(p * 2.1 + 3.7) + 0.15 * vnoise(p * 4.3 + 9.1); }
// her life as a row: up the opening from its foot
float level_row(float lv) { return orb_c.y + orb_vis - lv * 2.0 * orb_vis; }

void fragment()
{
	vec2 px = UV * canvas;
	float t = TIME;
	vec4 C = texture(cold, UV);
	vec3 m = texture(mask, UV).rgb;
	float a = C.a;
	vec3 col = C.rgb;
	float on = out_t < 0.0 ? 1.0 : 0.0;
	float g = theme == 2 ? clamp(glow, 0.0, 1.3) * on : 0.0;
	float gs = clamp(g, 0.0, 1.0);
	vec3 fire = mix(vec3(1.0, 0.46, 0.14), vec3(1.0, 0.80, 0.52), smoothstep(0.15, 0.9, gs));
	vec2 heart = wick - vec2(0.0, flame_full * 0.42 * max(flame, 0.15));
	// ---- the casing
	if (theme == 1)
	{
		// the embers through the grille: her warmth, dimming as she bleeds (a slow breath and a flicker), their
		// light kept under the blood's (at full ~0.75 of the painted glow, ~0.2 near empty)
		vec4 L = texture(lit, UV);
		float br = 0.6 + 0.4 * fbm(vec2(px.x * 0.12 + t * 0.35, px.y * 0.2 - t * 0.6));
		float ek = mix(0.20, 0.82, smoothstep(0.0, 1.0, level)) * br * (1.0 + 0.25 * beat);
		// (capped at a deep orange: the hottest coal never outshines the blood)
		float e = dot(L.rgb, vec3(0.5, 0.4, 0.1)) * ek;
		col = mix(col, vec3(1.0, 0.36, 0.07) * min(e, 0.62) + col * (1.0 - ek), m.r);
		// their light up the bowl's inside and the iron near them
		col += vec3(1.0, 0.36, 0.10) * 0.05 * ek * a * smoothstep(orb_c.y + orb_vis * 0.6, canvas.y - 8.0, px.y) * (1.0 - m.r);
		// and up the inner faces of the arch's legs (beside the glass's lower half)
		float leg = smoothstep(orb_c.y - orb_vis * 0.1, orb_c.y + orb_vis * 0.7, px.y) * (1.0 - smoothstep(orb_c.y + orb_vis * 0.75, orb_c.y + orb_vis * 0.9, px.y))
			* smoothstep(orb_vis * 1.25, orb_vis * 1.0, abs(px.x - orb_c.x)) * step(orb_vis * 0.97, abs(px.x - orb_c.x));
		col += vec3(1.0, 0.38, 0.10) * 0.13 * ek * a * leg;
	}
	else if (theme == 2)
	{
		// the flame's light on the crown and the ring's top (mask G: the iron near it)
		float dw = length((px - heart) * vec2(1.0, 0.7));
		col += fire * a * g * (0.22 * m.g + 0.12 * exp(-dw / 10.0));
	}

	// ---- the orb: a glass sphere (n its normal, view down -z), the blood level and flat across it
	vec2 q = (px - orb_c) / orb_r;
	float rr = length(q);
	float gin = 1.0 - smoothstep(1.0 - 1.0 / orb_r, 1.0, rr);
	vec3 gcol = vec3(0.0);
	float ga = 0.0;
	if (gin > 0.0)
	{
		float z = sqrt(max(1.0 - rr * rr, 0.0));
		float lv = level;
		float span = 2.0 * orb_vis;
		// the surface: the flow's tilt and wave, and a slow swell (under 2 px) that never stops
		float swell = 0.8 * sin(t * 1.3 + q.x * 2.2) + 0.45 * sin(t * 2.1 - q.x * 3.7);
		float surf = level_row(lv) + tilt * q.x * span * 0.45 + wave * span * 0.5 * sin(q.x * 3.1 + t * 7.0) + swell * step(0.002, lv) * step(lv, 0.998);
		float d = px.y - surf;
		float below = smoothstep(-0.6, 0.6, d) * step(0.002, lv);
		// (its depth mostly the glass's own, so a full orb is as rich as a half one: dark only low in the glass)
		float depth = mix(clamp(d / span, 0.0, 1.0), clamp((px.y - orb_c.y + 0.2 * orb_vis) / (1.2 * orb_vis), 0.0, 1.0), 0.7);
		// the blood: deep red, brighter just under its surface, near black at the glass's foot and its edges
		// (two broad octaves only: the fine one showed as 4 px blocks at 1:1)
		vec2 sp = vec2(px.x * 0.035 + t * 0.03, px.y * 0.045 - t * 0.07);
		float sw = 0.65 * vnoise(sp) + 0.35 * vnoise(sp * 1.9 + 3.7);
		vec3 blood = mix(blood_hi.rgb, blood_lo.rgb, pow(depth, 0.55)) * (0.80 + 0.40 * sw);
		blood *= mix(0.16, 1.0, pow(z, 1.1));
		// a glow held low in the middle of the sphere (the classic orb's depth)
		blood += blood_hi.rgb * 0.30 * exp(-dot(q - vec2(0.05, 0.28), q - vec2(0.05, 0.28)) / 0.22);
		// the light through it from the upper left: a warm glow low on the right (light gathered in the liquid)
		blood += vec3(0.45, 0.04, 0.03) * 0.30 * exp(-dot(q - vec2(0.38, 0.45), q - vec2(0.38, 0.45)) / 0.10) * below;
		// healing: fresh blood swirling up from the foot
		float hs = heal * smoothstep(0.0, 0.4, heal_t) * (1.0 - smoothstep(0.6, 1.4, heal_t));
		float rise = orb_c.y + orb_vis - heal_t * span * 1.1;
		blood += vec3(0.9, 0.12, 0.10) * hs * exp(-abs(px.y - rise) / 8.0) * (0.5 + sw);
		blood *= 1.0 + 0.85 * beat;
		// (never clipping: the brightest red stays at ~235)
		blood = min(blood, vec3(0.92, 0.30, 0.30));
		// the empty glass above: smoked glass (a little of the world through it), a fresnel rim round its edge,
		// and the blood's red light on the inner back wall just over the surface
		float vis_r = orb_vis / orb_r;
		vec3 empty = vec3(0.085, 0.080, 0.095) + vec3(0.16, 0.17, 0.20) * pow(1.0 - z, 2.0);
		// (the rim lit as the window is: full at the upper left, ~30% at the lower right)
		float rim_lit = mix(0.3, 1.0, 0.5 + 0.5 * dot(q / max(rr, 1e-3), normalize(vec2(-0.62, -0.78))));
		empty += vec3(0.34, 0.36, 0.42) * rim_lit * smoothstep(vis_r - 3.0 / orb_r, vis_r - 0.8 / orb_r, rr);
		empty += vec3(0.42, 0.035, 0.045) * exp(min(d, 0.0) / 7.0) * step(0.002, lv) * smoothstep(1.0, 0.6, rr);
		gcol = mix(empty, blood, below);
		// the surface seen a little from above: a lens 5 px deep across the glass, lit on the left, its front lip
		// bright, its back edge a dark line (reads on any ground)
		float hc = sqrt(max(orb_vis * orb_vis - pow(surf - orb_c.y, 2.0), 1.0));
		float lx = (px.x - orb_c.x) / hc;
		float ey = 2.5;
		float e2 = lx * lx + pow((px.y - (surf + 0.4)) / ey, 2.0);
		float lens = (1.0 - smoothstep(0.80, 1.0, e2)) * step(0.002, lv) * step(lv, 0.995);
		vec3 lcol = mix(vec3(0.98, 0.50, 0.46), vec3(0.42, 0.04, 0.05), smoothstep(-0.9, 0.9, lx)) * (1.0 + 0.35 * beat);
		float front = exp(-pow((e2 - 0.9) / 0.12, 2.0)) * step(surf + 0.4, px.y);
		float back = exp(-pow((e2 - 0.9) / 0.12, 2.0)) * step(px.y, surf + 0.4);
		lcol += vec3(1.0, 0.78, 0.70) * 0.55 * front * smoothstep(0.9, -0.3, lx);
		lcol *= 1.0 - 0.45 * back;
		gcol = mix(gcol, lcol, lens);
		below = max(below, lens);
		ga = gin * mix(0.90, 1.0, below);
		// the hurt: blood on the glass from where it stood, running down for a moment
		float emp = 1.0 - below;
		// (the orb's runs last ~0.2 s of the flow's 0.6)
		float ft = min(film_t * 3.0, 1.0);
		float ftop = level_row(mix(film_top, lv, ft * ft));
		float runs = smoothstep(0.5, 0.78, vnoise(vec2(px.x * 0.55, px.y * 0.035 - t * 2.4)));
		float film = emp * step(ftop, px.y) * (1.0 - ft) * runs;
		gcol = mix(gcol, vec3(0.34, 0.015, 0.025), film * 0.85);
		ga = max(ga, gin * film * 0.9);
		// the shield: a pale silver film over the glass, from its top round both sides as far as it holds
		// (stronger at the glass's edge, as a film on a sphere is); broken, it shatters off and falls
		float fr = crack < 1.0 ? crack_reach : frost;
		if (fr > 0.001)
		{
			vec2 fq = q;
			float fade = 1.0;
			if (crack < 1.0)
			{
				float cell = h21(floor(px / vec2(8.0, 8.0)));
				fq.y -= (0.1 + 0.4 * cell) * crack * crack;
				fade = (1.0 - smoothstep(0.2, 1.0, crack)) * step(0.35, cell);
			}
			// (a crisp 3 px silver arc on the glass's visible rim, frost falling off 9 px inward, bright tips
			// where it ends; the glass inside stays as it is)
			float ang = abs(atan(fq.x, -fq.y)) / 3.14159265;
			float held = 1.0 - smoothstep(fr - 0.006, fr + 0.006, ang);
			float inpx = (orb_vis - length(fq) * orb_r);   // px in from the visible rim
			float arc = smoothstep(-0.8, 0.4, inpx) * (1.0 - smoothstep(3.4, 4.4, inpx));
			float frostf = 0.38 * exp(-max(inpx - 3.5, 0.0) / 3.5) * step(0.0, inpx);
			// a fine frost: sparkles in the falloff, twinkling slowly
			float spk = step(0.93, h21(floor(px * 0.9))) * (0.5 + 0.5 * sin(t * 2.3 + 40.0 * h21(floor(px * 0.9) + 7.0)));
			frostf += 0.55 * spk * exp(-max(inpx - 2.0, 0.0) / 4.0) * step(0.0, inpx);
			float tip = exp(-pow((fr - ang) * 3.14159 * length(fq) * orb_r / 2.2, 2.0)) * step(-0.8, inpx) * (1.0 - smoothstep(4.0, 7.0, inpx)) * step(fr, 0.995);
			float sh = clamp((arc * 0.9 + frostf) * held + tip * 0.9, 0.0, 1.0) * fade;
			gcol = mix(gcol, vec3(0.70, 0.80, 0.94), sh);
		}
		// the glass's light from the upper left: a soft window, a hot point, a thin rim crescent; a faint
		// bounce low on the right
		// (the window: a curved band of light round the upper left, inside the rim; the hot point on it)
		// (the window: a curved band ~16 x 7 px by the rim at 10-11 o'clock, brightest in its middle; no point)
		vec2 dir = q / max(rr, 1e-3);
		float side = smoothstep(0.93, 0.995, dot(dir, normalize(vec2(-0.62, -0.78))));
		float soft = smoothstep(0.66, 0.74, rr) * (1.0 - smoothstep(0.84, 0.90, rr)) * side;
		float hot = soft * smoothstep(0.975, 0.998, dot(dir, normalize(vec2(-0.62, -0.78))));
		float cres = smoothstep(0.80, 0.96, rr) * smoothstep(0.25, 0.9, dot(q / max(rr, 1e-3), normalize(vec2(-0.75, -0.85)))) * (1.0 - smoothstep(0.96, 1.0, rr));
		float bounce = smoothstep(0.82, 0.96, rr) * smoothstep(0.4, 0.95, dot(q / max(rr, 1e-3), normalize(vec2(0.7, 0.8)))) * (1.0 - smoothstep(0.96, 1.0, rr));
		gcol += vec3(0.95, 0.93, 0.92) * (0.42 * soft + 0.30 * hot + 0.22 * cres) + vec3(0.9, 0.35, 0.3) * 0.16 * bounce;
		// (the embers under it light the glass's foot from below)
		if (theme == 1)
			gcol += vec3(1.0, 0.36, 0.08) * 0.22 * mix(0.2, 0.82, level) * smoothstep(0.55, 1.0, q.y) * (0.6 + 0.4 * rr);
		// (the lamp's flame lights the glass's top a little)
		gcol += fire * 0.12 * gs * smoothstep(0.2, -0.9, q.y) * (1.0 - z * 0.5);
	}
	// ---- the casing over the glass (premultiplied)
	vec4 outc = vec4(col * a + gcol * ga * (1.0 - a), a + ga * (1.0 - a));

	// ---- the flame (theme 2): its height her life's, swaying; guttering, low, leaning and blue at its root
	if (theme == 2)
	{
		float gd = length((px - heart) * vec2(1.0, 0.8));
		outc.rgb += fire * g * 0.30 * exp(-gd / 9.0) * (1.0 - outc.a * 0.6) * smoothstep(halo_row + 0.3, halo_row + 6.0, px.y);
		if (on > 0.5 && flame > 0.01)
		{
			float fh = flame_full * flame * (1.0 - 0.18 * gutter * (0.5 + 0.5 * sin(t * 13.0 + 2.0 * sin(t * 5.3))));
			fh *= 0.94 + 0.06 * min(flick, 1.0);
			float fw = fh / flame_aspect * (1.0 + 0.35 * gutter) * mix(1.25, 1.0, flame) * 1.25;
			vec2 fq = vec2((px.x - wick.x) / fw + 0.5, (px.y - (wick.y - fh)) / fh);
			float up = 1.0 - fq.y;
			fq.x -= (0.05 + 0.18 * gutter) * up * up * sin(t * (3.1 + 6.0 * gutter) + up * 3.0) + 0.03 * up * sin(t * 11.0 + up * 9.0);
			if (fq.x > 0.0 && fq.x < 1.0 && fq.y > 0.0 && fq.y < 1.0)
			{
				vec4 f = texture(flame_tex, fq);
				vec3 fl = f.rgb;
				float core = smoothstep(0.55, 0.95, dot(fl, vec3(0.33)));
				fl = mix(fl * fire * 1.3, vec3(1.0, 0.95, 0.82) * f.a, core * (0.4 + 0.6 * gs));
				float root = smoothstep(0.55, 1.0, fq.y);
				fl = mix(fl, fl * vec3(0.45, 0.6, 1.25) + vec3(0.0, 0.08, 0.35) * f.a, gutter * root);
				fl *= mix(1.0, 0.75, gutter * (1.0 - root));
				fl *= (0.95 + 0.25 * clamp(flick, 0.6, 1.4)) * (0.9 + 0.7 * gs);
				outc.rgb += fl;
				outc.a = max(outc.a, f.a * 0.9);
			}
		}
		if (out_t >= 0.0 && out_t < 4.5)
		{
			float rise = wick.y - px.y;
			float travel = 20.0 + out_t * 90.0;
			if (rise > -2.0 && rise < travel)
			{
				float cx = wick.x + sin(rise * 0.09 - out_t * 2.2) * (1.5 + rise * 0.10);
				float w = 1.4 + rise * 0.07;
				float dens = exp(-pow((px.x - cx) / w, 2.0)) * (0.55 + 0.45 * fbm(vec2(px.x * 0.15, rise * 0.08 - out_t * 1.5)));
				dens *= smoothstep(travel, travel - 18.0, rise) * (1.0 - smoothstep(1.5, 4.5, out_t)) * (1.0 - smoothstep(0.0, 40.0, rise)) * smoothstep(halo_row, halo_row + 4.0, px.y);
				float sa = clamp(dens * 0.7, 0.0, 0.8);
				outc = vec4(vec3(0.62, 0.60, 0.58) * sa + outc.rgb * (1.0 - sa), sa + outc.a * (1.0 - sa));
				float e = exp(-length(px - wick) / 1.4) * (1.0 - smoothstep(0.0, 1.2, out_t));
				outc.rgb += vec3(1.0, 0.35, 0.1) * e;
				outc.a = max(outc.a, e);
			}
		}
	}
	COLOR = outc;
}
