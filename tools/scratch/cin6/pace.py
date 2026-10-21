"""Pacing table: python pace.py LOG CINE [CINE...]
For each shot: its laid-out start and length (lines at their takes' length, fits and tails as the player lays them),
the lines in it (start-end, shot-local), the last thing that starts or ends in it, the quiet tail after that,
the camera's move, and her motion between the --stills frames (max bone travel in cm between consecutive stills)."""
import json, re, sys, math
G = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\cine-4\godot\data"
idx = json.load(open(G + r"\vo\index.json", encoding="utf-8"))["lines"]
dia = json.load(open(G + r"\content\dialogue.json", encoding="utf-8"))


def text_of(lid):
    conv, node = lid.split(".", 1)
    c = dia.get(conv) or {}
    n = (c.get("nodes") or {}).get(node) or {}
    t = n.get("text")
    if isinstance(t, list): t = t[0]["text"] if t and isinstance(t[0], dict) else (t[0] if t else "")
    return t or ""


def secs(lid):
    k = f"dlg.{lid}.0"
    if k in idx: return idx[k].get("read") or idx[k]["sec"]
    words = len([w for w in re.split(r"[ /]", re.sub(r"\([^)]*\)", " ", text_of(lid))) if w])
    return max(1.2, 0.5 + words / 2.6)


def off(at, dur):
    if at is None: return 0.0
    if isinstance(at, (int, float)): return min(at, dur)
    s = at.replace(" ", "")
    if s == "end": return dur
    if s.startswith("end-"): return max(0, dur - float(s[4:]))
    return min(float(s), dur)


def at_of(at, dur, t, ends, wait=False):
    if isinstance(at, str) and at.startswith("after:"):
        s = at[6:].replace(" ", "")
        k = next((i for i, ch in enumerate(s) if ch in "+-" and i > s.find(".")), -1)
        lid = s[:k] if k > 0 else s
        add = float(s[k:]) if k > 0 else 0
        v = ends.get(lid, t) + add - t
        return max(0, v) if wait else min(max(0, v), dur)
    return off(at, dur)


def lay(cid, facts=()):
    f = json.load(open(G + rf"\cinematics\{cid}.json", encoding="utf-8"))
    t, ends, out = 0.0, {}, []
    for sh in f["shots"]:
        w = sh.get("when") or {}
        if w.get("facts") and any((x[1:] in facts) if x.startswith("!") else (x not in facts) for x in w["facts"]): continue
        if w.get("calling") and "warden" not in w["calling"]: continue
        cues = [c for c in sh.get("cues", []) if not (c.get("when") or {}).get("calling") or "warden" in c["when"]["calling"]]
        dur = sh["dur"]
        for c in cues:
            if c.get("do") == "line": ends[c["id"]] = t + at_of(c.get("at"), sh["dur"], t, ends, True) + secs(c["id"])
        for lid in sh.get("fit") or []: dur = max(dur, ends[lid] - t + sh.get("tail", 0))
        events = []
        for c in cues:
            ct = at_of(c.get("at"), dur, t, ends)
            d = c.get("do")
            if d == "line":
                ends[c["id"]] = t + ct + secs(c["id"])
                events.append((ct, ct + secs(c["id"]), "line " + c["id"].split(".")[1]))
            elif d in ("move",): events.append((ct, ct + c.get("dur", 0), f"move {c.get('actor','her')}->{c.get('to')}"))
            elif d in ("anim",): events.append((ct, ct, f"anim {c.get('actor','her')} {c.get('clip')}"))
            elif d in ("face", "head", "gaze", "look", "lids"): events.append((ct, ct + c.get("over", 0), d))
            elif d in ("sfx", "vfx", "event", "spawn", "light", "glow", "prop", "hold", "hide", "lamp"): events.append((ct, ct + c.get("over", 0), d + " " + str(c.get("name") or c.get("kind") or c.get("actor") or "")))
        cam = sh.get("cam", {})
        mv = cam.get("move")
        camtxt = ""
        if mv:
            s0 = off(mv.get("start", 0), dur); s1 = off(mv.get("end", "end"), dur)
            camtxt = f"cam move {s0:.1f}-{s1:.1f}" + (" follow" if mv.get("follow") else "")
        elif isinstance(cam.get("at"), dict) and cam["at"].get("track"): camtxt = "cam tracks " + cam["at"].get("bone", "")
        last = max([e[1] for e in events] + [0])
        out.append(dict(id=sh["id"], t=t, dur=dur, events=events, cam=camtxt, last=last, note=sh.get("note", "")))
        t += dur
    return out, t


def motion(log, cid):
    """her bone travel between consecutive stills of each shot, cm (max over bones)."""
    rx = re.compile(r"cinebones (\S+) s(\S+) (\S+) (head=.*)")
    per = {}
    for line in open(log, encoding="utf-8", errors="replace"):
        m = rx.search(line)
        if not m or m.group(1) != cid: continue
        pts = dict((k, tuple(map(float, v.split(",")))) for k, v in re.findall(r"(\w+)=\(([-\d.,]+)\)", m.group(4)))
        per.setdefault((m.group(2), m.group(3)), []).append(pts)
    res = {}
    for (sid, who), frames in per.items():
        mv = []
        for a, b in zip(frames, frames[1:]):
            mv.append(max([math.dist(a[k], b[k]) for k in a if k in b and len(a[k]) == len(b[k])] + [0]) * 100)
        res.setdefault(sid, {})[who] = mv
    return res


log = sys.argv[1]
for cid in sys.argv[2:]:
    shots, total = lay(cid)
    mo = motion(log, cid)
    print(f"== {cid}: {total:.1f} s, {len(shots)} shots")
    for s in shots:
        m = mo.get(s["id"], {})
        mt = " | ".join(w + " " + " ".join(f"{x:.1f}" for x in v) for w, v in m.items() if not w.startswith("drowned") or w == "drowned.0")
        lines = "; ".join(f"{e[2][5:]} {e[0]:.1f}-{e[1]:.1f}" for e in s["events"] if e[2].startswith("line"))
        print(f"{s['id']:>4} @{s['t']:5.1f} {s['dur']:4.1f}s  last {s['last']:4.1f}  tail {s['dur']-s['last']:4.1f}  {s['cam']:<22} cm/still: [{mt}]  {lines}")
