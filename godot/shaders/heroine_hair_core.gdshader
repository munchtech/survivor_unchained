// Her hair's solid parts (heroine_hair.gdshader): where a strand covers nearly
// all of a pixel, drawn opaque, so the depth, the motion the temporal smoothing
// follows and the ambient occlusion are hers there; the whole is drawn again
// over it, blended, by its next pass (heroine_hair_over.gdshader;
// src/Actors/HairDraw.cs).
shader_type spatial;
render_mode cull_disabled, depth_draw_opaque;

#define CORE
#include "res://shaders/heroine_hair.gdshaderinc"
