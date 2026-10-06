p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa15f092820132274\godot\tools_scenes\anim_review.gd"
s = open(p, encoding="utf-8").read()
old = '''	if view == "game": cam.fov = 26'''
new = '''	# OFF=x,y,z: the camera at this offset from the look point (her space,
	# metres), LOOKOFF=x,y,z the look point moved: a cinematic's own set-up.
	if env("OFF", "") != "":
		var o = env("OFF", "").split_floats(",")
		off = Vector3(o[0], o[1], o[2])
	if env("LOOKOFF", "") != "":
		var lo = env("LOOKOFF", "").split_floats(",")
		c += Vector3(lo[0], lo[1], lo[2])
	if view == "game": cam.fov = 26'''
assert old in s
s = s.replace(old, new, 1)
old2 = '''	var hands = {"sword": [["hand_r", 0.95, 0.05, steel]],'''
new2 = '''	if kind == "flask":
		flask(skel)
		return
	var hands = {"sword": [["hand_r", 0.95, 0.05, steel]],'''
assert old2 in s
s = s.replace(old2, new2, 1)
old3 = '''func stage(root):'''
new3 = '''# A flat pewter flask in the right hand, as Arms.Hold would mount one: its
# body round the grip (13 cm tall, 10 wide, 4.5 thin across the palm), the
# neck's mouth 9 cm up out of the thumb side.
func flask(skel):
	var at = BoneAttachment3D.new()
	at.bone_name = "hand_r"
	skel.add_child(at)
	var mount = Node3D.new()
	var x = Vector3(0, 1, 0)
	var y = Vector3(0, 0, 1)
	mount.basis = Basis(x, y, x.cross(y))
	mount.position = Vector3(-0.025, 0.075, 0)
	at.add_child(mount)
	var pewter = StandardMaterial3D.new()
	pewter.albedo_color = Color(0.56, 0.58, 0.59)
	pewter.metallic = 0.85
	pewter.roughness = 0.4
	var body = MeshInstance3D.new()
	var bm = CylinderMesh.new()
	bm.top_radius = 0.05
	bm.bottom_radius = 0.05
	bm.height = 0.13
	bm.material = pewter
	body.mesh = bm
	body.scale = Vector3(1, 1, 0.45)
	mount.add_child(body)
	var neck = MeshInstance3D.new()
	var nm = CylinderMesh.new()
	nm.top_radius = 0.012
	nm.bottom_radius = 0.016
	nm.height = 0.03
	nm.material = pewter
	neck.mesh = nm
	neck.position = Vector3(0, 0.075, 0)
	mount.add_child(neck)

func stage(root):'''
s = s.replace(old3, new3, 1)
open(p, "w", encoding="utf-8").write(s)
print("patched")
