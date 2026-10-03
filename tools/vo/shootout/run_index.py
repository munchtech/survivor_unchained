"""Shoot-out takes from IndexTTS-2.5 (bilibili licence): the cast reference
for timbre, the line's emotion vector for the performance. Run with the
IndexTTS venv from inside its checkout:

    cd ~/vo-tools/index-tts && .venv/Scripts/python ../../<repo>/tools/vo/shootout/run_index.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REFS = os.path.join(os.path.dirname(HERE), "refs")
RAW = os.path.join(os.environ.get("VO_TOOLS", os.path.expanduser("~/vo-tools")), "shootout", "raw")
sys.path.insert(0, os.getcwd())
from indextts.infer_v2_5 import IndexTTS2  # noqa: E402

tts = IndexTTS2(cfg_path="checkpoints/config.yaml", model_dir="checkpoints", use_bf16=True)
LINES = json.load(open(os.path.join(HERE, "lines.json"), encoding="utf-8"))["lines"]
import torch  # noqa: E402
for key, L in LINES.items():
    ref = os.path.join(REFS, f"{L['voice']}.flac")
    if not os.path.exists(ref):
        continue
    d = os.path.join(RAW, key)
    os.makedirs(d, exist_ok=True)
    for s in (1, 2, 3):
        out = os.path.join(d, f"indextts_s{s}.wav")
        if os.path.exists(out):
            continue
        torch.manual_seed(s)
        tts.infer(spk_audio_prompt=ref, text=L["text"], output_path=out, lang="en", emo_vector=L["emo"], emo_alpha=0.9)
        print(key, s, flush=True)
