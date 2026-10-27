// UI 16, the Drowned Girl's life orb (--hud drowned, LifeLamp.cs), rebuilt (dg2) after the owner's "the orb is very
// bad": the liquid is the hero. One quad: her bronze figure (art/ui/lamp_life/drowned, tools/uiforge/dg_figure_cut.py)
// in two layers round a glass sphere of blood drawn here. Under the glass, all of her that the glass hides (her palm
// and thumb behind it); over it, only her fingers up its far side (mask R), so the lowest quarter of the glass is
// always clear. The blood is deep garnet with depth (dark to the rim, a glow low inside), a slow swirl through it and
// a bright thin meniscus that moves a little; the empty glass shows the screen behind it (the world, and her hand
// behind the glass) darkened and refracted (screen_tex: LifeLamp's BackBufferCopy over the orb only); a bright rim,
// a dark line of glass inside it and one crisp window upper left. The ward is a smooth frost band ~10 px inside the
// rim, its arc (clockwise from the top) how much ward is left. The fade (fig_a) dims her figure, never the glass or her hand and forearm
// (mask G). Vessel.Flow's uniforms drive the blood (level, tilt, wave, film, heal, beat, frost, crack); nothing on
// the CPU redraws.
shader_type canvas_item;
render_mode blend_premul_alpha;

uniform sampler2D cold : source_color, filter_linear_mipmap;      // her figure, straight alpha
uniform sampler2D mask : hint_default_black, filter_linear_mipmap; // R over the glass, G held at full in the fade
uniform sampler2D screen_tex : hint_screen_texture, filter_linear;
uniform vec2 canvas = vec2(434.0, 268.0);
uniform vec2 orb_c = vec2(70.0, 65.0);
uniform float orb_r = 60.0;
uniform float orb_vis = 59.4;
uniform float level_foot = -1.0;
uniform float fig_a = 1.0;

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

// garnet: near black in the depths, a deep wine red, a hot red-orange where light gathers low inside
uniform vec3 g_deep : source_color = vec3(0.105, 0.004, 0.016);
uniform vec3 g_mid : source_color = vec3(0.40, 0.022, 0.042);
uniform vec3 g_hot : source_color = vec3(0.98, 0.20, 0.12);

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
float fbm(vec2 p) { return 0.55 * vnoise(p) + 0.3 * vnoise(p * 2.07 + 3.7) + 0.15 * vnoise(p * 4.21 + 9.1); }
float level_row(float lv) { float f = level_foot < 0.0 ? orb_c.y + orb_vis : level_foot; return f - lv * (f - (orb_c.y - orb_vis)); }
// premultiplied over
vec4 over(vec4 src, vec4 dst) { return src + dst * (1.0 - src.a); }

void fragment()
{
	vec2 px = UV * canvas;
	float t = TIME;
	vec4 C = texture(cold, UV);
	vec2 M = texture(mask, UV).rg;
	float a = C.a * mix(fig_a, 1.0, M.g);
	// her figure in two layers: under the glass (all but her fingers over it) and over it
	vec4 back = vec4(C.rgb * a * (1.0 - M.r), a * (1.0 - M.r));
	vec4 front = vec4(C.rgb * a * M.r, a * M.r);
	vec4 outc = back;

	vec2 q = (px - orb_c) / orb_r;
	float rr = length(q);
	float aa = 1.0 / orb_r;   // a px, in the glass's radius
	float gin = 1.0 - smoothstep(1.0 - aa, 1.0 + 0.25 * aa, rr);
	if (gin > 0.0)
	{
		float z = sqrt(max(1.0 - rr * rr, 0.0));
		vec2 dir = q / max(rr, 1e-4);
		vec2 lightd = normalize(vec2(-0.62, -0.78));   // the window, upper left
		float lit = 0.5 + 0.5 * dot(dir, lightd);
		float lv = level;
		float span = 2.0 * orb_vis;
		// ---- the surface: the flow's tilt and wave and a slow swell (under 2 px) that never stops
		float swell = 0.8 * sin(t * 1.3 + q.x * 2.2) + 0.45 * sin(t * 2.1 - q.x * 3.7);
		bool part = lv > 0.002 && lv < 0.998;
		float surf = level_row(lv) + tilt * q.x * span * 0.45 + wave * span * 0.5 * sin(q.x * 3.1 + t * 7.0) + swell * (part ? 1.0 : 0.0);
		float d = px.y - surf;
		float below = smoothstep(-0.6, 0.6, d) * step(0.002, lv);

		// ---- the blood
		// (the swirl drawn on the sphere's inside: wrapped round it, turning slowly, warped through itself)
		vec2 sq = q / (0.55 + 0.45 * z);
		float ang = t * 0.07;
		vec2 p = mat2(vec2(cos(ang), sin(ang)), vec2(-sin(ang), cos(ang))) * sq * 2.3;
		vec2 w = vec2(fbm(p + vec2(0.0, t * 0.06)), fbm(p + vec2(5.2, 1.3) - vec2(t * 0.05, 0.0)));
		float sw = fbm(p * 1.25 + 2.4 * w + vec2(t * 0.025, -t * 0.035));
		// (thin darker veins where the warp folds)
		float vein = 1.0 - smoothstep(0.0, 0.07, abs(fbm(p * 1.6 + 1.8 * w + 7.0) - 0.5));
		// depth: the light's path through the ball (z), deeper low in it
		float thick = smoothstep(0.0, 0.95, z) * mix(1.0, 0.72, smoothstep(-0.2, 1.0, q.y));
		vec3 blood = mix(g_deep, g_mid, thick);
		blood *= mix(0.58, 1.30, smoothstep(0.30, 0.78, sw));
		blood *= 1.0 - 0.38 * vein * smoothstep(0.15, 0.6, z);
		// (dg4, the judge: the full red a touch darker in the rim band, the ball's edge turning away)
		blood *= 1.0 - 0.24 * smoothstep(0.76, 0.97, rr);
		// the glow held low inside, a little right of centre (the window's light gathered by the ball)
		vec2 gq = (q - vec2(0.16, 0.40)) * vec2(1.0, 1.25);
		float glow = exp(-dot(gq, gq) / 0.17);
		blood += g_hot * glow * (0.42 + 0.30 * sw) * (1.0 + 0.6 * beat);
		// the far wall's red edge low on the right (light bent round the inside of the glass)
		float kick = smoothstep(0.78, 0.97, rr) * smoothstep(0.1, 0.85, dot(dir, normalize(vec2(0.55, 0.84))));
		blood += vec3(0.70, 0.06, 0.05) * 0.55 * kick;
		// the light through the surface: a lighter band just under it, as the surface is lit from above
		blood += g_mid * 0.45 * exp(-max(d, 0.0) / 5.0) * (part ? 1.0 : 0.0);
		// healing: fresh blood swirling up from the foot
		float hs = heal * smoothstep(0.0, 0.4, heal_t) * (1.0 - smoothstep(0.6, 1.4, heal_t));
		float rise = orb_c.y + orb_vis - heal_t * span * 1.1;
		blood += vec3(0.9, 0.14, 0.10) * hs * exp(-abs(px.y - rise) / 8.0) * (0.5 + sw);
		blood *= 1.0 + 0.55 * beat;
		blood = min(blood, vec3(0.95, 0.34, 0.30));

		// ---- the empty glass: what is behind it (the world, her hand behind the glass), darkened and refracted
		// (pulled in toward the middle a little, more at the edge: the glass's lens; a small blur, the glass's thickness)
		vec2 spx = orb_c + (px - orb_c) * (0.80 + 0.10 * z);
		vec2 dpx = spx - px;
		vec2 uvpx = vec2(dFdx(SCREEN_UV.x) / max(dFdx(px.x), 1e-4), dFdy(SCREEN_UV.y) / max(dFdy(px.y), 1e-4));
		vec2 suv = SCREEN_UV + dpx * uvpx;
		vec3 world = 0.36 * texture(screen_tex, suv).rgb;
		world += 0.16 * texture(screen_tex, suv + vec2(1.5, 1.5) * uvpx).rgb;
		world += 0.16 * texture(screen_tex, suv + vec2(-1.5, 1.5) * uvpx).rgb;
		world += 0.16 * texture(screen_tex, suv + vec2(1.5, -1.5) * uvpx).rgb;
		world += 0.16 * texture(screen_tex, suv + vec2(-1.5, -1.5) * uvpx).rgb;
		// (dg3: nothing of her is behind the glass now, her palm is under it, so the world alone shows through)
		vec3 empty = world * vec3(0.52, 0.51, 0.56) + vec3(0.012, 0.010, 0.016);
		// the inside of the far wall: a little light round its edge, and the blood's red on it just over the surface
		empty += vec3(0.10, 0.11, 0.14) * pow(1.0 - z, 2.0);
		empty += vec3(0.40, 0.025, 0.040) * exp(min(d, 0.0) / 6.0) * step(0.002, lv) * smoothstep(1.0, 0.55, rr);
		vec3 gcol = mix(empty, blood, below);

		// ---- the meniscus: the surface seen a little from above, a lens ~3 px deep across the glass; its front lip a
		// bright thin line (a glint travels along it), its back edge a dark line
		float hc = sqrt(max(orb_vis * orb_vis - pow(surf - orb_c.y, 2.0), 1.0));
		float lx = (px.x - orb_c.x) / hc;
		float ey = 1.8;
		float e2 = lx * lx + pow((px.y - (surf + 0.3)) / ey, 2.0);
		float lens = (1.0 - smoothstep(0.82, 1.0, e2)) * (part ? 1.0 : 0.0);
		vec3 lcol = mix(vec3(0.72, 0.14, 0.13), vec3(0.30, 0.02, 0.035), smoothstep(-0.9, 0.9, lx)) * (1.0 + 0.3 * beat);
		float lip = exp(-pow((e2 - 0.92) / 0.10, 2.0)) * step(surf + 0.3, px.y);
		float rim_back = exp(-pow((e2 - 0.92) / 0.10, 2.0)) * step(px.y, surf + 0.3);
		float glint = 0.55 + 0.45 * sin(lx * 5.0 - t * 1.6);
		lcol += vec3(1.0, 0.70, 0.62) * 0.85 * lip * mix(1.0, 0.35, smoothstep(-0.8, 0.9, lx)) * glint;
		lcol *= 1.0 - 0.5 * rim_back;
		gcol = mix(gcol, lcol, lens);
		below = max(below, lens);

		// ---- the hurt: blood on the glass from where it stood, running down for a moment
		float emp = 1.0 - below;
		float ft = min(film_t * 3.0, 1.0);
		float ftop = level_row(mix(film_top, lv, ft * ft));
		float runs = smoothstep(0.5, 0.78, vnoise(vec2(px.x * 0.55, px.y * 0.035 - t * 2.4)));
		float film = emp * step(ftop, px.y) * (1.0 - ft) * runs;
		gcol = mix(gcol, vec3(0.30, 0.012, 0.024), film * 0.85);

		// ---- the glass's own wall: a dark line just inside the rim (its thickness seen edge on), heavier where no
		// light catches it (upper right, lower left)
		float lr = dot(dir, normalize(vec2(0.62, 0.78)));     // 1 toward the lower right
		float wall = smoothstep(0.90, 0.94, rr) * (1.0 - smoothstep(0.955, 0.985, rr));
		gcol *= 1.0 - wall * mix(0.50, 0.18, max(abs(lr), 0.0));
		// (the sky's soft reflection over its upper half)
		gcol += vec3(0.62, 0.66, 0.74) * 0.06 * smoothstep(0.45, 0.98, rr) * smoothstep(0.25, -0.85, q.y);

		// ---- the ward (dg4, the judge: "the crackle reads as cracked glass"): a smooth frost band ~10 px wide inside
		// the rim, grown clockwise from the top as far round as the ward holds (all the way round at a ward equal to her
		// life): milky ice brighter at the rim, a faint slow shimmer through it, a thin cold line at its inner edge; a sharp
		// start at the top and a bright leading tip with a glint; broken, it shatters off in flakes and falls
		float fr = crack < 1.0 ? crack_reach : frost;
		if (fr > 0.001)
		{
			vec2 fq = q;
			float fade = 1.0;
			if (crack < 1.0)
			{
				float cell = h21(floor(px / vec2(5.0, 5.0)) + 3.0);
				fq.y -= (0.06 + 0.32 * cell) * crack * crack;
				fq.x += (cell - 0.5) * 0.12 * crack;
				fade = (1.0 - smoothstep(0.15, 1.0, crack)) * step(0.30, cell);
			}
			float fl = length(fq);
			float ang = fract(atan(fq.x, -fq.y) / 6.2831853);   // 0 at the top, clockwise
			float arcpx = ang * 6.2831853 * orb_r;               // round the rim, px
			float dep = (1.0 - fl) * orb_r;                      // in from the rim, px
			float bwid = 10.0;
			float tb = clamp(dep / bwid, 0.0, 1.0);
			float inband = smoothstep(bwid + 0.6, bwid - 0.6, dep) * smoothstep(0.0, 0.9, dep);
			bool whole = fr >= 0.999;
			float reach = fr * 6.2831853 * orb_r;
			// (the start: a clean radial cut at the top, a px of edge; the end at the reach)
			float cover = smoothstep(reach + 0.6, reach - 0.6, arcpx) * (whole ? 1.0 : smoothstep(0.0, 1.0, arcpx));
			if (whole) cover = 1.0;
			float lit_f = mix(0.62, 1.0, 0.5 + 0.5 * dot(fq / max(fl, 1e-4), lightd));
			vec3 ice = vec3(0.62, 0.83, 1.0);
			float shim = fbm(vec2(arcpx * 0.045 - t * 0.12, dep * 0.10 + t * 0.05));
			float body = mix(0.86, 0.50, tb) * (0.88 + 0.24 * shim);
			vec3 frostc = ice * body * lit_f;
			float fa = clamp(mix(0.80, 0.58, tb) * inband * cover * fade, 0.0, 1.0);
			gcol = mix(gcol, frostc, fa);
			// (the inner edge: a thin cold line where the frost stops; the start cut's edge a touch brighter)
			gcol += ice * 0.30 * exp(-pow((dep - bwid) / 0.7, 2.0)) * cover * fade * lit_f * step(dep, bwid + 2.0);
			gcol += ice * 0.30 * (whole ? 0.0 : 1.0) * exp(-pow(arcpx / 1.0, 2.0)) * inband * fade;
			// (the leading tip: bright ice over its last ~5 px, a glint at its heart and a short glow ahead of it)
			float behind = reach - arcpx;
			float lead = (whole ? 0.0 : 1.0) * fade;
			float spark = 0.80 + 0.20 * sin(t * 4.0);
			float tip = exp(-pow(behind / 4.0, 2.0)) * step(-0.5, behind) * inband;
			gcol = mix(gcol, vec3(0.93, 0.98, 1.0), clamp(tip * lead * 0.92, 0.0, 1.0));
			float gl = exp(-(pow(behind - 1.2, 2.0) + pow(dep - 0.5 * bwid, 2.0)) / 9.0);
			gcol += vec3(1.0, 1.0, 1.0) * 1.3 * gl * lead * spark;
			gcol += vec3(0.45, 0.72, 1.0) * 0.30 * exp(-max(-behind, 0.0) / 3.0) * step(behind, 0.0) * smoothstep(bwid + 2.0, bwid - 2.0, dep) * lead;
		}

		// ---- the rim (dg3, the judge: "an even bright outline reads as a drawn circle"): uneven Fresnel. A dim cool
		// edge all round, a short bright cool glint at the upper left where the window's light catches the curve, and
		// a red crescent at the lower right, the blood's light bent out through the far wall (thick in its middle,
		// faint where the glass is empty)
		float e1 = smoothstep(1.0 - 2.0 * aa, 1.0 - 0.7 * aa, rr);
		float ul = dot(dir, lightd);
		float rglint = pow(max(ul, 0.0), 10.0);
		vec3 rimc = vec3(0.62, 0.68, 0.80) * (0.16 + 0.10 * smoothstep(-0.2, 0.9, -q.y)) * e1;
		rimc += vec3(0.86, 0.93, 1.0) * 0.95 * rglint * e1;
		float cres = smoothstep(0.30, 0.95, lr);
		float cth = mix(0.8, 3.6, cres) * aa;
		float cb = smoothstep(1.0 - cth - 1.2 * aa, 1.0 - cth * 0.35, rr) * (1.0 - smoothstep(1.0 - 0.6 * aa, 1.0, rr) * 0.3) * cres;
		vec3 credc = mix(vec3(0.20, 0.08, 0.09), vec3(1.0, 0.22, 0.10), below) * (1.0 + 0.35 * beat);
		gcol = gcol * (1.0 - 0.55 * e1 * (1.0 - rglint)) + rimc;
		gcol = mix(gcol, credc, clamp(cb * 0.85, 0.0, 1.0));
		gcol += vec3(1.0, 0.45, 0.30) * 0.35 * cb * cres * below;

		// ---- the window (dg3, the judge: "a hard white trapezoid that reads as a paper cup"): a soft curved
		// reflection upper left, ~75% white at its heart, curved round the glass (a patch in the ball's polar
		// coordinates), soft all round and fading toward the rim; a faint mullion so it reads as a window
		float th = atan(q.y, q.x);
		float th0 = atan(-0.76, -0.65);
		float dth = th - th0;
		dth = dth - 6.2831853 * floor((dth + 3.14159265) / 6.2831853);
		float wa = abs(dth) / 0.36;                        // across: 1 at its ends (~26 px across)
		float wrr = (rr - 0.60) / 0.14;                    // in and out: -1 inner edge, +1 outer
		float wshape = (1.0 - smoothstep(0.55, 1.0, wa)) * (1.0 - smoothstep(0.55, 1.05, -wrr)) * (1.0 - smoothstep(-0.2, 1.25, wrr));
		float mull = 1.0 - 0.22 * exp(-pow(dth * rr * orb_r / 1.1, 2.0));
		float win = 0.75 * wshape * mull;
		gcol = mix(gcol, vec3(1.0, 0.975, 0.94), clamp(win, 0.0, 1.0));
		// (a small soft second light low on the right)
		vec2 s2 = (q - vec2(0.44, 0.58)) * vec2(1.0, 1.6);
		gcol += vec3(1.0, 0.80, 0.74) * 0.16 * exp(-dot(s2, s2) / 0.006);

		outc = over(vec4(gcol * gin, gin), outc);
	}
	COLOR = over(front, outc);
}
