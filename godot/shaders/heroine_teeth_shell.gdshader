// Her teeth's gaps filled while her lips are parted a little (a next pass on heroine_teeth, set by
// HerFaceLife.TeethDrop only while its band is on: mouth_open about 0.25, none shut or by 0.6). Both rows (the upper
// dropped as heroine_teeth drops it), grown by grow (metres, at her head's scale) across (its normals less their part along the drop) and drawn from behind
// (cull_front): it shows only where the teeth themselves don't, in the gaps and notches between her incisors, and there
// in heroine_teeth's band shade (band_col by height, flat, the same light; the lower row's band_lower). Without it those notches read as chips
// and black pockets between grey shards (c04a A5, judge F1 r2, face 30). Nothing drawn on her gums.
// (No shadows on it: inside the teeth, their own shadow fell on it, the gaps black again)
shader_type spatial;
render_mode cull_front, shadows_disabled;

uniform sampler2D paint : source_color, filter_linear_mipmap, hint_default_white;
uniform sampler2D upper_mask : filter_nearest, hint_default_black;
uniform int mask_w = 256;
uniform vec3 drop_v = vec3(0.0);
uniform float grow = 0.0004;
uniform float band = 0.0;
uniform vec3 band_col : source_color = vec3(0.9, 0.84, 0.68);
uniform float band_low = 0.35;
uniform float band_glow = 0.15;
uniform float band_lower = 0.6;
uniform float lit = 1.0;
uniform float side_floor = 0.8;
uniform float narrow = 0.0;
uniform float closed = 0.2;
varying float up_w;
varying float up_t;

void vertex() {
	vec4 um = texelFetch(upper_mask, ivec2(VERTEX_ID % mask_w, VERTEX_ID / mask_w), 0);
	up_w = um.r; up_t = um.g;
	// (grown across, not down: its normal less its part along the drop, so the gaps close and her incisors' edge stays)
	vec3 dn = dot(drop_v, drop_v) > 0.0 ? normalize(drop_v) : vec3(0.0, -1.0, 0.0);
	VERTEX += drop_v * um.r + (NORMAL - dn * dot(NORMAL, dn)) * grow;
}

void fragment() {
	vec3 p = texture(paint, UV).rgb;
	float tooth = band * (1.0 - smoothstep(0.08, 0.25, p.r - p.b));
	if (tooth < 0.5) discard;
	float bw = smoothstep(0.5, 1.0, up_w);
	float k = max(COLOR.r, side_floor * narrow * lit) * mix(closed, 1.0, lit);
	float f = pow(k, 2.2);
	vec3 bc = band_col * mix(band_lower, mix(1.0, band_low, smoothstep(0.0, 1.0, up_t)), bw);
	ALBEDO = bc;
	NORMAL = VIEW;
	SPECULAR = 0.1 * f;
	ROUGHNESS = 0.8;
	AO = f;
	AO_LIGHT_AFFECT = 1.0;
	EMISSION = bc * band_glow * f;
}
