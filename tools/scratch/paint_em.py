"""Paint emblems over their guides (existing guides reused) at several denoises, one graph."""
import os
import sys
import time

WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a1a394643aabfb169"
sys.path.insert(0, os.path.join(WT, "tools", "uiforge"))
import emblems  # noqa: E402
import krea  # noqa: E402

seed = int(sys.argv[1])
dns = [float(x) for x in sys.argv[2].split(",")]
n = int(sys.argv[3])
keys = sys.argv[4:] or list(emblems.DESIGNS)
SCH = {}
for k in keys:
    if not os.path.exists(os.path.join(emblems.RAW, f"{k}_guide.png")):
        emblems.make_guide(k)
jobs = []
for k in keys:
    school = emblems.DESIGNS[k].__doc__ and None
    jobs_school = None
for k in keys:
    # The school without remaking the guide: read it from the design's first line.
    import inspect
    src = inspect.getsource(emblems.DESIGNS[k])
    school = src.split('Emblem("')[1].split('"')[0]
    for dn in dns:
        jobs.append((f"em_{k}_{int(round(dn * 100))}", os.path.join(emblems.RAW, f"{k}_guide.png"), emblems.prompt(k, school), dn, seed))
t = time.time()
res = krea.i2i_many(jobs, n=n, out=emblems.RAW)
print(len(res), "jobs", f"{time.time() - t:.0f}s")
import json  # noqa: E402
import urllib.request  # noqa: E402
req = urllib.request.Request("http://127.0.0.1:8188/free", data=json.dumps({"unload_models": True, "free_memory": True}).encode(),
                             headers={"Content-Type": "application/json"})
urllib.request.urlopen(req).read()
print("freed")
