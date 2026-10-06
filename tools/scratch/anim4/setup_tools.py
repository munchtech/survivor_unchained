from pathlib import Path
src = Path(r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\anim3")
dst = src.parent / "anim4"
for n in ["board.py", "cine.py", "cine_try.py", "cine_try3.py", "csheet.py", "game.py", "hsheet.py", "joints.py",
          "repack.py", "stick.py", "take_info.py", "tile.py", "try_takes.py"]:
    t = (src / n).read_text(encoding="utf-8")
    t = t.replace("agent-a03acf30b3e9bdd70", "agent-a7dd95d00c4a6a017").replace("scratchpad\\anim3", "scratchpad\\anim4").replace("scratchpad/anim3", "scratchpad/anim4")
    (dst / n).write_text(t, encoding="utf-8")
print("ok")
