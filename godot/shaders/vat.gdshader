// A crowd drawn from vertex-animation textures (Actors/Vat.cs; the web
// game's render/vat.ts). Every vertex reads where it is, and which way it
// faces, from two textures written when the kind of creature was baked: one
// texel per vertex per frame. Each instance carries (INSTANCE_CUSTOM) the two
// frames it is between and how far, and a packed word of what is happening
// to it: a hit's flash, dissolving, frozen, burning. Its colour (the
// MultiMesh colour, multiplied into COLOR with the vertex colour) tints it,
// and its alpha is a glow of its own colour.
shader_type spatial;
render_mode cull_back, depth_draw_opaque;

#include "res://shaders/vat.gdshaderinc"


