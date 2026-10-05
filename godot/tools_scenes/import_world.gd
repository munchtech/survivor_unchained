@tool
extends EditorScenePostImport
# The photoscans (art/world, Poly Haven) carry their images inside the model,
# and the importer keeps those uncompressed and without mipmaps: every texel
# of a 1K map read from 20 to 50 pixels away on screen (sparkle under TAA),
# four bytes a texel in video memory. Here each gets its mipmaps and is
# compressed as Godot's own imported textures are (BC7 for colour and
# roughness, BC5 for normal maps, mipmaps renormalised): steady at a
# distance, a quarter of the memory, and a third of the file to read.

func _post_import(scene: Node) -> Object:
	var done := {}
	_walk(scene, done)
	return scene

func _walk(n: Node, done: Dictionary) -> void:
	if n is MeshInstance3D and n.mesh:
		for s in n.mesh.get_surface_count():
			_material(n.mesh.surface_get_material(s), done)
	for c in n.get_children():
		_walk(c, done)

func _material(m: Material, done: Dictionary) -> void:
	if m == null:
		return
	if m is BaseMaterial3D:
		for p in ["albedo_texture", "normal_texture", "roughness_texture", "metallic_texture", "orm_texture", "ao_texture", "emission_texture"]:
			_texture(m.get(p), p, done)
	_material(m.next_pass, done)

func _texture(t, prop: String, done: Dictionary) -> void:
	if not (t is ImageTexture) or done.has(t):
		return
	done[t] = true
	var img: Image = t.get_image()
	if img == null or img.is_compressed():
		return
	var normal := prop == "normal_texture"
	if not img.has_mipmaps():
		img.generate_mipmaps(normal)
	if normal:
		img.compress(Image.COMPRESS_S3TC, Image.COMPRESS_SOURCE_NORMAL)
	else:
		img.compress(Image.COMPRESS_BPTC, Image.COMPRESS_SOURCE_SRGB if prop in ["albedo_texture", "emission_texture"] else Image.COMPRESS_SOURCE_GENERIC)
	t.set_image(img)
