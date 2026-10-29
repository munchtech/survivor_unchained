// A braid's ropes of hair (her cap's strands with blue 0.5 or more,
// heroine_hair.gdshaderinc) drawn solid first, so their depth, motion and
// ambient occlusion are written; the cap is drawn again over it, blended, by
// its next pass (heroine_hair_soft.gdshader). Blended alone (Face 48), a rope
// wrote no depth, and the loose hair cards inside and behind it, blended after
// it (heroine_hair_over.gdshader), were drawn over it: a see-through net.
// The rest of the cap is not drawn here (src/Actors/HairDraw.cs: RopeCore).
shader_type spatial;
render_mode cull_disabled, depth_draw_opaque;

#define CORE
#define ROPE_CORE
#include "res://shaders/heroine_hair.gdshaderinc"
