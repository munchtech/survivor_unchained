"""Many measured runs of one scenario, each with one thing changed, and a table of them.

    python tools/perf/sweep.py SCENARIO off  her,crowd,grass,...     # each taken out of the picture in turn (--perf-off)
    python tools/perf/sweep.py SCENARIO quality low,medium,high       # each quality
    python tools/perf/sweep.py SCENARIO scale native,quality,balanced,performance
    python tools/perf/sweep.py SCENARIO prop-cell 32,48,64,1000
    python tools/perf/sweep.py SCENARIO engine "--render-thread safe|--render-thread separate"
    python tools/perf/sweep.py SCENARIO flag "--merge-landmarks|--perf-off lamps"   # the game's own options, as given
    [--build DIR] [--wait S] [--tag T] [--repeat N]

A plain run (nothing changed) comes first, as the reference for the
differences. With --repeat, the whole set runs N times over, each set in
turn, so what else the machine is doing weighs on every case alike.
Results land beside run.py's (godot/.shots/perf).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run as R  # noqa: E402


def main():
    argv = sys.argv[1:]

    def opt(flag, default):
        if flag in argv:
            i = argv.index(flag)
            v = argv[i + 1]
            del argv[i:i + 2]
            return v
        return default

    build = opt("--build", None)
    wait = int(opt("--wait", "30"))
    tag = opt("--tag", "sw")
    repeat = int(opt("--repeat", "1"))
    scenario, kind, values = argv[0], argv[1], argv[2]
    sep = "|" if kind in ("engine", "flag") else ","
    rows = []
    cases = [("ref", [], "high", [])] if kind not in ("quality",) else []
    for v in values.split(sep):
        name = v.strip().replace(" ", "").replace("-", "")
        if kind == "off":
            cases.append((f"off_{name}", ["--perf-off", v], "high", []))
        elif kind == "quality":
            cases.append((f"q_{name}", [], v, []))
        elif kind == "scale":
            cases.append((f"s_{name}", ["--scale", v], "high", []))
        elif kind == "prop-cell":
            cases.append((f"cell{name}", ["--prop-cell", v], "high", []))
        elif kind == "engine":
            cases.append((f"eng_{name}", [], "high", v.split()))
        elif kind == "flag":
            cases.append((f"f_{name}", v.split(), "high", []))
    for rep in range(repeat):
        for label, extra, quality, engine in cases:
            R.ENGINE[:] = engine
            t = f"{tag}_{label}" + (str(rep) if repeat > 1 else "")
            print(f"{scenario} {t}", flush=True)
            r = R.run(scenario, t, "2560x1440", quality, extra, wait, build)
            if r:
                rows.append((t, r))
    print()
    R.table(rows)


if __name__ == "__main__":
    main()
