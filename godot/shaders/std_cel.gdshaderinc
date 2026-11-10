// std_cel.gdshaderinc: the cel model put into the engine's own code for a StandardMaterial3D or ORMMaterial3D (L1 B2).
//
// The converter (src/World/CelLib.cs) takes Godot 4.5.1's generated shader for the material's feature set
// (src/World/StdCelCode.cs, a port of material.cpp's BaseMaterial3D::_update_shader), includes this right after its
// render_mode line and makes CEL_FRAGMENT; the last statement of its fragment(), then binds that shader to the
// material's own RID: every parameter the material sets (albedo, textures, roughness, emission, UVs ...) reaches it
// under the engine's own names, including the ones game code changes later (a hit flash, a fade). The class's numbers
// are set per material from godot/data/look/materials.json; the defaults here are the library's "stone" (the
// fallback class: rule 5's band, rule 6's matte, rule 8's ink 0), which godot/tests/MaterialLibraryTests.cs checks.
// The converter defines CEL_BUILTIN_RIM when the material has rim and CEL_CLEARCOAT when it has clearcoat, so the
// default light()'s A side (cel_on 0) is Godot's built-in light for it; --cel off converts nothing (today exactly).
#ifndef CEL_EXACT_ROUGH
#define CEL_EXACT_ROUGH
#endif
#define CEL_SPEC vec4(9.0, 1.5, 0.0, 0.85)
#include "res://shaders/cel.gdshaderinc"
