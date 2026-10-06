extends SceneTree
# How far her areola's pigment reaches from each nipple tip: her skin texture's mean colour in
# 0.5 cm rings round the tips found by the motion check (bind pose). Headless; prints only.
const TIPS = [Vector3(-0.110512, 1.419238, 0.164873), Vector3(0.116004, 1.424733, 0.160397)]
func _init():
	var h = load("res://art/people/heroine.glb").instantiate()
	get_root().add_child(h)
	var mi = null
	for c in h.find_children("*", "MeshInstance3D", true, false):
		if String(c.name) == "Heroine": mi = c
	var src = mi.mesh
	for si in src.get_surface_count():
		var mat = src.surface_get_material(si)
		if mat == null or not (mat is BaseMaterial3D) or mat.albedo_texture == null: continue
		var img: Image = mat.albedo_texture.get_image()
		if img.is_compressed(): img.decompress()
		var arr = src.surface_get_arrays(si)
		var vs = arr[Mesh.ARRAY_VERTEX]
		var uv = arr[Mesh.ARRAY_TEX_UV]
		print("surface ", si, " texture ", img.get_width(), "x", img.get_height())
		for tp in TIPS:
			var rings = {}
			for i in vs.size():
				var d = vs[i].distance_to(tp)
				if d > 0.05: continue
				var r = int(d / 0.005)
				var px = img.get_pixel(clampi(int(uv[i].x * img.get_width()), 0, img.get_width() - 1), clampi(int(uv[i].y * img.get_height()), 0, img.get_height() - 1))
				if not rings.has(r): rings[r] = [Color(0, 0, 0), 0]
				rings[r][0] += px
				rings[r][1] += 1
			var line = "tip %s:" % tp
			for r in range(0, 10):
				if rings.has(r):
					var c = rings[r][0] / float(rings[r][1])
					line += "  %.1fcm %d,%d,%d" % [r * 0.5 + 0.25, int(c.r * 255), int(c.g * 255), int(c.b * 255)]
			print(line)
	quit()
