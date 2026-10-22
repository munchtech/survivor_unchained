// The Ford-Warden soaked (BossViews.WardenView, WardenLook.Wet): his baked package's own textures, drawn wet.
// Cloth, leather and beard 35-45% darker with a wet sheen (lower roughness, a little specular); metal stays metal;
// the hood's inside and the face deep in it go dark (the face mostly lost, the beard catching the light); a ragged
// silt tide line at the shins with silt-dulled cloth below it. Where things are comes from his data map
// (tools/assets/warden_wet_maps.py: R silt, G occlusion, B beard, A face, in the surface's own UVs).
// iron = 1: the base's bare fingers inside his gauntlet drawn as the gauntlet's black river-grown iron.
shader_type spatial;
render_mode cull_disabled, depth_draw_opaque;

uniform sampler2D albedo_tex : source_color, filter_linear_mipmap_anisotropic, repeat_disable;
uniform sampler2D normal_tex : hint_normal, filter_linear_mipmap_anisotropic, repeat_disable;
uniform sampler2D mr_tex : hint_default_white, filter_linear_mipmap, repeat_disable; // glTF: G roughness, B metal
uniform sampler2D data_tex : hint_default_black, filter_linear, repeat_disable;
uniform bool has_normal = true;
uniform bool has_mr = true;
uniform float iron = 0.0;
// wet
uniform float wet_dark : hint_range(0.3, 1.0) = 0.6;     // cloth/leather base colour kept (0.6: 40% darker)
uniform float wet_sat : hint_range(0.8, 1.6) = 1.12;     // wet colour is a touch richer
uniform float white_knee : hint_range(0.0, 8.0) = 2.5;   // pale paint compressed (no plaster-white): c / (1 + k c)
uniform float wet_rough : hint_range(0.2, 1.0) = 0.62;   // roughness scale on the wet cloth
uniform float wet_spec : hint_range(0.0, 1.0) = 0.55;
uniform float beard_dark : hint_range(0.2, 1.0) = 0.62;  // the beard on top of the wet pass
uniform float beard_rough = 0.32;
// shadow in the hood
uniform float face_dark : hint_range(0.0, 1.0) = 0.22;   // the face's base colour kept, deep in the hood
uniform float occ_dark : hint_range(0.0, 1.0) = 0.45;    // at full occlusion (the hood's inside)
uniform float occ_from = 0.8;
uniform float occ_to = 1.0;
// silt tide line
uniform float silt_amount : hint_range(0.0, 1.0) = 0.55;
uniform vec3 silt_color : source_color = vec3(0.30, 0.27, 0.22);
uniform vec3 band_color : source_color = vec3(0.10, 0.085, 0.065);
uniform float band_amount : hint_range(0.0, 1.0) = 0.75;
// iron
uniform vec3 iron_color : source_color = vec3(0.075, 0.075, 0.08);
uniform vec3 rust_color : source_color = vec3(0.22, 0.12, 0.06);

const vec3 LUM = vec3(0.2126, 0.7152, 0.0722);

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float vnoise(vec2 p) {
	vec2 i = floor(p), f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), f.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), f.x), f.y);
}

void fragment() {
	if (iron > 0.5) {
		// black iron, a little rust and silt in it, satin where it is worn
		float n = vnoise(UV * 90.0) * 0.6 + vnoise(UV * 310.0) * 0.4;
		float rust = smoothstep(0.62, 0.8, vnoise(UV * 55.0 + 7.0));
		ALBEDO = mix(iron_color * (0.8 + 0.4 * n), rust_color, rust * 0.55);
		METALLIC = mix(0.85, 0.2, rust);
		ROUGHNESS = mix(0.42 + 0.2 * n, 0.85, rust);
		SPECULAR = 0.5;
	} else {
		vec3 a = texture(albedo_tex, UV).rgb;
		vec4 mr = has_mr ? texture(mr_tex, UV) : vec4(1.0, 0.8, 0.0, 1.0);
		vec4 d = texture(data_tex, UV);
		float metal = smoothstep(0.35, 0.65, mr.b);
		// wet: darker, a touch richer, the pale paint compressed
		vec3 w = a * wet_dark;
		w = max(mix(vec3(dot(w, LUM)), w, wet_sat), vec3(0.0));
		w = w / (1.0 + white_knee * w);
		float rough = clamp(mr.g * wet_rough, 0.24, 0.75);
		// the beard: darker again, ropey wet sheen
		w *= mix(1.0, beard_dark, d.b);
		rough = mix(rough, beard_rough, d.b);
		// deep in the hood: the face mostly lost, the hood's inside dark
		float occ = smoothstep(occ_from, occ_to, d.g);
		w *= mix(1.0, occ_dark, occ) * mix(1.0, face_dark, d.a);
		float spec = wet_spec * mix(1.0, 0.35, max(occ, d.a));
		// the silt: below the tide line the cloth dries dull and pale with river mud, the line itself a dark band
		float silt = d.r * silt_amount;
		float band = clamp(d.r * (1.0 - d.r) * 4.0, 0.0, 1.0);
		band = band * band * band_amount;
		w = mix(w, mix(vec3(dot(w, LUM)), w, 0.5) * 0.6 + silt_color * 0.4, silt);
		rough = mix(rough, 0.9, d.r);
		spec = mix(spec, 0.3, d.r);
		w = mix(w, band_color, band);
		// metal keeps its own paint and finish
		ALBEDO = mix(w, a, metal);
		METALLIC = has_mr ? mr.b : 0.0;
		ROUGHNESS = mix(rough, mr.g, metal);
		SPECULAR = mix(spec, 0.5, metal);
		if (has_normal) NORMAL_MAP = texture(normal_tex, UV).rgb;
	}
}
