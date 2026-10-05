@tool
extends EditorScenePostImport
# Mipmaps for the images a model carries inside it (heroine.glb embeds hers
# uncompressed, and the importer gives those none). Without them her 4K face
# and 2K body were read texel by texel from 20 to 150 pixels away on screen:
# grain and crawl under TAA, the detail lost rather than kept. With them each
# pixel sees the true average, and up close the full image is unchanged.

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
		for p in ["albedo_texture", "normal_texture", "roughness_texture", "metallic_texture", "orm_texture", "emission_texture", "subsurf_scatter_texture"]:
			_texture(m.get(p), done)
	_material(m.next_pass, done)

func _texture(t, done: Dictionary) -> void:
	if not (t is ImageTexture) or done.has(t):
		return
	done[t] = true
	var img: Image = t.get_image()
	if img == null or img.has_mipmaps() or img.is_compressed():
		return
	img.generate_mipmaps()
	t.set_image(img)
