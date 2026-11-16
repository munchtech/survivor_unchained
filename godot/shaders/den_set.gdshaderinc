// The den's painted set's body (den_set.gdshader cuts at alpha 0.5; den_set_soft.gdshader blends: the hole paintings).

uniform sampler2D paint_tex : source_color, filter_linear_mipmap_anisotropic, repeat_disable;
uniform float gain = 1.0;                       // the painting's albedo scale (calibrated on the den's frames)
uniform vec3 tint = vec3(1.0);
uniform float sat = 1.0;
uniform float cold_take = 0.5;                  // how much of a cold light's brightness it takes (never its colour)
uniform float local_turn = 0.5;                 // how much a spot or omni follows the proxy's normal (0 flat)
uniform float key_shadow = 0.0;                 // 1: the key's shadow falls on it (her shadow on a spill); 0: pre-lit only
// (round 10b) The painting's own shade goes cool grey-violet, its lit masses keep their warmth: the targets' darks between
// the roots are blue-grey (90% of their pixels under 20 of 255 have B >= R), their lit root tops warm. By the painting's own
// luminance (linear): under shade_lo all shade_tint, over shade_hi all the painting's colour.
uniform vec3 shade_tint = vec3(0.84, 0.92, 1.2);
uniform float shade_lo = 0.01;
uniform float shade_hi = 0.08;
uniform float shade_k = 1.0;
// (r10c) The darks between the roots never go black: the targets' sit at L 12-20 of 255, cool; the painting's own darks
// lit at least dark_floor (an emission in shade_tint, fading out over the painting's darkest 5%), whatever light reaches them.
uniform float dark_floor = 0.0;
// (r10c) and the painting shows at least amb_floor of its own painted value where little light reaches (the frame's edges
// fell to 1/20 of it: flat black between roots the target paints at L 20-40)
uniform float amb_floor = 0.0;
uniform float glow_k = 0.7;
uniform float fg_dark = 0.65;
uniform float rim_in = 1.15;    // (r11, the hole paintings) the surround shown to this many lip radii, gone by rim_out
uniform float rim_out = 1.45;

void fragment() {
	vec4 c = texture(paint_tex, UV);
	float lb = dot(textureLod(paint_tex, UV, 3.0).rgb, vec3(0.299, 0.587, 0.114));
	float s = smoothstep(0.1, 0.4, sqrt(max(lb, 0.0)));
	float show = step(1.0, s + COLOR.r + 0.001);
	vec3 col = c.rgb * tint;
	float l = dot(col, vec3(0.299, 0.587, 0.114));
	col = mix(vec3(l), col, sat);
	col = mix(col, vec3(l) * shade_tint, shade_k * (1.0 - smoothstep(shade_lo, shade_hi, l)));
	ALBEDO = col * gain * mix(1.0, fg_dark, smoothstep(0.82, 1.0, SCREEN_UV.y));   // (r11 judge: the nearest banks fall off, as den_room.png's bottom row)
	EMISSION = col * gain * amb_floor + shade_tint * dark_floor * (1.0 - smoothstep(0.0, 0.05, l));
	// (r10d) the painted glow caps (pale cyan: G and B well over R) give their own light, whatever reaches them
	EMISSION += c.rgb * glow_k * smoothstep(0.05, 0.2, min(c.g, c.b) - c.r);
	ALPHA = c.a * show * step(0.5, COLOR.g);
#ifdef SET_SOFT
	// (r11) a hole painting's own earth surround fades out past its rim (COLOR.b: half the distance in lip radii)
	ALPHA *= 1.0 - smoothstep(rim_in, rim_out, 2.0 * COLOR.b);
#endif
#ifndef SET_SOFT
	ALPHA_SCISSOR_THRESHOLD = 0.5;
#endif
	// the ink tag (cel.gdshaderinc's cel_tag): roughness 1, class 2 (no post ink: the painting carries its own)
	ROUGHNESS = 126.0 / 127.0;
}

void light() {
	float w = LIGHT_IS_DIRECTIONAL ? 1.0 : mix(1.0, max(dot(NORMAL, LIGHT), 0.0), local_turn);
	vec3 lc = LIGHT_COLOR;
	float ll = dot(lc, vec3(0.299, 0.587, 0.114));
	lc = LIGHT_IS_DIRECTIONAL || lc.r >= lc.g ? lc : vec3(ll) * cold_take;
	float att = LIGHT_IS_DIRECTIONAL ? mix(1.0, ATTENUATION, key_shadow) : ATTENUATION;
	DIFFUSE_LIGHT += lc * att * w / PI;
}
