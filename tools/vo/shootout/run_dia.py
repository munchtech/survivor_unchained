"""Shoot-out takes from Dia 1.6B (Nari Labs, Apache 2.0): the line as a
one-speaker script with its non-verbal cues ("(sighs)", "(laughs)"), the
cast reference as the audio prompt (its transcript first, as Dia clones)."""
import json
import os
import sys

import soundfile as sf
import torch
import torchaudio

# torchaudio's loader needs torchcodec (and ffmpeg's DLLs) on Windows; read with soundfile.
torchaudio.load = lambda p, *a, **k: (lambda x: (torch.from_numpy(x[0].T if x[0].ndim > 1 else x[0][None]).float(), x[1]))(sf.read(p, dtype="float32"))
from dia.model import Dia  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
REFS = os.path.join(os.path.dirname(HERE), "refs")
RAW = os.path.join(os.environ.get("VO_TOOLS", os.path.expanduser("~/vo-tools")), "shootout", "raw")
sys.path.insert(0, os.path.dirname(HERE))
LINES = json.load(open(os.path.join(HERE, "lines.json"), encoding="utf-8"))["lines"]
casting = json.load(open(os.path.join(REFS, "casting.json"), encoding="utf-8"))
cast = json.load(open(os.path.join(os.path.dirname(HERE), "cast.json"), encoding="utf-8"))["voices"]
model = Dia.from_pretrained("nari-labs/Dia-1.6B-0626", compute_dtype="float16")
for key, L in LINES.items():
    v = L["voice"]
    ref = os.path.join(REFS, f"{v}.flac")
    if not os.path.exists(ref):
        continue
    ref_words = casting.get(v, {}).get("text") or cast[v]["ref_text"]
    d = os.path.join(RAW, key)
    os.makedirs(d, exist_ok=True)
    for s in (1, 2, 3):
        out = os.path.join(d, f"dia_s{s}.wav")
        if os.path.exists(out):
            continue
        torch.manual_seed(s)
        wav = model.generate(f"[S1] {ref_words} " + L["dia"], audio_prompt=ref, cfg_scale=3.0, temperature=1.2, top_p=0.95)
        sf.write(out, wav, 44100)
        print(key, s, flush=True)
