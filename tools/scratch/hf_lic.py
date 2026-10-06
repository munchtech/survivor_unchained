import json
import sys
import urllib.request

for r in sys.argv[1:]:
    try:
        d = json.load(urllib.request.urlopen(f"https://huggingface.co/api/models/{r}", timeout=30))
        c = d.get("cardData") or {}
        print(r, "|", c.get("license"), "|", c.get("license_name"), "|", c.get("base_model"), "| gated", d.get("gated"))
    except Exception as e:
        print(r, "ERR", e)
