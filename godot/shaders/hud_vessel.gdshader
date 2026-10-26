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

vec3 blood(vec2 p, float r, float px, float t)
{
	bool small = mode == 1;
	// her blood: #1e0205 in its depth, #8c0d14 near the surface, the rim #e0302a, the meniscus #ff7a66;
	// the draught's a shade warmer
	vec3 c_deep = small ? vec3(0.150, 0.026, 0.014) : vec3(0.118, 0.008, 0.020);
	vec3 c_surf = small ? vec3(0.640, 0.130, 0.060) : vec3(0.549, 0.051, 0.078);
	vec3 c_rim = small ? vec3(0.960, 0.320, 0.170) : vec3(0.878, 0.188, 0.165);
	vec3 c_men = small ? vec3(1.000, 0.560, 0.420) : vec3(1.000, 0.478, 0.400);
	vec3 c_air = vec3(0.036, 0.030, 0.033);
	float aa = 0.6 * px;

	// Inside the thick wall the cavity's edge is seen refracted: the liquid just inside it, darker.
	float wall = smoothstep(RI - 0.5 * px, RI + 0.5 * px, r);
	vec2 q = r > RI ? p * ((RI - 0.006) / r) : p;
	float rq = length(q);
	float zq = sqrt(max(RI * RI - rq * rq, 0.0)) / RI;

	// The surface: a plane at the level, swelling a little at rest and tilted by a slosh; seen from a
	// little above, an ellipse 8% of its chord in height. None at full or empty.
	float lv = level;
	float s0 = RI * (1.0 - 2.0 * lv);
	float w = sqrt(max(RI * RI - s0 * s0, 0.0));
	float live = smoothstep(0.0, 0.025, lv) * smoothstep(1.0, 0.975, lv);
	float swell = (0.014 * sin(q.x * 3.1 + t * 1.25) + 0.007 * sin(q.x * 7.3 - t * 2.05 + 1.7)) * (small ? 0.0 : 1.0);
	float yc = s0 + (swell + tilt * q.x + wave * sin(q.x * 5.0 + t * 9.0)) * live;
	float xw = clamp(q.x / max(w, 1e-4), -1.0, 1.0);
	float he = 0.08 * w * sqrt(max(0.0, 1.0 - xw * xw));
	float yn = yc + he, yf = yc - he;
	float body = smoothstep(yn - aa, yn + aa, q.y);
	float top = smoothstep(yf - aa, yf + aa, q.y) * (1.0 - body);

	// The body: lighter toward its surface (full, toward the glass's top), near-black in its depth, round
	// as the cavity is, lit from the upper left.
	float dep = max(q.y - yn, 0.0);
	vec3 liq = mix(c_surf * 0.80, c_deep, smoothstep(0.0, small ? 1.1 : 0.95, dep));
	vec3 nq = vec3(q.x, -q.y, zq * RI) / RI;
	float lit = clamp(dot(nq, normalize(vec3(-0.55, 0.60, 0.58))), 0.0, 1.0);
	liq *= (0.70 + 0.45 * lit) * (0.80 + 0.20 * zq);
	// Slow dark veins turning in it, at low contrast.
	float va = t * 0.045 + seed * 6.0;
	mat2 vr = mat2(vec2(cos(va), sin(va)), vec2(-sin(va), cos(va)));
	float f = fbm(vr * q * (small ? 1.2 : 1.8) + vec2(seed * 13.0, t * 0.025));
	float vein = 1.0 - smoothstep(0.0, small ? 0.05 : 0.03, abs(f - 0.5));
	float swirl = fbm(vr * q * 0.9 + vec2(-t * 0.03, seed * 7.0));
	liq *= (0.93 + 0.14 * swirl) * (1.0 - 0.18 * vein);
	// The light leaving at the lower right: a rim, brightest just inside the wall.
	vec2 dq = q / max(rq, 1e-4);
	float face = clamp(dot(dq, vec2(0.574, 0.819)), 0.0, 1.0);
	float ex = pow(face, 3.0) * smoothstep(RI - (small ? 0.40 : 0.24), RI - 0.03, rq);
	liq = mix(liq, c_rim, clamp(ex * 0.95, 0.0, 1.0));
	liq += c_rim * 0.20 * pow(face, 8.0) * smoothstep(RI - 0.10, RI - 0.03, rq);

	// The surface seen from above: lighter than the body, the window's light caught on its far left.
	float v = clamp((q.y - yf) / max(2.0 * he, 1e-4), 0.0, 1.0);
	vec3 surf = mix(c_surf * 1.30, c_men, 0.20 * (1.0 - v)) * mix(1.0, 0.85, v);
	surf += c_men * 0.12 * exp(-pow((xw + 0.40) / 0.38, 2.0)) * (1.0 - v);
	// (the near lip a hair darker, so the ellipse reads)
	liq *= 1.0 - 0.30 * exp(-pow((q.y - yn) / (1.2 * px), 2.0)) * live;
	// Its far edge: the meniscus, 1 px, where the blood climbs the far wall.
	float men = (1.0 - smoothstep(0.30 * px, 1.05 * px, abs(q.y - yf + 0.25 * px))) * live;
	men *= smoothstep(1.0, 0.80, abs(xw)) * (1.0 - wall);

	// The air in the glass: dark, its far wall a little lighter toward the edge, warmed just above the blood.
	vec3 air = c_air * (0.70 + 0.65 * smoothstep(0.30, RI, rq));
	air += c_surf * 0.09 * exp(-max(yf - q.y, 0.0) / 0.16) * live;

	vec3 col = air;
	col = mix(col, surf, top);
	col = mix(col, liq, body);
	col = mix(col, c_men, 0.7 * men);
	// The heartbeat: the blood brightens.
	col += (col * 0.60 + c_rim * 0.10) * beat * max(top, body);

	// Healing: lighter, fresh blood swirling up from the foot.
	if (heal > 0.001)
	{
		float rise = heal_t * 0.85;
		float hn = fbm(vec2(q.x * 2.6 + 0.45 * sin(q.y * 4.0 + heal_t * 1.9), q.y * 2.1 + heal_t * 1.5) + seed * 3.0);
		float risen = smoothstep(RI - rise - 0.30, RI - rise + 0.05, q.y);
		float plume = smoothstep(0.40, 0.58, hn) * risen * body * exp(-pow(q.x / (0.35 + 0.6 * clamp(rise, 0.0, 1.0)), 2.0));
		col = mix(col, vec3(1.0, 0.40, 0.34), clamp(plume * heal * 1.5, 0.0, 1.0));
	}

	// Hurt: above the new level the glass keeps a film of blood from where it stood; it runs down,
	// unevenly (its rivulets slower), and clears.
	if (film_t < 1.0 && film_top > lv + 0.002)
	{
		float y0 = RI * (1.0 - 2.0 * film_top);
		float n1 = noise(vec2(q.x * 2.2 + seed * 11.0, 0.37));
		float prog = clamp(film_t / mix(0.62, 0.92, n1), 0.0, 1.0);
		float ytop = mix(y0, yn, prog * prog);
		float cx = q.x * 7.0 + seed * 5.0, cid = floor(cx);
		float rx = (cid + 0.25 + 0.5 * hash(vec2(cid, 7.7)) - seed * 5.0) / 7.0;
		float riv = step(0.6, hash(vec2(cid, 3.1))) * (1.0 - smoothstep(0.5 * px, 1.3 * px, abs(q.x - rx)));
		float rtop = mix(y0, yn, pow(prog * (0.45 + 0.3 * hash(vec2(cid, 9.9))), 2.0));
		float thin = 1.0 - smoothstep(0.5, 1.0, film_t);
		float sheet = smoothstep(ytop - aa, ytop + aa, q.y);
		float on = max(sheet, riv * smoothstep(rtop - aa, rtop + aa, q.y)) * (1.0 - body) * (1.0 - wall);
		float fa = (0.30 + 0.22 * smoothstep(ytop, yn, q.y) + 0.25 * riv + 0.18 * exp(-pow((q.y - ytop) / (1.6 * px), 2.0))) * thin;
		vec3 fc = vec3(0.30, 0.018, 0.032) + c_men * 0.08 * smoothstep(0.2, -0.8, q.x + q.y);
		col = mix(col, fc, clamp(fa, 0.0, 0.9) * on);
	}

	// Empty: dark glass with a dried film, heaviest at the foot where the last of it stood.
	float dry = (1.0 - smoothstep(0.0, 0.012, lv)) * dry_film;
	if (dry > 0.0)
	{
		float dn = fbm(q * 5.0 + seed * 7.0);
		float stain = smoothstep(0.50, 0.72, dn) * smoothstep(0.0, 0.85, q.y);
		float tide = exp(-pow((q.y - (RI - 0.14) - 0.015 * sin(q.x * 11.0)) / (1.3 * px), 2.0)) * step(abs(q.x), 0.62);
		float cid = floor(q.x * 6.0 + 3.0);
		float trail_ = step(0.7, hash(vec2(cid, 5.3))) * (1.0 - smoothstep(0.4 * px, 1.1 * px, abs(q.x - (cid + 0.5 - 3.0) / 6.0))) * smoothstep(-0.2, 0.6, q.y);
		float pool = smoothstep(RI - 0.12, RI - 0.03, q.y);
		float da = clamp(stain * 0.35 + tide * 0.55 + trail_ * 0.35 + pool * 0.45, 0.0, 0.7) * dry;
		col = mix(col, vec3(0.17, 0.040, 0.028) * (0.8 + 0.4 * dn), da);
	}

	// Shielded: frost rimes the glass from the top, as far round as the shield holds; when the shield
	// breaks it cracks into shards that slide off and fade.
	float reach = crack < 1.0 ? crack_reach : frost;
	if (reach > 0.001)
	{
		vec2 fp = p;
		float fade = 1.0, lines = 0.0;
		if (crack < 1.0)
		{
			vec2 mid; float border;
			cells(p * 4.5 + seed * 3.0, mid, border);
			vec2 cm = (mid - seed * 3.0) / 4.5;
			fp = p - (normalize(cm + vec2(0.0, -0.15)) * 0.10 * crack + vec2(0.0, 0.45 * crack * crack));
			fade = 1.0 - smoothstep(0.30, 1.0, crack);
			lines = (1.0 - smoothstep(0.0, 0.06, border)) * (1.0 - smoothstep(0.0, 0.6, crack));
		}
		float fr = length(fp);
		float ang = abs(atan(fp.x, -fp.y)) / PI;
		float held = 1.0 - smoothstep(reach - 0.02, reach + 0.02, ang + (fbm(fp * 9.0 + seed * 4.0) - 0.5) * 0.10);
		float th = 0.195 * (1.0 - 0.5 * ang / max(reach, 0.05));
		float sp = noise(vec2(ang * 46.0 + seed * 3.0, 0.5));
		float inner = RI - th * (0.35 + 0.9 * sp * sp);
		float rime = smoothstep(inner - px, inner + px, fr) * held * fade * step(fr, 1.0);
		vec2 fm; float fb;
		cells(fp * 9.0 + seed * 5.0, fm, fb);
		float facet = 1.0 - smoothstep(0.0, 0.08, fb);
		float dens = mix(0.45, 0.85, smoothstep(inner, RI, fr));
		vec3 ice = mix(vec3(0.604, 0.831, 1.0), vec3(0.97, 0.99, 1.0), 0.65 * facet);
		col = mix(col, ice, clamp(rime * (dens + 0.22 * facet), 0.0, 1.0));
		col += vec3(0.604, 0.831, 1.0) * 0.055 * reach * fade;
		col += vec3(0.85, 0.94, 1.0) * lines * held * 0.9;
	}

	// The wall: the cavity's edge seen through thick glass, darker.
	col *= mix(1.0, 0.70, wall);
	return col;
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
		COLOR = vec4(blood(p, r, px, t), 1.0 - smoothstep(1.0 - px, 1.0, r));
}
