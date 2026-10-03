"""Casting: audition designed voices for each part and keep the best as the
part's reference, the voice every one of its lines is then cloned from.

Each candidate is VoxCPM2 voice design (the part's description in cast.json,
reading its ref_text) with a different seed. Every candidate is heard by
tools/vo/analyse.py: the words, the accent CommonAccent hears, naturalness
(UTMOS), pitch for the age and sex, pace, artefacts. The winner is written to
tools/vo/refs/<voice>.flac (16 kHz, what the model encodes references at)
with its numbers in refs/casting.json; the rest stay in VO_WORK.

    python tools/vo/cast_session.py rook vonnra        # these parts
    python tools/vo/cast_session.py --all [--n 8]      # every part without a reference
    python tools/vo/cast_session.py rook --redo        # audition again
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys

import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyse  # noqa: E402
from common import REFS, WORK, cast, judge, voxcpm  # noqa: E402

CASTING = os.path.join(REFS, "casting.json")


def save_ref(src: str, dst: str):
    import librosa
    wav, sr = sf.read(src, dtype="float32")
    if wav.ndim > 1:
        wav = wav.mean(1)
    a = librosa.resample(wav, orig_sr=sr, target_sr=16000)
    # Trim the edges to the speech, with a little air.
    rep = analyse.pauses(a, 16000)
    s = max(0, int((rep["head"] - 0.08) * 16000))
    e = len(a) - max(0, int((rep["tail"] - 0.15) * 16000))
    a = a[s:e]
    a = a / max(1e-6, np.max(np.abs(a))) * 0.89
    sf.write(dst, a, 16000, format="FLAC")


def audition(worker, name: str, v: dict, n: int) -> dict:
    d = os.path.join(WORK, "casting", name)
    os.makedirs(d, exist_ok=True)
    results = []
    for seed in range(1, n + 1):
        out = os.path.join(d, f"c{seed:02d}.wav")
        if not os.path.exists(out):
            r = worker.ask(text=v["ref_text"], design=v["design"], seed=seed, out=out)
            if "error" in r:
                print(name, seed, r["error"], flush=True)
                continue
        rep = analyse.asdict(analyse.analyse(out, v["ref_text"]))
        # The reference sets how every line of the part moves: it must be at
        # the part's own tempo (Vonnra's stillness, Tam's tumble).
        score, bad = judge(rep, name, v, tuple(v["tempo"]) if v.get("tempo") else None)
        rep.update(score=score, bad=bad, seed=seed)
        results.append(rep)
        print(f"  {name} c{seed:02d} score {score:.2f} mos {rep['utmos']:.2f} acc {rep['accent']} "
              f"f0 {rep['pitch']['f0_median']:.0f} wps {rep['words_per_sec']:.1f} {bad}", flush=True)
    ok = [r for r in results if not r["bad"]]
    pool = ok or results
    best = max(pool, key=lambda r: r["score"])
    return {"pick": best, "clean": len(ok), "of": len(results)}


def ref_text(voice: str) -> str:
    """The words the part's reference says (its own line, or the line of the
    audition it was found in)."""
    book = json.load(open(CASTING, encoding="utf-8")) if os.path.exists(CASTING) else {}
    return book.get(voice, {}).get("text") or cast()[voice]["ref_text"]


def adopt(book: dict, voice: str, src: str):
    """Cast a part from another part's audition (a candidate heard as the
    right accent for this one): `--adopt chid rav:9`."""
    other, seed = src.split(":")
    v = cast()
    path = os.path.join(WORK, "casting", other, f"c{int(seed):02d}.wav")
    text = v[other]["ref_text"]
    rep = analyse.asdict(analyse.analyse(path, text))
    score, bad = judge(rep, voice, v[voice], tuple(v[voice]["tempo"]))
    save_ref(path, os.path.join(REFS, f"{voice}.flac"))
    book[voice] = {"seed": int(seed), "from": other, "text": text, "score": score, "utmos": rep["utmos"],
                   "accent": rep["accent_top"], "f0": rep["pitch"]["f0_median"], "wps": rep["words_per_sec"],
                   "bad": bad, "said": rep["said"]}
    json.dump(book, open(CASTING, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"cast {voice} from {other} c{int(seed):02d}: {book[voice]}")


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("voices", nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--n", type=int, default=6)
    ap.add_argument("--redo", action="store_true")
    ap.add_argument("--adopt", nargs=2, metavar=("VOICE", "FROM:SEED"))
    a = ap.parse_args(argv)
    voices = cast()
    os.makedirs(REFS, exist_ok=True)
    book = json.load(open(CASTING, encoding="utf-8")) if os.path.exists(CASTING) else {}
    if a.adopt:
        adopt(book, *a.adopt)
        return
    names = a.voices or [k for k in voices if a.all and (a.redo or k not in book)]
    worker = voxcpm()
    try:
        for name in names:
            v = voices[name]
            if name in book and not a.redo and not a.voices:
                continue
            print(f"casting {name}", flush=True)
            res = audition(worker, name, v, a.n)
            pick = res["pick"]
            save_ref(pick["path"], os.path.join(REFS, f"{name}.flac"))
            book[name] = {"seed": pick["seed"], "score": pick["score"], "clean": f"{res['clean']}/{res['of']}",
                          "utmos": pick["utmos"], "accent": pick["accent_top"], "f0": pick["pitch"]["f0_median"],
                          "wps": pick["words_per_sec"], "bad": pick["bad"], "said": pick["said"]}
            json.dump(book, open(CASTING, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
            print(f"cast {name}: c{pick['seed']:02d} {book[name]}", flush=True)
    finally:
        worker.close()


if __name__ == "__main__":
    main(sys.argv[1:])
