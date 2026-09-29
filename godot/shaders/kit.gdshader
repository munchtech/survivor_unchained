// The kits' pieces as the web game shades them (src/render/env.ts's weather,
// src/render/flora.ts's kit look): the bright, clean kit paint pulled toward
// this country's grey and dark, foliage recoloured to its kind (autumn, the
// blight), moss on what faces up, each copy a little different, and wind in
// what grows. For MultiMesh copies, each copy's origin is its own.
shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;

uniform sampler2D albedo_tex : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform vec4 albedo_color : source_color = vec4(1.0);
uniform bool use_vcolor = false;
uniform bool use_normal = false;
uniform sampler2D normal_tex : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform float roughness = 0.9;
uniform float alpha_scissor = 0.0;
uniform float wind = 0.0;
uniform float weather_sat = 0.82;
uniform vec3 weather_tint = vec3(0.88, 0.87, 0.85);
uniform vec4 recolor_a = vec4(0.0);  // rgb, amount
uniform vec3 recolor_b = vec3(0.0);
uniform float moss = 0.0;
uniform float jitter = 0.08;
// The village kit's walls darken toward their foot (splash, damp, dirt).
uniform bool foot = false;

// Where the survivor is (xyz; w = 1 when there is one): what stands between
// them and the camera is cut away (Fight.cs sets it each frame).
global uniform vec4 survivor;

varying float v_up;
varying float v_jit;
varying float v_y;

// 4x4 ordered dither: a fade the temporal AA resolves to translucency.
float bayer(vec2 p) {
	ivec2 q = ivec2(mod(floor(p), 4.0));
	int i = q.x + q.y * 4;
	int[16] m = int[](0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5);
	return (float(m[i]) + 0.5) / 16.0;
}

const vec3 LW = vec3(0.2126, 0.7152, 0.0722);

void vertex() {
	vec3 ip = MODEL_MATRIX[3].xyz;
	v_up = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz).y;
	v_jit = fract(sin(dot(ip.xz, vec2(12.9898, 78.233))) * 43758.5453);
	v_y = VERTEX.y;
	float h = max(VERTEX.y, 0.0);
	float ph = TIME * 1.1 + ip.x * 0.23 + ip.z * 0.19;
	float sway = (sin(ph) * 0.65 + sin(ph * 2.3 + 1.7) * 0.25 + sin(ph * 5.1 + ip.x) * 0.1) * wind * h * h * 0.02;
	VERTEX.x += sway;
	VERTEX.z += sway * 0.5;
}

void fragment() {
	if (survivor.w > 0.0) {
		// A tunnel from the camera to the survivor, wider at their end.
		vec3 wp = (INV_VIEW_MATRIX * vec4(VERTEX, 1.0)).xyz;
		vec3 cam = CAMERA_POSITION_WORLD;
		vec3 d = survivor.xyz - cam;
		float len = length(d);
		vec3 dir = d / len;
		float t = dot(wp - cam, dir);
		if (t < len - 1.0) {
			float r = length((wp - cam) - dir * t);
			float radius = mix(1.2, 3.4, clamp(t / len, 0.0, 1.0));
			float fade = (1.0 - smoothstep(radius * 0.7, radius, r)) * 0.94;
			if (bayer(FRAGCOORD.xy) < fade) discard;
		}
	}
	vec4 c = texture(albedo_tex, UV) * albedo_color;
	if (use_vcolor) c *= COLOR;
	if (alpha_scissor > 0.0) {
		ALPHA = c.a;
		ALPHA_SCISSOR_THRESHOLD = alpha_scissor;
	}
	float l = dot(c.rgb, LW);
	vec3 col = mix(vec3(l), c.rgb, weather_sat) * weather_tint;
	vec3 rc = mix(recolor_a.rgb, recolor_b, v_jit);
	float lt = dot(col, LW);
	col = mix(col, rc * (lt / max(dot(rc, LW), 0.05)), recolor_a.a);
	col = mix(col, vec3(0.2, 0.3, 0.12) * (0.55 + lt), moss * smoothstep(0.45, 0.85, v_up));
	col *= 1.0 - jitter + 2.0 * jitter * v_jit;
	if (foot) col *= mix(0.6, 1.0, smoothstep(0.0, 1.3, v_y));
	ALBEDO = col;
	ROUGHNESS = roughness;
	if (use_normal) NORMAL_MAP = texture(normal_tex, UV).rgb;
}
