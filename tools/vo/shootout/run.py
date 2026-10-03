"""The shoot-out's takes, for the methods that run through this repo's
workers (VoxCPM2 three ways, Chatterbox). Other models have their own
scripts beside this one; all write to VO_TOOLS/shootout/raw/<line>/.

    python tools/vo/shootout/run.py vox_cont vox_style vox_design chatterbox [--seeds 4]
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from common import REFS, TOOLS, Worker, cast, voxcpm  # noqa: E402
from cast_session import ref_text  # noqa: E402

RAW = os.path.join(TOOLS, "shootout", "raw")
LINES = json.load(open(os.path.join(HERE, "lines.json"), encoding="utf-8"))["lines"]


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("methods", nargs="+")
    ap.add_argument("--seeds", type=int, default=4)
    ap.add_argument("--only")
    a = ap.parse_args(argv)
    voices = cast()
    vox = voxcpm() if any(m.startswith("vox") for m in a.methods) else None
    cb = Worker(os.path.join(TOOLS, "chatterbox", "Scripts", "python.exe"), os.path.join(os.path.dirname(HERE), "backends", "chatterbox_worker.py")) if "chatterbox" in a.methods else None
    try:
        for key, L in LINES.items():
            if a.only and a.only not in key:
                continue
            v = L["voice"]
            ref = os.path.join(REFS, f"{v}.flac")
            if not os.path.exists(ref):
                print(f"{key}: no cast reference for {v} yet"); continue
            d = os.path.join(RAW, key)
            os.makedirs(d, exist_ok=True)
            for m in a.methods:
                for s in range(1, a.seeds + 1):
                    out = os.path.join(d, f"{m}_s{s}.wav")
                    if os.path.exists(out):
                        continue
                    if m == "vox_cont":
                        r = vox.ask(text=L["text"], ref=ref, prompt_wav=ref, prompt_text=ref_text(v), seed=s, out=out, steps=25)
                    elif m == "vox_style":
                        r = vox.ask(text=L["text"], ref=ref, style=L["style"], seed=s, out=out, steps=25)
                    elif m == "vox_design":
                        r = vox.ask(text=L["text"], design=voices[v]["design"] + " " + L["act"], seed=s, out=out, steps=25)
                    elif m == "chatterbox":
                        r = cb.ask(text=L["text"], ref=ref, seed=s, out=out, exaggeration=L["exag"], cfg=0.3 if L["exag"] > 0.6 else 0.5)
                    print(key, m, s, r, flush=True)
    finally:
        for w in (vox, cb):
            if w:
                w.close()


if __name__ == "__main__":
    main(sys.argv[1:])
