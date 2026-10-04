// The survivor stays readable through every effect drawn over the crowd
// (the experience director's rule): where such an effect crosses her on
// screen it is drawn at a third of its strength, eased over a body's width,
// so the eye never loses her in her own light. `survivor` is her chest
// (WorldScene; w is 1 while she is in a fight).
global uniform vec4 survivor;

float hero_clear(vec3 view_pos, mat4 view, mat4 proj, vec2 viewport) {
	if (survivor.w < 0.5) return 1.0;
	vec4 me = proj * vec4(view_pos, 1.0);
	vec4 feet = proj * (view * vec4(survivor.xyz - vec3(0.0, 1.0, 0.0), 1.0));
	vec4 head = proj * (view * vec4(survivor.xyz + vec3(0.0, 0.75, 0.0), 1.0));
	vec2 half_vp = viewport * 0.5;
	vec2 p = me.xy / me.w * half_vp;
	vec2 a = feet.xy / feet.w * half_vp;
	vec2 b = head.xy / head.w * half_vp;
	vec2 ab = b - a;
	float t = clamp(dot(p - a, ab) / max(dot(ab, ab), 1.0), 0.0, 1.0);
	float d = length(p - (a + ab * t));
	float r = max(10.0, length(ab) * 0.3);
	return mix(0.33, 1.0, smoothstep(r, r * 1.9, d));
}
