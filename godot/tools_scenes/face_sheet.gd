extends SceneTree
# Her looks side by side (FaceSheet.cs: SHEET=list.json OUT=folder CAM=face|head|body YAW=deg).
func _init():
	get_root().add_child(load("res://tools_scenes/FaceSheet.cs").new())
