extends SceneTree
# Saves the Quaternius base bodies' imported textures as PNG (legal: do their maps paint
# anatomical detail?). Args after --: <out dir> <res path> ...
func _init():
	var a = OS.get_cmdline_user_args()
	var out = a[0]
	DirAccess.make_dir_recursive_absolute(out)
	for i in range(1, a.size()):
		var t = load(a[i])
		if t == null:
			print("legal dump: cannot load ", a[i])
			continue
		var img: Image = t.get_image()
		if img.is_compressed(): img.decompress()
		var f = out + "/" + a[i].get_file().get_basename() + ".png"
		print("legal dump: ", a[i], " ", img.get_size(), " -> ", f, " ", img.save_png(f))
	quit()
