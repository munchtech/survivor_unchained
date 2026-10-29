# applied to chain.sh after run1: s2 runs heroine_body_post.main itself (so any step integration adds, e.g. Face 41's
# brow strokes, runs too) with only 7b axilla_fold / 7c shoulder_psd skipped and no LOD; s9 also copies head_tex changes.
import re
p = r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\a44c2c21-ed7f-40ee-bf4a-842fa5db11c1\scratchpad\body12\g3\chain.sh"
s = open(p, encoding="utf-8").read()
a = s.index("import os, sys\nsys.path.insert")
b = s.index("EOF\n  cp \"$ART/heroine.glb\" \"$OUT/base.glb\"")
s = s[:a] + '''import os, sys
sys.path.insert(0, os.path.join(os.getcwd(), "tools", "assets"))
import heroine_body_post as hbp
# (every step of the body post, as integration has it, but 7b/7c: the new body brings its own shoulder shapes,
# and the export's old ones would land on the outfits as follows of shapes the body no longer has)
SKIP = ("axilla_fold_post.py", "shoulder_psd_post.py", "heroine_lod.py")
_run = hbp.run
def run(*a):
    if os.path.basename(a[0]) in SKIP:
        print("G3 skipped", os.path.basename(a[0])); return
    _run(*a)
hbp.run = run
hbp.main([sys.argv[1], "--no-lod"])
print("MARKS", sorted(hbp.marks(os.path.join(sys.argv[1], "heroine.glb"))))
''' + s[b:]
s = s.replace('''  for f in "$ST"/godot/art/outfit/*; do''', '''  for f in "$ART"/head_tex/*; do cmp -s "$f" "$W/$P/head_tex/$(basename "$f")" || cp "$f" "$W/$P/head_tex/"; done
  for f in "$ST"/godot/art/outfit/*; do''')
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("patched")
