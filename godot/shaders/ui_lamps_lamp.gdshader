// The Lamps board's lamps (src/Ui/LampBoard.cs): one MultiMesh of 574 quads, every kind an SDF here
// (docs/design/LAMPS_SCREEN_BRIEF.md §5, §6, §16; the mock's skins/a.py lamp() is the look).
// Instance COLOR: r kind (LampKind's order), g state (0 lit, 1 available, 2 unlit, 3 blocked), b fade, a flags
// (1 dim, 2 focus, 4 on the path, 8 near (within 3 steps), 16 found, 32 the gate notch).
// INSTANCE_CUSTOM: x radius px (the focus's x1.1 in), y seed 0..1, z calling (0 warden, 1 reaver, 2 arcanist, 3 stalker),
// w the notch's alpha (it fades with its lamp).
shader_type canvas_item;
render_mode blend_premul_alpha, unshaded;

#include "res://shaders/ui_lamps_field.gdshaderinc"
uniform float valley = 0.0;                            // 1: the Valley's dots
uniform float find_on = 0.0;                           // 1: Find is up (the rest drop to 45%)
uniform sampler2D palm : filter_linear_mipmap, repeat_disable;

varying flat vec4 d0;
varying flat vec4 d1;
varying vec2 lp;


void vertex() {
	d0 = COLOR;
	d1 = INSTANCE_CUSTOM;
	float H = d1.x + 14.0;
	lp = (UV - 0.5) * 2.0 * H;
	COLOR = vec4(1.0);
}

vec3 hexc(int h) { return vec3(float((h >> 16) & 255), float((h >> 8) & 255), float(h & 255)) / 255.0; }

float cov(float d) { return clamp(0.5 - d, 0.0, 1.0); }
float covs(float d, float soft) { return clamp(0.5 - d / (1.0 + soft), 0.0, 1.0); }
float ring(float d, float w) { return abs(d) - w * 0.5; }
float circle(vec2 p, vec2 c, float r) { return length(p - c) - r; }

float rbox(vec2 p, vec2 hw, float r) {
	vec2 q = abs(p) - hw + r;
	return length(max(q, 0.0)) + min(max(q.x, q.y), 0.0) - r;
}
float stadium(vec2 p, float hw, float hh) {
	float ax = max(hw - hh, 0.0);
	float x = clamp(p.x, -ax, ax);
	return length(vec2(p.x - x, p.y)) - hh;
}
float lozenge(vec2 p, float r) { vec2 q = abs(p); return (q.x + q.y - r) * 0.70710678; }
float segd(vec2 p, vec2 a, vec2 b) {
	vec2 ab = b - a;
	float t = clamp(dot(p - a, ab) / max(dot(ab, ab), 1e-6), 0.0, 1.0);
	return length(p - a - ab * t);
}
// an n-ray sunburst, the mock's polar star
float star(vec2 p, float r_in, float r_out, float n, float rot) {
	float rr = length(p);
	float th = atan(p.y, p.x) - rot;
	float seg = 2.0 * PI / n;
	float f = abs(fract(th / seg) - 0.5) * 2.0;
	float a = (1.0 - f) * seg * 0.5;
	vec2 t1 = vec2(r_out, 0.0);
	vec2 t2 = r_in * vec2(cos(seg * 0.5), sin(seg * 0.5));
	vec2 nn = normalize(vec2(t2.y - t1.y, t1.x - t2.x));
	float c = dot(nn, t1);
	float rb = c / (nn.x * cos(a) + nn.y * sin(a));
	return (rr - rb) * (c / max(rb, 1e-6) * 0.9 + 0.1);
}
// a flame drop, point up (y down): base circle w/2 at the bottom, tip at cy - h/2
float teardrop(vec2 p, vec2 c, float h, float w) {
	float r = w * 0.5;
	float by = c.y + h * 0.5 - r;
	float ty = c.y - h * 0.5;
	float dx = abs(p.x - c.x);
	float L = max(by - ty, 1e-6);
	float s = min(r / L, 0.999);
	float ang = asin(s);
	float side = dx * cos(ang) - (p.y - ty) * sin(ang);
	float dc = length(vec2(dx, p.y - by)) - r;
	float tang = by - r * s;
	return p.y < tang ? max(side, ty - p.y) : dc;
}
float shield(vec2 p, float s) {
	float x = abs(p.x), y = p.y;
	float body = max(x - s, -s * 1.05 - y);
	float R = s * 2.0;
	float dc = length(vec2(x + (R - s), y + s * 0.1)) - R;
	float lower = y > -s * 0.1 ? dc : body;
	return max(max(lower, body), y - s * 1.25);
}
// the calling's glyph in the hearth (warden shield, reaver axe, arcanist staff, stalker bow); s = half width
float calling_glyph(vec2 p, float s, int calling) {
	if (calling == 1) {           // axe: a haft and a crescent blade
		float haft = segd(p, vec2(-0.15 * s, 1.25 * s), vec2(0.15 * s, -1.2 * s)) - 0.16 * s;
		float blade = max(circle(p, vec2(-0.1 * s, -0.55 * s), 0.85 * s), -circle(p, vec2(-0.95 * s, -0.55 * s), 0.75 * s));
		blade = max(blade, -p.x - 0.05 * s);
		return min(haft, blade);
	} else if (calling == 2) {    // staff: a shaft and a ringed head
		float shaft = segd(p, vec2(0.0, 1.3 * s), vec2(0.0, -0.55 * s)) - 0.15 * s;
		float head = ring(circle(p, vec2(0.0, -0.9 * s), 0.38 * s), 0.22 * s);
		return min(shaft, head);
	} else if (calling == 3) {    // bow: an arc and its string
		float arc = ring(circle(p, vec2(-0.75 * s, 0.0), 1.35 * s), 0.24 * s);
		arc = max(arc, -(p.x - 0.12 * s));
		arc = max(arc, abs(p.y) - 1.15 * s);
		float str = segd(p, vec2(0.18 * s, -1.08 * s), vec2(0.18 * s, 1.08 * s)) - 0.06 * s;
		return min(arc, str);
	}
	return shield(p, s);
}
float crescent(vec2 p, float R) {
	float rr = R * 0.66;
	float ang = atan(p.y, p.x);
	float dang = abs(mod(ang + 0.75 * PI + PI, 2.0 * PI) - PI);
	float arc = abs(length(p) - rr) - 1.0;
	return max(arc, (dang - 0.66) * rr);
}
// a 3-stop radial ramp: a at 0, b at tm, c at 1
vec3 grad3(float t, vec3 a, float tm, vec3 b, vec3 c) {
	t = clamp(t, 0.0, 1.0);
	return t < tm ? mix(a, b, t / tm) : mix(b, c, (t - tm) / (1.0 - tm));
}

// acc: premultiplied, "over" from the bottom up; light: additive glow (alpha untouched)
void over_(inout vec4 acc, vec3 c, float a) { acc = vec4(c * a, a) + acc * (1.0 - a); }
void fill(inout vec4 acc, float d, vec3 c, float a) { over_(acc, c, cov(d) * a); }
void fills(inout vec4 acc, float d, vec3 c, float a, float soft) { over_(acc, c, covs(d, soft) * a); }
void glow(inout vec3 light, vec2 p, float sigma, vec3 c, float peak) { light += c * peak * exp(-dot(p, p) / (2.0 * sigma * sigma)); }

float fmask(vec2 fc) { return field_mask(fc); }

void fragment() {
	vec4 acc = vec4(0.0);
	vec3 add_light = vec3(0.0);
	int kind = int(d0.r + 0.5);
	int st = int(d0.g + 0.5);
	float fade = d0.b;
	int flags = int(d0.a + 0.5);
	bool dim = (flags & 1) != 0, focus = (flags & 2) != 0, onpath = (flags & 4) != 0, near = (flags & 8) != 0;
	bool found = (flags & 16) != 0, notch_on = (flags & 32) != 0;
	bool inked = (flags & 64) != 0;                       // the Lamp stop: its feed glyph is drawn inside (LampBoard's ink layer)
	float R = d1.x;
	float seed = d1.y;
	int calling = int(d1.z + 0.5);
	vec2 p = lp;
	bool lit = st == 0;
	// kinds: 0 start 1 small 2 attribute 3 entry 4 skill 5 notable 6 blue 7 reflex 8 reflexUp 9 form 10 flareLamp
	// 11 ultimate 12 ultimateMod 13 rite 14 link 15 hand; the wick panel's (LampWick): 16 wick lead-in 17 Turn
	bool flare = kind == 10 || kind == 11 || kind == 12;
	bool blue = kind == 6;
	bool far_blue = blue && !lit && !near;
	bool asleep = lit && dim;
	float op = (dim ? 0.5 : 1.0) * fade;
	float flick = 1.0 + (seed - 0.5) * 0.08;
	float breathe = 0.8 + 0.2 * sin(2.0 * PI * (TIME / 2.6 + seed));
	float rimw = 1.25;
	float rim_a = st == 3 ? 0.30 : 0.55;

	vec3 GLASS_IN = hexc(0x1b1f26), GLASS_OUT = hexc(0x0d1014), GLASS_RIM = hexc(0x9aa4b2);
	vec3 LIT_RIM = hexc(0xffd98a), EMBER = hexc(0xff9a3c), FOCUS = hexc(0xe8c87a);
	vec3 COLLET = hexc(0xb9c3d6), FL_RIM = hexc(0xc9672a), ASLEEP = hexc(0xa9b4c2);

	if (valley > 0.5) {
		// the Valley's dots
		float body = length(p) - R;
		if (lit) {
			vec3 col = blue ? hexc(0x7fb2ff) : flare ? hexc(0xff9a3a) : hexc(0xf7cf7f);
			fill(acc, body, col, 1.0);
			fill(acc, length(p) - R * 0.45, hexc(0xfff6e0), 0.9);
		} else {
			body = length(p) - max(R, 1.5);
			vec3 dc = blue ? hexc(0x3b6fd8) : flare ? FL_RIM : hexc(0xb4bccb);
			fill(acc, body, dc, 0.5);
			op = dim ? 0.5 : 1.0;
			if (st == 1) {
				fill(acc, ring(body - 0.2, 1.25), EMBER, 0.85 * breathe);
				glow(add_light, p, 3.0, EMBER, 0.35 * breathe);
			}
		}
		if (focus) {
			fill(acc, ring(length(p) - (R + 4.0), 1.5), FOCUS, 1.0);
			glow(add_light, p, R + 5.0, FOCUS, 0.15);
		}
	} else {
		// ---- the body by kind
		float hw = R, hh = R * 14.0 / 22.0;
		float body;
		if (kind == 13) body = lozenge(p, R);
		else if (kind == 2) body = rbox(p, vec2(R), R * 0.35);
		else if (kind == 14) body = stadium(p, hw, hh);
		else if (kind == 11) body = star(p, R * 0.58, R, 8.0, -PI * 0.5);
		else if (kind == 12) body = teardrop(p, vec2(0.0, R * 0.08), R * 2.0, R * 1.25);
		else body = length(p) - R;

		// ---- the glass
		if (kind == 14) {
			float ringd = ring(body, 2.0);
			if (lit) {
				fill(acc, ringd, LIT_RIM, 1.0);
				fill(acc, ring(body, 0.8), hexc(0xfff4d6), 0.8);
				glow(add_light, p, R * 0.9, hexc(0xffb04a), 0.45 * flick);
			} else {
				fill(acc, ring(body, 3.2), hexc(0x0b0d11), 0.55);
				fill(acc, ringd, GLASS_RIM, st != 3 ? 0.75 : 0.40);
			}
			// §16: the chain link, a 1 px stroke: two interlocked ovals inside the stadium ring
			float ohw = hw * 0.44, ohh = hh * 0.46;
			for (int k = 0; k < 2; k++) {
				float sx = k == 0 ? -1.0 : 1.0;
				float ov = stadium(p - vec2(sx * hw * 0.24, 0.0), ohw, ohh);
				fill(acc, ring(ov, 1.0), lit ? hexc(0x5a3a12) : GLASS_RIM, lit ? 0.75 : (st != 3 ? 0.55 : 0.32));
			}
		} else {
			if (lit && !asleep) {
				float t = length(p - vec2(0.0, -R * 0.12)) / (R * 1.05);
				vec3 c = blue ? grad3(t, hexc(0xe6f4ff), 0.55, hexc(0x7fb2ff), hexc(0x2a5bd7))
					: flare ? grad3(t, hexc(0xfff0c0), 0.6, hexc(0xff9a3a), hexc(0xb8461c))
					: grad3(t, hexc(0xfff0c4), 0.6, hexc(0xf4c46a), hexc(0xc8822e));
				fill(acc, body, c * flick, 1.0);
				vec3 rc = blue ? hexc(0xcfe2ff) : flare ? hexc(0xffc27a) : hexc(0xe9b45c);
				fill(acc, ring(body + rimw * 0.5, rimw), rc, 0.95);
			} else {
				if (blue && !far_blue) {
					// §16 cobalt glass: a dark core, the light gathering at the rim
					float t = length(p - vec2(R * 0.08, R * 0.10)) / (R * 1.02);
					vec3 c = t < 0.55 ? mix(hexc(0x0d2a6b), hexc(0x123077), t / 0.55)
						: t < 0.86 ? mix(hexc(0x123077), hexc(0x2852ad), (t - 0.55) / 0.31)
						: mix(hexc(0x2852ad), hexc(0x3b6fd8), clamp((t - 0.86) / 0.14, 0.0, 1.0));
					fill(acc, body, c, 0.97);
				} else {
					float t = length(p - vec2(-R * 0.2, -R * 0.25)) / (R * 1.25);
					fill(acc, body, mix(GLASS_IN, GLASS_OUT, clamp(t, 0.0, 1.0)), 0.94);
				}
				if (onpath) {     // §16: a 60% warm inner glow
					float g = exp(-dot(p, p) / (2.0 * (R * 0.55) * (R * 0.55)));
					float cv = cov(body) * 0.60;
					acc.rgb += hexc(0xffb860) * g * cv;
				}
				if (!asleep && !blue) {
					vec3 rc = flare ? FL_RIM : GLASS_RIM;
					float ra = st != 3 ? (flare ? 0.70 : rim_a) : 0.30;
					if (dim) {
						float th = atan(p.y, p.x);
						float per = 4.0 / max(R, 1.0);
						float dots = abs(fract(th / per) - 0.5) * 2.0 - 0.5;
						fill(acc, max(ring(body + rimw * 0.5, rimw), dots * per * R * 0.5), hexc(0x8c8f95), 0.9);
					} else {
						fill(acc, ring(body + rimw * 0.5, rimw), rc, ra);
					}
				}
				if (!blue && !asleep && kind != 12)
					fill(acc, length(p - vec2(-0.35 * R)) - 0.18 * R, vec3(1.0), 0.25);
			}
			if (blue) {
				// the 4-prong collet (prongs at 45°)
				float ca = st != 3 ? 0.70 : 0.4;
				fill(acc, ring(length(p) - (R + 0.75), 1.5), COLLET, ca);
				for (int k = 0; k < 4; k++) {
					float a = PI * 0.25 + float(k) * PI * 0.5;
					vec2 u = vec2(cos(a), sin(a));
					fill(acc, segd(p, u * (R + 0.3), u * (R * 1.35)) - 1.0, COLLET, ca);
				}
				if (!lit && !far_blue) {
					float cres = crescent(p, R);
					fills(acc, cres, vec3(1.0), 0.80, 0.3);
					fills(acc, cres - 1.2, hexc(0xcfe0ff), 0.14, 1.0);
					float arc = ring(length(p) - R * 0.66, 1.0);
					float ang = atan(p.y, p.x);
					arc = max(arc, (abs(ang - PI * 0.25) - 0.42) * R * 0.66);
					fills(acc, arc, hexc(0x9cc0ff), 0.30, 0.4);
				} else if (!lit) {
					fill(acc, length(p - vec2(-0.32 * R, -0.36 * R)) - 0.16 * R, vec3(1.0), 0.22);
				} else {
					fills(acc, crescent(p, R), vec3(1.0), 0.80, 0.3);
				}
			}
		}

		// ---- the kind's marks
		vec3 mark_c = (lit && !asleep) ? hexc(0x4a3214) : GLASS_RIM;
		float mark_a = lit ? 0.85 : 0.65;
		if (kind == 5 && !inked) {
			fill(acc, ring(length(p) - R * 0.60, 1.0), mark_c, lit ? 0.55 : 0.45);
		} else if (kind == 3) {
			fill(acc, ring(length(p) - (R - 3.5), 1.0), lit ? mark_c : GLASS_RIM, lit ? 0.75 : 0.5);
		} else if (kind == 0) {
			vec3 rc = lit ? LIT_RIM : GLASS_RIM;
			fill(acc, ring(body + 1.25, 2.5), rc, lit ? 0.95 : 0.6);       // the heavy collet
			for (int k = 0; k < 4; k++) {
				float a = float(k) * PI * 0.5 + PI * 0.25;
				vec2 u = vec2(cos(a), sin(a));
				fill(acc, segd(p, u * (R + 2.5), u * (R + 6.5)) - 0.8, rc, lit ? 0.9 : 0.55);
			}
			fill(acc, calling_glyph(p - vec2(0.0, 0.5), R * 0.36, calling), lit ? hexc(0x5a3a12) : GLASS_RIM, 0.80);
		} else if (kind == 9) {
			float a1 = abs(p.y) * 0.9 + p.x - R * 0.25;
			float dch = max(a1, -a1 - 1.3);
			fill(acc, max(dch, abs(p.y) - R * 0.45), mark_c, mark_a);
		} else if (kind == 7) {
			float arc = ring(length(p - vec2(R * 0.25, 0.0)) - R * 0.5, 1.1);
			fill(acc, max(arc, p.x - R * 0.1), mark_c, mark_a);
		}

		// ---- the flame / core
		float D_ = 2.0 * R;
		if (lit && kind != 14 && !inked) {
			if (asleep) fill(acc, teardrop(p, vec2(0.0, R * 0.1), R * 0.6, R * 0.34), ASLEEP, 0.9);
			else if (D_ >= 18.0 && (kind == 5 || kind == 3 || kind == 13 || kind == 10 || kind == 7 || kind == 9 || kind == 17))
				fills(acc, teardrop(p, vec2(0.0, R * 0.05), R * 0.70, R * 0.36), hexc(0xfffbea), 0.95, 0.25);
			else if (kind != 0 && kind != 15 && kind != 6 && kind != 11 && kind != 12)
				fills(acc, length(p) - max(R * 0.32, 1.4), hexc(0xfffbea), 0.95, 0.3);
			else if (kind == 6 || kind == 11)
				fills(acc, length(p) - R * 0.22, vec3(1.0), 0.85, 0.6);
		}

		// ---- the Turn's flame crown: three small tongues over its top (skins/a.py wick_turn)
		if (kind == 17) {
			vec3 cc = lit ? hexc(0xffd98a) : hexc(0x8a8f98);
			float ca = lit ? 0.95 : 0.55;
			float dc = 1e6;
			dc = min(dc, teardrop(p, vec2(-6.5, -R - 3.5 + 3.0), 7.0, 4.2));
			dc = min(dc, teardrop(p, vec2(0.0, -R - 5.0 + 3.0), 10.0, 4.2));
			dc = min(dc, teardrop(p, vec2(6.5, -R - 3.5 + 3.0), 7.0, 4.2));
			fill(acc, dc, cc, ca);
			if (lit) glow(add_light, p - vec2(0.0, -R - 3.0), 6.0, hexc(0xffb04a), 0.35);
		}

		// ---- the hand's palm
		if (kind == 15) {
			float gs = D_ * 0.74;
			vec2 uv = p / gs + 0.5;
			if (uv.x >= 0.0 && uv.x <= 1.0 && uv.y >= 0.0 && uv.y <= 1.0) {
				vec4 g = texture(palm, uv);
				float a = clamp(max(g.a * dot(g.rgb, vec3(0.333)) * 1.6, 0.0), 0.0, 1.0);
				over_(acc, lit ? hexc(0x5a3a12) : GLASS_RIM, a * (lit ? 0.9 : 0.7));
			}
		}

		// ---- available: the ember rim, breathing (60-100% over 2.6 s)
		if (st == 1 && blue) {
			// a blue stays cobalt glass: its ember is a thin outer rim past the collet, and its glow never on the glass
			fill(acc, ring(length(p) - (R + 3.4), 1.1), EMBER, 0.85 * breathe);
			float outside = smoothstep(R + 1.5, R + 3.5, length(p));
			glow(add_light, p, R + 3.0, EMBER, 0.14 * breathe * outside);
		} else if (st == 1) {
			fill(acc, ring(body + 0.875, 1.75), EMBER, breathe);
			glow(add_light, p, R + 3.0, EMBER, 0.20 * breathe);
		}
	}

	// ---- found: a white-gold ring pulse
	if (found) {
		float pulse = 0.5 + 0.5 * sin(TIME * 4.0);
		fill(acc, ring(length(p) - (R + 3.0 + 2.0 * pulse), 1.5), hexc(0xfff2cf), 0.9 * (1.0 - 0.5 * pulse));
	} else if (find_on > 0.5) {
		op *= 0.45;
	}

	acc *= op;
	add_light *= op;

	// ---- the Turn crossed (One Turn a skill): a thin dark bar, at full strength over the dimmed glass
	if (kind == 17 && dim) {
		float ds = segd(p, vec2(-R - 2.0, R + 2.0), vec2(R + 2.0, -R - 2.0));
		fill(acc, ds - 1.6, hexc(0x050607), 0.9);
		fill(acc, abs(ds - 2.1) - 0.4, hexc(0x9aa4b2), 0.25);
	}

	// ---- the gate notch (its alpha is its lamp's fade and the edge's)
	if (notch_on && valley < 0.5) {
		vec2 c = vec2(R * 0.72 + 5.0, R * 0.72 + 4.0);
		float tab = rbox(p - c, vec2(7.5, 8.0), 4.0);
		float na = d1.w;
		vec4 keep = acc;
		acc = vec4(0.0);
		fill(acc, tab, hexc(0x0b0c0f), 0.88);
		fill(acc, ring(tab, 0.9), hexc(0xcdae72), 0.30);
		acc = acc * na + keep * (1.0 - acc.a * na);
	}

	// ---- focus: a crisp 1.5 px gold ring at r+5, a soft outer glow at 30%
	if (focus && valley < 0.5) {
		float fr = ring(length(p) - (R + 5.0), 1.5);
		fill(acc, fr, FOCUS, 1.0);
		add_light += FOCUS * 0.30 * covs(fr, 3.0);
		glow(add_light, p, R + 6.0, FOCUS, 0.12);
	}

	// (the glows end in a round window inside the quad (R + 14): the focus's wide glow read as a lighter square on A's smoke)
	add_light *= 1.0 - smoothstep(R + 4.0, R + 14.0, length(lp));
	float m = fmask(FRAGCOORD.xy);
	COLOR = vec4(acc.rgb + add_light, acc.a) * m;
}
