// The Ford-Warden soaked (BossViews.WardenView, WardenLook.Wet): his baked package's own textures, drawn as distinct
// real materials, wet. His Meshy body is one atlas with one material, so what each texel is made of comes from his ID
// map (tools/assets/warden_id_map.py -> id_generated.png: R class*32 + the quilting's loft, G bind height, BA a detail
// normal): wool, tabard, quilting, leather, iron, badge, head. Each class has its own colour (the atlas's light and
// dark kept, its hue pulled to the class's), value, roughness, metal, specular and weave strength; the classes are
// blended over the 4 nearest texels so their edges don't step. Wetness is by height: soaked dark from the hem to the
// thigh, drier toward the shoulders. On top, the data map (tools/assets/warden_wet_maps.py: R silt, G occlusion,
// B the beard's drip, A wet streaks: warden_id_map.py's body_extras(); the old TRELLIS head's beard and face are gone):
// a ragged silt tide line at the shins, the hood's inside dark, the beard's drip on the tabard, wet runs on the iron.
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
// (Warden 7, the garment: its inside drawn as the same wool, a touch darker; wool's grazing sheen, no plastic spec)
uniform float value_mul = 1.0;
uniform float wool_sheen = 0.0;
uniform float wool_sheen_tint = 0.35;
uniform float debug_view = 0.0; // 1: the classes in flat colours (WARDEN_WET="debug_view=1")
// the classes (consts: Godot has no defaults on uniform arrays): 0 wool, 1 tabard, 2 quilting, 3 leather, 4 iron, 5 badge, 6 head
// colour (sRGB) the atlas's hue is pulled to (its light and dark kept), how far, then a value scale
// (r2, Warden 6 judge: the quilting a darker, greyer wet linen, matte; the iron's reflection neutral, not brass)
const vec3 cls_color[7] = { vec3(0.13, 0.145, 0.19), vec3(0.08, 0.20, 0.33), vec3(0.095, 0.092, 0.088), vec3(0.24, 0.13, 0.07),
	vec3(0.30, 0.30, 0.305), vec3(0.42, 0.38, 0.30), vec3(0.5, 0.45, 0.4) };
const float cls_colmix[7] = { 0.8, 0.85, 0.95, 0.25, 1.0, 0.5, 0.0 };
const float cls_value[7] = { 0.55, 1.1, 0.24, 0.85, 0.8, 0.4, 0.85 };
const float cls_rough[7] = { 0.88, 0.88, 0.92, 0.6, 0.5, 0.7, 0.7 };
const float cls_metal[7] = { 0.0, 0.0, 0.0, 0.0, 0.6, 0.0, 0.0 };
const float cls_spec[7] = { 0.15, 0.12, 0.08, 0.35, 0.5, 0.2, 0.2 };
// (Warden 7 judge: the tabard read as satin, the quilting as a puffer: both matte however soaked, their wet only darker)
const float cls_matte[7] = { 0.0, 1.0, 1.0, 0.0, 0.0, 0.6, 0.0 };
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
// the quilting (Warden 6 r3: the sculpt's square waffle smoothed out of the mesh and its pale paint blotches evened in
// the atlas at the source; the ID map's channels lead): the ID map's low bits are its padding's loft (0 in a stitch line)
uniform float quilt_flat = 0.0;      // how far the quilting's paint is flattened to its blur (the atlas is evened now)
uniform float quilt_atlas = 0.0;     // the sculpt's waffle in the atlas normal, kept on the quilting
uniform float quilt_groove = 0.35;   // the stitch grooves' shade (the loft's bottom x 1 - this)
uniform float quilt_detail = 1.4;    // the baked channels + linen weave's strength on the quilting
uniform float quilt_rough_min = 0.86; // wet linen and the tabard stay matte (no tight highlight even soaked)
// the tabard (Warden 7 judge): a faded blue, sun- and river-faded unevenly (the ID map's low bits on it: its fade), the
// lower third wet-dark to a ragged line, mud and silt at the hem, a darker wet run where the beard's tips touch it
uniform vec3 tabard_deep : source_color = vec3(0.17, 0.26, 0.46);
uniform vec3 tabard_faded : source_color = vec3(0.37, 0.41, 0.47);
uniform float tabard_value = 0.95;
uniform float tabard_wet_lo = 0.58;  // bind height (m): wet-dark below
uniform float tabard_wet_hi = 0.74;
uniform float tabard_wet_dark = 0.55;
uniform float tabard_hem = 0.47;     // mud and silt below this, to the hem (~0.34 m)
uniform vec3 mud_color : source_color = vec3(0.17, 0.145, 0.11);
uniform bool body_data = false;     // WardenLook: the body's data map (its B, A: the beard's drip, wet streaks)
uniform float face_dark : hint_range(0.0, 1.0) = 0.22;   // (no data map: the hood's old darkening, kept)
uniform float beard_drip_dark = 0.6; // the data map's B on the body: the beard's drip
// the iron (Warden 7 judge: too clean): rough patches, pits, rust in the recesses (the ID map's convexity, the atlas's
// crevices), its convex edges worn bright, wet runs down it (the data map's A)
uniform vec3 rust_deep : source_color = vec3(0.24, 0.11, 0.05);
uniform float rust_amount : hint_range(0.0, 1.0) = 0.8;
uniform float edge_wear = 0.9;
// (Warden 7 r3 judge: the gauntlets and forearm plates read as pale grey cloth, the lamp arm's iron as glossy vinyl and
// the rust as orange glitter: the iron's value down, its worn edges only the sharpest and a darker steel, rougher, the
// rust soft low-frequency patches)
uniform float iron_value = 0.6;
uniform float iron_rough = 0.74;
uniform float edge_from = 0.86;
uniform float edge_value = 0.085;
uniform float rust_pit = 0.12;
// (Warden 7 r3 judge: a satin band down the tabard's front edges: the atlas's pale trim strips there. The tabard's paint
// held to its blurred surroundings' value, so a strip can't stand out)
uniform float tabard_trim_cap = 1.12;
uniform float tabard_trim_mip = 4.5;
uniform float pit_amount = 0.5;
uniform float streak_amount = 0.7;
// the iron's grime: dark against its blurred surroundings in the atlas (the crevices), dull and black-brown
uniform vec3 grime_color : source_color = vec3(0.035, 0.03, 0.026);
uniform float grime_amount : hint_range(0.0, 1.0) = 0.85;
uniform float grime_from = 0.05;
uniform float grime_to = 0.35;
// shadow in the hood
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
		vec2 dx = body_data ? d.ba : vec2(0.0, 0.5); // the body's beard drip and wet streaks
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
		// (the tabard's own colour by its fade; the iron's convexity: 0.5 where it is not iron)
		float fade = smoothstep(0.2, 0.85, puff);
		vec3 tab = mix(tabard_deep, tabard_faded, fade);
		float cmatte = 0.0;
		for (int c = 0; c < 7; c++) {
			ccol += wc[c] * (c == 1 ? tab : pow(cls_color[c], vec3(2.2)));
			cmatte += wc[c] * cls_matte[c];
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
		la_q *= mix(1.0, mix(1.0 - quilt_groove, 1.0, sqrt(clamp(puff, 0.0, 1.0))), wc[2]);
		float la_t = max(dot(textureLod(albedo_tex, UV, tabard_trim_mip).rgb, LUM), 1e-4);
		la_q = mix(la_q, min(la_q, la_t * tabard_trim_cap), wc[1]);
		vec3 b = mix(a * (la_q / max(la, 1e-4)), ccol * (la_q / max(dot(ccol, LUM), 1e-4)), cmix) * cval;
		b *= mix(1.0, tabard_value * (0.78 + 0.4 * fade), wc[1]);
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
		// the quilting and the tabard: matte however soaked
		rough = mix(rough, max(rough, quilt_rough_min), cmatte);
		spec = mix(spec, cspec, cmatte);
		// the tabard: its lower third wet-dark to a ragged line, the hem's mud and silt, the beard's drip
		float rag = (dx.y - 0.5) * 0.12 + (puff - 0.5) * 0.1;
		float twet = (1.0 - smoothstep(tabard_wet_lo, tabard_wet_hi, hy + rag)) * wc[1];
		w *= mix(1.0, tabard_wet_dark, twet);
		rough = mix(rough, rough - 0.06, twet);
		float hem = (1.0 - smoothstep(tabard_hem - 0.08, tabard_hem, hy + rag * 0.8)) * wc[1];
		hem *= 0.55 + 0.45 * smoothstep(0.3, 0.7, dx.y);
		w = mix(w, mud_color * (0.7 + 0.5 * puff), hem * 0.85);
		rough = mix(rough, 0.93, hem);
		float drip = dx.x * (1.0 - wc[4]);
		w *= mix(1.0, beard_drip_dark, drip);
		rough = mix(rough, min(rough, 0.72), drip);
		spec = mix(spec, max(spec, 0.22), drip);
		// the iron: rough patches, pits, rust in the recesses, worn convex edges, wet runs
		float cvx = mix(0.5, puff, wc[4]);
		float pit = smoothstep(0.55, 0.8, vnoise(UV * 1600.0)) * smoothstep(0.35, 0.75, vnoise(UV * 220.0 + 3.0));
		float rpatch = vnoise(UV * 140.0 + 11.0);
		float recess = max(smoothstep(0.52, 0.28, cvx), smoothstep(grime_from, grime_to * 0.8, (la_b - la) / la_b));
		float rlow = vnoise(UV * 38.0 + 11.0);
		float bloom = smoothstep(0.55, 0.85, rlow) * smoothstep(0.35, 0.7, vnoise(UV * 17.0 + 5.0)); // oxide patches, soft
		float rust = clamp(recess * (0.6 + 0.4 * rlow) + bloom * 0.6 + pit * rust_pit, 0.0, 1.0) * rust_amount * wc[4];
		float edge = smoothstep(edge_from, 0.98, cvx) * edge_wear * wc[4] * (1.0 - rust);
		float stre = smoothstep(0.6, 0.82, dx.y) * streak_amount * wc[4];
		w = mix(w, w * (0.75 + 0.5 * rpatch) * iron_value, wc[4]);
		w *= mix(1.0, 0.6, pit * pit_amount * wc[4]);
		w = mix(w, rust_deep * (0.7 + 0.4 * rlow), rust);
		w = mix(w, vec3(edge_value, edge_value, edge_value * 1.03), edge);
		w *= mix(1.0, 0.7, stre);
		rough = mix(rough, iron_rough + (rpatch - 0.5) * 0.25, wc[4]);
		rough = mix(rough, 0.9, max(rust, pit * pit_amount * wc[4]));
		rough = mix(rough, 0.5, edge);
		rough = mix(rough, 0.4, stre);
		float rmetal = 1.0 - rust;
		// the iron's crevices: grime (dark in the atlas against its blurred surroundings), dull, not metal
		float grime = smoothstep(grime_from, grime_to, (la_b - la) / la_b) * wc[4] * grime_amount;
		w = mix(w, grime_color, grime);
		rough = mix(rough, 0.92, grime);
		spec = mix(spec, 0.2, grime);
		// deep in the hood: the hood's inside dark (and without a data map, the default texture's alpha 1 through the
		//  old face term: the hood's judged look, kept)
		float occ = smoothstep(occ_from, occ_to, d.g);
		float legacy = body_data ? 0.0 : d.a;
		w *= mix(1.0, occ_dark, occ) * mix(1.0, face_dark, legacy);
		spec *= mix(1.0, 0.35, max(occ, legacy));
		// the silt: below the tide line the cloth dries dull and pale with river mud, the line itself a dark band
		// (the boots: the mud patchy on them, the leather kept wet under it)
		float silt = d.r * silt_amount * (1.0 - wc[3] * (0.75 - 0.55 * smoothstep(0.35, 0.7, dx.y)));
		float band = clamp(d.r * (1.0 - d.r) * 4.0, 0.0, 1.0);
		band = band * band * band_amount;
		w = mix(w, mix(vec3(dot(w, LUM)), w, 0.5) * 0.6 + silt_color * 0.4, silt);
		rough = mix(rough, 0.9, d.r * (1.0 - 0.7 * wc[3]));
		spec = mix(spec, 0.3, d.r * (1.0 - wc[3]));
		w = mix(w, band_color, band);
		w *= value_mul;
		ALBEDO = w;
		RIM = wool_sheen * wc[0];
		RIM_TINT = wool_sheen_tint;
		METALLIC = cmetal * (1.0 - grime) * rmetal;
		ROUGHNESS = rough;
		SPECULAR = spec;
		// the atlas's normal (the quilting's puffs each their own height) + the class's baked weave/grain/dents
		vec2 nxy = vec2(0.0);
		if (has_normal) nxy = texture(normal_tex, UV).rg * 2.0 - 1.0;
		nxy *= mix(1.0, quilt_atlas, wc[2]);
		nxy += (idl.ba * 2.0 - 1.0) * cdet * mix(1.0, quilt_detail, wc[2]);
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
