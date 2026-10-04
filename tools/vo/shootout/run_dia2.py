"""Shoot-out takes from Dia2 2B (Nari Labs, Apache 2.0), the successor of
Dia, which moved most like a person in the first shoot-out: the line's Dia
script (with its non-verbal cues) spoken as speaker 1, conditioned on the
part's cast reference as speaker 1's prefix (`dia2`), and with no prefix
(`dia2-free`, Dia2's own voice: a performance to convert, run_vc.py dia2-free).

Runs in Dia2's own environment (its checkout, `uv sync`):
    ~/vo-tools/dia2-main/.venv/Scripts/python tools/vo/shootout/run_dia2.py
"""
import json
import os
import sys

import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.environ.get("VO_TOOLS", os.path.expanduser("~/vo-tools"))
RAW = os.path.join(TOOLS, "shootout", "raw")
REFS = os.path.join(os.path.dirname(HERE), "refs")
LINES = json.load(open(os.path.join(HERE, "lines.json"), encoding="utf-8"))["lines"]

import torch  # noqa: E402
from dia2 import Dia2, GenerationConfig, SamplingConfig  # noqa: E402


def wav_ref(voice: str) -> str:
    """Dia2 reads WAV prefixes: the cast reference as 24 kHz WAV."""
    import librosa
    out = os.path.join(TOOLS, "shootout", "dia2_refs", f"{voice}.wav")
    if not os.path.exists(out):
        os.makedirs(os.path.dirname(out), exist_ok=True)
        x, sr = sf.read(os.path.join(REFS, f"{voice}.flac"), dtype="float32")
        sf.write(out, librosa.resample(x, orig_sr=sr, target_sr=24000), 24000)
    return out


def main():
    dia = Dia2.from_repo("nari-labs/Dia2-2B", device="cuda", dtype="bfloat16")
    for key, L in LINES.items():
        d = os.path.join(RAW, key)
        os.makedirs(d, exist_ok=True)
        for method, prefix in (("dia2", wav_ref(L["voice"])), ("dia2-free", None)):
            for s in (1, 2, 3):
                out = os.path.join(d, f"{method}_s{s}.wav")
                if os.path.exists(out):
                    continue
                torch.manual_seed(s)
                np.random.seed(s)
                cfg = GenerationConfig(cfg_scale=2.0, audio=SamplingConfig(temperature=0.8, top_k=50))
                try:
                    dia.generate(L["dia"], config=cfg, output_wav=out, prefix_speaker_1=prefix)
                    print(key, method, s, flush=True)
                except Exception as e:  # one bad take is not the run
                    print(key, method, s, "FAILED", type(e).__name__, e, flush=True)


if __name__ == "__main__":
    main()
