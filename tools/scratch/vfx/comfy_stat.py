"""ComfyUI's queue, its VRAM and the machine's free RAM: python comfy_stat.py [free]"""
import json
import sys
import urllib.request

URL = "http://127.0.0.1:8188"


def get(path):
    return json.load(urllib.request.urlopen(URL + path, timeout=5))


try:
    q = get("/queue")
    print("running", len(q["queue_running"]), "pending", len(q["queue_pending"]))
    for item in q["queue_running"] + q["queue_pending"]:
        # A prompt's own text, to tell whose it is.
        texts = [str(n.get("inputs", {}).get("text", n.get("inputs", {}).get("value", "")))[:70] for n in item[2].values()
                 if isinstance(n, dict) and ("text" in n.get("inputs", {}) or isinstance(n.get("inputs", {}).get("value"), str))]
        print("  ", item[1][:8], [t for t in texts if t][:2])
    s = get("/system_stats")
    print("ram free GB", round(s["system"]["ram_free"] / 2**30, 1), "of", round(s["system"]["ram_total"] / 2**30, 1))
    for d in s["devices"]:
        print("vram free MB", d["vram_free"] // 2**20, "of", d["vram_total"] // 2**20, "torch free", d.get("torch_vram_free", 0) // 2**20)
    # Freed only when nothing of anyone's is queued: freeing under another lead's job makes it
    # load its models again.
    if len(sys.argv) > 1 and sys.argv[1] == "free" and (q["queue_running"] or q["queue_pending"]):
        print("not freed: the queue is busy")
    elif len(sys.argv) > 1 and sys.argv[1] == "free":
        req = urllib.request.Request(URL + "/free", data=json.dumps({"unload_models": True, "free_memory": True}).encode(),
                                     headers={"Content-Type": "application/json"}, method="POST")
        urllib.request.urlopen(req, timeout=10)
        print("freed")
except Exception as e:
    print("comfy:", e)
