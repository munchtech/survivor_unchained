extends SceneTree
# Only the named clips repacked into an existing library: each <name>.json in the (staged) clips dir replaces or adds
# that animation and its meta; every other clip in the library and its meta is kept as packed. anim_pack.gd builds the
# whole library from one folder, so a folder holding a few clips would drop the rest (tools/anim/out/clips is often
# partial in a worktree). Same conversion as anim_pack.gd.
#   godot --headless --path godot -s res://tools_scenes/anim_pack_merge.gd -- <clips dir> <lib.res> <meta.json> <name>...
func _clip(d: Dictionary) -> Animation:
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
	return a


func _init():
	var args = OS.get_cmdline_user_args()
	var dir = args[0]
	var out = args[1]
	var meta_out = args[2]
	var names = args.slice(3)
	var old: AnimationLibrary = ResourceLoader.load(out, "", ResourceLoader.CACHE_MODE_IGNORE)
	var metas = JSON.parse_string(FileAccess.get_file_as_string(meta_out))
	if old == null or metas == null or names.is_empty():
		print("MERGE ERROR: library, meta or names missing")
		quit(1)
		return
	var fresh = {}
	for n in names:
		var p = dir.path_join(n + ".json")
		if not FileAccess.file_exists(p):
			print("MERGE ERROR: no %s" % p)
			quit(1)
			return
		var d = JSON.parse_string(FileAccess.get_file_as_string(p))
		fresh[d["name"]] = _clip(d)
		var m = d["meta"]
		m["length"] = fresh[d["name"]].length
		m["loop"] = d["loop"]
		metas[d["name"]] = m
	# Rebuilt in name order, as anim_pack.gd adds them (its files sorted by name).
	var all = {}
	for n in old.get_animation_list():
		all[String(n)] = true
	var added = []
	for n in fresh:
		if not all.has(String(n)):
			added.append(String(n))
	for n in fresh:
		all[String(n)] = true
	var keys = all.keys()
	keys.sort()
	var lib = AnimationLibrary.new()
	for n in keys:
		lib.add_animation(StringName(n), fresh[n] if fresh.has(n) else old.get_animation(n))
	var err = ResourceSaver.save(lib, out)
	var fm = FileAccess.open(meta_out, FileAccess.WRITE)
	fm.store_string(JSON.stringify(metas, "\t", true))
	fm.close()
	print("PACKED %d clips into %s (%s), replaced: %s; added (new to the library): %s" % [lib.get_animation_list().size(), out, error_string(err), ", ".join(fresh.keys()), ", ".join(added) if added else "none"])
	quit()
