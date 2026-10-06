extends SceneTree
# What the textures inside some scenes are: class, size, format, mipmaps, and
# how long each scene takes to load.  godot --headless --path godot -s texprobe.gd -- res://a.glb ...

func _init() -> void:
	for path in OS.get_cmdline_user_args():
		var t := Time.get_ticks_usec()
		var ps: PackedScene = load(path)
		var ms := (Time.get_ticks_usec() - t) / 1000.0
		var root := ps.instantiate()
		var seen := {}
		var lines := []
		for mi in root.find_children("*", "MeshInstance3D", true, false):
			var mesh: Mesh = mi.mesh
			for s in mesh.get_surface_count():
				var m = mesh.surface_get_material(s)
				if m is BaseMaterial3D:
					for prop in ["albedo_texture", "normal_texture", "roughness_texture", "metallic_texture", "ao_texture"]:
						var tex = m.get(prop)
						if tex == null or seen.has(tex):
							continue
						seen[tex] = true
						var info := "%s %s %dx%d" % [prop, tex.get_class(), tex.get_width(), tex.get_height()]
						if tex is PortableCompressedTexture2D:
							info += " mode %d" % tex.get_compression_mode()
						var img: Image = tex.get_image()
						if img:
							info += " fmt %d mips %s" % [img.get_format(), img.has_mipmaps()]
						lines.append("    " + info)
		print("%s: %.0f ms" % [path, ms])
		for l in lines:
			print(l)
		root.free()
	quit()
