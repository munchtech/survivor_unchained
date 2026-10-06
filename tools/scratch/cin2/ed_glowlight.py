import os
G = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a3058a45eee41d695\godot"
p = os.path.join(G, r"src\Game\GameCinema.cs")
s = open(p, encoding="utf-8").read()
old = '''                    // "under": [width, height], the dark of what the light is set in (a tower against the sky).'''
new = '''                    // "light": it lights what is near it too (a lamp held to a face), within "range".
                    if (c.Has("light"))
                        root.AddChild(new OmniLight3D { LightColor = col, LightEnergy = (float)c.Num("light"), OmniRange = (float)c.Num("range", 4), OmniAttenuation = 1.4f });
                    // "under": [width, height], the dark of what the light is set in (a tower against the sky).'''
assert s.count(old) == 1
s = s.replace(old, new)
open(p, "w", encoding="utf-8", newline="").write(s)

p = r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\cin2\prev.py"
s = open(p, encoding="utf-8").read()
old = '''cols, width, zone = opt("--cols", "3"), opt("--width", "620"), opt("--zone", "lowford")'''
new = '''cols, width, zone = opt("--cols", "3"), opt("--width", "620"), opt("--zone", "lowford")
only = [x for x in opt("--only", "").split(",") if x]'''
assert old in s
s = s.replace(old, new)
old = '''files = sorted((f for f in glob.glob(os.path.join(WT, ".shots", f"{name}_*.png")) if os.path.getmtime(f) >= t0 - 1), key=os.path.getmtime)'''
new = '''files = sorted((f for f in glob.glob(os.path.join(WT, ".shots", f"{name}_*.png")) if os.path.getmtime(f) >= t0 - 1
                and (not only or any(f"_s{o.lower()}_" in os.path.basename(f) for o in only))), key=os.path.getmtime)'''
assert old in s
s = s.replace(old, new)
open(p, "w", encoding="utf-8", newline="").write(s)
print("ok")
