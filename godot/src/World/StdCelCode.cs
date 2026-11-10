// StdCelCode: a port of Godot 4.5.1-stable BaseMaterial3D::_update_shader() (scene/resources/material.cpp,
// lines 685-2060) as plain C#, so that for any StandardMaterial3D or ORMMaterial3D we can produce the SAME shader
// code string the engine builds for it, plus two optional injection points (see Generate).
//
// The generator body below is a mechanical translation of the C++: same statement order, same strings, same
// whitespace (C++ raw strings became C# verbatim strings, vformat became F with %s substitution). The enum constants
// carry the numeric values of material.h so that arrays (features, flags) read through the C# getters line up.
// Known differences from the engine:
//   * the engine's WARN_PRINT blocks (MSDF+triplanar, heightmap+triplanar) are not ported (they only print);
//   * the first comment line takes the version from Engine.GetVersionInfo() (falls back to "Godot Engine 4.5.1.stable").
// No Godot node code. Source: Godot 4.5.1-stable.
using System;
using System.Text;
using Godot;

namespace SurvivorUnchained.World;

public static class StdCelCode
{
	// Enum values from material.h (4.5.1).
	const int FEATURE_MAX = 13, FLAG_MAX = 25;
	const int TEXTURE_FILTER_NEAREST = 0, TEXTURE_FILTER_LINEAR = 1, TEXTURE_FILTER_NEAREST_WITH_MIPMAPS = 2, TEXTURE_FILTER_LINEAR_WITH_MIPMAPS = 3, TEXTURE_FILTER_NEAREST_WITH_MIPMAPS_ANISOTROPIC = 4, TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC = 5, TEXTURE_FILTER_MAX = 6;
	const int DETAIL_UV_1 = 0, DETAIL_UV_2 = 1;
	const int TRANSPARENCY_DISABLED = 0, TRANSPARENCY_ALPHA = 1, TRANSPARENCY_ALPHA_SCISSOR = 2, TRANSPARENCY_ALPHA_HASH = 3, TRANSPARENCY_ALPHA_DEPTH_PRE_PASS = 4;
	const int ALPHA_ANTIALIASING_OFF = 0, ALPHA_ANTIALIASING_ALPHA_TO_COVERAGE = 1, ALPHA_ANTIALIASING_ALPHA_TO_COVERAGE_AND_TO_ONE = 2;
	const int SHADING_MODE_UNSHADED = 0, SHADING_MODE_PER_PIXEL = 1, SHADING_MODE_PER_VERTEX = 2;
	const int FEATURE_EMISSION = 0, FEATURE_NORMAL_MAPPING = 1, FEATURE_RIM = 2, FEATURE_CLEARCOAT = 3, FEATURE_ANISOTROPY = 4, FEATURE_AMBIENT_OCCLUSION = 5, FEATURE_HEIGHT_MAPPING = 6, FEATURE_SUBSURFACE_SCATTERING = 7, FEATURE_SUBSURFACE_TRANSMITTANCE = 8, FEATURE_BACKLIGHT = 9, FEATURE_REFRACTION = 10, FEATURE_DETAIL = 11, FEATURE_BENT_NORMAL_MAPPING = 12;
	const int BLEND_MODE_MIX = 0, BLEND_MODE_ADD = 1, BLEND_MODE_SUB = 2, BLEND_MODE_MUL = 3, BLEND_MODE_PREMULT_ALPHA = 4, BLEND_MODE_MAX = 5;
	const int DEPTH_DRAW_OPAQUE_ONLY = 0, DEPTH_DRAW_ALWAYS = 1, DEPTH_DRAW_DISABLED = 2, DEPTH_DRAW_MAX = 3;
	const int DEPTH_TEST_DEFAULT = 0, DEPTH_TEST_INVERTED = 1, DEPTH_TEST_MAX = 2;
	const int CULL_BACK = 0, CULL_FRONT = 1, CULL_DISABLED = 2, CULL_MAX = 3;
	const int FLAG_DISABLE_DEPTH_TEST = 0, FLAG_ALBEDO_FROM_VERTEX_COLOR = 1, FLAG_SRGB_VERTEX_COLOR = 2, FLAG_USE_POINT_SIZE = 3, FLAG_FIXED_SIZE = 4, FLAG_BILLBOARD_KEEP_SCALE = 5, FLAG_UV1_USE_TRIPLANAR = 6, FLAG_UV2_USE_TRIPLANAR = 7, FLAG_UV1_USE_WORLD_TRIPLANAR = 8, FLAG_UV2_USE_WORLD_TRIPLANAR = 9, FLAG_AO_ON_UV2 = 10, FLAG_EMISSION_ON_UV2 = 11, FLAG_ALBEDO_TEXTURE_FORCE_SRGB = 12, FLAG_DONT_RECEIVE_SHADOWS = 13, FLAG_DISABLE_AMBIENT_LIGHT = 14, FLAG_USE_SHADOW_TO_OPACITY = 15, FLAG_USE_TEXTURE_REPEAT = 16, FLAG_INVERT_HEIGHTMAP = 17, FLAG_SUBSURFACE_MODE_SKIN = 18, FLAG_PARTICLE_TRAILS_MODE = 19, FLAG_ALBEDO_TEXTURE_MSDF = 20, FLAG_DISABLE_FOG = 21, FLAG_DISABLE_SPECULAR_OCCLUSION = 22, FLAG_USE_Z_CLIP_SCALE = 23, FLAG_USE_FOV_OVERRIDE = 24;
	const int DIFFUSE_BURLEY = 0, DIFFUSE_LAMBERT = 1, DIFFUSE_LAMBERT_WRAP = 2, DIFFUSE_TOON = 3, DIFFUSE_MAX = 4;
	const int SPECULAR_SCHLICK_GGX = 0, SPECULAR_TOON = 1, SPECULAR_DISABLED = 2, SPECULAR_MAX = 3;
	const int BILLBOARD_DISABLED = 0, BILLBOARD_ENABLED = 1, BILLBOARD_FIXED_Y = 2, BILLBOARD_PARTICLES = 3, BILLBOARD_MAX = 4;
	const int TEXTURE_CHANNEL_RED = 0, TEXTURE_CHANNEL_GREEN = 1, TEXTURE_CHANNEL_BLUE = 2, TEXTURE_CHANNEL_ALPHA = 3, TEXTURE_CHANNEL_GRAYSCALE = 4, TEXTURE_CHANNEL_MAX = 5;
	const int EMISSION_OP_ADD = 0, EMISSION_OP_MULTIPLY = 1;
	const int DISTANCE_FADE_DISABLED = 0, DISTANCE_FADE_PIXEL_ALPHA = 1, DISTANCE_FADE_PIXEL_DITHER = 2, DISTANCE_FADE_OBJECT_DITHER = 3;
	const int STENCIL_MODE_DISABLED = 0, STENCIL_MODE_OUTLINE = 1, STENCIL_MODE_XRAY = 2, STENCIL_MODE_CUSTOM = 3;
	const int STENCIL_FLAG_READ = 1, STENCIL_FLAG_WRITE = 2, STENCIL_FLAG_WRITE_DEPTH_FAIL = 4;
	const int STENCIL_COMPARE_ALWAYS = 0, STENCIL_COMPARE_LESS = 1, STENCIL_COMPARE_EQUAL = 2, STENCIL_COMPARE_LESS_OR_EQUAL = 3, STENCIL_COMPARE_GREATER = 4, STENCIL_COMPARE_NOT_EQUAL = 5, STENCIL_COMPARE_GREATER_OR_EQUAL = 6, STENCIL_COMPARE_MAX = 7;

	/// The material's shader key as the engine computes it (_compute_key), as a string, so callers can cache one Shader per key.
	public static string Key(BaseMaterial3D m)
	{
		var s = new StringBuilder();
		s.Append((int)m.DetailUVLayer).Append('.').Append((int)m.BlendMode).Append('.').Append((int)m.DepthDrawMode).Append('.')
			.Append((int)m.DepthTest).Append('.').Append((int)m.CullMode).Append('.').Append((int)m.TextureFilter).Append('.')
			.Append((int)m.Transparency).Append('.').Append((int)m.ShadingMode).Append('.').Append((int)m.RoughnessTextureChannel).Append('.')
			.Append((int)m.DetailBlendMode).Append('.').Append((int)m.DiffuseMode).Append('.').Append((int)m.SpecularMode).Append('.')
			.Append((int)m.BillboardMode).Append('.').Append(m.HeightmapDeepParallax ? 1 : 0).Append('.').Append(m.Grow ? 1 : 0).Append('.')
			.Append(m.ProximityFadeEnabled ? 1 : 0).Append('.').Append((int)m.DistanceFadeMode).Append('.').Append((int)m.EmissionOperator).Append('.')
			.Append((int)m.AlphaAntialiasingMode).Append('.').Append(m is OrmMaterial3D ? 1 : 0).Append('.')
			.Append((int)m.StencilMode).Append('.').Append((int)m.StencilFlags & 7).Append('.').Append((int)m.StencilCompare).Append('.')
			.Append((int)m.StencilReference & 255).Append('.');
		uint fm = 0, fl = 0;
		for (int i = 0; i < FEATURE_MAX; i++) if (m.GetFeature((BaseMaterial3D.Feature)i)) fm |= 1u << i;
		for (int i = 0; i < FLAG_MAX; i++) if (m.GetFlag((BaseMaterial3D.Flags)i)) fl |= 1u << i;
		s.Append(fm.ToString("x")).Append('.').Append(fl.ToString("x"));
		return s.ToString();
	}

	// printf-like "%s" substitution (vformat for the only format the generator uses).
	static string F(string fmt, params object[] a)
	{
		var sb = new StringBuilder();
		int n = 0;
		for (int i = 0; i < fmt.Length; i++)
		{
			if (fmt[i] == '%' && i + 1 < fmt.Length && fmt[i + 1] == 's') { sb.Append(a[n++]); i++; }
			else sb.Append(fmt[i]);
		}
		return sb.ToString();
	}

	static string VersionLine()
	{
		string v = "4.5.1.stable";
		try
		{
			var d = Engine.GetVersionInfo();
			int maj = (int)d["major"], min = (int)d["minor"], pat = (int)d["patch"];
			v = maj + "." + min + (pat != 0 ? "." + pat : "") + "." + (string)d["status"];
		}
		catch (Exception) { }
		return "Godot Engine " + v;
	}

	/// The engine's code for this material (Godot 4.5.1 material.cpp _update_shader), with `afterModes` inserted as its own
	/// line(s) right after the render_mode line (and after the stencil_mode line when there is one), and `fragmentTail`
	/// inserted as the last statement(s) of fragment() (just before its closing brace). Both null = the engine's code exactly.
	public static string Generate(BaseMaterial3D m, string? afterModes = null, string? fragmentTail = null)
	{
		bool orm = m is OrmMaterial3D;
		var features = new bool[FEATURE_MAX];
		var flags = new bool[FLAG_MAX];
		for (int i = 0; i < FEATURE_MAX; i++) features[i] = m.GetFeature((BaseMaterial3D.Feature)i);
		for (int i = 0; i < FLAG_MAX; i++) flags[i] = m.GetFlag((BaseMaterial3D.Flags)i);
		int texture_filter = (int)m.TextureFilter, blend_mode = (int)m.BlendMode, depth_draw_mode = (int)m.DepthDrawMode, cull_mode = (int)m.CullMode;
		int diffuse_mode = (int)m.DiffuseMode, specular_mode = (int)m.SpecularMode, shading_mode = (int)m.ShadingMode, depth_test = (int)m.DepthTest;
		int transparency = (int)m.Transparency, alpha_antialiasing_mode = (int)m.AlphaAntialiasingMode, billboard_mode = (int)m.BillboardMode;
		int detail_uv = (int)m.DetailUVLayer, detail_blend_mode = (int)m.DetailBlendMode, emission_op = (int)m.EmissionOperator;
		int distance_fade = (int)m.DistanceFadeMode, roughness_texture_channel = (int)m.RoughnessTextureChannel;
		int stencil_mode = (int)m.StencilMode, stencil_flags = (int)m.StencilFlags & 7, stencil_compare = (int)m.StencilCompare, stencil_reference = (int)m.StencilReference;
		bool grow_enabled = m.Grow, proximity_fade_enabled = m.ProximityFadeEnabled, deep_parallax = m.HeightmapDeepParallax;

		string texfilter_str = "";
		string texfilter_height_str = "";
	switch (texture_filter) {
		case TEXTURE_FILTER_NEAREST:
			texfilter_str = "filter_nearest";
			texfilter_height_str = "filter_linear";
			break;
		case TEXTURE_FILTER_LINEAR:
			texfilter_str = "filter_linear";
			texfilter_height_str = "filter_linear";
			break;
		case TEXTURE_FILTER_NEAREST_WITH_MIPMAPS:
			texfilter_str = "filter_nearest_mipmap";
			texfilter_height_str = "filter_linear_mipmap";
			break;
		case TEXTURE_FILTER_LINEAR_WITH_MIPMAPS:
			texfilter_str = "filter_linear_mipmap";
			texfilter_height_str = "filter_linear_mipmap";
			break;
		case TEXTURE_FILTER_NEAREST_WITH_MIPMAPS_ANISOTROPIC:
			texfilter_str = "filter_nearest_mipmap_anisotropic";
			texfilter_height_str = "filter_linear_mipmap_anisotropic";
			break;
		case TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC:
			texfilter_str = "filter_linear_mipmap_anisotropic";
			texfilter_height_str = "filter_linear_mipmap_anisotropic";
			break;
		case TEXTURE_FILTER_MAX:
			break; // Internal value, skip.
	}

	if (flags[FLAG_USE_TEXTURE_REPEAT]) {
		texfilter_str += ", repeat_enable";
		texfilter_height_str += ", repeat_enable";
	} else {
		texfilter_str += ", repeat_disable";
		texfilter_height_str += ", repeat_disable";
	}
	string code = F("// NOTE: Shader automatically converted from " + VersionLine() + "'s %s.\n\n", orm ? "ORMMaterial3D" : "StandardMaterial3D");
	// Define shader type and render mode based on property values.
	code += "shader_type spatial;\nrender_mode ";
	switch (blend_mode) {
		case BLEND_MODE_MIX:
			code += "blend_mix";
			break;
		case BLEND_MODE_ADD:
			code += "blend_add";
			break;
		case BLEND_MODE_SUB:
			code += "blend_sub";
			break;
		case BLEND_MODE_MUL:
			code += "blend_mul";
			break;
		case BLEND_MODE_PREMULT_ALPHA:
			code += "blend_premul_alpha";
			break;
		case BLEND_MODE_MAX:
			break; // Internal value, skip.
	}

	int ddm = depth_draw_mode;
	if (features[FEATURE_REFRACTION]) {
		ddm = DEPTH_DRAW_ALWAYS;
	}

	switch (ddm) {
		case DEPTH_DRAW_OPAQUE_ONLY:
			code += ", depth_draw_opaque";
			break;
		case DEPTH_DRAW_ALWAYS:
			code += ", depth_draw_always";
			break;
		case DEPTH_DRAW_DISABLED:
			code += ", depth_draw_never";
			break;
		case DEPTH_DRAW_MAX:
			break; // Internal value, skip.
	}

	switch (cull_mode) {
		case CULL_BACK:
			code += ", cull_back";
			break;
		case CULL_FRONT:
			code += ", cull_front";
			break;
		case CULL_DISABLED:
			code += ", cull_disabled";
			break;
		case CULL_MAX:
			break; // Internal value, skip.
	}
	switch (diffuse_mode) {
		case DIFFUSE_BURLEY:
			code += ", diffuse_burley";
			break;
		case DIFFUSE_LAMBERT:
			code += ", diffuse_lambert";
			break;
		case DIFFUSE_LAMBERT_WRAP:
			code += ", diffuse_lambert_wrap";
			break;
		case DIFFUSE_TOON:
			code += ", diffuse_toon";
			break;
		case DIFFUSE_MAX:
			break; // Internal value, skip.
	}
	switch (specular_mode) {
		case SPECULAR_SCHLICK_GGX:
			code += ", specular_schlick_ggx";
			break;
		case SPECULAR_TOON:
			code += ", specular_toon";
			break;
		case SPECULAR_DISABLED:
			code += ", specular_disabled";
			break;
		case SPECULAR_MAX:
			break; // Internal value, skip.
	}
	if (features[FEATURE_SUBSURFACE_SCATTERING] && flags[FLAG_SUBSURFACE_MODE_SKIN]) {
		code += ", sss_mode_skin";
	}

	if (shading_mode == SHADING_MODE_UNSHADED) {
		code += ", unshaded";
	}
	if (flags[FLAG_DISABLE_DEPTH_TEST]) {
		code += ", depth_test_disabled";
	} else {
		switch (depth_test) {
			case DEPTH_TEST_DEFAULT:
				// depth_test_default is the default behavior, no need to emit it here.
				break;
			case DEPTH_TEST_INVERTED:
				code += ", depth_test_inverted";
				break;
			case DEPTH_TEST_MAX:
				break; // Internal value, skip.
		}
	}
	if (flags[FLAG_PARTICLE_TRAILS_MODE]) {
		code += ", particle_trails";
	}
	if (shading_mode == SHADING_MODE_PER_VERTEX) {
		code += ", vertex_lighting";
	}
	if (flags[FLAG_DONT_RECEIVE_SHADOWS]) {
		code += ", shadows_disabled";
	}
	if (flags[FLAG_DISABLE_AMBIENT_LIGHT]) {
		code += ", ambient_light_disabled";
	}
	if (flags[FLAG_USE_SHADOW_TO_OPACITY]) {
		code += ", shadow_to_opacity";
	}
	if (flags[FLAG_DISABLE_FOG]) {
		code += ", fog_disabled";
	}
	if (flags[FLAG_DISABLE_SPECULAR_OCCLUSION]) {
		code += ", specular_occlusion_disabled";
	}
	if (transparency == TRANSPARENCY_ALPHA_DEPTH_PRE_PASS) {
		code += ", depth_prepass_alpha";
	}

	// Although it's technically possible to do alpha antialiasing without using alpha hash or alpha scissor,
	// it is restricted in the base material because it has no use, and abusing it with regular Alpha blending can
	// saturate the MSAA mask.
	if (transparency == TRANSPARENCY_ALPHA_HASH || transparency == TRANSPARENCY_ALPHA_SCISSOR) {
		// Alpha antialiasing is only useful with ALPHA_HASH or ALPHA_SCISSOR.
		if (alpha_antialiasing_mode == ALPHA_ANTIALIASING_ALPHA_TO_COVERAGE) {
			code += ", alpha_to_coverage";
		} else if (alpha_antialiasing_mode == ALPHA_ANTIALIASING_ALPHA_TO_COVERAGE_AND_TO_ONE) {
			code += ", alpha_to_coverage_and_one";
		}
	}

	code += ";\n";

	if (stencil_mode != STENCIL_MODE_DISABLED && stencil_flags != 0) {
		code += "stencil_mode ";

		if ((stencil_flags & STENCIL_FLAG_READ) != 0) {
			code += "read";
		}

		if ((stencil_flags & STENCIL_FLAG_WRITE) != 0) {
			if ((stencil_flags & STENCIL_FLAG_READ) != 0) {
				code += ", ";
			}
			code += "write";
		}

		if ((stencil_flags & STENCIL_FLAG_WRITE_DEPTH_FAIL) != 0) {
			if ((stencil_flags & (STENCIL_FLAG_READ | STENCIL_FLAG_WRITE)) != 0) {
				code += ", ";
			}
			code += "write_depth_fail";
		}

		switch (stencil_compare) {
			case STENCIL_COMPARE_ALWAYS:
				code += ", compare_always";
				break;
			case STENCIL_COMPARE_LESS:
				code += ", compare_less";
				break;
			case STENCIL_COMPARE_EQUAL:
				code += ", compare_equal";
				break;
			case STENCIL_COMPARE_LESS_OR_EQUAL:
				code += ", compare_less_or_equal";
				break;
			case STENCIL_COMPARE_GREATER:
				code += ", compare_greater";
				break;
			case STENCIL_COMPARE_NOT_EQUAL:
				code += ", compare_not_equal";
				break;
			case STENCIL_COMPARE_GREATER_OR_EQUAL:
				code += ", compare_greater_or_equal";
				break;
			case STENCIL_COMPARE_MAX:
				break;
		}

		code += F(", %s;\n", stencil_reference);
	}

	if (afterModes != null) { code += afterModes.TrimEnd((char)10) + (char)10; }
	// Generate list of uniforms.
	code += F(@"
uniform vec4 albedo : source_color;
uniform sampler2D texture_albedo : source_color, %s;
",
			texfilter_str);

	if (grow_enabled) {
		code += "uniform float grow : hint_range(-16.0, 16.0, 0.001);\n";
	}

	if (proximity_fade_enabled) {
		code += "uniform float proximity_fade_distance : hint_range(0.0, 4096.0, 0.01);\n";
	}
	if (distance_fade != DISTANCE_FADE_DISABLED) {
		code += @"
uniform float distance_fade_min : hint_range(0.0, 4096.0, 0.01);
uniform float distance_fade_max : hint_range(0.0, 4096.0, 0.01);
";
	}


	if (flags[FLAG_ALBEDO_TEXTURE_MSDF] && !flags[FLAG_UV1_USE_TRIPLANAR]) {
		code += @"
uniform float msdf_pixel_range : hint_range(1.0, 100.0, 1.0);
uniform float msdf_outline_size : hint_range(0.0, 250.0, 1.0);
";
	}

	// Alpha scissor is only valid if there is no antialiasing edge.
	// Alpha hash is valid whenever, but not with alpha scissor.
	if (transparency == TRANSPARENCY_ALPHA_SCISSOR) {
		code += "uniform float alpha_scissor_threshold : hint_range(0.0, 1.0, 0.001);\n";
	} else if (transparency == TRANSPARENCY_ALPHA_HASH) {
		code += "uniform float alpha_hash_scale : hint_range(0.0, 2.0, 0.01);\n";
	}
	// If alpha antialiasing isn't off, add in the edge variable.
	if (alpha_antialiasing_mode != ALPHA_ANTIALIASING_OFF &&
			(transparency == TRANSPARENCY_ALPHA_SCISSOR || transparency == TRANSPARENCY_ALPHA_HASH)) {
		code += "uniform float alpha_antialiasing_edge : hint_range(0.0, 1.0, 0.01);\n";
	}

	code += "uniform ivec2 albedo_texture_size;\n";
	code += "uniform float point_size : hint_range(0.1, 128.0, 0.1);\n";

	if (!orm) {
		code += F(@"
uniform float roughness : hint_range(0.0, 1.0);
uniform sampler2D texture_metallic : hint_default_white, %s;
uniform vec4 metallic_texture_channel;
",
				texfilter_str);
		switch (roughness_texture_channel) {
			case TEXTURE_CHANNEL_RED: {
				code += F("uniform sampler2D texture_roughness : hint_roughness_r, %s;\n", texfilter_str);
			} break;
			case TEXTURE_CHANNEL_GREEN: {
				code += F("uniform sampler2D texture_roughness : hint_roughness_g, %s;\n", texfilter_str);
			} break;
			case TEXTURE_CHANNEL_BLUE: {
				code += F("uniform sampler2D texture_roughness : hint_roughness_b, %s;\n", texfilter_str);
			} break;
			case TEXTURE_CHANNEL_ALPHA: {
				code += F("uniform sampler2D texture_roughness : hint_roughness_a, %s;\n", texfilter_str);
			} break;
			case TEXTURE_CHANNEL_GRAYSCALE: {
				code += F("uniform sampler2D texture_roughness : hint_roughness_gray, %s;\n", texfilter_str);
			} break;
			case TEXTURE_CHANNEL_MAX:
				break; // Internal value, skip.
		}

		code += @"
uniform float specular : hint_range(0.0, 1.0, 0.01);
uniform float metallic : hint_range(0.0, 1.0, 0.01);
";
	} else {
		code += "uniform sampler2D texture_orm : hint_roughness_g, " + texfilter_str + ";\n";
	}

	if (billboard_mode == BILLBOARD_PARTICLES) {
		code += @"
uniform int particles_anim_h_frames : hint_range(1, 128);
uniform int particles_anim_v_frames : hint_range(1, 128);
uniform bool particles_anim_loop;
";
	}

	if (features[FEATURE_EMISSION]) {
		code += F(@"
uniform sampler2D texture_emission : source_color, hint_default_black, %s;
uniform vec4 emission : source_color;
uniform float emission_energy : hint_range(0.0, 100.0, 0.01);
",
				texfilter_str);
	}

	if (features[FEATURE_REFRACTION]) {
		code += F(@"
uniform sampler2D texture_refraction : %s;
uniform float refraction : hint_range(-1.0, 1.0, 0.001);
uniform vec4 refraction_texture_channel;
",
				texfilter_str);
	}

	if (features[FEATURE_REFRACTION]) {
		code += "uniform sampler2D screen_texture : hint_screen_texture, repeat_disable, filter_linear_mipmap;\n";
	}

	if (features[FEATURE_REFRACTION] || proximity_fade_enabled) {
		code += "uniform sampler2D depth_texture : hint_depth_texture, repeat_disable, filter_nearest;\n";
	}

	if (features[FEATURE_NORMAL_MAPPING]) {
		code += F(@"
uniform sampler2D texture_normal : hint_roughness_normal, %s;
uniform float normal_scale : hint_range(-16.0, 16.0);
",
				texfilter_str);
	}
	if (features[FEATURE_BENT_NORMAL_MAPPING]) {
		code += F(@"
uniform sampler2D texture_bent_normal : hint_roughness_normal, %s;
",
				texfilter_str);
	}
	if (features[FEATURE_RIM]) {
		code += F(@"
uniform float rim : hint_range(0.0, 1.0, 0.01);
uniform float rim_tint : hint_range(0.0, 1.0, 0.01);
uniform sampler2D texture_rim : hint_default_white, %s;
",
				texfilter_str);
	}
	if (features[FEATURE_CLEARCOAT]) {
		code += F(@"
uniform float clearcoat : hint_range(0.0, 1.0, 0.01);
uniform float clearcoat_roughness : hint_range(0.0, 1.0, 0.01);
uniform sampler2D texture_clearcoat : hint_default_white, %s;
",
				texfilter_str);
	}
	if (features[FEATURE_ANISOTROPY]) {
		code += F(@"
uniform float anisotropy_ratio : hint_range(0.0, 1.0, 0.01);
uniform sampler2D texture_flowmap : hint_anisotropy, %s;
",
				texfilter_str);
	}
	if (features[FEATURE_AMBIENT_OCCLUSION]) {
		code += F(@"
uniform sampler2D texture_ambient_occlusion : hint_default_white, %s;
uniform vec4 ao_texture_channel;
uniform float ao_light_affect : hint_range(0.0, 1.0, 0.01);
",
				texfilter_str);
	}

	if (features[FEATURE_DETAIL]) {
		code += F(@"
uniform sampler2D texture_detail_albedo : source_color, %s;
uniform sampler2D texture_detail_normal : hint_normal, %s;
uniform sampler2D texture_detail_mask : hint_default_white, %s;
",
				texfilter_str, texfilter_str, texfilter_str);
	}

	if (features[FEATURE_SUBSURFACE_SCATTERING]) {
		code += F(@"
uniform float subsurface_scattering_strength : hint_range(0.0, 1.0, 0.01);
uniform sampler2D texture_subsurface_scattering : hint_default_white, %s;
",
				texfilter_str);
	}

	if (features[FEATURE_SUBSURFACE_TRANSMITTANCE]) {
		code += F(@"
uniform vec4 transmittance_color : source_color;
uniform float transmittance_depth : hint_range(0.001, 8.0, 0.001);
uniform sampler2D texture_subsurface_transmittance : hint_default_white, %s;
uniform float transmittance_boost : hint_range(0.0, 1.0, 0.01);
",
				texfilter_str);
	}

	if (features[FEATURE_BACKLIGHT]) {
		code += F(@"
uniform vec4 backlight : source_color;
uniform sampler2D texture_backlight : hint_default_black, %s;
",
				texfilter_str);
	}

	if (features[FEATURE_HEIGHT_MAPPING]) {
		code += F(@"
uniform sampler2D texture_heightmap : hint_default_black, %s;
uniform float heightmap_scale : hint_range(-16.0, 16.0, 0.001);
uniform int heightmap_min_layers : hint_range(1, 64);
uniform int heightmap_max_layers : hint_range(1, 64);
uniform vec2 heightmap_flip;
",
				texfilter_height_str);
	}
	if (flags[FLAG_UV1_USE_TRIPLANAR]) {
		code += "varying vec3 uv1_triplanar_pos;\n";
	}
	if (flags[FLAG_UV2_USE_TRIPLANAR]) {
		code += "varying vec3 uv2_triplanar_pos;\n";
	}
	if (flags[FLAG_UV1_USE_TRIPLANAR]) {
		code += @"
uniform float uv1_blend_sharpness : hint_range(0.0, 150.0, 0.001);
varying vec3 uv1_power_normal;
";
	}

	if (flags[FLAG_UV2_USE_TRIPLANAR]) {
		code += @"uniform float uv2_blend_sharpness : hint_range(0.0, 150.0, 0.001);
varying vec3 uv2_power_normal;
";
	}

	code += @"
uniform vec3 uv1_scale;
uniform vec3 uv1_offset;
uniform vec3 uv2_scale;
uniform vec3 uv2_offset;
";

	if (flags[FLAG_USE_Z_CLIP_SCALE]) {
		code += "uniform float z_clip_scale : hint_range(0.01, 1.0, 0.01);\n";
	}

	if (flags[FLAG_USE_FOV_OVERRIDE]) {
		code += "uniform float fov_override : hint_range(1.0, 179.0, 0.1);\n";
	}

	// Generate vertex shader.
	code += @"
void vertex() {";

	if (flags[FLAG_SRGB_VERTEX_COLOR]) {
		code += @"
	// Vertex Color is sRGB: Enabled
	if (!OUTPUT_IS_SRGB) {
		COLOR.rgb = mix(
				pow((COLOR.rgb + vec3(0.055)) * (1.0 / (1.0 + 0.055)), vec3(2.4)),
				COLOR.rgb * (1.0 / 12.92),
				lessThan(COLOR.rgb, vec3(0.04045)));
	}
";
	}
	if (flags[FLAG_USE_POINT_SIZE]) {
		code += @"
	// Use Point Size: Enabled
	POINT_SIZE = point_size;
";
	}

	if (shading_mode == SHADING_MODE_PER_VERTEX) {
		code += @"
	// Shading Mode: Per Vertex
	ROUGHNESS = roughness;
";
	}

	if (!flags[FLAG_UV1_USE_TRIPLANAR]) {
		code += @"
	UV = UV * uv1_scale.xy + uv1_offset.xy;
";
	}

	if (detail_uv == DETAIL_UV_2 && !flags[FLAG_UV2_USE_TRIPLANAR]) {
		// Don't add a newline if the UV assignment above is already performed,
		// so that UV1 and UV2 are closer to each other.
		if (flags[FLAG_UV1_USE_TRIPLANAR]) {
			code += "\n";
		}
		code += @"	// Detail UV Layer: UV2
	UV2 = UV2 * uv2_scale.xy + uv2_offset.xy;
";
	}

	switch (billboard_mode) {
		case BILLBOARD_DISABLED: {
		} break;
		case BILLBOARD_ENABLED: {
			// `MAIN_CAM_INV_VIEW_MATRIX` is inverse of the camera, even on shadow passes.
			// This ensures the billboard faces the camera when casting shadows.
			code += @"
	// Billboard Mode: Enabled
	MODELVIEW_MATRIX = VIEW_MATRIX * mat4(
			MAIN_CAM_INV_VIEW_MATRIX[0],
			MAIN_CAM_INV_VIEW_MATRIX[1],
			MAIN_CAM_INV_VIEW_MATRIX[2],
			MODEL_MATRIX[3]);
";
			if (flags[FLAG_BILLBOARD_KEEP_SCALE]) {
				code += @"
	// Billboard Keep Scale: Enabled
	MODELVIEW_MATRIX = MODELVIEW_MATRIX * mat4(
			vec4(length(MODEL_MATRIX[0].xyz), 0.0, 0.0, 0.0),
			vec4(0.0, length(MODEL_MATRIX[1].xyz), 0.0, 0.0),
			vec4(0.0, 0.0, length(MODEL_MATRIX[2].xyz), 0.0),
			vec4(0.0, 0.0, 0.0, 1.0));
";
			}
			code += "	MODELVIEW_NORMAL_MATRIX = mat3(MODELVIEW_MATRIX);\n";
		} break;
		case BILLBOARD_FIXED_Y: {
			// `MAIN_CAM_INV_VIEW_MATRIX` is inverse of the camera, even on shadow passes.
			// This ensures the billboard faces the camera when casting shadows.
			code += @"
	// Billboard Mode: Y-Billboard
	MODELVIEW_MATRIX = VIEW_MATRIX * mat4(
			vec4(normalize(cross(vec3(0.0, 1.0, 0.0), MAIN_CAM_INV_VIEW_MATRIX[2].xyz)), 0.0),
			vec4(0.0, 1.0, 0.0, 0.0),
			vec4(normalize(cross(MAIN_CAM_INV_VIEW_MATRIX[0].xyz, vec3(0.0, 1.0, 0.0))), 0.0),
			MODEL_MATRIX[3]);
";
			if (flags[FLAG_BILLBOARD_KEEP_SCALE]) {
				code += @"
	// Billboard Keep Scale: Enabled
	MODELVIEW_MATRIX = MODELVIEW_MATRIX * mat4(
			vec4(length(MODEL_MATRIX[0].xyz), 0.0, 0.0, 0.0),
			vec4(0.0, length(MODEL_MATRIX[1].xyz), 0.0, 0.0),
			vec4(0.0, 0.0, length(MODEL_MATRIX[2].xyz), 0.0),
			vec4(0.0, 0.0, 0.0, 1.0));
";
			}
			code += "	MODELVIEW_NORMAL_MATRIX = mat3(MODELVIEW_MATRIX);\n";
		} break;
		case BILLBOARD_PARTICLES: {
			// Make billboard and rotated by rotation.
			code += @"
	// Billboard Mode: Particles
	mat4 mat_world = mat4(
			normalize(INV_VIEW_MATRIX[0]),
			normalize(INV_VIEW_MATRIX[1]),
			normalize(INV_VIEW_MATRIX[2]),
			MODEL_MATRIX[3]);
	mat_world = mat_world * mat4(
			vec4(cos(INSTANCE_CUSTOM.x), -sin(INSTANCE_CUSTOM.x), 0.0, 0.0),
			vec4(sin(INSTANCE_CUSTOM.x), cos(INSTANCE_CUSTOM.x), 0.0, 0.0),
			vec4(0.0, 0.0, 1.0, 0.0),
			vec4(0.0, 0.0, 0.0, 1.0));
";
			// Set modelview.
			code += "	MODELVIEW_MATRIX = VIEW_MATRIX * mat_world;\n";
			if (flags[FLAG_BILLBOARD_KEEP_SCALE]) {
				code += @"
	// Billboard Keep Scale: Enabled
	MODELVIEW_MATRIX = MODELVIEW_MATRIX * mat4(
			vec4(length(MODEL_MATRIX[0].xyz), 0.0, 0.0, 0.0),
			vec4(0.0, length(MODEL_MATRIX[1].xyz), 0.0, 0.0),
			vec4(0.0, 0.0, length(MODEL_MATRIX[2].xyz), 0.0),
			vec4(0.0, 0.0, 0.0, 1.0));
";
			}
			// Set modelview normal and handle animation.
			code += @"
	MODELVIEW_NORMAL_MATRIX = mat3(MODELVIEW_MATRIX);

	float h_frames = float(particles_anim_h_frames);
	float v_frames = float(particles_anim_v_frames);
	float particle_total_frames = float(particles_anim_h_frames * particles_anim_v_frames);
	float particle_frame = floor(INSTANCE_CUSTOM.z * float(particle_total_frames));
	if (!particles_anim_loop) {
		particle_frame = clamp(particle_frame, 0.0, particle_total_frames - 1.0);
	} else {
		particle_frame = mod(particle_frame, particle_total_frames);
	}
	UV /= vec2(h_frames, v_frames);
	UV += vec2(mod(particle_frame, h_frames) / h_frames, floor((particle_frame + 0.5) / h_frames) / v_frames);
";
		} break;
		case BILLBOARD_MAX:
			break; // Internal value, skip.
	}

	if (flags[FLAG_FIXED_SIZE]) {
		code += @"
	// Fixed Size: Enabled
	if (PROJECTION_MATRIX[3][3] != 0.0) {
		// Orthogonal matrix; try to do about the same with viewport size.
		float h = abs(1.0 / (2.0 * PROJECTION_MATRIX[1][1]));
		// Consistent with vertical FOV (Keep Height).
		float sc = (h * 2.0);
		MODELVIEW_MATRIX[0] *= sc;
		MODELVIEW_MATRIX[1] *= sc;
		MODELVIEW_MATRIX[2] *= sc;
	} else {
		// Scale by depth.
		float sc = -(MODELVIEW_MATRIX)[3].z;
		MODELVIEW_MATRIX[0] *= sc;
		MODELVIEW_MATRIX[1] *= sc;
		MODELVIEW_MATRIX[2] *= sc;
	}
";
	}

	if (flags[FLAG_UV1_USE_TRIPLANAR] || flags[FLAG_UV2_USE_TRIPLANAR]) {
		// Generate tangent and binormal in world space.
		if (flags[FLAG_UV1_USE_WORLD_TRIPLANAR]) {
			code += @"
	vec3 normal = MODEL_NORMAL_MATRIX * NORMAL;
";
		} else {
			code += @"
	vec3 normal = NORMAL;
";
		}
		code += @"
	TANGENT = vec3(0.0, 0.0, -1.0) * abs(normal.x);
	TANGENT += vec3(1.0, 0.0, 0.0) * abs(normal.y);
	TANGENT += vec3(1.0, 0.0, 0.0) * abs(normal.z);
";
		if (flags[FLAG_UV1_USE_WORLD_TRIPLANAR]) {
			code += "	TANGENT = inverse(MODEL_NORMAL_MATRIX) * normalize(TANGENT);\n";
		} else {
			code += "	TANGENT = normalize(TANGENT);\n";
		}

		code += @"
	BINORMAL = vec3(0.0, 1.0, 0.0) * abs(normal.x);
	BINORMAL += vec3(0.0, 0.0, -1.0) * abs(normal.y);
	BINORMAL += vec3(0.0, 1.0, 0.0) * abs(normal.z);
";
		if (flags[FLAG_UV1_USE_WORLD_TRIPLANAR]) {
			code += "	BINORMAL = inverse(MODEL_NORMAL_MATRIX) * normalize(BINORMAL);\n";
		} else {
			code += "	BINORMAL = normalize(BINORMAL);\n";
		}
	}

	if (flags[FLAG_UV1_USE_TRIPLANAR]) {
		if (flags[FLAG_UV1_USE_WORLD_TRIPLANAR]) {
			code += @"
	// UV1 Triplanar: Enabled (with World Triplanar)
	uv1_power_normal = pow(abs(normal), vec3(uv1_blend_sharpness));
	uv1_triplanar_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz * uv1_scale + uv1_offset;
";
		} else {
			code += @"
	// UV1 Triplanar: Enabled
	uv1_power_normal = pow(abs(NORMAL), vec3(uv1_blend_sharpness));
	uv1_triplanar_pos = VERTEX * uv1_scale + uv1_offset;
";
		}
		code += @"	uv1_power_normal /= dot(uv1_power_normal, vec3(1.0));
	uv1_triplanar_pos *= vec3(1.0, -1.0, 1.0);
";
	}

	if (flags[FLAG_UV2_USE_TRIPLANAR]) {
		if (flags[FLAG_UV2_USE_WORLD_TRIPLANAR]) {
			code += @"
	// UV2 Triplanar: Enabled (with World Triplanar)
	uv2_power_normal = pow(abs(mat3(MODEL_MATRIX) * NORMAL), vec3(uv2_blend_sharpness));
	uv2_triplanar_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz * uv2_scale + uv2_offset;
";
		} else {
			code += @"
	// UV2 Triplanar: Enabled
	uv2_power_normal = pow(abs(NORMAL), vec3(uv2_blend_sharpness));
	uv2_triplanar_pos = VERTEX * uv2_scale + uv2_offset;
";
		}
		code += @"	uv2_power_normal /= dot(uv2_power_normal, vec3(1.0));
	uv2_triplanar_pos *= vec3(1.0, -1.0, 1.0);
";
	}

	if (grow_enabled) {
		code += @"
	// Grow: Enabled
	VERTEX += NORMAL * grow;
";
	}

	if (flags[FLAG_USE_Z_CLIP_SCALE]) {
		code += @"
	Z_CLIP_SCALE = z_clip_scale;
";
	}

	if (flags[FLAG_USE_FOV_OVERRIDE]) {
		code += @"
	if (!IN_SHADOW_PASS) {
		float flip_y = sign(PROJECTION_MATRIX[1][1]);
		float aspect = PROJECTION_MATRIX[1][1] / PROJECTION_MATRIX[0][0];
		float f = flip_y / tan(fov_override * PI / 360.0);
		PROJECTION_MATRIX[0][0] = f / aspect;
		PROJECTION_MATRIX[1][1] = f;
	}
";
	}

	// End of the vertex shader function.
	code += "}\n";

	if (flags[FLAG_ALBEDO_TEXTURE_MSDF] && !flags[FLAG_UV1_USE_TRIPLANAR]) {
		code += @"
float msdf_median(float r, float g, float b) {
	return max(min(r, g), min(max(r, g), b));
}
";
	}

	if (flags[FLAG_UV1_USE_TRIPLANAR] || flags[FLAG_UV2_USE_TRIPLANAR]) {
		code += @"
vec4 triplanar_texture(sampler2D p_sampler, vec3 p_weights, vec3 p_triplanar_pos) {
	vec4 samp = vec4(0.0);
	samp += texture(p_sampler, p_triplanar_pos.xy) * p_weights.z;
	samp += texture(p_sampler, p_triplanar_pos.xz) * p_weights.y;
	samp += texture(p_sampler, p_triplanar_pos.zy * vec2(-1.0, 1.0)) * p_weights.x;
	return samp;
}
";
	}

	// Generate fragment shader.
	code += @"
void fragment() {";

	if (!flags[FLAG_UV1_USE_TRIPLANAR]) {
		code += @"
	vec2 base_uv = UV;
";
	}

	if ((features[FEATURE_DETAIL] && detail_uv == DETAIL_UV_2) || (features[FEATURE_AMBIENT_OCCLUSION] && flags[FLAG_AO_ON_UV2]) || (features[FEATURE_EMISSION] && flags[FLAG_EMISSION_ON_UV2])) {
		// Don't add a newline if the UV assignment above is already performed,
		// so that UV1 and UV2 are closer to each other.
		if (flags[FLAG_UV1_USE_TRIPLANAR]) {
			code += "\n";
		}
		code += @"	vec2 base_uv2 = UV2;
";
	}


	// Heightmapping isn't supported at the same time as triplanar mapping.
	if (features[FEATURE_HEIGHT_MAPPING] && !flags[FLAG_UV1_USE_TRIPLANAR]) {
		// Binormal is negative due to mikktspace. Flipping it "unflips" it.
		code += @"
	{
		// Height: Enabled
		vec3 view_dir = normalize(normalize(-VERTEX + EYE_OFFSET) * mat3(TANGENT * heightmap_flip.x, -BINORMAL * heightmap_flip.y, NORMAL));
";

		if (deep_parallax) {
			// Multiply the heightmap scale by 0.01 to improve heightmap scale usability.
			code += @"
		// Height Deep Parallax: Enabled
		float num_layers = mix(float(heightmap_max_layers), float(heightmap_min_layers), abs(dot(vec3(0.0, 0.0, 1.0), view_dir)));
		float layer_depth = 1.0 / num_layers;
		float current_layer_depth = 0.0;
		vec2 p = view_dir.xy * heightmap_scale * 0.01;
		vec2 delta = p / num_layers;
		vec2 ofs = base_uv;
";
			if (flags[FLAG_INVERT_HEIGHTMAP]) {
				code += "		float depth = texture(texture_heightmap, ofs).r;\n";
			} else {
				code += "		float depth = 1.0 - texture(texture_heightmap, ofs).r;\n";
			}
			code += @"
		float current_depth = 0.0;
		while (current_depth < depth) {
			ofs -= delta;
";
			if (flags[FLAG_INVERT_HEIGHTMAP]) {
				code += "			depth = texture(texture_heightmap, ofs).r;\n";
			} else {
				code += "			depth = 1.0 - texture(texture_heightmap, ofs).r;\n";
			}
			code += @"
			current_depth += layer_depth;
		}

		vec2 prev_ofs = ofs + delta;
		float after_depth = depth - current_depth;
";
			if (flags[FLAG_INVERT_HEIGHTMAP]) {
				code += "		float before_depth = texture(texture_heightmap, prev_ofs).r - current_depth + layer_depth;\n";
			} else {
				code += "		float before_depth = (1.0 - texture(texture_heightmap, prev_ofs).r) - current_depth + layer_depth;\n";
			}
			code += @"
		float weight = after_depth / (after_depth - before_depth);
		ofs = mix(ofs, prev_ofs, weight);
";

		} else {
			if (flags[FLAG_INVERT_HEIGHTMAP]) {
				code += "		float depth = texture(texture_heightmap, base_uv).r;\n";
			} else {
				code += "		float depth = 1.0 - texture(texture_heightmap, base_uv).r;\n";
			}
			// Use offset limiting to improve the appearance of non-deep parallax.
			// This reduces the impression of depth, but avoids visible warping in the distance.
			// Multiply the heightmap scale by 0.01 to improve heightmap scale usability.
			code += "		vec2 ofs = base_uv - view_dir.xy * depth * heightmap_scale * 0.01;\n";
		}

		code += "		base_uv = ofs;\n";
		if (features[FEATURE_DETAIL] && detail_uv == DETAIL_UV_2) {
			code += "		base_uv2 -= ofs;\n";
		}

		code += "	}\n";
	}

	if (flags[FLAG_USE_POINT_SIZE]) {
		code += @"
	// Use Point Size: Enabled
	vec4 albedo_tex = texture(texture_albedo, POINT_COORD);
";
	} else {
		if (flags[FLAG_UV1_USE_TRIPLANAR]) {
			code += @"
	vec4 albedo_tex = triplanar_texture(texture_albedo, uv1_power_normal, uv1_triplanar_pos);
";
		} else {
			code += @"
	vec4 albedo_tex = texture(texture_albedo, base_uv);
";
		}
	}

	if (flags[FLAG_ALBEDO_TEXTURE_MSDF] && !flags[FLAG_UV1_USE_TRIPLANAR]) {
		code += @"
	{
		// Albedo Texture MSDF: Enabled
		if (!OUTPUT_IS_SRGB) {
			albedo_tex.rgb = mix(
					vec3(1.0 + 0.055) * pow(albedo_tex.rgb, vec3(1.0 / 2.4)) - vec3(0.055),
					vec3(12.92) * albedo_tex.rgb,
					lessThan(albedo_tex.rgb, vec3(0.0031308)));
		}
		vec2 msdf_size = vec2(msdf_pixel_range) / vec2(albedo_texture_size);
";
		if (flags[FLAG_USE_POINT_SIZE]) {
			code += "		vec2 dest_size = vec2(1.0) / fwidth(POINT_COORD);\n";
		} else {
			code += "		vec2 dest_size = vec2(1.0) / fwidth(base_uv);\n";
		}
		code += @"
		float px_size = max(0.5 * dot(msdf_size, dest_size), 1.0);
		float d = msdf_median(albedo_tex.r, albedo_tex.g, albedo_tex.b);
		if (msdf_outline_size > 0.0) {
			float cr = clamp(msdf_outline_size, 0.0, (msdf_pixel_range / 2.0) - 1.0) / msdf_pixel_range;
			d = min(d, albedo_tex.a);
			albedo_tex.a = clamp((d - 0.5 + cr) * px_size, 0.0, 1.0);
		} else {
			albedo_tex.a = clamp((d - 0.5) * px_size + 0.5, 0.0, 1.0);
		}
		albedo_tex.rgb = vec3(1.0);
	}
";
	} else if (flags[FLAG_ALBEDO_TEXTURE_FORCE_SRGB]) {
		code += @"
	// Albedo Texture Force sRGB: Enabled
	albedo_tex.rgb = mix(
			pow((albedo_tex.rgb + vec3(0.055)) * (1.0 / (1.0 + 0.055)), vec3(2.4)),
			albedo_tex.rgb.rgb * (1.0 / 12.92),
			lessThan(albedo_tex.rgb, vec3(0.04045)));
";
	}

	if (flags[FLAG_ALBEDO_FROM_VERTEX_COLOR]) {
		code += @"
	// Vertex Color Use as Albedo: Enabled
	albedo_tex *= COLOR;

";
	}
	code += "	ALBEDO = albedo.rgb * albedo_tex.rgb;\n";

	if (!orm) {
		if (flags[FLAG_UV1_USE_TRIPLANAR]) {
			code += @"
	float metallic_tex = dot(triplanar_texture(texture_metallic, uv1_power_normal, uv1_triplanar_pos), metallic_texture_channel);
";
		} else {
			code += @"
	float metallic_tex = dot(texture(texture_metallic, base_uv), metallic_texture_channel);
";
		}

		code += @"	METALLIC = metallic_tex * metallic;
	SPECULAR = specular;
";
		switch (roughness_texture_channel) {
			case TEXTURE_CHANNEL_RED: {
				code += @"
	vec4 roughness_texture_channel = vec4(1.0, 0.0, 0.0, 0.0);
";
			} break;
			case TEXTURE_CHANNEL_GREEN: {
				code += @"
	vec4 roughness_texture_channel = vec4(0.0, 1.0, 0.0, 0.0);
";
			} break;
			case TEXTURE_CHANNEL_BLUE: {
				code += @"
	vec4 roughness_texture_channel = vec4(0.0, 0.0, 1.0, 0.0);
";
			} break;
			case TEXTURE_CHANNEL_ALPHA: {
				code += @"
	vec4 roughness_texture_channel = vec4(0.0, 0.0, 0.0, 1.0);
";
			} break;
			case TEXTURE_CHANNEL_GRAYSCALE: {
				code += @"
	vec4 roughness_texture_channel = vec4(0.333333, 0.333333, 0.333333, 0.0);
";
			} break;
			case TEXTURE_CHANNEL_MAX:
				break; // Internal value, skip.
		}

		if (flags[FLAG_UV1_USE_TRIPLANAR]) {
			code += "	float roughness_tex = dot(triplanar_texture(texture_roughness, uv1_power_normal, uv1_triplanar_pos), roughness_texture_channel);\n";
		} else {
			code += "	float roughness_tex = dot(texture(texture_roughness, base_uv), roughness_texture_channel);\n";
		}
		code += @"	ROUGHNESS = roughness_tex * roughness;
";
	} else {
		if (flags[FLAG_UV1_USE_TRIPLANAR]) {
			code += @"
	vec4 orm_tex = triplanar_texture(texture_orm, uv1_power_normal, uv1_triplanar_pos);
";
		} else {
			code += @"
	vec4 orm_tex = texture(texture_orm, base_uv);
";
		}

		code += @"	ROUGHNESS = orm_tex.g;
 	METALLIC = orm_tex.b;
";
	}

	if (features[FEATURE_NORMAL_MAPPING]) {
		code += @"
	// Normal Map: Enabled
";
		if (flags[FLAG_UV1_USE_TRIPLANAR]) {
			code += "	NORMAL_MAP = triplanar_texture(texture_normal, uv1_power_normal, uv1_triplanar_pos).rgb;\n";
		} else {
			code += "	NORMAL_MAP = texture(texture_normal, base_uv).rgb;\n";
		}
		code += "	NORMAL_MAP_DEPTH = normal_scale;\n";
	}

	if (features[FEATURE_BENT_NORMAL_MAPPING]) {
		code += @"
	// Bent Normal Map: Enabled
";
		if (flags[FLAG_UV1_USE_TRIPLANAR]) {
			code += "	BENT_NORMAL_MAP = triplanar_texture(texture_bent_normal, uv1_power_normal, uv1_triplanar_pos).rgb;\n";
		} else {
			code += "	BENT_NORMAL_MAP = texture(texture_bent_normal, base_uv).rgb;\n";
		}
	}

	if (features[FEATURE_EMISSION]) {
		code += @"
	// Emission: Enabled
";
		if (flags[FLAG_EMISSION_ON_UV2]) {
			if (flags[FLAG_UV2_USE_TRIPLANAR]) {
				code += "	vec3 emission_tex = triplanar_texture(texture_emission, uv2_power_normal, uv2_triplanar_pos).rgb;\n";
			} else {
				code += "	vec3 emission_tex = texture(texture_emission, base_uv2).rgb;\n";
			}
		} else {
			if (flags[FLAG_UV1_USE_TRIPLANAR]) {
				code += "	vec3 emission_tex = triplanar_texture(texture_emission, uv1_power_normal, uv1_triplanar_pos).rgb;\n";
			} else {
				code += "	vec3 emission_tex = texture(texture_emission, base_uv).rgb;\n";
			}
		}

		if (emission_op == EMISSION_OP_ADD) {
			code += @"	// Emission Operator: Add
	EMISSION = (emission.rgb + emission_tex) * emission_energy;
";
		} else {
			code += @"	// Emission Operator: Multiply
	EMISSION = (emission.rgb * emission_tex) * emission_energy;
";
		}
	}

	if (features[FEATURE_REFRACTION]) {
		if (features[FEATURE_NORMAL_MAPPING]) {
			code += @"
	// Refraction: Enabled (with normal map texture)
	vec3 unpacked_normal = NORMAL_MAP;
	unpacked_normal.xy = unpacked_normal.xy * 2.0 - 1.0;
	unpacked_normal.z = sqrt(max(0.0, 1.0 - dot(unpacked_normal.xy, unpacked_normal.xy)));
	vec3 ref_normal = normalize(mix(
			NORMAL,
			TANGENT * unpacked_normal.x + BINORMAL * unpacked_normal.y + NORMAL * unpacked_normal.z,
			NORMAL_MAP_DEPTH));
";
		} else {
			code += @"
	// Refraction: Enabled
	vec3 ref_normal = NORMAL;
";
		}
		if (flags[FLAG_UV1_USE_TRIPLANAR]) {
			code += "	vec2 ref_ofs = SCREEN_UV - ref_normal.xy * dot(triplanar_texture(texture_refraction, uv1_power_normal, uv1_triplanar_pos), refraction_texture_channel) * refraction;\n";
		} else {
			code += "	vec2 ref_ofs = SCREEN_UV - ref_normal.xy * dot(texture(texture_refraction, base_uv), refraction_texture_channel) * refraction;\n";
		}
		code += @"
	float ref_amount = 1.0 - albedo.a * albedo_tex.a;

	float refraction_depth_tex = textureLod(depth_texture, ref_ofs, 0.0).r;
	vec4 refraction_view_pos = INV_PROJECTION_MATRIX * vec4(SCREEN_UV * 2.0 - 1.0, refraction_depth_tex, 1.0);
	refraction_view_pos.xyz /= refraction_view_pos.w;

	// If the depth buffer is lower then the model's Z position, use the refracted UV, otherwise use the normal screen UV.
	// At low depth differences, decrease refraction intensity to avoid sudden discontinuities.
	EMISSION += textureLod(screen_texture, mix(SCREEN_UV, ref_ofs, smoothstep(0.0, 1.0, VERTEX.z - refraction_view_pos.z)), ROUGHNESS * 8.0).rgb * ref_amount * EXPOSURE;
	ALBEDO *= 1.0 - ref_amount;
	// Force transparency on the material (required for refraction).
	ALPHA = 1.0;
";

	} else if (transparency != TRANSPARENCY_DISABLED || flags[FLAG_USE_SHADOW_TO_OPACITY] || (distance_fade == DISTANCE_FADE_PIXEL_ALPHA) || proximity_fade_enabled) {
		code += "	ALPHA *= albedo.a * albedo_tex.a;\n";
	}
	if (transparency == TRANSPARENCY_ALPHA_HASH) {
		code += "	ALPHA_HASH_SCALE = alpha_hash_scale;\n";
	} else if (transparency == TRANSPARENCY_ALPHA_SCISSOR) {
		code += "	ALPHA_SCISSOR_THRESHOLD = alpha_scissor_threshold;\n";
	}
	if (alpha_antialiasing_mode != ALPHA_ANTIALIASING_OFF && (transparency == TRANSPARENCY_ALPHA_HASH || transparency == TRANSPARENCY_ALPHA_SCISSOR)) {
		code += "	ALPHA_ANTIALIASING_EDGE = alpha_antialiasing_edge;\n";
		code += "	ALPHA_TEXTURE_COORDINATE = UV * vec2(albedo_texture_size);\n";
	}

	if (proximity_fade_enabled) {
		code += @"
	// Proximity Fade: Enabled
	float proximity_depth_tex = textureLod(depth_texture, SCREEN_UV, 0.0).r;
	vec4 proximity_view_pos = INV_PROJECTION_MATRIX * vec4(SCREEN_UV * 2.0 - 1.0, proximity_depth_tex, 1.0);
	proximity_view_pos.xyz /= proximity_view_pos.w;
	ALPHA *= clamp(1.0 - smoothstep(proximity_view_pos.z + proximity_fade_distance, proximity_view_pos.z, VERTEX.z), 0.0, 1.0);
";
	}

	if (distance_fade != DISTANCE_FADE_DISABLED) {
		// Use the slightly more expensive circular fade (distance to the object) instead of linear
		// (Z distance), so that the fade is always the same regardless of the camera angle.
		if ((distance_fade == DISTANCE_FADE_OBJECT_DITHER || distance_fade == DISTANCE_FADE_PIXEL_DITHER)) {
			code += "\n	{";

			if (distance_fade == DISTANCE_FADE_OBJECT_DITHER) {
				code += @"
		// Distance Fade: Object Dither
		float fade_distance = length((VIEW_MATRIX * MODEL_MATRIX[3]));
";
			} else {
				code += @"
		// Distance Fade: Pixel Dither
		float fade_distance = length(VERTEX);
";
			}
			code += @"
		// Use interleaved gradient noise, which is fast but still looks good.
		const vec3 magic = vec3(0.06711056, 0.00583715, 52.9829189);
		float fade = clamp(smoothstep(distance_fade_min, distance_fade_max, fade_distance), 0.0, 1.0);
		// Use a hard cap to prevent a few stray pixels from remaining when past the fade-out distance.
		if (fade < 0.001 || fade < fract(magic.z * fract(dot(FRAGCOORD.xy, magic.xy)))) {
			discard;
		}
	}
";
		} else {
			code += @"
	// Distance Fade: Pixel Alpha
	ALPHA *= clamp(smoothstep(distance_fade_min, distance_fade_max, length(VERTEX)), 0.0, 1.0);
";
		}
	}

	if (features[FEATURE_RIM]) {
		code += @"
	// Rim: Enabled
";
		if (flags[FLAG_UV1_USE_TRIPLANAR]) {
			code += "	vec2 rim_tex = triplanar_texture(texture_rim, uv1_power_normal, uv1_triplanar_pos).xy;\n";
		} else {
			code += "	vec2 rim_tex = texture(texture_rim, base_uv).xy;\n";
		}
		code += @"	RIM = rim * rim_tex.x;
	RIM_TINT = rim_tint * rim_tex.y;
";
	}

	if (features[FEATURE_CLEARCOAT]) {
		code += @"
	// Clearcoat: Enabled
";
		if (flags[FLAG_UV1_USE_TRIPLANAR]) {
			code += "	vec2 clearcoat_tex = triplanar_texture(texture_clearcoat, uv1_power_normal, uv1_triplanar_pos).xy;\n";
		} else {
			code += "	vec2 clearcoat_tex = texture(texture_clearcoat, base_uv).xy;\n";
		}
		code += @"	CLEARCOAT = clearcoat * clearcoat_tex.x;
	CLEARCOAT_ROUGHNESS = clearcoat_roughness * clearcoat_tex.y;
";
	}

	if (features[FEATURE_ANISOTROPY]) {
		code += @"
	// Anisotropy: Enabled
";
		if (flags[FLAG_UV1_USE_TRIPLANAR]) {
			code += "	vec3 anisotropy_tex = triplanar_texture(texture_flowmap, uv1_power_normal, uv1_triplanar_pos).rga;\n";
		} else {
			code += "	vec3 anisotropy_tex = texture(texture_flowmap, base_uv).rga;\n";
		}
		code += @"	ANISOTROPY = anisotropy_ratio * anisotropy_tex.b;
	ANISOTROPY_FLOW = anisotropy_tex.rg * 2.0 - 1.0;
";
	}

	if (features[FEATURE_AMBIENT_OCCLUSION]) {
		code += @"
	// Ambient Occlusion: Enabled
";
		if (!orm) {
			if (flags[FLAG_AO_ON_UV2]) {
				if (flags[FLAG_UV2_USE_TRIPLANAR]) {
					code += "	AO = dot(triplanar_texture(texture_ambient_occlusion, uv2_power_normal, uv2_triplanar_pos), ao_texture_channel);\n";
				} else {
					code += "	AO = dot(texture(texture_ambient_occlusion, base_uv2), ao_texture_channel);\n";
				}
			} else {
				if (flags[FLAG_UV1_USE_TRIPLANAR]) {
					code += "	AO = dot(triplanar_texture(texture_ambient_occlusion, uv1_power_normal, uv1_triplanar_pos), ao_texture_channel);\n";
				} else {
					code += "	AO = dot(texture(texture_ambient_occlusion, base_uv), ao_texture_channel);\n";
				}
			}
		} else {
			code += "	AO = orm_tex.r;\n";
		}

		code += "	AO_LIGHT_AFFECT = ao_light_affect;\n";
	}

	if (features[FEATURE_SUBSURFACE_SCATTERING]) {
		code += @"
	// Subsurface Scattering: Enabled
";
		if (flags[FLAG_UV1_USE_TRIPLANAR]) {
			code += "	float sss_tex = triplanar_texture(texture_subsurface_scattering, uv1_power_normal, uv1_triplanar_pos).r;\n";
		} else {
			code += "	float sss_tex = texture(texture_subsurface_scattering, base_uv).r;\n";
		}
		code += "	SSS_STRENGTH = subsurface_scattering_strength * sss_tex;\n";
	}

	if (features[FEATURE_SUBSURFACE_TRANSMITTANCE]) {
		code += @"
	// Subsurface Scattering Transmittance: Enabled
";
		if (flags[FLAG_UV1_USE_TRIPLANAR]) {
			code += "	vec4 trans_color_tex = triplanar_texture(texture_subsurface_transmittance, uv1_power_normal, uv1_triplanar_pos);\n";
		} else {
			code += "	vec4 trans_color_tex = texture(texture_subsurface_transmittance, base_uv);\n";
		}
		code += "	SSS_TRANSMITTANCE_COLOR = transmittance_color * trans_color_tex;\n";

		code += @"	SSS_TRANSMITTANCE_DEPTH = transmittance_depth;
	SSS_TRANSMITTANCE_BOOST = transmittance_boost;
";
	}

	if (features[FEATURE_BACKLIGHT]) {
		code += @"
	// Backlight: Enabled
";
		if (flags[FLAG_UV1_USE_TRIPLANAR]) {
			code += "	vec3 backlight_tex = triplanar_texture(texture_backlight, uv1_power_normal, uv1_triplanar_pos).rgb;\n";
		} else {
			code += "	vec3 backlight_tex = texture(texture_backlight, base_uv).rgb;\n";
		}
		code += "	BACKLIGHT = (backlight.rgb + backlight_tex);\n";
	}

	if (features[FEATURE_DETAIL]) {
		code += @"
	// Detail: Enabled
";
		bool triplanar = (flags[FLAG_UV1_USE_TRIPLANAR] && detail_uv == DETAIL_UV_1) || (flags[FLAG_UV2_USE_TRIPLANAR] && detail_uv == DETAIL_UV_2);
		if (triplanar) {
			string tp_uv = detail_uv == DETAIL_UV_1 ? "uv1" : "uv2";
			code += F(@"	vec4 detail_tex = triplanar_texture(texture_detail_albedo, %s_power_normal, %s_triplanar_pos);
	vec4 detail_norm_tex = triplanar_texture(texture_detail_normal, %s_power_normal, %s_triplanar_pos);
",
					tp_uv, tp_uv, tp_uv, tp_uv);
		} else {
			string det_uv = detail_uv == DETAIL_UV_1 ? "base_uv" : "base_uv2";
			code += F(@"	vec4 detail_tex = texture(texture_detail_albedo, %s);
	vec4 detail_norm_tex = texture(texture_detail_normal, %s);
",
					det_uv, det_uv);
		}

		if (flags[FLAG_UV1_USE_TRIPLANAR]) {
			code += "	vec4 detail_mask_tex = triplanar_texture(texture_detail_mask, uv1_power_normal, uv1_triplanar_pos);\n";
		} else {
			code += "	vec4 detail_mask_tex = texture(texture_detail_mask, base_uv);\n";
		}

		switch (detail_blend_mode) {
			case BLEND_MODE_MIX: {
				code += @"
	// Detail Blend Mode: Mix
	vec3 detail = mix(ALBEDO.rgb, detail_tex.rgb, detail_tex.a);
";
			} break;
			case BLEND_MODE_ADD: {
				code += @"
	// Detail Blend Mode: Add
	vec3 detail = mix(ALBEDO.rgb, ALBEDO.rgb + detail_tex.rgb, detail_tex.a);
";
			} break;
			case BLEND_MODE_SUB: {
				code += @"
	// Detail Blend Mode: Subtract
	vec3 detail = mix(ALBEDO.rgb, ALBEDO.rgb - detail_tex.rgb, detail_tex.a);
";
			} break;
			case BLEND_MODE_MUL: {
				code += @"
	// Detail Blend Mode: Multiply
	vec3 detail = mix(ALBEDO.rgb, ALBEDO.rgb * detail_tex.rgb, detail_tex.a);
";
			} break;
			case BLEND_MODE_PREMULT_ALPHA: {
				// This is unlikely to ever be used for detail textures, and in order for it to function in the editor, another bit must be used in MaterialKey,
				// but there are only 5 bits left, so I'm going to leave this disabled unless it's actually requested.
				//code += "\tvec3 detail = (1.0-detail_tex.a)*ALBEDO.rgb+detail_tex.rgb;\n";
			} break;
			case BLEND_MODE_MAX:
				break; // Internal value, skip.
		}

		code += @"	vec3 detail_norm = mix(NORMAL_MAP, detail_norm_tex.rgb, detail_tex.a);
	NORMAL_MAP = mix(NORMAL_MAP, detail_norm, detail_mask_tex.r);
	ALBEDO.rgb = mix(ALBEDO.rgb, detail, detail_mask_tex.r);
";
	}

	if (fragmentTail != null) { code += fragmentTail.TrimEnd((char)10) + (char)10; }
	code += "}\n";
		return code.Replace("\r\n", "\n");
	}

	/// Builds a handful of materials and returns each one's Generate(m) code. Must not throw.
	public static string[] SelfCheck()
	{
		var list = new System.Collections.Generic.List<string>();
		var img = Image.CreateEmpty(4, 4, false, Image.Format.Rgba8);
		var tex = ImageTexture.CreateFromImage(img);

		list.Add(Generate(new StandardMaterial3D()));

		var a = new StandardMaterial3D();
		a.AlbedoTexture = tex;
		a.NormalEnabled = true; a.NormalTexture = tex;
		a.RoughnessTexture = tex;
		a.EmissionEnabled = true; a.EmissionTexture = tex;
		a.Transparency = BaseMaterial3D.TransparencyEnum.AlphaScissor;
		a.VertexColorUseAsAlbedo = true;
		a.CullMode = BaseMaterial3D.CullModeEnum.Disabled;
		a.Uv1Scale = new Vector3(2, 3, 1); a.Uv1Offset = new Vector3(0.5f, 0.25f, 0);
		list.Add(Generate(a));

		var t = new StandardMaterial3D();
		t.AlbedoTexture = tex; t.Uv1Triplanar = true;
		list.Add(Generate(t));

		var o = new OrmMaterial3D();
		o.OrmTexture = tex;
		list.Add(Generate(o));

		var u = new StandardMaterial3D();
		u.ShadingMode = BaseMaterial3D.ShadingModeEnum.Unshaded;
		u.Transparency = BaseMaterial3D.TransparencyEnum.Alpha;
		list.Add(Generate(u));

		list.Add(Generate(u, "render_mode depth_draw_always;", "ALBEDO *= 0.5;"));
		return list.ToArray();
	}
}
