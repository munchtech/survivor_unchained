"""Shoot-out takes through Voicebox (tools/vo/voicebox.py), every cloning
engine it has, from two kinds of reference:

- `vb_<engine>`: the part's cast reference (a designed read, tools/vo/refs).
- `vb_<engine>-acted`: an acted performance of the line already converted
  into the part's voice (the best of the perform-then-convert takes), so the
  engine clones a person mid-performance rather than a reader. Both
  references are our own generated voices.

Chatterbox Turbo gets the line's beats as its tags ([sigh], [chuckle]...).
Three seeds a method; tools/vo/shootout/pack.py picks and mixes the best.

    python tools/vo/shootout/run_voicebox.py [engine ...]   (the server must be running)
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from cast_session import ref_text  # noqa: E402
from common import REFS, TOOLS  # noqa: E402
from voicebox import Voicebox, VoiceboxError  # noqa: E402

RAW = os.path.join(TOOLS, "shootout", "raw")
LINES = json.load(open(os.path.join(HERE, "lines.json"), encoding="utf-8"))["lines"]
ENGINES = ["chatterbox_turbo", "qwen", "chatterbox", "luxtts", "tada"]
SHORT = {"chatterbox_turbo": "turbo", "qwen": "qwen", "chatterbox": "cb", "luxtts": "lux", "tada": "tada"}
# The acted performance each line's "-acted" reference is taken from, best first (pack.py's heard.json picks).
ACTED = ("maya-vc", "dia-vc", "orpheus-vcf0", "orpheus-vc", "vox_design-vc")
TURBO_TAG = {"sniffle": "sniff", "giggle": "laugh", "angry": "", "sarcastic": "", "cry": "sniff"}


def turbo_text(L: dict) -> str:
    """Orpheus's tagged script in Chatterbox Turbo's bracket tags. Turbo
    tends to end the take at a tag in mid-line (the first round lost
    everything after Holloway's [sigh]), so only a tag at either end is kept."""
    text = L["orpheus"][1]

    def tag(m):
        t = TURBO_TAG.get(m.group(1), m.group(1))
        return f"[{t}]" if t else ""
    text = re.sub(r"\s+", " ", re.sub(r"<(\w+)>", tag, text)).strip()
    head = re.match(r"^(\[[\w ]+\])\s*", text)
    tail = re.search(r"\s*(\[[\w ]+\])$", text)
    core = re.sub(r"\s*\[[\w ]+\]\s*", " ", text[head.end() if head else 0: tail.start() if tail else len(text)]).strip()
    return " ".join(x for x in ((head.group(1) if head else ""), core, (tail.group(1) if tail else "")) if x)


def acted_ref(key: str) -> str | None:
    """The best converted performance of this line, by pack.py's measures."""
    heard_path = os.path.join(TOOLS, "shootout", "heard.json")
    heard = json.load(open(heard_path, encoding="utf-8")) if os.path.exists(heard_path) else {}
    for method in ACTED:
        takes = [(k, r) for k, r in heard.items()
                 if k.replace("\\", "/").startswith(f"{key}/{method}_s") and not r.get("faults")]
        if takes:
            k, _ = max(takes, key=lambda kr: kr[1]["tells"]["pace_variation"] + kr[1]["similarity"])
            return os.path.join(RAW, k)
    return None


def main(engines):
    vb = Voicebox()
    vb.health()
    for key, L in LINES.items():
        v = L["voice"]
        cast = vb.make_profile(f"su_{v}", [(os.path.join(REFS, f"{v}.flac"), ref_text(v))],
                               description=f"Survivor Unchained cast voice: {v} (designed, VoxCPM2)")
        acted = acted_ref(key)
        actedp = vb.make_profile(f"su_{v}_{key}_acted", [(acted, L["text"])], replace=True,
                                 description=f"{v} acting {key} ({os.path.basename(acted)})") if acted else None
        for eng in engines:
            text = turbo_text(L) if eng == "chatterbox_turbo" else L["text"]
            for prof, suffix in ((cast, ""), (actedp, "-acted")):
                if prof is None:
                    continue
                for seed in (1, 2, 3):
                    out = os.path.join(RAW, key, f"vb_{SHORT[eng]}{suffix}_s{seed}.wav")
                    if os.path.exists(out):
                        continue
                    try:
                        r = vb.generate(prof["id"], text, out, engine=eng, seed=seed)
                        print(key, eng + suffix, seed, f"{r['duration']} s in {r['took']} s", flush=True)
                    except VoiceboxError as e:
                        print(key, eng + suffix, seed, "FAILED", e, flush=True)
        print(key, "acted reference:", acted, flush=True)
    vb.free()


if __name__ == "__main__":
    main(sys.argv[1:] or ENGINES)
