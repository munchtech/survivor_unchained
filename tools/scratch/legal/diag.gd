extends SceneTree
# Diagnostics for the legal motion check's marks: her body mesh's bones, and where her
# breasts' and crotch's landmarks are in bind pose. Headless; prints only.
func _init():
	var h = load("res://art/people/heroine.glb").instantiate()
	get_root().add_child(h)
	var skel = h.find_children("*", "Skeleton3D", true, false)[0]
	for bm in skel.get_children():
		if not (bm is MeshInstance3D): continue
		var src = bm.mesh
		print("mesh ", bm.name, " surfaces=", src.get_surface_count(), " skin binds=", bm.skin.get_bind_count() if bm.skin else -1)
		if bm.skin == null: continue
		var names = []
		for b in bm.skin.get_bind_count():
			var nm = String(bm.skin.get_bind_name(b))
			if nm == "": nm = skel.get_bone_name(bm.skin.get_bind_bone(b))
			names.append(nm)
		var want = []
		for i in names.size():
			var n = names[i].to_lower()
			if n.contains("breast") or n.contains("pelvis") or n.contains("thigh") or n.contains("glute") or n.contains("hip"): want.append("%d:%s" % [i, names[i]])
		print("  binds of interest: ", want)
		var lo = Vector3(1e9, 1e9, 1e9)
		var hi = -lo
		for si in src.get_surface_count():
			var arr = src.surface_get_arrays(si)
			for v in arr[Mesh.ARRAY_VERTEX]:
				lo = lo.min(v)
				hi = hi.max(v)
		print("  bbox ", lo, " .. ", hi)
		# Forward-most vertex mostly weighted to each breast bind.
		for si in src.get_surface_count():
			var arr = src.surface_get_arrays(si)
			var vs = arr[Mesh.ARRAY_VERTEX]
			var bones = arr[Mesh.ARRAY_BONES]
			var wts = arr[Mesh.ARRAY_WEIGHTS]
			if bones == null or bones.size() == 0: continue
			var per = bones.size() / vs.size()
			var best = {}
			var bestz = {}
			for i in vs.size():
				for j in per:
					var b = bones[i * per + j]
					var w = wts[i * per + j]
					if w > 0.5 and names[b].to_lower().contains("breast"):
						if not bestz.has(b) or vs[i].z > bestz[b]:
							bestz[b] = vs[i].z
							best[b] = vs[i]
			for b in best: print("  surface ", si, " breast bind ", names[b], " forward-most ", best[b])
			# The midline at several strictness: lowest vertex.
			for tol in [0.002, 0.004, 0.008, 0.015]:
				var low = null
				for v in vs:
					if abs(v.x) < tol and v.y > lo.y + 0.3 * (hi.y - lo.y) and v.y < lo.y + 0.6 * (hi.y - lo.y):
						if low == null or v.y < low.y: low = v
				print("  surface ", si, " midline |x|<", tol, " lowest ", low)
	quit()
