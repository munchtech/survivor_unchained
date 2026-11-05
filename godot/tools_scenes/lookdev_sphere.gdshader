// The lookdev stage's material spheres (GameLookdev, L1 B0): the library's base classes on clean forms.
// A plain spatial shader on the shared default path, adopting the cel model (shaders/cel.gdshaderinc) as its
// header says: ink 0 (full), CEL_FRAGMENT last, the include's default light(). At cel_on 0 (--cel off) that is
// Godot's built-in Burley + Schlick-GGX exactly; cel on, the spheres show the model.
shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;
#define CEL_INK 0
#include "res://shaders/cel.gdshaderinc"

uniform vec4 albedo_color : source_color = vec4(0.5, 0.5, 0.5, 1.0);
uniform float roughness : hint_range(0.0, 1.0) = 0.8;
uniform float metallic : hint_range(0.0, 1.0) = 0.0;
uniform float specular : hint_range(0.0, 1.0) = 0.5;

void fragment() {
	ALBEDO = albedo_color.rgb;
	ROUGHNESS = roughness;
	METALLIC = metallic;
	SPECULAR = specular;
	CEL_FRAGMENT;
}
