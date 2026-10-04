// What a skill makes grow out of the ground for a moment (src/Fx/BattleFx.Skills.cs,
// Spikes): ice, thorns, stone. Cut, not turned: every face is flat and
// catches the light on its own, so a spike reads as a hard thing (smooth,
// lit cones read as paper). Ice is deep in its body, glows from its root
// and burns white at its edges and tip; stone and thorn stay dull with a
// faint rim of their school. COLOR is its colour, COLOR.a how much it
// glows (it fades as it sinks). The mesh is one unit tall about its origin.
shader_type spatial;
render_mode cull_back;

uniform float emit = 0.4;
uniform float rim = 2.4;
uniform float gloss = 0.1;
// How much each face shows its own light (ice: a lot; stone: a little).
uniform float facet = 0.0;

varying float v_up;

void vertex() {
	v_up = clamp(VERTEX.y + 0.5, 0.0, 1.0);
}

void fragment() {
	vec3 n = normalize(cross(dFdx(VERTEX), dFdy(VERTEX)));
	if (dot(n, VIEW) < 0.0) n = -n;
	NORMAL = n;
	float fres = pow(1.0 - clamp(dot(n, VIEW), 0.0, 1.0), 2.2);
	// Each face its own: one turned to the key light flares, the rest stay deep.
	float key = pow(max(dot(n, normalize(vec3(-0.45, 0.75, 0.5))), 0.0), 5.0);
	float own = fract(sin(dot(floor(n * 6.0), vec3(12.9898, 78.233, 37.719))) * 43758.5453);
	vec3 col = COLOR.rgb;
	ALBEDO = col * mix(0.4, 0.1, facet);
	ROUGHNESS = gloss;
	SPECULAR = mix(0.8, 0.45, facet);
	// Glowing from the root, the tip and the cut edges catching white.
	float root = mix(1.0, 0.45 + 0.55 * (1.0 - v_up), facet);
	vec3 faces = col * (own * 0.45 + key * 1.6) + vec3(key * 0.6);
	vec3 edge = mix(col, vec3(1.0), 0.45 * facet) * fres * rim;
	vec3 tip = vec3(0.9, 0.97, 1.0) * smoothstep(0.75, 1.0, v_up) * facet * 0.8;
	EMISSION = (col * emit * root + faces * facet + edge + tip) * COLOR.a;
}
