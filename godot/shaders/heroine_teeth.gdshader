// Her teeth (People.HerPart): their paint, in the mouth's own shade.
// Her side teeth stand in the cheeks' shade (the buccal corridor): the mesh's grey vertex colour
// (tools/assets/heroine_teethshade.py, 1 over the front teeth, down to 0.2 at the sides; white where a
// mesh has none) eases them toward the warm dark of the inside of her cheek, and their sheen with them
// (a dark tooth with a white sheen read as a steel-grey bead). With her lips closed the whole row is
// in that shade too (lit, set each frame by HerFaceLife.TeethLight from how far her lips part).
shader_type spatial;
render_mode cull_disabled;

uniform sampler2D paint : source_color, filter_linear_mipmap, hint_default_white;
uniform float lit : hint_range(0.0, 1.0) = 1.0;
uniform vec3 cheek : source_color = vec3(0.42, 0.24, 0.20);  // (the inside of her cheek, sRGB)
uniform float closed = 0.2;      // (her lips closed: how much of the front teeth's light is left)
uniform float roughness = 0.35;

void fragment() {
	float s = COLOR.r;
	vec3 c = texture(paint, UV).rgb;
	// (the shade: toward the cheek's warm dark, never grey)
	float k = s * mix(closed, 1.0, lit);
	ALBEDO = c * mix(cheek, vec3(1.0), k) * mix(0.55, 1.0, k);
	SPECULAR = 0.5 * k * k;
	ROUGHNESS = mix(0.75, roughness, k);
}
