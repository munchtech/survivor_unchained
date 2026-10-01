// Her (Actors/People.cs, the woman survivor's body): the figure's own paint,
// with a mask baked beside it (tools/assets/woman_body.py: red her skin,
// green her hair, blue her suit) saying what takes which choice. Her skin
// takes the tone chosen, lighter or darker as the paint was (her eyes keep
// theirs); her hair takes its colour and her suit the calling's
// cloth, each shaded as the paint was. A rim of light at the edge, as on everyone.
shader_type spatial;

uniform sampler2D tex : source_color, filter_linear_mipmap_anisotropic;
uniform sampler2D normal_tex : hint_normal, filter_linear_mipmap_anisotropic;
uniform sampler2D mask : hint_default_black, filter_linear_mipmap;
// The paint's own skin (as lit: its shading is carried over), hair and suit,
// as woman_body.py measures them (set by People.Woman, as is everything chosen).
uniform vec3 paint_skin : source_color = vec3(0.867, 0.678, 0.624);
uniform vec3 paint_hair : source_color = vec3(0.553, 0.451, 0.353);
uniform vec3 paint_suit : source_color = vec3(0.153, 0.176, 0.208);
// What was chosen.
uniform vec3 skin : source_color = vec3(0.867, 0.678, 0.624);
uniform bool dye_hair = false;
uniform vec3 hair : source_color = vec3(0.37, 0.24, 0.16);
uniform bool dye_suit = false;
uniform vec3 cloth : source_color = vec3(0.24, 0.25, 0.27);
// A suit dyed is darker than the cloth's swatch: close-fitting, oiled.
uniform float suit_depth = 0.62;
uniform float rim_amount = 0.45;
uniform float rim_tint = 0.35;

float lum(vec3 c) { return dot(c, vec3(0.2126, 0.7152, 0.0722)); }

void fragment() {
	vec3 t = texture(tex, UV).rgb;
	vec3 m = texture(mask, UV).rgb;
	m /= max(m.r + m.g + m.b, 1e-3);
	// Skin: the paint carried over to the tone chosen, texel by texel (her
	// shading, her lips, as they were against her own); what the mask calls
	// skin but is not (the whites of her eyes, her teeth: greys; her irises:
	// bluer than red) keeps its paint.
	float hi = max(t.r, max(t.g, t.b)), lo = min(t.r, min(t.g, t.b));
	float is_skin = m.r * smoothstep(0.12, 0.22, (hi - lo) / max(hi, 1e-3)) * step(t.b, t.r);
	vec3 col = mix(t, t * skin / max(paint_skin, vec3(1e-3)), is_skin);
	if (dye_hair) col = mix(col, hair * clamp(lum(t) / lum(paint_hair), 0.0, 2.5), m.g);
	if (dye_suit) col = mix(col, cloth * suit_depth * clamp(lum(t) / lum(paint_suit), 0.0, 3.0), m.b);
	ALBEDO = col;
	NORMAL_MAP = texture(normal_tex, UV).rgb;
	// Skin, hair, and the suit's satin (not a wet latex).
	ROUGHNESS = 0.62 * m.r + 0.7 * m.g + 0.56 * m.b;
	SPECULAR = 0.35 + 0.05 * m.b;
	RIM = rim_amount;
	RIM_TINT = rim_tint;
}
