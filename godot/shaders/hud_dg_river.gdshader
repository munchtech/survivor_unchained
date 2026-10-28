// UI 17, the Drowned Girl's river (--hud drowned, DgRiver.cs): the river's art as drawn (its modulate and fade kept),
// with the bronze's idle sheen: the same slow band hud_dg_orb.gdshader sweeps over her figure, in screen px, so it runs
// from her on into the river, once every 10 s and still between. Only the raised, lit bronze takes it.
// UI 18: the experience light (hud_dg_xp.gdshaderinc) runs on the river on a gain; at rest it does nothing.
shader_type canvas_item;
#include "res://shaders/hud_dg_xp.gdshaderinc"

uniform vec2 scr_at = vec2(553.0, 833.0);   // the art's top left on the 1080 screen
uniform vec2 size = vec2(1051.0, 247.0);    // its size on the 1080 screen

float sheen(vec2 s, float t)
{
	float ph = mod(t + 3.0, 10.0);
	float x = s.x + 0.45 * (s.y - 950.0);
	float pos = 180.0 + ph * 480.0;
	return exp(-pow((x - pos) / 55.0, 2.0)) * (1.0 - smoothstep(2.9, 3.2, ph));
}

void fragment()
{
	vec4 c = COLOR;
	float lum = dot(c.rgb, vec3(0.3, 0.59, 0.11));
	c.rgb += c.rgb * vec3(0.55, 0.45, 0.30) * sheen(scr_at + UV * size, TIME) * smoothstep(0.16, 0.45, lum);
	if (xp_on > 0.5) c.rgb = xp_light(c.rgb, scr_at + UV * size, 1.0, 1.0);
	COLOR = c;
}
