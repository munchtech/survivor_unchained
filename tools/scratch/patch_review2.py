p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a435f4dd0ac80df75\godot\tools_scenes\anim_review.gd"
s = open(p, encoding="utf-8").read()
rep = [
('''#   NOHERPOSE=1                            without her corrective pose layer''',
'''#   NOHERPOSE=1                            without her corrective pose layer
#   GESTURE=her/nod GESTUREAT=s            a gesture laid over the clip (Gestures.cs) s seconds in''', 1),
('''	if env("OVER", "") != "": overlay(env("OVER", ""))
	stage(root)''',
'''	if env("OVER", "") != "": overlay(env("OVER", ""))
	if env("GESTURE", "") != "":
		var gsk: Skeleton3D = her.find_children("*", "Skeleton3D", true, false)[0]
		gestures = load("res://src/Actors/Gestures.cs").new()
		gsk.add_child(gestures)
	stage(root)''', 1),
('''var tree: AnimationTree
''',
'''var tree: AnimationTree
var gestures = null
''', 1),
('''	if tree != null and k == int(float(env("OVERAT", "0")) * 30):
		tree.set("parameters/shot/request", AnimationNodeOneShot.ONE_SHOT_REQUEST_FIRE)''',
'''	if tree != null and k == int(float(env("OVERAT", "0")) * 30):
		tree.set("parameters/shot/request", AnimationNodeOneShot.ONE_SHOT_REQUEST_FIRE)
	if gestures != null and k == int(float(env("GESTUREAT", "0")) * 30):
		gestures.Play(ap.get_animation(env("GESTURE", "")), 1.0, env("HOLD", "") != "")''', 1),
]
for a, b, n in rep:
    assert s.count(a) == n, a[:60]
    s = s.replace(a, b)
open(p, "w", encoding="utf-8").write(s)
print("ok")
