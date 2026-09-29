// The stream, as the web game shades it (src/render/water.ts): the surface
// broken by two layers of noise drifting downstream in the stream's own
// coordinates, darker looking straight down, the sky in it at a grazing
// angle, shallows clearing toward the mud and scum where it laps the bank;
// the poisoned stream's greens and its sick glow. What Godot adds: the bed
// seen through the water, bent by the ripples, and the murk by how deep the
// water really is over it (the depth buffer), not only by the bank's
// distance.
shader_type spatial;
render_mode blend_mix, depth_draw_never, cull_disabled, diffuse_burley, specular_schlick_ggx;

uniform sampler2D noise_tex : filter_linear_mipmap, repeat_enable;
uniform sampler2D screen_tex : hint_screen_texture, filter_linear_mipmap;
uniform sampler2D depth_tex : hint_depth_texture, filter_nearest;
uniform bool stream = true;
// The Verge's poisoned stream (src/world/zones/verge.ts).
uniform vec3 color : source_color = vec3(0.165, 0.29, 0.118);
uniform vec3 murk : source_color = vec3(0.047, 0.118, 0.024);
uniform vec3 shallow : source_color = vec3(0.306, 0.353, 0.165);
uniform vec3 foam_color : source_color = vec3(0.722, 0.784, 0.565);
uniform vec3 sky : source_color = vec3(0.18, 0.29, 0.188);
uniform vec2 flow = vec2(0.0, 0.6);
uniform float glow = 0.45;
uniform float murkiness = 2.4;

varying vec3 w_pos;

void vertex() {
	w_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

float wh(vec2 p) {
	vec2 a = p * 0.045 + flow * TIME * 0.05;
	vec2 b = p * 0.11 - flow.yx * TIME * 0.07 + 3.7;
	return texture(noise_tex, a).g * 0.6 + texture(noise_tex, b).b * 0.4;
}

void fragment() {
	// Stream space: across in x, downstream in y, so the ripples travel
	// with the current however the stream bends.
	vec2 wp = stream ? vec2(UV.x, -UV.y) : w_pos.xz;
	float e = 0.35;
	float h0 = wh(wp), hx = wh(wp + vec2(e, 0.0)), hz = wh(wp + vec2(0.0, e));
	vec3 n_w = normalize(vec3(-(hx - h0) * 1.3, 1.0, -(hz - h0) * 1.3));
	NORMAL = normalize((VIEW_MATRIX * vec4(n_w, 0.0)).xyz);
	float fres = pow(1.0 - clamp(dot(normalize(-VERTEX), NORMAL), 0.0, 1.0), 3.0);

	// How much water there is between the surface and the bed, here.
	vec2 bent = SCREEN_UV + n_w.xz * 0.035;
	float d = texture(depth_tex, bent).r;
	vec4 bed = INV_PROJECTION_MATRIX * vec4(bent * 2.0 - 1.0, d, 1.0);
	bed.xyz /= bed.w;
	if (bed.z > VERTEX.z) {
		// What is bent into view is in front of the water: look straight.
		bent = SCREEN_UV;
		d = texture(depth_tex, bent).r;
		bed = INV_PROJECTION_MATRIX * vec4(bent * 2.0 - 1.0, d, 1.0);
		bed.xyz /= bed.w;
	}
	float thick = max(VERTEX.z - bed.z, 0.0);
	float sh = stream ? 1.0 - smoothstep(0.0, 0.55, UV2.x) : 0.0;
	float see = exp(-thick * murkiness) * 0.9 + sh * 0.25;
	see = clamp(see, 0.04, 0.85);
	vec3 under = texture(screen_tex, bent).rgb * mix(vec3(1.0), shallow * 1.6, 0.5);

	vec3 body = mix(murk, color, 0.35 + fres * 0.65);
	body = mix(body, shallow, sh * 0.6);
	float ripple = smoothstep(0.52, 0.7, wh(w_pos.xz * 1.7));
	vec3 lit_from_sky = sky * (0.25 + fres * 1.1 + ripple * 0.35) * (1.0 - sh * 0.5);
	vec3 sick = murk * glow * (0.6 + 0.4 * wh(w_pos.xz * 2.0));

	// Scum where it laps the bank, streaks down the current.
	float foam = 0.0;
	if (stream) {
		vec2 fp = vec2(UV.x * 1.6, -UV.y * 0.9);
		float fn = wh(fp * 2.4) * 0.65 + wh(fp * 6.0 + 11.0) * 0.35;
		float edge = 1.0 - smoothstep(0.02, 0.22, UV2.x);
		float streak = smoothstep(0.5, 0.66, fn) * (0.25 + 0.75 * edge);
		foam = max(edge * smoothstep(0.35, 0.55, fn), streak * 0.35);
	}
	see *= 1.0 - foam * 0.85;

	ALBEDO = mix(body * (1.0 - see), foam_color, foam * 0.75);
	EMISSION = under * see + lit_from_sky + sick + foam_color * foam * 0.18;
	ROUGHNESS = mix(0.06, 0.6, foam);
	SPECULAR = 0.5;
	METALLIC = 0.0;
}
