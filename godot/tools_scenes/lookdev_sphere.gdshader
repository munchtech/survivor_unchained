// The lookdev stage's material spheres (GameLookdev, L1 B0): the library's base classes on clean forms.
// A plain spatial shader on Godot's default light, the shared default path. When the cel include
// (shaders/cel.gdshaderinc, B1a) lands, adopt it here as its header says, so the spheres show the model.
shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;

uniform vec4 albedo_color : source_color = vec4(0.5, 0.5, 0.5, 1.0);
uniform float roughness : hint_range(0.0, 1.0) = 0.8;
uniform float metallic : hint_range(0.0, 1.0) = 0.0;
uniform float specular : hint_range(0.0, 1.0) = 0.5;

void fragment() {
	ALBEDO = albedo_color.rgb;
	ROUGHNESS = roughness;
	METALLIC = metallic;
	SPECULAR = specular;
}
