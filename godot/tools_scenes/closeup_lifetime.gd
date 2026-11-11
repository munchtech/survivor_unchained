extends SceneTree
# Exercise freed close-up lights and the c04b hand-back in the real game.
func _init():
	get_root().add_child(load("res://tools_scenes/CloseUpLifetime.cs").new())
