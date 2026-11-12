"""Keep per-case timings and compare the full suite's names and outcomes."""

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path
import xml.etree.ElementTree as ET


NS = {"t": "http://microsoft.com/schemas/VisualStudio/TeamTest/2010"}
STATIONARY = ("BlockAnswerTests.", "ClockTests.", "StatusWeightTests.",
              "ProcWeightTests.", "TailWeightTests.")


def seconds(duration):
    hours, minutes, secs = duration.split(":")
    return int(hours) * 3600 + int(minutes) * 60 + float(secs)


def read(path):
    root = ET.parse(path).getroot()
    rows = [
        {"test": r.attrib["testName"], "outcome": r.attrib["outcome"],
         "seconds": seconds(r.attrib.get("duration", "00:00:00"))}
        for r in root.findall("t:Results/t:UnitTestResult", NS)
    ]
    return root, sorted(rows, key=lambda r: (-r["seconds"], r["test"]))


def outputs(root):
    return {r.attrib["testName"]: (r.findtext("t:Output/t:StdOut", "", NS)).strip()
            for r in root.findall("t:Results/t:UnitTestResult", NS)}


def cards(root):
    output = next(v for k, v in outputs(root).items() if "DraftCardFitTests." in k)
    match = re.search(r"card_fit: (\d+) cards, (\d+) failed", output)
    if not match or int(match[2]) != 0:
        raise SystemExit("The real card harness did not report a clean fit pass.")
    return int(match[1])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trx", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--compare", type=Path)
    args = parser.parse_args()
    root, rows = read(args.trx)
    if not rows:
        raise SystemExit("No test results; an aborted runner is not a timing baseline.")
    card_count = cards(root)
    checked_outputs = 0
    if args.compare:
        before_root, before = read(args.compare)
        identity = lambda cases: Counter((r["test"], r["outcome"]) for r in cases)
        lost, added = identity(before) - identity(rows), identity(rows) - identity(before)
        if lost or added:
            raise SystemExit(f"Case/outcome mismatch: missing={dict(lost)}, added={dict(added)}")
        if cards(before_root) != card_count:
            raise SystemExit("The number of cards checked changed.")
        before_output = outputs(before_root)
        for name, output in outputs(root).items():
            if name.removeprefix("SurvivorUnchained.Tests.").startswith(STATIONARY):
                if output != before_output[name]:
                    raise SystemExit(f"Stationary harness output changed: {name}")
                checked_outputs += 1
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["test", "outcome", "seconds"])
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({"cases": len(rows), "outcomes": dict(Counter(r["outcome"] for r in rows)),
                      "cards": card_count, "stationaryOutputsMatched": checked_outputs,
                      "summedCaseSeconds": sum(r["seconds"] for r in rows),
                      "counters": root.find("t:ResultSummary/t:Counters", NS).attrib}))
    for i, r in enumerate(rows[:25], 1):
        print(f"| {i} | `{r['test'].removeprefix('SurvivorUnchained.Tests.')}` | {r['seconds']:.3f} | |")


if __name__ == "__main__":
    main()
