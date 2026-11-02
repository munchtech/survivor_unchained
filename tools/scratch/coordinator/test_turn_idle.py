import os, sys, json, time, tempfile
os.environ["TURN_HOME"] = tempfile.mkdtemp()
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
import turn
def run(samples, smi_ok=True, since_min=60):
    for p in turn.HOME.glob("gpu.*"):
        (p/"who.json").unlink(missing_ok=True); p.rmdir()
    d = turn.HOME/"gpu.0"; d.mkdir(parents=True, exist_ok=True)
    (d/"who.json").write_text(json.dumps({"who":"holder","since":time.time()-since_min*60}))
    now = time.time()
    (turn.HOME/"gpu_util.json").write_text(json.dumps([[now-m*60,u] for m,u in samples]))
    turn.gpu_util = (lambda: 0) if smi_ok else (lambda: None)
    return turn.try_take("gpu","waiter") is None
idle=[(m,1) for m in range(20,0,-2)]
assert run(idle) is True, "idle freed"
assert run(idle[:3]+[(10,50)]+idle[3:]) is False, "busy sample"
assert run([(3,0),(2,0),(1,0)]) is False, "too few"
assert run([(25,0),(2,0)]) is False, "gap"
assert run(idle, smi_ok=False) is False, "smi fail (stale samples >5min? latest 2min old ok) "
assert run(idle, since_min=10) is False, "young hold"
print("all ok")
