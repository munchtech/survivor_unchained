p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7dd95d00c4a6a017\godot\tools_scenes\anim_review.gd"
s = open(p, encoding="utf-8").read()
old = '''	her.position += her.basis.z.normalized() * speed * delta
	place_camera()'''
new = '''	her.position += her.basis.z.normalized() * speed * delta
	# FIXCAM=1: the camera set up on the clip's first frame and left there,
	# as a cinematic's camera is set on its marks when the shot begins.
	if env("FIXCAM", "") == "" or frame <= warm:
		place_camera()'''
assert old in s
s = s.replace(old, new, 1)
open(p, "w", encoding="utf-8").write(s)
print("patched")
