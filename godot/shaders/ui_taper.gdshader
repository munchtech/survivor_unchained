// A surface that has to run on fades out at its foot into what is behind it, instead of
// ending in an empty box (docs/design/UI_RESEARCH.md, "Waste no space"). Only the surface's
// own drawing fades: what it holds keeps clear of the fade.
shader_type canvas_item;

// Where the surface is gone, and how far above that it starts to go, in its own pixels.
uniform float foot = 1000.0;
uniform float fade = 110.0;

varying float y;

void vertex() {
	y = VERTEX.y;
}

void fragment() {
	float k = clamp((foot - y) / max(fade, 1.0), 0.0, 1.0);
	COLOR.a *= k * k;
}
