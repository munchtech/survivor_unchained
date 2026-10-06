"""Rename the placeholder work files made before they were keyed by what was
asked (p0_c0_r1.wav -> p0_c0_r1_<key>.wav), for lines whose direction has not
changed since, so the run does not act them again."""
import os
import sys

sys.path.insert(0, os.path.abspath("tools/vo"))
import lines as lines_mod  # noqa: E402
import placeholders as ph  # noqa: E402

CHANGED = ("dlg.cin_none_cross.", "dlg.cin_heart_goes_down.", "cbark.f7a2a69e2307")
man = lines_mod.merge(lines_mod.build())
moved = skipped = 0
for l in man:
    folder = os.path.join(ph.FOLDER, l["id"])
    if l["status"] == "skip" or not os.path.isdir(folder):
        continue
    if l["id"].startswith(CHANGED):
        skipped += 1
        continue
    for rnd in (1, 2, 3):
        try:
            jobs = ph.segment_jobs(l, rnd)
        except KeyError:
            continue
        for j in jobs:
            pairs = [(os.path.join(folder, f"p{j['part']}_c{k}_r{rnd}.wav"), c["out"]) for k, c in enumerate(j["chunks"])]
            pairs += [(os.path.join(folder, f"p{j['part']}_perf_r{rnd}.wav"), j["perf"]),
                      (os.path.join(folder, f"p{j['part']}_vc_r{rnd}.wav"), j["vc"])]
            for old, new in pairs:
                if os.path.exists(old) and not os.path.exists(new):
                    os.rename(old, new)
                    moved += 1
print(f"renamed {moved} files; left {skipped} changed lines to be acted again")
