extends SceneTree
func _init():
	var n := 4
	var v := PackedVector3Array(); var c := PackedColorArray(); var u := PackedVector2Array(); var u2 := PackedVector2Array()
	for i in n:
		v.append(Vector3(i, 2*i, 3*i)); c.append(Color(0.5 + i*0.3, 0.1234, 1.7, 0.999)); u.append(Vector2(i*0.25, 1)); u2.append(Vector2(2.5, 4))
	var idx := PackedInt32Array([0,1,2, 1,3,2])
	var arr := []
	arr.resize(Mesh.ARRAY_MAX)
	arr[Mesh.ARRAY_VERTEX] = v; arr[Mesh.ARRAY_COLOR] = c; arr[Mesh.ARRAY_TEX_UV] = u; arr[Mesh.ARRAY_TEX_UV2] = u2; arr[Mesh.ARRAY_INDEX] = idx
	var m := ArrayMesh.new()
	m.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr, [], {}, Mesh.ARRAY_FLAG_USE_DYNAMIC_UPDATE)
	var s: Dictionary = RenderingServer.mesh_get_surface(m.get_rid(), 0)
	var f: int = s["format"]
	print("format ", f, " vstride ", RenderingServer.mesh_surface_get_format_vertex_stride(f, n), " astride ", RenderingServer.mesh_surface_get_format_attribute_stride(f, n), " istride ", RenderingServer.mesh_surface_get_format_index_stride(f, n))
	print("offsets col ", RenderingServer.mesh_surface_get_format_offset(f, n, Mesh.ARRAY_COLOR), " uv ", RenderingServer.mesh_surface_get_format_offset(f, n, Mesh.ARRAY_TEX_UV), " uv2 ", RenderingServer.mesh_surface_get_format_offset(f, n, Mesh.ARRAY_TEX_UV2))
	print("vertex ", s["vertex_data"])
	print("attrib ", s["attribute_data"])
	print("index ", s["index_data"], " count ", s["index_count"])
	quit()
