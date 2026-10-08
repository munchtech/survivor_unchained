// Her hair (heroine_hair.gdshader) blended to its strands' own cover over its
// solid parts (heroine_hair_core.gdshader, the pass before): soft at every
// edge, and still in every frame (src/Actors/HairDraw.cs).
shader_type spatial;
render_mode blend_mix, depth_draw_never, cull_disabled;

#define OVER
#include "res://shaders/heroine_hair.gdshaderinc"
