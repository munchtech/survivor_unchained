// The crowd's fur and hair cards (vat.gdshader's cut-out twin): both sides
// drawn, and cut where the texture's alpha is clear.
shader_type spatial;
render_mode cull_disabled, depth_draw_opaque;

#define VAT_CUT
#include "res://shaders/vat.gdshaderinc"
