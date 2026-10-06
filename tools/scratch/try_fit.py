"""Try produce.fit on existing placeholder takes (no GPU)."""
import os
import sys

sys.path.insert(0, os.path.abspath("tools/vo"))
import lines as lines_mod  # noqa: E402
import produce  # noqa: E402

man = {l["id"]: l for l in lines_mod.merge(lines_mod.build())}
for lid in sys.argv[1:]:
    l = man[lid]
    t = l.get("take") or {}
    picks = [{**p, "path": p["src"]} for p in t.get("parts", [])]
    if not picks:
        print(lid, "no take")
        continue
    for g in produce.FIT_GAPS:
        audio, marks, read = produce.mix(l, picks, g)
        print(f"{lid} gap {g}: read {read} s, file {len(audio) / 48000:.2f} s")
    a, m, read, g = produce.fit(l, picks)
    print("  fit ->", read, g, produce.timing(l, read))
