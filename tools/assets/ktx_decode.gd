extends SceneTree
# Decodes KTX2 sheets to PNG through Godot's own loader (Basis transcode, then decompress):
#   godot --headless --path godot -s ../tools/assets/ktx_decode.gd -- OUT_DIR res://assets/a.ktx2 ...
# (tools/assets/paint_tex.py --decode runs this for the normal maps it needs.)
func _init():
	var a := OS.get_cmdline_user_args()
	var out: String = a[0]
	DirAccess.make_dir_recursive_absolute(out)
	for i in range(1, a.size()):
		var t := load(a[i]) as Texture2D
		if t == null:
			printerr("ktx_decode: cannot load ", a[i]); continue
		var img := t.get_image()
		if img.is_compressed(): img.decompress()
		if img.has_mipmaps(): img.clear_mipmaps()
		img.convert(Image.FORMAT_RGBA8)
		var p: String = out.path_join(a[i].get_file().get_basename() + ".png")
		img.save_png(p)
		print("ktx_decode: ", p, " ", img.get_width(), "x", img.get_height())
	quit()
