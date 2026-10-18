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
// (how much of the light its vertex colour gives it reaches it as her lips part (HerFaceLife.MouthShade): its colour
// was set for an open mouth (0.6); her lips parted a little (0.25) its tip, deep behind her teeth, read as a lit pink
// band across her mouth (c04a A5, judge F1, face 29))
uniform float open_light = 1.0;
uniform float fill = 0.15;
uniform float roughness = 0.45;
uniform float specular = 0.3;
uniform float shine = 0.15;     // (the lamps' sheen on it, x.15 of what it was, by its depth and darkening (COLOR.r*COLOR.g) so it dies toward its root and where it touches her lower teeth: a blue-white glint on its far raised edge there (judge r4))
// (judge a00723b7: its far side ended in a hard vertical line against her back teeth. Its side falls into their shade:
// its light cut by lat_amt from lat_in to lat_out m off her mouth's middle (lat_mid), its points taken to her head's own
// space (head_inv, set each frame by HerFaceLife.TongueFrame), so the shade stays on its sides as her head turns.
// Judged ON (judge abdb6549, 14 Oct): reads as a rounded tongue in shadow by the teeth; edge step 17-21 still over the 10 aim (a refinement).
uniform mat4 head_inv = mat4(1.0);
uniform float lat_amt = 0.85;
uniform float lat_in = 0.008;
uniform float lat_out = 0.018;
uniform float lat_mid = 0.0016;
varying float shade_k;
varying float shine_k;
varying float lat_x;

void vertex() {
	lat_x = abs((head_inv * vec4(VERTEX, 1.0)).x - lat_mid);
}

void fragment() {
	float k = COLOR.r * open_light;
	vec3 c = texture(paint, UV).rgb;
	c = mix(c, vec3(dot(c, vec3(0.3, 0.59, 0.11))), grey) * tint;
	float side = 1.0 - rim * (1.0 - smoothstep(0.0, 0.6, abs(dot(NORMAL, VIEW))));
	// (its vertex colour's green: darker where it touches her lower teeth and on its raised sides (heroine_mouth.py's
	// TOUCH, EDGE), so its edge there never reads lighter than its top (solver int3))
	float dark = COLOR.g * (1.0 - lat_amt * smoothstep(lat_in, lat_out, lat_x));
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
