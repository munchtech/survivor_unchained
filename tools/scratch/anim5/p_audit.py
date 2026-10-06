from pathlib import Path
p = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa15f092820132274\tools\anim\audit.py")
t = p.read_text(encoding="utf-8")
E = [
    ('''- the hand's turn on the forearm, split into the wrist's bend and a twist
  about the hand's length (the wrist has none of its own: a twist there
  is a forearm twist put in the wrong bone);''',
     '''- the hand's turn on the forearm, split into the wrist's bend and a twist
  about the hand's length (the wrist has none of its own: a twist there
  is a forearm twist put in the wrong bone); the bend split again as a
  wrist bends, toward the palm or the back (flexion, extension: far) and
  toward the thumb or the little finger (radial, ulnar: a little), on the
  wrist's own axes, which turn with the forearm as it rolls;'''),
    ('''wrist twist past WRIST_TWIST; a wrist bend past WRIST_BEND; a forearm twist
past FORE_TWIST from rest; an elbow bent sideways past ELBOW_SIDE. Reports
the worst frames of each clip.''',
     '''wrist twist past WRIST_TWIST; a wrist bend past WRIST_BEND, or past what a
wrist can do (FLEX, EXT, RADIAL, ULNAR: a few degrees past the solver's own
limits, keyed.Rig); a forearm twist past FORE_TWIST from rest; an elbow
bent sideways past ELBOW_SIDE. Reports the worst frames of each clip.'''),
    ('''ELBOW_SIDE = 25.0
''', '''ELBOW_SIDE = 25.0
FLEX, EXT, RADIAL, ULNAR = 80.0, 70.0, 25.0, 40.0
'''),
    ('''def angle(a, b):''', '''def wrist_bend(dh, y, side):
    """A hand's local turn from rest (dh) as the wrist's flexion (+ toward the
    palm) and deviation (+ toward the thumb), degrees: the twist about the
    hand's length (y) taken off first, so the bend is read on the axes the
    forearm's roll leaves (dh = twist * bend)."""
    t = np.array([*(y * np.dot(dh[:3], y)), dh[3]])
    n = np.linalg.norm(t)
    t = t / n if n > 1e-9 else np.array([0, 0, 0, 1.0])
    s = qmul(qinv(t), dh)
    if s[3] < 0:
        s = -s
    a = 2 * math.acos(min(1.0, s[3]))
    if a < 1e-6 or np.linalg.norm(s[:3]) < 1e-9:
        return 0.0, 0.0
    ax = s[:3] / np.linalg.norm(s[:3])
    # The hand's +Z is its thumb side (keyed.Rig); +X = Y x Z is the back of
    # her right hand and the palm of her left.
    z = np.array([0, 0, 1.0]) - y * y[2]
    z = z / np.linalg.norm(z)
    x = np.cross(y, z)
    d = math.degrees(a)
    return d * float(np.dot(ax, z)) * (1 if side == "r" else -1), d * float(np.dot(ax, x))


def angle(a, b):'''),
    ('''            rows.append((f, step, step_fa, fa_tw, h_sw, h_tw, roll_h, roll_fa))
        flags = []
        for f, step, step_fa, fa_tw, h_sw, h_tw, roll_h, roll_fa in rows:''',
     '''            flex, dev = wrist_bend(dh, h_axis, s)
            rows.append((f, step, step_fa, fa_tw, h_sw, h_tw, roll_h, roll_fa, flex, dev))
        flags = []
        for f, step, step_fa, fa_tw, h_sw, h_tw, roll_h, roll_fa, flex, dev in rows:'''),
    ('''            if h_sw > WRIST_BEND:
                why.append(f"wrist bend {h_sw:.0f}")''',
     '''            if h_sw > WRIST_BEND:
                why.append(f"wrist bend {h_sw:.0f}")
            if dev > RADIAL or -dev > ULNAR:
                why.append(f"wrist bent {'to the thumb' if dev > 0 else 'to the little finger'} {abs(dev):.0f}")
            if flex > FLEX or -flex > EXT:
                why.append(f"wrist {'flexed' if flex > 0 else 'bent back'} {abs(flex):.0f}")'''),
    ('''                  "max_fore_twist": max(abs(r[3]) for r in rows), "flags": flags}''',
     '''                  "max_fore_twist": max(abs(r[3]) for r in rows), "max_dev": max(abs(r[9]) for r in rows),
                  "flags": flags}'''),
    ('''                                 f"wbend {o['max_wrist_bend']:.0f} ftw {o['max_fore_twist']:.0f} elbow {out['elbow_' + s]:.0f} "''',
     '''                                 f"wbend {o['max_wrist_bend']:.0f} wdev {o['max_dev']:.0f} ftw {o['max_fore_twist']:.0f} elbow {out['elbow_' + s]:.0f} "'''),
]
for a, b in E:
    assert t.count(a) == 1, a[:60]
    t = t.replace(a, b)
p.write_text(t, encoding="utf-8")
print("ok")
