// (r10d) The den's hole paintings (H1 hollows, H2 the pit: DungeonDress.Set.cs PlaceSetHole): the set's body, blended
// at the painting's fading surround (alpha) instead of cut, so the earth round a hole fades into the floor.
shader_type spatial;
render_mode cull_disabled, depth_draw_never, specular_disabled, blend_mix;
#define SET_SOFT
#include "res://shaders/den_set.gdshaderinc"
