"""Give new textures the import settings of a sibling (VRAM compressed, mipmapped), with no
remap paths, so Godot's next --import makes them as their siblings are made."""
import os
import re
import sys

WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a560452c597415545\godot"
pairs = [
    ("art/fx/fb/fire_loop.png.import", "art/fx/fb/watch_dial.png"),
    ("art/fx/marks/frost.png.import", "art/fx/marks/watch_dial.png"),
    ("art/fx/marks/frost_emit.png.import", "art/fx/marks/watch_dial_emit.png"),
    ("art/fx/marks/scorch.png.import", "art/fx/marks/smoulder.png"),
    ("art/fx/marks/scorch_emit.png.import", "art/fx/marks/smoulder_emit.png"),
]
for like, tex in pairs:
    text = open(os.path.join(WT, like), encoding="utf-8").read()
    params = text[text.index("[params]"):]
    head = '[remap]\n\nimporter="texture"\ntype="CompressedTexture2D"\n\n[deps]\n\nsource_file="res://%s"\n\n' % tex
    out = os.path.join(WT, tex + ".import")
    old = open(out, encoding="utf-8").read() if os.path.exists(out) else ""
    uid = re.search(r'^uid="[^"]+"', old, re.M)
    if uid:
        head = head.replace('type="CompressedTexture2D"\n', 'type="CompressedTexture2D"\n' + uid.group(0) + "\n")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(head + params)
    print("wrote", out)
