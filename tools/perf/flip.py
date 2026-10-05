"""A --perf-flip run read both ways: the frames with the thing in (flip 0)
against those with it out (flip 1), the first frames after each switch left
out (they carry the change itself: a pipeline, TAA settling).

    python tools/perf/flip.py RUN [RUN ...]       (godot/.shots/perf/RUN.csv)

For each column it prints in, out and out minus in, with the spread of that
difference across the flips (each in-second against the out-second after it),
so a busy GPU's drift shows as spread rather than as a result.
"""
import csv
import os
import statistics
import sys

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "godot", ".shots", "perf")
COLS = ["ms", "gpu", "render_cpu", "main", "draws", "shadow_draws", "primitives"]
SKIP = 6


def read(run):
    with open(os.path.join(OUT, run + ".csv"), encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    # Blocks of frames with the same flip state, each without its first frames.
    blocks, cur, state, since = [], [], None, 0
    for r in rows:
        s = int(float(r["flip"]))
        if s != state:
            if cur:
                blocks.append((state, cur))
            cur, state, since = [], s, 0
        since += 1
        if since > SKIP:
            cur.append(r)
    if cur:
        blocks.append((state, cur))
    return blocks


def main():
    for run in sys.argv[1:]:
        blocks = read(run)
        print(f"{run}: {len(blocks)} blocks")
        for c in COLS:
            ins = [float(r[c]) for s, b in blocks if s == 0 for r in b]
            outs = [float(r[c]) for s, b in blocks if s == 1 for r in b]
            if not ins or not outs:
                continue
            # Paired: each in-block against the out-block after it.
            pairs = [statistics.mean(float(r[c]) for r in blocks[i + 1][1]) - statistics.mean(float(r[c]) for r in blocks[i][1])
                     for i in range(len(blocks) - 1) if blocks[i][0] == 0 and blocks[i][1] and blocks[i + 1][1]]
            spread = f" (pairs: median {statistics.median(pairs):+.3f}, quartiles {statistics.quantiles(pairs, n=4)[0]:+.3f} to {statistics.quantiles(pairs, n=4)[2]:+.3f}, n {len(pairs)})" if len(pairs) >= 4 else ""
            mi, mo = statistics.mean(ins), statistics.mean(outs)
            print(f"  {c:13} in {mi:10.3f}  out {mo:10.3f}  out-in {mo - mi:+9.3f}{spread}")


if __name__ == "__main__":
    main()
