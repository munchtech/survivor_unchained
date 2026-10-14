extends SceneTree
# Ground truth for her fist on a held piece: her body and outfit as Godot skins them (the bind poses on the CPU, blend shapes left out,
# her clip from art/anim/heroine.res, HerPose Native and HerJoints as the game lays them), and the piece as the game mounts
# it (SheathedReview.Held: Arms.MountTransform and Arms.Seat), both in hand_r's own space (model metres), to JSON for
# tools/anim/griptruth.py. Only what lies within 0.2 m of hand_r. Each vertex keeps its top-weighted bone and that weight.
# usage: Godot --headless --path godot -s res://tools_scenes/grip_truth.gd -- OUT.json OUTFIT PIECE CLIP:FRAME[,CLIP:FRAME...]
#   e.g. ... -- C:/tmp/staff.json arcanist mage_staff her/idle_arcanist:0,her/cast_raise:10
var her: Node3D
var skel: Skeleton3D
var ap: AnimationPlayer
var jobs = []
var k = -1
var wait = 0
var out = ""
var piece = ""
var frames = []
const NEAR = 0.2

func _init():
	var a = OS.get_cmdline_user_args()
	out = a[0]
	var outfit = a[1]
	piece = a[2]
	for s in a[3].split(","):
		var p = s.split(":")
		jobs.append([p[0], int(p[1])])
	her = load("res://art/people/heroine.glb").instantiate()
	get_root().add_child(her)
	skel = her.find_children("*", "Skeleton3D", true, false)[0]
	var o = load("res://art/people/heroine_outfit_%s.gltf" % outfit).instantiate()
	var os_ = o.find_children("*", "Skeleton3D", true, false)[0]
	for mi in os_.get_children():
		if mi is MeshInstance3D and String(mi.name).begins_with(outfit + "_"):
			os_.remove_child(mi)
			mi.owner = null
			skel.add_child(mi)
			mi.skeleton = NodePath("..")
	o.free()
	var hp = load("res://src/Actors/HerPose.cs").new()
	skel.add_child(hp)
	hp.set("Native", 1.0)
	skel.add_child(load("res://src/Actors/HerJoints.cs").new())
	ap = AnimationPlayer.new()
	her.add_child(ap)
	ap.root_node = NodePath("..")
	ap.add_animation_library("her", load("res://art/anim/heroine.res"))
	load("res://tools_scenes/SheathedReview.cs").new().Held(skel, piece, "hand_r")

func _process(_d):
	if wait > 0:
		wait -= 1
		if wait == 0: grab()
		return false
	k += 1
	if k >= jobs.size():
		var f = FileAccess.open(out, FileAccess.WRITE)
		f.store_string(JSON.stringify({"piece": piece, "frames": frames}))
		f.close()
		print("grip_truth: wrote ", out)
		quit()
		return false
	if not ap.has_animation(jobs[k][0]):
		push_error("no clip " + jobs[k][0])
		quit(1)
		return false
	ap.play(jobs[k][0])
	ap.seek(jobs[k][1] / 30.0, true)
	ap.speed_scale = 0.0
	wait = 3
	return false

func r5(v: Vector3):
	return [snappedf(v.x, 0.00001), snappedf(v.y, 0.00001), snappedf(v.z, 0.00001)]

func grab():
	var hb = skel.find_bone("hand_r")
	var H: Transform3D = skel.global_transform * skel.get_bone_global_pose(hb)
	var Hi = H.affine_inverse()
	var verts = []
	var bone = []
	var wt = []
	var mesh = []
	var names = []
	# Skinned on the CPU as the renderer skins (bake_mesh_from_current_skeleton_pose needs a renderer): each vertex the
	# weighted sum of (bone's global pose x the skin's bind pose), in the skeleton's space (the meshes sit at its origin).
	var SG: Transform3D = skel.global_transform
	for m in her.find_children("*", "MeshInstance3D", true, false):
		if m.mesh == null or m.skin == null: continue
		var mn = names.size()
		names.append(String(m.name))
		if not m.transform.is_equal_approx(Transform3D.IDENTITY): print("grip_truth: ", m.name, " not at the skeleton's origin: ", m.transform)
		var nb = m.skin.get_bind_count()
		var M = []
		var bnames = []
		for bi in nb:
			var bn = m.skin.get_bind_name(bi)
			var b = skel.find_bone(bn) if bn != &"" else m.skin.get_bind_bone(bi)
			M.append(SG * skel.get_bone_global_pose(b) * m.skin.get_bind_pose(bi))
			bnames.append(skel.get_bone_name(b))
		for si in m.mesh.get_surface_count():
			var src = m.mesh.surface_get_arrays(si)
			var pv = src[Mesh.ARRAY_VERTEX]
			var bones = src[Mesh.ARRAY_BONES]
			var ws = src[Mesh.ARRAY_WEIGHTS]
			if bones == null or ws == null: continue
			var per = bones.size() / pv.size()
			for i in pv.size():
				var best = 0
				var g = Vector3.ZERO
				for j in per:
					var w = ws[i * per + j]
					if w > ws[i * per + best]: best = j
					if w > 0: g += (M[bones[i * per + j]] * pv[i]) * w
				var l = Hi * g
				if l.length() > NEAR: continue
				verts.append(r5(l))
				bone.append(bnames[bones[i * per + best]])
				wt.append(snappedf(ws[i * per + best], 0.001))
				mesh.append(mn)
	var pv_ = []
	var pn = []
	var pnames = []
	for m in skel.find_children("*", "MeshInstance3D", true, false):
		if m.skin != null or m.mesh == null: continue
		var gt: Transform3D = m.global_transform
		var mn = pnames.size()
		pnames.append(String(m.get_path()).get_file())
		for si in m.mesh.get_surface_count():
			for v in m.mesh.surface_get_arrays(si)[Mesh.ARRAY_VERTEX]:
				var l = Hi * (gt * v)
				if l.length() > NEAR: continue
				pv_.append(r5(l))
				pn.append(mn)
	frames.append({"clip": jobs[k][0], "frame": jobs[k][1], "t": ap.current_animation_position, "hand_scale": H.basis.get_scale().x,
		"her": {"v": verts, "bone": bone, "w": wt, "mesh": mesh, "meshes": names},
		"piece": {"v": pv_, "node": pn, "nodes": pnames}})
	print("grip_truth: %s f%d: %d of her vertices, %d of the piece's" % [jobs[k][0], jobs[k][1], verts.size(), pv_.size()])
