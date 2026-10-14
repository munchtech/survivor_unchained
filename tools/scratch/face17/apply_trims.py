"""apply_trims.py TRIMS.txt: multiply People.cs's HerBodyTone by each face's body gains and HerFaceTone by its face
gains (trims.py's output). Keeps the file's BOM and CRLF."""
import re, sys
P = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\godot\src\Actors\People.cs"
g = {}
for line in open(sys.argv[1], encoding="utf-8"):
    m = re.match(r"(\w+)\s+cheek.*body \(([\d.]+), ([\d.]+), ([\d.]+)\) face x\(([\d.]+), ([\d.]+), ([\d.]+)\)", line)
    if m: g[m.group(1)] = ([float(v) for v in m.group(2, 3, 4)], [float(v) for v in m.group(5, 6, 7)])
raw = open(P, "rb").read().decode("utf-8-sig")
def block(s, name, idx):
    a = s.index("Dictionary<string, Vector3> %s = new()" % name); b = s.index("};", a)
    def rep(m):
        f = m.group(1)
        if f not in g: return m.group(0)
        v = [float(m.group(i)) * g[f][idx][i - 2] for i in (2, 3, 4)]
        return '["%s"] = new(%.3ff, %.3ff, %.3ff)' % (f, *v)
    return s[:a] + re.sub(r'\["(\w+)"\] = new\(([\d.]+)f, ([\d.]+)f, ([\d.]+)f\)', rep, s[a:b]) + s[b:]
raw = block(raw, "HerBodyTone", 0); raw = block(raw, "HerFaceTone", 1)
open(P, "wb").write(b"\xef\xbb\xbf" + raw.encode("utf-8"))
print("applied", sorted(g))
