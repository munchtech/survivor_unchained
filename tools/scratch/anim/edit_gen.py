from pathlib import Path
p = Path(r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa4f5fc266b043035\tools\anim\clips\generated.py')
s = p.read_text()
old = '''    speed = 0.0
    if loop:
        d, a, b = best_loop(local, pos, rig.sk, int(0.6 * len(local)), len(local) - 1)
        local, pos = make_loop(local, pos, a, b)
    if place == "line":
        pos, speed, _ = in_place(rig.sk, pos)
    elif place == "pin":
        pos = pin(rig.sk, pos)'''
new = '''    speed = 0.0
    if loop == "cycle":
        # The take is one whole cycle (Mixamo's walks): closed by its own
        # first frame, carried on by a frame's travel.
        pel = rig.sk.i("pelvis")
        step = (pos[-1, pel] - pos[0, pel]) / (len(pos) - 1)
        first = pos[:1].copy()
        first[0, pel] = pos[0, pel] + step * len(pos)
        local = np.concatenate([local, local[:1]])
        pos = np.concatenate([pos, first])
    # Travel out before looping (a loop's seam is spread over the clip, and
    # would take the travel with it).
    if place == "line":
        pos, speed, _ = in_place(rig.sk, pos)
    elif place == "pin":
        pos = pin(rig.sk, pos)
    if loop is True:
        d, a, b = best_loop(local, pos, rig.sk, int(0.6 * len(local)), len(local) - 1)
        local, pos = make_loop(local, pos, a, b)'''
assert old in s
s = s.replace(old, new)
p.write_text(s)
print('ok')
