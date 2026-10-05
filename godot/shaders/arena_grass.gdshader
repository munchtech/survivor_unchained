// An ember arena's grass (World/Grass.cs, arena tussocks): whole tussocks
// of long blades arching out from one root, laid on a jittered grid that
// wraps round the survivor; where each grows, and how tall, comes from the
// place's grass paint (Maps/ArenaGen.cs). Grass reads from thirty metres up
// by its light, not its blades: dark at the root where the tussock shades
// itself, its arched backs and tips catching the moon, and gaps of earth
// between the tussocks; a carpet of thin blades at the ground's own colour
// reads as scratches.
shader_type spatial;
render_mode cull_disabled, diffuse_burley, world_vertex_coords;

uniform sampler2D noise_tex : filter_linear_mipmap, repeat_enable;
// G: where none grows (255 less the paint's grass).
uniform sampler2D splat : filter_linear_mipmap, repeat_disable;
uniform float zone_size = 300.0;
uniform float density = 1.0;
// Metres, the shortest tussock and the tallest, and how far a tussock spreads.
uniform vec2 height = vec2(0.35, 0.8);
uniform float spread = 1.0;
// The tussock's colours, all linear: deep in it, its body, its sunned tips
// (dead grass), and the green still living in some of it.
uniform vec3 root_col : source_color = vec3(0.02, 0.018, 0.012);
uniform vec3 body_col : source_color = vec3(0.12, 0.1, 0.06);
uniform vec3 tip_col : source_color = vec3(0.3, 0.26, 0.17);
uniform vec3 green_col : source_color = vec3(0.07, 0.09, 0.04);
uniform float green = 0.3;
uniform vec3 wind = vec3(1.0, 0.35, 0.7);
uniform vec4 pusher = vec4(0.0);
uniform vec2 centre = vec2(0.0);
uniform float span = 80.0;
uniform sampler2D heights : filter_linear, repeat_disable;
uniform float h_size = 300.0;
uniform float h_res = 300.0;

varying float v_t;
varying vec3 v_col;
varying float v_dry;

float gh(vec2 p) { vec3 p3 = fract(vec3(p.xyx) * 0.1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }

float ground_at(vec2 p) {
	vec2 f = clamp((p + h_size * 0.5) / h_size * (h_res - 1.0), vec2(0.0), vec2(h_res - 1.0));
	return textureLod(heights, (f + 0.5) / h_res, 0.0).r;
}

void vertex() {
	vec3 root = MODEL_MATRIX[3].xyz;
	vec3 off = VERTEX - root;
	vec2 wp = root.xz + span * round((centre - root.xz) / span);
	float edge = 1.0 - smoothstep(span * 0.38, span * 0.5, length(wp - centre));
	float h1 = gh(wp * 7.1), h3 = gh(wp * 3.3 + 11.0), h4 = gh(wp * 5.7 + 4.0);
	float paint = 1.0 - texture(splat, (wp + zone_size * 0.5) / zone_size).g;
	vec4 nz = texture(noise_tex, wp * 0.05);
	// The paint's edge frayed, and the field gathered into swathes and gaps
	// a few metres across, so earth shows between.
	float g = smoothstep(0.08, 0.6, paint + (nz.g - 0.5) * 0.45);
	float swathe = smoothstep(0.3, 0.62, texture(noise_tex, wp * 0.13 + 0.4).r * 0.7 + nz.r * 0.3);
	float dens = g * mix(0.45, 1.0, swathe);
	float keep = step(h3, dens * density * edge);
	// Taller where it grows thick, short at the fringes.
	float hgt = mix(height.x, height.y, clamp(g * 0.6 + swathe * 0.4 + (h4 - 0.5) * 0.4, 0.0, 1.0)) * keep;
	float t = clamp(UV.y, 0.0, 1.0);
	v_t = t;
	vec3 p = vec3(off.x * spread * (0.8 + 0.4 * h1) * keep, off.y * hgt, off.z * spread * (0.8 + 0.4 * h1) * keep);
	// Wind: a slow swell and gusts travelling over the field; the survivor parts it.
	float swell = sin(TIME * 1.3 + dot(wp, wind.xy) * 0.45 + nz.a * 5.0) * 0.5 + 0.5;
	float gust = texture(noise_tex, wp * 0.018 - TIME * vec2(0.03, 0.011)).r;
	vec2 bend = normalize(wind.xy) * (swell * 0.25 + gust * gust * 0.8) * wind.z;
	vec2 a = wp - pusher.xy;
	float pd = length(a);
	bend += (pd > 0.001 ? a / pd : vec2(0.0)) * (1.0 - smoothstep(0.0, pusher.z, pd)) * pusher.w * 1.6;
	float bl = min(length(bend), 1.2);
	bend = bl > 0.0 ? normalize(bend) * bl : vec2(0.0);
	float tt = t * t;
	p.xz += bend * tt * hgt * 0.8;
	p.y -= bl * tt * hgt * 0.3;
	VERTEX = vec3(wp.x, ground_at(wp) - 0.03, wp.y) + p;
	NORMAL = vec3(0.0, 1.0, 0.0);
	// Each tussock its own: some still green, most gone to straw, each blade
	// a shade of its own (UV.x).
	float live = smoothstep(0.55, 0.85, texture(noise_tex, wp * 0.021 + 5.3).g * 0.75 + h1 * 0.25) * green * 2.0;
	v_dry = clamp(1.0 - live, 0.0, 1.0);
	v_col = mix(green_col, body_col, v_dry) * (0.75 + 0.5 * UV.x) * (0.85 + 0.3 * h4);
}

void fragment() {
	float t = clamp(v_t, 0.0, 1.0);
	// Deep in the tussock it shades itself; its arched backs and tips take the light.
	vec3 c = mix(root_col, v_col, smoothstep(0.0, 0.45, t));
	c = mix(c, tip_col * (0.8 + 0.4 * v_col.r / max(body_col.r, 1e-3)), smoothstep(0.5, 1.0, t) * v_dry);
	ALBEDO = c;
	NORMAL = normalize((VIEW_MATRIX * vec4(0.0, 1.0, 0.0, 0.0)).xyz);
	ROUGHNESS = 0.8;
	SPECULAR = 0.35;
	BACKLIGHT = c * 0.4;
}
