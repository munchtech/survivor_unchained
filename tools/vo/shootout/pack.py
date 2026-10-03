"""The shoot-out's sample pack: for each line and method, the best of its
takes (right words first, then the least made-sounding by tells.py), put
through the same mix (post.py: the scene's room, loudness for the volume),
written to docs/voice/samples/<line>__<method>.ogg, with every number in
docs/voice/samples/metrics.json for the README.

    python tools/vo/shootout/pack.py
"""
import glob
import json
import os
import re
import sys
from collections import defaultdict
from dataclasses import asdict

import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import analyse  # noqa: E402
import post  # noqa: E402
import tells  # noqa: E402
from common import FFMPEG, REFS, ROOT, TOOLS, accent_target, cast  # noqa: E402

RAW = os.path.join(TOOLS, "shootout", "raw")
OUT = os.path.join(ROOT, "docs", "voice", "samples")
LINES = json.load(open(os.path.join(HERE, "lines.json"), encoding="utf-8"))["lines"]
LUFS = {"quiet": -18.0, "level": -16.0, "shout": -14.0}
CACHE = os.path.join(TOOLS, "shootout", "heard.json")


def human(t: dict) -> float:
    """How much a take moves like a person: pace that changes, stress that
    lands, pitch that travels, breath. Each capped so no one measure wins."""
    return (min(t["pace_variation"], 0.3) * 6 + min(t["stress_spread_db"], 8) * 0.25
            + min(t["word_pitch_moves_st"], 4) * 0.35 + min(t["breaths"], 3) * 0.2)


def main():
    voices = cast()
    heard = json.load(open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else {}
    os.makedirs(OUT, exist_ok=True)
    metrics = {}
    for key, L in LINES.items():
        v = L["voice"]
        ref = os.path.join(REFS, f"{v}.flac")
        rw, rsr = sf.read(ref, dtype="float32")
        eref = analyse.speaker_embedding(rw, rsr)
        target = accent_target(v)
        takes = defaultdict(list)
        for p in sorted(glob.glob(os.path.join(RAW, key, "*.wav"))):
            method = re.sub(r"_s\d+$", "", os.path.basename(p)[:-4])
            takes[method].append(p)
        for method, paths in takes.items():
            best = None
            for p in paths:
                k = os.path.relpath(p, RAW)
                if k not in heard:
                    # One Whisper pass (with word times, for the tells) serves the word check too.
                    r = asdict(analyse.analyse(p, None, want=("utmos", "accent")))
                    tl = tells.tells(p)
                    r["said"] = tl["said"]
                    r["wer"], r["wrong"] = analyse.wer(L["text"], tl["said"])
                    r["wer"] = round(float(r["wer"]), 3)
                    r["faults"] = analyse.substantive(r["wrong"])
                    x, sr = sf.read(p, dtype="float32")
                    if x.ndim > 1:
                        x = x.mean(1)
                    r["similarity"] = float(np.dot(analyse.speaker_embedding(x, sr), eref))
                    r["tells"] = tl
                    heard[k] = r
                    json.dump(heard, open(CACHE, "w", encoding="utf-8"), indent=1)
                r = heard[k]
                acc = r["accent_top"].get(target, 0) if target else 1.0
                ok = not r["faults"] and "clipping" not in " ".join(r["artefacts"])
                score = (10 if ok else 0) + human(r["tells"]) + 0.5 * r["utmos"] + acc + r["similarity"]
                if best is None or score > best[0]:
                    best = (score, p, r, ok, acc)
            score, p, r, ok, acc = best
            x = post.master(p, L["room"], voices[v].get("sex", "m"), None, vol=L["vol"])
            line, _ = post.assemble([(x, L["room"])], vol=L["vol"])
            line = post.loudness(line, LUFS.get(L["vol"], -16.0))
            dst = os.path.join(OUT, f"{key}__{method}.ogg")
            post.write_ogg(line, dst, FFMPEG)
            metrics[f"{key}__{method}"] = {
                "take": os.path.basename(p), "of": len(paths), "words_right": ok, "faults": r["faults"],
                "said": r["said"], "accent": r["accent"], "accent_target_p": round(acc, 2), "utmos": r["utmos"],
                "similarity_to_cast_voice": round(r["similarity"], 2), "f0": r["pitch"]["f0_median"],
                "wps": r["words_per_sec"], "tells": {k2: v2 for k2, v2 in r["tells"].items() if k2 != "said"},
                "human": round(human(r["tells"]), 2), "artefacts": r["artefacts"],
            }
            print(f"{key:12s} {method:18s} {'ok ' if ok else 'BAD'} human {human(r['tells']):.2f} mos {r['utmos']:.2f} "
                  f"acc {r['accent']}({acc:.2f}) sim {r['similarity']:.2f} {r['faults'][:3]}", flush=True)
    json.dump(metrics, open(os.path.join(OUT, "metrics.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    listen_page(metrics)


def listen_page(metrics: dict):
    """listen.html beside the files: every line, every method, a player
    each, in the order to try them (open it in a browser)."""
    rows = []
    for key, L in LINES.items():
        rows.append(f"<h2>{key.split('_', 1)[1].title()}: {L['voice'].title()}</h2><p class=line>{L['text']}</p><table>")
        mine = sorted(((k, r) for k, r in metrics.items() if k.startswith(key + "__")), key=lambda kr: -kr[1]["human"])
        for k, r in mine:
            method = k.split("__")[1]
            flag = "" if r["words_right"] else " (words wrong)"
            rows.append(f"<tr><td class=m>{method}{flag}</td><td><audio controls preload=none src='{k}.ogg'></audio></td>"
                        f"<td class=n>moves like a person {r['human']:.1f} · heard as {r['accent']} · same voice {r['similarity_to_cast_voice']:.2f}</td></tr>")
        rows.append("</table>")
    html = ("<!doctype html><meta charset=utf-8><title>Voice shoot-out</title><style>body{font:15px/1.5 system-ui;margin:2em;"
            "max-width:1100px;background:#141218;color:#e8dcc4}h2{margin-top:2em;color:#f3d9a0}.line{font-style:italic;color:#bfb29c}"
            "td{padding:4px 10px}.m{font-family:monospace}.n{color:#9a907e;font-size:13px}audio{height:32px}</style>"
            "<h1>Voice shoot-out</h1><p>Same five lines, every method. Listen with headphones; judge by ear. Notes in README.md.</p>"
            + "".join(rows))
    open(os.path.join(OUT, "listen.html"), "w", encoding="utf-8").write(html)


if __name__ == "__main__":
    main()
