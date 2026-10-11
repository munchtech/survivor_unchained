"""Lock lines for recording. A lock binds words, not ids: a line is locked while its
text hash matches the one recorded here; if the words change the lock is BROKEN and the
packet holds the line until the story lead locks it again.

    python tools/vo/lock.py --by "the story lead" --date 2026-10-11 --prefix dlg.rook. --where Prologue.cs
    python tools/vo/lock.py --list      # each lock: ok or BROKEN
    python tools/vo/lock.py --check     # exit 1 if any lock is broken
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lines as lines_mod  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
LOCKED = os.path.join(HERE, "locked.json")
ABOUT = ("Lines locked for recording: id -> the text hash locked, who locked it and when. A line whose "
         "hash no longer matches is BROKEN and held until re-locked (python tools/vo/lock.py).")


def load() -> dict:
    if os.path.exists(LOCKED):
        return json.load(open(LOCKED, encoding="utf-8")).get("lines", {})
    return {}


def status(locks: dict, line_id: str, current_hash: str | None) -> str:
    """ok, broken (the words changed) or gone (the id no longer exists), or '' when not locked."""
    lock = locks.get(line_id)
    if lock is None:
        return ""
    if current_hash is None:
        return "gone"
    return "ok" if lock["hash"] == current_hash else "broken"


def save(locks: dict) -> None:
    out = {"about": ABOUT, "lines": {k: locks[k] for k in sorted(locks)}}
    with open(LOCKED, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(out, indent=1, ensure_ascii=False) + "\n")


def report(locks: dict) -> list[tuple[str, str]]:
    cur = {l["id"]: l["hash"] for l in lines_mod.merge(lines_mod.build())}
    return [(i, status(locks, i, cur.get(i))) for i in sorted(locks)]


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--by")
    ap.add_argument("--date")
    ap.add_argument("--prefix", nargs="+", default=[])
    ap.add_argument("--where", nargs="+", default=[])
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    locks = load()
    if a.prefix or a.where:
        if not (a.by and a.date):
            ap.error("--by and --date are needed to lock")
        n = 0
        for l in lines_mod.merge(lines_mod.build()):
            if l.get("skip") or l.get("status") == "skip":
                continue
            if any(l["id"].startswith(p) for p in a.prefix) or any(w in l.get("where", "") for w in a.where):
                locks[l["id"]] = {"hash": l["hash"], "by": a.by, "date": a.date}
                n += 1
        save(locks)
        print(f"locked {n} lines ({len(locks)} in all)")
    if a.list or a.check:
        rows = report(locks)
        bad = [r for r in rows if r[1] != "ok"]
        if a.list:
            for i, s in rows:
                print(f"{'ok' if s == 'ok' else 'BROKEN'}  {i}" + ("" if s == "ok" else f"  ({s})"))
        if a.check:
            for i, s in bad:
                print(f"BROKEN: {i} ({s})")
            print(f"{len(rows) - len(bad)} locks ok, {len(bad)} broken")
            return 1 if bad else 0
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
