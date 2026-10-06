W = r'C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-ae2de192cce8298ca/'
for p, a, b in [
    ('godot/src/Actors/People.cs', '''                EyeColour(e, look.Eyes, look.EyeRing);
                return e;''', '''                // (his own, when none is chosen: flint grey, Lore.Eyes' "flint")
                if (who == "hero" && look.Eyes == null) EyeColour(e, HisEyes.Iris, HisEyes.Ring);
                else EyeColour(e, look.Eyes, look.EyeRing);
                return e;'''),
    ('godot/src/Actors/People.cs', '''    const float HisNeckPitch = 22f;''', '''    const float HisNeckPitch = 22f;

    /// <summary>His own eyes: flint grey, a little warmer round the pupil.</summary>
    static readonly (Color Iris, Color Ring) HisEyes = (new("#727c84"), new("#8a8672"));'''),
    ('godot/tools_scenes/lookdev.gd', '''						m.set_shader_parameter("iris", load(iris if ResourceLoader.exists(iris) else "res://art/people/head_tex/heroine_iris.png"))''',
     '''						m.set_shader_parameter("iris", load(iris if ResourceLoader.exists(iris) else "res://art/people/head_tex/heroine_iris.png"))
						# (his own flint grey, as People.HisEyes)
						if who == "hero":
							m.set_shader_parameter("recolour", 1.0)
							m.set_shader_parameter("iris_colour", Color("#727c84"))
							m.set_shader_parameter("ring_colour", Color("#8a8672"))'''),
    ('tools/assets/hero_male_head.py', '''        "X-eye-height2-decr": 0.3, "X-eye-push1-in": 0.25, "X-eye-scale-decr": 0.05,''',
     '''        "X-eye-height2-decr": 0.15, "X-eye-push1-in": 0.25,'''),
    ('tools/assets/hero_male_head.py', '''S = np.linalg.norm(hn - hc) / np.linalg.norm(mn - mc)''',
     '''# (A size larger than his sculpt's face: on his shoulders and his neck, a
# wrestler's, the sculpt's own head looked small.)
S = HEAD_SCALE * np.linalg.norm(hn - hc) / np.linalg.norm(mn - mc)'''),
    ('tools/assets/hero_male_head.py', '''SPLIT_Z, CUT_Z, LEAN = 1.696, 1.662, 0.54''', '''SPLIT_Z, CUT_Z, LEAN = 1.696, 1.662, 0.54
HEAD_SCALE = 1.06'''),
]:
    s = open(W + p, encoding='utf-8').read()
    assert a in s, (p, a)
    s = s.replace(a, b)
    open(W + p, 'w', encoding='utf-8', newline='\n').write(s)
print('ok')
