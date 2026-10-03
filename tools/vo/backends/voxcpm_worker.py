"""VoxCPM2 as a long-running worker: one JSON request per line on stdin,
one JSON reply per line on stdout. The model loads once.

Request:
  {"out": "take.wav", "text": "...", "seed": 3,
   "design": "A man in his fifties..."            # voice design: no reference
   "ref": "refs/rook.flac",                       # or: clone this timbre
   "style": "slower, tired and dry",              #     with this direction
   "prompt_wav": "...", "prompt_text": "...",     # or continue from this take
   "cfg": 2.0, "steps": 10}
Reply: {"out": ..., "sec": audio seconds, "took": seconds} or {"error": ...}

Runs in its own venv (tools/vo/README.md): python voxcpm_worker.py
"""
import json
import os
import sys
import time
import traceback

import soundfile as sf
import torch

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
from voxcpm import VoxCPM  # noqa: E402

out = sys.stdout
sys.stdout = sys.stderr  # the library's chatter must not reach the reply channel
model = VoxCPM.from_pretrained("openbmb/VoxCPM2", load_denoiser=False, optimize=os.environ.get("VOX_COMPILE", "1") == "1")
SR = model.tts_model.sample_rate
out.write(json.dumps({"ready": True, "sr": SR}) + "\n")
out.flush()

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        r = json.loads(line)
        torch.manual_seed(int(r.get("seed", 0)))
        text = r["text"]
        kw = dict(cfg_value=float(r.get("cfg", 2.0)), inference_timesteps=int(r.get("steps", 10)),
                  retry_badcase=True, retry_badcase_max_times=3)
        if r.get("design"):
            text = f"({r['design']}){text}"
        elif r.get("style"):
            text = f"({r['style']}){text}"
        if r.get("ref"):
            kw["reference_wav_path"] = r["ref"]
        if r.get("prompt_wav"):
            kw["prompt_wav_path"] = r["prompt_wav"]
            kw["prompt_text"] = r["prompt_text"]
        t = time.time()
        wav = model.generate(text=text, **kw)
        os.makedirs(os.path.dirname(os.path.abspath(r["out"])), exist_ok=True)
        sf.write(r["out"], wav, SR)
        out.write(json.dumps({"out": r["out"], "sec": round(len(wav) / SR, 2), "took": round(time.time() - t, 1)}) + "\n")
    except Exception as e:  # keep serving; the caller decides what a failure costs
        traceback.print_exc()
        out.write(json.dumps({"error": f"{type(e).__name__}: {e}"}) + "\n")
    out.flush()
