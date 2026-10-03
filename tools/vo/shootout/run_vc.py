"""Performance first, voice second: convert a performance to the cast voice
with Seed-VC (zero-shot voice conversion, GPL-3.0 code). The performance
keeps its timing, stresses and breath; the timbre becomes the part's.

Sources are other methods' takes in raw/<line>/ (by prefix); the target is
the part's cast reference. Two modes: `vc` (speech model, 22 kHz) and
`vcf0` (the 44 kHz model, which also follows the performance's pitch
contour, shifted into the part's range).

    cd ~/vo-tools/seed-vc && ../seedvc/Scripts/python <repo>/tools/vo/shootout/run_vc.py vox_design orpheus
"""
import glob
import json
import os
import sys

import soundfile as sf

sys.path.insert(0, os.getcwd())
from seed_vc_wrapper import SeedVCWrapper  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
REFS = os.path.join(os.path.dirname(HERE), "refs")
RAW = os.path.join(os.environ.get("VO_TOOLS", os.path.expanduser("~/vo-tools")), "shootout", "raw")
LINES = json.load(open(os.path.join(HERE, "lines.json"), encoding="utf-8"))["lines"]
sources = sys.argv[1:] or ["vox_design", "orpheus"]
w = SeedVCWrapper()
for key, L in LINES.items():
    ref = os.path.join(REFS, f"{L['voice']}.flac")
    if not os.path.exists(ref):
        continue
    for src in sources:
        for path in sorted(glob.glob(os.path.join(RAW, key, f"{src}_s*.wav"))):
            seed = path.rsplit("_s", 1)[1][:-4]
            for mode, f0 in (("vc", False), ("vcf0", True)):
                out = os.path.join(RAW, key, f"{src}-{mode}_s{seed}.wav")
                if os.path.exists(out):
                    continue
                gen = w.convert_voice(path, ref, diffusion_steps=30, length_adjust=1.0, inference_cfg_rate=0.7,
                                      f0_condition=f0, auto_f0_adjust=True, pitch_shift=0, stream_output=False)
                # The wrapper is a generator either way; unstreamed, it returns the whole take at the end.
                try:
                    while True:
                        next(gen)
                except StopIteration as e:
                    audio = e.value
                sf.write(out, audio, 44100 if f0 else 22050)
                print(key, src, mode, seed, flush=True)
