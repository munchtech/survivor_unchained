// The den's painted set (den round 10, DungeonDress.Set.cs; the paintings by tools/look/den_set.py): each module is the
// painting laid in the camera's plane and cast along the play camera's view onto its proxy (the bank's surface and the
// floor for the banks, a half-ellipsoid on the floor for a boulder), so every painted pixel sits at the depth of the
// ground it shows: she stands in front of the far bank, behind the near bank's crest, on the roots spilled on the floor.
// The painting is already lit and shaded (its lit tops, cool gaps and ink): the room's light only scales it (no cel bands,
// no n.l from the key; a soft turn for the shafts' spots and the fungus' omnis), as the round 6 boulders.
// COLOR.r: the module's fade (1 shown; toward 0 only its brightest masses, so a module laid over its neighbour shows its
// roots crossing the other's and never a seam); COLOR.g: 0 where the cast landed on walkable floor beyond the bank.
shader_type spatial;
render_mode cull_disabled, depth_draw_opaque, specular_disabled;
#include "res://shaders/den_set.gdshaderinc"
