// Her brows' dye, over her skin (People.HerPaint). The face paint itself is drawn in her skin since 20 October
// (heroine_skin.gdshader's face_paint); this pass draws it only with --paint-pass, to compare.
// Paint on her face (People.HerPaint; tools/assets/heroine_paint.py lays
// each design out on her head's own paint): drawn over her skin as a pass of
// its own, the same face a hair's breadth out, so it lies on the skin rather
// than in it (no light carried under it) and moves with her face as it is
// shaped, blinks and speaks. Its own sheen: chalky woad and ash, waxy kohl,
// bright gold leaf.
shader_type spatial;
render_mode blend_mix, depth_draw_never, cull_back;

#include "res://shaders/heroine_paint.gdshaderinc"
