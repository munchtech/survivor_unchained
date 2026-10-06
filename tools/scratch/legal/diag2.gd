extends SceneTree
# Where each breast bone points, and the vertex farthest along each of its axes.
func _init():
	var h = load("res://art/people/heroine.glb").instantiate()
	get_root().add_child(h)
	var skel = h.find_children("*", "Skeleton3D", true, false)[0]
	var mi = null
	for c in skel.get_children():
		if c is MeshInstance3D and String(c.name) == "Heroine": mi = c
	var src = mi.mesh
	for b in mi.skin.get_bind_count():
		var nm = String(mi.skin.get_bind_name(b))
		if not nm.to_lower().contains("breast"): continue
		var bp = mi.skin.get_bind_pose(b)
		var inv = bp.affine_inverse()
		print(nm, " head(mesh)=", inv.origin, " +Y(mesh)=", inv.basis.y.normalized(), " +Z(mesh)=", inv.basis.z.normalized())
		for axis in ["y", "-y", "z", "-z"]:
			var best = null
			var bs = -1e9
			for si in src.get_surface_count():
				var arr = src.surface_get_arrays(si)
				var vs = arr[Mesh.ARRAY_VERTEX]
				var bones = arr[Mesh.ARRAY_BONES]
				var wts = arr[Mesh.ARRAY_WEIGHTS]
				if vs.size() == 0: continue
				var per = bones.size() / vs.size()
				for i in vs.size():
					var w = 0.0
					for j in per:
						if bones[i * per + j] == b: w = max(w, wts[i * per + j])
					if w < 0.5: continue
					var l = bp * vs[i]
					var s = {"y": l.y, "-y": -l.y, "z": l.z, "-z": -l.z}[axis]
					if s > bs:
						bs = s
						best = vs[i]
			print("   farthest along ", axis, ": ", best, " (", bs, ")")
	quit()
