import sys
from pathlib import Path
sys.argv = ["x"]
exec(open(Path(__file__).with_name("stance.py")).read().split("if args and")[0].replace("Path(__file__)", f"Path(r'{Path(__file__).with_name('stance.py')}')"))
from keyed import Rig
from clips import idle
from rig import qangle
rig = Rig(sk, body="her")
base = idle.base_of(rig, "stalker")
gb, pb = sk.fk(base.rot, base.pos)
for n in ("idle_stalker", "idle_stalker_break"):
    r, p = load(n); g, pp = sk.fk(r, p)
    for f in (0, 30, 100):
        print(n, f, [round(qangle(qmul(qinv(gb[f, sk.i(f"foot_{s}")]), g[f, sk.i(f"foot_{s}")])), 2) for s in "lr"],
              "base foot vs base f0", [round(qangle(qmul(qinv(gb[0, sk.i(f"foot_{s}")]), gb[f, sk.i(f"foot_{s}")])), 2) for s in "lr"])
