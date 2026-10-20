extends SceneTree
# A kit townsperson and what it holds, skinned at N times across a clip, to JSON (FolkHold.cs; tools/anim/folkhold.py).
func _init():
	get_root().add_child(load("res://tools_scenes/FolkHold.cs").new())
