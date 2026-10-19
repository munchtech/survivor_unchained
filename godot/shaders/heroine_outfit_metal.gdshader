// Her outfits' metal (every key of kind metal in art/people/outfit_materials.json): heroine_outfit.gdshader's
// body with metal's own light (a highlight shoulder: no blown domes by a fire) and its reflection held to
// what it can see (no probe: the sky's reflection kept only in part, least at the horizon and in recesses).
// The look bible's armor-metal page (docs/art/look_bible/01_armor_metal.md).
shader_type spatial;

#define OUTFIT_METAL_LIGHT
#include "res://shaders/heroine_outfit.gdshaderinc"
