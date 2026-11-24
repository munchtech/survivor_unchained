"""Memory A/B legs on an exported build, one after another (the tester lane, 23 Nov): each leg starts the game standing in the
den (the den test's own start, plus the leg's switches) and samples it with tools/perf/memrun.py.

    python tools/perf/memmatrix.py EXE OUT_DIR SECONDS LEG [LEG ...]

LEG: name=switches, the switches split on '+' ("base=", "headless=--headless", "nowarm=--no-fx-warm"). Engine switches go
before the game's '--'; a leg's switches after a ':' are the game's ("gl=--rendering-driver+opengl3", "x=:--no-fx-warm").
Take a godot turn first (tools/turn.py run). Prints one memrun line per leg.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEN = ["--quick", "warden", "--sex", "female", "--zone", "map", "--dungeon", "hollow", "--veteran", "9", "--seed", "1", "--mem-log", "10"]


def main():
    exe, out, secs, legs = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]
    for leg in legs:
        name, _, sw = leg.partition("=")
        eng, _, game = sw.partition(":")
        cmd = [sys.executable, os.path.join(HERE, "memrun.py"), os.path.join(out, name), secs, exe]
        cmd += [a for a in eng.split("+") if a] + ["--"] + DEN + [a for a in game.split("+") if a]
        r = subprocess.run(cmd, capture_output=True, text=True)
        print(f"{name}: {r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-300:]}", flush=True)


if __name__ == "__main__":
    main()
