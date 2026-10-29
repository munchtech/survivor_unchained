extends SceneTree
# Upper-arm elevation over each clip (degrees above horizontal in spine_03's frame, per side) and where
# each breast bone's tip sits in spine_03's frame, for tuning HerRaise (Armor 16).
#   godot --headless --path godot -s res://tools_scenes/raise_dump.gd -- <out.json> [clip,clip...]
var done = false
func _process(_d):
	if done: return true
	done = true
	var args = OS.get_cmdline_user_args()
	var out = args[0]
	var only = args[1].split(",") if args.size() > 1 else []
	var scene = load("res://art/people/heroine.glb").instantiate()
	get_root().add_child(scene)
	var sk: Skeleton3D = scene.find_children("*", "Skeleton3D", true, false)[0]
	var ap := AnimationPlayer.new()
	scene.add_child(ap)
	ap.root_node = ap.get_path_to(scene)
	var lib: AnimationLibrary = load("res://art/anim/heroine.res")
	ap.add_animation_library("", lib)
	var names = lib.get_animation_list()
	var a0: Animation = lib.get_animation(names[0])
	print("track0 ", a0.track_get_path(0), " skel path ", scene.get_path_to(sk))
	var b = {}
	for n in ["spine_03", "upperarm_l", "upperarm_r", "lowerarm_l", "lowerarm_r", "breast_l", "breast_r", "clavicle_l", "clavicle_r"]:
		b[n] = sk.find_bone(n)
	var res = {}
	# rest
	sk.reset_bone_poses()
	res["_rest"] = sample(sk, b)
	for name in names:
		if only.size() > 0 and not (name in only): continue
		var an: Animation = lib.get_animation(name)
		ap.play(name)
		var rows = []
		var t := 0.0
		while t <= an.length + 0.001:
			ap.seek(t, true)
			sk.force_update_all_bone_transforms()
			var s = sample(sk, b)
			s["t"] = snapped(t, 0.001)
			rows.append(s)
			t += 1.0 / 30.0
		res[name] = rows
	var f = FileAccess.open(out, FileAccess.WRITE)
	f.store_string(JSON.stringify(res))
	f.close()
	return true

func sample(sk: Skeleton3D, b) -> Dictionary:
	var ch: Transform3D = sk.get_bone_global_pose(b["spine_03"])
	var inv = ch.affine_inverse()
	var d = {}
	for s in ["l", "r"]:
		var ua = inv * sk.get_bone_global_pose(b["upperarm_" + s]).origin
		var la = inv * sk.get_bone_global_pose(b["lowerarm_" + s]).origin
		var dir = (la - ua).normalized()
		d["el_" + s] = rad_to_deg(asin(clamp(dir.y, -1.0, 1.0)))
		d["dir_" + s] = [dir.x, dir.y, dir.z]
		var bp: Transform3D = sk.get_bone_global_pose(b["breast_" + s])
		var tip = inv * (bp.origin + bp.basis.y.normalized() * 0.085)
		d["tip_" + s] = [tip.x, tip.y, tip.z]
		d["head_" + s] = Array([(inv * bp.origin).x, (inv * bp.origin).y, (inv * bp.origin).z])
	return d
