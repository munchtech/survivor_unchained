extends SceneTree
# tools/anim's clips (one JSON each) packed into one AnimationLibrary for the
# game, with what the game needs to know of each (speed, contacts, layer)
# beside it as JSON.
#   godot --headless --path godot -s res://tools_scenes/anim_pack.gd -- <clips dir> <out.res> <out meta.json>
func _init():
	var args = OS.get_cmdline_user_args()
	var dir = args[0]
	var out = args[1]
	var meta_out = args[2]
	var lib = AnimationLibrary.new()
	var metas = {}
	var files = DirAccess.get_files_at(dir)
	files.sort()
	for f in files:
		if not f.ends_with(".json"):
			continue
		var d = JSON.parse_string(FileAccess.get_file_as_string(dir.path_join(f)))
		var a = Animation.new()
		var fps = float(d["fps"])
		a.length = float(d["length"])
		a.step = 1.0 / fps
		a.loop_mode = Animation.LOOP_LINEAR if d["loop"] else Animation.LOOP_NONE
		for tr in d["tracks"]:
			var rot = tr["type"] == "rot"
			var i = a.add_track(Animation.TYPE_ROTATION_3D if rot else Animation.TYPE_POSITION_3D)
			a.track_set_path(i, NodePath(d["path"] + ":" + tr["bone"]))
			a.track_set_interpolation_type(i, Animation.INTERPOLATION_LINEAR)
			a.track_set_interpolation_loop_wrap(i, true)
			var keys = tr["keys"]
			for k in keys.size():
				var t = min(k / fps, a.length)
				var v = keys[k]
				if rot:
					a.rotation_track_insert_key(i, t, Quaternion(v[0], v[1], v[2], v[3]).normalized())
				else:
					a.position_track_insert_key(i, t, Vector3(v[0], v[1], v[2]))
		lib.add_animation(StringName(d["name"]), a)
		var m = d["meta"]
		m["length"] = a.length
		m["loop"] = d["loop"]
		metas[d["name"]] = m
	var err = ResourceSaver.save(lib, out)
	var fm = FileAccess.open(meta_out, FileAccess.WRITE)
	fm.store_string(JSON.stringify(metas, "\t", true))
	fm.close()
	print("PACKED %d clips into %s (%s)" % [lib.get_animation_list().size(), out, error_string(err)])
	quit()
