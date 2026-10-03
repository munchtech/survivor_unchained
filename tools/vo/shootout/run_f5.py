"""Shoot-out takes from F5-TTS (code MIT, weights CC BY-NC 4.0: for this
comparison only, not shippable), cloning the part's cast reference. F5 has
no acting control: it copies the manner of its reference clip."""
import json
import os

import soundfile as sf
import torch
import torchaudio

# torchaudio's loader wants torchcodec's DLLs (a shared ffmpeg build); read with soundfile.
torchaudio.load = lambda p, *a, **k: (lambda x: (torch.from_numpy(x[0].T if x[0].ndim > 1 else x[0][None]).float(), x[1]))(sf.read(p, dtype="float32"))
from f5_tts.api import F5TTS  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(os.environ.get("VO_TOOLS", os.path.expanduser("~/vo-tools")), "shootout", "raw")
REFS = os.path.join(os.path.dirname(HERE), "refs")
LINES = json.load(open(os.path.join(HERE, "lines.json"), encoding="utf-8"))["lines"]
casting = json.load(open(os.path.join(REFS, "casting.json"), encoding="utf-8"))
cast = json.load(open(os.path.join(os.path.dirname(HERE), "cast.json"), encoding="utf-8"))["voices"]
tts = F5TTS()
for key, L in LINES.items():
    v = L["voice"]
    ref = os.path.join(REFS, f"{v}.flac")
    if not os.path.exists(ref):
        continue
    ref_words = casting.get(v, {}).get("text") or cast[v]["ref_text"]
    for s in (1, 2, 3):
        out = os.path.join(RAW, key, f"f5_s{s}.wav")
        if os.path.exists(out):
            continue
        tts.infer(ref_file=ref, ref_text=ref_words, gen_text=L["text"], file_wave=out, seed=s, nfe_step=32)
        print(key, s, flush=True)
