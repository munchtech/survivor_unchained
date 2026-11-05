extends SceneTree
# (L1 B6) The UI language's test panel: shaders/ui_cel_panel.gdshader drawn from data/look/ui_language.json, at 1:1 on
# a 1920x1080 frame, saved as a PNG. Never a live screen (the UI lead owns every element's look).
#   godot --path godot --resolution 1920x1080 -s res://tools_scenes/ui_panel.gd -- OUT.png [W H X Y] [BACKDROP.png]
# W H X Y: the panel's size and place in px (default: target 11's result panel at 1080 lines); BACKDROP: drawn behind,
# stretched to the frame (a target, to see the panel in its place).
var out = ""
var frames = 0
func _init():
	var a = OS.get_cmdline_user_args()
	out = a[0]
	var w = 1208.0; var h = 838.0; var x = 354.0; var y = 110.0
	if a.size() >= 5:
		w = float(a[1]); h = float(a[2]); x = float(a[3]); y = float(a[4])
	var ui = JSON.parse_string(FileAccess.get_file_as_string("res://data/look/ui_language.json"))
	var p = ui["panel"]
	var root = Control.new()
	root.size = Vector2(1920, 1080)
	get_root().add_child(root)
	var bg = ColorRect.new()
	bg.color = Color(0.03, 0.04, 0.07)
	bg.size = Vector2(1920, 1080)
	root.add_child(bg)
	if a.size() == 6 or a.size() == 2:
		var img = Image.load_from_file(a[a.size() - 1])
		var tr = TextureRect.new()
		tr.texture = ImageTexture.create_from_image(img)
		tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		tr.size = Vector2(1920, 1080)
		root.add_child(tr)
	var r = ColorRect.new()
	r.position = Vector2(x, y)
	r.size = Vector2(w, h)
	var m = ShaderMaterial.new()
	m.shader = load("res://shaders/ui_cel_panel.gdshader")
	m.set_shader_parameter("size_px", Vector2(w, h))
	for k in ["field", "field_deep", "frame", "frame_hi", "ink"]:
		m.set_shader_parameter(k, Color.html(p[k]))
	for k in ["frame_px", "line_px", "corner_px", "grain"]:
		m.set_shader_parameter(k, float(p[k]))
	m.set_shader_parameter("band", float(ui["blocks"]["bronze"]["band"]))
	m.set_shader_parameter("gold", Color.html(ui["text"]["gold"]["hex"]))
	m.set_shader_parameter("gold_y", h * 0.42)
	m.set_shader_parameter("gold_px", float(ui["line"]["px"]) * 0.7)
	r.material = m
	root.add_child(r)
	# the swatches: each block as a painted tile (field, its highlight band on top, the ink outline), the text and accents
	var sx = x + 60.0
	var sy = y + 90.0
	for name in ["bronze", "iron", "parchment", "statue_bronze"]:
		var b = ui["blocks"][name]
		var ink = ColorRect.new(); ink.color = Color.html(b["ink"]); ink.position = Vector2(sx, sy); ink.size = Vector2(120, 80); root.add_child(ink)
		var lw = float(ui["line"]["px"])
		var f = ColorRect.new(); f.color = Color.html(b["field"]); f.position = Vector2(sx + lw, sy + lw); f.size = Vector2(120 - 2 * lw, 80 - 2 * lw); root.add_child(f)
		var hb = ColorRect.new(); hb.color = Color.html(b["highlight"]); hb.position = Vector2(sx + lw, sy + lw); hb.size = Vector2(120 - 2 * lw, (80 - 2 * lw) * float(b["band"])); root.add_child(hb)
		var l = Label.new(); l.text = name; l.position = Vector2(sx, sy + 86); l.add_theme_color_override("font_color", Color.html(ui["text"]["cream"]["hex"])); l.add_theme_font_size_override("font_size", 18); root.add_child(l)
		sx += 150.0
	for name in ["skill", "level", "hostile"]:
		var l = Label.new(); l.text = name; l.position = Vector2(sx, sy + 20 + 30 * ["skill", "level", "hostile"].find(name))
		l.add_theme_color_override("font_color", Color.html(ui["accents"][name]["hex"])); l.add_theme_font_size_override("font_size", 22); root.add_child(l)
	var t = Label.new(); t.text = "The night is held: reading text in cream, one gold line below"
	t.position = Vector2(x + 60.0, y + h * 0.42 - 48.0); t.add_theme_color_override("font_color", Color.html(ui["text"]["cream"]["hex"])); t.add_theme_font_size_override("font_size", 28)
	root.add_child(t)

func _process(_d):
	frames += 1
	if frames == 8:
		get_root().get_texture().get_image().save_png(out)
		print("ui_panel: wrote ", out)
		quit()
	return false
