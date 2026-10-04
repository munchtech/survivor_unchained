// What a skill makes grow out of the ground for a moment (src/Fx/BattleFx.Skills.cs,
// Spikes): ice, thorns, stone. Lit like a hard thing, its edges catching the
// light of its school (a rim brightest where it turns from the eye), so a
// spike reads against the ground and the pale dead alike. COLOR is its
// colour, COLOR.a how much it glows (it fades as it sinks).
shader_type spatial;
render_mode cull_back;

uniform float emit = 0.4;
uniform float rim = 2.4;
uniform float gloss = 0.1;

void fragment() {
	float fres = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 2.2);
	ALBEDO = COLOR.rgb * 0.4;
	ROUGHNESS = gloss;
	SPECULAR = 0.8;
	EMISSION = COLOR.rgb * (emit + fres * rim) * COLOR.a;
}
