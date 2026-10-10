// Her hair's solid parts under MSAA (the Look): heroine_hair_core.gdshader with
// the cut's edge spread over the samples (alpha to coverage), so the core's edge
// over her skin is soft, not a stepped dark rim. src/Actors/HairDraw.cs swaps
// the two as MSAA comes and goes (Graphics.Apply).
shader_type spatial;
render_mode cull_disabled, depth_draw_opaque, alpha_to_coverage;

#define CORE
#define CORE_A2C
#include "res://shaders/heroine_hair.gdshaderinc"
