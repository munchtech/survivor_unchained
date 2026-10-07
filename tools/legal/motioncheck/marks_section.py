# The MARKS part of the legal motion check's scene script, kept apart from make_motioncheck.py
# so the GDScript reads as GDScript. make_motioncheck.py appends GD below to the script.
#
# MARKS=1 draws two test codes on her skin, in the last lines of her skin shader's fragment
# (so they show wherever her skin is drawn, tucked skin included), unlit, under a linear
# tonemapper, so the colours read back exactly:
# - near a nipple (within 6 cm, measured in her rest pose): blue, with the distance in red
#   (red = 0.9 * d / 6 cm, linear). Any visible skin there says how far it is from the tip, so
#   count.py can give the margin between a cup's edge and the areola (2.2 cm: her texture's
#   pigment) as well as flag the areola itself;
# - the strip a garment must cover (the vulva's footprint, were one modelled): pure green.
#   The midline, 1.2 cm either side, from the perineum (2.3 cm behind the lowest point of her
#   crotch's underside) forward and up to just below the front of the mons. Skin facing
#   sideways (her inner thighs, which touch below it) is left out.
# - tucked skin (the outfit's channel of her vertex colours, which her skin shader pushes in
#   under a garment) that comes into view: near a nipple, the blue code with green at exactly
#   0.5 once the tuck is past half (the edge ring's 1/3 is not counted); elsewhere, cyan, paler
#   the shallower the tuck (red = 0.9 * (1 - tuck)). Seen tucked skin is a dent or a gap.
# Each areola is found from her paint (the skin painted darker than its breast's own, on the
# breast's front half), and the distance is measured from its centre; the posed landmark is
# her skin nearest that centre. Without a paint to read, the sharpest bump on the front half of
# each breast stands in (welded neighbours, so UV seams can't fake one), with a warning. The
# landmarks come from her untrimmed body. Calibrate (run.sh calib) after any body change: the
# log says whether the two areolas are mirror images.

GD = r'''
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

# Where a function's body ends in shader code: the brace closing the first one opened after
# `head` (comments skipped).
func _body_end(code: String, head: int) -> int:
	var depth = 0
	var i = code.find("{", head)
	while i >= 0 and i < code.length():
		if code.substr(i, 2) == "//":
			i = code.find("\n", i)
			continue
		if code.substr(i, 2) == "/*":
			i = code.find("*/", i) + 2
			continue
		var ch = code[i]
		if ch == "{":
			depth += 1
		elif ch == "}":
			depth -= 1
			if depth == 0: return i
		i += 1
	return -1

# DUMP=1: at each picture, her posed body and outfit as drawn this frame, for a look at a
# flagged frame in three dimensions (tools/legal/motioncheck: posed.py reads them). Per
# mesh: positions and normals (skinned, in the world), its triangles once, and for her body
# its codes (UV2: areola distance / 6 cm, strip) and her tuck (the outfit's vertex colour).
var _dumped_tris = {}
func dump_posed(path: String):
	var sk = follow_skel
	var head = {"cams": [], "meshes": []}
	for vi in view_cams.size():
		var c: Camera3D = view_cams[vi]
		var t = c.global_transform
		head["cams"].append({"name": view_names[vi], "fov": c.fov, "size": [c.get_viewport().get_visible_rect().size.x, c.get_viewport().get_visible_rect().size.y],
			"basis": [t.basis.x.x, t.basis.x.y, t.basis.x.z, t.basis.y.x, t.basis.y.y, t.basis.y.z, t.basis.z.x, t.basis.z.y, t.basis.z.z],
			"origin": [t.origin.x, t.origin.y, t.origin.z]})
	var f = FileAccess.open(path + ".bin", FileAccess.WRITE)
	var off = 0
	for mi in sk.get_children():
		if not (mi is MeshInstance3D) or not mi.visible: continue
		var baked: ArrayMesh = mi.bake_mesh_from_current_skeleton_pose()
		var g = mi.global_transform
		for si in baked.get_surface_count():
			var arr = baked.surface_get_arrays(si)
			var vs: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
			var ns: PackedVector3Array = arr[Mesh.ARRAY_NORMAL]
			var wv = PackedVector3Array()
			wv.resize(vs.size())
			var wn = PackedVector3Array()
			wn.resize(ns.size())
			for i in vs.size():
				wv[i] = g * vs[i]
				wn[i] = (g.basis * ns[i]).normalized()
			var e = {"name": String(mi.name), "surface": si, "verts": vs.size(), "off": off}
			f.store_buffer(wv.to_byte_array()); off += vs.size() * 12
			f.store_buffer(wn.to_byte_array()); off += vs.size() * 12
			var src = mi.mesh.surface_get_arrays(si)
			if src[Mesh.ARRAY_TEX_UV2] != null and src[Mesh.ARRAY_TEX_UV2].size() == vs.size():
				f.store_buffer(src[Mesh.ARRAY_TEX_UV2].to_byte_array()); e["uv2"] = off; off += vs.size() * 8
			if src[Mesh.ARRAY_COLOR] != null and src[Mesh.ARRAY_COLOR].size() == vs.size():
				f.store_buffer(src[Mesh.ARRAY_COLOR].to_byte_array()); e["color"] = off; off += vs.size() * 16
			var key = String(mi.name) + "#" + str(si)
			if not _dumped_tris.has(key):
				var tf = FileAccess.open(path.get_base_dir().path_join("tris_" + key.replace("#", "_") + ".bin"), FileAccess.WRITE)
				tf.store_buffer(PackedInt32Array(arr[Mesh.ARRAY_INDEX]).to_byte_array())
				tf.close()
				_dumped_tris[key] = true
			head["meshes"].append(e)
	f.close()
	var hf = FileAccess.open(path + ".json", FileAccess.WRITE)
	hf.store_string(JSON.stringify(head))
	hf.close()

var _tinted: Shader
func tinted_skin(base: Shader) -> Shader:
	if _tinted != null: return _tinted
	var code = base.code
	var flat = "ALBEDO = vec3(0.0); SPECULAR = 0.0; ROUGHNESS = 1.0; METALLIC = 0.0; RIM = 0.0; SSS_STRENGTH = 0.0; BACKLIGHT = vec3(0.0); legal_flat = 1.0; "
	# (the outfit's channel of her vertex colours, as her shader's tuck reads it; -1: none)
	var head = code.find("void fragment()")
	code = code.substr(0, head) + "uniform int legal_tuck_ch = -1;\nvarying float legal_flat;\n" + code.substr(head)
	# The codes go at the end of fragment() itself, not of the file: her shader has its own
	# light() after it (face v10), where COLOR is unknown and the codes never compiled.
	head = code.find("void fragment()")
	var end = _body_end(code, head)
	code = code.substr(0, end) \
		+ "\t// legal motion check (test codes, never in the game): see tools/legal/motioncheck\n" \
		+ "\tlegal_flat = 0.0;\n" \
		+ "\tfloat legal_th = legal_tuck_ch == 0 ? COLOR.r : legal_tuck_ch == 1 ? COLOR.g : legal_tuck_ch == 2 ? COLOR.b : legal_tuck_ch == 3 ? COLOR.a : 0.0;\n" \
		+ "\tif (UV2.y > 0.5) { " + flat + "EMISSION = vec3(0.0, 1.0, 0.0); }\n" \
		+ "\telse if (UV2.x < 0.995) { " + flat + "EMISSION = vec3(UV2.x * 0.9, legal_th > 0.5 ? 0.5 : 0.0, 1.0); }\n" \
		+ "\telse if (legal_th > 0.02) { " + flat + "EMISSION = vec3((1.0 - legal_th) * 0.9, 1.0, 1.0); }\n" \
		+ code.substr(end)
	# Her own light() adds a sheen from what fragment() had before the codes (a varying), so
	# no lamp may light a coded pixel: the codes are read back exactly, as emission alone.
	var lh = code.find("void light()")
	if lh >= 0:
		var lend = _body_end(code, lh)
		code = code.substr(0, lend) \
			+ "\tif (legal_flat > 0.5) { DIFFUSE_LIGHT = vec3(0.0); SPECULAR_LIGHT = vec3(0.0); }\n" \
			+ code.substr(lend)
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
		# Each areola as her paint has it, which is what must be covered: on each breast's front
		# half, the skin painted darker than that breast's own (under 0.8 of its median), and
		# its centre. (The sharpest bump, all this once was, took a lump low on her right breast
		# for the nipple on the v10/v11 body, 6 cm off, and her real areola went uncoded; on her
		# left it took a point 9 mm off the areola's middle, and a disc round that missed pigment.)
		var paint: Image = null
		var ov = mi.get_surface_override_material(si)
		if ov is ShaderMaterial and ov.get_shader_parameter("paint") is Texture2D:
			paint = ov.get_shader_parameter("paint").get_image()
			if paint != null and paint.is_compressed(): paint.decompress()
		var uvs = arr[Mesh.ARRAY_TEX_UV]
		var pig = {}
		if paint != null and uvs.size() == vs.size():
			var pw = paint.get_width()
			var ph = paint.get_height()
			var lum = {}
			for i in vs.size():
				var b = owner[i]
				if b < 0 or along[i] < 0.5 * reach[b]: continue
				var c = paint.get_pixel(clampi(int(uvs[i].x * pw), 0, pw - 1), clampi(int(uvs[i].y * ph), 0, ph - 1))
				if not lum.has(b): lum[b] = []
				lum[b].append([i, 0.3 * c.r + 0.59 * c.g + 0.11 * c.b])
			for b in lum:
				var ls = []
				for e in lum[b]: ls.append(e[1])
				ls.sort()
				var med = ls[ls.size() / 2]
				var acc = Vector3.ZERO
				var n = 0
				for e in lum[b]:
					if e[1] < 0.8 * med:
						acc += vs[e[0]]
						n += 1
				if n >= 8:
					pig[b] = acc / n
					print("legal marks: ", breast_name[b], " areola from her paint: ", n, " vertices, centre ", pig[b])
		var best = {}
		var bests = {}
		var bidx = {}
		for i in vs.size():
			var b = owner[i]
			if b < 0 or along[i] < 0.5 * reach[b]: continue
			var score = 0.0
			if pig.has(b):
				# (its landmark: her skin nearest the areola's centre)
				score = -vs[i].distance_to(pig[b])
			else:
				var kk = key.call(vs[i])
				if not ncount.has(kk) or ncount[kk] < 3: continue
				score = -(nsum[kk] / float(ncount[kk]) - vs[i]).dot(ns[i].normalized())
			if not bests.has(b) or score > bests[b]:
				bests[b] = score
				best[b] = vs[i]
				bidx[b] = i
		if pig.size() == 2:
			var cs = pig.values()
			print("legal marks: areolas level within %.1f cm, out from her middle alike within %.1f cm" % [abs(cs[0].y - cs[1].y) * 100.0, abs(abs(cs[0].x) - abs(cs[1].x)) * 100.0])
			if abs(cs[0].y - cs[1].y) > 0.015 or abs(abs(cs[0].x) - abs(cs[1].x)) > 0.015:
				print("legal marks: WARNING the two areolas are not mirror images: check the landmarks before trusting a count")
		elif best.size() > 0:
			print("legal marks: WARNING no paint read: the nipples are guessed as the sharpest bumps")
		for b in best:
			tips.append(pig[b] if pig.has(b) else best[b])
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
'''
