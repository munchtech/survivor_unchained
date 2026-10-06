extends SceneTree
# Every resource the pack carries, and each dependency it names: any that the
# pack does not carry would fail to load in a release build.
# godot --headless --path godot -s depcheck.gd -- <pack_listing.txt>

func _init() -> void:
	var listing: String = OS.get_cmdline_user_args()[0]
	var f := FileAccess.open(listing, FileAccess.READ)
	var shipped := {}
	while not f.eof_reached():
		var line := f.get_line().strip_edges()
		if line == "":
			continue
		var p := line.split("  ", false)
		shipped["res://" + p[p.size() - 1].strip_edges()] = true
	var missing := {}
	var checked := 0
	for path in shipped.keys():
		if not ResourceLoader.exists(path):
			continue
		checked += 1
		for d in ResourceLoader.get_dependencies(path):
			var dep: String = d.get_slice("::", d.get_slice_count("::") - 1)
			if dep.begins_with("uid://"):
				var id := ResourceUID.text_to_id(dep)
				dep = ResourceUID.get_id_path(id) if ResourceUID.has_id(id) else dep
			if not shipped.has(dep):
				missing[dep] = path
	print("checked %d resources; dependencies not shipped: %d" % [checked, missing.size()])
	for k in missing.keys():
		print("  ", k, "  <- ", missing[k])
	quit()
