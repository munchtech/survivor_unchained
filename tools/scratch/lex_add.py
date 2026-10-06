"""Whisper's spellings of words the placeholders said right (names, homophones, a broken-off word)."""
import json

P = "tools/vo/lexicon.json"
d = json.load(open(P, encoding="utf-8"))
ADD = {
    "ashe": ["ash"],                 # the dead man in Rook's story
    "wenna": ["wenner"],             # non-rhotic
    "brannoc": ["branagh"],
    "aumery": ["omri", "aumry"],
    "redi": ["ready", "reddy"],      # the Barrow Lord's Latin
    "c": ["sea", "see"],             # the letter
    "one": ["won"],
    "saw": ["sore"],                 # non-rhotic
    "chid will": ["chiddle"],        # "Chid'll"
    "m": ["him", "mm", "em"],        # Grimtunnel's "surface-m—", broken off
}
for k, v in ADD.items():
    have = d["hear"].setdefault(k, [])
    for w in v:
        if w not in have:
            have.append(w)
open(P, "w", encoding="utf-8", newline="\n").write(json.dumps(d, indent=1, ensure_ascii=False) + "\n")
print("ok")
