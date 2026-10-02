// The air thrown out by a blast: a ring racing outward over the ground that
// bends the picture behind it, with a faint bright lip. Drawn flat on the
// ground; COLOR.rgb is the lip's tint, COLOR.a its strength, and
// INSTANCE_CUSTOM.x how far it has gone (0 to 1).
shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;

uniform sampler2D screen : hint_screen_texture, filter_linear_mipmap;
uniform float width = 0.09;
uniform float bend = 0.035;

varying vec4 tint;
varying float k;
// Outward from the middle of the ring, in view space.
varying vec3 out_dir;

void vertex() {
	tint = COLOR;
	k = INSTANCE_CUSTOM.x;
	out_dir = (MODELVIEW_MATRIX * vec4(VERTEX.x, 0.0, VERTEX.z, 0.0)).xyz;
}

void fragment() {
	vec2 p = UV * 2.0 - 1.0;
	float r = length(p);
	float front = 0.15 + 0.85 * (1.0 - (1.0 - k) * (1.0 - k));
	float d = (r - front) / width;
	// Strongest just behind the front, gone at its leading edge.
	float ring = exp(-d * d * 3.0) * step(r, 1.0);
	float fade = (1.0 - k) * tint.a;
	// Pushed outward, in the direction the ring travels, on screen.
	vec4 a = PROJECTION_MATRIX * vec4(VERTEX, 1.0);
	vec4 b = PROJECTION_MATRIX * vec4(VERTEX + normalize(out_dir + 1e-5) * 0.5, 1.0);
	vec2 dir = normalize((b.xy / b.w - a.xy / a.w) + 1e-5);
	vec2 at = SCREEN_UV - dir * vec2(0.5, -0.5) * ring * fade * bend;
	vec3 seen = textureLod(screen, at, 0.0).rgb;
	// Mostly the bend; only a breath of the blast's own colour on its lip.
	ALBEDO = seen + tint.rgb * ring * ring * fade * 0.04;
	ALPHA = clamp(ring * fade * 1.5, 0.0, 1.0);
}
