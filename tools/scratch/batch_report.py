"""A summary of the placeholders made so far: counts, faults, and the timed lines."""
import json
from collections import Counter

m = json.load(open("tools/vo/manifest.json", encoding="utf-8"))["lines"]
done = [l for l in m if (l.get("take") or {}).get("placeholder") and l["status"] == "done"]
print(f"{len(done)} placeholders; by voice: {dict(Counter(l['voice'] for l in done).most_common())}")
bad = [l for l in done if l["take"].get("faults")]
print(f"{len(bad)} with faults:")
for l in bad:
    print(f"  {l['id']}: {l['take']['faults'][:4]}")
print("timed lines:")
for l in m:
    d = l.get("direction") or {}
    if d.get("time"):
        t = l.get("take") or {}
        print(f"  {l['id']:42s} {l['status']:6s} read {t.get('read')} sec {t.get('sec')} want {d['time']} {t.get('timing', '')}")
