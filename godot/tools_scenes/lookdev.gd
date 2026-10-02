extends SceneTree
# Lookdev: the heroine played through several clips side by side, front on, saved as one picture.
var clips = []
var out = ""
var t = 0.0
var shot = 0
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
				if OS.get_environment("NOTEX") != "": m.albedo_texture = null; m.albedo_color = Color(0.85, 0.62, 0.5)
				m.vertex_color_use_as_albedo = false
				m.subsurf_scatter_enabled = true
				m.subsurf_scatter_strength = 0.35
				m.subsurf_scatter_skin_mode = true
				m.roughness = 0.52
				mi.set_surface_override_material(s, m)
		var skel = h.find_children("*", "Skeleton3D", true, false)[0]
		# OUTFIT=prefix ("warden_" a set, "warden_straps" one piece): her pieces (heroine_outfit_<set>.gltf), on her skeleton.
		var outfit = OS.get_environment("OUTFIT")
		if outfit != "":
			var o = load("res://art/people/heroine_outfit_%s.gltf" % outfit.split("_")[0]).instantiate()
			var os_ = o.find_children("*", "Skeleton3D", true, false)[0]
			for mi in os_.get_children():
				if mi is MeshInstance3D and String(mi.name).begins_with(outfit):
					os_.remove_child(mi)
					mi.owner = null
					skel.add_child(mi)
					mi.skeleton = NodePath("..")
					fur(mi)
			o.free()
			# Her skin under the outfit's fitted pieces is not drawn (its
			# channel in her vertex colours: warden red, arcanist green).
			var ch = ["warden", "arcanist", "reaver", "ranger"].find(outfit.trim_suffix("_").split(".")[0].split("_")[0])
			if ch >= 0 and OS.get_environment("NOHIDE") == "":
				for bm in skel.get_children():
					if bm is MeshInstance3D and not String(bm.name).contains("."):
						hide_skin(bm, ch)
		if OS.get_environment("NOHERPOSE") == "":
			skel.add_child(load("res://src/Actors/HerPose.cs").new())
		if OS.get_environment("NOJIGGLE") == "":
			skel.add_child(load("res://src/Actors/HerJiggle.cs").new())
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
	# A sky for metal to reflect (the background stays plain).
	var sky = Sky.new()
	var sm = ProceduralSkyMaterial.new()
	sm.ground_bottom_color = Color(0.18, 0.16, 0.14)
	sm.ground_horizon_color = Color(0.45, 0.42, 0.4)
	sky.sky_material = sm
	e.sky = sky
	e.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
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

# As People.Fur: a fur piece drawn again in shells, each further out.
func fur(mi, shells = 20):
	for si in mi.mesh.get_surface_count():
		var src = mi.mesh.surface_get_material(si)
		if src != null and src.resource_name == "stocking":
			var sm = ShaderMaterial.new()
			sm.shader = load("res://shaders/sheer.gdshader")
			mi.set_surface_override_material(si, sm)
			continue
		if src == null or src.resource_name != "fur": continue
		var first = null
		var last = null
		for i in shells + 1:
			var m = ShaderMaterial.new()
			m.shader = load("res://shaders/fur_shell.gdshader")
			m.set_shader_parameter("albedo_tex", src.albedo_texture)
			m.set_shader_parameter("tint", src.albedo_color)
			m.set_shader_parameter("layer", float(i) / shells)
			if last: last.next_pass = m
			else: first = m
			last = m
		mi.set_surface_override_material(si, first)

func hide_skin(mi, ch):
	var src = mi.mesh
	var out = ArrayMesh.new()
	for si in src.get_surface_count():
		var arr = src.surface_get_arrays(si)
		var col = arr[Mesh.ARRAY_COLOR]
		if col != null and col.size() > 0:
			var idx = arr[Mesh.ARRAY_INDEX]
			var kept = PackedInt32Array()
			for t in range(0, idx.size(), 3):
				var a = col[idx[t]][ch]; var b = col[idx[t + 1]][ch]; var c = col[idx[t + 2]][ch]
				if a < 0.5 or b < 0.5 or c < 0.5:
					kept.append(idx[t]); kept.append(idx[t + 1]); kept.append(idx[t + 2])
			arr[Mesh.ARRAY_INDEX] = kept
		out.add_surface_from_arrays(src.surface_get_primitive_type(si), arr)
		out.surface_set_material(si, src.surface_get_material(si))
	var overrides = []
	for si in src.get_surface_count(): overrides.append(mi.get_surface_override_material(si))
	mi.mesh = out
	for si in overrides.size(): mi.set_surface_override_material(si, overrides[si])

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
	# FRAMES=n: n pictures, a fifteenth of a second apart, from 1 s in (out gets _NN).
	var frames = OS.get_environment("FRAMES")
	if frames != "":
		var k = int((t - 1.0) * 15.0)
		if t > 1.0 and k > shot:
			shot = k
			get_root().get_texture().get_image().save_png(out.replace(".png", "_%02d.png" % k))
			if k >= int(frames): quit()
		return false
	if t > 1.5:
		var img = get_root().get_texture().get_image()
		img.save_png(out)
		quit()
	return false
