"""Try a board's prompt at several denoise levels over its staging, in a scratch id (not committed).
python btest.py CID SHOT d1,d2,... "prompt with {names}" [seed]"""
import json, os, shutil, subprocess, sys
W = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a79b6d8c81e14dc63"
cid, shot, ds, prompt = sys.argv[1], sys.argv[2], sys.argv[3].split(","), sys.argv[4]
seed = int(sys.argv[5]) if len(sys.argv) > 5 else 4000
boards = os.path.join(W, "docs", "cinematics", "shoot", "boards")
spec = json.load(open(os.path.join(boards, f"{cid}.json"), encoding="utf-8"))
tid = "_t"
os.makedirs(os.path.join(W, "tools", "comfy", "out", "staging", tid), exist_ok=True)
shots = {}
for i, d in enumerate(ds):
    key = f"{shot}d{d.replace('.', '')}"
    shutil.copy(os.path.join(W, "tools", "comfy", "out", "staging", cid, f"s{shot}.png"),
                os.path.join(W, "tools", "comfy", "out", "staging", tid, f"s{key}.png"))
    shots[key] = {"prompt": prompt, "from": "staging", "denoise": float(d)}
t = {"seed": seed, "people": spec.get("people", {}), "shots": shots}
json.dump(t, open(os.path.join(boards, f"{tid}.json"), "w", encoding="utf-8"), indent=1)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"bt_{cid}_{shot}.jpg")
subprocess.run([sys.executable, os.path.join(W, "tools", "cinematics", "boards.py"), tid, "--force", "--sheet", out], check=True)
print(out)
