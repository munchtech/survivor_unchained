extends SceneTree
# Clips judged as an animator judges them: the heroine played through a clip
# at a fixed 30 frames a second, every frame (or every STEP-th) photographed
# and tiled into one contact sheet, numbered, over a checked floor so a foot
# that slides shows. Run with --fixed-fps 30 so time is exact.
#
#   godot --path godot --fixed-fps 30 --resolution 420x560 -s res://tools_scenes/anim_review.gd -- <clip> <out.png>
#
# The clip is a name from her library (res://art/anim/heroine.res, as
# "her/<name>") or from the Universal Animation Libraries ("ual/<name>").
# Options by environment:
#   VIEW=front|side|back|three|top|game   where the camera stands (game: the arena's 64 degrees)
#   FRAMES=n  STEP=k  START=s              n cells, every k-th frame, from s seconds in
#   COLS=c                                 cells to a row
#   SPEED=m/s                              carried forward at this speed (in metres of the world), camera following
#   PLAY=x                                 playback speed
#   OUTFIT=warden|arcanist|reaver|ranger   her outfit; HAIR=style; WEAPON=sword|staff|bow|axe|axes|daggers|wand
#   MODEL=female|male                      a townsfolk body (the kit's) instead of hers, in PARTS (kit
#                                          outfit parts, comma-separated); clips "folk/<name>"
#   MODEL=hero                             the hero, with his clips ("him/<name>", art/anim/hero.res)
#   NOHERPOSE=1                            without her corrective pose layer
#   GESTURE=her/nod GESTUREAT=s            a gesture laid over the clip (Gestures.cs) s seconds in
#   FULL=1                                 save every frame as its own picture too (out_NN.png)
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
		her = load("res://art/people/heroine.glb").instantiate()
	root.add_child(her)
	her.scale = Vector3.ONE * 1.04
	if model == "hero": hero(her)
	elif model != "": kit(her, env("PARTS", ""))
	else: dress(her)
	ap = AnimationPlayer.new()
	her.add_child(ap)
	ap.root_node = NodePath("..")
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
	stage(root)

var tree: AnimationTree
var gestures = null

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

func env(k, d):
	var v = OS.get_environment(k)
	return v if v != "" else d

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
			else:
				var sk = ShaderMaterial.new()
				sk.shader = load("res://shaders/heroine_skin.gdshader")
				sk.set_shader_parameter("paint", src.albedo_texture)
				sk.set_shader_parameter("pores", load("res://art/people/skin_pores.png"))
				sk.set_shader_parameter("pore_scale", 30.0)
				mi.set_surface_override_material(s, sk)
	var outfit = env("OUTFIT", "warden")
	if outfit != "none":
		var o = load("res://art/people/heroine_outfit_%s.gltf" % outfit).instantiate()
		var os_ = o.find_children("*", "Skeleton3D", true, false)[0]
		for mi in os_.get_children():
			if mi is MeshInstance3D and String(mi.name).begins_with(outfit + "_"):
				os_.remove_child(mi)
				mi.owner = null
				skel.add_child(mi)
				mi.skeleton = NodePath("..")
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
		if clip.begins_with("her/"): hp.set("Native", 1.0)
	skel.add_child(load("res://src/Actors/HerJiggle.cs").new())
	weapon(skel, env("WEAPON", ""))

# Stand-ins for what she holds, mounted as Arms.Hold mounts them: in the
# hand's space the fingers run +Y and the thumb side is +Z, and a held shaft
# leaves the fist out of the thumb side.
func weapon(skel, kind):
	if kind == "": return
	var steel = StandardMaterial3D.new()
	steel.albedo_color = Color(0.75, 0.77, 0.8)
	steel.metallic = 0.8
	steel.roughness = 0.3
	var wood = StandardMaterial3D.new()
	wood.albedo_color = Color(0.35, 0.22, 0.12)
	if kind.begins_with("sword+shield") or kind == "shield":
		# A buckler on the left forearm, as Arms.Hold mounts one: its face
		# along the mount's +Z.
		var fa = BoneAttachment3D.new()
		fa.bone_name = "lowerarm_l"
		skel.add_child(fa)
		var fm = Node3D.new()
		var fx = Vector3(0, 1, 0)
		var fy = Vector3(0, 0, -1)
		fm.basis = Basis(fx, fy, fx.cross(fy))
		fm.position = Vector3(0, 0.14, 0)
		fa.add_child(fm)
		var disc = MeshInstance3D.new()
		var cm = CylinderMesh.new()
		cm.top_radius = 0.3
		cm.bottom_radius = 0.3
		cm.height = 0.04
		var wood2 = StandardMaterial3D.new()
		wood2.albedo_color = Color(0.45, 0.3, 0.18)
		cm.material = wood2
		disc.mesh = cm
		disc.rotation_degrees = Vector3(90, 0, 0)
		disc.position = Vector3(0, 0, 0.05)
		fm.add_child(disc)
		if kind == "shield": return
		kind = "sword"
	var hands = {"sword": [["hand_r", 0.95, 0.05, steel]], "axe": [["hand_r", 0.8, 0.07, steel]],
		"axes": [["hand_r", 0.8, 0.07, steel], ["hand_l", 0.8, 0.07, steel]],
		"daggers": [["hand_r", 0.4, 0.03, steel], ["hand_l", 0.4, 0.03, steel]],
		"staff": [["hand_r", 1.75, 0.03, wood]], "wand": [["hand_r", 0.38, 0.015, wood]], "crossbow": [["hand_r", 0.85, 0.05, wood]]}
	for h in hands.get(kind, []):
		var at = BoneAttachment3D.new()
		at.bone_name = h[0]
		skel.add_child(at)
		var mount = Node3D.new()
		var x = Vector3(0, 1, 0)
		var y = Vector3(0, 0, 1)
		mount.basis = Basis(x, y, x.cross(y))
		mount.position = Vector3(-0.025, 0.075, 0)
		at.add_child(mount)
		var len = h[1]
		var grip = {"staff": 0.45, "crossbow": 0.3}.get(kind, 0.15)
		var m = MeshInstance3D.new()
		var bm = BoxMesh.new()
		bm.size = Vector3(h[2] * 1.6, len, h[2] * 0.4)
		bm.material = h[3]
		m.mesh = bm
		var w = Node3D.new()
		if kind == "crossbow":
			# Pistol-fashion, as Arms.Hold: the stock along the fingers.
			w.basis = Basis(Vector3(0, 0, 1), Vector3(1, 0, 0), Vector3(0, 1, 0))
			w.position = Vector3(0, 0.05, 0)
		mount.add_child(w)
		m.position = Vector3(0, len * (0.5 - grip), 0)
		w.add_child(m)

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
	if view == "game": cam.fov = 26
	if view in ["day", "arena"]:
		cam.fov = rad_to_deg(2 * atan(tan(deg_to_rad(17)) * vp.size.y / 1080.0))
		her.rotation_degrees.y = float(env("YAW", "0"))
		c = her.position + Vector3(0, 0.9, 0)
	cam.look_at_from_position(c + off / float(env("ZOOM", "1")), c)

func _process(delta):
	her.position += her.basis.z.normalized() * speed * delta
	place_camera()
	frame += 1
	if frame <= warm:
		if frame == warm:
			# The first shots after warming: from the clip's start.
			ap.seek(start, true)
			her.position = Vector3.ZERO
		return false
	var k = frame - warm - 1
	if tree != null and k == int(float(env("OVERAT", "0")) * 30):
		tree.set("parameters/shot/request", AnimationNodeOneShot.ONE_SHOT_REQUEST_FIRE)
	if gestures != null and k == int(float(env("GESTUREAT", "0")) * 30):
		gestures.Play(ap.get_animation(env("GESTURE", "")), 1.0, env("HOLD", "") != "")
	if k % step == 0:
		# DEBUG=bone: print where that bone is and which way its axes point.
		if env("DEBUG", "") != "":
			var sk: Skeleton3D = her.find_children("*", "Skeleton3D", true, false)[0]
			var gp = sk.get_bone_global_pose(sk.find_bone(env("DEBUG", "")))
			print("DBG %d t=%.3f pos=%s y=%s z=%s" % [k, ap.current_animation_position, gp.origin, gp.basis.y, gp.basis.z])
		var img = vp.get_texture().get_image()
		shots.append(img)
		if env("FULL", "") != "": img.save_png(out.replace(".png", "_%02d.png" % shots.size()))
	if shots.size() >= nframes:
		sheet()
		quit()
	return false

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
