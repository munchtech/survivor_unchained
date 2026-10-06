// Grass: the web game's blades (src/render/grass.ts), in Godot. One tapered
// blade, instanced on a jittered grid (World/Grass.cs); whether each grows,
// how tall, and its colour come from the ground's own paint and meadow
// photograph where it stands, so roots vanish into the ground; it leans in
// a travelling wind.
shader_type spatial;
render_mode cull_disabled, diffuse_burley, world_vertex_coords;

uniform sampler2D noise_tex : filter_linear_mipmap, repeat_enable;
uniform sampler2D splat : filter_linear_mipmap, repeat_disable;
uniform sampler2DArray g_alb : source_color, filter_linear_mipmap, repeat_enable;
uniform float meadow_scale = 0.5;
uniform float zone_size = 290.0;
uniform float leaves = 0.3;
uniform float heal = 0.0;
uniform float density = 1.0;
// A place's own grass (an ember arena's): its colour against the ground's,
// its value, and how much of it has gone to straw.
uniform vec3 tint = vec3(0.9, 1.2, 0.72);
uniform float tone = 1.0;
uniform float straw_bias = 0.0;
uniform vec3 straw_color = vec3(0.24, 0.21, 0.11);
uniform float straw_mix = 0.3;
uniform vec3 wind = vec3(1.0, 0.35, 1.0);
uniform vec4 pusher = vec4(0.0, 0.0, 0.0, 0.0);
// The grid wraps round `centre` every `span` metres; heights from the zone's.
uniform vec2 centre = vec2(0.0);
uniform float span = 80.0;
uniform sampler2D heights : filter_linear, repeat_disable;
uniform float h_size = 290.0;
uniform float h_res = 256.0;
// Where nothing grows (a fire's pit): x, z and radius; radius 0 is unused.
uniform vec4 bare_at[4];

varying float v_t;
varying vec3 v_tint;
varying float v_dry;

float gh(vec2 p) { vec3 p3 = fract(vec3(p.xyx) * 0.1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }

float ground_at(vec2 p) {
	vec2 f = clamp((p + h_size * 0.5) / h_size * (h_res - 1.0), vec2(0.0), vec2(h_res - 1.0));
	return textureLod(heights, (f + 0.5) / h_res, 0.0).r;
}

void vertex() {
	// Where the tuft's root was laid, and the copy of it nearest the centre.
	vec3 root = MODEL_MATRIX[3].xyz;
	vec3 off = VERTEX - root;
	vec2 wp = root.xz + span * round((centre - root.xz) / span);
	float edge = 1.0 - smoothstep(span * 0.36, span * 0.5, length(wp - centre));
	float h1 = gh(wp * 7.1), h3 = gh(wp * 3.3 + 11.0), h4 = gh(wp * 5.7 + 4.0);
	vec4 sp = texture(splat, (wp + zone_size * 0.5) / zone_size);
	sp.b *= 1.0 - heal * 0.85;
	vec4 nz = texture(noise_tex, wp * 0.035);
	float bare = max(max(sp.r, sp.g), max(sp.b, sp.a));
	// None on setts, mud or blight; over trodden earth it thins rather than
	// stopping at the edge.
	float hard = max(sp.g, max(sp.b, sp.a));
	float dens = (1.0 - smoothstep(0.12, 0.45, hard + (nz.g - 0.5) * 0.35))
		* (1.0 - smoothstep(0.15, 0.8, sp.r + (nz.g - 0.5) * 0.35) * 0.85);
	dens *= smoothstep(0.18, 0.5, nz.r + 0.22);
	float leafy = smoothstep(0.42, 0.78, texture(noise_tex, wp * 0.011).g * 0.7 + texture(noise_tex, wp * 0.061 + 0.37).a * 0.3 + leaves - 0.5);
	dens *= 1.0 - leafy * 0.5;
	float keep = step(h3, dens * density * edge);
	for (int i = 0; i < 4; i++) keep *= step(bare_at[i].z, length(wp - bare_at[i].xy));
	// Shorter than a meadow: the fight is read through it from above.
	float hgt = mix(0.22, 0.5, nz.b) * (0.75 + 0.5 * h4) * keep;
	float wid = (0.85 + 0.4 * h1) * keep;
	float t = clamp(off.y / 1.2, 0.0, 1.0);
	v_t = t;
	vec3 p = vec3(off.x * wid, off.y * hgt, off.z * wid);
	// Wind: a slow travelling swell and gusts; the survivor parts it.
	float swell = sin(TIME * 1.6 + dot(wp, wind.xy) * 0.55 + nz.a * 5.0) * 0.5 + 0.5;
	float gust = texture(noise_tex, wp * 0.018 - TIME * vec2(0.035, 0.012)).r;
	vec2 bend = normalize(wind.xy) * (swell * 0.3 + gust * gust * 0.9) * wind.z;
	vec2 a = wp - pusher.xy;
	float pd = length(a);
	bend += (pd > 0.001 ? a / pd : vec2(0.0)) * (1.0 - smoothstep(0.0, pusher.z, pd)) * pusher.w * 1.6;
	float bl = min(length(bend), 1.4);
	bend = bl > 0.0 ? normalize(bend) * bl : vec2(0.0);
	float tt = t * t;
	p.xz += bend * tt * hgt;
	p.y -= bl * tt * hgt * 0.38;
	VERTEX = vec3(wp.x, ground_at(wp) - 0.02, wp.y) + p;
	NORMAL = vec3(0.0, 1.0, 0.0);
	// The meadow's colour, averaged over a hand's breadth, greener at the tip.
	vec3 g = textureLod(g_alb, vec3(wp * meadow_scale, 0.0), 5.0).rgb;
	g *= 0.8 + 0.2 * texture(noise_tex, wp * 0.011).r;
	// Each blade its own shade; patches gone to straw over tens of metres.
	v_tint = g * tint * tone * (0.78 + 0.4 * UV2.x) * (0.9 + 0.25 * h4);
	v_dry = clamp(smoothstep(0.45, 0.75, texture(noise_tex, wp * 0.02 + 5.3).g) * (0.6 + 0.4 * h1) + straw_bias, 0.0, 1.0);
}

void fragment() {
	// (Clamped: interpolation leaves the root a hair below zero, and pow of
	// a negative is NaN, which draws black.)
	float t = clamp(v_t, 0.0, 1.0);
	vec3 gb = v_tint * mix(0.32, 1.15, pow(t, 0.7));
	gb = mix(gb, gb * vec3(1.12, 1.08, 0.78), smoothstep(0.7, 1.0, t) * 0.5);
	// Straw: dry grass, paler and warmer, toward the tip most.
	vec3 straw = straw_color * mix(0.4, 1.0, t);
	gb = mix(gb, straw, v_dry * straw_mix);
	ALBEDO = gb;
	// Both faces of a blade take the ground's normal: lit as the meadow is,
	// not half of it from below.
	NORMAL = normalize((VIEW_MATRIX * vec4(0.0, 1.0, 0.0, 0.0)).xyz);
	ROUGHNESS = 0.92;
	SPECULAR = 0.25;
	BACKLIGHT = gb * 0.35;
}
