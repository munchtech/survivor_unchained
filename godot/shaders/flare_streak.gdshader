// The Long Cut's light shapes (Fx/Flare/FlareFx.LongCutLight.cs): a camera-facing strip between two points, additive.
// The blade's white-gold core along the real steel (HDR 6-8 at its middle, soft across its width, faded at both
// ends), and the Spend's short soft column at her (bright at its foot, gone toward its top).
// UV.x: 0..1 across the strip; UV.y: 0 at its first point .. 1 at its second.
shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;

uniform vec4 col = vec4(1.0, 0.85, 0.55, 0.0); // rgb the hue; a its HDR peak
uniform float column = 0.0;                     // 0 the blade's (both ends faded); 1 the column's (fades up)

void fragment() {
	float x = abs(UV.x * 2.0 - 1.0);
	float across = (1.0 - x) * (1.0 - x) * (1.0 - x);
	float y = UV.y;
	float along = column > 0.5 ? smoothstep(0.0, 0.06, y) * pow(1.0 - y, 1.6) : smoothstep(0.0, 0.12, y) * (1.0 - smoothstep(0.86, 1.0, y));
	ALBEDO = col.rgb * col.a * across * along;
}
