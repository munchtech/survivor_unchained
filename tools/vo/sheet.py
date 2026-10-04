"""Rewrite the casting table in docs/VO_CAST.md from the cast, the casting
results, the mood banks and the manifest (between the CAST TABLE markers).

    python tools/vo/sheet.py
"""
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import REFS, ROOT, accent_target, cast  # noqa: E402

DOC = os.path.join(ROOT, "docs", "VO_CAST.md")


def main():
    voices = cast()
    casting = json.load(open(os.path.join(REFS, "casting.json"), encoding="utf-8")) if os.path.exists(os.path.join(REFS, "casting.json")) else {}
    bank = json.load(open(os.path.join(REFS, "registers.json"), encoding="utf-8")) if os.path.exists(os.path.join(REFS, "registers.json")) else {}
    man = json.load(open(os.path.join(os.path.dirname(__file__), "manifest.json"), encoding="utf-8"))["lines"]
    lines, done, failed = Counter(), Counter(), Counter()
    for l in man:
        if l["status"] == "skip":
            continue
        for s in l.get("segments", []):
            lines[s["voice"]] += 1
        if l["status"] == "done":
            done[l["voice"]] += 1
        if l["status"] == "failed":
            failed[l["voice"]] += 1
    rows = ["| Part | Wanted | Cast take | Heard as | Pitch | Pace | Moods | Lines (parts) | Recorded | Failed | Notes |",
            "|---|---|---|---|---|---|---|---|---|---|---|"]
    for k, v in voices.items():
        c = casting.get(k)
        tgt = accent_target(k)
        if c:
            heard = max(c["accent"], key=c["accent"].get) if c.get("accent") else "?"
            hp = c["accent"].get(heard, 0)
            take = f"c{c['seed']:02d}" + (f" (from {c['from']})" if c.get("from") else "")
            ok = "" if not c.get("bad") else "; ".join(c["bad"])
            heard_s = f"{heard} {hp:.2f}"
            pitch, pace = f"{c['f0']:.0f} Hz", f"{c['wps']:.1f} w/s"
        else:
            take, heard_s, pitch, pace, ok = "not cast", "", "", "", ""
        moods = ", ".join(sorted(bank.get(k, {}))) or "-"
        wanted = f"{v.get('age') or ''} {v['sex']}, {v['accent']}".strip()
        rows.append(f"| {v['name']} (`{k}`) | {wanted} | {take} | {heard_s} | {pitch} | {pace} | {moods} | {lines[k]} | {done[k]} | {failed[k]} | {ok} |")
    table = "\n".join(rows)
    doc = open(DOC, encoding="utf-8").read()
    a, b = doc.find("<!-- CAST TABLE -->"), doc.find("<!-- /CAST TABLE -->")
    new = "<!-- CAST TABLE -->\n" + table + "\n<!-- /CAST TABLE -->"
    doc = doc[:a] + new + doc[b + len("<!-- /CAST TABLE -->"):] if b > a else doc.replace("<!-- CAST TABLE -->", new)
    open(DOC, "w", encoding="utf-8", newline="\n").write(doc)
    print(f"{len(voices)} parts; {sum(done.values())} lines recorded, {sum(failed.values())} failed")


if __name__ == "__main__":
    main()
