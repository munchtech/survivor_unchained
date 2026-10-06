extends SceneTree
# Print every clip in the kit libraries and her own, with its length.
func _init():
	for f in ["res://assets/people/UAL1.glb", "res://assets/people/UAL2.glb"]:
		var s = load(f).instantiate()
		var ap = s.find_child("AnimationPlayer", true, false)
		for lib in ap.get_animation_library_list():
			for n in ap.get_animation_library(lib).get_animation_list():
				print("clip ", f.get_file(), " ", n, " ", "%.2f" % ap.get_animation_library(lib).get_animation(n).length)
		s.free()
	for f in ["res://art/anim/heroine.res", "res://art/anim/folk.res"]:
		var lib = load(f)
		for n in lib.get_animation_list():
			print("clip ", f.get_file(), " ", n, " ", "%.2f" % lib.get_animation(n).length)
	quit()
