from ed import edit
edit(r"shaders\blade.gdshader", [
("""INSTANCE_CUSTOM is (head, back,
// span in radians, seed + what is left): the blade's place along the swing
// (0 the start, 1 the end), where its smear ends behind it, the angle it
// sweeps, and a seed whose fraction is how much of it is left.""",
"""INSTANCE_CUSTOM is (head, back,
// span in radians, heat + seed + what is left): the blade's place along the swing
// (0 the start, 1 the end), where its smear ends behind it, the angle it
// sweeps, and in the last its edge's heat in thousands (1 to 5: its own hue to
// white), a seed under a thousand, and in its fraction how much of it is left."""),
("""	float seed = floor(v_custom.w), left = fract(v_custom.w);""",
"""	float packed = floor(v_custom.w), left = fract(v_custom.w);
	float level = floor(packed / 1000.0);
	float seed = packed - level * 1000.0;
	float white = clamp((level - 1.0) / 4.0, 0.0, 1.0);"""),
("""	vec3 hot = mix(hue, vec3(1.0), 0.75) * 2.4;""",
"""	vec3 hot = mix(hue, vec3(1.0), white) * 2.4;"""),
])
