"""Add the man under the Ford-Warden (C03's last line: VOICES.md, 'the tired man under him')."""
import json
from collections import OrderedDict

P = "tools/vo/cast.json"
c = json.load(open(P, encoding="utf-8"), object_pairs_hook=OrderedDict)
c["voices"]["warden_man"] = OrderedDict([
    ("name", "The Ford-Warden, the man under him"),
    ("sex", "m"),
    ("age", 60),
    ("accent", "plain English, the accent worn almost away"),
    ("design", "A plain, tired man of sixty, an old soldier of a religious order, speaking quietly and close with a dry, worn, "
               "slightly hoarse baritone. English, the regional accent worn almost away. No boom, no grandeur: an ordinary "
               "man who has been very tired for a very long time."),
    ("ref_text", "Is it morning? I kept the lamps. Someone has to keep the lamps, or nobody knows where the water is."),
    ("room", "close"),
    ("tempo", [1.8, 2.6]),
    ("maya", "Realistic male voice in the 60s age with british accent, a tired old soldier. Low pitch, dry worn hoarse timbre, "
             "slow pacing, tired lost tone."),
])
s = json.dumps(c, indent=1, ensure_ascii=False)
open(P, "w", encoding="utf-8", newline="\n").write(s + "\n")
print("ok", len(c["voices"]))
