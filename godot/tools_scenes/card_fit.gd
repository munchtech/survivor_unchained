extends SceneTree
# Every draft card a calling can be dealt, laid out in a real DraftPanel at 1920x1080, checked for overlap and truncation (CardFit.cs).
func _init():
	get_root().add_child(load("res://tools_scenes/CardFit.cs").new())
