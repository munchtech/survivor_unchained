// Paint on her face (People.HerPaint; tools/assets/heroine_paint.py lays
// each design out on her head's own paint): drawn over her skin as a pass of
// its own, the same face a hair's breadth out, so it lies on the skin rather
// than in it (no light carried under it) and moves with her face as it is
// shaped, blinks and speaks. Its own sheen: chalky woad and ash, waxy kohl,
// bright gold leaf.
shader_type spatial;
render_mode blend_mix, depth_draw_never, cull_back;

uniform sampler2D paint : source_color, filter_linear_mipmap_anisotropic;
uniform float rough = 0.7;
uniform float metal = 0.0;
uniform float strength = 1.0;

void vertex() {
	// (a tenth of a millimetre out, so it never fights the skin under it)
	VERTEX += NORMAL * 0.0001;
}

void fragment() {
	vec4 p = texture(paint, UV);
	ALBEDO = p.rgb;
	ALPHA = p.a * strength;
	ROUGHNESS = rough;
	METALLIC = metal;
	SPECULAR = 0.5;
}
