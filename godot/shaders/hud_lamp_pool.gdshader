// HUD A2 "Lamps Are Lit": the life lamp's light on the ground (LifeLamp.Pool). A local screen-space
// light under the whole HUD: one quad round the lamp's foot reads the world under it (a BackBufferCopy of that
// rect only) and lifts it: scene x (1 + gain x falloff), warm. It brightens, never only tints (round 1's real
// light read as a rust stain on brown ground and vanished under canopy), and it multiplies, so whatever stands
// in it stays readable. Its gain is the flame's light (LampState.Light, its flicker included): about +45% (brightness) at
// full, +20% at 55%, a flickering +6% guttering, none out.
shader_type canvas_item;
render_mode blend_mix;

uniform sampler2D screen : hint_screen_texture, filter_linear;
uniform float gain = 0.54;
uniform vec2 size = vec2(480.0, 300.0);     // the quad (1080 px)
uniform vec2 centre = vec2(240.0, 220.0);   // the pool's heart in the quad: the lamp's foot
uniform vec2 radii = vec2(250.0, 175.0);
uniform vec4 tint : source_color = vec4(1.0, 0.84, 0.60, 1.0);

void fragment()
{
	vec2 p = (UV * size - centre) / radii;
	float r2 = dot(p, p);
	if (r2 >= 1.0 || gain <= 0.0005) discard;
	// a pool: full round the lamp's foot (its heart is under the lamp: the light shows round it), easing out to
	// nothing at its edge
	float f = 1.0 - smoothstep(0.3, 1.0, sqrt(r2));
	vec3 scene = texture(screen, SCREEN_UV).rgb;
	vec3 lift = vec3(1.0) + gain * f * tint.rgb;
	// (a breath of warm light on near-black ground, where a lift alone shows nothing)
	COLOR = vec4(scene * lift + tint.rgb * 0.035 * gain * f, 1.0);
}
