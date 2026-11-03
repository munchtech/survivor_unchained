// The Lamps board's type and marks in A (src/Ui/LampBoard.cs BoardInk): the knockout only (the edges' fade is the
// labels' own, set per label on the CPU), so no label or chip crosses the HUD's foot or her.
shader_type canvas_item;
#include "res://shaders/ui_lamps_field.gdshaderinc"

void fragment() {
	COLOR.a *= knock_mask(FRAGCOORD.xy);
}
