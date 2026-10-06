from pathlib import Path
p = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa15f092820132274\tools\anim\clips\run.py")
t = p.read_text(encoding="utf-8")
a = t[t.index("def blade_carry("):t.index("def shield_guard(")]
b = '''def blade_carry(out=-1.0, up_back=0.35, up_fwd=0.75, swing=None):
    """A blade carried in the swinging hand as a running hand carries one:
    the wrist straight in the grip and the forearm rolled so the thumb side
    faces out and up (`out`: -1 her right, +1 her left), so the blade rides
    out and ahead of her, rising as the fist comes through and dipping as
    it goes back, never across her legs. `swing`: the fist's own path (back,
    forward: from the shoulder, in the chest's frame, as for her right hand),
    held steadier than the free arm's: a hand behind her with the wrist
    straight can only point a blade down or across her, so a long blade's
    hand stays at her side. (Keyed by direction, up over her shoulder behind
    her, it asked a wrist bent back past what one can, and the hand flapped
    from one side to the other.)"""
    def f(ph, k, hand):
        hand = dict(hand)
        hand.update({"thumb": (out, up_back + (up_fwd - up_back) * k, 0.0), "frame": "chest", "twist": 0.5})
        if swing is not None:
            e = k * k * (3 - 2 * k)
            back, fwd = np.array(swing[0], float), np.array(swing[1], float)
            v = (back + (fwd - back) * e) * [-out, 1, 1]
            v[1] += 0.03 * math.sin(math.pi * k)
            hand["arc"] = arc_of(v)
        hand["pole"] = tuple(np.array(hand["pole"]))
        return hand
    return f


# The long blades' hands: the sword at her side and ahead; the reaver's axe
# pumped harder, but still never far behind her.
SWORD_SWING = ((0.0, -0.34, 0.0), (0.02, -0.20, 0.27))
AXE_SWING = ((0.02, -0.30, -0.08), (0.0, -0.10, 0.31))


'''
t = t.replace(a, b)
E = [
    ('"run_warden": (WARDEN, {"r": blade_carry(), "l": shield_guard()}, "sword+shield"),',
     '"run_warden": (WARDEN, {"r": blade_carry(swing=SWORD_SWING), "l": shield_guard()}, "sword+shield"),'),
    ('"run_reaver": (REAVER, {"r": blade_carry()}, "axe"),', '"run_reaver": (REAVER, {"r": blade_carry(swing=AXE_SWING)}, "axe"),'),
    ('"run_reaver_axes": (REAVER, {"r": blade_carry(), "l": blade_carry(1.0)}, "axes"),',
     '"run_reaver_axes": (REAVER, {"r": blade_carry(swing=AXE_SWING), "l": blade_carry(1.0, swing=AXE_SWING)}, "axes"),'),
]
for x, y in E:
    assert t.count(x) == 1, x
    t = t.replace(x, y)
p.write_text(t, encoding="utf-8")
print("ok")
