"""Each voice in a handful of moods: the prompts its lines are spoken on from.

VoxCPM2 can clone a voice two ways. Told a style ("quiet, sad and tender"),
it acts, but the person drifts: the pitch rises, the accent can slip, and
the speaker match falls. Continuing from a take of the voice instead, it
keeps the person almost exactly, and carries on in that take's manner: its
pace, its weight, its mood. So each part gets a small bank of takes of
itself in different moods ("registers"), each made by styled cloning from
the cast reference and kept only if it is still plainly the same person, in
the same accent, at the register's pace. A line is then continued from the
register its direction calls for (produce.py), which brings the mood without
losing the voice.

    python tools/vo/registers.py rook vonnra     # these voices
    python tools/vo/registers.py --all           # every cast voice without a bank

Writes refs/<voice>.<register>.flac and refs/registers.json.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict

import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyse  # noqa: E402
from cast_session import save_ref  # noqa: E402
from common import REFS, WORK, accent_target, cast, voxcpm  # noqa: E402

BANK = os.path.join(REFS, "registers.json")
# The style the voice is asked for, a sentence that suits it, and the pace
# (as a share of the part's own tempo) the take has to keep.
REGISTERS = {
    "warm": ("warm and amused, a smile in the voice, relaxed",
             "Oh, you'll do. Sit down, sit down, and I'll tell you how it really went, because nobody else will.", (0.85, 1.15)),
    "quiet": ("quiet, sad and tender, slow, soft",
              "I know. I know it was. There's nothing to say about it, so don't. Just sit a while.", (0.6, 0.95)),
    "hard": ("cold and angry, firm and clipped, hard",
             "No. You listen to me now. You'll do as you're told, or you'll leave, and you'll not come back.", (0.85, 1.25)),
    "quick": ("excited and breathless, quick, bright",
              "Quick, come and look! It's lit, it's working, I told them it would, I told every one of them!", (1.05, 1.5)),
    "hushed": ("hushed and afraid, almost whispering, very slow",
               "Listen. Can you hear that? Under the floor. Something down there, waiting. Don't move.", (0.55, 0.9)),
}
# Who has which moods (the rest of the cast has them all).
ONLY = {
    "narrator": ["quiet", "hushed"], "vonnra": ["quiet", "hushed", "hard"], "brannoc": ["quiet", "hard"],
    "warden": [], "bones": [], "watchman": [], "lampling": [], "grimtunnel": ["quick"], "snib": ["quick", "hard"],
    "guard": ["hard"], "guard_f": ["hard"], "folk_f1": ["warm", "quiet"], "folk_f2": ["warm", "quick"],
    "folk_m1": ["warm", "hard"], "folk_m2": ["warm", "quiet"], "folk_child_f": ["quick"], "folk_child_m": ["quick"],
}


def registers_for(voice: str) -> list[str]:
    return ONLY.get(voice, list(REGISTERS))


def build(worker, voice: str, v: dict, n: int, book: dict, log=print):
    ref = os.path.join(REFS, f"{voice}.flac")
    rw, rsr = sf.read(ref, dtype="float32")
    eref = analyse.speaker_embedding(rw, rsr)
    tempo = sum(v.get("tempo", [2.6, 3.4])) / 2
    target = accent_target(voice)
    folder = os.path.join(WORK, "registers", voice)
    os.makedirs(folder, exist_ok=True)
    book.setdefault(voice, {})
    for reg in registers_for(voice):
        style, text, (lo, hi) = REGISTERS[reg]
        best = None
        for seed in range(1, n + 1):
            out = os.path.join(folder, f"{reg}_s{seed:02d}.wav")
            if not os.path.exists(out):
                r = worker.ask(text=text, ref=ref, style=style, seed=seed, out=out, steps=25)
                if "error" in r:
                    continue
            rep = asdict(analyse.analyse(out, text))
            x, sr = sf.read(out, dtype="float32")
            sim = float(np.dot(analyse.speaker_embedding(x, sr), eref))
            acc = rep["accent_top"].get(target, 0) if target else 1.0
            pace = rep["words_per_sec"] / tempo
            bad = list(rep["faults"]) + rep["artefacts"]
            if sim < 0.72:
                bad.append(f"drifted ({sim:.2f})")
            if target and acc < 0.5:
                bad.append(f"accent {rep['accent']}")
            if not (lo <= pace <= hi):
                bad.append(f"pace x{pace:.2f}")
            score = 2.5 * sim + 0.5 * rep["utmos"] + acc
            log(f"  {voice}.{reg} s{seed:02d} {score:.2f} sim {sim:.2f} mos {rep['utmos']:.2f} acc {rep['accent']} pace x{pace:.2f} {bad or 'OK'}")
            if not bad and (best is None or score > best[0]):
                best = (score, out, seed, sim, rep["utmos"], pace)
        if best:
            save_ref(best[1], os.path.join(REFS, f"{voice}.{reg}.flac"))
            book[voice][reg] = {"text": text, "seed": best[2], "similarity": round(best[3], 3), "utmos": best[4], "pace": round(best[5], 2)}
        else:
            book[voice].pop(reg, None)
            log(f"  {voice}.{reg}: no take kept; its lines use the cast reference")
        json.dump(book, open(BANK, "w", encoding="utf-8"), indent=1)


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("voices", nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--n", type=int, default=6)
    a = ap.parse_args(argv)
    voices = cast()
    book = json.load(open(BANK, encoding="utf-8")) if os.path.exists(BANK) else {}
    names = a.voices or [k for k in voices if os.path.exists(os.path.join(REFS, f"{k}.flac")) and k not in book]
    worker = voxcpm()
    try:
        for name in names:
            print(f"registers for {name}", flush=True)
            build(worker, name, voices[name], a.n, book, lambda s: print(s, flush=True))
    finally:
        worker.close()


if __name__ == "__main__":
    main(sys.argv[1:])
