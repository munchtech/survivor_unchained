p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abc6bbe020c7fe287\godot\src\Fx\BattleFx.Skills.cs"
s = open(p, encoding="utf-8").read()
a = '''                Dust(z.X, z.Z, 8, 2.5f);
            }'''
b = '''                Dust(z.X, z.Z, 8, 2.5f);
            }
            // Blightfield rots the ground it takes: a dark stain of rot under its veins (a bright
            // ring round clean ground read as a circle drawn on it, not a field gone bad).
            if (inside == Inside.Veins)
                Scars.Add("blight", V(z.X, Y(z.X, z.Z), z.Z), r * 1.05f, (float)Math.Max(0.8, z.Life - z.Age) + 0.6f, 0);'''
assert a in s
s = s.replace(a, b)
a2 = "(inside == Inside.Roots ? 0.45f : 0.85f)"
b2 = "(inside is Inside.Roots or Inside.Veins ? 0.45f : 0.85f)"
assert a2 in s
s = s.replace(a2, b2)
s = s.replace("        // (A thicket's edge is its thorns: its lit ring held back so the brambles are what reads.)",
              "        // (A thicket's edge is its thorns, a rot's its stain: their lit rings held back.)")
open(p, "w", encoding="utf-8").write(s)

b2p = r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\vfx\b2.sh"
t = open(b2p).read()
t = t.replace("thornbloom gravecall --horde", "thornbloom gravecall blightfield firepot --horde")
open(b2p, "w", newline="\n").write(t)
print("ok")
