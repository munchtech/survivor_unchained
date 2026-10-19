// A lamp's iron lit by its own flame (World/Lamps.cs, next pass over the holder's iron; look bible 10). The
// zone's light leaves the holder out (ZoneView.LampLayer: a hand from the iron it flared it white); this lays
// the flame's colour on the faces that look at the flame instead, with a soft falloff that never blows up
// close in: the burner, the cage floor, the posts' and the hood's inner faces glow, the outside stays dark.
shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, cull_back, shadows_disabled, fog_disabled;

uniform vec3 flame_at;
uniform vec3 color : source_color = vec3(1.0, 0.62, 0.32);
uniform float strength = 0.5;
uniform float radius = 0.15;
uniform float iron = 0.14;
uniform float lit = 1.0;

varying vec3 wpos;
varying vec3 wnorm;

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	wnorm = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

void fragment() {
	vec3 d = flame_at - wpos;
	float r = max(length(d), 1e-3);
	float ndl = max(dot(normalize(wnorm), d / r), 0.0);
	float fall = 1.0 / (1.0 + (r / radius) * (r / radius)) * (1.0 - smoothstep(radius * 2.5, radius * 4.0, r));
	ALBEDO = color * (strength * lit * iron * ndl * fall);
}
