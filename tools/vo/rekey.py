"""Carry directions over to lines whose words changed.

A line spoken from the game's code is known by the hash of its words
(`say.<hash>`), so a rewrite gives it a new id and leaves its direction
behind. This finds each orphaned direction's line again (the same source
file, the closest words, nothing else claiming it) and moves the direction
to the new id, keeping the old words beside it so a reviewer can see what
changed. Run it after the writing changes, before recording.

    python tools/vo/rekey.py            # report
    python tools/vo/rekey.py --apply [--old=<an earlier manifest.json>]
"""
import difflib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lines as lines_mod  # noqa: E402

DIRECTION = os.path.join(os.path.dirname(os.path.abspath(__file__)), "direction")


def main(argv):
    apply = "--apply" in argv
    built = lines_mod.build()
    ids = {l["id"] for l in built}
    files = {f: json.load(open(os.path.join(DIRECTION, f), encoding="utf-8")) for f in os.listdir(DIRECTION) if f.endswith(".json")}
    directed = {k for d in files.values() for k in d}
    old_text = {}
    old_path = next((a.split("=", 1)[1] for a in argv if a.startswith("--old=")), lines_mod.MANIFEST)
    if os.path.exists(old_path):
        old_text = {l["id"]: (l["text"], l.get("where", "")) for l in json.load(open(old_path, encoding="utf-8"))["lines"]}
    free = [l for l in built if l["id"] not in directed and not l.get("skip") and l["id"].split(".")[0] in ("say", "cbark")]
    moved = 0
    for f, d in files.items():
        for k in list(d):
            if k in ids or not k.startswith(("say.", "cbark.")) or k not in old_text:
                continue
            text, where = old_text[k]
            cands = [(difflib.SequenceMatcher(None, text, l["text"]).ratio(), l) for l in free if l.get("where") == where]
            if not cands:
                print(f"{k}: no line left in {where}")
                continue
            score, best = max(cands, key=lambda c: c[0])
            if score < 0.6:
                print(f"{k}: nothing close enough ({score:.2f}) for {text[:60]!r}")
                continue
            print(f"{k} -> {best['id']} ({score:.2f})\n   was: {text[:110]}\n   now: {best['text'][:110]}")
            free.remove(best)
            moved += 1
            if apply:
                v = d.pop(k)
                v["was"] = text
                d[best["id"]] = v
    if apply and moved:
        for f, d in files.items():
            with open(os.path.join(DIRECTION, f), "w", encoding="utf-8", newline="\n") as fh:
                fh.write("{\n" + ",\n".join(f" {json.dumps(k)}: {json.dumps(v, ensure_ascii=False)}" for k, v in d.items()) + "\n}\n")
    print(f"{moved} directions {'moved' if apply else 'to move'}")


if __name__ == "__main__":
    main(sys.argv[1:])
