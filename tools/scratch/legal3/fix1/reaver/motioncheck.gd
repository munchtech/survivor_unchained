extends SceneTree
# Lookdev: the heroine played through several clips side by side, front on, saved as one picture.
# BODY=hero: the hero in her place (hero.glb, his hair hero_hair_*, his outfits hero_outfit_*), as People.Hero has him.
var clips = []
var out = ""
var t = 0.0
var shot = 0
var players = []
var clip_len = 0.0
var follow_skel: Skeleton3D
var follow_from = Vector3.ZERO
var view_cams = []
var view_from = []
var view_names = []
var view_ports = []
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
	var who = OS.get_environment("BODY") if OS.get_environment("BODY") != "" else "heroine"
	for i in clips.size():
		var h = load("res://art/people/%s.glb" % who).instantiate()
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
						var iris = "res://art/people/head_tex/%s_iris.png" % who
						m.set_shader_parameter("iris", load(iris if ResourceLoader.exists(iris) else "res://art/people/head_tex/heroine_iris.png"))
						# (his own flint grey, as People.HisEyes)
						if who == "hero":
							m.set_shader_parameter("recolour", 1.0)
							m.set_shader_parameter("iris_colour", Color("#727c84"))
							m.set_shader_parameter("ring_colour", Color("#8a8672"))
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
					# (as People.Skin: shallower on her body and hands than her face)
					if m.resource_name != "skin_head": sk.set_shader_parameter("pore_depth", 0.4)
					# (His relief baked from his sculpt, and his own tone: People.Skin, People.HisTone.)
					if m.normal_texture != null:
						sk.set_shader_parameter("relief", m.normal_texture)
						sk.set_shader_parameter("has_relief", true)
					if who == "hero":
						sk.set_shader_parameter("tone", Color(1.0, 0.95, 0.9))
						# (his rougher skin, as People.HisSkin)
						sk.set_shader_parameter("rough", 0.62)
						sk.set_shader_parameter("shine", 0.3)
						sk.set_shader_parameter("edge_rough", 0.45)
						# (his brows dyed his hair's colour, and his stubble: People.HisShadow;
						# BEARD=, SCALP= its depth, 0 to 1)
						if part == "skin_head" and ResourceLoader.exists("res://art/people/head_tex/hero_shadow.png"):
							var hc = Color(OS.get_environment("HAIRCOLOR")) if OS.get_environment("HAIRCOLOR") != "" else Color("#3a2a20")
							sk.set_shader_parameter("shadow_mask", load("res://art/people/head_tex/hero_shadow.png"))
							sk.set_shader_parameter("beard_shadow", float(OS.get_environment("BEARD")) if OS.get_environment("BEARD") != "" else 0.0)
							sk.set_shader_parameter("scalp_shadow", float(OS.get_environment("SCALP")) if OS.get_environment("SCALP") != "" else 0.0)
							sk.set_shader_parameter("shadow_colour", hc.darkened(0.35))
							sk.set_shader_parameter("brow_dye", float(OS.get_environment("BROWDYE")) if OS.get_environment("BROWDYE") != "" else 0.0)
							sk.set_shader_parameter("brow_paint", Color(OS.get_environment("BROWPAINT")) if OS.get_environment("BROWPAINT") != "" else Color("#4c3c2e"))
							sk.set_shader_parameter("brow_colour", hc)
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
			var o = load("res://art/people/%s_outfit_%s.gltf" % [who, outfit.split("_")[0]]).instantiate()
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
			# Her skin under the outfit's fitted pieces is drawn tucked in (its
			# channel in her vertex colours: warden red, arcanist green).
			var ch = ["warden", "arcanist", "reaver", "ranger"].find(outfit.trim_suffix("_").split(".")[0].split("_")[0])
			if ch >= 0 and OS.get_environment("NOHIDE") == "":
				for bm in skel.get_children():
					# (her body only, as People.HerOutfit has it: not her outfit's pieces, whose colours are their own)
					if bm is MeshInstance3D and not String(bm.name).contains(".") and not String(bm.name).contains("_") and bm.mesh.surface_get_format(0) & Mesh.ARRAY_FORMAT_COLOR:
						hide_skin(bm, ch)
		if OS.get_environment("MARKS") != "":
			for bm in skel.get_children():
				if bm is MeshInstance3D and not String(bm.name).contains(".") and not String(bm.name).contains("_") and bm.mesh.surface_get_format(0) & Mesh.ARRAY_FORMAT_COLOR:
					legal_marks(bm)
			if OS.get_environment("LEGALBARE") != "" and outfit != "":
				for pm in skel.get_children():
					if pm is MeshInstance3D and String(pm.name).begins_with(outfit.split("_")[0] + "_"): pm.visible = false
		# HAIR=<style> (heroine_hair_<style>.gltf; "none" for none), HAIRCOLOR=#rrggbb.
		var style = OS.get_environment("HAIR") if OS.get_environment("HAIR") != "" else "long"
		if style != "none" and ResourceLoader.exists("res://art/people/%s_hair_%s.gltf" % [who, style]):
			var hs = load("res://art/people/%s_hair_%s.gltf" % [who, style]).instantiate()
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
			var pose = load("res://src/Actors/HerPose.cs").new()
			# (His carriage as People.Hero sets it: arms clear of his lats, hips square.)
			if who == "hero":
				pose.ArmsIn = -5.0
				pose.HipTilt = 0.0
				pose.NeckPitch = float(OS.get_environment("NECK")) if OS.get_environment("NECK") != "" else 22.0
			skel.add_child(pose)
		if OS.get_environment("NOJIGGLE") == "" and who == "heroine":
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
		ap.add_animation_library("her", load("res://art/anim/heroine.res"))
		ap.root_node = ".."
		if OS.get_environment("SPREAD") != "":
			var anim = ap.get_animation(clips[i])
			anim.loop_mode = Animation.LOOP_LINEAR
			clip_len = max(clip_len, anim.length)
		ap.play(clips[i])
		if follow_skel == null:
			var sks = h.find_children("*", "Skeleton3D", true, false)
			if sks.size() > 0: follow_skel = sks[0]
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
	e.tonemap_mode = Environment.TONE_MAPPER_LINEAR if OS.get_environment("MARKS") != "" or OS.get_environment("LINEAR") != "" else Environment.TONE_MAPPER_AGX
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
	var views = OS.get_environment("VIEWS")
	if views != "":
		var parts = views.split(";", false)
		for vi in parts.size():
			var p = parts[vi].split(":")
			var o = p[1].split(",")
			var c: Camera3D = cam
			var port: Viewport = get_root()
			if vi > 0:
				var sv = SubViewport.new()
				sv.size = Vector2i(960, 540)
				sv.msaa_3d = get_root().msaa_3d
				sv.render_target_update_mode = SubViewport.UPDATE_ALWAYS
				root.add_child(sv)
				c = Camera3D.new()
				sv.add_child(c)
				c.current = true
				port = sv
			var a = deg_to_rad(float(o[0]))
			c.fov = float(p[2])
			c.look_at_from_position(Vector3(sin(a) * float(o[2]), float(o[1]), cos(a) * float(o[2])), Vector3(0, float(o[3]), 0))
			view_cams.append(c)
			view_from.append(c.global_position)
			view_names.append(p[0])
			view_ports.append(port)
	else:
		view_cams.append(cam)
		view_from.append(cam.global_position)
		view_names.append("")
		view_ports.append(get_root())

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
		var k = {"leather": 0, "metal": 1, "cloth": 2, "gloss": 3, "twill": 4}.get(outfit_table[String(src.resource_name)]["kind"], -1)
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
	return sqrt(area / uv_area) / 0.009 if uv_area > 0.0 else 50.0

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
	# As People.TuckSkin: her skin under the outfit tucked in by her skin's
	# shader, not cut away.
	for si in mi.get_surface_override_material_count():
		var m = mi.get_surface_override_material(si)
		if m is ShaderMaterial and m.shader == load("res://shaders/heroine_skin.gdshader"):
			m.set_shader_parameter("tuck_channel", ch)

func _process(delta):
	t += delta
	# FOLLOW=1: every camera keeps its offset from her hips (taken at 0.5 s, once she has settled).
	if OS.get_environment("FOLLOW") != "" and follow_skel != null:
		var hb = follow_skel.find_bone("pelvis")
		if hb < 0: hb = 0
		var hp = follow_skel.global_transform * follow_skel.get_bone_global_pose(hb).origin
		hp.y = 0.0
		if t < 0.5:
			follow_from = hp
			for vi in view_cams.size(): view_from[vi] = view_cams[vi].global_position
		else:
			for vi in view_cams.size(): view_cams[vi].global_position = view_from[vi] + (hp - follow_from)
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
		var step = 1.0 / 15.0
		if OS.get_environment("SPREAD") != "" and clip_len > 0.0: step = clip_len / float(int(frames))
		var k = int((t - 1.0) / step)
		if t > 1.0 and k > shot:
			shot = k
			for vi in view_ports.size():
				var tag = ("_" + view_names[vi]) if view_names[vi] != "" else ""
				view_ports[vi].get_texture().get_image().save_png(out.replace(".png", "%s_%02d.png" % [tag, k]))
				if follow_skel != null: save_landmarks(view_cams[vi], out.replace(".png", "%s_%02d.json" % [tag, k]))
			if k >= int(frames): quit()
		return false
	if t > 1.5:
		var img = get_root().get_texture().get_image()
		img.save_png(out)
		quit()
	return false

# Where her landmarks fall on screen in a picture (count.py: which breast, which way). Each
# nipple tip is posed as its breast bone moves it, with 2 cm up and 2 cm in towards her
# midline beside it, so count.py can say where on the rim a pixel lies as seen in that view.
var legal_tips = {}
var _baked_at = -1
var _baked_vs = {}
func save_landmarks(c: Camera3D, path: String):
	var sk = follow_skel
	var g = sk.global_transform
	var pts = {}
	for nm in ["breast_l", "breast_r"]:
		var b = sk.find_bone(nm)
		if b >= 0: pts[nm] = g * sk.get_bone_global_pose(b).origin
	var outj = {}
	for n in pts:
		var s = c.unproject_position(pts[n])
		outj[n] = {"xy": [s.x, s.y], "behind": c.is_position_behind(pts[n])}
	# The tip as the engine skins it this frame (her mesh baked in its current pose), so the
	# landmark sits exactly on the drawn nipple, and the skin above it and inside it likewise.
	# (The bone's own pose put it about 12 cm low in the first calibration; kept as bonetip_.)
	if legal_tips.size() > 0 and Engine.get_process_frames() != _baked_at:
		_baked_at = Engine.get_process_frames()
		_baked_vs = {}
		var bm: ArrayMesh = legal_tips.values()[0][3].bake_mesh_from_current_skeleton_pose()
		for si in bm.get_surface_count(): _baked_vs[si] = bm.surface_get_arrays(si)[Mesh.ARRAY_VERTEX]
	for n in legal_tips:
		var e = legal_tips[n]
		var xf = e[3].global_transform * sk.get_bone_global_pose(e[0]) * e[1]
		var tip = e[2]
		var bv = _baked_vs[e[4]]
		var p0 = e[3].global_transform * bv[e[5]]
		var mid = []
		for h in e[6]:
			var acc = Vector3.ZERO
			for i in h: acc += bv[i]
			mid.append(acc / max(h.size(), 1))
		var gb = e[3].global_transform.basis
		var pu = c.unproject_position(p0 + (gb * (mid[0] - mid[1])).normalized() * 0.02)
		var pin = c.unproject_position(p0 + (gb * (mid[2] - mid[3])).normalized() * 0.02)
		var s0 = c.unproject_position(p0)
		outj["tip_" + n] = {"xy": [s0.x, s0.y], "behind": c.is_position_behind(p0), "up": [pu.x, pu.y], "inner": [pin.x, pin.y]}
		var pb = xf * tip
		var sb = c.unproject_position(pb)
		outj["bonetip_" + n] = {"xy": [sb.x, sb.y], "behind": c.is_position_behind(pb)}
	var vs = c.get_viewport().get_visible_rect().size
	outj["size"] = {"xy": [vs.x, vs.y], "behind": true}
	var f = FileAccess.open(path, FileAccess.WRITE)
	f.store_string(JSON.stringify(outj))
	f.close()

var _tinted: Shader
func tinted_skin(base: Shader) -> Shader:
	if _tinted != null: return _tinted
	var code = base.code
	var end = code.rfind("}")
	var flat = "ALBEDO = vec3(0.0); SPECULAR = 0.0; ROUGHNESS = 1.0; METALLIC = 0.0; RIM = 0.0; SSS_STRENGTH = 0.0; BACKLIGHT = vec3(0.0); "
	# (the outfit's channel of her vertex colours, as her shader's tuck reads it; -1: none)
	var head = code.find("void fragment()")
	code = code.substr(0, head) + "uniform int legal_tuck_ch = -1;\n" + code.substr(head)
	end = code.rfind("}")
	code = code.substr(0, end) \
		+ "\t// legal motion check (test codes, never in the game): see tools/legal/motioncheck\n" \
		+ "\tfloat legal_th = legal_tuck_ch == 0 ? COLOR.r : legal_tuck_ch == 1 ? COLOR.g : legal_tuck_ch == 2 ? COLOR.b : legal_tuck_ch == 3 ? COLOR.a : 0.0;\n" \
		+ "\tif (UV2.y > 0.5) { " + flat + "EMISSION = vec3(0.0, 1.0, 0.0); }\n" \
		+ "\telse if (UV2.x < 0.995) { " + flat + "EMISSION = vec3(UV2.x * 0.9, legal_th > 0.5 ? 0.5 : 0.0, 1.0); }\n" \
		+ "\telse if (legal_th > 0.02) { " + flat + "EMISSION = vec3((1.0 - legal_th) * 0.9, 1.0, 1.0); }\n}\n"
	_tinted = Shader.new()
	_tinted.code = code
	return _tinted

func legal_marks(mi):
	var src = mi.mesh
	var fresh = load("res://art/people/heroine.glb").instantiate()
	for c in fresh.find_children("*", "MeshInstance3D", true, false):
		if c.name == mi.name: src = c.mesh
	fresh.free()
	var skel = mi.get_parent()
	var breast = {}
	var breast_name = {}
	for b in mi.skin.get_bind_count():
		var nm = String(mi.skin.get_bind_name(b))
		if nm == "": nm = skel.get_bone_name(mi.skin.get_bind_bone(b))
		if nm.to_lower().contains("breast"):
			breast[b] = mi.skin.get_bind_pose(b)
			breast_name[b] = nm
	var tips = []
	var under = null
	var mons = null
	for si in src.get_surface_count():
		var arr = src.surface_get_arrays(si)
		var vs = arr[Mesh.ARRAY_VERTEX]
		if vs.size() == 0: continue
		var ns = arr[Mesh.ARRAY_NORMAL]
		var bones = arr[Mesh.ARRAY_BONES]
		var wts = arr[Mesh.ARRAY_WEIGHTS]
		var idx = arr[Mesh.ARRAY_INDEX]
		var per = bones.size() / vs.size()
		# Her crotch: the lowest downward-facing point on the midline, and where the mons
		# begins to face forward in front of it.
		for i in vs.size():
			var v = vs[i]
			if abs(v.x) < 0.003 and v.y > 0.6 and v.y < 1.1 and ns[i].y < -0.9 and abs(ns[i].x) < 0.6:
				if under == null or v.y < under.y: under = v
		if under != null:
			for i in vs.size():
				var v = vs[i]
				if abs(v.x) < 0.003 and v.z > under.z and v.y > under.y and v.y < under.y + 0.15 and ns[i].z > 0.8:
					if mons == null or v.y < mons.y: mons = v
		var owner = PackedInt32Array()
		owner.resize(vs.size())
		var along = PackedFloat32Array()
		along.resize(vs.size())
		var reach = {}
		for i in vs.size():
			owner[i] = -1
			for j in per:
				var b = bones[i * per + j]
				if breast.has(b) and wts[i * per + j] > 0.5:
					owner[i] = b
					along[i] = (breast[b] * vs[i]).y
					reach[b] = max(reach.get(b, -1e9), along[i])
		var key = func(v): return Vector3i(roundi(v.x * 20000.0), roundi(v.y * 20000.0), roundi(v.z * 20000.0))
		var nsum = {}
		var ncount = {}
		var seen = {}
		for t in range(0, idx.size(), 3):
			var tri = [idx[t], idx[t + 1], idx[t + 2]]
			if owner[tri[0]] < 0 and owner[tri[1]] < 0 and owner[tri[2]] < 0: continue
			for e in 3:
				var p = tri[e]
				var q = tri[(e + 1) % 3]
				for pair in [[p, q], [q, p]]:
					var kp = key.call(vs[pair[0]])
					var kq = key.call(vs[pair[1]])
					var ek = [kp, kq]
					if seen.has(ek): continue
					seen[ek] = true
					nsum[kp] = nsum.get(kp, Vector3.ZERO) + vs[pair[1]]
					ncount[kp] = ncount.get(kp, 0) + 1
		var best = {}
		var bests = {}
		var bidx = {}
		for i in vs.size():
			var b = owner[i]
			if b < 0 or along[i] < 0.5 * reach[b]: continue
			var kk = key.call(vs[i])
			if not ncount.has(kk) or ncount[kk] < 3: continue
			var score = -(nsum[kk] / float(ncount[kk]) - vs[i]).dot(ns[i].normalized())
			if not bests.has(b) or score > bests[b]:
				bests[b] = score
				best[b] = vs[i]
				bidx[b] = i
		for b in best:
			tips.append(best[b])
			# (and the skin 2 cm above the tip and 2 cm in towards her midline, at rest, so the
			# directions on screen come from her skin as drawn too)
			# (and her skin 2 to 6 cm around it, split into its upper and lower halves and its
			# inner and outer ones: the halves' centres, as drawn, give its up and in directions)
			var halves = [[], [], [], []]
			for i in vs.size():
				var off = vs[i] - best[b]
				var ol = off.length()
				if ol < 0.02 or ol > 0.06: continue
				var side = -signf(best[b].x) * off.x
				if off.y > 0.01: halves[0].append(i)
				elif off.y < -0.01: halves[1].append(i)
				if side > 0.01: halves[2].append(i)
				elif side < -0.01: halves[3].append(i)
			legal_tips[breast_name[b]] = [skel.find_bone(breast_name[b]), breast[b], best[b], mi, si, bidx[b], halves]
	print("legal marks: ", mi.name, " tips=", tips, " crotch underside=", under, " mons front=", mons)
	print("legal marks: mesh transform ", mi.transform, " in a skeleton at ", skel.transform)
	# Codes on the body as drawn (trimmed or not): same vertex positions.
	src = mi.mesh
	var overrides = []
	for si in src.get_surface_count(): overrides.append(mi.get_surface_override_material(si))
	var out = ArrayMesh.new()
	var counts = [0, 0]
	for si in src.get_surface_count():
		var arr = src.surface_get_arrays(si)
		var vs = arr[Mesh.ARRAY_VERTEX]
		var ns = arr[Mesh.ARRAY_NORMAL]
		var uv2 = PackedVector2Array()
		uv2.resize(vs.size())
		for i in vs.size():
			var v = vs[i]
			var d = 1.0
			for tp in tips: d = min(d, v.distance_to(tp) / 0.06)
			var g = 0.0
			if under != null and mons != null and abs(v.x) < 0.012 and abs(ns[i].x) < 0.7 \
					and v.z > under.z - 0.023 and v.y > under.y - 0.005 and v.y < mons.y - 0.005:
				g = 1.0
			uv2[i] = Vector2(min(d, 1.0), g)
			counts[0] += int(d * 0.06 < 0.022)
			counts[1] += int(g)
		arr[Mesh.ARRAY_TEX_UV2] = uv2
		var fmt = src.surface_get_format(si)
		var custom = fmt & (Mesh.ARRAY_FORMAT_CUSTOM_MASK << Mesh.ARRAY_FORMAT_CUSTOM0_SHIFT | Mesh.ARRAY_FORMAT_CUSTOM_MASK << Mesh.ARRAY_FORMAT_CUSTOM1_SHIFT | Mesh.ARRAY_FORMAT_CUSTOM_MASK << Mesh.ARRAY_FORMAT_CUSTOM2_SHIFT | Mesh.ARRAY_FORMAT_CUSTOM_MASK << Mesh.ARRAY_FORMAT_CUSTOM3_SHIFT)
		out.add_surface_from_arrays(src.surface_get_primitive_type(si), arr, [], {}, custom)
		out.surface_set_material(si, src.surface_get_material(si))
	print("legal marks: vertices within the areola=", counts[0], " in the genital strip=", counts[1])
	mi.mesh = out
	# (the outfit's channel, as lookdev and People.HerOutfit find it)
	var tuck_ch = ["warden", "arcanist", "reaver", "ranger"].find(OS.get_environment("OUTFIT").trim_suffix("_").split(".")[0].split("_")[0])
	for si in overrides.size():
		var m = overrides[si]
		if m is ShaderMaterial and m.shader != null and String(m.shader.resource_path).ends_with("heroine_skin.gdshader"):
			# Carry every uniform across (the outfit's tuck_channel among them), so her skin is
			# drawn, tucked and hidden exactly as in play; only the codes are added.
			var kept = {}
			for u in m.shader.get_shader_uniform_list():
				kept[u.name] = m.get_shader_parameter(u.name)
			m.shader = tinted_skin(m.shader)
			for n in kept: m.set_shader_parameter(n, kept[n])
			m.set_shader_parameter("legal_tuck_ch", tuck_ch if OS.get_environment("NOHIDE") == "" else -1)
		mi.set_surface_override_material(si, m)
	print("legal marks: tucked skin read from vertex colour channel ", tuck_ch)
