extends SceneTree
func _init():
	var h = load("res://art/people/heroine.glb").instantiate()
	get_root().add_child(h)
	var bt = AnimationNodeBlendTree.new()
	var a = AnimationNodeAnimation.new()
	a.animation = "her/run_warden"
	bt.add_node("run", a)
	bt.connect_node("output", 0, "run")
	var t = AnimationTree.new()
	t.tree_root = bt
	h.add_child(t)
	t.root_node = NodePath("..")
	t.add_animation_library("her", load("res://art/anim/heroine.res"))
	t.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
	t.active = true
	t.advance(0.25)
	print("POS ", t.get("parameters/run/current_position"), " LEN ", t.get("parameters/run/current_length"))
	for p in t.get_property_list():
		if String(p.name).begins_with("parameters/run"): print("PARAM ", p.name)
	quit()
