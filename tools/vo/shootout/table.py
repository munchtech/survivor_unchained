"""Print the sample pack's numbers as Markdown tables (for its README):
per method across the five lines, and per line."""
import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from common import ROOT  # noqa: E402

m = json.load(open(os.path.join(ROOT, "docs", "voice", "samples", "metrics.json"), encoding="utf-8"))
by = defaultdict(list)
for k, r in m.items():
    line, method = k.split("__")
    by[method].append((line, r))


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else 0


print("| Method | Lines | Words right | Accent heard right | Same voice as cast | Naturalness (UTMOS) | Moves like a person | Pace changes | Stress spread dB | Breaths |")
print("|---|---|---|---|---|---|---|---|---|---|")
rows = []
for method, rs in by.items():
    rows.append((mean(r["human"] for _, r in rs), method, rs))
for h, method, rs in sorted(rows, reverse=True):
    print(f"| {method} | {len(rs)} | {sum(r['words_right'] for _, r in rs)}/{len(rs)} | {mean(r['accent_target_p'] for _, r in rs):.2f} | "
          f"{mean(r['similarity_to_cast_voice'] for _, r in rs):.2f} | {mean(r['utmos'] for _, r in rs):.2f} | {h:.2f} | "
          f"{mean(r['tells']['pace_variation'] for _, r in rs):.2f} | {mean(r['tells']['stress_spread_db'] for _, r in rs):.1f} | "
          f"{mean(r['tells']['breaths'] for _, r in rs):.1f} |")
print()
for line in sorted({k.split('__')[0] for k in m}):
    print(f"\n**{line}**\n")
    print("| Method | Words | Heard as | Same voice | UTMOS | Moves like a person | Said |")
    print("|---|---|---|---|---|---|---|")
    for k, r in sorted(((k, r) for k, r in m.items() if k.startswith(line)), key=lambda kr: -kr[1]["human"]):
        said = r["said"][:70].replace("|", "/")
        print(f"| {k.split('__')[1]} | {'ok' if r['words_right'] else ', '.join(r['faults'][:3])} | {r['accent']} ({r['accent_target_p']:.2f}) | "
              f"{r['similarity_to_cast_voice']:.2f} | {r['utmos']:.2f} | {r['human']:.2f} | {said} |")
