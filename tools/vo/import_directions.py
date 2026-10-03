"""Take direction written elsewhere for lines that have none here.

The cloud voice pass (branch claude/cloud-voice, tools/voice/directions.json
and godot/data/voice/lines.json) directed every line of the merged writing,
keyed by its own ids but hashed exactly as here (the first 12 hex digits of
the SHA-1 of the words as written). Matched by that hash, its emotion,
intensity, pace, wants and notes become direction/imported.json for every
line that has no hand direction in tools/vo/direction; lines directed here
keep theirs.

    python tools/vo/import_directions.py <lines.json> [<directions.json>]
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as lines_mod  # noqa: E402


def pace_word(p: str) -> str:
    p = p.lower()
    for k in ("very slow", "slow", "quick", "fast", "brisk", "rushed"):
        if k in p:
            return {"fast": "quick", "rushed": "quick"}.get(k, k)
    return "measured"


def vol_word(text: str) -> str:
    t = text.lower()
    if re.search(r"whisper|hushed|barely voiced|under (his|her) breath", t):
        return "hushed"
    if re.search(r"shout|bellow|roar|yell", t):
        return "shout"
    if re.search(r"raised|loud|calling out", t):
        return "raised"
    if re.search(r"\bquiet|\blow\b|soft|gentle|close", t):
        return "quiet"
    return "level"


def main(argv):
    src = json.load(open(argv[0], encoding="utf-8"))
    by_hash = {}
    for l in src["lines"]:
        d = l.get("direction") or {}
        if d.get("emotion"):
            by_hash.setdefault(l["hash"], d)
    if len(argv) > 1:
        for k, d in json.load(open(argv[1], encoding="utf-8")).items():
            if isinstance(d, dict) and d.get("hash") and d.get("emotion"):
                by_hash.setdefault(d["hash"], d)
    mine = lines_mod.load_directions()
    out = {}
    for l in lines_mod.build():
        if l.get("skip") or l["id"] in mine:
            continue
        d = by_hash.get(l["hash"])
        if not d:
            continue
        words = " ".join([d.get("pace", ""), d.get("notes", ""), d.get("emotion", "")])
        out[l["id"]] = {"emo": d["emotion"], "intent": d.get("wants", ""), "pace": pace_word(d.get("pace", "")),
                        "vol": vol_word(words), "wants": d.get("wants", ""), "note": d.get("notes", ""),
                        "intensity": d.get("intensity"), "from": "cloud voice pass"}
    dst = os.path.join(HERE, "direction", "imported.json")
    json.dump(out, open(dst, "w", encoding="utf-8", newline="\n"), indent=1, ensure_ascii=False)
    print(f"{len(out)} lines directed from the cloud pass -> {os.path.relpath(dst)}")


if __name__ == "__main__":
    main(sys.argv[1:])
