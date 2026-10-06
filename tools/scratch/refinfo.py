import json
import os
import sys

import soundfile as sf

REFS = sys.argv[1]
book = json.load(open(os.path.join(REFS, "casting.json"), encoding="utf-8"))
for v in sys.argv[2:]:
    i = sf.info(os.path.join(REFS, f"{v}.flac"))
    print(v, round(i.duration, 1), i.samplerate, json.dumps(book.get(v, {}), ensure_ascii=False)[:400])
