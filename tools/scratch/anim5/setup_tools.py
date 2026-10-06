from pathlib import Path
src = Path(r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\anim4")
dst = src.parent / "anim5"
(dst / "sh").mkdir(exist_ok=True)
for f in src.glob("*.py"):
    if f.name in ("setup_tools.py",):
        continue
    t = f.read_text(encoding="utf-8")
    t = t.replace("agent-a7dd95d00c4a6a017", "agent-aa15f092820132274").replace("scratchpad\\anim4", "scratchpad\\anim5").replace("scratchpad/anim4", "scratchpad/anim5")
    (dst / f.name).write_text(t, encoding="utf-8")
    print(f.name)
