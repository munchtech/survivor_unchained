// The Ford-Warden's face (WardenLook key "face": his Face Forge head, materials warden_face and warden_face_lod), soaked.
// The head's texture is a portrait projected on it, its own front light baked in: in a night shot that read as a lit
// photo pasted on a dark body. Here: the portrait's low-frequency shading taken out (the data map's R, fitted on the
// surface by tools/assets/warden_face_maps.py), the colour pulled to a cold pale grey and down in value, the stubble
// and buzz cut's dark specks made the beard's grey, and the river on it: glossy on the brow ridge, nose, cheekbones,
// lower lids and lips (G 0..0.8), the creases duller (B), the eyes glassy (G 0.8..1), the hair zones (A).
// The LOD has no data map (has_data false): the grade only.
shader_type spatial;
render_mode cull_back, depth_draw_opaque;

uniform sampler2D albedo_tex : source_color, filter_linear_mipmap_anisotropic, repeat_disable;
uniform sampler2D normal_tex : hint_normal, filter_linear_mipmap_anisotropic, repeat_disable;
uniform sampler2D face_data : hint_default_black, filter_linear_mipmap, repeat_disable;
uniform bool has_normal = true;
uniform bool has_data = false;
uniform float debug_view = 0.0;   // 1: the data map (R de-light, G wet/eyes, B creases) as flat colour; 2: A hair zones
// the grade: cold pale grey, low
uniform float face_value : hint_range(0.0, 2.0) = 0.25;
uniform float face_sat : hint_range(0.0, 1.0) = 0.45;
uniform vec3 face_tint : source_color = vec3(0.88, 0.93, 1.0);
uniform float white_knee : hint_range(0.0, 8.0) = 2.5;    // pale paint compressed: c / (1 + k c)
uniform float delight : hint_range(0.0, 1.5) = 1.0;       // how much of the map's de-light is applied
// stubble / buzz cut: dark specks against their surroundings (a blurred mip) lifted to the beard's grey
uniform float speck_mip = 4.0;
uniform float speck_from = 0.05;
uniform float speck_to = 0.3;
uniform float speck_amount : hint_range(0.0, 1.0) = 1.0;
uniform float hair_grey = 1.25;
uniform float hair_cover : hint_range(0.0, 1.0) = 0.65; // the hair zones evened to their grey (dense stubble blurs dark too)    // the grey, against the blurred surroundings' luminance
// wet
uniform float skin_rough = 0.55;
uniform float wet_rough = 0.3;
uniform float crease_rough = 0.5;
uniform float eye_rough = 0.05;
uniform float wet_dark : hint_range(0.5, 1.0) = 0.85;
uniform float crease_dark : hint_range(0.3, 1.0) = 0.75;
uniform float eye_dark : hint_range(0.2, 1.0) = 0.6;
uniform float skin_spec = 0.35;
uniform float wet_spec = 0.45;
uniform float eye_spec = 0.7;
// his lamp, under the hood (Warden 6 r3): the hood shades the face from the sky, so at his closest camera (C03 s1) the
// face went black. The lamp he carries lights it from below and in front: a fill toward the camera and down, wrapped
// so the nose, cheekbone fronts, lower lids and brow underside take it and the forehead (facing up) does not, and the
// wet eyes catch it as a small hard highlight. Emitted, so the hood's shadow does not take it out.
uniform vec3 lamp_colour : source_color = vec3(0.62, 0.80, 1.0);
uniform float lamp_on : hint_range(0.0, 1.0) = 1.0;      // BossViews: his lamp lit (0 when it is out)
uniform float lamp_fill : hint_range(0.0, 8.0) = 4.0;
uniform float lamp_down : hint_range(0.0, 2.0) = 0.9;      // how far below the view line the lamp sits
uniform float lamp_power : hint_range(0.5, 8.0) = 3.0;     // the falloff across the face (higher: only what faces it)
uniform float lamp_glint : hint_range(0.0, 8.0) = 4.0;     // the eyes' highlight
uniform float lamp_glint_power = 80.0;
uniform float lamp_wet_glint : hint_range(0.0, 4.0) = 0.3; // the wet skin's (nose tip, cheekbones, lids) small sheen

const vec3 LUM = vec3(0.2126, 0.7152, 0.0722);

void fragment() {
	vec3 a = texture(albedo_tex, UV).rgb;
	vec4 d = has_data ? texture(face_data, UV) : vec4(0.5, 0.0, 0.0, 0.0);
	float wet = clamp(d.g / 0.8, 0.0, 1.0);
	float eye = clamp((d.g - 0.8) / 0.2, 0.0, 1.0);
	float crease = d.b;
	// stubble: dark against its blurred surroundings, in the hair zones
	vec3 ab = textureLod(albedo_tex, UV, speck_mip).rgb;
	float l = dot(a, LUM), lb = max(dot(ab, LUM), 1e-4);
	float speck = smoothstep(speck_from, speck_to, (lb - l) / lb) * d.a * speck_amount;
	a = mix(a, vec3(lb * hair_grey), max(speck, d.a * hair_cover));
	// de-light, then the cold grade
	a *= mix(1.0, d.r * 2.0, delight * (has_data ? 1.0 : 0.0));
	float la = dot(a, LUM);
	a = mix(vec3(la), a, face_sat) * face_tint * face_value;
	a *= mix(1.0, wet_dark, wet) * mix(1.0, crease_dark, crease) * mix(1.0, eye_dark, eye);
	a = a / (1.0 + white_knee * a);
	ALBEDO = a;
	float rough = mix(skin_rough, wet_rough, wet);
	rough = mix(rough, crease_rough, crease);
	ROUGHNESS = mix(rough, eye_rough, eye);
	SPECULAR = mix(mix(skin_spec, wet_spec, wet), eye_spec, eye);
	METALLIC = 0.0;
	if (has_normal) NORMAL_MAP = texture(normal_tex, UV).rgb;
	if (lamp_fill > 0.0 || lamp_glint > 0.0) {
		vec3 down = normalize((VIEW_MATRIX * vec4(0.0, -1.0, 0.0, 0.0)).xyz);
		vec3 L = normalize(VIEW + lamp_down * down);
		vec3 n = NORMAL;
		if (has_normal) {
			vec3 t = texture(normal_tex, UV).rgb * 2.0 - 1.0;
			n = normalize(TANGENT * t.x + BINORMAL * t.y + NORMAL * t.z);
		}
		float w = pow(clamp(dot(n, L), 0.0, 1.0), lamp_power);
		vec3 h = normalize(L + VIEW);
		float g = pow(clamp(dot(n, h), 0.0, 1.0), lamp_glint_power);
		EMISSION = lamp_on * lamp_colour * (a * lamp_fill * w + g * (lamp_glint * eye + lamp_wet_glint * wet * (1.0 - eye)));
	}
	if (debug_view > 0.5) {
		vec3 dc = debug_view > 1.5 ? vec3(d.a) : vec3(d.r * 2.0 - 0.5, d.g, d.b);
		ALBEDO = vec3(0.0); EMISSION = dc * 0.6; ROUGHNESS = 1.0; SPECULAR = 0.0;
	}
}
