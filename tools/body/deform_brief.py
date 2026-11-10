"""deform_brief: audit.json (deform_audit) boiled down to the lead's tables: per region B vs A over the library clips
(worst and median of each clip's worst frame), the layers' deltas, the walk and run, the ROM break angles, L/R symmetry.

    python tools/body/deform_brief.py [tools/body/out/audit/audit.json] [> brief.txt]
"""
import json
import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from deform_audit import CLIPMET, MET, OUT  # noqa: E402

A = json.loads(Path(sys.argv[1] if len(sys.argv) > 1 else OUT / "audit.json").read_text())
C, R = A["clips"], A["rom"]
ROWS = ["shoulder_{s}", "shoulder_{s}.deltoid", "shoulder_{s}.axilla", "clav_{s}", "elbow_{s}", "forearm_{s}", "wrist_{s}",
        "hip_{s}", "hip_{s}.front", "hip_{s}.glute", "hip_{s}.groin", "knee_{s}", "knee_{s}.front", "knee_{s}.back",
        "ankle_{s}", "neck", "trunk", "trunk.core"]
dumps = sorted(c for c in C["B.full"] if not c.startswith("p4:"))
p4 = sorted(c for c in C["B.full"] if c.startswith("p4:"))


def per_clip(col, rg, m, names):
    """[(value, clip, frame)] : each clip's worst (both sides)."""
    i, out = CLIPMET.index(m), []
    for n in names:
        e = C.get(col, {}).get(n)
        if not e:
            continue
        v = [(e["regions"][r][i][0], n, e["regions"][r][i][1]) for r in {rg.replace("{s}", s) for s in "lr"} if r in e["regions"]]
        if v:
            out.append(max(v))
    return out


def wm(col, rg, m, names):
    v = per_clip(col, rg, m, names)
    return (max(v)[0], float(np.median([x[0] for x in v])), max(v)) if v else (0, 0, (0, "-", 0))


def slide(rg):
    return "sb95" if rg.endswith("deltoid") or rg.startswith("clav") else "slide95"


print("== CLIPS (33 dumps): worst/median over clips of each clip's worst frame. st99% bad% flip% kink99deg ins_mm slide(sb95 for deltoid, clav)mm pop99")
for rg in ROWS:
    ms = ["st99", "bad", "flip", "kink99", "ins_mm", slide(rg), "pop99"]
    line = [f"{rg.replace('_{s}', ''):16s}"]
    for col in ("B.full", "A.full"):
        line.append(col[0] + " " + " ".join("{:.3g}/{:.3g}".format(*wm(col, rg, m, dumps)[:2]) for m in ms))
    for col in ("B.nocorr", "B.nolaws", "Bplay.full"):
        line.append(col.split(".")[0][1:] + col.split(".")[1][:3] + " d " + " ".join(
            "{:+.3g}".format(wm(col, rg, m, dumps)[0] - wm("B.full", rg, m, dumps)[0]) for m in ("st99", "bad", "flip", "ins_mm", slide(rg))))
    w = max(per_clip("B.full", rg, "flip", dumps) + [(0, "-", 0)])
    w = w if w[0] > 0 else wm("B.full", rg, "bad", dumps)[2]
    line.append(f"worst {w[1]}@{w[2]}")
    if p4:
        line.append("p4 " + " ".join("{:.3g}".format(wm("B.full", rg, m, p4)[0]) for m in ("st99", "bad", "flip", "ins_mm", slide(rg), "pop99"))
                    + " " + wm("B.full", rg, "bad", p4)[2][1][3:])
    print(" | ".join(line))

print("\n== WALK / RUN: st99 bad flip kink99 slide95(sb95) pop99, worst side")
for clip, cols in (("p4:walk_warden", ["B.full", "Bplay.full"]), ("p4:run_warden", ["B.full", "Bplay.full"]),
                   ("Jog_Fwd", ["B.full", "A.full"]), ("run_warden", ["B.full", "A.full"])):
    for rg in ("knee_{s}", "knee_{s}.back", "hip_{s}", "hip_{s}.glute", "ankle_{s}", "shoulder_{s}", "shoulder_{s}.deltoid", "shoulder_{s}.axilla"):
        print(f"{clip:16s} {rg.replace('_{s}', ''):16s} " + " | ".join(
            c + " " + " ".join("{:.3g}".format(wm(c, rg, m, [clip])[0]) for m in ("st99", "bad", "flip", "kink99", slide(rg), "pop99")) for c in cols))

print("\n== axilla at_mm / ins_mm (arm under the torso skin), B.full p4 and worst dump; A.full worst dump")
for n in p4:
    print(n, "at_mm {:.3g} ins_mm {:.3g}".format(wm("B.full", "shoulder_{s}.axilla", "at_mm", [n])[0], wm("B.full", "shoulder_{s}.axilla", "ins_mm", [n])[0]))
for col in ("B.full", "A.full"):
    w = wm(col, "shoulder_{s}.axilla", "at_mm", dumps)
    print(col, "dumps at_mm worst/median {:.3g}/{:.3g}".format(*w[:2]), f"{w[2][1]}@{w[2][2]}")


def rom_row(col, pose, rg):
    v = [e["regions"][rg.replace("{s}", k.split("|")[1])] for k, e in R.get(col, {}).items()
         if k.split("|")[0] == pose and rg.replace("{s}", k.split("|")[1]) in e["regions"]]
    g = [e["girth"][0] for k, e in R.get(col, {}).items() if k.split("|")[0] == pose and e.get("girth")]
    return (max(v, key=lambda r: r[MET.index("flip")] * 10 + r[MET.index("bad")]) if v else None), (min(g) if g else 1.0)


print("\n== ROM: st99/bad/flip/kink99/ins_mm/slide95 [girth min]; * = broken (bad > 5 or flip > 0.5 or girth < 0.85)")
poses = list(dict.fromkeys(k.split("|")[0] for k in R["B.full"]))
for ps in poses:
    e = next(e for k, e in R["B.full"].items() if k.split("|")[0] == ps)
    rg = next(iter(e["regions"]))
    rg = re.sub(r"_[lr](?=$|\.)", "_{s}", rg)
    cells = []
    for col in ("B.full", "B.nocorr", "B.nolaws", "Bplay.full", "A.full", "A.nocorr"):
        r, g = rom_row(col, ps, rg)
        if r is None:
            cells.append("-")
            continue
        brk = r[MET.index("bad")] > 5 or r[MET.index("flip")] > 0.5 or g < 0.85
        cells.append(("*" if brk else "") + "/".join(f"{r[MET.index(m)]:.3g}" for m in ("st99", "bad", "flip", "kink99", "ins_mm", "slide95")) + f" g{g:.2f}")
    print(f"{ps:15s} " + " | ".join(cells))

print("\n== ROM slide_bone (deltoid sb50/sb95/sbmax, clav sb95) B.full | A.full")
for ps in [p for p in poses if p.startswith("sh_")]:
    out = []
    for col in ("B.full", "A.full"):
        d, _ = rom_row(col, ps, "shoulder_{s}.deltoid")
        c, _ = rom_row(col, ps, "clav_{s}")
        i = MET.index("sb50")
        out.append(f"{col[0]} delt {d[i]:.3g}/{d[i + 1]:.3g}/{d[i + 2]:.3g} clav {c[i + 1]:.3g} at_mm " + "{:.3g}".format(rom_row(col, ps, "shoulder_{s}.axilla")[0][MET.index("at_mm")]))
    print(f"{ps:12s} " + " | ".join(out))

print("\n== L/R on B.full ROM (st99 of the first region; signed poses mirrored): the largest relative gaps")
gap = []
for k, e in R["B.full"].items():
    ps, s = k.split("|")
    if s != "l":
        continue
    m = re.sub(r"([+-])(\d+)$", lambda x: ("-" if x.group(1) == "+" else "+") + x.group(2), ps) if re.search(r"(twist|pronate|wrist_flex|hip_rot|ankle_inv)", ps) else ps
    o = R["B.full"].get(f"{m}|r")
    if not o:
        continue
    for (ra, a), (rb, b) in zip(e["regions"].items(), o["regions"].items()):
        for mt in ("st99", "bad", "slide95"):
            x, y = a[MET.index(mt)], b[MET.index(mt)]
            gap.append((abs(x - y) / max(x, y, 1.0), ps, ra, mt, x, y))
for g in sorted(gap, reverse=True)[:8]:
    print("{:.0%} {} {} {} L {:.3g} R {:.3g}".format(*g))
