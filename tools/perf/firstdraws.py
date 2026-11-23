"""(P2 task 5, session 3) The first-draw check on a --perf run's log: exit 1 when a pipeline was compiled in play after the
place's warm-up (FxWarm), 0 when none was, 2 when the check never armed. Prints Perf's verdict line and each in-play first
draw (time, frame ms, pipelines by kind c/m/s/d/sp, what entered the tree that frame), over-budget ones marked.

usage: python tools/perf/firstdraws.py RUN.log [--budget 16.7]
"""
import re
import sys


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 2
    budget = float(args[args.index("--budget") + 1]) if "--budget" in args else 16.7
    lines = open(args[0], encoding="utf-8", errors="replace").read().splitlines()
    verdict = [l for l in lines if l.startswith("perf first draws:")]
    warm = [l for l in lines if l.startswith("load: fx warm-up")]
    rows = []
    for l in lines:
        m = re.match(r"perf first draw in play ([\d.]+)s frame ([\d.]+) ms, pipelines c/m/s/d/sp ([\d/]+); new: (.*)", l)
        if m:
            rows.append((float(m.group(1)), float(m.group(2)), m.group(3), m.group(4)))
    for l in warm:
        print(l)
    for t, ms, kinds, new in rows:
        print(f"{'OVER' if ms > budget else '    '} {t:8.2f}s {ms:7.1f} ms  pipes {kinds:12}  {new[:200]}")
    for l in verdict:
        print(l)
    if not any("watched from" not in v for v in verdict) or any("NOT ARMED" in v for v in verdict):
        return 2
    return 0 if not rows else 1


if __name__ == "__main__":
    sys.exit(main())
