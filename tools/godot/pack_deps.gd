extends SceneTree
# For tools/godot/pack_listing.py: every resource a pack carries, and each
# dependency it names. One the pack does not carry would fail to load in a
# release build. Prints "deps N" (N missing), then each missing one.
#   godot --headless --path godot -s tools/godot/pack_deps.gd -- PATHS_FILE

func _init() -> void:
	var f := FileAccess.open(OS.get_cmdline_user_args()[0], FileAccess.READ)
	var shipped := {}
	while not f.eof_reached():
		var line := f.get_line().strip_edges()
		if line != "":
			shipped["res://" + line] = true
	var missing := {}
	for path in shipped.keys():
		if not ResourceLoader.exists(path):
			continue
		for d in ResourceLoader.get_dependencies(path):
			var dep: String = d.get_slice("::", d.get_slice_count("::") - 1)
			if dep.begins_with("uid://"):
				var id := ResourceUID.text_to_id(dep)
				dep = ResourceUID.get_id_path(id) if ResourceUID.has_id(id) else dep
			if not shipped.has(dep):
				missing[dep] = path
	print("deps %d" % missing.size())
	for k in missing.keys():
		print("  ", k, " (for ", missing[k], ")")
	quit()
