// Grass: the web game's blades (src/render/grass.ts), in Godot. One tapered
// blade, instanced on a jittered grid (World/Grass.cs); whether each grows,
// how tall, and its colour come from the ground's own paint and meadow
// photograph where it stands, so roots vanish into the ground; it leans in
// a travelling wind.
shader_type spatial;
render_mode cull_disabled, diffuse_burley;

uniform sampler2D noise_tex : filter_linear_mipmap, repeat_enable;
uniform sampler2D splat : filter_linear_mipmap, repeat_disable;
uniform sampler2DArray g_alb : source_color, filter_linear_mipmap, repeat_enable;
uniform float meadow_scale = 0.5;
uniform float zone_size = 290.0;
uniform float leaves = 0.3;
uniform float heal = 0.0;
uniform float density = 1.0;
uniform vec3 wind = vec3(1.0, 0.35, 1.0);
uniform vec4 pusher = vec4(0.0, 0.0, 0.0, 0.0);

varying float v_t;
varying vec3 v_tint;

float gh(vec2 p) { vec3 p3 = fract(vec3(p.xyx) * 0.1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }

void vertex() {
	vec2 wp = (MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xz;
	float h1 = gh(wp * 7.1), h3 = gh(wp * 3.3 + 11.0), h4 = gh(wp * 5.7 + 4.0);
	vec4 sp = texture(splat, (wp + zone_size * 0.5) / zone_size);
	sp.b *= 1.0 - heal * 0.85;
	vec4 nz = texture(noise_tex, wp * 0.035);
	float bare = max(max(sp.r, sp.g), max(sp.b, sp.a));
	float dens = 1.0 - smoothstep(0.12, 0.45, bare + (nz.g - 0.5) * 0.35);
	dens *= smoothstep(0.18, 0.5, nz.r + 0.22);
	float leafy = smoothstep(0.42, 0.78, texture(noise_tex, wp * 0.011).g * 0.7 + texture(noise_tex, wp * 0.061 + 0.37).a * 0.3 + leaves - 0.5);
	dens *= 1.0 - leafy * 0.5;
	float keep = step(h3, dens * density);
	float hgt = mix(0.32, 0.78, nz.b) * (0.65 + 0.7 * h4) * keep;
	float wid = 0.12 * (0.8 + 0.5 * h1) * keep;
	float t = VERTEX.y;
	v_t = t;
	vec3 p = vec3(VERTEX.x * wid, t * hgt, 0.0);
	// Wind: a slow travelling swell and gusts; the survivor parts it.
	float swell = sin(TIME * 1.6 + dot(wp, wind.xy) * 0.55 + nz.a * 5.0) * 0.5 + 0.5;
	float gust = texture(noise_tex, wp * 0.018 - TIME * vec2(0.035, 0.012)).r;
	vec2 bend = normalize(wind.xy) * (swell * 0.3 + gust * gust * 0.9) * wind.z;
	vec2 a = wp - pusher.xy;
	float pd = length(a);
	bend += (pd > 0.001 ? a / pd : vec2(0.0)) * (1.0 - smoothstep(0.0, pusher.z, pd)) * pusher.w * 1.6;
	float bl = min(length(bend), 1.4);
	bend = bl > 0.0 ? normalize(bend) * bl : vec2(0.0);
	// Into the blade's own frame (it is turned by its instance transform).
	mat3 inv = inverse(mat3(MODEL_MATRIX[0].xyz, MODEL_MATRIX[1].xyz, MODEL_MATRIX[2].xyz));
	vec3 lb = inv * vec3(bend.x, 0.0, bend.y);
	float tt = t * t;
	p.xz += lb.xz * tt * hgt;
	p.y -= bl * tt * hgt * 0.38;
	VERTEX = p;
	NORMAL = inv * vec3(0.0, 1.0, 0.0);
	// The meadow's colour, averaged over a hand's breadth, greener at the tip.
	vec3 g = textureLod(g_alb, vec3(wp * meadow_scale, 0.0), 5.0).rgb;
	g *= 0.8 + 0.2 * texture(noise_tex, wp * 0.011).r;
	v_tint = g * vec3(0.9, 1.2, 0.72) * (0.9 + 0.3 * h4);
}

void fragment() {
	// (Clamped: interpolation leaves the root a hair below zero, and pow of
	// a negative is NaN, which draws black.)
	float t = clamp(v_t, 0.0, 1.0);
	vec3 gb = v_tint * mix(0.62, 1.12, pow(t, 0.8));
	gb = mix(gb, gb * vec3(1.12, 1.08, 0.78), smoothstep(0.7, 1.0, t) * 0.5);
	ALBEDO = gb;
	// Both faces of a blade take the ground's normal: lit as the meadow is,
	// not half of it from below.
	NORMAL = normalize((VIEW_MATRIX * vec4(0.0, 1.0, 0.0, 0.0)).xyz);
	ROUGHNESS = 0.92;
	SPECULAR = 0.25;
	BACKLIGHT = gb * 0.35;
}
