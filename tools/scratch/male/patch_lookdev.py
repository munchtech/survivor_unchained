p = r'C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-ae2de192cce8298ca/godot/tools_scenes/lookdev.gd'
s = open(p, encoding='utf-8').read()
rep = [
('# Lookdev: the heroine played through several clips side by side, front on, saved as one picture.',
 '# Lookdev: the heroine played through several clips side by side, front on, saved as one picture.\n'
 '# BODY=hero: the hero in her place (hero.glb, his hair hero_hair_*, his outfits hero_outfit_*), as People.Hero has him.'),
('''	for i in clips.size():
		var h = load("res://art/people/heroine.glb").instantiate()''',
 '''	var who = OS.get_environment("BODY") if OS.get_environment("BODY") != "" else "heroine"
	for i in clips.size():
		var h = load("res://art/people/%s.glb" % who).instantiate()'''),
('''						m.set_shader_parameter("iris", load("res://art/people/head_tex/heroine_iris.png"))''',
 '''						var iris = "res://art/people/head_tex/%s_iris.png" % who
						m.set_shader_parameter("iris", load(iris if ResourceLoader.exists(iris) else "res://art/people/head_tex/heroine_iris.png"))'''),
('''					sk.set_shader_parameter("pore_scale", pore_scale(mi.mesh))
''', '''					sk.set_shader_parameter("pore_scale", pore_scale(mi.mesh))
					# (His relief baked from his sculpt, and his own tone: People.Skin, People.HisTone.)
					if m.normal_texture != null:
						sk.set_shader_parameter("relief", m.normal_texture)
						sk.set_shader_parameter("has_relief", true)
					if who == "hero": sk.set_shader_parameter("tone", Color(1.0, 0.95, 0.9))
'''),
('''			var o = load("res://art/people/heroine_outfit_%s.gltf" % outfit.split("_")[0]).instantiate()''',
 '''			var o = load("res://art/people/%s_outfit_%s.gltf" % [who, outfit.split("_")[0]]).instantiate()'''),
('''		if style != "none" and ResourceLoader.exists("res://art/people/heroine_hair_%s.gltf" % style):
			var hs = load("res://art/people/heroine_hair_%s.gltf" % style).instantiate()''',
 '''		if style != "none" and ResourceLoader.exists("res://art/people/%s_hair_%s.gltf" % [who, style]):
			var hs = load("res://art/people/%s_hair_%s.gltf" % [who, style]).instantiate()'''),
('''		if OS.get_environment("NOHERPOSE") == "":
			skel.add_child(load("res://src/Actors/HerPose.cs").new())
		if OS.get_environment("NOJIGGLE") == "":''',
 '''		if OS.get_environment("NOHERPOSE") == "":
			var pose = load("res://src/Actors/HerPose.cs").new()
			# (His carriage as People.Hero sets it: arms clear of his lats, hips square.)
			if who == "hero":
				pose.ArmsIn = -5.0
				pose.HipTilt = 0.0
			skel.add_child(pose)
		if OS.get_environment("NOJIGGLE") == "" and who == "heroine":'''),
]
for a, b in rep:
    assert a in s, a[:70]
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('ok')
