from pathlib import Path
p = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa15f092820132274\docs\team\animation.md")
t = p.read_text(encoding="utf-8")
E = [
    ('''| leap | Ground |''', '''| flinch (new, a gesture) | Sheets over a run and a cut, three-quarter and the arena camera | New: laid over a run or a blow (`PlayerView`, when moving or busy); standing, the upper-body hit as before | Good on sheets: the chest caves, the head snaps back, the legs keep running and the arms their hold |
| leap | Ground |'''),
    ('''2. Grimtunnel's four and the lampling's slam (`Beasts.cs`); the chain haul's landing crouch and a heavier running flinch.''',
     '''2. Grimtunnel's four and the lampling's slam (`Beasts.cs`): nothing in the game asks for these roles yet; agree the moments with combat first. The chain haul's landing crouch.'''),
]
for a, b in E:
    assert t.count(a) == 1, a[:50]
    t = t.replace(a, b)
p.write_text(t, encoding="utf-8")
print("ok")
