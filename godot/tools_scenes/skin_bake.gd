extends SceneTree
# Her body skinned from the IMPORTED mesh's own arrays (bones, weights, the skin's binds; every weight the vertex
# carries, the engine's linear blend) at a --pose-dump's bone poses (Body 6: the proof that the import keeps all eight
# bone weights a point; MeshInstance3D.bake_mesh_from_current_skeleton_pose refuses a scene loaded this way). Per surface of the mesh named "Heroine": its format's 8-weight flag, bones a
# vertex, then its rest and posed vertices (float32), into <out.bin>; a line per surface to stdout.
#   godot --headless --path godot -s res://tools_scenes/skin_bake.gd -- <dump.json> <out.bin> [res://model.glb]
var scene: Node
var frames := 0

func _initialize():
	var a = OS.get_cmdline_user_args()
	var model = a[2] if a.size() > 2 else "res://art/people/heroine.glb"
	scene = load(model).instantiate()
	root.add_child(scene)

func _process(_d):
	frames += 1
	if frames < 4:
		return false
	var a = OS.get_cmdline_user_args()
	var pose = JSON.parse_string(FileAccess.get_file_as_string(a[0]))
	var mi: MeshInstance3D = null
	for m in scene.find_children("*", "MeshInstance3D", true, false):
		if m.name == "Heroine":
			mi = m
	var sk: Skeleton3D = mi.get_node(mi.skeleton)
	var miss = 0
	for b in sk.get_bone_count():
		var n = sk.get_bone_name(b)
		if not pose.has(n):
			miss += 1
			continue
		var v = pose[n]
		var t = Transform3D(Basis(Vector3(v[0], v[1], v[2]), Vector3(v[3], v[4], v[5]), Vector3(v[6], v[7], v[8])), Vector3(v[9], v[10], v[11]))
		sk.set_bone_global_pose(b, t)
	sk.force_update_all_bone_transforms()
	var sk_ = mi.skin
	var xf = []
	for i in sk_.get_bind_count():
		var bb = sk_.get_bind_bone(i)
		if bb < 0:
			bb = sk.find_bone(sk_.get_bind_name(i))
		xf.append(sk.get_bone_global_pose(bb) * sk_.get_bind_pose(i))
	var src: Mesh = mi.mesh
	var f = FileAccess.open(a[1], FileAccess.WRITE)
	f.store_32(src.get_surface_count())
	print("skin_bake: bones missing from the dump ", miss, "; skin binds ", sk_.get_bind_count(), "; mesh to skeleton ", mi.global_transform, " / ", sk.global_transform)
	for s in src.get_surface_count():
		var arr = src.surface_get_arrays(s)
		var rest: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
		var bones: PackedInt32Array = arr[Mesh.ARRAY_BONES]
		var w: PackedFloat32Array = arr[Mesh.ARRAY_WEIGHTS]
		var st = bones.size() / max(rest.size(), 1)
		var posed = PackedVector3Array()
		posed.resize(rest.size())
		for i in rest.size():
			var acc = Vector3.ZERO
			for k in st:
				var wk = w[i * st + k]
				if wk > 0.0:
					acc += wk * (xf[bones[i * st + k]] * rest[i])
			posed[i] = acc
		var eight = (src.surface_get_format(s) & Mesh.ARRAY_FLAG_USE_8_BONE_WEIGHTS) != 0
		var over4 = 0
		if bones.size() == rest.size() * 8:
			for i in rest.size():
				if w[i * 8 + 4] > 0.0:
					over4 += 1
		print("skin_bake: surface ", s, " vertices ", rest.size(), " 8-weight flag ", eight, " bones/vertex ", bones.size() / max(rest.size(), 1), " vertices with a 5th weight ", over4)
		f.store_32(rest.size())
		var r = PackedFloat32Array()
		var p = PackedFloat32Array()
		for i in rest.size():
			r.append_array([rest[i].x, rest[i].y, rest[i].z])
			p.append_array([posed[i].x, posed[i].y, posed[i].z])
		f.store_buffer(r.to_byte_array())
		f.store_buffer(p.to_byte_array())
	f.close()
	scene.free()
	quit()
	return true
