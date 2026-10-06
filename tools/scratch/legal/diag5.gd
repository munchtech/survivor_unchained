extends SceneTree
# Her crotch's underside on the midline (|x| < 3 mm, normal facing down), front to back, and
# where it meets the front of the mons and the cleft behind. Headless.
func _init():
	var h = load("res://art/people/heroine.glb").instantiate()
	get_root().add_child(h)
	var mi = null
	for c in h.find_children("*", "MeshInstance3D", true, false):
		if String(c.name) == "Heroine": mi = c
	var arr = mi.mesh.surface_get_arrays(0)
	var vs = arr[Mesh.ARRAY_VERTEX]
	var ns = arr[Mesh.ARRAY_NORMAL]
	var pts = []
	for i in vs.size():
		var v = vs[i]
		if abs(v.x) < 0.003 and v.y > 0.85 and v.y < 1.0 and abs(ns[i].x) < 0.6:
			pts.append([v.z, v.y, ns[i].y, ns[i].z])
	pts.sort_custom(func(a, b): return a[0] < b[0])
	var last = -1.0
	for p in pts:
		if p[0] - last < 0.006: continue
		last = p[0]
		print("z=%.3f y=%.3f normal(y=%.2f z=%.2f)" % [p[0], p[1], p[2], p[3]])
	quit()
