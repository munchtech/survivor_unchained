// The Warden's lamp glass (LampIron.cs; tools/assets/lamp_iron.py's panes, UV u across, v down each pane as glTF has it).
// Old, grimy, river-washed glass: unshaded so no light drives it past the glow threshold; nearly clear
// where it is clean, the flame's light caught in the grime (strongest round the flame, at the pane's
// height of it), the panes' edges brighter where the light runs into the glass and out at its cut
// edges, soot toward the top, dried water runs down, and a fresnel sheen of the night at grazing angles.
shader_type spatial;
render_mode unshaded, blend_mix, cull_disabled, depth_draw_never, shadows_disabled;

uniform sampler2D masks : filter_linear_mipmap, repeat_enable;
// The flame's colour (linear) and how lit the lamp is (0 out, 1 as built).
uniform vec3 glow = vec3(0.35, 0.62, 1.0);
uniform float lit = 1.0;
uniform float glow_k = 0.1;
// The flame's place in the lamp's own frame, and how far round it the glass catches its light (model units).
uniform vec3 flame_at = vec3(0.0, -0.15, 0.0);
uniform float spot_r = 0.045;
uniform float edge_k = 0.5;
uniform vec3 sheen = vec3(0.16, 0.19, 0.23);
uniform float sheen_k = 0.12;
// dark (the Warden's lantern, LampIron.MakeWarden): smoked glass that shows the night's reflections and the
// flame's glow round it and little else, never a pale pane. 0 the sill lamp's glass as it was.
uniform float dark = 0.0;
uniform vec3 reflect_col = vec3(0.30, 0.40, 0.55);

varying vec3 opos;

void vertex() {
	opos = VERTEX;
}

void fragment() {
	float up = 1.0 - UV.y;
	vec4 m = texture(masks, UV * vec2(1.3, 1.6) + vec2(0.37, 0.11));
	vec4 m2 = texture(masks, UV * vec2(0.45, 0.6) + vec2(0.71, 0.29));
	// Grime: blotchy film, thicker at the bottom corners and in runs down from the top.
	float film = smoothstep(0.35, 0.8, m2.r * 0.8 + m.g * 0.35) * 0.7 + 0.15;
	float runs = smoothstep(0.45, 0.9, m.a) * (0.35 + 0.65 * up);
	float soot = smoothstep(0.62, 1.0, up) * (0.6 + 0.4 * m.g);
	float corner = smoothstep(0.25, 0.0, min(UV.x, 1.0 - UV.x)) * smoothstep(0.3, 0.0, up);
	float grime = clamp(film + runs * 0.5 + corner * 0.5, 0.0, 1.0);
	// The flame's light: a soft spot round its height and line, and the cut edges of the pane.
	float across = abs(opos.x) > abs(opos.z) ? opos.z - flame_at.z : opos.x - flame_at.x;
	vec2 d = vec2(across, (opos.y - flame_at.y) * 0.7);
	float spot = exp(-dot(d, d) / (spot_r * spot_r));
	float edge = max(smoothstep(0.08, 0.0, min(UV.x, 1.0 - UV.x)), smoothstep(0.06, 0.0, min(UV.y, 1.0 - UV.y)));
	float light = lit * glow_k * (0.25 + 1.6 * spot) * (0.35 + 0.9 * grime) * (1.0 - 0.75 * soot) + lit * edge_k * glow_k * edge;
	float f = pow(1.0 - clamp(abs(dot(NORMAL, VIEW)), 0.0, 1.0), 3.0);
	vec3 alb = glow * light + sheen * f * sheen_k + vec3(0.025, 0.024, 0.02) * grime;
	float a = clamp(0.05 + 0.22 * grime + 0.5 * soot + 0.2 * f + 0.6 * clamp(light, 0.0, 0.5), 0.0, 0.85);
	if (dark > 0.0) {
		// The night in it: the sky's reflection, a soft band where the reflected ray looks up, broken by the grime.
		vec3 rv = reflect(-VIEW, NORMAL);
		float sky = smoothstep(0.1, 0.9, (INV_VIEW_MATRIX * vec4(rv, 0.0)).y);
		float refl = (0.04 + 0.6 * f) * (0.35 + 0.65 * sky) * (1.0 - 0.5 * grime);
		vec3 dk = glow * light + reflect_col * refl + vec3(0.012, 0.012, 0.011) * grime;
		float da = clamp(0.10 + 0.16 * grime + 0.35 * soot + 0.35 * refl + 0.5 * clamp(light, 0.0, 0.45), 0.0, 0.8);
		alb = mix(alb, dk, dark);
		a = mix(a, da, dark);
	}
	ALBEDO = alb;
	ALPHA = a;
}
