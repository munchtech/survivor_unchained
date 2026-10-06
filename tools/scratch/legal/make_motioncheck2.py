"""Builds motioncheck2.gd from motioncheck.gd (the legal motion check):
- SPREAD=1: the clip loops in memory (nothing saved) and the FRAMES pictures are spread
  evenly over one pass of it, from 1 s in, so a short swing is seen whole with its jiggle warmed;
- VIEWS="name:deg,height,dist,targety:fov;...": several cameras in one run (the first is the
  window's, the rest SubViewports sharing its world); pictures are out_<name>_NN.png;
- FOLLOW=1: every camera keeps its offset from her hips, for clips that travel (dash, leap, vault).
Written as UTF-8 without a byte-order mark (Godot refuses a BOM in GDScript)."""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, 'motioncheck.gd'), encoding='utf-8-sig').read()


def swap(a, b):
    global src
    assert src.count(a) == 1, a
    src = src.replace(a, b)


swap('var players = []\n',
     'var players = []\n'
     'var clip_len = 0.0\n'
     'var follow_skel: Skeleton3D\n'
     'var follow_from = Vector3.ZERO\n'
     'var view_cams = []\n'
     'var view_from = []\n'
     'var view_names = []\n'
     'var view_ports = []\n')
swap('\t\tap.play(clips[i])\n',
     '\t\tif OS.get_environment("SPREAD") != "":\n'
     '\t\t\tvar anim = ap.get_animation(clips[i])\n'
     '\t\t\tanim.loop_mode = Animation.LOOP_LINEAR\n'
     '\t\t\tclip_len = max(clip_len, anim.length)\n'
     '\t\tap.play(clips[i])\n'
     '\t\tif follow_skel == null:\n'
     '\t\t\tvar sks = h.find_children("*", "Skeleton3D", true, false)\n'
     '\t\t\tif sks.size() > 0: follow_skel = sks[0]\n')
swap('\troot.add_child(rim)\n',
     '\troot.add_child(rim)\n'
     '\tvar views = OS.get_environment("VIEWS")\n'
     '\tif views != "":\n'
     '\t\tvar parts = views.split(";", false)\n'
     '\t\tfor vi in parts.size():\n'
     '\t\t\tvar p = parts[vi].split(":")\n'
     '\t\t\tvar o = p[1].split(",")\n'
     '\t\t\tvar c: Camera3D = cam\n'
     '\t\t\tvar port: Viewport = get_root()\n'
     '\t\t\tif vi > 0:\n'
     '\t\t\t\tvar sv = SubViewport.new()\n'
     '\t\t\t\tsv.size = Vector2i(960, 540)\n'
     '\t\t\t\tsv.msaa_3d = get_root().msaa_3d\n'
     '\t\t\t\tsv.render_target_update_mode = SubViewport.UPDATE_ALWAYS\n'
     '\t\t\t\troot.add_child(sv)\n'
     '\t\t\t\tc = Camera3D.new()\n'
     '\t\t\t\tsv.add_child(c)\n'
     '\t\t\t\tc.current = true\n'
     '\t\t\t\tport = sv\n'
     '\t\t\tvar a = deg_to_rad(float(o[0]))\n'
     '\t\t\tc.fov = float(p[2])\n'
     '\t\t\tc.look_at_from_position(Vector3(sin(a) * float(o[2]), float(o[1]), cos(a) * float(o[2])), Vector3(0, float(o[3]), 0))\n'
     '\t\t\tview_cams.append(c)\n'
     '\t\t\tview_from.append(c.global_position)\n'
     '\t\t\tview_names.append(p[0])\n'
     '\t\t\tview_ports.append(port)\n'
     '\telse:\n'
     '\t\tview_cams.append(cam)\n'
     '\t\tview_from.append(cam.global_position)\n'
     '\t\tview_names.append("")\n'
     '\t\tview_ports.append(get_root())\n')
swap('\t\tvar k = int((t - 1.0) * 15.0)\n',
     '\t\tvar step = 1.0 / 15.0\n'
     '\t\tif OS.get_environment("SPREAD") != "" and clip_len > 0.0: step = clip_len / float(int(frames))\n'
     '\t\tvar k = int((t - 1.0) / step)\n')
swap('\t\t\tget_root().get_texture().get_image().save_png(out.replace(".png", "_%02d.png" % k))\n',
     '\t\t\tfor vi in view_ports.size():\n'
     '\t\t\t\tvar tag = ("_" + view_names[vi]) if view_names[vi] != "" else ""\n'
     '\t\t\t\tview_ports[vi].get_texture().get_image().save_png(out.replace(".png", "%s_%02d.png" % [tag, k]))\n'
     '\t\t\t\tif follow_skel != null: save_landmarks(view_cams[vi], out.replace(".png", "%s_%02d.json" % [tag, k]))\n')
swap('\tt += delta\n',
     '\tt += delta\n'
     '\t# FOLLOW=1: every camera keeps its offset from her hips (taken at 0.5 s, once she has settled).\n'
     '\tif OS.get_environment("FOLLOW") != "" and follow_skel != null:\n'
     '\t\tvar hb = follow_skel.find_bone("pelvis")\n'
     '\t\tif hb < 0: hb = 0\n'
     '\t\tvar hp = follow_skel.global_transform * follow_skel.get_bone_global_pose(hb).origin\n'
     '\t\thp.y = 0.0\n'
     '\t\tif t < 0.5:\n'
     '\t\t\tfollow_from = hp\n'
     '\t\t\tfor vi in view_cams.size(): view_from[vi] = view_cams[vi].global_position\n'
     '\t\telse:\n'
     '\t\t\tfor vi in view_cams.size(): view_cams[vi].global_position = view_from[vi] + (hp - follow_from)\n')
# MARKS=1: her areolas tinted magenta and her genital area cyan, on her body mesh only (after
# the outfit's skin hiding, so hidden skin stays hidden), in a copy of her skin shader. Any
# magenta or cyan in a picture is skin the player could see there.
swap('\t\t# HAIR=<style> (heroine_hair_<style>.gltf; "none" for none), HAIRCOLOR=#rrggbb.\n',
     '\t\tif OS.get_environment("MARKS") != "":\n'
     '\t\t\tfor bm in skel.get_children():\n'
     '\t\t\t\tif bm is MeshInstance3D and not String(bm.name).contains(".") and not String(bm.name).contains("_") and bm.mesh.surface_get_format(0) & Mesh.ARRAY_FORMAT_COLOR:\n'
     '\t\t\t\t\tlegal_marks(bm)\n'
     '\t\t# HAIR=<style> (heroine_hair_<style>.gltf; "none" for none), HAIRCOLOR=#rrggbb.\n')
src += '''
# Where her landmarks fall on screen in a picture (for count.py to tell an areola mark from
# the genital mark): her breast bones, and a point 10 cm below the middle of her hip joints.
func save_landmarks(c: Camera3D, path: String):
	var sk = follow_skel
	var g = sk.global_transform
	var pts = {}
	for nm in ["breast_l", "breast_r"]:
		var b = sk.find_bone(nm)
		if b >= 0: pts[nm] = g * sk.get_bone_global_pose(b).origin
	var tl = sk.find_bone("thigh_l")
	var tr = sk.find_bone("thigh_r")
	if tl >= 0 and tr >= 0:
		var mid = (sk.get_bone_global_pose(tl).origin + sk.get_bone_global_pose(tr).origin) * 0.5
		pts["crotch"] = g * (mid + Vector3(0, -0.10, 0))
	var outj = {}
	for n in pts:
		var s = c.unproject_position(pts[n])
		outj[n] = {"xy": [s.x, s.y], "behind": c.is_position_behind(pts[n])}
	var vs = c.get_viewport().get_visible_rect().size
	outj["size"] = {"xy": [vs.x, vs.y], "behind": true}
	var f = FileAccess.open(path, FileAccess.WRITE)
	f.store_string(JSON.stringify(outj))
	f.close()

var _tinted: Shader
# The legal check's copy of her skin shader: marked skin drawn flat magenta (areolas, UV2.x)
# or cyan (genital area, UV2.y), so the counter can find it in any light.
func tinted_skin() -> Shader:
	if _tinted != null: return _tinted
	var code = (load("res://shaders/heroine_skin.gdshader") as Shader).code
	var end = code.rfind("}")
	code = code.substr(0, end) + "\\tif (UV2.x > 0.5) { ALBEDO = vec3(0.0); SPECULAR = 0.0; ROUGHNESS = 1.0; RIM = 0.0; SSS_STRENGTH = 0.0; BACKLIGHT = vec3(0.0); EMISSION = vec3(0.0, 0.6, 0.6); }\\n\\telse if (UV2.y > 0.5) { ALBEDO = vec3(0.0); SPECULAR = 0.0; ROUGHNESS = 1.0; RIM = 0.0; SSS_STRENGTH = 0.0; BACKLIGHT = vec3(0.0); EMISSION = vec3(0.0, 0.2, 0.2); }\\n}\\n"
	_tinted = Shader.new()
	_tinted.code = code
	return _tinted

# Finds her nipples and the lowest point of her crotch in bind pose, and marks the skin round
# them in UV2. A nipple is the sharpest bump on the front half of a breast: the vertex that
# stands furthest out from its neighbours along its normal (vertices welded by position, so
# UV seams don't fake a bump). The crotch is the lowest vertex on her exact midline between
# 0.6 and 1.1 m. Metres: her body mesh stops at the neck.
func legal_marks(mi):
	# Landmarks from her untrimmed body (the outfit's skin hiding drops the triangles at a
	# nipple's tip, which would move the bump); the hiding keeps vertex order, so the marks
	# land on the trimmed mesh's same vertices.
	var src = mi.mesh
	var fresh = load("res://art/people/heroine.glb").instantiate()
	for c in fresh.find_children("*", "MeshInstance3D", true, false):
		if c.name == mi.name: src = c.mesh
	fresh.free()
	var skel = mi.get_parent()
	var breast = {}
	for b in mi.skin.get_bind_count():
		var nm = String(mi.skin.get_bind_name(b))
		if nm == "": nm = skel.get_bone_name(mi.skin.get_bind_bone(b))
		if nm.to_lower().contains("breast"): breast[b] = mi.skin.get_bind_pose(b)
	var tips = []
	var crotch = null
	for si in src.get_surface_count():
		var arr = src.surface_get_arrays(si)
		var vs = arr[Mesh.ARRAY_VERTEX]
		if vs.size() == 0: continue
		var ns = arr[Mesh.ARRAY_NORMAL]
		var bones = arr[Mesh.ARRAY_BONES]
		var wts = arr[Mesh.ARRAY_WEIGHTS]
		var idx = arr[Mesh.ARRAY_INDEX]
		var per = bones.size() / vs.size()
		for v in vs:
			if abs(v.x) < 0.002 and v.y > 0.6 and v.y < 1.1:
				if crotch == null or v.y < crotch.y: crotch = v
		# Each vertex's breast (if mostly weighted to one) and how far along that breast's bone it is.
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
		# Welded neighbour sums for breast vertices.
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
		for i in vs.size():
			var b = owner[i]
			if b < 0 or along[i] < 0.5 * reach[b]: continue
			var kk = key.call(vs[i])
			if not ncount.has(kk) or ncount[kk] < 3: continue
			var avg = nsum[kk] / float(ncount[kk])
			var spread = 0.0
			var lap = avg - vs[i]
			var score = -lap.dot(ns[i].normalized())
			if not bests.has(b) or score > bests[b]:
				bests[b] = score
				best[b] = vs[i]
		for b in best: tips.append(best[b])
	print("legal marks: ", mi.name, " tips=", tips, " crotch=", crotch)
	src = mi.mesh
	var overrides = []
	for si in src.get_surface_count(): overrides.append(mi.get_surface_override_material(si))
	var out = ArrayMesh.new()
	var counts = [0, 0]
	for si in src.get_surface_count():
		var arr = src.surface_get_arrays(si)
		var vs = arr[Mesh.ARRAY_VERTEX]
		var uv2 = PackedVector2Array()
		uv2.resize(vs.size())
		for i in vs.size():
			var v = vs[i]
			var n = 0.0
			var g = 0.0
			for tp in tips:
				if v.distance_to(tp) < 0.022: n = 1.0  # her areola's pigment: dark to 2.3 cm, gone by 3.8 (texture rings, 4 Oct)
			if crotch != null:
				var half = 0.02 if v.y < crotch.y + 0.05 else 0.035
				if abs(v.x) < half and v.y > crotch.y - 0.01 and v.y < crotch.y + 0.13 and v.z > crotch.z - 0.005: g = 1.0
				if abs(v.x) < 0.015 and v.y > crotch.y - 0.01 and v.y < crotch.y + 0.05 and v.z <= crotch.z - 0.005: g = 1.0
			uv2[i] = Vector2(n, g)
			counts[0] += int(n)
			counts[1] += int(g)
		arr[Mesh.ARRAY_TEX_UV2] = uv2
		out.add_surface_from_arrays(src.surface_get_primitive_type(si), arr)
		out.surface_set_material(si, src.surface_get_material(si))
	print("legal marks: vertices marked areola=", counts[0], " genital=", counts[1])
	mi.mesh = out
	for si in overrides.size():
		var m = overrides[si]
		if m is ShaderMaterial and m.shader != null and String(m.shader.resource_path).ends_with("heroine_skin.gdshader"):
			m.shader = tinted_skin()
		mi.set_surface_override_material(si, m)
'''
open(os.path.join(HERE, 'motioncheck2.gd'), 'w', encoding='utf-8', newline='\n').write(src)
print('written', len(src))
