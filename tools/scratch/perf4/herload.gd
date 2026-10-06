extends SceneTree
# Her files' load, timed: the file read alone, then the resource load (twice,
# the second from Godot's cache dropped), and what each holds (meshes,
# vertices, blend shapes, images by format). Run windowed and headless: the
# difference is what the renderer's uploads cost.

const FILES := [
	"res://art/people/heroine.glb",
	"res://art/people/heroine_outfit_warden.gltf",
	"res://art/people/heroine_hair_long.gltf",
]

func _initialize() -> void:
	for f in FILES:
		var remap: String = _remap(f)
		var t0 := Time.get_ticks_usec()
		var bytes := FileAccess.get_file_as_bytes(remap)
		var t_read := (Time.get_ticks_usec() - t0) / 1000.0
		t0 = Time.get_ticks_usec()
		var res: PackedScene = ResourceLoader.load(f, "", ResourceLoader.CACHE_MODE_REPLACE)
		var t_load := (Time.get_ticks_usec() - t0) / 1000.0
		t0 = Time.get_ticks_usec()
		var inst := res.instantiate()
		var t_inst := (Time.get_ticks_usec() - t0) / 1000.0
		var stats := {"meshes": 0, "surfaces": 0, "verts": 0, "shapes": 0, "images": {}}
		_walk(inst, stats, {})
		print("%s: file %.1f MB read %.0f ms, load %.0f ms, instantiate %.0f ms; %s" % [f.get_file(), bytes.size() / 1e6, t_read, t_load, t_inst, stats])
		inst.free()
		res = null
	quit()

func _remap(f: String) -> String:
	var cfg := ConfigFile.new()
	cfg.load(f + ".import")
	return cfg.get_value("remap", "path", f)

func _walk(n: Node, stats: Dictionary, seen: Dictionary) -> void:
	if n is MeshInstance3D and n.mesh and not seen.has(n.mesh):
		seen[n.mesh] = true
		var m: Mesh = n.mesh
		stats.meshes += 1
		stats.surfaces += m.get_surface_count()
		if m is ArrayMesh:
			stats.shapes += (m as ArrayMesh).get_blend_shape_count()
		for s in m.get_surface_count():
			stats.verts += m.surface_get_array_len(s)
			var mat := m.surface_get_material(s)
			if mat is BaseMaterial3D:
				for p in ["albedo_texture", "normal_texture", "roughness_texture", "orm_texture", "emission_texture", "subsurf_scatter_texture"]:
					var t = mat.get(p)
					if t is Texture2D and not seen.has(t):
						seen[t] = true
						var key := "%s %dx%d" % [t.get_class(), t.get_width(), t.get_height()]
						if t is ImageTexture:
							key += " " + str(t.get_format())
						stats.images[key] = stats.images.get(key, 0) + 1
	for c in n.get_children():
		_walk(c, stats, seen)
