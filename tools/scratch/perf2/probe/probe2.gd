extends SceneTree
# How long a mesh's Duplicate and SurfaceGetArrays take on the real renderer
# (do they read the GPU's buffers back and stall?).
var frame := 0
var m: ArrayMesh
func _init():
	var st := SurfaceTool.new()
	st.create_from(SphereMesh.new(), 0)
	var sphere := st.commit()
	var arr := sphere.surface_get_arrays(0)
	m = ArrayMesh.new()
	for i in 4:
		m.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	var mi := MeshInstance3D.new()
	mi.mesh = m
	root.add_child(mi)
	var cam := Camera3D.new()
	cam.position = Vector3(0, 0, 4)
	root.add_child(cam)
	print("verts per surface ", (arr[Mesh.ARRAY_VERTEX] as PackedVector3Array).size())

func _process(_d):
	frame += 1
	if frame == 30:
		var t := Time.get_ticks_usec()
		for i in 20:
			var d = m.duplicate()
		var t1 := Time.get_ticks_usec()
		for i in 20:
			var a = m.surface_get_arrays(0)
		var t2 := Time.get_ticks_usec()
		for i in 20:
			var s := MultiMesh.new()
		var t3 := Time.get_ticks_usec()
		print("duplicate x20: %d us; surface_get_arrays x20: %d us; (4 surfaces each dup)" % [t1 - t, t2 - t1])
	if frame == 32:
		quit()
	return false
