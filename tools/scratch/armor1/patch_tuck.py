# Refactor the outfit tuck loop in heroine_outfits.py into tuck_of(name, objs, slot=None) (CRLF kept).
import re, sys
p = sys.argv[1]
src = open(p, encoding="utf-8", newline="").read()
NL = "\r\n"
L = src.split(NL)
i0 = next(i for i, l in enumerate(L) if l == "if BODY_OUT:" and "hide nothing" in L[i - 1])
assert L[i0 + 1] == "    me = body.data"
f0 = next(i for i in range(i0, i0 + 10) if L[i] == "    for name in OUTFITS:")
assert L[f0 + 1] == "        k = CHANNELS.index(name)"
assert L[f0 + 2].startswith("        objs = [o for o in made if o.name.startswith(name + \".\") and o.get(\"hides\")]")
assert L[f0 + 3] == "        if not objs or k > 3:" and L[f0 + 4] == "            continue"
f1 = next(i for i in range(f0, f0 + 400) if L[i] == '        print("HIDES", name, hid, "of", len(me.vertices), "vertices of her skin")')
body = L[f0 + 5:f1 + 1]
pat = re.compile(r"vals\[((?:[^\[\]]|\[[^\[\]]*\])*?), k\]")
out = []
for l in body:
    assert l == "" or l.startswith("        "), l
    l = l[4:] if l else l
    while pat.search(l):
        l = pat.sub(lambda m: "t[%s]" % m.group(1), l)
    assert "vals" not in l and ", k]" not in l, l
    l = re.sub(r"(?<![\w.])print\(", "say(", l)
    if l == "    for v in me.vertices:":
        out.append(l)
        out.append("        if skip_ is not None and skip_[v.index]:")
        out.append("            continue")
        continue
    if l.lstrip().startswith('if ARC_HANDS in ("fingerless", "glove") and os.environ.get("ARC_CAPS", "1") == "1" and GLOVE_TUCK_IN > 0:'):
        l = l[:-1] + ' and (whole or any(o.name.startswith("arcanist.glove_") for o in objs)):'
    if l == "    if name in BALD:":
        l = '    if name in BALD and (whole or slot == "head"):'
    if l == '    if name in ("ranger", "warden"):':
        l = '    if name in ("ranger", "warden") and (whole or slot == "boots"):'
    out.append(l)
for need in ('and (whole or any(o.name.startswith("arcanist.glove_")', 'slot == "head"', 'slot == "boots"', "skip_[v.index]"):
    assert any(need in l for l in out), need
head = '''def tuck_of(name, objs, slot=None):
    """Her skin's tuck (0..1 a vertex of her body, as one channel of its `hide` colours holds it) under `objs`,
    the hiding pieces of outfit `name`: all of them (slot None: that outfit's channel, as it always was), or
    one slot's (armor lead 1: the tuck a slot carries, for the game to take the max over what she wears).
    The rules tied to one piece (the arcanist glove's top, the boot's foot, a hat's hair) apply only in
    the slot that holds it."""
    me = body.data
    mw3 = body.matrix_world.to_3x3()
    t = np.zeros(len(me.vertices))
    whole = slot is None
    say = print if whole else (lambda *a, **k: None)
    skip_ = None
    if not whole:
        # (a slot's pieces reach her skin within 3 cm (the boot's ray) or 1.5 cm behind: points of hers
        # well outside the pieces' box are left untucked without their rays, as the rays would leave them)
        pw_ = np.array([(o.matrix_world @ v.co)[:] for o in objs for v in o.data.vertices])
        bw0_ = np.array([(body.matrix_world @ v.co)[:] for v in me.vertices])
        skip_ = ((bw0_ < pw_.min(0) - 0.05) | (bw0_ > pw_.max(0) + 0.05)).any(1)'''.split("\n")
tail = ["    return t, hid", "", ""]
func = head + out + tail
call = ["        vals[:, k] = tuck_of(name, objs)[0]"]
ins = next(i for i in range(i0, i0 - 12, -1) if L[i].startswith("# Her skin under each outfit"))
L2 = L[:ins] + func + L[ins:f0 + 5] + call + L[f1 + 1:]
open(p, "w", encoding="utf-8", newline="").write(NL.join(L2))
print("tuck_of: %d lines of the loop moved; call at the old loop" % len(body))
