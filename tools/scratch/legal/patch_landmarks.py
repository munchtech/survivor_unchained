"""Patches make_motioncheck2.py: each picture also saves where her landmarks fall on screen
(<picture>.json), so count.py can tell an areola mark from the genital mark."""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(HERE, 'make_motioncheck2.py')
t = open(p, encoding='utf-8').read()

anchor = "'\\t\\t\\t\\tview_ports[vi].get_texture().get_image().save_png(out.replace(\".png\", \"%s_%02d.png\" % [tag, k]))\\n')"
assert t.count(anchor) == 1, 'capture anchor'
t = t.replace(anchor, anchor[:-1] + "\n     '\\t\\t\\t\\tif follow_skel != null: save_landmarks(view_cams[vi], out.replace(\".png\", \"%s_%02d.json\" % [tag, k]))\\n')")

func = '''
# Where her landmarks fall on screen in a picture (for count.py to tell an areola mark from
# the genital mark): her breast bones, and a point 10 cm below the middle of her hip joints.
func save_landmarks(c: Camera3D, path: String):
	var sk = follow_skel
	var g = sk.global_transform
	var pts = {}
	for nm in ["breast_l", "breast_r"]:
		var b = sk.find_bone(nm)
		if b >= 0: pts[nm] = g * sk.get_bone_global_pose(b).origin
	var tl = sk.find_bone("thigh_l")
	var tr = sk.find_bone("thigh_r")
	if tl >= 0 and tr >= 0:
		var mid = (sk.get_bone_global_pose(tl).origin + sk.get_bone_global_pose(tr).origin) * 0.5
		pts["crotch"] = g * (mid + Vector3(0, -0.10, 0))
	var outj = {}
	for n in pts:
		var s = c.unproject_position(pts[n])
		outj[n] = {"xy": [s.x, s.y], "behind": c.is_position_behind(pts[n])}
	var f = FileAccess.open(path, FileAccess.WRITE)
	f.store_string(JSON.stringify(outj))
	f.close()
'''
anchor2 = "src += '''\nvar _tinted: Shader"
assert t.count(anchor2) == 1, 'func anchor'
t = t.replace(anchor2, "src += '''" + func + "\nvar _tinted: Shader")
open(p, 'w', encoding='utf-8', newline='\n').write(t)
print('patched')
