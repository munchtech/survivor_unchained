// The Ford-Warden soaked (BossViews.WardenView, WardenLook.Wet): his baked package's own textures, drawn as distinct
// real materials, wet. His Meshy body is one atlas with one material, so what each texel is made of comes from his ID
// map (tools/assets/warden_id_map.py -> id_generated.png: R class*32 + quilting puff, G bind height, BA a detail
// normal): wool, tabard, quilting, leather, iron, badge, head. Each class has its own colour (the atlas's light and
// dark kept, its hue pulled to the class's), value, roughness, metal, specular and weave strength; the classes are
// blended over the 4 nearest texels so their edges don't step. Wetness is by height: soaked dark from the hem to the
// thigh, drier toward the shoulders. On top, the data map (tools/assets/warden_wet_maps.py: R silt, G occlusion,
// B beard, A face): a ragged silt tide line at the shins, the hood's inside dark, the face deep in it.
// iron = 1: the base's bare fingers inside his gauntlet drawn as the gauntlet's black river-grown iron.
shader_type spatial;
render_mode cull_disabled, depth_draw_opaque;

uniform sampler2D albedo_tex : source_color, filter_linear_mipmap_anisotropic, repeat_disable;
uniform sampler2D normal_tex : hint_normal, filter_linear_mipmap_anisotropic, repeat_disable;
uniform sampler2D mr_tex : hint_default_white, filter_linear_mipmap, repeat_disable; // glTF: G roughness, B metal
uniform sampler2D data_tex : hint_default_black, filter_linear, repeat_disable;
uniform sampler2D id_near : hint_default_black, filter_nearest, repeat_disable;     // the ID map, its classes
uniform sampler2D id_lin : hint_default_black, filter_linear_mipmap, repeat_disable; // the same, its height and detail
uniform bool has_normal = true;
uniform bool has_mr = true;
uniform bool has_id = false;
uniform float iron = 0.0;
uniform float debug_view = 0.0; // 1: the classes in flat colours (WARDEN_WET="debug_view=1")
// the classes (consts: Godot has no defaults on uniform arrays): 0 wool, 1 tabard, 2 quilting, 3 leather, 4 iron, 5 badge, 6 head
// colour (sRGB) the atlas's hue is pulled to (its light and dark kept), how far, then a value scale
// (r2, Warden 6 judge: the quilting a darker, greyer wet linen, matte; the iron's reflection neutral, not brass)
const vec3 cls_color[7] = { vec3(0.13, 0.145, 0.19), vec3(0.08, 0.20, 0.33), vec3(0.095, 0.092, 0.088), vec3(0.24, 0.13, 0.07),
	vec3(0.30, 0.30, 0.305), vec3(0.42, 0.38, 0.30), vec3(0.5, 0.45, 0.4) };
const float cls_colmix[7] = { 0.8, 0.85, 0.95, 0.25, 1.0, 0.5, 0.0 };
const float cls_value[7] = { 0.55, 1.1, 0.3, 0.85, 1.0, 0.4, 0.85 };
const float cls_rough[7] = { 0.88, 0.8, 0.9, 0.6, 0.42, 0.7, 0.7 };
const float cls_metal[7] = { 0.0, 0.0, 0.0, 0.0, 0.75, 0.0, 0.0 };
const float cls_spec[7] = { 0.15, 0.2, 0.1, 0.35, 0.5, 0.2, 0.2 };
const float cls_detail[7] = { 0.7, 0.55, 1.0, 0.35, 0.3, 0.3, 0.0 };   // the baked detail normal's strength
const float cls_wet[7] = { 1.0, 1.0, 1.0, 1.0, 0.5, 1.0, 0.0 };       // how much the soak shows
uniform float rough_var = 0.35;  // the atlas roughness's variation kept around the class's
// wet: the base pass everywhere (judged r2: wet_dark 0.9, wet_spec 0.15; its wet_rough 1.2 is now the classes'
// roughness), then the soak by height
uniform float wet_dark : hint_range(0.3, 1.0) = 0.9;     // cloth/leather base colour kept
uniform float wet_sat : hint_range(0.8, 1.6) = 1.12;     // wet colour is a touch richer
uniform float white_knee : hint_range(0.0, 8.0) = 2.5;   // pale paint compressed (no plaster-white): c / (1 + k c)
uniform float wet_spec : hint_range(0.0, 1.0) = 0.15;    // the cloth's specular floor
uniform float soak_lo = 0.55;    // bind height (m): soaked through below this
uniform float soak_hi = 1.25;    // ... drying to the damp floor above this
uniform float soak_floor = 0.15; // the shoulders' dampness
uniform float soak_dark = 0.6;   // the soaked cloth's colour kept
uniform float soak_rough = 0.72; // the soaked cloth's roughness scale
uniform float soak_spec = 0.32;  // the soaked cloth's specular
uniform float puff_lo = 0.4;     // the quilting's atlas normal per cell, x puff_lo .. puff_hi
uniform float puff_hi = 1.6;
uniform float quilt_flat = 0.7;     // how far the quilting's paint is flattened to its blur
uniform float quilt_atlas = 0.15;    // the sculpt's square waffle in the atlas normal, kept on the quilting (the baked channels lead)
uniform float quilt_rough_min = 0.8; // wet linen stays matte (no tight highlight even soaked)
// the iron's grime: dark against its blurred surroundings in the atlas (the crevices), dull and black-brown
uniform vec3 grime_color : source_color = vec3(0.035, 0.03, 0.026);
uniform float grime_amount : hint_range(0.0, 1.0) = 0.85;
uniform float grime_from = 0.05;
uniform float grime_to = 0.35;
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
		// the class weights: the 4 nearest ID texels, bilinear
		float wc[7] = { 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 };
		float puff = 0.5;
		vec4 idl = vec4(0.0, 0.5, 0.5, 0.5);
		if (has_id) {
			vec2 sz = vec2(textureSize(id_near, 0));
			vec2 q = UV * sz - 0.5;
			ivec2 i0 = ivec2(floor(q));
			vec2 f = fract(q);
			ivec2 mx = ivec2(sz) - 1;
			puff = 0.0;
			for (int k = 0; k < 4; k++) {
				ivec2 o = ivec2(k & 1, k >> 1);
				float r = texelFetch(id_near, clamp(i0 + o, ivec2(0), mx), 0).r * 255.0 + 0.5;
				float w = (o.x == 1 ? f.x : 1.0 - f.x) * (o.y == 1 ? f.y : 1.0 - f.y);
				int c = clamp(int(r / 32.0), 0, 6);
				wc[c] += w;
				puff += w * mod(floor(r), 32.0) / 31.0;
			}
			idl = texture(id_lin, UV);
		} else {
			wc[0] = 1.0;
		}
		vec3 ccol = vec3(0.0);
		float cmix = 0.0, cval = 0.0, crough = 0.0, cmetal = 0.0, cspec = 0.0, cdet = 0.0, cwet = 0.0;
		for (int c = 0; c < 7; c++) {
			ccol += wc[c] * pow(cls_color[c], vec3(2.2));
			cmix += wc[c] * cls_colmix[c];
			cval += wc[c] * cls_value[c];
			crough += wc[c] * cls_rough[c];
			cmetal += wc[c] * cls_metal[c];
			cspec += wc[c] * cls_spec[c];
			cdet += wc[c] * cls_detail[c];
			cwet += wc[c] * cls_wet[c];
		}
		// the class's colour: the atlas's light and dark, its hue pulled to the class's
		float la = dot(a, LUM);
		float la_b = max(dot(textureLod(albedo_tex, UV, 3.0).rgb, LUM), 1e-4);
		// (the quilting: its pale paint blotches flattened toward their surroundings, wet linen is even)
		float la_q = mix(la, max(dot(textureLod(albedo_tex, UV, 5.0).rgb, LUM), 1e-4), quilt_flat * wc[2]);
		vec3 b = mix(a * (la_q / max(la, 1e-4)), ccol * (la_q / max(dot(ccol, LUM), 1e-4)), cmix) * cval;
		// the soak by height: through below the thigh, damp toward the shoulders
		float hy = idl.g * 2.0;
		float soak = has_id ? mix(soak_floor, 1.0, 1.0 - smoothstep(soak_lo, soak_hi, hy)) * cwet : 0.0;
		// wet: darker, a touch richer, the pale paint compressed
		vec3 w = b * wet_dark * mix(1.0, soak_dark, soak);
		w = max(mix(vec3(dot(w, LUM)), w, mix(1.0, wet_sat, soak * (1.0 - wc[4]))), vec3(0.0));
		w = w / (1.0 + white_knee * w);
		float rough = clamp(crough + (mr.g - 0.6) * rough_var, 0.3, 0.97);
		rough = clamp(mix(rough, rough * soak_rough, soak), 0.3, 0.95);
		float spec = mix(max(cspec, wet_spec), max(cspec, soak_spec), soak);
		// the quilting: matte however soaked
		rough = mix(rough, max(rough, quilt_rough_min), wc[2]);
		spec = mix(spec, cspec, wc[2]);
		// the iron's crevices: grime (dark in the atlas against its blurred surroundings), dull, not metal
		float grime = smoothstep(grime_from, grime_to, (la_b - la) / la_b) * wc[4] * grime_amount;
		w = mix(w, grime_color, grime);
		rough = mix(rough, 0.92, grime);
		spec = mix(spec, 0.2, grime);
		// the beard: darker again, ropey wet sheen
		w *= mix(1.0, beard_dark, d.b);
		rough = mix(rough, beard_rough, d.b);
		// deep in the hood: the face mostly lost, the hood's inside dark
		float occ = smoothstep(occ_from, occ_to, d.g);
		w *= mix(1.0, occ_dark, occ) * mix(1.0, face_dark, d.a);
		spec *= mix(1.0, 0.35, max(occ, d.a));
		// the silt: below the tide line the cloth dries dull and pale with river mud, the line itself a dark band
		float silt = d.r * silt_amount;
		float band = clamp(d.r * (1.0 - d.r) * 4.0, 0.0, 1.0);
		band = band * band * band_amount;
		w = mix(w, mix(vec3(dot(w, LUM)), w, 0.5) * 0.6 + silt_color * 0.4, silt);
		rough = mix(rough, 0.9, d.r);
		spec = mix(spec, 0.3, d.r);
		w = mix(w, band_color, band);
		ALBEDO = w;
		METALLIC = cmetal * (1.0 - grime);
		ROUGHNESS = rough;
		SPECULAR = spec;
		// the atlas's normal (the quilting's puffs each their own height) + the class's baked weave/grain/dents
		vec2 nxy = vec2(0.0);
		if (has_normal) nxy = texture(normal_tex, UV).rg * 2.0 - 1.0;
		nxy *= mix(1.0, mix(puff_lo, puff_hi, puff) * quilt_atlas, wc[2]);
		nxy += (idl.ba * 2.0 - 1.0) * cdet;
		vec3 n = normalize(vec3(nxy, 1.0));
		NORMAL_MAP = n * 0.5 + 0.5;
		if (debug_view > 0.5) {
			const vec3 PAL[7] = { vec3(0.16, 0.16, 0.24), vec3(0.16, 0.35, 0.9), vec3(0.78, 0.67, 0.35), vec3(0.6, 0.27, 0.12),
				vec3(0.67, 0.7, 0.75), vec3(1.0), vec3(0.9, 0.47, 0.67) };
			vec3 dc = vec3(0.0);
			for (int c = 0; c < 7; c++) dc += wc[c] * PAL[c];
			ALBEDO = vec3(0.0); EMISSION = pow(dc, vec3(2.2)) * (has_id ? 1.0 : 0.2); ROUGHNESS = 1.0; SPECULAR = 0.0; METALLIC = 0.0;
		}
	}
}
