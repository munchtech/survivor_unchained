extends SceneTree
# Clips judged as an animator judges them: the heroine played through a clip
# at a fixed 30 frames a second, every frame (or every STEP-th) photographed
# and tiled into one contact sheet, numbered, over a checked floor so a foot
# that slides shows. Run with --fixed-fps 30 so time is exact.
#
#   godot --path godot --fixed-fps 30 --resolution 420x560 -s res://tools_scenes/anim_review.gd -- <clip> <out.png>
#
# The clip is a name from her library (res://art/anim/heroine.res, as
# "her/<name>") or from the Universal Animation Libraries ("ual/<name>"), or a
# path to one of tools/anim's JSON clips (unpacked: a test pose, a clip in work).
# Options by environment:
#   VIEW=front|side|back|three|top|game   where the camera stands (game: the arena's 64 degrees)
#   FRAMES=n  STEP=k  START=s              n cells, every k-th frame, from s seconds in
#   COLS=c                                 cells to a row
#   SPEED=m/s                              carried forward at this speed (in metres of the world), camera following
#   PLAY=x                                 playback speed
#   OUTFIT=warden|arcanist|reaver|ranger   her outfit; HAIR=style; WEAPON=sword|sword+shield|shield|staff|axe|axes|daggers|wand|crossbow|flask
#   MODEL=female|male                      a townsfolk body (the kit's) instead of hers, in PARTS (kit
#                                          outfit parts, comma-separated); clips "folk/<name>"
#   MODEL=hero                             the hero, with his clips ("him/<name>", art/anim/hero.res)
#   NOHERPOSE=1                            without her corrective pose layer
#   GESTURE=her/nod GESTUREAT=s            a gesture laid over the clip (Gestures.cs) s seconds in
#   FULL=1                                 save every frame as its own picture too (out_NN.png)
#   BODYDIR=folder                         her body and outfits read from another build (before a change)
#   NOJOINTS=1                             her helper bones left undriven (not her body before them:
#                                          an elbow's share then follows the upper arm; use BODYDIR)
#   SKINDBG=faces|cull|uv                  her skin as faces seen from behind (red) / normals turned
#                                          away (blue); her own skin drawn from both sides; her UVs as colour
#   HAIRCLEAR=1 [HAIRMESH=folder]          debug: per photographed frame, how near her hair chain comes to her posed
#                                          body and outfit (signed cm, negative = inside) and its jump in her neck frame
var clip = ""
var out = ""
var her: Node3D
var ap: AnimationPlayer
var cam: Camera3D
var frame = 0
var shots = []
var nframes = 16
var step = 1
var start = 0.0
var speed = 0.0
var travelled = 0.0
var view = "three"
var warm = 4
var vp: SubViewport

func _init():
	var args = OS.get_cmdline_user_args()
	clip = args[0]
	out = args[1]
	nframes = int(env("FRAMES", "16"))
	step = int(env("STEP", "1"))
	start = float(env("START", "0"))
	speed = float(env("SPEED", "0"))
	view = env("VIEW", "three")
	# Each cell (W by H) is drawn in a viewport of its own, whatever the
	# project's window and stretch settings are.
	vp = SubViewport.new()
	vp.size = Vector2i(int(env("W", "360")), int(env("H", "480")))
	vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	vp.msaa_3d = Viewport.MSAA_4X
	get_root().add_child(vp)
	var root = Node3D.new()
	vp.add_child(root)
	var model = env("MODEL", "")
	if model == "hero":
		her = load("res://art/people/hero.glb").instantiate()
	elif model != "":
		her = load("res://assets/people/Superhero_%s_FullBody.gltf" % model.capitalize()).instantiate()
	else:
		her = people("heroine.glb")
	root.add_child(her)
	her.scale = Vector3.ONE * 1.04
	if model == "hero": hero(her)
	elif model != "": kit(her, env("PARTS", ""))
	else: dress(her)
	ap = AnimationPlayer.new()
	her.add_child(ap)
	ap.root_node = NodePath("..")
	# Advanced by hand, after each photograph (see _process): played by the
	# tree, the pose drawn at a tick was a frame on from the one asked for.
	ap.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
	var ual = AnimationLibrary.new()
	for f in ["res://assets/people/UAL1.glb", "res://assets/people/UAL2.glb"]:
		var s = load(f).instantiate()
		var p = s.find_children("*", "AnimationPlayer", true, false)[0]
		var L = p.get_animation_library("")
		for n in L.get_animation_list():
			if not ual.has_animation(n): ual.add_animation(n, L.get_animation(n))
		s.free()
	ap.add_animation_library("ual", ual)
	if ResourceLoader.exists("res://art/anim/heroine.res"):
		ap.add_animation_library("her", load("res://art/anim/heroine.res"))
	if ResourceLoader.exists("res://art/anim/folk.res"):
		ap.add_animation_library("folk", load("res://art/anim/folk.res"))
	if ResourceLoader.exists("res://art/anim/hero.res"):
		ap.add_animation_library("him", load("res://art/anim/hero.res"))
	# A clip straight from tools/anim's JSON (a path ending .json), unpacked:
	# a test pose or a clip being worked on, seen before it is packed.
	if clip.ends_with(".json"):
		var a = json_clip(clip)
		var tl = AnimationLibrary.new()
		tl.add_animation("clip", a)
		ap.add_animation_library("test", tl)
		clip = "test/clip"
	if not ap.has_animation(clip):
		push_error("no clip " + clip)
		quit(1)
		return
	ap.play(clip, 0, float(env("PLAY", "1")))
	if start > 0: ap.seek(start, true)
	# OVER=clip: that clip laid over this one on the upper body (as the
	# game lays a swing over her run: the spine up, filtered, at OVERSPEED,
	# fired OVERAT seconds in).
	if env("OVER", "") != "": overlay(env("OVER", ""))
	if env("GESTURE", "") != "":
		var gsk: Skeleton3D = her.find_children("*", "Skeleton3D", true, false)[0]
		gestures = load("res://src/Actors/Gestures.cs").new()
		gsk.add_child(gestures)
	# The helper bones (HerJoints) from the finished pose, as in the game:
	# last of every layer. NOJOINTS=1 leaves them at rest (as before them).
	if env("NOJOINTS", "") == "":
		var jsk: Skeleton3D = her.find_children("*", "Skeleton3D", true, false)[0]
		jsk.add_child(load("res://src/Actors/HerJoints.cs").new())
	stage(root)

var tree: AnimationTree
var gestures = null

# A clip as tools/anim writes it (anim_pack.gd packs the same JSON).
func json_clip(path):
	var d = JSON.parse_string(FileAccess.get_file_as_string(path))
	var a = Animation.new()
	var fps = float(d["fps"])
	a.length = float(d["length"])
	a.step = 1.0 / fps
	a.loop_mode = Animation.LOOP_LINEAR if d["loop"] else Animation.LOOP_NONE
	for tr in d["tracks"]:
		var rot = tr["type"] == "rot"
		var i = a.add_track(Animation.TYPE_ROTATION_3D if rot else Animation.TYPE_POSITION_3D)
		a.track_set_path(i, NodePath(d["path"] + ":" + tr["bone"]))
		a.track_set_interpolation_type(i, Animation.INTERPOLATION_LINEAR)
		a.track_set_interpolation_loop_wrap(i, true)
		var keys = tr["keys"]
		for k in keys.size():
			var v = keys[k]
			var t = min(k / fps, a.length)
			if rot: a.rotation_track_insert_key(i, t, Quaternion(v[0], v[1], v[2], v[3]).normalized())
			else: a.position_track_insert_key(i, t, Vector3(v[0], v[1], v[2]))
	return a

func overlay(over):
	ap.stop()
	var bt = AnimationNodeBlendTree.new()
	var base = AnimationNodeAnimation.new()
	base.animation = clip
	var up = AnimationNodeAnimation.new()
	up.animation = over
	var sc = AnimationNodeTimeScale.new()
	var shot = AnimationNodeOneShot.new()
	shot.fadein_time = 0.05
	shot.fadeout_time = 0.18
	shot.filter_enabled = true
	var skel: Skeleton3D = her.find_children("*", "Skeleton3D", true, false)[0]
	for b in skel.get_bone_count():
		var n = skel.get_bone_name(b)
		if n in ["root", "pelvis"] or n.begins_with("thigh") or n.begins_with("calf") or n.begins_with("foot") or n.begins_with("ball") or n.begins_with("glute"): continue
		shot.set_filter_path(NodePath("Armature/Skeleton3D:" + n), true)
	bt.add_node("base", base)
	bt.add_node("up", up)
	bt.add_node("sc", sc)
	bt.add_node("shot", shot)
	bt.connect_node("sc", 0, "up")
	bt.connect_node("shot", 0, "base")
	bt.connect_node("shot", 1, "sc")
	bt.connect_node("output", 0, "shot")
	tree = AnimationTree.new()
	tree.tree_root = bt
	her.add_child(tree)
	tree.root_node = NodePath("..")
	for L in ap.get_animation_library_list(): tree.add_animation_library(L, ap.get_animation_library(L))
	tree.set("parameters/sc/scale", float(env("OVERSPEED", "1.6")))
	tree.active = true
	tree.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL

func env(k, d):
	var v = OS.get_environment(k)
	return v if v != "" else d

# Her body or an outfit as the game has it, or (BODYDIR=folder) read at run
# time from another build of them (a copy from before a change: no import).
# (OUTFITSHADER=1) an outfit piece drawn as the game draws it, as
# People.OutfitMaterials does (heroine_outfit.gdshader from
# outfit_materials.json), not in the file's own materials.
func game_outfit(mi):
	var table = JSON.parse_string(FileAccess.get_file_as_string("res://art/people/outfit_materials.json"))
	var sh = load("res://shaders/heroine_outfit.gdshader")
	for s in mi.mesh.get_surface_count():
		var src = mi.mesh.surface_get_material(s)
		if not (src is StandardMaterial3D) or not table.has(src.resource_name):
			continue
		var e = table[src.resource_name]
		var kind = {"leather": 0, "metal": 1, "cloth": 2, "gloss": 3, "twill": 4}.get(e["kind"], -1)
		if kind < 0:
			continue
		src.vertex_color_use_as_albedo = false
		var m = ShaderMaterial.new()
		m.shader = sh
		m.set_shader_parameter("kind", kind)
		m.set_shader_parameter("albedo", src.albedo_texture)
		m.set_shader_parameter("normal_map", src.normal_texture)
		m.set_shader_parameter("orm", src.roughness_texture)
		m.set_shader_parameter("has_orm", src.roughness_texture != null)
		m.set_shader_parameter("roughness_value", src.roughness)
		m.set_shader_parameter("metallic_value", src.metallic)
		m.set_shader_parameter("repeats", float(e["repeats"]))
		if e.has("pull"):
			m.set_shader_parameter("view_pull", float(e["pull"]))
		if e.has("drop_folded"):
			m.set_shader_parameter("drop_folded", bool(e["drop_folded"]))
		mi.set_surface_override_material(s, m)


func people(file):
	var dir = env("BODYDIR", "")
	if dir == "":
		return load("res://art/people/" + file).instantiate()
	var doc = GLTFDocument.new()
	var st = GLTFState.new()
	st.use_named_skin_binds = true
	if doc.append_from_file(dir.path_join(file), st) != OK:
		push_error("can't read " + dir.path_join(file))
		quit(1)
	return doc.generate_scene(st)

# A townsfolk body in the kit's clothes, as People.Build puts one together.
func kit(h, parts):
	var skel: Skeleton3D = h.find_children("*", "Skeleton3D", true, false)[0]
	for part in parts.split(",", false):
		var sc = load("res://assets/people/%s.gltf" % part).instantiate()
		var from = sc.find_children("*", "Skeleton3D", true, false)[0]
		for mi in from.get_children():
			if mi is MeshInstance3D:
				from.remove_child(mi)
				mi.owner = null
				skel.add_child(mi)
				mi.skeleton = NodePath("..")
		sc.free()

# The hero (MODEL=hero) as his model comes, his paint on plain materials,
# with his carriage over library clips (People.Hero) and what he holds.
func hero(h):
	var skel: Skeleton3D = h.find_children("*", "Skeleton3D", true, false)[0]
	var hp = load("res://src/Actors/HerPose.cs").new()
	hp.set("ArmsIn", -5.0)
	hp.set("HipTilt", 0.0)
	hp.set("NeckPitch", 22.0)
	skel.add_child(hp)
	if clip.begins_with("him/"): hp.set("Native", 1.0)
	weapon(skel, env("WEAPON", ""))

func dress(h):
	var skel: Skeleton3D = h.find_children("*", "Skeleton3D", true, false)[0]
	for mi in h.find_children("*", "MeshInstance3D", true, false):
		for s in mi.mesh.get_surface_count():
			var src = mi.mesh.surface_get_material(s)
			var part = String(src.resource_name)
			if part == "eyes":
				var e = ShaderMaterial.new()
				e.shader = load("res://shaders/heroine_eye.gdshader")
				e.set_shader_parameter("eye", load("res://art/people/head_tex/heroine_eye.png"))
				e.set_shader_parameter("iris", load("res://art/people/head_tex/heroine_iris.png"))
				mi.set_surface_override_material(s, e)
			elif part in ["brows", "lashes"]:
				var m = src.duplicate()
				m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
				m.alpha_scissor_threshold = 0.35
				m.cull_mode = BaseMaterial3D.CULL_DISABLED
				m.albedo_color = Color("#8f2d14").darkened(0.45) if part == "brows" else Color(0.12, 0.08, 0.07)
				if part == "lashes": m.albedo_texture = load("res://art/people/head_tex/heroine_lashes.png")
				mi.set_surface_override_material(s, m)
			elif part in ["teeth", "tongue"]:
				pass
			elif env("SKINDBG", "") == "uv":
				# Her UVs as colour (red, green; blue where seen from behind),
				# drawn linear: a pixel read back finds the face under it.
				var um = ShaderMaterial.new()
				um.shader = Shader.new()
				um.shader.code = "shader_type spatial; render_mode unshaded, cull_disabled;
void fragment() { ALBEDO = vec3(UV.x, UV.y, FRONT_FACING ? 0.0 : 1.0); }"
				mi.set_surface_override_material(s, um)
			elif env("SKINDBG", "") == "faces":
				# What a see-through spot is: red where a face is seen from
				# behind (folded or wound the wrong way), blue where a face
				# seen from the front has a normal turned away, else grey.
				var dm = ShaderMaterial.new()
				dm.shader = Shader.new()
				dm.shader.code = "shader_type spatial; render_mode unshaded, cull_disabled;\nvoid fragment() { float f = clamp(NORMAL.z, 0.0, 1.0); ALBEDO = !FRONT_FACING ? vec3(1.0, 0.0, 0.0) : (NORMAL.z < 0.0 ? vec3(0.0, 0.2, 1.0) : vec3(0.25 + 0.6 * f)); }"
				mi.set_surface_override_material(s, dm)
			else:
				var sk = ShaderMaterial.new()
				sk.shader = load("res://shaders/heroine_skin.gdshader")
				if env("SKINDBG", "") == "cull":
					# her skin drawn from both sides: a hole stays a hole
					var sh = Shader.new()
					sh.code = sk.shader.code.replace("render_mode sss_mode_skin;", "render_mode sss_mode_skin, cull_disabled;")
					sk.shader = sh
				sk.set_shader_parameter("paint", src.albedo_texture)
				sk.set_shader_parameter("pores", load("res://art/people/skin_pores.png"))
				sk.set_shader_parameter("pore_scale", 50.0)
				# (OUTFITSHADER=1: her skin under the outfit tucked in, as People.TuckSkin has it)
				if env("OUTFITSHADER", "") != "" and mi.mesh.surface_get_format(s) & Mesh.ARRAY_FORMAT_COLOR:
					sk.set_shader_parameter("tuck_channel", ["warden", "arcanist", "reaver", "ranger"].find(env("OUTFIT", "warden")))
				mi.set_surface_override_material(s, sk)
	var outfit = env("OUTFIT", "warden")
	if outfit != "none":
		var o = people("heroine_outfit_%s.gltf" % outfit)
		var os_ = o.find_children("*", "Skeleton3D", true, false)[0]
		for mi in os_.get_children():
			if mi is MeshInstance3D and String(mi.name).begins_with(outfit + "_"):
				os_.remove_child(mi)
				mi.owner = null
				skel.add_child(mi)
				mi.skeleton = NodePath("..")
				if env("OUTFITSHADER", "") != "":
					game_outfit(mi)
		o.free()
	var style = env("HAIR", "ponytail")
	if style != "none":
		var hs = load("res://art/people/heroine_hair_%s.gltf" % style).instantiate()
		var hsk = hs.find_children("*", "Skeleton3D", true, false)[0]
		for mi in hsk.get_children():
			if mi is MeshInstance3D:
				hsk.remove_child(mi)
				mi.owner = null
				skel.add_child(mi)
				mi.skeleton = NodePath("..")
				for s in mi.mesh.get_surface_count():
					var m = ShaderMaterial.new()
					m.shader = load("res://shaders/heroine_hair.gdshader")
					m.set_shader_parameter("strands", mi.mesh.surface_get_material(s).albedo_texture)
					m.set_shader_parameter("colour", Color("#8f2d14"))
					m.set_shader_parameter("cap", mi.mesh.surface_get_material(s).resource_name == "hair_cap")
					m.set_shader_parameter("tie", mi.mesh.surface_get_material(s).resource_name == "hair_tie")
					mi.set_surface_override_material(s, m)
				var sw = load("res://src/Actors/HairSway.cs").new()
				sw.Style = style
				mi.add_child(sw)
		hs.free()
	if env("NOHERPOSE", "") == "":
		var hp = load("res://src/Actors/HerPose.cs").new()
		skel.add_child(hp)
		if clip.begins_with("her/") or clip.ends_with(".json"): hp.set("Native", 1.0)
	skel.add_child(load("res://src/Actors/HerJiggle.cs").new())
	weapon(skel, env("WEAPON", ""))

# What she holds: the real pieces, from tools/anim/data/arms_local.json (the
# ArmsDump output; vertices already in the bone's space, mount included), so
# each hangs under a BoneAttachment3D with an identity mount.
const PIECES = {"sword": ["chevalier_sword@hand_r"], "sword+shield": ["chevalier_sword@hand_r", "shield_round@lowerarm_l"],
	"shield": ["shield_round@lowerarm_l"], "axe": ["viking_axe@hand_r"], "axes": ["viking_axe@hand_r", "viking_axe@hand_l"],
	"daggers": ["daggers@hand_r", "dagger_b@hand_l"], "staff": ["mage_staff@hand_r"], "wand": ["wand@hand_r"],
	"crossbow": ["crossbow@hand_r"]}

func weapon(skel, kind):
	if kind == "": return
	if kind == "flask":
		flask(skel)
		return
	var f = FileAccess.open(ProjectSettings.globalize_path("res://") + "../tools/anim/data/arms_local.json", FileAccess.READ)
	if f == null:
		print("WEAPON: arms_local.json missing")
		return
	var data = JSON.parse_string(f.get_as_text())
	var steel = StandardMaterial3D.new()
	steel.albedo_color = Color(0.75, 0.77, 0.8)
	steel.metallic = 0.8
	steel.roughness = 0.3
	var wood = StandardMaterial3D.new()
	wood.albedo_color = Color(0.35, 0.22, 0.12)
	# SHEATH=1: the pieces at their sockets, mounted by the game's code (Arms.HoldSheathed: the sword in its
	# scabbard, the worn outfit's clearance) instead of the hands; one with no socket stays in hand.
	var sheathe = env("SHEATH", "") != ""
	# GAMEMAT=1: the held pieces as the game draws them (Arms.Hold's mount, the asset's own materials).
	var gamemat = env("GAMEMAT", "") != ""
	var sr = load("res://tools_scenes/SheathedReview.cs").new() if (sheathe or gamemat) else null
	var calling = "" if env("OUTFIT", "none") == "none" else env("OUTFIT", "none")
	for key in PIECES.get(kind, []):
		# (The game's own piece and socket: Arms.HoldSheathed, through SheathedReview.cs.)
		if sheathe and sr.Mount(skel, key.split("@")[0], key.ends_with("@hand_l"), calling):
			continue
		if gamemat:
			sr.Held(skel, key.split("@")[0], key.split("@")[1])
			continue
		if not data.has(key):
			print("WEAPON: no piece ", key)
			continue
		var piece = data[key]
		var bone = key.split("@")[1]
		var verts = PackedVector3Array()
		for v in piece["v"]:
			verts.append(Vector3(v[0], v[1], v[2]))
		var idx = PackedInt32Array()
		for t in piece["t"]:
			idx.append(int(t[0]))
			idx.append(int(t[1]))
			idx.append(int(t[2]))
		var arrays = []
		arrays.resize(Mesh.ARRAY_MAX)
		arrays[Mesh.ARRAY_VERTEX] = verts
		arrays[Mesh.ARRAY_INDEX] = idx
		var am = ArrayMesh.new()
		am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
		var st = SurfaceTool.new()
		st.create_from(am, 0)
		st.generate_normals()
		var mesh = st.commit()
		var mat = steel
		if key.begins_with("shield") or key.begins_with("mage_staff") or key.begins_with("wand") or key.begins_with("crossbow"):
			mat = wood
		mesh.surface_set_material(0, mat)
		var at = BoneAttachment3D.new()
		at.bone_name = bone
		skel.add_child(at)
		var mi = MeshInstance3D.new()
		mi.mesh = mesh
		at.add_child(mi)

# A flat pewter flask in the right hand, as Arms.Hold would mount one: its
# body round the grip (13 cm tall, 10 wide, 4.5 thin across the palm), the
# neck's mouth 9 cm up out of the thumb side.
func flask(skel):
	var at = BoneAttachment3D.new()
	at.bone_name = "hand_r"
	skel.add_child(at)
	var mount = Node3D.new()
	var x = Vector3(0, 1, 0)
	var y = Vector3(0, 0, 1)
	mount.basis = Basis(x, y, x.cross(y))
	mount.position = Vector3(-0.025, 0.075, 0)
	at.add_child(mount)
	var pewter = StandardMaterial3D.new()
	pewter.albedo_color = Color(0.56, 0.58, 0.59)
	pewter.metallic = 0.85
	pewter.roughness = 0.4
	var body = MeshInstance3D.new()
	var bm = CylinderMesh.new()
	bm.top_radius = 0.05
	bm.bottom_radius = 0.05
	bm.height = 0.13
	bm.material = pewter
	body.mesh = bm
	body.scale = Vector3(1, 1, 0.45)
	mount.add_child(body)
	var neck = MeshInstance3D.new()
	var nm = CylinderMesh.new()
	nm.top_radius = 0.012
	nm.bottom_radius = 0.016
	nm.height = 0.03
	nm.material = pewter
	neck.mesh = nm
	neck.position = Vector3(0, 0.075, 0)
	mount.add_child(neck)

func stage(root):
	# A checked floor: squares of half a metre, so a sliding foot shows.
	var floor = MeshInstance3D.new()
	var pm = PlaneMesh.new()
	pm.size = Vector2(400, 400)
	var fm = ShaderMaterial.new()
	var sh = Shader.new()
	sh.code = "shader_type spatial;\nvoid fragment(){ vec3 w = (INV_VIEW_MATRIX * vec4(VERTEX,1.0)).xyz; vec2 c = floor(w.xz*2.0); float k = mod(c.x+c.y,2.0); ALBEDO = mix(vec3(0.20,0.21,0.23), vec3(0.30,0.31,0.33), k); vec2 g = abs(fract(w.xz)-0.5); if (min(g.x,g.y) > 0.49) ALBEDO = vec3(0.5,0.4,0.25); ROUGHNESS = 0.9; }"
	fm.shader = sh
	pm.material = fm
	floor.mesh = pm
	root.add_child(floor)
	cam = Camera3D.new()
	cam.fov = float(env("FOV", "32"))
	root.add_child(cam)
	cam.current = true
	var env_ = WorldEnvironment.new()
	var e = Environment.new()
	e.background_mode = Environment.BG_COLOR
	e.background_color = Color(0.36, 0.37, 0.4)
	e.ambient_light_color = Color(0.6, 0.6, 0.65)
	e.ambient_light_energy = 0.7
	e.tonemap_mode = Environment.TONE_MAPPER_AGX
	if env("SKINDBG", "") == "uv":
		e.tonemap_mode = Environment.TONE_MAPPER_LINEAR
	env_.environment = e
	root.add_child(env_)
	var key = DirectionalLight3D.new()
	key.rotation_degrees = Vector3(-50, 35, 0)
	key.light_energy = 1.5
	key.shadow_enabled = true
	root.add_child(key)
	var rim = DirectionalLight3D.new()
	rim.rotation_degrees = Vector3(-20, 200, 0)
	rim.light_energy = 0.9
	root.add_child(rim)
	place_camera()

func place_camera():
	var c = her.position + Vector3(0, float(env("LOOKY", "0.95")), 0)
	# LOOK=bone: the camera on one of her bones (a hand, her head), ZOOM nearer.
	var look = env("LOOK", "")
	if look != "":
		var sk: Skeleton3D = her.find_children("*", "Skeleton3D", true, false)[0]
		c = sk.global_transform * sk.get_bone_global_pose(sk.find_bone(look)).origin
	var off = {"front": Vector3(0, 0.2, 4.6), "back": Vector3(0, 0.2, -4.6), "side": Vector3(4.6, 0.2, 0), "left": Vector3(-4.6, 0.2, 0),
		"three": Vector3(3.2, 0.6, 3.4), "rthree": Vector3(-3.2, 0.6, 3.4), "top": Vector3(0.01, 6.0, 0.6), "game": Vector3(0, 9.0, 4.4),
		# The game's own cameras (FollowCamera: 56 degrees at 23 m by day,
		# 64 at 31 m in an arena; Fov 34 on a 1080-line screen), the cell
		# cut from that screen at its true size. YAW turns her under it.
		"day": Vector3(0, sin(deg_to_rad(56)) * 23, cos(deg_to_rad(56)) * 23),
		"arena": Vector3(0, sin(deg_to_rad(64)) * 31, cos(deg_to_rad(64)) * 31)}[view]
	# OFF=x,y,z: the camera at this offset from the look point (her space,
	# metres), LOOKOFF=x,y,z the look point moved: a cinematic's own set-up.
	if env("OFF", "") != "":
		var o = env("OFF", "").split_floats(",")
		off = Vector3(o[0], o[1], o[2])
	if view == "game": cam.fov = 26
	if view in ["day", "arena"]:
		cam.fov = rad_to_deg(2 * atan(tan(deg_to_rad(17)) * vp.size.y / 1080.0))
		her.rotation_degrees.y = float(env("YAW", "0"))
		c = her.position + Vector3(0, 0.9, 0)
	# (After the game cameras' own look point, so LOOKOFF frames a body
	# that has moved off its spot, a fall's end, under them too.)
	if env("LOOKOFF", "") != "":
		var lo = env("LOOKOFF", "").split_floats(",")
		c += Vector3(lo[0], lo[1], lo[2])
	cam.look_at_from_position(c + off / float(env("ZOOM", "1")), c)

func _process(delta):
	her.position += her.basis.z.normalized() * speed * TICK
	# FIXCAM=1: the camera set up on the clip's first frame and left there,
	# as a cinematic's camera is set on its marks when the shot begins.
	if env("FIXCAM", "") == "" or frame <= warm:
		place_camera()
	frame += 1
	if frame <= warm:
		if frame == warm:
			# The first shots after warming: from the clip's start (not
			# advanced this tick, so the start itself is drawn and photographed).
			ap.seek(start, true)
			her.position = Vector3.ZERO
			# (her hair hung afresh from this pose: the seek back was a jump, and it flung her hair)
			for h in her.find_children("HairSway", "", true, false): h.call("Settle")
		else:
			play_on(delta)
		return false
	var k = frame - warm - 1
	if tree != null and k == int(float(env("OVERAT", "0")) * 30):
		tree.set("parameters/shot/request", AnimationNodeOneShot.ONE_SHOT_REQUEST_FIRE)
	if gestures != null and k == int(float(env("GESTUREAT", "0")) * 30):
		gestures.Play(ap.get_animation(env("GESTURE", "")), 1.0, env("HOLD", "") != "")
	if k % step == 0:
		# DEBUG=bone[,bone...]: print where each bone is and which way its axes point.
		if env("DEBUG", "") != "":
			var sk: Skeleton3D = her.find_children("*", "Skeleton3D", true, false)[0]
			for bn in env("DEBUG", "").split(","):
				var gp = sk.get_bone_global_pose(sk.find_bone(bn))
				print("DBG %d t=%.3f %s pos=%s x=%s y=%s z=%s" % [k, ap.current_animation_position, bn, gp.origin, gp.basis.x, gp.basis.y, gp.basis.z])
		var img = vp.get_texture().get_image()
		if env("HAIRCLEAR", "") != "": hair_clear(k)
		shots.append(img)
		if env("FULL", "") != "": img.save_png(out.replace(".png", "_%02d.png" % shots.size()))
	if shots.size() >= nframes:
		sheet()
		quit()
	# The photograph above is the frame drawn last tick: only now does the
	# clip move on to the next (until 14 Oct the player moved on before the
	# first photograph, so every cell showed one frame later than its number).
	play_on(delta)
	return false

# Exactly a frame: the engine's tick wanders (0.025-0.042 s seen under
# --fixed-fps 30, 14 Oct), which moved cells off their frames by up to a quarter.
const TICK = 1.0 / 30.0
func play_on(_delta):
	if tree != null: tree.advance(TICK)
	else: ap.advance(TICK)

func sheet():
	var w = shots[0].get_width()
	var h = shots[0].get_height()
	var cols = int(env("COLS", str(min(8, nframes))))
	var rows = int(ceil(shots.size() / float(cols)))
	var img = Image.create(w * cols, h * rows, false, shots[0].get_format())
	for i in shots.size():
		img.blit_rect(shots[i], Rect2i(0, 0, w, h), Vector2i((i % cols) * w, (i / cols) * h))
	img.save_png(out)
	print("SHEET %s %d frames" % [out, shots.size()])

# HAIRCLEAR=1: how near each hair chain comes to her posed skin and outfit, and
# how far its points jump between photographed frames in her neck's frame.
var hc_prev = {}
var hc_named = false
func hair_clear(k):
	var skel: Skeleton3D = her.find_children("*", "Skeleton3D", true, false)[0]
	var nb = skel.find_bone("neck_01")
	var N: Transform3D = skel.global_transform * skel.get_bone_global_pose(nb)
	var skip = ["hair", "lash", "brow", "eye", "teeth", "tongue"]
	var meshes = []
	for m in her.find_children("*", "MeshInstance3D", true, false):
		if m.skin == null and m.get_node_or_null(m.skeleton) == null: continue
		var low = String(m.name).to_lower()
		var bad = false
		for s in skip:
			if low.contains(s): bad = true
		if not bad and m.mesh != null: meshes.append(m)
	if not hc_named:
		hc_named = true
		var names = []
		for m in meshes: names.append(String(m.name))
		print("HAIRCLEAR meshes: ", ", ".join(names))
	for hn in her.find_children("HairSway", "", true, false):
		var cw = hn.get("ChainWorld")
		if cw == null or cw.size() != 8: continue
		var p0: Vector3 = cw[0]
		var vs = []   # [pos, normal, mesh name]
		for m in meshes:
			var bm: ArrayMesh = m.bake_mesh_from_current_skeleton_pose()
			if bm == null: continue
			var gt: Transform3D = m.global_transform
			var nb3 = gt.basis.inverse().transposed()
			for si in bm.get_surface_count():
				var arr = bm.surface_get_arrays(si)
				var pv = arr[Mesh.ARRAY_VERTEX]
				var nv = arr[Mesh.ARRAY_NORMAL]
				if pv == null or nv == null: continue
				for i in pv.size():
					var g = gt * pv[i]
					if g.distance_to(p0) <= 0.45:
						vs.append([g, (nb3 * nv[i]).normalized(), String(m.name)])
		# HAIRMESH=folder: these posed vertices (position, normal, mesh) saved per
		# frame, so the clearance can be replayed offline against a changed chain.
		if env("HAIRMESH", "") != "":
			var f = FileAccess.open("%s/k%02d.bin" % [env("HAIRMESH", ""), k], FileAccess.WRITE)
			var names = []
			for m in meshes: names.append(String(m.name))
			for v in vs:
				for c in [v[0].x, v[0].y, v[0].z, v[1].x, v[1].y, v[1].z, float(names.find(v[2]))]: f.store_float(c)
			f.close()
			if k == 0: print("HAIRMESH names: ", ",".join(names))
		var worst = INF
		var wseg = 0
		var wmesh = ""
		var wdist = 0.0
		var segmin = []
		for i in range(1, 8):
			var smin = INF
			for j in 5:
				var s: Vector3 = cw[i - 1].lerp(cw[i], j / 4.0)
				var bd = INF
				var bv = null
				for v in vs:
					var d = s.distance_squared_to(v[0])
					if d < bd:
						bd = d
						bv = v
				if bv == null: continue
				var sg = (s - bv[0]).dot(bv[1]) * 100.0
				smin = min(smin, sg)
				if sg < worst:
					worst = sg
					wseg = i
					wmesh = bv[2]
					wdist = sqrt(bd) * 100.0
			segmin.append(smin)
		var sm = ""
		for v in segmin: sm += " %.1f" % v
		print("HAIRCLEAR k=%d worst seg=%d mesh=%s signed=%.1f dist=%.1f" % [k, wseg, wmesh, worst, wdist])
		print("HAIRCLEAR k=%d segs%s" % [k, sm])
		var inv = N.affine_inverse()
		var loc = []
		for i in 8: loc.append(inv * Vector3(cw[i]))
		var key = hn.get_instance_id()
		if hc_prev.has(key):
			var mx = 0.0
			var mp = 1
			for i in range(1, 8):
				var d = loc[i].distance_to(hc_prev[key][i]) * 100.0
				if d > mx:
					mx = d
					mp = i
			print("HAIRMOVE k=%d max=%.1f point=%d" % [k, mx, mp])
		hc_prev[key] = loc
