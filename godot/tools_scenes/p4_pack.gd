extends SceneTree
# P4 clips packed into p4_clips.res (P4Pack.cs; tools/anim/p4_pack.sh).
func _init():
	get_root().add_child(load("res://tools_scenes/P4Pack.cs").new())
