import json
import os
import sys
import time
import urllib.request

WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a1a394643aabfb169"
sys.path.insert(0, os.path.join(WT, "tools", "uiforge"))
import items  # noqa: E402

seed = int(sys.argv[1])
n = int(sys.argv[2])
keys = sys.argv[3:] or list(items.T2I)
t = time.time()
res = items.t2i(keys, seed=seed, n=n)
print({k: len(v) for k, v in res.items()}, f"{time.time() - t:.0f}s")
req = urllib.request.Request("http://127.0.0.1:8188/free", data=json.dumps({"unload_models": True, "free_memory": True}).encode(),
                             headers={"Content-Type": "application/json"})
urllib.request.urlopen(req).read()
print("freed")
