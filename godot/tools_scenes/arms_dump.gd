extends SceneTree
# Every weapon and shield she holds, in its bone's own space, to tools/anim/data/arms_local.json (ArmsDump.cs).
func _init():
	get_root().add_child(load("res://tools_scenes/ArmsDump.cs").new())
