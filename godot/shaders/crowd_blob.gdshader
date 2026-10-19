// The ground darkened softly under a crowd body (Actors/Vat.cs, VatCrowd): the crowd casts no shadow in play
// (E1: shadow draws), and without one a mob floated over moonlit ground beside her long shadow. One flat quad per
// body in one MultiMesh per kind, multiplied over what is drawn: no shadow map, a few pixels each. The instance's
// colour alpha is how much it shows (a dissolving body's fades with it).
shader_type spatial;
render_mode unshaded, blend_mul, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;

uniform float strength = 0.6;

void fragment() {
	float d = length(UV - 0.5) * 2.0;
	float a = 1.0 - smoothstep(0.0, 1.0, d);
	a *= a;
	ALBEDO = vec3(1.0 - a * strength * COLOR.a);
}
