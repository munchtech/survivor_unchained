extends SceneTree
# Her skeleton as Godot sees it, for tools/anim: every bone's name, parent and
# rest (local and global), written as JSON. The clips are built against it.
#   godot --headless --path godot -s res://tools_scenes/anim_skeleton.gd -- <out.json> [res://model.glb]
func _init():
	var args = OS.get_cmdline_user_args()
	var out = args[0]
	var model = args[1] if args.size() > 1 else "res://art/people/heroine.glb"
	var scene = load(model).instantiate()
	var sk: Skeleton3D = scene.find_children("*", "Skeleton3D", true, false)[0]
	var bones = []
	for b in sk.get_bone_count():
		var rest: Transform3D = sk.get_bone_rest(b)
		var g: Transform3D = sk.get_bone_global_rest(b)
		var q = rest.basis.get_rotation_quaternion()
		var gq = g.basis.get_rotation_quaternion()
		bones.append({
			"name": sk.get_bone_name(b), "parent": sk.get_bone_parent(b),
			"rot": [q.x, q.y, q.z, q.w], "pos": [rest.origin.x, rest.origin.y, rest.origin.z],
			"scale": [rest.basis.get_scale().x, rest.basis.get_scale().y, rest.basis.get_scale().z],
			"grot": [gq.x, gq.y, gq.z, gq.w], "gpos": [g.origin.x, g.origin.y, g.origin.z],
		})
	var path = str(scene.get_path_to(sk))
	var f = FileAccess.open(out, FileAccess.WRITE)
	f.store_string(JSON.stringify({"model": model, "skeleton_path": path, "skeleton_xform": var_to_str(sk.transform), "bones": bones}, "  "))
	f.close()
	scene.free()
	quit()
