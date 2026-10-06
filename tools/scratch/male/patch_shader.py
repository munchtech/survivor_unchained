p = r'C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-ae2de192cce8298ca/godot/shaders/heroine_skin.gdshader'
s = open(p, encoding='utf-8').read()
rep = [
('''uniform bool has_relief = false;
''', '''uniform bool has_relief = false;
// A man's shaved shadow (the hero's: People.HisShadow): where his beard and
// his hair grow (shadow_mask, red his beard's ground, green his scalp's),
// each as dark as chosen, of the hair's own colour; stubble, not a stain:
// the darkening broken into the stubs of hairs.
uniform sampler2D shadow_mask : hint_default_black, filter_linear_mipmap;
uniform float beard_shadow = 0.0;
uniform float scalp_shadow = 0.0;
uniform vec3 shadow_colour : source_color = vec3(0.16, 0.12, 0.1);
'''),
('''	ALBEDO = texture(paint, UV).rgb * tone;
	vec4 q = texture(pores, UV * pore_scale);''', '''	ALBEDO = texture(paint, UV).rgb * tone;
	vec4 q = texture(pores, UV * pore_scale);
	float stubble = 0.0;
	if (beard_shadow > 0.0 || scalp_shadow > 0.0) {
		vec2 g = texture(shadow_mask, UV).rg;
		// (the stubs: the pore tile's grain, finer, as dots)
		float stubs = smoothstep(0.3, 0.7, texture(pores, UV * pore_scale * 2.7 + vec2(0.37, 0.11)).a);
		stubble = clamp(g.r * beard_shadow + g.g * scalp_shadow, 0.0, 1.0) * mix(0.55, 1.0, stubs);
		ALBEDO = mix(ALBEDO, ALBEDO * shadow_colour * 2.4, stubble * 0.85);
	}'''),
('''	ROUGHNESS = clamp(rough + (q.a - 0.5) * 0.3, 0.0, 1.0);''', '''	ROUGHNESS = clamp(rough + (q.a - 0.5) * 0.3 + stubble * 0.15, 0.0, 1.0);'''),
]
for a, b in rep:
    assert a in s, a[:60]
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('ok')
