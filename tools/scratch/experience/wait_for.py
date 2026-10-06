"""Block until a file holds a pattern, or time runs out: python wait_for.py FILE REGEX [seconds]"""
import re, sys, time, os
f, pat = sys.argv[1], re.compile(sys.argv[2])
limit = float(sys.argv[3]) if len(sys.argv) > 3 else 540
t0 = time.time()
while time.time() - t0 < limit:
    if os.path.exists(f):
        s = open(f, encoding="utf-8", errors="replace").read()
        if pat.search(s):
            print(s[-1500:])
            sys.exit(0)
    time.sleep(3)
print("still waiting after", int(time.time() - t0), "s")
sys.exit(1)
