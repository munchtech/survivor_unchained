"""Write Godot .import files for new UI icons, as the editor would (a sibling's settings, the
res path's md5 in the imported name, a fresh uid in Godot's alphabet, unique in the project).

    python uiart_imports.py PROJECT_GODOT_DIR OUT_DIR rel/a.png rel/b.png ...
"""
import hashlib
import os
import re
import secrets
import sys

proj, out, rels = sys.argv[1], sys.argv[2], sys.argv[3:]
TEMPLATE = open(os.path.join(proj, "art/ui/icons/item/pelt.png.import"), encoding="utf-8").read()
taken = set()
for root, _, files in os.walk(proj):
    if ".godot" in root:
        continue
    for f in files:
        if f.endswith((".import", ".uid", ".tscn", ".tres")):
            try:
                taken.update(re.findall(r"uid://([a-z0-9]+)", open(os.path.join(root, f), encoding="utf-8", errors="ignore").read()))
            except OSError:
                pass


def uid():
    # ResourceUID::id_to_text: base 34, 'a'..'y' then '0'..'8', of a 63-bit id.
    while True:
        n = secrets.randbits(63)
        s = ""
        while True:
            c = n % 34
            s = (chr(ord("a") + c) if c < 25 else chr(ord("0") + c - 25)) + s
            n //= 34
            if not n:
                break
        if s not in taken:
            taken.add(s)
            return s


os.makedirs(out, exist_ok=True)
for rel in rels:
    res = "res://" + rel.replace("\\", "/")
    name = os.path.basename(rel)
    dest = f"res://.godot/imported/{name}-{hashlib.md5(res.encode()).hexdigest()}.ctex"
    text = re.sub(r'uid="uid://[a-z0-9]+"', f'uid="uid://{uid()}"', TEMPLATE)
    text = re.sub(r'path="res://\.godot/imported/[^"]+"', f'path="{dest}"', text)
    text = re.sub(r'source_file="[^"]+"', f'source_file="{res}"', text)
    text = re.sub(r'dest_files=\["[^"]+"\]', f'dest_files=["{dest}"]', text)
    p = os.path.join(out, name + ".import")
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(p)
print(len(taken), "uids in use checked")
