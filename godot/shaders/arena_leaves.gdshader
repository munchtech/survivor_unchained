// Fallen leaves lying on an arena's litter (World/Grass.cs, Leaves): a scatter of
// leaves per cell on a jittered grid that wraps round the survivor, each lying
// flat and a little curled, rust, ochre and dead-pale, where the place's paint
// says the litter lies (its mask's R). From thirty metres up a photograph of
// litter averages into gravel; leaves a few pixels long, each its own colour and
// catching the light on its curl, read as leaves.
// COLOR.rg: the leaf's middle in its cell (0..1 over cell_span); COLOR.b: its own
// hash; UV.y: 0 at its edge, 1 on its curl's crown.
shader_type spatial;
render_mode cull_disabled, diffuse_burley, world_vertex_coords;

uniform sampler2D noise_tex : filter_linear_mipmap, repeat_enable;
uniform sampler2D splat : filter_linear_mipmap, repeat_disable;
uniform float zone_size = 300.0;
uniform float density = 1.0;
uniform float size = 1.0;
uniform float cell_span = 0.6;
// Linear colours: this year's rust, ochre, dead-pale, and old leaves gone dark.
uniform vec3 rust : source_color = vec3(0.24, 0.07, 0.02);
uniform vec3 ochre : source_color = vec3(0.3, 0.17, 0.04);
uniform vec3 pale : source_color = vec3(0.32, 0.25, 0.14);
uniform vec3 dark : source_color = vec3(0.06, 0.035, 0.02);
uniform vec2 centre = vec2(0.0);
uniform float span = 80.0;
uniform sampler2D heights : filter_linear, repeat_disable;
uniform float h_size = 300.0;
uniform float h_res = 300.0;

varying vec3 v_col;
varying float v_t;

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
	// (The cell is turned as it was laid: its leaves' middles with it.)
	vec2 mid = (MODEL_MATRIX * vec4((COLOR.r - 0.5) * cell_span, 0.0, (COLOR.g - 0.5) * cell_span, 0.0)).xz;
	float own = COLOR.b;
	vec2 lp = wp + mid;
	float paint = texture(splat, (lp + zone_size * 0.5) / zone_size).r;
	float drift = texture(noise_tex, lp * 0.09 + 0.3).g;
	// Thick in drifts, thin between them; none where the paint has none.
	float keep = step(own, paint * density * edge * (0.45 + 1.0 * drift));
	float s = size * (0.75 + 0.5 * gh(wp * 3.7 + own * 11.0)) * keep;
	vec3 rel = (off - vec3(mid.x, 0.0, mid.y)) * s;
	VERTEX = vec3(lp.x, ground_at(lp) + 0.012, lp.y) + rel;
	NORMAL = vec3(0.0, 1.0, 0.0);
	float h = gh(wp * 5.3 + own * 17.0);
	vec3 c = h < 0.35 ? mix(rust, ochre, h / 0.35) : h < 0.7 ? mix(ochre, pale, (h - 0.35) / 0.35) : mix(dark, rust, (h - 0.7) / 0.3);
	// Older underneath: darker where they lie thickest.
	v_col = c * (0.7 + 0.5 * gh(wp * 9.1 + own * 3.0)) * mix(1.0, 0.7, smoothstep(0.6, 1.0, paint * drift));
	v_t = UV.y;
}

void fragment() {
	// The curl's crown catches the light; the leaf's edges lie in its own shade.
	ALBEDO = v_col * mix(0.7, 1.15, v_t);
	ROUGHNESS = 0.6;
	SPECULAR = 0.4;
	NORMAL = normalize((VIEW_MATRIX * vec4(0.0, 1.0, 0.0, 0.0)).xyz);
}
