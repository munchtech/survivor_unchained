"""Seed-VC (zero-shot voice conversion; GPL-3.0 code) as a long-running
worker, the same protocol as voxcpm_worker.py: a performance in, the same
performance in the cast voice out. Runs from inside a Seed-VC checkout
with its venv (tools/vo/README.md).

Request: {"source": "performance.wav", "target": "refs/rook.flac", "out": "take.wav",
          "f0": false, "steps": 30, "cfg": 0.7}
"""
import json
import os
import sys
import time
import traceback

import soundfile as sf

out = sys.stdout
sys.stdout = sys.stderr
sys.path.insert(0, os.getcwd())
from seed_vc_wrapper import SeedVCWrapper  # noqa: E402

w = SeedVCWrapper()
out.write(json.dumps({"ready": True, "sr": 22050}) + "\n")
out.flush()
for line in sys.stdin:
    if not line.strip():
        continue
    try:
        r = json.loads(line)
        f0 = bool(r.get("f0", False))
        t = time.time()
        gen = w.convert_voice(r["source"], r["target"], diffusion_steps=int(r.get("steps", 30)), length_adjust=1.0,
                              inference_cfg_rate=float(r.get("cfg", 0.7)), f0_condition=f0, auto_f0_adjust=True,
                              pitch_shift=0, stream_output=False)
        try:
            while True:
                next(gen)
        except StopIteration as e:
            audio = e.value
        sr = 44100 if f0 else 22050
        os.makedirs(os.path.dirname(os.path.abspath(r["out"])), exist_ok=True)
        sf.write(r["out"], audio, sr)
        out.write(json.dumps({"out": r["out"], "sec": round(len(audio) / sr, 2), "took": round(time.time() - t, 1)}) + "\n")
    except Exception as e:
        traceback.print_exc()
        out.write(json.dumps({"error": f"{type(e).__name__}: {e}"}) + "\n")
    out.flush()
