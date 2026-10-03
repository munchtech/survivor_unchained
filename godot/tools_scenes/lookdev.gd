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
				# Her head's parts as People.HerPart has them; the rest is skin.
				var part = String(mi.mesh.surface_get_material(s).resource_name)
				if part in ["eyes", "brows", "lashes", "teeth", "tongue"]:
					if part == "eyes":
						# As People.HerPart: shaders/heroine_eye.gdshader on her eyes' own paint.
						m = ShaderMaterial.new()
						m.shader = load("res://shaders/heroine_eye.gdshader")
						m.set_shader_parameter("eye", load("res://art/people/head_tex/heroine_eye.png"))
						m.set_shader_parameter("iris", load("res://art/people/head_tex/heroine_iris.png"))
						for kv in OS.get_environment("EYE").split(",", false):
							var e = kv.split("=")
							var xy = e[1].split(":")
							m.set_shader_parameter(e[0], Vector2(float(xy[0]), float(xy[1])) if xy.size() == 2 else float(e[1]))
					if part in ["brows", "lashes"]:
						m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
						m.alpha_scissor_threshold = 0.35
						m.alpha_antialiasing_mode = BaseMaterial3D.ALPHA_ANTIALIASING_ALPHA_TO_COVERAGE_AND_TO_ONE
						m.cull_mode = BaseMaterial3D.CULL_DISABLED
						m.albedo_color = hair_colour().darkened(0.45) if part == "brows" else Color(0.12, 0.08, 0.07)
						if part == "lashes": m.albedo_texture = load("res://art/people/head_tex/heroine_lashes.png")
					mi.set_surface_override_material(s, m)
					continue
				# As People.Skin: shaders/heroine_skin.gdshader (OLDSKIN=1 the material before it).
				if OS.get_environment("OLDSKIN") == "":
					var sk = ShaderMaterial.new()
					sk.shader = load("res://shaders/heroine_skin.gdshader")
					sk.set_shader_parameter("paint", m.albedo_texture)
					sk.set_shader_parameter("pores", load("res://art/people/skin_pores.png"))
					sk.set_shader_parameter("pore_scale", pore_scale(mi.mesh))
					if OS.get_environment("NOSSS") != "": sk.set_shader_parameter("scatter", 0.0)
					for kv in OS.get_environment("SKIN").split(",", false):
						var e = kv.split("=")
						sk.set_shader_parameter(e[0], float(e[1]))
					mi.set_surface_override_material(s, sk)
					continue
				m.albedo_color = Color(1.0, 0.86, 0.74)
				if OS.get_environment("NOTEX") != "": m.albedo_texture = null; m.albedo_color = Color(0.85, 0.62, 0.5)
				m.vertex_color_use_as_albedo = false
				m.subsurf_scatter_enabled = OS.get_environment("NOSSS") == ""
				m.subsurf_scatter_strength = 0.35
				m.subsurf_scatter_skin_mode = true
				m.roughness = 0.52
				mi.set_surface_override_material(s, m)
		var skel = h.find_children("*", "Skeleton3D", true, false)[0]
		# HIDE=name,...: those meshes of hers not drawn (to see what is what).
		for hide in OS.get_environment("HIDE").split(",", false):
			for mi in h.find_children(hide, "MeshInstance3D", true, false):
				mi.visible = false
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
					if OS.get_environment("OLDOUTFIT") == "": outfit_materials(mi)
					else:
						for s in mi.mesh.get_surface_count():
							if mi.mesh.surface_get_material(s) is StandardMaterial3D: mi.mesh.surface_get_material(s).vertex_color_use_as_albedo = false
			o.free()
			# Her skin under the outfit's fitted pieces is not drawn (its
			# channel in her vertex colours: warden red, arcanist green).
			var ch = ["warden", "arcanist", "reaver", "ranger"].find(outfit.trim_suffix("_").split(".")[0].split("_")[0])
			if ch >= 0 and OS.get_environment("NOHIDE") == "":
				for bm in skel.get_children():
					# (her body only, as People.HerOutfit has it: not her outfit's pieces, whose colours are their own)
					if bm is MeshInstance3D and not String(bm.name).contains(".") and not String(bm.name).contains("_") and bm.mesh.surface_get_format(0) & Mesh.ARRAY_FORMAT_COLOR:
						hide_skin(bm, ch)
		# HAIR=<style> (heroine_hair_<style>.gltf; "none" for none), HAIRCOLOR=#rrggbb.
		var style = OS.get_environment("HAIR") if OS.get_environment("HAIR") != "" else "long"
		if style != "none" and ResourceLoader.exists("res://art/people/heroine_hair_%s.gltf" % style):
			var hs = load("res://art/people/heroine_hair_%s.gltf" % style).instantiate()
			var hsk = hs.find_children("*", "Skeleton3D", true, false)[0]
			for mi in hsk.get_children():
				if mi is MeshInstance3D:
					hsk.remove_child(mi)
					mi.owner = null
					skel.add_child(mi)
					mi.skeleton = NodePath("..")
					for s in mi.mesh.get_surface_count():
						# As People.Hair: shaders/heroine_hair.gdshader, dyed.
						var m = ShaderMaterial.new()
						m.shader = load("res://shaders/heroine_hair.gdshader")
						m.set_shader_parameter("strands", mi.mesh.surface_get_material(s).albedo_texture)
						m.set_shader_parameter("colour", hair_colour())
						var is_cap = mi.mesh.surface_get_material(s).resource_name == "hair_cap"
						m.set_shader_parameter("cap", is_cap)
						m.set_shader_parameter("tie", mi.mesh.surface_get_material(s).resource_name == "hair_tie")
						mi.set_surface_override_material(s, m)
						# HAIRONLY=cap|cards: only that part shown (to look at each alone).
						var only = OS.get_environment("HAIRONLY")
						if only != "" and (only == "cap") != is_cap:
							var none = StandardMaterial3D.new()
							none.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
							none.albedo_color = Color(0, 0, 0, 0)
							mi.set_surface_override_material(s, none)
					if OS.get_environment("NOJIGGLE") == "":
						var sw = load("res://src/Actors/HairSway.cs").new()
						sw.Style = style
						mi.add_child(sw)
			hs.free()
		# FACE=name=value,...: her face's sliders (-1..1) and expressions (0..1), as People.HerFace.
		if OS.get_environment("FACE") != "":
			for pair in OS.get_environment("FACE").split(","):
				var kv = pair.split("=")
				var v = float(kv[1])
				for mi in skel.get_children():
					if mi is MeshInstance3D and mi.mesh.get_blend_shape_count() > 0:
						for n in [[kv[0] + "+", max(v, 0.0)], [kv[0] + "-", max(-v, 0.0)], [kv[0], v]]:
							var bi = mi.find_blend_shape_by_name(n[0])
							if bi >= 0: mi.set_blend_shape_value(bi, n[1])
		if OS.get_environment("NOHERPOSE") == "":
			skel.add_child(load("res://src/Actors/HerPose.cs").new())
		if OS.get_environment("NOJIGGLE") == "":
			skel.add_child(load("res://src/Actors/HerJiggle.cs").new())
		# NOLIFE=1: her face still (no blinks, no eyes moving), for side-by-side pictures.
		if OS.get_environment("NOLIFE") == "":
			skel.add_child(load("res://src/Actors/HerFaceLife.cs").new())
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
	cam.fov = float(OS.get_environment("FOV")) if OS.get_environment("FOV") != "" else 40.0
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

# As People.OutfitMaterials: her outfit's pieces by shaders/heroine_outfit.gdshader
# (OLDOUTFIT=1: as exported, to compare).
var outfit_table = null
func outfit_materials(mi):
	if outfit_table == null:
		outfit_table = JSON.parse_string(FileAccess.get_file_as_string("res://art/people/outfit_materials.json"))
	for s in mi.mesh.get_surface_count():
		var src = mi.mesh.surface_get_material(s)
		if mi.get_surface_override_material(s) != null or not (src is StandardMaterial3D): continue
		src.vertex_color_use_as_albedo = false
		if not outfit_table.has(String(src.resource_name)): continue
		var k = {"leather": 0, "metal": 1, "cloth": 2, "gloss": 3}.get(outfit_table[String(src.resource_name)]["kind"], -1)
		if k < 0: continue
		var m = ShaderMaterial.new()
		m.shader = load("res://shaders/heroine_outfit.gdshader")
		m.set_shader_parameter("kind", k)
		m.set_shader_parameter("albedo", src.albedo_texture)
		m.set_shader_parameter("normal_map", src.normal_texture)
		m.set_shader_parameter("orm", src.roughness_texture)
		m.set_shader_parameter("has_orm", src.roughness_texture != null)
		m.set_shader_parameter("roughness_value", src.roughness)
		m.set_shader_parameter("metallic_value", src.metallic)
		m.set_shader_parameter("repeats", float(outfit_table[String(src.resource_name)]["repeats"]))
		if OS.get_environment("OUTFITVIEW") != "": m.set_shader_parameter("debug_view", int(OS.get_environment("OUTFITVIEW")))
		for kv in OS.get_environment("OUTFITSET").split(",", false):
			var e = kv.split("=")
			m.set_shader_parameter(e[0], float(e[1]))
		mi.set_surface_override_material(s, m)

# As People.PoreScale: pore tiles to a UV unit, one every 1.5 cm on her.
func pore_scale(mesh):
	var area = 0.0
	var uv_area = 0.0
	for s in mesh.get_surface_count():
		var arr = mesh.surface_get_arrays(s)
		if arr[Mesh.ARRAY_TEX_UV] == null: continue
		var v = arr[Mesh.ARRAY_VERTEX]
		var uv = arr[Mesh.ARRAY_TEX_UV]
		var idx = arr[Mesh.ARRAY_INDEX]
		for t in range(0, idx.size() - 2, 3):
			area += (v[idx[t + 1]] - v[idx[t]]).cross(v[idx[t + 2]] - v[idx[t]]).length() / 2.0
			uv_area += abs((uv[idx[t + 1]] - uv[idx[t]]).cross(uv[idx[t + 2]] - uv[idx[t]])) / 2.0
	return sqrt(area / uv_area) / 0.015 if uv_area > 0.0 else 30.0

func hair_colour():
	return Color(OS.get_environment("HAIRCOLOR")) if OS.get_environment("HAIRCOLOR") != "" else Color("#8f2d14")

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
	# MOVE=metres: each figure carried forward and back that far, about one
	# return a second and a half (to see her hair swing and stream).
	if OS.get_environment("MOVE") != "":
		var a = float(OS.get_environment("MOVE"))
		for h in get_root().get_child(0).get_children():
			if h is Node3D and not h is Camera3D and not h is Light3D and h.has_method("find_children"):
				h.position.z = a * sin(t * TAU / 1.5)
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
