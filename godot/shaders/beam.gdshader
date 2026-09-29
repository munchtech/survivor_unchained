// A column or band of light (a pillar from the sky, a beam, loot's light):
// brightest at the core, fading up its length, faded as a whole by alpha.
// Drawn on a mesh one unit tall centred on its origin (scaled to size);
// instances tint it by their colour.
shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;

uniform vec3 color : source_color = vec3(1.0);
uniform float energy = 2.0;
uniform float alpha = 1.0;
uniform float taper = 1.0;

varying vec3 tint;
varying float up;

void vertex() {
	tint = COLOR.rgb * COLOR.a;
	up = clamp(VERTEX.y + 0.5, 0.0, 1.0);
}

void fragment() {
	float along = mix(1.0, 1.0 - up, taper);
	float rim = pow(abs(dot(NORMAL, VIEW)), 1.5);
	ALBEDO = color * tint * energy * along * rim * alpha;
}
