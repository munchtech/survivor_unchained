// Drawn last over her blended hair (src/Actors/HairDraw.cs): the colour left as
// it is (multiplied by white) and the alpha multiplied by `keep`. Godot hands
// FSR 2 the colour's alpha as its reactive mask, so blended hair would show as
// the near-raw jittered frame; erased, FSR 2 accumulates her hair as it does her
// skin. Swings with her hair (heroine_hair.gdshaderinc's vertex).
shader_type spatial;
render_mode blend_mul, unshaded, fog_disabled, depth_draw_never, cull_disabled;

#define ERASE
#include "res://shaders/heroine_hair.gdshaderinc"
