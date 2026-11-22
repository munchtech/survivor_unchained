"""Every long frame of a perf run, with where its time went (P2 task 5, frame pacing).

    python tools/perf/frames.py RUN.csv [RUN2.csv ...] [--budget 16.7] [--skip 5] [--list 40]

RUN.csv is a frames file written by --perf (src/Perf.cs). For each run it prints D1's
two frame criteria ("Zero frames over 16.7 ms in the run after the first 5 s; 99.9 % of
frames under 2 times the median frame time"), then every frame over the budget after
the first --skip seconds of the recording, with its cause read from the frame's cuts:

  main     the process callbacks (named by the biggest timed part: fx, player, sim ...)
  tail     the rest of the process step (message queue, deferred calls, skeletons)
  draw     the renderer's draw on the main thread (pipelines compiled in the frame are named)
  after    after the draw: the swap/present and input (a GPU wait shows here)
  phys     the physics steps
  gc       a collection ran in the frame (the runtime's pause falls in whichever cut it hit)

A frame's "ms" is the wall time from the previous frame's end; its cuts add up to about it.
Last, a table of causes: how many long frames each explains.
"""
import csv
import statistics
import sys

PARTS = ["sim", "player", "crowd", "fx", "hud", "sound", "zone", "events", "draft", "auto", "later", "draftui", "labels"]


def num(r, k):
    try:
        return float(r.get(k) or 0)
    except ValueError:
        return 0.0


def cause(r):
    cuts = {"main": num(r, "main"), "tail": num(r, "tail"), "draw": num(r, "draw"), "after": num(r, "after"), "phys": num(r, "phys_wall")}
    big = max(cuts, key=cuts.get)
    gc = int(num(r, "gen0") + num(r, "gen1") + num(r, "gen2"))
    pipes = int(num(r, "pipelines"))
    what = big
    if big == "main":
        parts = sorted(((num(r, p), p) for p in PARTS), reverse=True)
        named = parts[0][0]
        what = f"main:{parts[0][1]}" if named > 0.4 * cuts["main"] else "main:unparted"
    elif big == "draw" and pipes:
        what = "draw:pipelines"
    tags = []
    if gc:
        tags.append("gc" + "".join(g for g, k in (("0", "gen0"), ("1", "gen1"), ("2", "gen2")) if num(r, k)))
    if pipes:
        tags.append(f"pipes{pipes}")
    return what, tags, cuts


def one(path, budget, skip, listn):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        print(f"{path}: empty")
        return {}
    t0 = num(rows[0], "t")
    ms = [num(r, "ms") for r in rows]
    med = statistics.median(ms)
    after = [r for r in rows if num(r, "t") - t0 >= skip]
    longs = [r for r in after if num(r, "ms") > budget]
    under2 = sum(1 for r in rows if num(r, "ms") < 2 * med) / len(rows)
    srt = sorted(ms)
    p999 = srt[min(len(srt) - 1, int(0.999 * len(srt)))]
    print(f"== {path}")
    print(f"frames {len(rows)}  median {med:.2f} ms  mean {statistics.mean(ms):.2f}  p99.9 {p999:.1f}  max {max(ms):.1f}")
    print(f"D1 a: frames over {budget} ms after the first {skip:g} s: {len(longs)} of {len(after)} -> {'MET' if not longs else 'NOT MET'}")
    print(f"D1 b: frames under 2 x median ({2 * med:.2f} ms): {100 * under2:.2f}% (need 99.9) -> {'MET' if under2 >= 0.999 else 'NOT MET'}")
    over2 = sum(1 for r in rows if num(r, "ms") >= 2 * med)
    print(f"      frames at or over 2 x median: {over2}")
    table = {}
    print(f"{'t':>8} {'ms':>6} {'main':>5} {'tail':>5} {'draw':>5} {'after':>5} {'phys':>5} {'rcpu':>5} {'gpu':>5}  cause  [tags]  top parts")
    for r in sorted(longs, key=lambda r: -num(r, "ms"))[:listn]:
        what, tags, c = cause(r)
        parts = sorted(((num(r, p), p) for p in PARTS), reverse=True)[:3]
        ps = " ".join(f"{p} {v:.1f}" for v, p in parts if v >= 0.5)
        print(f"{num(r, 't'):8.2f} {num(r, 'ms'):6.1f} {c['main']:5.1f} {c['tail']:5.1f} {c['draw']:5.1f} {c['after']:5.1f} {c['phys']:5.1f} "
              f"{num(r, 'render_cpu'):5.1f} {num(r, 'gpu'):5.1f}  {what} [{' '.join(tags)}]  {ps}")
    for r in longs:
        what, tags, _ = cause(r)
        key = what + ("+gc" if any(t.startswith("gc") for t in tags) else "")
        table[key] = table.get(key, 0) + 1
    print("causes (frames over budget):")
    for k, v in sorted(table.items(), key=lambda kv: -kv[1]):
        print(f"  {v:5d}  {k}")
    # The near-misses: frames between 2 x median and the budget, by cause too (they fail D1 b).
    near = [r for r in rows if 2 * med <= num(r, "ms") <= budget]
    nt = {}
    for r in near:
        what, tags, _ = cause(r)
        key = what + ("+gc" if any(t.startswith("gc") for t in tags) else "")
        nt[key] = nt.get(key, 0) + 1
    if near:
        print(f"frames from 2 x median to the budget ({len(near)}), by cause:")
        for k, v in sorted(nt.items(), key=lambda kv: -kv[1])[:10]:
            print(f"  {v:5d}  {k}")
    return table


def main():
    a = sys.argv[1:]
    def opt(flag, d):
        if flag in a:
            i = a.index(flag)
            v = a[i + 1]
            del a[i:i + 2]
            return v
        return d
    budget = float(opt("--budget", "16.7"))
    skip = float(opt("--skip", "5"))
    listn = int(opt("--list", "40"))
    for p in a:
        one(p, budget, skip, listn)


if __name__ == "__main__":
    main()
