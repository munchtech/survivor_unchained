// Her hair (tools/assets/heroine_hair.py's cards): the strands' atlas, grey,
// dyed her colour, each strand and each lock a little lighter or darker than
// the next; darker at the root and deep in the hair (its vertex colour); cut
// to its strands by hashed alpha (smoothed over frames by the TAA). Lit as
// hair is, not as a surface: light along a strand, not across it (Kajiya-Kay),
// a white highlight off its outside and a second, her colour, from light gone
// through it, shifted apart along the strand; light wrapping round it and
// through it from behind (red hair glows against the light).
shader_type spatial;
render_mode cull_disabled, depth_draw_opaque;

#include "res://shaders/heroine_hair.gdshaderinc"
