// The HUD's vessels (src/Ui/Instrument.cs), HUD v2 (docs/design/HUD_V2.md section 3).
// mode 0, her life: blood in thick old glass, lit as a sphere. Near-black crimson in its depth, lighter
// toward its surface, slow dark veins turning in it; the light that entered at the upper left leaves at the
// lower right as a rim of the brightest red on the HUD. Its surface, seen from a little above, is a thin
// ellipse lighter than the body with a 1 px meniscus along its far edge; it swells at rest and sloshes on a
// change. Hurt, the glass keeps a film of blood above the new level that runs down and clears; low, the
// blood brightens on the heartbeat; healing, fresh blood swirls up from the foot; shielded, frost rimes the
// glass from the top and cracks away when the shield breaks; empty, dark glass with a dried film.
// mode 1, the draught: the same glass, small, its red a shade warmer.
// mode 2, the art in hand: the first HUD's look, until its gold mode is made.
// The glass's own light (its window, hot spot, rim and the cuff's shadow) is rendered art laid over this
// (hud/glass.png, hud/glass_small.png, premultiplied), so none of it is drawn here. Everything that moves
// is a uniform the vessel sets (or TIME): nothing on the CPU redraws.
shader_type canvas_item;

uniform int mode = 0;
uniform float level : hint_range(0.0, 1.0) = 1.0;
// The slosh: the surface's tilt and a standing wave on it, kicked by a change and damped by the vessel.
uniform float tilt = 0.0;
uniform float wave = 0.0;
// The hurt film: the level it began at, and how far it has run (0 the blow, 1 cleared).
uniform float film_top = 0.0;
uniform float film_t = 1.0;
// Healing: how strongly fresh blood rises (0..1), and for how long it has (seconds).
uniform float heal = 0.0;
uniform float heal_t = 0.0;
// The heartbeat, 0..1 (1 on the beat).
uniform float beat = 0.0;
// The frost: the shield's reach round the glass from the top (0..1); its cracking away (0 the break,
// 1 gone) from the reach it had.
uniform float frost = 0.0;
uniform float crack = 1.0;
uniform float crack_reach = 0.0;
// Empty: a dried film (her life; the draught's empty glass is only dark).
uniform float dry_film = 1.0;
uniform float seed = 0.0;
// mode 2 (the art):
uniform float trail : hint_range(0.0, 1.0) = 1.0;
uniform float shield : hint_range(0.0, 1.0) = 0.0;
uniform float pulse : hint_range(0.0, 1.0) = 0.0;
uniform float slosh = 0.0;
uniform float glow = 0.0;
uniform vec4 shallow : source_color = vec4(0.84, 0.16, 0.17, 1.0);
uniform vec4 deep : source_color = vec4(0.30, 0.02, 0.04, 1.0);
uniform vec4 empty : source_color = vec4(0.07, 0.035, 0.04, 1.0);
uniform vec4 trail_col : source_color = vec4(1.0, 0.62, 0.52, 1.0);
uniform vec4 shield_col : source_color = vec4(0.62, 0.84, 1.0, 1.0);
uniform float own_light = 1.0;
// HUD A2 round 2: the draught as a small dark vial (one red in the corner: the life lamp's): its liquid dimmed and
// drained of colour (1 and 0 leave it as it was)
uniform float liq_dim = 1.0;
uniform float liq_desat = 0.0;

// The cavity inside the thick glass (the rendered rim's bright inner line sits on it).
const float RI = 0.94;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
vec2 hash2(vec2 p) { return fract(sin(vec2(dot(p, vec2(127.1, 311.7)), dot(p, vec2(269.5, 183.3)))) * 43758.5453); }

float noise(vec2 p)
{
	vec2 i = floor(p), f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), u.x), mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), u.x), u.y);
}

float fbm(vec2 p)
{
	float v = 0.0, a = 0.5;
	for (int k = 0; k < 4; k++) { v += a * noise(p); p = p * 2.07 + vec2(1.7, 9.2); a *= 0.5; }
	return v;
}

// The nearest cell's middle (in x's space) and how far x lies inside its border.
void cells(vec2 x, out vec2 mid, out float border)
{
	vec2 n = floor(x), f = fract(x);
	vec2 mg = vec2(0.0), mr = vec2(0.0);
	float md = 8.0;
	for (int j = -1; j <= 1; j++)
	{
		for (int i = -1; i <= 1; i++)
		{
			vec2 g = vec2(float(i), float(j));
			vec2 r = g + hash2(n + g) - f;
			float d = dot(r, r);
			if (d < md) { md = d; mr = r; mg = g; }
		}
	}
	md = 8.0;
	for (int j = -2; j <= 2; j++)
	{
		for (int i = -2; i <= 2; i++)
		{
			vec2 g = mg + vec2(float(i), float(j));
			vec2 r = g + hash2(n + g) - f;
			if (dot(mr - r, mr - r) > 0.00001) md = min(md, dot(0.5 * (mr + r), normalize(r - mr)));
		}
	}
	mid = n + mg + hash2(n + mg);
	border = md;
}

// HUD v2 r2 (the glass rebuilt from renders, tools/uiforge/blender_glass.py): the view through the glass at
// `frames` levels (liquid, an atlas; frame 0 the empty glass, the last full), each frame's surface per column
// (lines), and the outer surface's light (front, rgb added in linear light; alpha the cuff's shadow). The two
// frames either side of the level are slid onto one surface (theirs interpolated, plus the slosh) and blended;
// then the film, the heal, the beat and the frost go on in linear light, and the front over all. Opaque.
// (The overlays default black, so one unbound adds nothing; the liquid unbound reads white: a stale build.)
uniform sampler2D liquid : filter_linear_mipmap;
uniform sampler2D front : hint_default_black, filter_linear_mipmap;
uniform sampler2D lines : filter_nearest;
uniform sampler2D film_map : hint_default_black, filter_linear_mipmap;
uniform sampler2D frost_map : hint_default_black, filter_linear_mipmap;
uniform int frames = 17;
uniform int cols = 5;
uniform float canvas = 124.0;
uniform float cav_r = 56.5;
uniform float glass_r = 60.0;

vec3 lin(vec3 c) { return mix(c / 12.92, pow((c + 0.055) / 1.055, vec3(2.4)), step(0.04045, c)); }
vec3 enc(vec3 c) { c = clamp(c, 0.0, 1.0); return mix(c * 12.92, 1.055 * pow(c, vec3(1.0 / 2.4)) - 0.055, step(0.0031308, c)); }

// frame k's far surface edge at file column cx, in shown px from the frame's top
float line_at(int k, float cx)
{
	int w = int(canvas * 2.0);
	float c = clamp(cx - 0.5, 0.0, float(w - 1));
	int c0 = int(floor(c)), c1 = min(c0 + 1, w - 1);
	vec4 a = texelFetch(lines, ivec2(c0, k), 0), b = texelFetch(lines, ivec2(c1, k), 0);
	float ya = a.r * 255.0 + a.g * 255.0 / 256.0, yb = b.r * 255.0 + b.g * 255.0 / 256.0;
	return mix(ya, yb, fract(c)) * 0.5;
}

float line_lv(float lv, float cx)
{
	float fi = clamp(lv, 0.0, 1.0) * float(frames - 1);
	int k0 = int(floor(fi)), k1 = min(k0 + 1, frames - 1);
	return mix(line_at(k0, cx), line_at(k1, cx), fi - float(k0));
}

vec3 frame_at(int k, vec2 at)
{
	vec2 rows = vec2(float(cols), ceil(float(frames) / float(cols)));
	vec2 o = vec2(float(k % cols), float(k / cols));
	vec2 uv = (o + clamp(at / canvas, vec2(0.002), vec2(0.998))) / rows;
	return lin(texture(liquid, uv).rgb);
}

vec3 blood(vec2 p, float r, float px, float t)
{
	bool small = mode == 1;
	float R = glass_r;
	vec2 at = (p * (canvas * 0.5) / 1.0) + vec2(canvas * 0.5);    // shown px in the frame
	vec2 q = at - vec2(canvas * 0.5);
	float rr = length(q);
	float lv = clamp(level, 0.0, 1.0);
	float fi = lv * float(frames - 1);
	int k0 = int(floor(fi)), k1 = min(k0 + 1, frames - 1);
	float f = fi - float(k0);
	float cx = at.x * 2.0;
	float y0 = line_at(k0, cx), y1 = line_at(k1, cx);
	float live = smoothstep(0.0, 0.03, lv) * smoothstep(1.0, 0.97, lv);
	float xr = q.x / R;
	float swell = small ? 0.0 : (0.014 * sin(xr * 3.1 + t * 1.25) + 0.007 * sin(xr * 7.3 - t * 2.05 + 1.7));
	float target = mix(y0, y1, f) + (swell + tilt * xr + wave * sin(xr * 5.0 + t * 9.0)) * R * live;
	float w = exp(-pow((at.y - target) / 9.0, 2.0)) * (1.0 - smoothstep(cav_r - 2.0, cav_r + 1.5, rr));
	vec3 c0 = frame_at(k0, vec2(at.x, at.y - (target - y0) * w));
	vec3 c1 = frame_at(k1, vec2(at.x, at.y - (target - y1) * w));
	vec3 col = mix(c0, c1, f);
	bool inside = rr < cav_r - 0.4;
	float below = smoothstep(target - 0.6, target + 0.6, at.y) * live + step(0.999, lv);
	vec4 fm = texture(film_map, at / canvas);

	// Hurt: above the new level, the film the blood left on the glass runs down and clears (film_map: when
	// each place clears and how thick it is, between where the blood stood and where it stands).
	if (!small && film_t < 1.0 && film_top > lv + 0.002 && inside)
	{
		float yt = line_lv(film_top, cx);
		float s = (at.y - yt) / max(target - yt, 1.0);
		if (s >= 0.0 && s <= 1.0)
		{
			vec4 m = texture(film_map, vec2(at.x / canvas, s));
			float on = smoothstep(film_t - 0.035, film_t + 0.035, m.r) * (1.0 - below);
			vec3 fc = vec3(0.20, 0.006, 0.010) * (0.55 + 0.9 * m.g) + vec3(0.30, 0.02, 0.02) * m.g * smoothstep(-0.6, 0.8, (q.x + q.y) / R) * 0.5;
			col = mix(col, fc, clamp(on * (0.50 + 0.45 * m.g), 0.0, 0.95));
		}
	}
	// Empty: the dried film.
	float dry = (1.0 - smoothstep(0.0, 0.02, lv)) * dry_film * (small ? 0.0 : 1.0);
	col = mix(col, vec3(0.055, 0.008, 0.006), fm.b * dry * 0.85);
	// Healing: lighter, fresh blood swirling up from the foot.
	if (heal > 0.001)
	{
		vec2 hq = q / R;
		float rise = heal_t * 0.85;
		float hn = fbm(vec2(hq.x * 2.6 + 0.45 * sin(hq.y * 4.0 + heal_t * 1.9), hq.y * 2.1 + heal_t * 1.5) + seed * 3.0);
		float risen = smoothstep(0.94 - rise - 0.30, 0.94 - rise + 0.05, hq.y);
		float plume = smoothstep(0.40, 0.58, hn) * risen * below * exp(-pow(hq.x / (0.35 + 0.6 * clamp(rise, 0.0, 1.0)), 2.0));
		col = mix(col, vec3(1.0, 0.13, 0.09), clamp(plume * heal * 1.2, 0.0, 1.0));
	}
	// Low: on the beat a red bloom in the blood's lower third and on the glass's inner bevel.
	float lower = smoothstep(-0.05, 0.55, q.y / R);
	col *= 1.0 + beat * (0.55 * lower * below + 0.15 * below);
	col += vec3(0.75, 0.05, 0.04) * beat * 0.35 * smoothstep(R - 6.0, R - 1.5, rr);
	// Shielded: frost grown in from the rim, round from the top as far as the shield holds; cracked away once.
	float reach = crack < 1.0 ? crack_reach : frost;
	if (reach > 0.001)
	{
		vec2 fa = at;
		float fade = 1.0;
		if (crack < 1.0)
		{
			vec4 id = texture(frost_map, at / canvas);
			float hsh = fract(id.b * 91.7);
			fa = at - vec2((hsh - 0.5) * 10.0, 3.0 + 20.0 * hsh) * crack - vec2(0.0, 26.0 * crack * crack);
			fade = 1.0 - smoothstep(0.25, 1.0, crack);
		}
		vec4 fr = texture(frost_map, fa / canvas);
		float held = 1.0 - smoothstep(reach - 0.02, reach + 0.02, fr.g);
		float a = fr.a * held * fade;
		vec3 ice = lin(mix(vec3(0.604, 0.831, 1.0), vec3(0.96, 0.99, 1.0), fr.r * 0.7)) * (0.35 + 0.75 * fr.r);
		col = mix(col, ice, clamp(a * 0.85, 0.0, 0.9));
		col += lin(vec3(0.604, 0.831, 1.0)) * 0.025 * reach * fade;
	}
	col = mix(col, vec3(dot(col, vec3(0.21, 0.72, 0.07))), liq_desat) * liq_dim;
	vec4 fl = texture(front, at / canvas);
	col += lin(fl.rgb);
	return enc(col);
}

// mode 2: the first HUD's vessel (the art), kept as it was until its gold mode is made.
vec3 first(vec2 p, float r, float aa, float t)
{
	float z = sqrt(max(0.0, 1.0 - r * r));
	vec3 n = vec3(p.x, -p.y, z);
	float s0 = 1.0 - 2.0 * level;
	float amp = (0.010 + 0.05 * slosh) * smoothstep(0.0, 0.04, level) * smoothstep(1.0, 0.96, level);
	float s = s0 + amp * (sin(p.x * 4.0 + t * 1.7) + 0.5 * sin(p.x * 9.0 - t * 2.9 + 1.3));
	vec3 col = empty.rgb * (0.55 + 0.45 * z);
	float ts = 1.0 - 2.0 * trail;
	float in_trail = smoothstep(ts - aa, ts + aa, p.y) * (1.0 - smoothstep(s - aa, s + aa, p.y));
	col = mix(col, trail_col.rgb * (0.45 + 0.4 * z), in_trail * 0.5);
	float below = smoothstep(s - aa, s + aa, p.y);
	if (below > 0.0)
	{
		float depth = clamp((p.y - s) / max(0.08, 1.0 - s), 0.0, 1.0);
		vec3 liq = mix(shallow.rgb, deep.rgb, pow(depth, 0.75));
		float a = t * 0.21;
		vec2 q = mat2(vec2(cos(a), sin(a)), vec2(-sin(a), cos(a))) * (p * 2.1);
		float sw = fbm(q + vec2(t * 0.05, -t * 0.08));
		liq *= 0.80 + 0.40 * sw;
		liq *= 0.55 + 0.5 * clamp(dot(n, normalize(vec3(-0.45, 0.55, 0.7))), 0.0, 1.0);
		liq += shallow.rgb * glow * (0.30 + 0.30 * sw);
		float m = exp(-pow((p.y - s) / 0.028, 2.0)) * step(0.004, level) * step(level, 0.996);
		liq += mix(shallow.rgb, vec3(1.0), 0.5) * m * 0.6;
		col = mix(col, liq, below);
	}
	float ang = atan(p.x, -p.y) / 6.2831853;
	ang = ang < 0.0 ? ang + 1.0 : ang;
	float band = smoothstep(0.78, 0.86, r) * (1.0 - smoothstep(0.93, 0.98, r));
	float held = 1.0 - smoothstep(shield - 0.004, shield + 0.004, ang);
	col = mix(col, shield_col.rgb, band * held * 0.9 * step(0.001, shield));
	col += shield_col.rgb * 0.06 * shield;
	col = mix(col, vec3(1.0, 0.26, 0.2), pulse * 0.24);
	float hl = 1.0 - smoothstep(0.0, 0.42, length((p - vec2(-0.34, -0.48)) * vec2(1.0, 1.7)));
	col += vec3(1.0, 0.97, 0.92) * hl * 0.20 * own_light;
	float back = smoothstep(0.72, 0.95, r) * smoothstep(0.3, 1.0, dot(p / max(r, 1e-4), vec2(0.6, 0.8)));
	col += shallow.rgb * back * 0.22 * below;
	col *= 1.0 - mix(0.25, 0.6, own_light) * smoothstep(0.82, 1.0, r);
	return col;
}

void fragment()
{
	vec2 p = UV * 2.0 - 1.0;
	float r = length(p);
	float px = max(fwidth(p.x), 1e-4);
	float t = TIME + seed * 17.0;
	if (mode == 2)
	{
		float aa = max(fwidth(r), 0.004) * 1.25;
		COLOR = vec4(first(p, r, aa, t), 1.0 - smoothstep(1.0 - aa, 1.0, r));
	}
	else
	{
		float rs = r * canvas * 0.5;
		COLOR = vec4(blood(p, r, px, t), 1.0 - smoothstep(glass_r + 1.5, glass_r + 2.5, rs));
	}
}
