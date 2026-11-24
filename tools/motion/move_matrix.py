"""The movement fixes' before/after matrix (GAME_PLAN tasks 3, 4): each step is a set of --moves12 takes run with a
set of fix flags into its own folder under godot/.shots, then that folder's table.

  python tools/motion/move_matrix.py STEP [--max N] [--redo]     run up to N (default 5) of the step's missing takes
  python tools/motion/move_matrix.py list                        the steps, and how many takes each still lacks
  python tools/motion/move_matrix.py compare BEFORE AFTER [OUT]  every number of two folders' tables side by side

A take already on disk (its ticks.csv) is skipped, so a step is called again until it prints "left: 0"; a call stays
under ten minutes at about 66 s a take. The next movement fix costs one line in STEPS and one call of its step.
"""
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SHOTS = ROOT / "godot" / ".shots"
KBM = "s01 s03 s04 s05 s06 s07 s08 s09 s10a s10b s10c s10d s10e s11 s12 s13".split()
PAD = "p01 p03 p08 p08b p10a p10b".split()
ALL = KBM + PAD
CAM = "s01 s03 s04 s13 p01 p03".split()
ROLL = "s08 s09 p08".split()
# name: (folder, flags, takes). The fixes are added one cause at a time, in the order of the baseline's worst numbers.
STEPS = {
    "before": ("mv_before", "--move-old", ALL),   # (new is the default since 23 Nov)
    "cam": ("mv_a_cam", "--move-old --move-cam-lock", CAM),
    "ramps": ("mv_bc_ramps", "--move-old --move-cam-lock --move-start 2 --move-stop 2", CAM + ["s05"]),
    "after": ("mv_after", "--move-new", ALL + ["s12d"]),
    "after_b": ("mv_after_b", "--move-new", ["s12d"]),
    "roll55": ("mv_roll55", "--move-new --move-roll 0.45", ROLL),
    "roll80": ("mv_roll80", "--move-new --move-roll 0.45 --move-roll-len 8.0", ROLL),
}


def missing(folder, takes):
    return [t for t in takes if not (SHOTS / folder / t / "ticks.csv").exists()]


def run(step, most, redo):
    folder, flags, takes = STEPS[step]
    todo = (takes if redo else missing(folder, takes))[:most]
    env = dict(os.environ, MOVES_OUT=folder, MOVES_FLAGS=flags, TURN_LABEL=f"move: {step}")
    if todo:
        subprocess.run([sys.executable, str(ROOT / "tools/motion/move_baseline.py"), ",".join(todo)], env=env, cwd=ROOT)
    left = missing(folder, takes)
    if not left:
        subprocess.run([sys.executable, str(ROOT / "tools/motion/move_baseline_table.py")], env=env, cwd=ROOT, stdout=subprocess.DEVNULL)
        print(f"table: {SHOTS / folder / 'TABLE.md'}")
    print(f"{step}: ran {len(todo)} ({' '.join(todo) or 'none'}), left: {len(left)} {' '.join(left)}")


def rows(folder):
    """A TABLE.md's 'row: a=b, c=d' lines as {row: {a: b}} (a row seen twice, the s12d stops, gets #2, #3...)."""
    out, seen = {}, {}
    p = SHOTS / folder / "TABLE.md"
    for line in p.read_text(encoding="utf-8").splitlines() if p.exists() else []:
        m = re.match(r"^([a-z0-9 ]+): (.*=.*)$", line)
        if not m: continue
        k = m.group(1); seen[k] = seen.get(k, 0) + 1
        if seen[k] > 1: k = f"{k} #{seen[k]}"
        out[k] = dict(x.split("=", 1) for x in m.group(2).split(", ") if "=" in x)
    return out


def compare(before, after, out):
    a, b = rows(before), rows(after)
    lines = [f"# Movement: {before} (old) against {after} (new)", "", "| take | number | old | new |", "|---|---|---|---|"]
    for k in a:
        if k not in b: continue
        for name, old in a[k].items():
            new = b[k].get(name, "")
            mark = "" if old == new else " *"
            lines.append(f"| {k} | {name} | {old} | {new}{mark} |")
    for folder in (before, after):
        p = SHOTS / folder / "TABLE.md"
        rule = [l for l in p.read_text(encoding="utf-8").splitlines() if "follow the rule" in l or ": held " in l] if p.exists() else []
        lines += ["", f"## Dash rule, {folder}"] + [f"- {l}" for l in rule]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out} ({len(lines)} lines; * = changed)")


def main():
    a = sys.argv[1:]
    if not a or a[0] == "list":
        for s, (folder, flags, takes) in STEPS.items():
            print(f"{s}: {folder} [{flags or 'no flags'}] {len(takes)} takes, left {len(missing(folder, takes))}")
    elif a[0] == "compare":
        compare(a[1], a[2], Path(a[3]) if len(a) > 3 else SHOTS / a[2] / f"OLD_NEW_{a[1]}.md")
    else:
        most = int(a[a.index("--max") + 1]) if "--max" in a else 5
        run(a[0], most, "--redo" in a)


if __name__ == "__main__":
    main()
