"""Shoot-out baseline: Kokoro-82M (Apache 2.0) stock British voices. Clean,
in accent, and unacted: the yardstick for "reads, does not perform"."""
import json
import os

import numpy as np
import soundfile as sf
from kokoro import KPipeline

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(os.environ.get("VO_TOOLS", os.path.expanduser("~/vo-tools")), "shootout", "raw")
LINES = json.load(open(os.path.join(HERE, "lines.json"), encoding="utf-8"))["lines"]
VOICE = {"holloway": "bm_george", "sella": "bf_lily", "rook": "bf_emma", "brannoc": "bm_lewis", "redcowl": "bm_daniel"}
p = KPipeline(lang_code="b")
for key, L in LINES.items():
    d = os.path.join(RAW, key)
    os.makedirs(d, exist_ok=True)
    audio = [a for _, _, a in p(L["text"], voice=VOICE[L["voice"]])]
    sf.write(os.path.join(d, "kokoro_s1.wav"), np.concatenate(audio), 24000)
    print(key, flush=True)
