// A likeness at a counter (Ui/Forge.cs, the person as a strip): no frame; its edges fade into the
// panel behind it, the foot most (a bust cut off square by a box reads as a photograph pasted on).
shader_type canvas_item;

void fragment() {
	// An oval a little above the middle, where the face sits.
	vec2 d = (UV - vec2(0.5, 0.42)) / vec2(0.5, 0.6);
	float a = 1.0 - smoothstep(0.7, 1.0, length(d));
	a *= 1.0 - smoothstep(0.72, 1.0, UV.y);
	COLOR.a *= a;
}
