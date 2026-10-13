"""A blend's images whose files are gone (worktrees removed since it was saved) found again by name and packed in.

    blender -b X.blend --python tools/assets/blend_relink.py -- [--dry] DIR [DIR ...]

Each image not packed and not on disk is looked for by its file name in the DIRs, in order (default: this checkout's
godot/art/people/head_tex), then the blend's images are all packed and the blend saved. Unfound ones are named and
left as they are. (heroine_built.blend linked heroine_graft.jpg in a removed worktree: exported without it, the graft
on her neck, shoulders and upper chest came out unpainted, pale, with a ragged edge across her breasts: the outfits
lead's chest close-ups, 11 October 2026.)
"""
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
dry = "--dry" in args
dirs = [a for a in args if a != "--dry"] or [os.path.join(HERE, "..", "..", "godot", "art", "people", "head_tex")]
missing = 0
for im in bpy.data.images:
    if im.packed_file or im.source != "FILE":
        continue
    p = bpy.path.abspath(im.filepath)
    if os.path.exists(p):
        continue
    name = os.path.basename(p.replace("\\", "/"))
    found = next((os.path.join(d, name) for d in dirs if os.path.exists(os.path.join(d, name))), None)
    print("MISSING %s (%s) -> %s" % (im.name, p, found))
    missing += 1
    if found and not dry:
        im.filepath = os.path.abspath(found)
        im.reload()
if not dry:
    for im in bpy.data.images:
        if not im.packed_file and im.source == "FILE" and os.path.exists(bpy.path.abspath(im.filepath)):
            im.pack()
    bpy.ops.wm.save_mainfile()
print("RELINK: %d missing; %s" % (missing, "dry run" if dry else "packed and saved"))
