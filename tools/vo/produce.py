"""Record the lines: several directed takes of each, heard and judged, the
best one edited and mixed into the game.

For each line in tools/vo/manifest.json that has no take yet (or whose words
have changed since its take):

  1. Each part of the line (the narrator's aside, the speaker) is cloned from
     its voice's cast reference (tools/vo/refs, made by cast_session.py) by
     VoxCPM2, with the line's direction as the style instruction: the
     emotion, the pace, the volume. Names are respelt for the model
     (lexicon.json); a word in capitals is said with stress, not spelt.
  2. Every take is heard (analyse.py): the words against the script, the
     accent, naturalness, pitch for the part, pace for the direction, the
     speaker against the reference, artefacts. Takes with a fault are never
     used. If none of the first few is clean, more are made, up to a limit;
     a line that never gets a clean take is left silent and marked `failed`
     with the reasons, for a person to look at.
  3. The best take of each part goes through post.py (edit, tone, the room,
     loudness), the parts are joined, and the line is written to
     godot/art/vo/<voice>/<id>.ogg. data/vo/index.json gets its file, the
     hash of the words it was made from, its length, and where each part
     falls (so the words on screen follow the voice).

    python tools/vo/produce.py                      # everything to do
    python tools/vo/produce.py say. dlg.rook.first  # lines whose id starts so
    python tools/vo/produce.py --voice rook --takes 4 --max 10
    python tools/vo/produce.py dlg.rook.first.0 --redo
    python tools/vo/produce.py --index              # only rewrite the index
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from dataclasses import asdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyse  # noqa: E402
import lines as lines_mod  # noqa: E402
import post  # noqa: E402
from common import FFMPEG, INDEX, OUT_AUDIO, REFS, WORK, accent_target, cast, judge, seedvc, voxcpm  # noqa: E402

PACE = {"very slow": (1.3, 2.3), "slow": (1.7, 2.8), "measured": (2.2, 3.4), "measured then slow": (1.8, 3.3),
        "slow then quick": (1.9, 3.8), "quick then slower": (2.0, 3.8), "quick then measured": (2.2, 3.8),
        "measured then quick": (2.2, 3.8), "brisk": (2.7, 3.9), "quick": (3.0, 4.6)}
VOL_STYLE = {"hushed": "almost a whisper", "quiet": "quietly", "level": "", "raised": "voice raised", "shout": "shouting"}
VOL_LUFS = {"hushed": -20.0, "quiet": -18.0, "level": -16.0, "raised": -15.0, "shout": -14.0}
NARRATOR_ASIDE = {"emo": "quiet, plain and observant", "pace": "measured", "vol": "quiet"}
# Words in capitals that are written so (initials, the notice board), not shouted.
KEEP_CAPS = {"B.E.", "R.", "C.", "M.", "J.", "H.", "V.", "P."}


def prepare(text: str) -> tuple[str, list[str]]:
    """The words as the model should be given them, and the words to stress."""
    lex = analyse.lexicon().get("say", {})
    for k in sorted(lex, key=len, reverse=True):
        text = re.sub(rf"(?<![\w']){re.escape(k)}(?![\w'])", lex[k], text)
    stress = []

    def low(m):
        w = m.group(0)
        if w in KEEP_CAPS or len(w) < 2:
            return w
        stress.append(w.lower())
        return w.lower() if not text.startswith(w) else w.capitalize()
    text = re.sub(r"\b[A-Z]{2,}\b", low, text)
    text = text.replace("—", ", ").replace("–", ", ")
    text = re.sub(r"^\s*\.\.\.\s*", "", text)          # a line that starts on a pause: the edit gives it room
    text = re.sub(r"\s+,", ",", text)
    return text.strip(), stress


ANGER = ("anger", "angry", "fury", "furious", "cold", "contempt", "hostile", "threat", "menace", "scorn", "disgust", "stern",
         "hard", "hate", "bitter", "spite", "accus", "dangerous", "warning", "defensive", "irritable", "impatient", "sharp")
LIFT = ("joy", "excit", "delight", "eager", "overjoyed", "ecstatic", "panic", "breathless", "urgent", "gleeful", "thrilled",
        "bluster", "outrage", "bursting", "giddy", "babble", "hawking", "triumph")
LOW = ("grief", "sad", "sorrow", "tender", "loss", "shame", "guilt", "hurt", "numb", "broken", "despair", "haunted", "dread",
       "fear", "afraid", "frighten", "mourn", "wistful", "regret", "devastat", "stunned", "uneasy", "troubled", "solemn",
       "sombre", "grave", "pity", "moved", "confession", "longing", "stillness", "quiet", "reverent")
WARM = ("amused", "wry", "dry", "fond", "warm", "teas", "sly", "gossip", "playful", "cheerful", "humour", "joke", "merry",
        "flirt", "approv", "pleased", "relief", "relieved", "proud", "kind", "welcome", "delighted", "grateful", "gratitude")


def register_of(d: dict, voice: str) -> str:
    """The mood a line is spoken from (registers.py), read from its direction."""
    import registers
    have = set(registers.registers_for(voice))
    emo, pace, vol = d.get("emo", "").lower(), d.get("pace", "measured"), d.get("vol", "level")
    want = []
    if vol == "hushed":
        want.append("hushed")
    if any(w in emo for w in ANGER):
        want.append("hard")
    if (pace in ("quick", "brisk") or vol in ("raised", "shout")) and any(w in emo for w in LIFT):
        want.append("quick")
    if any(w in emo for w in LOW) or pace in ("slow", "very slow"):
        want += ["quiet", "hushed"] if pace == "very slow" else ["quiet"]
    if any(w in emo for w in WARM):
        want.append("warm")
    for r in want:
        if r in have:
            return r
    return "rest"


def prompt_for(voice: str, reg: str) -> tuple[str, str, str]:
    """The take a line continues from: its file, its words, and which it is."""
    import registers
    book = json.load(open(registers.BANK, encoding="utf-8")) if os.path.exists(registers.BANK) else {}
    if reg != "rest" and reg in book.get(voice, {}) and os.path.exists(os.path.join(REFS, f"{voice}.{reg}.flac")):
        return os.path.join(REFS, f"{voice}.{reg}.flac"), book[voice][reg]["text"], reg
    from cast_session import ref_text
    return os.path.join(REFS, f"{voice}.flac"), ref_text(voice), "rest"


# How lines are made: "cont" (continuation from the voice's mood bank) or
# "perform" (voice design acts the line, Seed-VC makes it the cast voice).
METHOD = {"name": "cont", "vc": None, "f0": False}


def performance(vdef: dict, d: dict) -> str:
    """The voice-design prompt for one line: the part as cast, and how this
    line is played (from its direction), in a director's plain words."""
    he = "She" if vdef.get("sex") == "f" else "He"
    bits = [vdef["design"]]
    play = f"{he} speaks {d.get('emo', 'plainly')}"
    pace, vol = d.get("pace", "measured"), d.get("vol", "level")
    if pace != "measured":
        play += f", {pace}"
    if vol != "level":
        play += {"hushed": ", almost whispering", "quiet": ", quietly", "raised": ", voice raised", "shout": ", shouting"}.get(vol, "")
    bits.append(play + ".")
    if d.get("note"):
        bits.append(d["note"][:240])
    return " ".join(bits)


def style_of(d: dict, stress: list[str]) -> str:
    bits = [d.get("emo", "")]
    pace = d.get("pace", "measured")
    bits.append(f"{pace} pace" if pace != "measured" else "unhurried")
    vol = VOL_STYLE.get(d.get("vol", "level"), "")
    if vol:
        bits.append(vol)
    if stress:
        bits.append("stressing " + ", ".join(f"'{w}'" for w in stress[:3]))
    return ", ".join(b for b in bits if b)


class Ears:
    """The analysis models plus each voice's reference print."""

    def __init__(self):
        self.refs = {}

    def ref_print(self, voice: str):
        if voice not in self.refs:
            import soundfile as sf
            w, sr = sf.read(os.path.join(REFS, f"{voice}.flac"), dtype="float32")
            self.refs[voice] = analyse.speaker_embedding(w, sr)
        return self.refs[voice]

    def hear(self, path: str, text: str, voice: str) -> dict:
        import soundfile as sf
        import tells
        # One Whisper pass, with word timings: the words, and the tells.
        rep = asdict(analyse.analyse(path, None, want=("utmos", "accent")))
        tl = tells.tells(path)
        rep["said"] = tl.pop("said")
        rep["tells"] = tl
        w_, rep["wrong"] = analyse.wer(text, rep["said"])
        rep["wer"] = round(float(w_), 3)
        rep["faults"] = analyse.substantive(rep["wrong"])
        rep["human"] = round(human(tl), 2)
        w, sr = sf.read(path, dtype="float32")
        if w.ndim > 1:
            w = w.mean(1)
        rep["similarity"] = round(float(np.dot(analyse.speaker_embedding(w, sr), self.ref_print(voice))), 3)
        return rep


def human(t: dict) -> float:
    """How much a take moves like a person (tells.py): pace that changes,
    stress that lands, pitch that travels, breath; each capped."""
    return (min(t["pace_variation"], 0.3) * 6 + min(t["stress_spread_db"], 8) * 0.25
            + min(t["word_pitch_moves_st"], 4) * 0.35 + min(t["breaths"], 3) * 0.2)


PACE_X = {"very slow": (0.55, 0.9), "slow": (0.65, 1.0), "measured": (0.8, 1.2), "brisk": (0.95, 1.35), "quick": (1.0, 1.5)}


def pace_window(d: dict, vdef: dict) -> tuple[float, float]:
    """Words a second the direction asks for, from this part's own tempo."""
    centre = sum(vdef.get("tempo", [2.6, 3.4])) / 2
    p = d.get("pace", "measured")
    key = next((k for k in ("very slow", "slow", "quick", "brisk") if k in p), "measured")
    if "then" in p:  # "measured then slow": anywhere across the two
        a = PACE_X[next((k for k in PACE_X if p.startswith(k)), "measured")]
        b = PACE_X[next((k for k in PACE_X if p.endswith(k)), "measured")]
        lo, hi = min(a[0], b[0]), max(a[1], b[1])
    else:
        lo, hi = PACE_X[key]
    return round(centre * lo, 2), round(centre * hi, 2)


def score_take(rep: dict, voice: str, vdef: dict, d: dict, words: int) -> tuple[float, list[str]]:
    want = pace_window(d, vdef) if words >= 6 else None
    score, bad = judge(rep, voice, vdef, want)
    # Short lines say too little for the accent or the pace to be judged fairly.
    if words < 6:
        bad = [b for b in bad if not b.startswith("accent") and not b.startswith("pace")]
    sim = rep.get("similarity", 0)
    if sim < 0.45 and not vdef.get("fx"):
        bad.append(f"not the same person as the reference ({sim:.2f})")
    score += 2.0 * sim + rep.get("human", 0)
    return round(score, 3), bad


def record_part(worker, ears: Ears, line: dict, i: int, seg: dict, d: dict, takes: int, most: int, log) -> dict | None:
    voices = cast()
    v = seg["voice"]
    vdef = voices[v]
    text, stress = prepare(seg["text"])
    reg = register_of(d, v)
    prompt_wav, prompt_text, reg = prompt_for(v, reg)
    style = f"continued from {reg}"
    words = len(analyse.norm_words(seg["text"]))
    folder = os.path.join(WORK, "takes", line["id"])
    os.makedirs(folder, exist_ok=True)
    heard = []
    seed = 0
    if METHOD["name"] == "perform":
        style = "performed, then converted"
    while seed < most:
        seed += 1
        if METHOD["name"] == "perform":
            # The line acted in full by voice design (the part described, and
            # how this line is played), then turned into the cast voice by
            # Seed-VC: the performance keeps its timing, stress and breath.
            perf = os.path.join(folder, f"p{i}_{v}_perf_s{seed:02d}.wav")
            out = os.path.join(folder, f"p{i}_{v}_vc_s{seed:02d}.wav")
            # A recorded guide performance, where there is one, is the take
            # to convert (<id>.wav, or <id>.p<part>.wav for a line in parts).
            guide = METHOD.get("guides") and next((g for g in (os.path.join(METHOD["guides"], f"{line['id']}.p{i}.wav"),
                                                               os.path.join(METHOD["guides"], f"{line['id']}.wav"))
                                                   if os.path.exists(g) and (len(line["segments"]) == 1 or g.endswith(f".p{i}.wav"))), None)
            if guide:
                perf = guide
                out = os.path.join(folder, f"p{i}_{v}_guide_vc.wav")
                most = 1
            if not os.path.exists(perf):
                r = worker.ask(text=text, design=performance(vdef, d), seed=seed, out=perf, steps=25)
                if "error" in r:
                    log(f"    seed {seed}: {r['error']}")
                    continue
            if not os.path.exists(out):
                r = METHOD["vc"].ask(source=perf, target=os.path.join(REFS, f"{v}.flac"), out=out, f0=METHOD["f0"])
                if "error" in r:
                    log(f"    seed {seed}: {r['error']}")
                    continue
        else:
            out = os.path.join(folder, f"p{i}_{v}_{reg}_s{seed:02d}.wav")
        if METHOD["name"] != "perform" and not os.path.exists(out):
            # Spoken on from a take of the same voice in the line's mood:
            # the person holds, and the mood and pace carry (registers.py).
            r = worker.ask(text=text, ref=os.path.join(REFS, f"{v}.flac"), prompt_wav=prompt_wav, prompt_text=prompt_text,
                           seed=seed, out=out, steps=25)
            if "error" in r:
                log(f"    seed {seed}: {r['error']}")
                continue
        rep = ears.hear(out, seg["text"], v)
        sc, bad = score_take(rep, v, vdef, d, words)
        rep.update(score=sc, bad=bad, seed=seed, style=style, said_as=text)
        heard.append(rep)
        log(f"    p{i} {v} s{seed:02d} {sc:5.2f} sim {rep['similarity']:.2f} mos {rep['utmos']:.2f} "
            f"acc {rep['accent']} wps {rep['words_per_sec']:.1f} {'OK' if not bad else bad}")
        clean = [h for h in heard if not h["bad"]]
        if seed >= takes and clean:
            break
    clean = [h for h in heard if not h["bad"]]
    if not clean:
        return {"failed": True, "best": max(heard, key=lambda h: h["score"]) if heard else None}
    return max(clean, key=lambda h: h["score"])


def char_marks(raw: str, segs: list[dict]) -> list[tuple[float, float]]:
    """Where each part's words sit in the line as shown, as fractions."""
    n = max(1, len(raw))
    out, cur = [], 0
    for s in segs:
        probe = s["text"][: min(24, len(s["text"]))]
        k = raw.find(probe, cur)
        if k < 0:
            k = cur
        end = raw.find(")", k) + 1 if s["voice"] == "narrator" and raw[max(0, k - 1):k] == "(" else k + len(s["text"])
        end = min(n, max(end, k + 1))
        out.append((max(0, k - 1 if raw[max(0, k - 1):k] == "(" else k) / n, end / n))
        cur = end
    out[-1] = (out[-1][0], 1.0)
    return out


def finish(line: dict, picks: list[dict], log) -> dict:
    voices = cast()
    d = line.get("direction", {})
    parts = []
    for seg, pick in zip(line["segments"], picks):
        v = voices[seg["voice"]]
        room = "close" if seg["voice"] == "narrator" else d.get("room", v.get("room", "close"))
        vol = "level" if seg["voice"] == "narrator" and line["voice"] != "narrator" else d.get("vol", "level")
        x = post.master(pick["path"], room, v.get("sex", "m"), v.get("fx"), vol=vol)
        parts.append((x, room))
    audio, marks = post.assemble(parts, vol=d.get("vol", "level"))
    target = -17.0 if line["voice"] == "narrator" else VOL_LUFS.get(d.get("vol", "level"), -16.0)
    audio = post.loudness(audio, target)
    rel = f"{line['voice']}/{line['id']}.ogg"
    dst = os.path.join(OUT_AUDIO, rel)
    post.write_ogg(audio, dst, FFMPEG)
    fr = char_marks(line["text"], line["segments"])
    segs = [[m[0], m[1], round(f[0], 3), round(f[1], 3)] for m, f in zip(marks, fr)]
    take = {"file": rel, "hash": line["hash"], "sec": round(len(audio) / post.SR, 2), "segs": segs, "model": "voxcpm2" if METHOD["name"] == "cont" else "voxcpm2 performance + seed-vc",
            "parts": [{"voice": s["voice"], "src": p.get("path"), "seed": p["seed"], "score": p["score"], "similarity": p["similarity"],
                       "utmos": p["utmos"], "accent": p["accent"], "wps": p["words_per_sec"], "said": p["said"],
                       "style": p["style"]} for s, p in zip(line["segments"], picks)],
            "made": time.strftime("%Y-%m-%d")}
    if line.get("sex"):
        take["sex"] = line["sex"]
    log(f"  -> {rel} {take['sec']}s")
    return take


def write_index(manifest_lines: list[dict]):
    idx = {"lines": {}}
    for l in manifest_lines:
        t = l.get("take")
        if l.get("status") == "done" and t and t.get("hash") == l["hash"] and os.path.exists(os.path.join(OUT_AUDIO, t["file"])):
            e = {"file": t["file"], "hash": t["hash"], "voice": l["voice"], "sec": t["sec"], "segs": t["segs"]}
            if t.get("sex"):
                e["sex"] = t["sex"]
            if t.get("placeholder"):
                e["placeholder"] = True
            idx["lines"][l["id"]] = e
    os.makedirs(os.path.dirname(INDEX), exist_ok=True)
    with open(INDEX, "w", encoding="utf-8", newline="\n") as f:
        json.dump(idx, f, indent=1, ensure_ascii=False, sort_keys=True)
        f.write("\n")
    return len(idx["lines"])


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*", help="line ids or id prefixes")
    ap.add_argument("--voice")
    ap.add_argument("--where", help="only lines from this source (e.g. Prologue.cs, npcs.json)")
    ap.add_argument("--takes", type=int, default=3)
    ap.add_argument("--max", type=int, default=8)
    ap.add_argument("--redo", action="store_true")
    ap.add_argument("--index", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--method", choices=["cont", "perform"], default="cont")
    ap.add_argument("--f0", action="store_true", help="perform: the 44 kHz converter that follows the performance's pitch")
    ap.add_argument("--guides", help="perform: a folder of recorded guide performances (<line id>.wav) to convert instead of generating")
    a = ap.parse_args(argv)
    man = lines_mod.merge(lines_mod.build())
    if a.index:
        print(write_index(man), "lines in the index")
        return
    todo = [l for l in man if l["status"] != "skip"
            and (a.redo or l["status"] in ("todo", "stale"))
            and (not a.ids or any(l["id"] == p or l["id"].startswith(p) for p in a.ids))
            and (not a.voice or l["voice"] == a.voice or any(s["voice"] == a.voice for s in l.get("segments", [])))
            and (not a.where or a.where in l.get("where", ""))]
    missing = sorted({s["voice"] for l in todo for s in l["segments"] if not os.path.exists(os.path.join(REFS, f"{s['voice']}.flac"))})
    if missing:
        print("no cast reference yet for:", ", ".join(missing), "(run cast_session.py); their lines wait")
        todo = [l for l in todo if not any(s["voice"] in missing for s in l["segments"])]
    if a.limit:
        todo = todo[: a.limit]
    print(f"{len(todo)} lines to record")
    logf = open(os.path.join(WORK, "produce.log"), "a", encoding="utf-8")

    def log(s):
        print(s, flush=True)
        logf.write(s + "\n"); logf.flush()

    by_id = {l["id"]: l for l in man}
    worker = voxcpm()
    METHOD.update(name=a.method, f0=a.f0, guides=a.guides, vc=seedvc() if a.method == "perform" else None)
    ears = Ears()
    done = 0
    try:
        for line in todo:
            d = line.get("direction", {})
            log(f"{line['id']} [{line['voice']}] {line['text'][:70]!r}")
            picks, failed = [], []
            for i, seg in enumerate(line["segments"]):
                sd = NARRATOR_ASIDE if seg["voice"] == "narrator" and line["voice"] != "narrator" else d
                p = record_part(worker, ears, line, i, seg, sd, a.takes, a.max, log)
                if p is None or p.get("failed"):
                    best = (p or {}).get("best")
                    failed.append({"part": i, "voice": seg["voice"], "why": best["bad"] if best else ["no take"]})
                else:
                    picks.append(p)
            if failed:
                by_id[line["id"]]["status"] = "failed"
                by_id[line["id"]]["failed"] = failed
                log(f"  FAILED {failed}")
            else:
                by_id[line["id"]]["take"] = finish(line, picks, log)
                by_id[line["id"]]["status"] = "done"
                by_id[line["id"]].pop("failed", None)
                done += 1
            lines_mod.save(list(by_id.values()))
            write_index(list(by_id.values()))
    finally:
        worker.close()
        if METHOD["vc"]:
            METHOD["vc"].close()
        n = write_index(list(by_id.values()))
        print(f"recorded {done}; {n} lines in the index")


if __name__ == "__main__":
    main(sys.argv[1:])
