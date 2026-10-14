// Her tongue (People.HerPart), in her mouth's shade. Its vertex colour (tools/assets/heroine_mouth.py: 1 at its tip,
// down to 0.12 at its root) is how much light her mouth lets in to it. As a StandardMaterial lit by every lamp it
// showed the lamps' shadow maps, too coarse at this scale: a hatched grain over it and a hard black edge where her
// lip's corner cut a lamp off, with a white sheen spot at its tip (the smile pass, e1). So it takes no shadows; the
// lamps reach it as a share (lamps) of its shade, the sky as its shade, and it gives off a little of the mouth's own
// dark red where the light can't reach (fill), as the inside of her mouth does (heroine_skin's mouth_fill).
shader_type spatial;
render_mode shadows_disabled;

uniform sampler2D paint : source_color, filter_linear_mipmap, hint_default_white;
uniform vec3 tint : source_color = vec3(0.86, 0.66, 0.6);      // (its paint, a bright salmon, made a muted rose: at
//                                 (0.9, 0.72, 0.72) its front read (132-153, 71-88, 66-92), blue up to its green, pink (solver int2))
uniform float grey = 0.42;      // (its paint's colour eased so far toward its own grey: a rose, not a crimson slab (j2))
uniform float rim = 0.6;        // (its sides, turned from the eye, darkened so far toward the mouth's dark: rounded, no
//                                 hard edge against what is behind it (j2))
uniform vec3 inside : source_color = vec3(0.42, 0.15, 0.14);  // (the mouth's own dark red, heroine_skin's mouth_colour)
uniform float lamps = 0.6;
uniform float fill = 0.15;
uniform float roughness = 0.45;
uniform float specular = 0.3;
uniform float shine = 0.15;     // (the lamps' sheen on it, x.15 of what it was, by its depth and darkening (COLOR.r*COLOR.g) so it dies toward its root and where it touches her lower teeth: a blue-white glint on its far raised edge there (judge r4))
varying float shade_k;
varying float shine_k;

void fragment() {
	float k = COLOR.r;
	vec3 c = texture(paint, UV).rgb;
	c = mix(c, vec3(dot(c, vec3(0.3, 0.59, 0.11))), grey) * tint;
	float side = 1.0 - rim * (1.0 - smoothstep(0.0, 0.6, abs(dot(NORMAL, VIEW))));
	// (its vertex colour's green: darker where it touches her lower teeth and on its raised sides (heroine_mouth.py's
	// TOUCH, EDGE), so its edge there never reads lighter than its top (solver int3))
	float dark = COLOR.g;
	ALBEDO = c * side * dark;
	AO = k * k;
	AO_LIGHT_AFFECT = 0.0;
	shade_k = k * k * side;
	shine_k = shine * k * dark;
	ROUGHNESS = roughness;
	SPECULAR = specular * k * dark;
	EMISSION = inside * fill * (1.0 - 0.5 * k) * dark;
}

void light() {
	DIFFUSE_LIGHT += lamps * shade_k * clamp(dot(NORMAL, LIGHT), 0.0, 1.0) * ATTENUATION * LIGHT_COLOR / PI;
	vec3 h = normalize(VIEW + LIGHT);
	float s = pow(clamp(dot(NORMAL, h), 0.0, 1.0), mix(8.0, 128.0, 1.0 - ROUGHNESS));
	SPECULAR_LIGHT += lamps * shade_k * shine_k * SPECULAR_AMOUNT * s * ATTENUATION * LIGHT_COLOR * clamp(dot(NORMAL, LIGHT), 0.0, 1.0);
}
