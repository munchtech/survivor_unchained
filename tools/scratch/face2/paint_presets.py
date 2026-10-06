"""paint_presets.py id ... : each preset's face painted (heroine_face.py on the unpainted head shaped as it), into face2/preset_<id>;
then its face_paint.png copied to tools/assets/heroine_face/face_paint_<id>.png."""
import json
import os
import shutil
import subprocess
import sys

W = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a6784044c82f101d9"
SC = r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face2"
B = r"C:\Users\munch\Tools\blender-4.5.14-windows-x64\blender.exe"
sys.path.insert(0, os.path.join(W, "tools", "assets"))
import face_refs  # noqa: E402

presets = {p["id"]: p for p in json.load(open(os.path.join(W, "tools", "assets", "heroine_face", "presets.json"), encoding="utf-8"))}
for pid in sys.argv[1:]:
    p = presets[pid]
    who = face_refs.FACES[pid]
    who = who.replace("She is a ", "a ", 1)
    who = ". ".join(s for s in who.split(". ") if "hair" not in s.lower()).rstrip(".") + "."
    out = os.path.join(SC, f"preset_{pid}")
    os.makedirs(out, exist_ok=True)
    shape = os.path.join(out, "shape.json")
    json.dump(p["shape"], open(shape, "w"))
    env = dict(os.environ, FACE_SHAPE=shape, FACE_WHO=who, FACE_SEED=os.environ.get("FACE_SEED", "11"))
    with open(out + ".log", "w") as log:
        subprocess.run([B, "-b", os.path.join(W, "tools", "comfy", "out", "heroes", "heroine_unpainted.blend"), "--python",
                        os.path.join(W, "tools", "assets", "heroine_face.py"), "--", out], env=env, stdout=log, stderr=subprocess.STDOUT)
    src = os.path.join(out, "face_paint.png")
    if os.path.exists(src):
        shutil.copy(src, os.path.join(W, "tools", "assets", "heroine_face", f"face_paint_{pid}.png"))
        print("PAINTED", pid, "as:", who)
    else:
        print("FAILED", pid)
