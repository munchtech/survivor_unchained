"""A quick look at some raw shoot-out takes before the pack: the words heard,
the accent, and the tells. `python tools/vo/shootout/peek.py 1_angry/maya_s1 ...`"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import analyse  # noqa: E402
import tells  # noqa: E402
from common import TOOLS  # noqa: E402

RAW = os.path.join(TOOLS, "shootout", "raw")
LINES = json.load(open(os.path.join(HERE, "lines.json"), encoding="utf-8"))["lines"]

for name in sys.argv[1:]:
    key = name.split("/")[0]
    p = os.path.join(RAW, name + ".wav")
    r = analyse.analyse(p, None, want=("utmos", "accent"))
    t = tells.tells(p)
    wer, wrong = analyse.wer(LINES[key]["text"], t["said"])
    print(f"{name}: {r.seconds:.1f} s, mos {r.utmos:.2f}, accent {r.accent_top}, f0 {r.pitch.get('f0_median', 0):.0f}, wrong {analyse.substantive(wrong)}")
    print(f"   said: {t['said']}")
    print(f"   tells: pace {t['pace_variation']}, stress {t['stress_spread_db']} dB, pitch moves {t['word_pitch_moves_st']} st, "
          f"breaths {t['breaths']}, longest gap {t['longest_gap_s']} s")
