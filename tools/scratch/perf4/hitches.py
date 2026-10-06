"""The hitches of perf runs: python hitches.py FILE.json [FILE.json ...]"""
import json
import sys

for path in sys.argv[1:]:
    r = json.load(open(path, encoding="utf-8"))
    print(f"== {path.split(chr(92))[-1].split('/')[-1]}: mean {r.get('ms_mean'):.2f} ms, max {r.get('ms_max')}, gc {r.get('gc')}, {len(r.get('hitches', []))} hitches")
    for h in r.get("hitches", [])[:25]:
        print("  " + h)
