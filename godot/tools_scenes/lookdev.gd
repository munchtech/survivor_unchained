extends SceneTree
# Lookdev: the heroine played through several clips side by side, front on, saved as one picture.
var clips = []
var out = ""
var t = 0.0
var players = []
func _init():
	var args = OS.get_cmdline_user_args()
	clips = args[0].split(",")
	out = args[1]
	var root = Node3D.new()
	get_root().add_child(root)
	var libs = []
	for f in ["res://assets/people/UAL1.glb", "res://assets/people/UAL2.glb"]:
		var s = load(f).instantiate()
		var ap = s.find_children("*", "AnimationPlayer", true, false)[0]
		libs.append(ap.get_animation_library(""))
	for i in clips.size():
		var h = load("res://art/people/heroine.glb").instantiate()
		root.add_child(h)
		h.position = Vector3((i - (clips.size() - 1) / 2.0) * 1.1, 0, 0)
		for mi in h.find_children("*", "MeshInstance3D", true, false):
			for s in mi.mesh.get_surface_count():
				var m = mi.mesh.surface_get_material(s).duplicate()
				m.albedo_color = Color(1.0, 0.86, 0.74)
				m.subsurf_scatter_enabled = true
				m.subsurf_scatter_strength = 0.35
				m.subsurf_scatter_skin_mode = true
				m.roughness = 0.52
				mi.set_surface_override_material(s, m)
		var ap = AnimationPlayer.new()
		h.add_child(ap)
		var lib = AnimationLibrary.new()
		for L in libs:
			for n in L.get_animation_list():
				if not lib.has_animation(n): lib.add_animation(n, L.get_animation(n))
		ap.add_animation_library("", lib)
		ap.root_node = ".."
		ap.play(clips[i])
		players.append(ap)
	var cam = Camera3D.new()
	cam.position = Vector3(0, float(OS.get_environment("CAMY")) if OS.get_environment("CAMY") != "" else 1.0, (1.6 + clips.size() * 0.75) * (float(OS.get_environment("CAMD")) if OS.get_environment("CAMD") != "" else 1.0))
	cam.fov = 40
	root.add_child(cam)
	cam.current = true
	# ORBIT=deg,height,dist,targety: the camera round the middle figure, looking at it.
	var orbit = OS.get_environment("ORBIT")
	if orbit != "":
		var o = orbit.split(",")
		var a = deg_to_rad(float(o[0]))
		cam.position = Vector3(sin(a) * float(o[2]), float(o[1]), cos(a) * float(o[2]))
		cam.look_at_from_position(cam.position, Vector3(0, float(o[3]), 0))
	var env = WorldEnvironment.new()
	var e = Environment.new()
	e.background_mode = Environment.BG_COLOR
	e.background_color = Color(0.32, 0.33, 0.36)
	e.ambient_light_color = Color(0.6, 0.6, 0.65)
	e.ambient_light_energy = 0.6
	e.tonemap_mode = Environment.TONE_MAPPER_AGX
	env.environment = e
	root.add_child(env)
	var key = DirectionalLight3D.new()
	key.rotation_degrees = Vector3(-35, 30, 0)
	key.light_energy = 1.6
	key.shadow_enabled = true
	root.add_child(key)
	var rim = DirectionalLight3D.new()
	rim.rotation_degrees = Vector3(-20, 200, 0)
	rim.light_energy = 0.0 if OS.get_environment("NORIM") != "" else 1.2
	root.add_child(rim)

func _process(delta):
	t += delta
	# POSE=bone:x,y,z degrees;...  applied on top of rest, no clip.
	var pose = OS.get_environment("POSE")
	if pose != "":
		for ap in players: ap.stop()
		for h in get_root().get_child(0).get_children():
			for sk in h.find_children("*", "Skeleton3D", true, false):
				for b in sk.get_bone_count(): sk.set_bone_pose(b, sk.get_bone_rest(b))
				for item in pose.split(";"):
					var kv = item.split(":")
					var e = kv[1].split(",")
					var b = sk.find_bone(kv[0])
					var q = Quaternion.from_euler(Vector3(deg_to_rad(float(e[0])), deg_to_rad(float(e[1])), deg_to_rad(float(e[2]))))
					sk.set_bone_pose_rotation(b, sk.get_bone_rest(b).basis.get_rotation_quaternion() * q)
	if t > 1.5:
		var img = get_root().get_texture().get_image()
		img.save_png(out)
		quit()
	return false
