"""The gist of a run's log: python runlog.py NAME -> its report lines (zone, clock, overlay), its frames and any errors."""
import re, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
text = open(os.path.join(HERE, "logs", sys.argv[1] + ".log"), encoding="utf-8", errors="replace").read()
for line in text.splitlines():
    if line.startswith("[") and "s]" in line[:10]:
        m = re.match(r"\[\s*([\d.]+)s\] (\S+) hp ([\d/]+).*? at (\S+) (.*?)clock (\S+) ([\d.]+)s day (\d+)", line)
        if m:
            t, zone, hp, at, ov, tod, clock, day = m.groups()
            print(f"{t:>6}s {zone:10} hp {hp:8} {ov.strip():10} {tod:6} {clock:>7} day {day}")
    elif line.startswith("saved"):
        print("  frame", line.split("/")[-1])
    elif ("Exception" in line or "ERROR" in line or "SCRIPT" in line) and not any(k in line for k in ("RID", "singleton", "leaked", "ObjectDB")):
        print("  !!", line[:240])
