"""Bring the owner's ElevenLabs takes into the game, replacing placeholders.

The takes sit in one folder under the names the packets give them
(docs/voice/elevenlabs/<voice>.md): `<line id>.wav`, or `<line id>.p<part>.wav`
for one part of a line several voices share. MP3, FLAC and M4A work too, and a
browser's " (1)" copies are taken as the newest of that name.

For each take: the line is found by its id, the voice is checked against
the part (with --voice), Whisper checks the words against the subtitle, and
the take is kept in VO_WORK/finals. Every line it touches is then mixed again
through the same chain as before (post.py: trim, de-click, the scene's
room, loudness), from its finals and, for parts not yet recorded, its
placeholder, and written into the game and its index. A line is final when
every part is. The report lists what was imported, what was refused and
why, and what that voice still has to record.

    python tools/vo/import_takes.py ~/Downloads/su_vo --voice rook
    python tools/vo/import_takes.py ~/Downloads/su_vo --dry-run      # only the report
    python tools/vo/import_takes.py ~/Downloads/su_vo --force        # keep takes whose words differ
"""
from __future__ import annotations

import argparse
import glob
import os
import re
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lines as lines_mod  # noqa: E402
from common import FFMPEG, WORK  # noqa: E402

AUDIO = (".wav", ".mp3", ".flac", ".m4a", ".ogg")
FINALS = os.path.join(WORK, "finals")


def parse_name(path: str) -> tuple[str, int | None] | None:
    """(line id, part) from a take's file name, or None if it is not one."""
    base, ext = os.path.splitext(os.path.basename(path))
    if ext.lower() not in AUDIO:
        return None
    base = re.sub(r"\s*\(\d+\)$", "", base.strip())
    m = re.match(r"^(?P<id>[a-z_]+\.[\w.]+?)(?:\.p(?P<part>\d+))?$", base)
    if not m:
        return None
    return m.group("id"), (int(m.group("part")) if m.group("part") else None)


def plan(files: list[str], man: list[dict], voice: str | None = None) -> dict:
    """Match files to the lines and parts they record. Returns the matched
    takes, the refused files with why, and (with a voice) what that voice
    still has to record."""
    by_id = {l["id"]: l for l in man}
    newest: dict[tuple, str] = {}
    refused = []
    for f in sorted(files, key=lambda p: os.path.getmtime(p) if os.path.exists(p) else 0):
        got = parse_name(f)
        if not got:
            if os.path.splitext(f)[1].lower() in AUDIO:
                refused.append((f, "the name is not a line id"))
            continue
        lid, part = got
        line = by_id.get(lid)
        if line is None:
            refused.append((f, f"no line {lid} in the game (renamed or rewritten? check the packet)"))
            continue
        if line.get("status") == "skip":
            refused.append((f, f"{lid} is not voiced"))
            continue
        segs = line["segments"]
        if part is None:
            if len(segs) > 1:
                voices = [s["voice"] for s in segs]
                mine = [i for i, s in enumerate(segs) if s["voice"] == voice] if voice else []
                if len(mine) == 1:
                    part = mine[0]
                else:
                    refused.append((f, f"{lid} has {len(segs)} parts ({', '.join(voices)}): name it {lid}.p<part>"))
                    continue
            else:
                part = 0
        if part >= len(segs):
            refused.append((f, f"{lid} has no part {part}"))
            continue
        if voice and segs[part]["voice"] != voice:
            refused.append((f, f"{lid} part {part} is {segs[part]['voice']}'s, not {voice}'s"))
            continue
        newest[(lid, part)] = f  # the latest of several copies wins
    matched = [{"line": lid, "part": part, "file": f, "voice": by_id[lid]["segments"][part]["voice"],
                "text": by_id[lid]["segments"][part]["text"]} for (lid, part), f in newest.items()]
    missing = []
    if voice:
        have = set(newest) | {(lid, int(p) if p else 0) for lid, p in (_final_key(x) for x in _finals())}
        for l in sorted(man, key=lines_mod.impact):
            if l.get("status") == "skip":
                continue
            for i, s in enumerate(l["segments"]):
                if s["voice"] == voice and (l["id"], i) not in have:
                    missing.append(f"{l['id']}.p{i}" if len(l["segments"]) > 1 else l["id"])
    return {"matched": matched, "refused": refused, "missing": missing}


def _finals() -> list[str]:
    return [p for p in glob.glob(os.path.join(FINALS, "*.wav"))]


def _final_key(path: str) -> tuple[str, str | None]:
    got = parse_name(path)
    return (got[0], str(got[1]) if got and got[1] is not None else None) if got else ("", None)


def final_path(lid: str, part: int, n_parts: int) -> str:
    return os.path.join(FINALS, f"{lid}.p{part}.wav" if n_parts > 1 else f"{lid}.wav")


def to_wav(src: str, dst: str):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if src.lower().endswith(".wav"):
        shutil.copyfile(src, dst)
    else:
        subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", src, "-ac", "1", dst], check=True)


def rebuild(line: dict, log) -> dict | None:
    """The line mixed from its finals, and its placeholder for any part not
    yet recorded. None when a part has neither."""
    import produce
    n = len(line["segments"])
    old = (line.get("take") or {}).get("parts") or []
    picks, final = [], []
    for i, s in enumerate(line["segments"]):
        fp = final_path(line["id"], i, n)
        if os.path.exists(fp):
            picks.append({"path": fp, "seed": 0, "score": 0, "similarity": 0, "utmos": 0, "accent": "", "words_per_sec": 0,
                          "said": "", "style": "final: ElevenLabs"})
            final.append(i)
        elif i < len(old) and old[i].get("src") and os.path.exists(old[i]["src"]):
            picks.append({**old[i], "path": old[i]["src"], "words_per_sec": old[i].get("wps", 0)})
        else:
            return None
    take = produce.finish(line, picks, log)
    whole = len(final) == n
    take.update(model="elevenlabs" if whole else "elevenlabs + placeholder", placeholder=not whole, final_parts=final)
    return take


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--voice", help="only takes of this voice, and report what it still has to record")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-check", action="store_true", help="skip Whisper's word check")
    ap.add_argument("--force", action="store_true", help="keep takes whose words differ from the subtitle")
    a = ap.parse_args(argv)
    folder = os.path.expanduser(a.folder)
    man = lines_mod.merge(lines_mod.build())
    by_id = {l["id"]: l for l in man}
    files = [p for p in glob.glob(os.path.join(folder, "*")) if os.path.isfile(p)]
    p = plan(files, man, a.voice)
    print(f"{len(files)} files: {len(p['matched'])} takes matched, {len(p['refused'])} refused")
    for f, why in p["refused"]:
        print(f"  refused {os.path.basename(f)}: {why}")
    if a.dry_run:
        _missing(p, a.voice)
        return p
    ears = None
    kept, wrong = [], []
    for m in p["matched"]:
        if not a.no_check:
            import produce
            if ears is None:
                ears = produce.Ears()
            tmp = os.path.join(FINALS, "_check.wav")
            to_wav(m["file"], tmp)
            rep = ears.hear(tmp, re.sub(r"\s\+\s", " and ", m["text"]), m["voice"])
            if rep["faults"] and not a.force:
                wrong.append((m, rep["faults"], rep["said"]))
                continue
        to_wav(m["file"], final_path(m["line"], m["part"], len(by_id[m["line"]]["segments"])))
        kept.append(m)
    # One take serves every part with the same words in the same voice (the packets list them once).
    same: dict = {}
    for l in man:
        for i, s in enumerate(l.get("segments") or []):
            same.setdefault((s["voice"], s.get("acted", s["text"])), []).append((l["id"], i, len(l["segments"])))
    for m in list(kept):
        seg = by_id[m["line"]]["segments"][m["part"]]
        src = final_path(m["line"], m["part"], len(by_id[m["line"]]["segments"]))
        for lid, i, n in same.get((seg["voice"], seg.get("acted", seg["text"])), []):
            dst = final_path(lid, i, n)
            if (lid, i) != (m["line"], m["part"]) and not os.path.exists(dst):
                shutil.copyfile(src, dst)
                kept.append({**m, "line": lid, "part": i, "copy": True})
    for m, faults, said in wrong:
        print(f"  words differ in {os.path.basename(m['file'])}: {faults[:6]}\n      heard: {said}\n      wants: {m['text']}")
    done, partial, waiting = [], [], []

    def log(s):
        pass
    # The placeholder run may have saved the manifest while the words were
    # being checked: mix against it afresh, so neither undoes the other.
    by_id = {l["id"]: l for l in lines_mod.merge(lines_mod.build())}
    for lid in sorted({m["line"] for m in kept}):
        take = rebuild(by_id[lid], log)
        if take is None:
            waiting.append(lid)
            continue
        by_id[lid].update(take=take, status="done")
        (partial if take["placeholder"] else done).append(lid)
    if kept:
        import produce
        lines_mod.save(list(by_id.values()))
        n = produce.write_index(list(by_id.values()))
        print(f"imported {len(kept)} takes: {len(done)} lines final, {len(partial)} waiting on another voice's parts, "
              f"{len(waiting)} with a part that has neither a take nor a placeholder ({', '.join(waiting[:8])}); "
              f"{n} lines in the game's index")
        # A cinematic's cut is timed to its line: say which takes miss it (kept; a new take retimes the cut).
        for lid in done + partial:
            if by_id[lid]["take"].get("timing"):
                print(f"  timing {lid}: {by_id[lid]['take']['timing']}")
    _missing(plan(files, list(by_id.values()), a.voice) if a.voice else p, a.voice)
    return {"kept": kept, "wrong": wrong, "done": done, "partial": partial, "waiting": waiting}


def _missing(p: dict, voice: str | None):
    if voice:
        miss = p["missing"]
        print(f"{voice} still to record: {len(miss)}" + (": " + ", ".join(miss[:15]) + (" …" if len(miss) > 15 else "") if miss else ""))


if __name__ == "__main__":
    main(sys.argv[1:])
