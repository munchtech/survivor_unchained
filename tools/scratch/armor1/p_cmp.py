s = open("compare.py").read()
s = s.replace("from heroine_lod import Gltf", "from heroine_lod import Gltf, slot_join")
s = s.replace('grp.setdefault(p[0], []).append((m.get("extras", {}).get("rank", 0), m["name"], p))', 'grp.setdefault(p[0], []).append((m.get("extras", {}), p[1], p[2]))')
a = s.index("        got = sorted(grp[mat]")
b = s.index("        cat = (mat, attrs, np.concatenate(tris))")
s = s[:a] + "        got = grp[mat]\n        attrs, tt = slot_join(got, mat)\n        cat = (mat, attrs, tt)" + s[b + len("        cat = (mat, attrs, np.concatenate(tris))"):]
open("compare.py", "w").write(s)
