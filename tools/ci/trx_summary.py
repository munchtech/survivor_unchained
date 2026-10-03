#!/usr/bin/env python3
"""A test run's .trx (dotnet test --logger trx) as Markdown for a GitHub
Actions run summary: the counts, every failure with its message, and the
slowest tests, so a red run reads without opening the log."""
import sys
import xml.etree.ElementTree as ET

NS = {"t": "http://microsoft.com/schemas/VisualStudio/TeamTest/2010"}


def seconds(duration):
    h, m, s = duration.split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def main(path):
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError) as e:
        print(f"## Tests\n\nNo results to read ({e}): the run stopped before the tests.")
        return
    counters = root.find("t:ResultSummary/t:Counters", NS).attrib
    results = root.findall("t:Results/t:UnitTestResult", NS)
    failed = [r for r in results if r.get("outcome") == "Failed"]
    skipped = sum(1 for r in results if r.get("outcome") == "NotExecuted")
    mark = "❌" if failed else "✅"
    print(f"## {mark} Tests: {counters['passed']} passed, {len(failed)} failed, "
          f"{skipped} skipped of {counters['total']}\n")
    for r in failed:
        msg = r.findtext("t:Output/t:ErrorInfo/t:Message", "", NS).strip()
        trace = r.findtext("t:Output/t:ErrorInfo/t:StackTrace", "", NS).strip()
        print(f"<details><summary><b>{r.get('testName')}</b></summary>\n")
        print("```\n" + msg + "\n" + "\n".join(trace.splitlines()[:12]) + "\n```\n</details>\n")
    timed = sorted(results, key=lambda r: seconds(r.get("duration", "0:0:0")), reverse=True)[:10]
    if timed:
        print("| Slowest | s |\n|---|---|")
        for r in timed:
            print(f"| {r.get('testName')} | {seconds(r.get('duration', '0:0:0')):.2f} |")


if __name__ == "__main__":
    main(sys.argv[1])
