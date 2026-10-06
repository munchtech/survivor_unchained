extends SceneTree
# Her midline profile (|x| < 3 mm) from the crotch's lowest point up 20 cm: height, depth and
# which way the surface faces, to see where the underside turns into the mons. Headless.
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
		if abs(v.x) < 0.003 and v.y > 0.83 and v.y < 1.05 and v.z > -0.03:
			pts.append([v.y, v.z, ns[i].y, ns[i].z])
	pts.sort_custom(func(a, b): return a[0] < b[0])
	var last = -1.0
	for p in pts:
		if p[0] - last < 0.008: continue
		last = p[0]
		print("y=%.3f z=%.3f normal(y=%.2f z=%.2f)" % [p[0], p[1], p[2], p[3]])
	quit()
