p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a435f4dd0ac80df75\godot\tools_scenes\anim_review.gd"
s = open(p, encoding="utf-8").read()
rep = [
('''	var model = env("MODEL", "")
	if model != "":
		her = load("res://assets/people/Superhero_%s_FullBody.gltf" % model.capitalize()).instantiate()
	else:
		her = load("res://art/people/heroine.glb").instantiate()
	root.add_child(her)
	her.scale = Vector3.ONE * 1.04
	if model != "": kit(her, env("PARTS", ""))
	else: dress(her)''',
'''	var model = env("MODEL", "")
	if model == "hero":
		her = load("res://art/people/hero.glb").instantiate()
	elif model != "":
		her = load("res://assets/people/Superhero_%s_FullBody.gltf" % model.capitalize()).instantiate()
	else:
		her = load("res://art/people/heroine.glb").instantiate()
	root.add_child(her)
	her.scale = Vector3.ONE * 1.04
	if model == "hero": hero(her)
	elif model != "": kit(her, env("PARTS", ""))
	else: dress(her)'''),
('''	if ResourceLoader.exists("res://art/anim/folk.res"):
		ap.add_animation_library("folk", load("res://art/anim/folk.res"))''',
'''	if ResourceLoader.exists("res://art/anim/folk.res"):
		ap.add_animation_library("folk", load("res://art/anim/folk.res"))
	if ResourceLoader.exists("res://art/anim/hero.res"):
		ap.add_animation_library("him", load("res://art/anim/hero.res"))'''),
('''func dress(h):''',
'''# The hero (MODEL=hero) as his model comes, his paint on plain materials,
# with his carriage over library clips (People.Hero) and what he holds.
func hero(h):
	var skel: Skeleton3D = h.find_children("*", "Skeleton3D", true, false)[0]
	var hp = load("res://src/Actors/HerPose.cs").new()
	hp.set("ArmsIn", -5.0)
	hp.set("HipTilt", 0.0)
	hp.set("NeckPitch", 22.0)
	skel.add_child(hp)
	if clip.begins_with("him/"): hp.set("Native", 1.0)
	weapon(skel, env("WEAPON", ""))

func dress(h):'''),
]
for a, b in rep:
    assert s.count(a) == 1, a[:60]
    s = s.replace(a, b)
s = s.replace('''#   MODEL=female|male                      a townsfolk body (the kit's) instead of hers, in PARTS (kit
#                                          outfit parts, comma-separated); clips "folk/<name>"''',
'''#   MODEL=female|male                      a townsfolk body (the kit's) instead of hers, in PARTS (kit
#                                          outfit parts, comma-separated); clips "folk/<name>"
#   MODEL=hero                             the hero, with his clips ("him/<name>", art/anim/hero.res)''')
open(p, "w", encoding="utf-8").write(s)
print("ok")
