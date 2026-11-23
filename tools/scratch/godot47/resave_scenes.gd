# Upgrade Project Files, the part the editor's menu does to text scenes: load each and save it back with this engine.
#   <godot 4.7.2 console exe> --headless --path godot --script <absolute path of this file>
extends SceneTree

func _init() -> void:
	for path in ["res://scenes/game.tscn", "res://scenes/slice.tscn"]:
		var scene: PackedScene = ResourceLoader.load(path)
		var err := ResourceSaver.save(scene, path)
		print("resave ", path, " -> ", err)
	quit()
