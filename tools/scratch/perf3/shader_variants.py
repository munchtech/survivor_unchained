"""Grass shader variants for checking the off-view early-out:
  NAME.orig.gdshader   the committed shader (git HEAD)
  NAME.new.gdshader    the working tree's (the early-out)
  NAME.debug.gdshader  every tuft drawn, the ones the early-out would drop tinted magenta
and `use NAME VARIANT` copies one into the project."""
import shutil
import subprocess
import sys

W = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a56abaf3a104be675"
S = r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\perf3\shaders"
NAMES = {"arena_grass": "v_col", "grass": "v_tint"}

if sys.argv[1] == "make":
    import os
    os.makedirs(S, exist_ok=True)
    for name, col in NAMES.items():
        orig = subprocess.run(["git", "-C", W, "show", f"HEAD:godot/shaders/{name}.gdshader"], capture_output=True, text=True).stdout
        open(f"{S}\\{name}.orig.gdshader", "w", encoding="utf-8", newline="\n").write(orig)
        src = open(f"{W}\\godot\\shaders\\{name}.gdshader", encoding="utf-8").read().replace("\r\n", "\n")
        open(f"{S}\\{name}.new.gdshader", "w", encoding="utf-8", newline="\n").write(src)
        i = src.index("\tif (d >= span * 0.5 ||")
        j = src.index(") {\n", i)
        cond = src[i + len("\tif ("):j]
        dbg = src[:i] + f"\tbool culled = {cond};\n\tif (false) {{\n" + src[j + 4:]
        k = dbg.rindex("\t}\n}")
        dbg = dbg[:k] + f"\t\tif (culled) {{ {col} = vec3(4.0, 0.0, 4.0); }}\n" + dbg[k:]
        open(f"{S}\\{name}.debug.gdshader", "w", encoding="utf-8", newline="\n").write(dbg)
        print(name, "made")
elif sys.argv[1] == "use":
    variant = sys.argv[2]
    for name in NAMES:
        shutil.copyfile(f"{S}\\{name}.{variant}.gdshader", f"{W}\\godot\\shaders\\{name}.gdshader")
    print("using", variant)
