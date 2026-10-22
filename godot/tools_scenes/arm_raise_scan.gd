extends SceneTree
# Peak upper-arm elevation per clip, per side: angle of (lowerarm - upperarm) above the
# horizontal in spine_03's frame (asin of its y), sampled every 1/30 s. One JSON line per clip.
#   godot --headless --path godot -s res://tools_scenes/arm_raise_scan.gd -- <out.jsonl>
func _init():
	var out = OS.get_cmdline_user_args()[0]
	var scene = load("res://art/people/heroine.glb").instantiate()
	var sk: Skeleton3D = scene.find_children("*", "Skeleton3D", true, false)[0]
	var lib: AnimationLibrary = load("res://art/anim/heroine.res")
	var n = sk.get_bone_count()
	var rest_rot = []
	var rest_pos = []
	var rest_scale = []
	for b in n:
		var r = sk.get_bone_rest(b)
		rest_rot.append(r.basis.get_rotation_quaternion())
		rest_pos.append(r.origin)
		rest_scale.append(r.basis.get_scale())
	var chest = sk.find_bone("spine_03")
	var ua = {"l": sk.find_bone("upperarm_l"), "r": sk.find_bone("upperarm_r")}
	var la = {"l": sk.find_bone("lowerarm_l"), "r": sk.find_bone("lowerarm_r")}
	var f = FileAccess.open(out, FileAccess.WRITE)
	for name in lib.get_animation_list():
		var anim: Animation = lib.get_animation(name)
		var rot_t = {}
		var pos_t = {}
		for t in anim.get_track_count():
			var p = str(anim.track_get_path(t))
			if not p.contains(":"):
				continue
			var bn = sk.find_bone(p.get_slice(":", p.get_slice_count(":") - 1))
			if bn < 0:
				continue
			if anim.track_get_type(t) == Animation.TYPE_ROTATION_3D:
				rot_t[bn] = t
			elif anim.track_get_type(t) == Animation.TYPE_POSITION_3D:
				pos_t[bn] = t
		var mx = {"l": -999.0, "r": -999.0}
		var mt = {"l": 0.0, "r": 0.0}
		var above = {"l": 0.0, "r": 0.0}
		var steps = int(ceil(anim.length * 30.0))
		for i in range(steps + 1):
			var tm = min(i / 30.0, anim.length)
			var g = []
			g.resize(n)
			for b in n:
				var q: Quaternion = rest_rot[b]
				var pos: Vector3 = rest_pos[b]
				if rot_t.has(b):
					q = anim.rotation_track_interpolate(rot_t[b], tm)
				if pos_t.has(b):
					pos = anim.position_track_interpolate(pos_t[b], tm)
				var loc = Transform3D(Basis(q).scaled(rest_scale[b]), pos)
				var par = sk.get_bone_parent(b)
				g[b] = loc if par < 0 else g[par] * loc
			var inv: Basis = g[chest].basis.orthonormalized().inverse()
			for s in ["l", "r"]:
				var d = (inv * (g[la[s]].origin - g[ua[s]].origin)).normalized()
				var e = rad_to_deg(asin(clamp(d.y, -1.0, 1.0)))
				if e > mx[s]:
					mx[s] = e
					mt[s] = tm
				if e > 30.0:
					above[s] += 1.0 / 30.0
		f.store_line(JSON.stringify({"name": name, "length": anim.length,
			"max_l": snapped(mx["l"], 0.1), "t_l": snapped(mt["l"], 0.01),
			"max_r": snapped(mx["r"], 0.1), "t_r": snapped(mt["r"], 0.01),
			"above30_l": snapped(above["l"], 0.01), "above30_r": snapped(above["r"], 0.01)}))
	f.close()
	scene.free()
	quit()
