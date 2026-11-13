extends SceneTree
# Look thumbnails contact sheet (LookSheet.cs: OUT=png path, SIZE=px per tile).
func _init():
	get_root().add_child(load("res://tools_scenes/LookSheet.cs").new())
