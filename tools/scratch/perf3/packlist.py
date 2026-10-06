"""List an exported pack (zip): every source path it carries (imported files by
their .import/.remap source), sizes by folder, and checks against what must stay
out and what the code reads with FileAccess."""
import fnmatch
import os
import re
import sys
import zipfile
from collections import defaultdict

pack = sys.argv[1]
out = sys.argv[2]
proj = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a56abaf3a104be675\godot"

z = zipfile.ZipFile(pack)
names = {i.filename: i.file_size for i in z.infolist()}

# Imported blobs live under .godot/imported; map them back to their source by the
# .import / .remap files the pack carries.
sources = {}
imported_size = {}
for n in names:
    if n.endswith(".import") or n.endswith(".remap"):
        src = n[: n.rfind(".")]
        txt = z.read(n).decode("utf-8", "replace")
        paths = re.findall(r'(?:path(?:\.\w+)?|dest_files)="?\[?"?(res://\.godot/[^"\]]+)', txt)
        paths = [p.replace("res://", "") for p in paths]
        size = sum(names.get(p, 0) for p in paths)
        sources[src] = size
for n, s in names.items():
    if n.endswith(".import") or n.endswith(".remap") or n.startswith(".godot/"):
        continue
    sources.setdefault(n, s)

with open(out, "w", encoding="utf-8") as f:
    for p in sorted(sources):
        f.write(f"{sources[p]:>12}  {p}\n")

by = defaultdict(lambda: [0, 0])
for p, s in sources.items():
    parts = p.split("/")
    key = "/".join(parts[:2]) if len(parts) > 2 else parts[0]
    by[key][0] += 1
    by[key][1] += s
print(f"pack {os.path.getsize(pack)/1e6:.0f} MB, {len(names)} entries, {len(sources)} source paths")
for k in sorted(by, key=lambda k: -by[k][1]):
    print(f"  {by[k][1]/1e6:9.1f} MB {by[k][0]:5d}  {k}")

excl = ["tools_scenes/*", "art/people/anime_female.glb", "art/people/her_Hair_*.glb",
        "art/people/woman.glb", "art/people/woman_mask.png", "art/people/hero.glb",
        "assets/characters/*", "assets/props/*", "assets/anim/humanoid.glb",
        "assets/ground/*.ktx2", "assets/people/*.bake.webp", "assets/env/polyhaven/*",
        "art/vo/*", "tests/*", ".shots/*"]
print("\nmust stay out:")
for e in excl:
    hits = [p for p in sources if fnmatch.fnmatch(p, e)]
    print(f"  {e}: {len(hits)} {'OK' if not hits else hits[:5]}")

# Every non-resource file the code reads with FileAccess: present in the project
# under art/ and data/, json/bin/png/txt that are not imported.
print("\nread with FileAccess (json/bin under art and data, and licences):")
missing = []
for root in ("art", "data", "licences"):
    for d, _, files in os.walk(os.path.join(proj, root)):
        for fn in files:
            rel = os.path.relpath(os.path.join(d, fn), proj).replace("\\", "/")
            if fn.endswith((".json", ".bin")) or root == "licences":
                if rel not in sources:
                    missing.append(rel)
print(f"  missing from the pack: {len(missing)}")
for m in missing[:80]:
    print("   ", m)
