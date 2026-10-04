"""The directed reads of some lines, as plain text for the writer (or an
actor): who says it, the words, and how it is to be played. Lines are picked
by id prefix, in the manifest's order.

    python tools/vo/reads.py say. dlg.rook.first dlg.brannoc.nell_ditch [--out reads.txt]
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lines import MANIFEST  # noqa: E402


def read(line: dict) -> str:
    d = line.get("direction") or {}
    how = ", ".join(f"{k} {d[k]}" for k in ("emo", "intent", "pace", "vol") if d.get(k))
    w = [f"[{line['id']}] {line['voice'].upper()}  ({line.get('where', '')})"]
    for s in line.get("segments") or [{"voice": line["voice"], "text": line["text"]}]:
        w.append(f"    {s['voice']}: {s['text']}")
    if how:
        w.append(f"    played: {how}")
    if d.get("note"):
        w.append(f"    note: {d['note']}")
    if d.get("say"):
        w.append(f"    said as: {d['say']}")
    return "\n".join(w)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("prefixes", nargs="+")
    ap.add_argument("--out")
    ap.add_argument("--limit", type=int, default=0, help="at most this many lines per prefix")
    a = ap.parse_intermixed_args(argv)
    lines = json.load(open(MANIFEST, encoding="utf-8"))["lines"]
    out = []
    for p in a.prefixes:
        mine = [l for l in lines if l["id"].startswith(p) and l.get("status") != "skip"]
        out += [read(l) for l in (mine[: a.limit] if a.limit else mine)]
    text = "\n\n".join(out) + "\n"
    if a.out:
        open(a.out, "w", encoding="utf-8").write(text)
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
