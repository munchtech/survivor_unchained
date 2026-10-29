// Mist lying on a zone's river in play (World/MistLayers.cs; look bible 1c, "mist in layers"): one of two or three
// sheets stacked over the water. It lies in banks, not as one sheet: a broad noise drifting slowly down the course,
// cut so about half the water is clear, torn at its edges by a finer drifting noise. The banks are lit by the key as
// if they had a body (their density read as a height, so the side toward the moon or the low sun takes its light and
// the far side keeps the air's own cool colour). It fades where it meets a bank or a stone (the depth buffer) and
// toward the sheet's edges, so it has no edge of its own.
// UV: x metres across from the course's middle, y metres along it; UV2.x 0 at the sheet's edge, 1 in its middle.
shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, cull_disabled, shadows_disabled;

uniform sampler2D noise_tex : filter_linear_mipmap, repeat_enable;
uniform sampler2D depth_tex : hint_depth_texture, filter_linear;
// The air's own colour in the mist (its shade side).
uniform vec3 mist : source_color = vec3(0.17, 0.22, 0.3);
// The key's light (linear, its energy in): what the lit side of a bank takes.
uniform vec3 key_light = vec3(0.0);
uniform float opacity = 0.3;
// The most this sheet veils (MistLayers sets each sheet's, so all three stacked never hide more than ~40%: the bed's
// stones keep over half their contrast through the thickest bank; judge E6 r1, the night ford read milky).
uniform float cap = 1.0;
// The finer noise's drift (metres a second, scaled) and the banks' (metres a second, down the course).
uniform float drift = 0.02;
uniform float bank_drift = 0.25;
// Which sheet (0, 1, 2): its banks a few metres along from the one under it, its tears its own.
uniform float layer = 0.0;
global uniform vec4 key_dir;

const float BANK = 40.0;

float bank_at(vec2 m) {
	return texture(noise_tex, m / BANK).r;
}

void fragment() {
	vec2 m = UV + vec2(layer * 3.0, layer * 7.0 - TIME * bank_drift);
	float b0 = bank_at(m);
	// Cut so about 40% of the water is wholly clear and a quarter half veiled (the noise's 40th and 70th percentiles).
	float cover = smoothstep(0.47, 0.6, b0);
	vec2 p = vec2(UV.x * 0.06, UV.y * 0.025) + vec2(TIME * drift * 0.3 + layer * 0.37, -TIME * drift + layer * 0.61);
	float n = texture(noise_tex, p).g * 0.6 + texture(noise_tex, p * 2.6 + vec2(0.3, TIME * drift * 0.7)).b * 0.4;
	float body = cover * (0.45 + 0.55 * smoothstep(0.35, 0.7, n)) * smoothstep(0.0, 0.7, UV2.x);
	float depth = texture(depth_tex, SCREEN_UV).r;
	vec4 v = INV_PROJECTION_MATRIX * vec4(SCREEN_UV * 2.0 - 1.0, depth, 1.0);
	float behind = -v.z / v.w + VERTEX.z;
	body *= smoothstep(0.0, 1.2, behind);
	// (C03 env r2: a sheet seen edge-on from a camera at the water, under 25 deg, thins to a quarter, so the water's mirror
	// shows through and the far reach does not fill with an even milky band; the play camera, looking down, as judged)
	body *= mix(0.25, 1.0, smoothstep(0.17, 0.42, abs(dot(normalize(-VERTEX), normalize((VIEW_MATRIX * vec4(0.0, 1.0, 0.0, 0.0)).xyz)))));
	if (body <= 0.002) discard;
	// The bank's body: its density as a height, its slope a normal (across is world z, along is world x).
	float e = 2.0;
	float bx = bank_at(m + vec2(0.0, e)), bz = bank_at(m + vec2(e, 0.0));
	vec3 nrm = normalize(vec3(-(bx - b0) / e * 30.0, 1.0, -(bz - b0) / e * 30.0));
	float lam = clamp(dot(nrm, normalize(key_dir.xyz)), 0.0, 1.0);
	ALBEDO = mist * (0.85 + 0.3 * n) + key_light * (0.1 + 0.9 * lam) * 0.3;
	ALPHA = clamp(body * opacity, 0.0, cap);
}
