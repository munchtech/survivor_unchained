// Her hair (heroine_hair.gdshader), cut to its strands by a threshold that moves
// every frame (coverage.gdshaderinc) in place of Godot's hashed alpha, so a
// temporal smoothing sums it into soft, still strands (src/View/Coverage.cs).
shader_type spatial;
render_mode cull_disabled, depth_draw_opaque;

#define COVERAGE
#include "res://shaders/heroine_hair.gdshaderinc"
