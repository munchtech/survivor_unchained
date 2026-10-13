// The Flares' own particles (Fx/Flare/FlareBits.cs): every look drawn here from shape and our own noise, no
// sprite sheet (the owner: "flares should be unique"). Each instance: its place (the transform's origin), its
// size (the basis's scale), its way (INSTANCE_CUSTOM.xyz, m/s, for the streaks and the turned tongues), and
// kind + age (INSTANCE_CUSTOM.w: the kind's whole number, the life's fraction). COLOR is its colour and alpha.
// Kinds: 0 a glow mote, 1 a molten streak, 2 a tongue of flame, 3 a puff (steam or smoke; the mixed batch),
// 4 a thread of light, 5 a soot fleck (mixed). The added batch's light is held under the knee by its colours;
// the mixed batch is the dark bed under it.
shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_never, shadows_disabled, blend_add;

global uniform sampler2D flare_noise : filter_linear_mipmap, repeat_enable;

varying vec2 v_uv;
varying flat float v_kind;
varying flat float v_age;
varying flat float v_seed;
varying float v_len;

void vertex() {
	vec3 at = MODEL_MATRIX[3].xyz;
	float size = length(MODEL_MATRIX[0].xyz);
	vec3 vel = INSTANCE_CUSTOM.xyz;
	v_kind = floor(INSTANCE_CUSTOM.w + 1e-4);
	v_age = INSTANCE_CUSTOM.w - v_kind;
	v_seed = fract(float(INSTANCE_ID) * 0.6180339);
	v_uv = UV;
	vec3 pv = (VIEW_MATRIX * vec4(at, 1.0)).xyz;
	vec3 vv = (VIEW_MATRIX * vec4(vel, 0.0)).xyz;
	vec2 dir = vv.xy;
	float sp = length(dir);
	vec2 ax = sp > 1e-4 ? dir / sp : vec2(0.0, 1.0);
	float len = size;
	float wid = size;
	if (v_kind > 0.5 && v_kind < 1.5) {
		// A streak: as long as its way over a few frames, its head at the front.
		len = size + sp * 0.055;
		wid = size * 0.55;
	} else if (v_kind > 1.5 && v_kind < 2.5) {
		// A tongue: long along its way, narrow, rooted at its base.
		len = size * 2.6;
		wid = size * 0.8;
	} else if (v_kind > 3.5 && v_kind < 4.5) {
		len = size + sp * 0.08;
		wid = size * 0.25;
	} else {
		// A puff turns slowly on itself.
		float a = v_seed * 6.2831 + TIME * (v_seed - 0.5) * 0.6;
		ax = vec2(cos(a), sin(a));
	}
	vec2 ay = vec2(-ax.y, ax.x);
	vec2 c = VERTEX.xy;
	// Streaks and tongues hang behind their head: the quad runs from the head back along the way.
	float back = (v_kind > 0.5 && v_kind < 2.5) || (v_kind > 3.5 && v_kind < 4.5) ? -0.5 : 0.0;
	vec2 off = ax * (c.y + back) * len + ay * c.x * wid;
	v_len = len / max(wid, 1e-3);
	POSITION = PROJECTION_MATRIX * vec4(pv + vec3(off, 0.0), 1.0);
}

void fragment() {
	vec2 q = v_uv * 2.0 - 1.0; // x across, y along (-1 tail .. 1 head)
	q.y = -q.y;
	vec4 col = COLOR;
	float a = 0.0;
	vec3 rgb = col.rgb;
	if (v_kind < 0.5) {
		// A mote: a soft point with a hot centre.
		float r2 = dot(q, q);
		a = exp(-r2 * 4.5) + exp(-r2 * 28.0) * 0.6;
	} else if (v_kind < 1.5) {
		// A molten streak: a white-hot head, the body cooling to deep orange and red along the tail.
		float along = q.y * 0.5 + 0.5; // 0 tail .. 1 head
		float across = exp(-q.x * q.x * 5.0 * (0.6 + 0.4 * along));
		float head = smoothstep(0.82, 1.0, along) * (1.0 - smoothstep(0.97, 1.0, along));
		float body = pow(along, 2.2);
		a = across * (body * 0.85 + head * 1.4);
		rgb = mix(col.rgb * vec3(0.55, 0.16, 0.05), col.rgb, smoothstep(0.35, 0.95, along));
		rgb = mix(rgb, vec3(1.0, 0.86, 0.6) * 1.25, head * exp(-q.x * q.x * 14.0));
	} else if (v_kind < 2.5) {
		// A tongue of flame: tapered from the root, licked ragged by the noise, hottest at its root.
		float along = q.y * 0.5 + 0.5;
		vec2 nuv = vec2(q.x * 0.35 + v_seed * 7.0, along * 0.8 - TIME * 2.2 - v_seed * 3.0);
		float n = texture(flare_noise, nuv).g * 0.65 + texture(flare_noise, nuv * 2.3 + 0.4).b * 0.35;
		float width = (1.0 - along) * 0.85 + 0.12;
		float shape = 1.0 - smoothstep(width * 0.55, width, abs(q.x) + (n - 0.5) * 0.55);
		shape *= smoothstep(0.0, 0.08, along) * (1.0 - smoothstep(0.55 + 0.45 * n, 1.0, along + v_age * 0.6));
		a = shape;
		float heat = clamp((1.0 - along) * 1.2 - abs(q.x) * 0.6 - v_age * 0.8 + n * 0.3, 0.0, 1.0);
		rgb = mix(vec3(0.5, 0.06, 0.01), mix(col.rgb, vec3(1.0, 0.82, 0.45), smoothstep(0.6, 1.0, heat)), smoothstep(0.1, 0.6, heat));
	} else if (v_kind < 3.5) {
		// A puff: billowed by two layers of noise, softly rounded, thinning as it ages.
		vec2 uv = q * 0.5 + 0.5;
		float n = texture(flare_noise, uv * 0.55 + v_seed * 5.0 + vec2(0.0, -TIME * 0.05)).r;
		float n2 = texture(flare_noise, uv * 1.3 + v_seed * 3.0 + vec2(TIME * 0.04, 0.0)).g;
		float r = length(q);
		float body = 1.0 - smoothstep(0.35, 1.0, r + (n - 0.5) * 0.7 + (n2 - 0.5) * 0.3);
		a = body * (0.55 + 0.45 * n2);
		// Lit from below and its rim brighter than its core (a puff seen against the dark).
		rgb = col.rgb * (0.75 + 0.5 * n2) * (0.85 + 0.3 * smoothstep(0.2, 0.8, r));
	} else if (v_kind < 4.5) {
		// A thread of light rising: thin, bright along its length, fading at both ends.
		float along = q.y * 0.5 + 0.5;
		a = exp(-q.x * q.x * 9.0) * smoothstep(0.0, 0.4, along) * (1.0 - smoothstep(0.75, 1.0, along));
	} else {
		// A fleck of soot: a small ragged dark scrap.
		float n = texture(flare_noise, q * 0.3 + v_seed * 9.0).b;
		a = 1.0 - smoothstep(0.3, 0.9, length(q) + (n - 0.5) * 0.6);
	}
	ALBEDO = rgb;
	// (The mixed batch is lit: a puff faces the eye, rounded a little, so the fire under it lights its belly.)
	NORMAL = normalize(vec3(q.x * 0.35, q.y * 0.35 + 0.15, 1.0));
	ALPHA = clamp(a * col.a, 0.0, 1.0);
}
