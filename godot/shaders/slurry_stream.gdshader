// The Hollow's stream with the Dig's slurry in it (View/ArenaEdge.cs): dark,
// slow water, the sky at a grazing angle, the bed seen through it where it
// is shallow, scum at the banks; and the slurry's light ("warm, faintly
// glowing", "a little like a wound") in threads drawn out down the current,
// thickest in the deep middle. From thirty metres up the threads are the
// stream's line; faint, so it never reads as ground that hurts.
// UV: x metres across from the middle, y metres downstream; UV2.x 0 at a
// bank, 1 in the middle.
shader_type spatial;
render_mode blend_mix, depth_draw_never, cull_disabled, diffuse_burley, specular_schlick_ggx;

uniform sampler2D noise_tex : filter_linear_mipmap, repeat_enable;
uniform sampler2D screen_tex : hint_screen_texture, filter_linear_mipmap;
uniform sampler2D depth_tex : hint_depth_texture, filter_nearest;
uniform vec3 water : source_color = vec3(0.07, 0.08, 0.05);
uniform vec3 sky : source_color = vec3(0.1, 0.14, 0.2);
uniform vec3 scum : source_color = vec3(0.42, 0.42, 0.3);
uniform vec3 light : source_color = vec3(0.6, 0.72, 0.18);
uniform float glow = 0.3;
uniform float speed = 0.25;

varying vec3 w_pos;

void vertex() {
	w_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

float wh(vec2 p) {
	vec2 a = p * vec2(0.09, 0.03) + vec2(0.0, -TIME * speed * 0.06);
	vec2 b = p * vec2(0.21, 0.08) + vec2(3.7, -TIME * speed * 0.11);
	return texture(noise_tex, a).g * 0.6 + texture(noise_tex, b).b * 0.4;
}

void fragment() {
	vec2 sp = vec2(UV.x, UV.y);
	float e = 0.3;
	float h0 = wh(sp), hx = wh(sp + vec2(e, 0.0)), hz = wh(sp + vec2(0.0, e));
	vec3 n_w = normalize(vec3(-(hx - h0) * 0.9, 1.0, -(hz - h0) * 0.9));
	NORMAL = normalize((VIEW_MATRIX * vec4(n_w, 0.0)).xyz);
	float fres = pow(1.0 - clamp(dot(normalize(-VERTEX), NORMAL), 0.0, 1.0), 4.0);

	// How deep the water is over its bed, here.
	vec2 bent = SCREEN_UV + n_w.xz * 0.02;
	float d = texture(depth_tex, bent).r;
	vec4 bed = INV_PROJECTION_MATRIX * vec4(bent * 2.0 - 1.0, d, 1.0);
	bed.xyz /= bed.w;
	if (bed.z > VERTEX.z) {
		bent = SCREEN_UV;
		d = texture(depth_tex, bent).r;
		bed = INV_PROJECTION_MATRIX * vec4(bent * 2.0 - 1.0, d, 1.0);
		bed.xyz /= bed.w;
	}
	float thick = max(VERTEX.z - bed.z, 0.0);
	float see = clamp(exp(-thick * 3.5) * 0.8, 0.03, 0.75);
	vec3 under = texture(screen_tex, bent).rgb * vec3(0.75, 0.8, 0.55);

	// The slurry's light: threads drawn out along the current, slow, in the middle.
	float mid = smoothstep(0.1, 0.85, UV2.x);
	// (Drawn out two to one, no more: stretched further they read from the camera as streaks of
	// speed, not slurry curling in a slow current.)
	vec2 tp = vec2(UV.x * 0.4, UV.y * 0.2 - TIME * speed * 0.035);
	float thread = texture(noise_tex, tp).r * 0.65 + texture(noise_tex, tp * vec2(2.3, 1.7) + 0.41).g * 0.35;
	thread = smoothstep(0.55, 0.82, thread);
	float pulse = 0.75 + 0.25 * sin(TIME * 0.6 + UV.y * 0.08);
	vec3 sick = light * glow * thread * mid * pulse;

	// Scum where it laps the banks, and in streaks down the current.
	float fn = wh(sp * vec2(3.0, 1.2) + 9.0);
	float edge = 1.0 - smoothstep(0.0, 0.3, UV2.x);
	float foam = edge * smoothstep(0.45, 0.62, fn) * 0.8 + smoothstep(0.62, 0.72, fn) * 0.25 * (1.0 - mid * 0.5);

	ALBEDO = mix(water * (1.0 - see), scum, foam * 0.6);
	EMISSION = under * see * (1.0 - foam) + sky * (0.12 + fres * 0.9) * (1.0 - foam) + sick * (1.0 - foam * 0.7);
	ROUGHNESS = mix(0.05, 0.7, foam);
	SPECULAR = 0.5;
}
