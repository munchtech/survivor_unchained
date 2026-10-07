// The kits' pieces as the web game shades them (src/render/env.ts's weather,
// src/render/flora.ts's kit look): the bright, clean kit paint pulled toward
// this country's grey and dark, foliage recoloured to its kind (autumn, the
// blight), moss on what faces up, each copy a little different, and wind in
// what grows. For MultiMesh copies, each copy's origin is its own.
//
// What stands between the camera and the survivor opens round her in a soft
// round window (see_through below). The piece itself is cut there, and its
// feathered rim is drawn again, translucent, by this material's next pass
// (KitLook: the same code with REVEAL defined, blended).
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

// Where the survivor is (her chest, xyz; w = 1 in a fight: WorldScene sets it
// each frame), and where the game's camera is (xyz; w = 1 in play: Game sets
// it each frame). The window is made only in the camera's own view: in a
// light's (its shadows) the piece is whole, so a tree opened for her still
// casts all of its shadow.
global uniform vec4 survivor;
global uniform vec4 view_from;

varying float v_up;
varying float v_jit;
varying float v_y;

const vec3 LW = vec3(0.2126, 0.7152, 0.0722);

// How much of the piece is kept at this point of it (1 all, 0 none): a round
// window round her, wide enough for all of her, clear in its middle and
// feathered over its outer metre, measured on the screen in metres at her
// distance (so it is round, and the same at every zoom). Only what stands
// nearer the camera than she does, and above her ankles (never the floor at
// her feet), is opened, each eased in, so no line is drawn across a piece she
// stands in: a point only partly in the way has a smaller window, never a
// fainter one, so the window is always clear and only its rim is see-through
// (a piece drawn faint across the window, on the rim's translucent pass, lost
// its shading and stood pale in it: a roof's underside, a gable).
float see_through(vec3 vpos, mat4 view, mat4 inv_view, mat4 proj, vec3 cam) {
	// (A light's view stands far from the camera's: a lamp's at most a few metres up, the sun's far off.)
	if (survivor.w <= 0.0 || view_from.w <= 0.0 || distance(cam, view_from.xyz) > 1.0) return 1.0;
	vec3 her = (view * vec4(survivor.xyz, 1.0)).xyz;
	float front = smoothstep(0.3, 1.3, vpos.z - her.z);
	float above = smoothstep(0.25, 0.7, (inv_view * vec4(vpos, 1.0)).y - (survivor.y - 1.1));
	float open = front * above;
	if (open <= 0.0) return 1.0;
	vec4 a = proj * vec4(vpos, 1.0);
	vec4 b = proj * vec4(her, 1.0);
	vec2 d = a.xy / a.w - b.xy / b.w;
	// (The projection's own scales, not their signs: Vulkan's is flipped in y, and a
	// negative distance opened all that stands before her, at any distance.)
	float fy = abs(proj[1][1]);
	d.x *= fy / abs(proj[0][0]);
	float metres = length(d) * -her.z / fy;
	return smoothstep(1.45 * open, 2.5 * open, metres);
}

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
#ifdef REVEAL
	// The rim is drawn again only for a piece near the line from her to the
	// camera (within 14 m of it on the ground); every other copy is put out of
	// view whole, so the second pass costs next to nothing.
	vec2 s = survivor.xz, c = view_from.xz, o = ip.xz;
	vec2 sc = c - s;
	float t = clamp(dot(o - s, sc) / max(dot(sc, sc), 1e-4), 0.0, 1.0);
	bool near_line = survivor.w > 0.0 && view_from.w > 0.0 && distance(o, s + sc * t) < 14.0;
	POSITION = near_line ? PROJECTION_MATRIX * (MODELVIEW_MATRIX * vec4(VERTEX, 1.0)) : vec4(2.0, 2.0, 2.0, 1.0);
#endif
}

void fragment() {
	float kept = see_through(VERTEX, VIEW_MATRIX, INV_VIEW_MATRIX, PROJECTION_MATRIX, CAMERA_POSITION_WORLD);
#ifdef REVEAL
	// Only the feathered rim (the piece's whole part is drawn by the first pass).
	if (kept >= 0.999 || kept <= 0.004) discard;
#else
	if (kept < 0.999) discard;
#endif
	vec4 c = texture(albedo_tex, UV) * albedo_color;
	if (use_vcolor) c *= COLOR;
#ifdef REVEAL
	if (alpha_scissor > 0.0 && c.a < alpha_scissor) discard;
	ALPHA = kept;
#else
	if (alpha_scissor > 0.0) {
		ALPHA = c.a;
		ALPHA_SCISSOR_THRESHOLD = alpha_scissor;
	}
#endif
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
