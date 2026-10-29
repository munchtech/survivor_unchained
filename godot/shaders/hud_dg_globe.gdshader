// UI 23, HUD A (the keeper): the Flare, a dark glass globe in the keeper's bowl that fills with fire as it charges
// (DgGlobe). A port of the mock's ember_glass() (ui23 R6 mock7.py 289-423; every constant in
// art/ui/dg_keeper/hud_a_geo.json "glass"): smoky dark glass, a wall of painted flame (fire.png) risen to the charge's
// level of the span seen above the bowl's lip, two amber arms on the bronze bezel rising from the bowl's lips; READY (full): a
// white-gold heart in an orb of fire (fire_ready.png), the bezel lit, five tongues of flame over the top, round embers
// rising, a halo on the air. Then the bowl's front lip (keeper_lip.png, the keeper's rect) over the glass's foot, the
// globe's light on the air x (1 - 0.75 lip alpha), as the baker composed it (tools/uiforge/dg_keeper_check.py).
// Live: the flame wall shimmers and its crown wavers; full, a slow heat breath (3.3 s) and the embers climb; a press
// (burst: seconds since it) flashes it orange, its light bursting out, then the glass cools from dull red as it refills.
// One quad, premultiplied: the glass and the lip are opaque, the light outside added.
shader_type canvas_item;
render_mode blend_premul_alpha;

uniform sampler2D fire : source_color, filter_linear_mipmap, repeat_disable;
uniform sampler2D fire_ready : source_color, filter_linear_mipmap, repeat_disable;
uniform sampler2D lip : source_color, filter_linear, repeat_disable;
/// the quad's top left and size on the 1080 screen; the glass's middle and radius; the lip's line (the span's foot)
uniform vec2 q_at = vec2(1384.0, 816.0);
uniform vec2 q_size = vec2(237.0, 264.0);
uniform vec2 c = vec2(1502.56, 964.34);
uniform float r = 37.0;
uniform float lip_y = 987.28;
/// the keeper's rect (x, y, w, h): where keeper_lip.png lies
uniform vec4 krect = vec4(1254.0, 873.0, 341.0, 207.0);
uniform float charge = 0.0;
/// seconds since a press (< 0 none); the ready swell (1 on reaching full, easing to 0)
uniform float burst = -1.0;
uniform float ping = 0.0;
/// the keeper's fade (the lip fades with him) and his modulate (a callout's dimming)
uniform float fig_a = 1.0;
uniform vec4 lip_tint = vec4(1.0);
/// the fire textures' mip (8.7 texels a screen px: the mock's 4x supersampled bilinear is about a box of 8)
uniform float fire_lod = 3.1;
/// 0: the mock's still frame (a --hud-pin shine=, as her shine and sheen are held): no shimmer, breath or drift
uniform float live = 1.0;

const vec3 LUMW = vec3(0.2126, 0.7152, 0.0722);
// the mock's embers (numpy default_rng(17)): how far up, the spread (normal x 0.30), size, brightness; trails on 0,3,6,9
const vec4 EMB[11] = vec4[](vec4(0.8606, 0.1015, 1.1404, 0.7788), vec4(0.4853, -0.2432, 1.2655, 0.6554),
	vec4(0.3286, -0.6830, 0.8086, 0.9992), vec4(0.8491, 0.1772, 1.1473, 0.8633), vec4(0.2612, 0.0322, 1.0734, 0.8485),
	vec4(0.5067, -0.1837, 1.3204, 0.7904), vec4(0.2828, 0.6078, 1.3534, 0.7721), vec4(0.3132, -0.0706, 1.2122, 0.8301),
	vec4(0.3512, 0.0247, 1.0854, 0.8787), vec4(0.5880, -0.7306, 1.3861, 0.6560), vec4(0.2542, -0.3984, 1.1823, 0.8428));
const float SW[4] = float[](-2.079, -1.510, 2.349, 1.966);
const vec2 TONGUE[5] = vec2[](vec2(-0.55, 0.55), vec2(-0.25, 0.95), vec2(0.02, 1.35), vec2(0.28, 0.85), vec2(0.55, 0.5));

float sm(float a, float b, float x) { return smoothstep(a, b, x); }
float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p)
{
	vec2 i = floor(p), f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), f.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), f.x), f.y);
}
vec3 screen(vec3 a, vec3 b) { return 1.0 - (1.0 - a) * (1.0 - b); }
// a texel coordinate (the mock's map_coordinates: texel centres on integers, edges clamped) to a UV
vec2 tuv(vec2 t) { return (clamp(t, vec2(0.0), vec2(767.0)) + 0.5) / 768.0; }

void fragment()
{
	vec4 tint = COLOR;
	vec2 P = q_at + UV * q_size;      // screen px (continuous: pixel i spans [i, i + 1])
	float X = P.x, Y = P.y;
	float dx = X - c.x, dy = Y - c.y;
	float d = length(vec2(dx, dy));
	float t = TIME * live;
	bool ready = charge >= 0.999;
	float rd = ready ? 1.0 : 0.0;
	float pad = r * (ready ? 3.2 : 2.2);
	float breath = live * (0.5 + 0.5 * sin(t * 1.9)) + (1.0 - live) * 0.5;
	float flash = burst >= 0.0 ? exp(-burst * 4.5) : 0.0;
	float cooling = burst >= 0.0 ? sm(0.05, 0.3, burst) * (1.0 - sm(0.7, 2.2, burst)) : 0.0;
	float rb = r + 3.6;

	vec3 rgb = vec3(0.0);
	float a = 0.0;
	if (d < rb + 2.0)
	{
		float body = clamp(r - d + 0.5, 0.0, 1.0);
		float bez = clamp(rb - d + 0.5, 0.0, 1.0) * (1.0 - body);
		float radial = clamp(d / r, 0.0, 1.0);
		// the level: of the span seen above the bowl's lip; READY over the top
		float vis_bot = min(c.y + r, lip_y + 1.0);
		float lvl = ready ? c.y - r - 6.0 : vis_bot - charge * (vis_bot - (c.y - r));
		vec3 f;
		if (!ready)
		{
			// the wall of flame, its crown of tongues on the level: shimmering, the crown wavering
			float sh = live * ((noise(vec2(X * 0.13, t * 1.7)) - 0.5) * 2.2 + sin(t * 2.3 + X * 0.21) * 0.5);
			float drift = live * sin(t * 0.8 + Y * 0.07) * 0.8;
			vec2 ft = vec2((dx + drift) / 0.115 + 424.0, (Y - lvl + sh) / 0.115 + 330.0);
			f = textureLod(fire, tuv(ft), fire_lod).rgb * 1.12 * (1.0 + live * (0.07 * noise(vec2(X * 0.05, Y * 0.05 + t * 1.3)) - 0.035));
		}
		else
		{
			// the orb of fire, boiling slowly; a white-gold heart breathing through it, gold toward the rim
			float ang = 0.05 * sin(t * 0.7);
			vec2 o = mat2(vec2(cos(ang), sin(ang)), vec2(-sin(ang), cos(ang))) * vec2(dx, dy) * (1.0 + 0.025 * sin(t * 1.3));
			f = clamp(textureLod(fire_ready, tuv(vec2(383.5, 383.0) + o / r * 318.0), fire_lod).rgb * 1.25 + 0.04, 0.0, 1.0);
			float ftl = dot(f, LUMW);
			float heart = exp(-pow(d / (0.46 * r), 2.0)) * (0.70 + 0.30 * clamp(ftl * 1.4, 0.0, 1.0)) * (1.0 + 0.06 * (breath - 0.5) * live + 0.1 * ping);
			f = screen(f, vec3(1.0, 0.72, 0.30) * exp(-pow(d / (0.80 * r), 2.0)) * 0.55);
			f = screen(f, vec3(1.0, 0.95, 0.80) * heart * 0.95);
		}
		f = clamp(f * (0.68 + 0.32 * (1.0 - pow(radial, 4.0))), 0.0, 1.0);
		// the smoky glass, lit faintly by the fire below the level; after a press, its last embers cooling dull red
		vec3 glass = vec3(0.050, 0.036, 0.030) + vec3(0.30, 0.10, 0.02) * exp(-max(lvl - Y, 0.0) / 9.0) * 0.35 * step(0.02, charge);
		glass += vec3(0.55, 0.09, 0.02) * cooling * 0.6 * sm(0.0, 1.0, (Y - c.y) / r + 0.3) * sm(0.35, 0.8, noise(vec2(dx, dy) * 0.18 + vec2(0.0, t * 1.5)));
		vec3 col = screen(glass, f);
		col += vec3(1.0, 0.60, 0.20) * flash * 0.55;
		// the glass's optics: the inner rim darkening, a fresnel rim, the upper-left window, a small sharp glint
		col *= 0.72 + 0.28 * clamp(1.0 - pow(radial, 6.0), 0.0, 1.0);
		float fres = pow(clamp((radial - 0.82) / 0.18, 0.0, 1.0), 2.0);
		col += vec3(0.95, 0.80, 0.60) * fres * 0.20 * clamp(-(dx + dy) / r * 0.7 + 0.5, 0.0, 1.0);
		float hx = c.x - 0.42 * r, hy = c.y - 0.46 * r;
		float win = exp(-(pow((X - hx) / (0.30 * r), 2.0) + pow((Y - hy) / (0.17 * r), 2.0)));
		col = col * (1.0 - 0.35 * win) + vec3(1.0, 0.97, 0.92) * win * 0.35;
		col += exp(-(pow((X - (hx - 0.1 * r)) / 1.6, 2.0) + pow((Y - (hy - 0.02 * r)) / 1.2, 2.0))) * 0.55;
		// the bezel: polished bronze lit from the upper left; the charge an amber arc clockwise from 12; lit gold READY
		float tb = clamp((d - r) / (rb - r), 0.0, 1.0);
		float lit = clamp(0.55 - 0.315 * (dx + dy) / (d + 1e-3), 0.1, 1.0);
		vec3 bezc = vec3(0.36, 0.27, 0.16) * (0.45 + 1.1 * lit) + vec3(0.9, 0.75, 0.5) * exp(-pow((tb - 0.45) / 0.22, 2.0)) * lit * 0.35;
		// UI 23: two arms rise from the bowl's lips at +-130 deg (from 12, clockwise) and meet at 12 as it fills; the lit core 3.5 px
		float sa = atan(dx, -dy);
		float aa = abs(sa), a_hi = radians(130.0), a_lo = a_hi * (1.0 - clamp(charge, 0.0, 1.0));
		float arc = clamp((aa - a_lo) * (r + 1.8) + 0.5, 0.0, 1.0) * clamp((a_hi - aa) * (r + 1.8) + 0.5, 0.0, 1.0) * step(0.01, charge);
		arc = ready ? 1.0 : arc;
		vec3 amber = vec3(1.0, 0.62, 0.20) * (0.75 + 0.35 * (ready ? exp(-pow((tb - 0.5) / 0.3, 2.0)) : exp(-pow(abs(tb - 0.5) / 0.7, 4.0))));   // (UI 23: the lit core fills the 3.6 px ring, was a ~2 px peak)
		bezc = bezc * 0.42 * (1.0 - arc) + amber * 1.1 * arc;
		bezc = mix(bezc, bezc * 0.55 + vec3(1.0, 0.70, 0.30) * 0.65, rd);
		bezc += vec3(1.0, 0.6, 0.25) * flash * 0.6;
		float outline = clamp(rb + 1.0 - d + 0.5, 0.0, 1.0) * (1.0 - clamp(rb - d + 0.5, 0.0, 1.0));
		rgb = col * body + bezc * bez + vec3(0.03, 0.022, 0.016) * outline;
		a = clamp(body + bez + outline * 0.85, 0.0, 1.0);
	}

	// the light on the air: the halo; READY, tongues of flame over the top and embers rising
	vec3 add = vec3(0.0);
	if (d > r && d < 0.98 * pad)
	{
		float halo = exp(-(d - r) / (r * (ready ? 0.85 : 0.22))) * (1.0 - sm(0.72 * pad, 0.98 * pad, d));
		add += ready ? vec3(1.0, 0.62, 0.22) * halo * 0.95 * (1.0 + 0.12 * (breath - 0.5) * live + 0.3 * ping) : vec3(1.0, 0.50, 0.12) * halo * (0.10 + 0.2 * charge);
	}
	add += vec3(1.0, 0.62, 0.28) * flash * 1.5 * exp(-max(d - r, 0.0) / (r * (0.25 + 0.9 * max(burst, 0.0)))) * step(r, d) * (1.0 - sm(0.8 * pad, pad, d));
	vec3 orange = vec3(1.00, 0.42, 0.07), gold = vec3(1.00, 0.76, 0.32), white = vec3(1.00, 0.95, 0.84);
	if (ready && Y < c.y + 4.0 && abs(dx) < r * 1.6)
	{
		for (int i = 0; i < 5; i++)
		{
			float pos = TONGUE[i].x, hm = TONGUE[i].y * (1.0 + live * (0.10 * sin(t * (3.1 + 0.7 * float(i)) + float(i) * 2.3) + 0.06 * (breath - 0.5)));
			float base = c.y - sqrt(max(r * r - pow(pos * r, 2.0), 0.0)) + 4.0;
			float v = clamp((base - Y) / (30.0 * hm), -0.4, 1.4);
			float lean = (2.5 * sin(v * 2.4 + float(i) * 1.9 + t * 2.6) + 0.8 * live * sin(t * 4.7 + float(i))) * v;
			float wid = 6.0 * (0.7 + 0.5 * TONGUE[i].y) * pow(clamp(1.0 - v, 0.0, 1.0), 0.8);
			float q = (X - c.x - pos * r - lean) / max(wid, 0.4);
			float bodyf = exp(-q * q) * sm(-0.3, 0.05, v) * (1.0 - sm(0.5, 1.0, v));
			float coref = exp(-pow(q / 0.45, 2.0)) * sm(-0.2, 0.05, v) * (1.0 - sm(0.15, 0.55, v));
			vec3 colv = v < 0.45 ? mix(gold, orange, v / 0.45) : mix(orange, vec3(0.8, 0.2, 0.04), clamp((v - 0.45) / 0.55, 0.0, 1.0));
			add += colv * bodyf * 0.85 + white * coref * 0.6;
		}
		// embers: round hot specks drifting up and out of the flames, dimmer and redder as they rise; a few trail a
		// faint curl of their path
		for (int k = 0; k < 11; k++)
		{
			vec4 e = EMB[k];
			float sp = 0.22 + 0.12 * fract(e.y * 7.13 + e.z);
			float u = fract((e.x - 0.1) / 0.9 + t * sp);
			float up = 0.1 + 0.9 * u;
			float ex = c.x + e.y * r * (0.6 + 0.8 * up) + 1.5 * live * sin(t * 2.0 + float(k) * 1.7) * up;
			float ey = c.y - r - 8.0 - up * (r * 0.95 + 14.0);
			float sz = e.z * (1.15 - 0.40 * up);
			float br = e.w * (1.05 - 0.55 * up) * mix(1.0, sm(0.0, 0.08, u) * (1.0 - sm(0.85, 1.0, u)), live);
			vec2 dd = vec2(X - ex, Y - ey);
			float dd2 = dot(dd, dd);
			if (dd2 > 400.0) continue;
			vec3 hot = mix(vec3(1.0, 0.86, 0.55), vec3(1.0, 0.55, 0.18), up);
			add += hot * exp(-dd2 / (2.0 * pow(0.42 * sz, 2.0))) * 1.7 * br + vec3(1.0, 0.35, 0.06) * exp(-dd2 / (2.0 * pow(1.9 * sz, 2.0))) * 0.42 * br;
			if (k % 3 == 0)
			{
				float sw = SW[k / 3];
				for (int j = 1; j < 9; j++)
				{
					float tj = float(j) / 8.0;
					vec2 pj = vec2(X - (ex - sw * sin(tj * 2.2)), Y - (ey + tj * 7.5));
					add += hot * exp(-dot(pj, pj) / (2.0 * 0.38 * 0.38)) * 0.16 * br * (1.0 - tj);
				}
			}
		}
	}
	else if (!ready && charge > 0.02 && d < r - 2.0)
	{
		// idle: a couple of small sparks lifting off the crown inside the glass
		float vis_bot = min(c.y + r, lip_y + 1.0);
		float lvl = vis_bot - charge * (vis_bot - (c.y - r));
		for (int k = 0; k < 2; k++)
		{
			float ph = fract(t * 0.45 + float(k) * 0.5);
			float ex = c.x + (k == 0 ? -0.3315 : 0.2410) * r + sin(t * 1.7 + float(k) * 2.0) * 1.5;
			float ey = lvl - (k == 0 ? 7.89 : 10.66) - (ph - 0.5) * 10.0;
			float e = exp(-(pow((X - ex) / 0.6, 2.0) + pow((Y - ey) / 1.8, 2.0))) * sin(ph * PI);
			add += gold * e * 0.7 * 1.2;
		}
	}

	// the bowl's front lip over the glass's foot; the light on the air under it x (1 - 0.75 its alpha)
	vec2 luv = (P - krect.xy) / krect.zw;
	vec4 L = texture(lip, luv);
	L.a *= fig_a * step(0.0, luv.x) * step(luv.x, 1.0) * step(0.0, luv.y) * step(luv.y, 1.0);
	vec3 lp = L.rgb * lip_tint.rgb * L.a;
	rgb = lp + rgb * tint.rgb * tint.a * (1.0 - L.a);
	float A = L.a + a * tint.a * (1.0 - L.a);
	add *= tint.rgb * tint.a * (1.0 - 0.75 * L.a);
	COLOR = vec4(rgb + add, A);
}
