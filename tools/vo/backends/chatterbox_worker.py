"""Chatterbox (Resemble AI, MIT) as a long-running worker, the same protocol
as voxcpm_worker.py. It clones a reference's timbre and accent; its only
acting control is how hard (exaggeration) and how closely it follows the
reference's pace (cfg).

Request: {"out", "text", "seed", "ref", "exaggeration": 0.5, "cfg": 0.5, "temperature": 0.8}
"""
import json
import os
import sys
import time
import traceback

import torch
import soundfile as sf

out = sys.stdout
sys.stdout = sys.stderr
from chatterbox.tts import ChatterboxTTS  # noqa: E402

model = ChatterboxTTS.from_pretrained(device="cuda")
out.write(json.dumps({"ready": True, "sr": model.sr}) + "\n")
out.flush()
for line in sys.stdin:
    if not line.strip():
        continue
    try:
        r = json.loads(line)
        torch.manual_seed(int(r.get("seed", 0)))
        t = time.time()
        wav = model.generate(r["text"], audio_prompt_path=r["ref"], exaggeration=float(r.get("exaggeration", 0.5)),
                             cfg_weight=float(r.get("cfg", 0.5)), temperature=float(r.get("temperature", 0.8)))
        os.makedirs(os.path.dirname(os.path.abspath(r["out"])), exist_ok=True)
        sf.write(r["out"], wav.squeeze(0).cpu().numpy(), model.sr)
        out.write(json.dumps({"out": r["out"], "sec": round(wav.shape[-1] / model.sr, 2), "took": round(time.time() - t, 1)}) + "\n")
    except Exception as e:
        traceback.print_exc()
        out.write(json.dumps({"error": f"{type(e).__name__}: {e}"}) + "\n")
    out.flush()
