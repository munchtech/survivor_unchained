p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-af551cacc6292152f\godot\shaders\vat.gdshaderinc"
s = open(p, encoding="utf-8").read()
old = '''// The crowd's vertex animation, shared by vat.gdshader (solid bodies, one
// side) and vat_cut.gdshader (fur and hair cards: two sides, cut by alpha).
// See vat.gdshader for what it does.
'''
new = '''// The crowd's vertex animation, shared by vat.gdshader (solid bodies, one
// side), vat_cut.gdshader (fur and hair cards: two sides, cut by alpha) and
// vat_normal.gdshader (solid, with a normal map). See vat.gdshader for what
// it does.
'''
assert old in s; s = s.replace(old, new)
old = '''uniform float dye_lum = 0.25;
'''
new = '''uniform float dye_lum = 0.25;

#ifdef VAT_NORMAL
// A tangent-space normal map (OpenGL's: green up the texture). Only the
// kinds that have one are drawn with this variant.
uniform sampler2D normal_tex : hint_normal, filter_linear_mipmap, repeat_enable;
uniform float normal_depth = 1.0;
#endif
'''
assert old in s; s = s.replace(old, new)
old = '''	vec3 c = albedo.rgb;
	vec4 tex = use_tex ? texture(albedo_tex, UV) : vec4(1.0);'''
new = '''#ifdef VAT_NORMAL
	{
		// No tangents are baked (the textures hold only where each vertex is
		// and which way it faces), so the frame is built per pixel from how
		// the position and the UV change across it: a cotangent frame, which
		// also holds where the UVs are mirrored.
		vec3 dp1 = dFdx(VERTEX), dp2 = dFdy(VERTEX);
		vec2 duv1 = dFdx(UV), duv2 = dFdy(UV);
		vec3 dp2perp = cross(dp2, NORMAL), dp1perp = cross(NORMAL, dp1);
		vec3 t = dp2perp * duv1.x + dp1perp * duv2.x;
		vec3 b = dp2perp * duv1.y + dp1perp * duv2.y;
		float invmax = inversesqrt(max(max(dot(t, t), dot(b, b)), 1e-20));
		vec2 nxy = (texture(normal_tex, UV).xy * 2.0 - 1.0) * normal_depth;
		float nz = sqrt(max(0.0, 1.0 - dot(nxy, nxy)));
		// (UV.y runs down the texture, the map's green up it.)
		NORMAL = normalize(t * invmax * nxy.x - b * invmax * nxy.y + NORMAL * nz);
	}
#endif
	vec3 c = albedo.rgb;
	vec4 tex = use_tex ? texture(albedo_tex, UV) : vec4(1.0);'''
assert old in s; s = s.replace(old, new)
open(p, "w", encoding="utf-8").write(s)
print("ok")
