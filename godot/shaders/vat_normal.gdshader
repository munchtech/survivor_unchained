// The crowd's solid bodies with a normal map (vat.gdshader's twin): a
// variant of its own, so only the kinds that carry one pay for reading it.
shader_type spatial;
render_mode cull_back, depth_draw_opaque;

#define VAT_NORMAL
#include "res://shaders/vat.gdshaderinc"
