// Her brows on deep skin (People.HerPaint, face 40 r2): heroine_paint.gdshader's brows as a multiply over her skin's
// own lit colour, so they keep its warm subsurface light (see heroine_paint.gdshaderinc's MUL).
shader_type spatial;
render_mode blend_mul, unshaded, depth_draw_never, cull_back;
#define MUL
#include "res://shaders/heroine_paint.gdshaderinc"
