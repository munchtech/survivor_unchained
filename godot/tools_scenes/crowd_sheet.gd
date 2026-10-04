extends SceneTree
# A crowd kind's role as a contact sheet (CrowdSheet.cs: VISUAL=key ROLE=role N=cells STEP=s START=s YAW=deg OUT=png).
func _init():
	get_root().add_child(load("res://tools_scenes/CrowdSheet.cs").new())
