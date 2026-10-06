// Her hair where it thins to nothing (heroine_hair.gdshaderinc): the cap on her
// scalp as it fades out over her hairline, and the fine short hairs and baby
// hairs there, blended over her skin as they are faint, not cut by hashed
// alpha: a faint hair cut so is a scatter of dots, and her hairline read as
// a speckled band with a hard edge (the dots do not move, so the TAA keeps them).
shader_type spatial;
render_mode blend_mix, cull_disabled, depth_draw_never;

#define SOFT
#include "res://shaders/heroine_hair.gdshaderinc"
