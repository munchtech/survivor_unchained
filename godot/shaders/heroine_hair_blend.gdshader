// Her hair (heroine_hair.gdshader) blended to its strands' own cover, not cut:
// soft and still in every frame, so FSR 2 has nothing to average (a cut that
// moves or a hashed one crawls under it). Its solid parts are drawn first in
// the depth prepass (Godot's depth_prepass_alpha: cover 0.99 and up), so what
// lies behind them is hidden, and the strands are blended in the order the
// cards were made, the layers nearest her first (src/Actors/HairDraw.cs).
shader_type spatial;
render_mode blend_mix, depth_prepass_alpha, cull_disabled;

#define BLEND
#include "res://shaders/heroine_hair.gdshaderinc"
