p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa15f092820132274\tools\anim\clips\rook.py"
s = open(p, encoding="utf-8").read()
s = s.replace('''                pose[f"hand_{s}"] = {"pos": tuple(pos), "pole": pole, "frame": "char",
                                     "knuckles": (-0.35 if s == "l" else 0.35, -0.85, 0.3)}''', '''                # The hand turns from how it lay in the fold (its fingers' way, +Y).
                lay = qrot(g[fr, I[f"hand_{s}"]], np.array([0.0, 1.0, 0.0]))
                knuck = slerp_dir(lay, (-0.35 if s == "l" else 0.35, -0.85, 0.3), w)
                pose[f"hand_{s}"] = {"pos": tuple(pos), "pole": pole, "frame": "char", "knuckles": tuple(knuck)}''')
s = s.replace('from held import solved', 'from held import slerp_dir, solved')
s = s.replace('from keyed import Rig, smoothstep_', 'from keyed import Rig, smoothstep_\nfrom rig import qrot')
open(p, "w", encoding="utf-8").write(s)
print("ok")
