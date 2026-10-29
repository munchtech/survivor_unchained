// UI 23, HUD A: the level coin's experience ring (DgPanel.Ring; mock7.py medallion(), hud_a_geo.json "xp_ring").
// A lit filament set in the coin's bronze rim (the rim, its groove and the arch are the plate's baked art): filled
// clockwise from 12 o'clock to frac, its colour the hue at its edges and the core along its middle (a gaussian of
// sigma), the unfilled track faintly tinted, a hair of light on the groove's outer lip over the filled part, a glint
// at the head, and the gold tick at 12. Premultiplied: the tint, the lip and the glint add; the fill and the tick
// cover. boost (a gain's run) lifts the filament; whole (a level-up) lights the whole track for its moment.
shader_type canvas_item;
render_mode blend_premul_alpha;

uniform vec2 at;                 // the quad's top left on the 1080 screen
uniform vec2 size;
uniform vec2 c = vec2(960.0, 1042.0);
uniform float r0 = 28.675;
uniform float r1 = 36.445;
uniform float sigma = 1.9;
uniform float track = 0.22;
uniform float lip = 0.35;
uniform vec2 glint = vec2(2.6, 0.9);   // the head's glint: sigma (px) and strength
uniform float frac = 0.0;
uniform float boost = 0.0;
uniform float whole = 0.0;
uniform vec3 hue = vec3(0.353, 0.635, 0.839);
uniform vec3 core = vec3(0.812, 0.91, 1.0);
const vec3 TICK = vec3(0.95, 0.80, 0.52);

void fragment()
{
	vec2 p = at + UV * size;
	vec2 dv = p - c;
	float d = length(dv);
	float ang = fract(atan(dv.x, -dv.y) / TAU + 1.0);
	float mid = 0.5 * (r0 + r1);
	float f = clamp(frac, 0.0, 1.0);
	float li = clamp(min(d - (r0 + 0.8), (r1 - 0.8) - d) + 0.5, 0.0, 1.0);
	float fill = li * clamp((f - ang) * TAU * mid + 0.5, 0.0, 1.0);
	float ck = exp(-pow((d - mid) / sigma, 2.0));
	float lift = 1.0 + boost;
	vec3 col = mix(hue, core, ck) * lift;
	vec3 rgb = col * fill;
	float a = fill;
	rgb += hue * (li * (1.0 - fill) * (track + 0.9 * whole));
	float lp = exp(-pow((d - (r1 + 0.6)) / 0.9, 2.0)) * clamp((f - ang) * TAU * r1 + 0.5, 0.0, 1.0);
	rgb += hue * (lp * lip * lift);
	float ta = f * TAU;
	vec2 tp = c + mid * vec2(sin(ta), -cos(ta));
	vec2 dt = p - tp;
	float gl = exp(-dot(dt, dt) / (2.0 * glint.x * glint.x)) * step(d, r1 + 3.0);
	rgb += core * (gl * glint.y * lift);
	float tk = clamp(1.2 - abs(dv.x), 0.0, 1.0) * clamp(min(d - (r0 - 1.5), (r1 + 1.5) - d) + 0.5, 0.0, 1.0) * step(dv.y, 0.0);
	rgb = TICK * tk + rgb * (1.0 - tk);
	a = tk + a * (1.0 - tk);
	// (the callouts' dim: the modulate, premultiplied)
	vec4 m = COLOR;
	COLOR = vec4(rgb * m.rgb * m.a, a * m.a);
}
