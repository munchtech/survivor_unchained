// The HUD's two vessels (src/Ui/Instrument.cs): her life's blood in the left, the art's charge in the
// right. A glass sphere seen face-on, filled to a level whose surface lives (a slow swell, a slosh when
// it changes), the liquid deeper and darker below and turning slowly within; a pale trail where it has
// just fallen; a shield's light round the inside of the glass; the glass's own light over it all.
shader_type canvas_item;

uniform float level : hint_range(0.0, 1.0) = 1.0;
uniform float trail : hint_range(0.0, 1.0) = 1.0;
uniform float shield : hint_range(0.0, 1.0) = 0.0;
uniform float pulse : hint_range(0.0, 1.0) = 0.0;
// The surface's swell, kicked by a change and settling (0 at rest).
uniform float slosh = 0.0;
// The liquid's own light (the art ready to strike).
uniform float glow = 0.0;
uniform vec4 shallow : source_color = vec4(0.84, 0.16, 0.17, 1.0);
uniform vec4 deep : source_color = vec4(0.30, 0.02, 0.04, 1.0);
uniform vec4 empty : source_color = vec4(0.07, 0.035, 0.04, 1.0);
uniform vec4 trail_col : source_color = vec4(1.0, 0.62, 0.52, 1.0);
uniform vec4 shield_col : source_color = vec4(0.62, 0.84, 1.0, 1.0);
uniform float seed = 0.0;
// 1: the glass's light is the shader's own; 0: a painted glass (hud/globe_glass.png) lies over it.
uniform float own_light = 1.0;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }

float noise(vec2 p)
{
	vec2 i = floor(p), f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), u.x), mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), u.x), u.y);
}

float fbm(vec2 p)
{
	float v = 0.0, a = 0.5;
	for (int k = 0; k < 4; k++) { v += a * noise(p); p *= 2.07; a *= 0.5; }
	return v;
}

void fragment()
{
	vec2 p = UV * 2.0 - 1.0;
	float r = length(p);
	float aa = max(fwidth(r), 0.004) * 1.25;
	float inside = 1.0 - smoothstep(1.0 - aa, 1.0, r);
	float t = TIME + seed * 17.0;
	// The sphere's face toward us, for its round shading.
	float z = sqrt(max(0.0, 1.0 - r * r));
	vec3 n = vec3(p.x, -p.y, z);
	// The surface (in p's y, down the glass): full at the top, empty at the foot. It swells a little
	// always and more after a change, never at the very top or foot.
	float s0 = 1.0 - 2.0 * level;
	float amp = (0.010 + 0.05 * slosh) * smoothstep(0.0, 0.04, level) * smoothstep(1.0, 0.96, level);
	float s = s0 + amp * (sin(p.x * 4.0 + t * 1.7) + 0.5 * sin(p.x * 9.0 - t * 2.9 + 1.3));
	// The empty glass: dark, a little lighter where it faces us.
	vec3 col = empty.rgb * (0.55 + 0.45 * z);
	// The trail: what has just been lost, pale, until it drains to the liquid.
	float ts = 1.0 - 2.0 * trail;
	float in_trail = smoothstep(ts - aa, ts + aa, p.y) * (1.0 - smoothstep(s - aa, s + aa, p.y));
	col = mix(col, trail_col.rgb * (0.45 + 0.4 * z), in_trail * 0.5);
	// The liquid: shallow at its surface, deep at the foot, turning slowly within, lit from above-left.
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
		// The meniscus: a bright line where the liquid meets the air.
		float m = exp(-pow((p.y - s) / 0.028, 2.0)) * step(0.004, level) * step(level, 0.996);
		liq += mix(shallow.rgb, vec3(1.0), 0.5) * m * 0.6;
		col = mix(col, liq, below);
	}
	// The shield: a pale light round the inside of the glass, from the top, as far round as it holds.
	float ang = atan(p.x, -p.y) / 6.2831853;
	ang = ang < 0.0 ? ang + 1.0 : ang;
	float band = smoothstep(0.78, 0.86, r) * (1.0 - smoothstep(0.93, 0.98, r));
	float held = 1.0 - smoothstep(shield - 0.004, shield + 0.004, ang);
	col = mix(col, shield_col.rgb, band * held * 0.9 * step(0.001, shield));
	col += shield_col.rgb * 0.06 * shield;
	// Low: the glass flushes with the beat.
	col = mix(col, vec3(1.0, 0.26, 0.2), pulse * 0.24);
	// The glass's light: a soft window up and to the left, and the liquid's colour caught at the
	// lower right where light comes back through it.
	float hl = 1.0 - smoothstep(0.0, 0.42, length((p - vec2(-0.34, -0.48)) * vec2(1.0, 1.7)));
	col += vec3(1.0, 0.97, 0.92) * hl * 0.20 * own_light;
	float back = smoothstep(0.72, 0.95, r) * smoothstep(0.3, 1.0, dot(p / max(r, 1e-4), vec2(0.6, 0.8)));
	col += shallow.rgb * back * 0.22 * below;
	// The cuff's shadow on the glass's edge.
	col *= 1.0 - mix(0.25, 0.6, own_light) * smoothstep(0.82, 1.0, r);
	COLOR = vec4(col, inside);
}
