p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7dd95d00c4a6a017\tools\anim\audit.py"
s = open(p, encoding="utf-8").read()
old = '''            step = angle(g[f, h], g[f - 1, h]) if f else 0.0
            step_fa = angle(g[f, fa], g[f - 1, fa]) if f else 0.0
            rows.append((f, step, step_fa, fa_tw, h_sw, h_tw))'''
new = '''            # A frame's turn of the hand and of the forearm, and the part of
            # it that spins each about its own length (a flip shows as a spin:
            # the bone's direction barely changes, it rolls over).
            step = angle(g[f, h], g[f - 1, h]) if f else 0.0
            step_fa = angle(g[f, fa], g[f - 1, fa]) if f else 0.0
            roll_h = roll_fa = 0.0
            if f:
                ax = qrot(g[f, h], h_axis)
                roll_h = abs(swing_twist(qmul(g[f, h], qinv(g[f - 1, h])), ax / np.linalg.norm(ax))[1])
                ax = qrot(g[f, fa], fa_axis)
                roll_fa = abs(swing_twist(qmul(g[f, fa], qinv(g[f - 1, fa])), ax / np.linalg.norm(ax))[1])
            rows.append((f, step, step_fa, fa_tw, h_sw, h_tw, roll_h, roll_fa))'''
assert old in s
s = s.replace(old, new)
old = '''        loop = d.get("loop")
        if loop and n > 2:
            rows[0] = (0, angle(g[0, h], g[n - 1, h]), angle(g[0, fa], g[n - 1, fa])) + rows[0][3:]
        flags = []
        for f, step, step_fa, fa_tw, h_sw, h_tw in rows:
            why = []
            if step > FLIP:
                why.append(f"hand turns {step:.0f} in a frame")
            if step_fa > FLIP:
                why.append(f"forearm turns {step_fa:.0f} in a frame")'''
new = '''        flags = []
        for f, step, step_fa, fa_tw, h_sw, h_tw, roll_h, roll_fa in rows:
            why = []
            if roll_h > FLIP:
                why.append(f"hand spins {roll_h:.0f} in a frame")
            if roll_fa > FLIP:
                why.append(f"forearm spins {roll_fa:.0f} in a frame")
            if step > 120:
                why.append(f"hand turns {step:.0f} in a frame")'''
assert old in s
s = s.replace(old, new)
s = s.replace('''        out[s] = {"max_step": max(r[1] for r in rows), "max_step_fa": max(r[2] for r in rows),''',
              '''        out[s] = {"max_step": max(r[6] for r in rows), "max_step_fa": max(r[7] for r in rows),''')
s = s.replace('''parts.append(f"{s}: step {o['max_step']:.0f}/{o['max_step_fa']:.0f} wtw''', '''parts.append(f"{s}: spin {o['max_step']:.0f}/{o['max_step_fa']:.0f} wtw''')
s = s.replace('''FLIP = 35.0''', '''FLIP = 30.0''')
s = s.replace('''Flags (degrees): a hand turning more than FLIP in one frame (30 fps); a''', '''Flags (degrees): a hand or forearm spinning about its own length more than
FLIP in one frame (30 fps), or any hand turning more than 120; a''')
open(p, "w", encoding="utf-8").write(s)
print("ok")
