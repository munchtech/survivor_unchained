"""The 4.7.2 upgrade: carry kit.gdshader's varying packing (52cff96be) into the warm-up library's copies of its code.
    python tools/scratch/godot47/warm_patch.py
warm.scn (res://data/fx_warm/warm.scn) keeps each code-made shader's text, so a shader file's edit leaves its stand-ins
warming the old code (on 4.7.2 the roof copy failed to compile). Converts the library to text with 4.5.1 (warm_patch.gd),
swaps the old block for kit.gdshader's new one in every copy, and saves it back as the binary library."""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
G45 = r"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
GD = os.path.join(ROOT, "tools", "scratch", "godot47", "warm_patch.gd")
TMP = os.path.join(os.environ["APPDATA"], "Godot", "app_userdata", "Survivor Unchained", "warm_patch.tscn")
OLD = ("varying float v_lx;\nvarying vec3 v_wn;\nvarying float v_rh;\nvarying float v_lz;\n#endif\n\n"
       "varying float v_up;\nvarying float v_jit;\nvarying float v_y;\n")


def gd(mode):
    r = subprocess.run([G45, "--headless", "--path", os.path.join(ROOT, "godot"), "-s", GD, "--", mode], capture_output=True, text=True)
    line = [l for l in r.stdout.splitlines() if l.startswith("PATCH")]
    print(*line)
    if r.returncode != 0:
        sys.exit(f"warm_patch.gd {mode} failed ({r.returncode})")


kit = open(os.path.join(ROOT, "godot", "shaders", "kit.gdshader"), encoding="utf-8").read()
a = kit.index("// (Godot 4.7.2 upgrade)")
b = kit.index("#define v_y v_ujy.z\n") + len("#define v_y v_ujy.z\n")
NEW = kit[a:b]
gd("to")
txt = open(TMP, encoding="utf-8", newline="").read()
# (the census kept some copies with Windows line ends: both kinds)
def crlf(s):
    return s.replace(chr(10), chr(13) + chr(10))


n = txt.count(OLD) + txt.count(crlf(OLD))
print(f"copies of the old block: {n}")
if n:
    txt = txt.replace(crlf(OLD), crlf(NEW)).replace(OLD, NEW)
    open(TMP, "w", encoding="utf-8", newline="").write(txt)
    gd("back")
    gd("to")
    t2 = open(TMP, encoding="utf-8", newline="").read()
    print(f"after: old {t2.count(OLD) + t2.count(crlf(OLD))}, new {t2.count(NEW) + t2.count(crlf(NEW))}")
