"""A person's lines as a recording script: each node with the replies that
lead to it, every variant with the condition it is said under, and the
current direction. For whoever directs the next session.

    python tools/vo/script.py rook [--out file.txt]
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lines import CONTENT, MANIFEST  # noqa: E402


def cond(c):
    return json.dumps(c, ensure_ascii=False, separators=(",", ":")) if c else ""


def main(npc, out=None):
    d = json.load(open(os.path.join(CONTENT, "dialogue.json"), encoding="utf-8"))[npc]
    man = {l["id"]: l for l in json.load(open(MANIFEST, encoding="utf-8"))["lines"]}
    leads = {}
    for nid, node in d["nodes"].items():
        for c in node.get("choices") or []:
            t = c["text"] if isinstance(c["text"], str) else c["text"][0]["text"]
            if c.get("goto"):
                leads.setdefault(c["goto"], []).append(f"{nid}: \"{t}\"")
        if node.get("next"):
            leads.setdefault(node["next"], []).append(f"{nid}: (continue)")
    entries = {e["node"]: cond(e.get("when")) for e in d["entry"]}
    w = []
    for nid, node in d["nodes"].items():
        w.append(f"\n## {nid}" + (f"   [entry when {entries[nid] or 'always'}]" if nid in entries else ""))
        for l in leads.get(nid, []):
            w.append(f"   <- {l}")
        texts = node["text"] if isinstance(node["text"], list) else [node["text"]]
        for i, t in enumerate(texts):
            t = t if isinstance(t, dict) else {"text": t}
            lid = f"dlg.{npc}.{nid}.{i}"
            m = man.get(lid, {})
            w.append(f"  [{lid}] {('when ' + cond(t.get('when'))) if t.get('when') else ''}")
            w.append(f"     {t['text']}")
            if m.get("direction"):
                w.append(f"     DIRECTION {json.dumps(m['direction'], ensure_ascii=False)}")
            if m.get("status") == "skip":
                w.append(f"     (skip: {m.get('skip')})")
        for c in node.get("choices") or []:
            t = c["text"] if isinstance(c["text"], str) else c["text"][0]["text"]
            w.append(f"     > {t}" + (f" -> {c['goto']}" if c.get("goto") else " (ends)" if c.get("end") else ""))
    s = "\n".join(w)
    if out:
        open(out, "w", encoding="utf-8").write(s)
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        print(s)


if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0], a[a.index("--out") + 1] if "--out" in a else None)
