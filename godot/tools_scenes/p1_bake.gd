extends SceneTree
# The clip bridge: every A clip baked onto B skeleton (P1BakeRun.cs; tools/body/bake_clips.sh).
func _init():
	get_root().add_child(load("res://tools_scenes/P1BakeRun.cs").new())
