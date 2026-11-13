extends SceneTree
# A package NPC's skin (People.NpcSkin) on our base head and body: the uniforms it sets, by default and with a manifest override (NpcSkinCheck.cs).
func _init():
	get_root().add_child(load("res://tools_scenes/NpcSkinCheck.cs").new())
