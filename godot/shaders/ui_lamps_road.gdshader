// The Lamps board's roads (src/Ui/LampBoard.cs): one MultiMesh of 591 quads, an anti-aliased line each
// (docs/design/LAMPS_SCREEN_BRIEF.md §5, §16; the mock's skins/a.py roads()). Rim to rim: the quad's ends are trimmed
// on the CPU. INSTANCE_CUSTOM: x length px, y kind (0 cold, 1 lit, 2 fuse, 3 path), z fade, w the dash phase (px).
shader_type canvas_item;
render_mode blend_premul_alpha, unshaded;

uniform vec4 win = vec4(0.0, 0.0, 1920.0, 1080.0);
uniform float feather = 48.0;
uniform float valley = 0.0;
uniform float find_on = 0.0;
const float PAD = 8.0;

varying flat vec4 d1;
varying vec2 lp;

vec3 hexc(int h) { return vec3(float((h >> 16) & 255), float((h >> 8) & 255), float(h & 255)) / 255.0; }

void vertex() {
	d1 = INSTANCE_CUSTOM;
	lp = vec2(UV.x * (d1.x + 2.0 * PAD) - PAD, (UV.y - 0.5) * 2.0 * PAD);
	COLOR = vec4(1.0);
}

void fragment() {
	float L = d1.x;
	int kind = int(d1.y + 0.5);
	float fade = d1.z;
	float s = lp.x, t = lp.y;
	float ex = max(max(-s, s - L), 0.0);
	float d = length(vec2(ex, t));
	bool v = valley > 0.5;
	float w = kind == 0 ? (v ? 1.5 : 1.25) : kind == 1 ? (v ? 1.4 : 2.0) : kind == 2 ? 2.0 : 3.0;
	float dl = d - w * 0.5;
	vec4 acc = vec4(0.0);
	vec3 light = vec3(0.0);
	if (kind == 0) {
		float a = clamp(0.5 - dl, 0.0, 1.0) * (v ? 0.40 : 0.38 * fade);
		acc = vec4(hexc(0xa7b1c2) * a, a);
	} else if (kind == 1) {
		float a = clamp(0.5 - dl, 0.0, 1.0) * 0.95;
		acc = vec4(hexc(0xf2c06b) * a, a);
		light = hexc(0xf2c06b) * 0.20 * exp(-d * d / (2.0 * 2.7 * 2.7));      // the mock: the line blurred (2.5 px) x0.64
	} else {
		bool path = kind == 3;
		float on = path ? 6.0 : 4.0, period = path ? 10.0 : 8.0;
		// the path's dashes run toward the focus at 30 px/s (§16); the fuse's stand
		float u = mod(s + d1.w - (path ? TIME * 30.0 : 0.0), period);
		float ddash = abs(u - on * 0.5) - on * 0.5;
		float dd = max(dl, ddash);
		vec3 col = path ? hexc(0xffd27a) : hexc(0xff9a3c);
		float al = path ? 1.0 : 0.60;
		if (path) {
			float ca = clamp(0.5 - (d - 0.6), 0.0, 1.0) * 0.25;
			acc = vec4(hexc(0xa7b1c2) * ca, ca);
		}
		float a = clamp(0.5 - dd, 0.0, 1.0) * al;
		acc = vec4(col * a, a) + acc * (1.0 - a);
		light = col * al * 0.12 * exp(-d * d / (2.0 * 2.7 * 2.7))
			* (0.5 + 0.5 * clamp(0.5 - ddash, 0.0, 1.0));
	}
	if (find_on > 0.5) { acc *= 0.45; light *= 0.45; }
	vec2 fc = FRAGCOORD.xy;
	float m = smoothstep(0.0, feather, fc.x - win.x) * smoothstep(0.0, feather, win.z - fc.x)
		* smoothstep(0.0, feather, fc.y - win.y) * smoothstep(0.0, feather, win.w - fc.y);
	COLOR = vec4(acc.rgb + light, acc.a) * m;
}
