extends SceneTree
# Creation's portraits (Portraits.cs: JOBS=list.json OUT=folder SIZE=px), run by tools/assets/creation_portraits.py.
func _init():
	get_root().add_child(load("res://tools_scenes/Portraits.cs").new())
