extends SceneTree
# The 4.7.2 upgrade: the warm-up library (res://data/fx_warm/warm.scn) keeps a copy of each code-made shader's text, so a
# shader file's edit leaves its stand-ins on the old code. warm_patch.py runs this twice around its text edit:
#   <4.5.1 console exe> --headless --path godot -s <abs path to this file> -- to     (the library as text, user://warm_patch.tscn)
#   <4.5.1 console exe> --headless --path godot -s <abs path to this file> -- back   (the text saved back as the library)
# Run with 4.5.1 so both engines can read the result.
const LIB := "res://data/fx_warm/warm.scn"
const TMP := "user://warm_patch.tscn"

func _init():
	var mode := "to"
	var a := OS.get_cmdline_user_args()
	if a.size() > 0: mode = a[0]
	var err := OK
	if mode == "to":
		err = ResourceSaver.save(load(LIB), TMP)
		print("PATCH to ", ProjectSettings.globalize_path(TMP), " err ", err)
	else:
		err = ResourceSaver.save(ResourceLoader.load(TMP, "", ResourceLoader.CACHE_MODE_IGNORE), LIB, ResourceSaver.FLAG_COMPRESS)  # (as the census saves it)
		print("PATCH back ", LIB, " err ", err)
	quit(0 if err == OK else 1)
