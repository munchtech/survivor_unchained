"""Show lines (exact ids) with their direction notes and beats."""
import os
import sys

sys.path.insert(0, os.path.abspath("tools/vo"))
import lines as lines_mod  # noqa: E402

want = set(sys.argv[1:])
for l in lines_mod.merge(lines_mod.build()):
    if l["id"] in want:
        d = l.get("direction") or {}
        print(f"== {l['id']} [{l['voice']}]\n  TEXT: {l['text']}\n  EMO: {d.get('emo')} | NOTE: {d.get('note')}\n  BEATS: {d.get('beats')}")
