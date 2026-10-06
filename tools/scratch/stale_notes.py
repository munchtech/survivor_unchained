"""Direction notes that quote words the line no longer has (a stale note), per voice."""
import os
import re
import sys

sys.path.insert(0, os.path.abspath("tools/vo"))
import lines as lines_mod  # noqa: E402


def norm(s):
    return " ".join(re.findall(r"[a-z0-9']+", s.lower().replace("’", "'")))


voices = set(sys.argv[1:])
for l in lines_mod.merge(lines_mod.build()):
    if l["status"] == "skip" or (voices and l["voice"] not in voices):
        continue
    d = l.get("direction") or {}
    text = norm(l["text"].replace("{name}", ""))
    issues = []
    for key in ("note", "beats"):
        v = d.get(key) or ""
        if key == "note":
            quotes = re.findall(r"(?<![a-zA-Z])'([^']+?)'(?![a-zA-Z])", v)
        else:
            quotes = [re.sub(r"\[[^\]]*\]", " ", p) for p in v.split("|")]
        for q in quotes:
            nq = norm(q)
            if nq and nq not in text:
                issues.append(f"{key}: '{q.strip()}'")
    if (d.get("vol") == "hushed") and l["voice"] not in ("narrator",):
        issues.append("hushed (ElevenLabs will whisper)")
    if issues:
        print(f"{l['id']} [{l['voice']}]: " + "; ".join(issues))
