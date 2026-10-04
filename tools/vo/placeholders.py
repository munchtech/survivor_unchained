"""Placeholder voice for every line until its final take (ElevenLabs, one
character at a time: docs/voice/elevenlabs/) replaces it.

The best local route the shoot-out found: Maya1 acts the line in a voice
designed from a sentence (`maya` in cast.json, with the line's direction as
the tone, pace and loudness, and the writer's beats as its tags), then
Seed-VC turns the performance into the part's cast voice. Whisper checks the
words; a part that is wrong is acted again (another seed), and after the last
round the take with the fewest faults is kept. Each take is mixed through the
same chain as every other (post.py) and marked as a placeholder in the
manifest and the game's index, so a final replaces it cleanly.

The three models run one after another, each in its own process, so the
shared card only ever holds one of them.

    python tools/vo/placeholders.py                       # every line without a take, most important first
    python tools/vo/placeholders.py dlg.rook --rounds 2   # these lines
    python tools/vo/placeholders.py --limit 40            # the first forty
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time

import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lines as lines_mod  # noqa: E402
import produce  # noqa: E402
from common import REFS, TOOLS, WORK, cast, seedvc  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
FOLDER = os.path.join(WORK, "placeholders")
MAYA_PY = os.path.join(TOOLS, "orpheus", "Scripts" if os.name == "nt" else "bin", "python")
ANALYSIS_PY = sys.executable
CHUNK = 230  # characters a performance is given at once (Maya1 holds about thirty seconds)
TAGS = {"laugh": "<laugh>", "laughs": "<laugh>", "chuckle": "<chuckle>", "sigh": "<sigh>", "sighs": "<sigh>",
        "gasp": "<gasp>", "cry": "<cry>", "whisper": "<whisper>", "beat": "...", "breath": "", "sniff": "", "name": ""}
PACE_WORD = {"very slow": "very slow", "slow": "slow", "measured": "conversational", "brisk": "fast", "quick": "fast"}
INTENSITY = {"hushed": "low", "quiet": "low", "level": "medium", "raised": "high", "shout": "high"}


def words(t: str) -> list[str]:
    return re.findall(r"[a-z']+", re.sub(r"\[[^\]]*\]|<[^>]*>", " ", t.lower()))


def tagged(seg_text: str, d: dict) -> str:
    """The writer's beats as Maya1's tags, where a beats part says exactly
    this segment's words; otherwise the words as written."""
    for part in (d.get("beats") or "").split("|"):
        if words(part) == words(seg_text) and words(part):
            out = re.sub(r"\[([a-z]+)[^\]]*\]", lambda m: TAGS.get(m.group(1), ""), part)
            return re.sub(r"\s+", " ", out).strip()
    return seg_text


PACES = ["very slow", "slow", "conversational", "fast"]


def description(vdef: dict, d: dict, nudge: int = 0) -> str:
    """The part's Maya1 voice with this line's tone, pace and loudness.
    `nudge` moves the pace a step quicker (+) or slower (-), for a line
    whose last take did not fit the cut it is timed to."""
    who, _, rest = vdef["maya"].partition(". ")
    keep = [x for x in rest.rstrip(".").split(", ") if "pitch" in x or "timbre" in x]
    pace = PACE_WORD[next((k for k in PACE_WORD if k in d.get("pace", "measured")), "measured")]
    pace = PACES[max(0, min(len(PACES) - 1, PACES.index(pace) + nudge))]
    keep.append(f"{pace} pacing")
    # The narrator never shows a feeling (the story lead's rule): his tone is always plain.
    emo = "plain" if vdef.get("name") == "The narrator" else re.split(r",| then ", d.get("emo", "") or "")[0].strip() or "plain"
    vol = d.get("vol", "level")
    keep.append(f"{emo} tone at {INTENSITY.get(vol, 'medium')} intensity")
    if vol == "hushed":
        keep.append("whispering")
    if vol == "shout":
        keep.append("shouting")
    return f"{who}. {', '.join(keep)}."


def chunks(text: str) -> list[str]:
    """Sentence groups short enough for one performance."""
    if len(text) <= CHUNK:
        return [text]
    out, cur = [], ""
    for s in re.split(r"(?<=[.!?…])\s+", text):
        if cur and len(cur) + len(s) + 1 > CHUNK:
            out.append(cur)
            cur = s
        else:
            cur = f"{cur} {s}".strip()
    return out + ([cur] if cur else [])


def segment_jobs(line: dict, rnd: int, nudge: int = 0) -> list[dict]:
    voices = cast()
    d = line.get("direction", {})
    jobs = []
    for i, seg in enumerate(line["segments"]):
        sd = produce.NARRATOR_ASIDE if seg["voice"] == "narrator" and line["voice"] != "narrator" else d
        text = produce.prepare(tagged(seg["text"], sd) if seg["voice"] != "narrator" or line["voice"] == "narrator" else seg["text"])[0]
        desc = description(voices[seg["voice"]], sd, nudge)
        parts = chunks(text)
        # The files are named for what was asked (the words, the description,
        # the voice), so a changed direction is acted again, not served from the cache.
        key = hashlib.sha1(f"{desc}|{text}|{seg['voice']}".encode("utf-8")).hexdigest()[:6]
        stem = os.path.join(FOLDER, line["id"], f"p{i}")
        jobs.append({"line": line["id"], "part": i, "voice": seg["voice"], "text": seg["text"], "round": rnd, "nudge": nudge,
                     "chunks": [{"out": f"{stem}_c{k}_r{rnd}_{key}.wav", "description": desc,
                                 "text": c, "seed": 1000 * rnd + 7} for k, c in enumerate(parts)],
                     "perf": f"{stem}_perf_r{rnd}_{key}.wav",
                     "vc": f"{stem}_vc_r{rnd}_{key}.wav"})
    return jobs


COMFY = os.environ.get("COMFY_URL", "http://127.0.0.1:8188")


def wait_for_gpu(log, most: float = 1800):
    """The card is shared with ComfyUI (the art). Wait until its queue is
    empty, then ask it to let go of its models, so neither of us pages the
    other's weights through system memory. Gives up waiting after `most`."""
    import urllib.request
    t0, said = time.time(), False
    while time.time() - t0 < most:
        try:
            q = json.load(urllib.request.urlopen(f"{COMFY}/queue", timeout=5))
        except Exception:
            return  # no ComfyUI running: nothing to wait for
        if not q.get("queue_running") and not q.get("queue_pending"):
            try:
                req = urllib.request.Request(f"{COMFY}/free", data=json.dumps({"unload_models": True, "free_memory": True}).encode(),
                                             headers={"Content-Type": "application/json"}, method="POST")
                urllib.request.urlopen(req, timeout=10)
            except Exception:
                pass
            time.sleep(3)
            return
        if not said:
            log("  waiting for ComfyUI's queue to empty")
            said = True
        time.sleep(15)
    log("  ComfyUI still busy; going on")


def act(jobs: list[dict], batch: int, log):
    flat = [c for j in jobs for c in j["chunks"] if not os.path.exists(c["out"])]
    if flat:
        path = os.path.join(FOLDER, "maya_jobs.json")
        json.dump(flat, open(path, "w", encoding="utf-8"), ensure_ascii=False)
        wait_for_gpu(log)
        log(f"  acting {len(flat)} performances (Maya1)")
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        for b in (batch, max(1, batch // 2), 1):
            r = subprocess.run([MAYA_PY, os.path.join(HERE, "backends", "maya_batch.py"), path, "--batch", str(b)], env=env,
                               stdout=open(os.path.join(TOOLS, "maya_batch.log"), "a", encoding="utf-8"), stderr=subprocess.STDOUT)
            if r.returncode == 0:
                break
            log(f"    Maya1 stopped (exit {r.returncode}); again with batches of {max(1, b // 2)}")
            time.sleep(20)
    for j in jobs:
        have = [c["out"] for c in j["chunks"] if os.path.exists(c["out"])]
        if len(have) == len(j["chunks"]) and not os.path.exists(j["perf"]):
            parts, sr = [], 24000
            for p in have:
                x, sr = sf.read(p, dtype="float32")
                parts += [x, np.zeros(int(0.3 * sr), np.float32)]
            sf.write(j["perf"], np.concatenate(parts[:-1]), sr)


def convert(jobs: list[dict], log):
    todo = [j for j in jobs if os.path.exists(j["perf"]) and not os.path.exists(j["vc"])]
    if not todo:
        return
    wait_for_gpu(log)
    log(f"  converting {len(todo)} into the cast voices (Seed-VC)")
    w = seedvc()
    try:
        for j in todo:
            r = w.ask(source=j["perf"], target=os.path.join(REFS, f"{j['voice']}.flac"), out=j["vc"], f0=False)
            if "error" in r:
                log(f"    {j['line']} p{j['part']}: {r['error']}")
    finally:
        w.close()


def check(jobs: list[dict], log) -> dict:
    """Whisper on every converted part, in its own process: the words heard,
    the faults, and how close the voice is to the cast reference."""
    todo = [{"path": j["vc"], "text": j["text"], "voice": j["voice"]} for j in jobs if os.path.exists(j["vc"])]
    if not todo:
        return {}
    path = os.path.join(FOLDER, "check_jobs.json")
    out = path + ".out"
    heard: dict = {}
    # The checker has died without a word on a crowded card (3 October):
    # what it did not hear is checked again, twice at most.
    for attempt in range(3):
        left = [t for t in todo if t["path"] not in heard]
        if not left:
            break
        json.dump(left, open(path, "w", encoding="utf-8"), ensure_ascii=False)
        if os.path.exists(out):
            os.remove(out)  # never read an earlier batch's answers as this one's
        wait_for_gpu(log)
        log(f"  checking {len(left)} parts (Whisper)" + (f", again (try {attempt + 1})" if attempt else ""))
        r = subprocess.run([ANALYSIS_PY, os.path.abspath(__file__), "--check", path, out], env=dict(os.environ, PYTHONIOENCODING="utf-8"),
                           stdout=open(os.path.join(TOOLS, "placeholder_check.log"), "a", encoding="utf-8"), stderr=subprocess.STDOUT)
        if os.path.exists(out):
            heard.update(json.load(open(out, encoding="utf-8")))
        if r.returncode:
            log(f"    the checker stopped (exit {r.returncode}) with {len(heard)} of {len(todo)} heard")
            time.sleep(20)
    return heard


def run_check(path: str, out: str):
    import analyse
    ears = produce.Ears()
    res = {}
    for j in json.load(open(path, encoding="utf-8")):
        try:
            rep = ears.hear(j["path"], j["text"], j["voice"])
            res[j["path"]] = {"said": rep["said"], "faults": rep["faults"], "similarity": rep["similarity"], "utmos": rep["utmos"],
                              "accent": rep["accent"], "words_per_sec": rep["words_per_sec"]}
        except Exception as e:  # a broken take is a fault, not the end of the batch
            res[j["path"]] = {"said": "", "faults": [f"unheard: {type(e).__name__}"], "similarity": 0, "utmos": 0, "accent": "",
                              "words_per_sec": 0}
        json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False)
    _ = analyse


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--voice")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--chunk", type=int, default=40, help="lines per pass through the three models")
    ap.add_argument("--batch", type=int, default=8, help="Maya1 performances decoded together (8 is about ten times one)")
    ap.add_argument("--redo", action="store_true", help="make placeholders again for lines that have one")
    ap.add_argument("--refault", action="store_true", help="judge the words of every placeholder again from what Whisper "
                                                                "heard, with the lexicon as it is now (no GPU)")
    ap.add_argument("--check", nargs=2, help=argparse.SUPPRESS)
    a = ap.parse_args(argv)
    if a.check:
        return run_check(*a.check)
    if a.refault:
        return refault()
    man = lines_mod.merge(lines_mod.build())
    by_id = {l["id"]: l for l in man}
    todo = [l for l in man if l["status"] != "skip"
            and (l["status"] in ("todo", "stale", "failed") or (a.redo and (l.get("take") or {}).get("placeholder") and not (l.get("take") or {}).get("final_parts")))
            and (not a.ids or any(l["id"] == p or l["id"].startswith(p) for p in a.ids))
            and (not a.voice or any(s["voice"] == a.voice for s in l["segments"]))
            and all(os.path.exists(os.path.join(REFS, f"{s['voice']}.flac")) for s in l["segments"])]
    todo.sort(key=lines_mod.impact)
    if a.limit:
        todo = todo[: a.limit]
    os.makedirs(FOLDER, exist_ok=True)
    logf = open(os.path.join(WORK, "placeholders.log"), "a", encoding="utf-8")

    def log(s):
        print(s, flush=True)
        logf.write(s + "\n"); logf.flush()

    log(f"{time.strftime('%H:%M')} {len(todo)} lines want a placeholder")
    made = 0
    for c in range(0, len(todo), a.chunk):
        group = todo[c: c + a.chunk]
        by_line = {l["id"]: l for l in group}
        best: dict[tuple, dict] = {}
        nudge: dict[str, int] = {}
        pending = [j for l in group for j in segment_jobs(l, 1)]
        for rnd in range(1, a.rounds + 1):
            if rnd > 1:
                pending = [j for l in group for j in segment_jobs(l, rnd, nudge.get(l["id"], 0))
                           if (l["id"], j["part"]) not in best or best[(l["id"], j["part"])]["faults"]]
            if not pending:
                break
            log(f"{time.strftime('%H:%M')} lines {c + 1}-{c + len(group)}, round {rnd}: {len(pending)} parts")
            act(pending, a.batch, log)
            convert(pending, log)
            heard = check(pending, log)
            for j in pending:
                h = heard.get(j["vc"])
                if not h:
                    continue
                k = (j["line"], j["part"])
                cand = {**h, "path": j["vc"], "seed": j["round"], "score": 0, "style": "placeholder: Maya1 performance, Seed-VC"}
                timed(by_line[j["line"]], cand, nudge)
                if k not in best or rank(cand) < rank(best[k]):
                    best[k] = cand
        # Another process (the importer) may have written finals since this
        # run read the manifest: take the manifest afresh, and never put a
        # placeholder over a final.
        by_id = {l["id"]: l for l in lines_mod.merge(lines_mod.build())}
        for l in group:
            picks = [best.get((l["id"], i)) for i in range(len(l["segments"]))]
            if any(p is None for p in picks):
                log(f"  {l['id']}: no take")
                continue
            now = by_id.get(l["id"])
            t = (now or {}).get("take") or {}
            if now is None or (t.get("final_parts") and t.get("hash") == now["hash"]):
                log(f"  {l['id']}: has a final take now; left alone")
                continue
            if now["hash"] != l["hash"]:
                log(f"  {l['id']}: its words changed during the run; next time")
                continue
            take = produce.finish(now, picks, log)
            take.update(model="maya1 performance + seed-vc", placeholder=True)
            faults = [f for p in picks for f in p["faults"]]
            if faults:
                take["faults"] = faults
            now.update(take=take, status="done", placeholder=True)
            now.pop("failed", None)
            made += 1
        lines_mod.save(list(by_id.values()))
        n = produce.write_index(list(by_id.values()))
        log(f"{time.strftime('%H:%M')} {made} placeholders made; {n} lines in the game's index")


def refault():
    """A word fault can be Whisper's spelling of a name said right ('Danit'
    for 'Dannet'): once the lexicon knows the spelling, the placeholders'
    faults are judged again from what was heard, and the lines still wrong
    are listed for --redo."""
    import analyse
    man = lines_mod.merge(lines_mod.build())
    cleared, wrong = 0, []
    for l in man:
        t = l.get("take") or {}
        if not t.get("placeholder") or t.get("hash") != l["hash"] or not t.get("parts"):
            continue
        words = []
        for seg, p in zip(l["segments"], t["parts"]):
            if p.get("said"):
                words += analyse.substantive(analyse.wer(seg["text"], p["said"])[1])
        other = [f for f in t.get("faults", []) if f.startswith(("long:", "short:", "unmixed", "unheard"))]
        if t.get("faults") and not words and not other:
            cleared += 1
        t.pop("faults", None)
        if words or other:
            t["faults"] = words + other
            wrong.append(f"{l['id']}: {', '.join((words + other)[:4])}")
    lines_mod.save(man)
    produce.write_index(man)
    print(f"{cleared} placeholders cleared; {len(wrong)} still with faults")
    for w in wrong:
        print("  " + w)


def rank(p: dict) -> tuple:
    """Fewest faults first; then, for a line timed to a cut, the nearest to its window."""
    return len(p["faults"]), p.get("off_by", 0.0)


def timed(line: dict, cand: dict, nudge: dict):
    """A line timed to a cut (direction `time`): a take that will not fit
    once its pauses are tightened is a fault, and the next round is asked a
    step quicker or slower."""
    win = (line.get("direction") or {}).get("time")
    if not win or len(line["segments"]) != 1:
        return
    try:
        _, _, read, _ = produce.fit(line, [cand])
    except Exception as e:  # a take the mix cannot read is judged on its words alone
        cand["faults"] = cand["faults"] + [f"unmixed: {type(e).__name__}"]
        return
    cand["read"] = read
    off = produce.timing(line, read)
    if off:
        cand["faults"] = cand["faults"] + [off]
        cand["off_by"] = round(max(win[0] - read, read - win[1]), 2)
        step = 1 if read > win[1] else -1
        if nudge.get(line["id"], 0) * step >= 0:  # keep going the same way; never undo a step
            nudge[line["id"]] = nudge.get(line["id"], 0) + step


if __name__ == "__main__":
    main(sys.argv[1:])
