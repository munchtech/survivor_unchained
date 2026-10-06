from pathlib import Path
p = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa15f092820132274\tools\anim\clips\run.py")
t = p.read_text(encoding="utf-8")
a = t[t.index("def blade_carry("):t.index("def shield_guard(")]
b = '''def blade_carry(out=-1.0, up_back=0.35, up_fwd=0.75):
    """A blade carried in the swinging hand as a running hand carries one:
    the wrist straight in the grip and the forearm rolled so the thumb side
    faces out and up (`out`: -1 her right, +1 her left), so the blade rides
    up and forward ahead of the fist as it comes through and trails out and
    back behind her as it goes back, never across her legs. (Keyed by
    direction, up over her shoulder behind her, it asked a wrist bent back
    past what one can, and the hand flapped from one side to the other.)"""
    def f(ph, k, hand):
        hand = dict(hand)
        hand.update({"thumb": (out, up_back + (up_fwd - up_back) * k, 0.0), "frame": "chest", "twist": 0.5})
        hand["pole"] = tuple(np.array(hand["pole"]))
        return hand
    return f


'''
t = t.replace(a, b)
E = [
    ('"run_warden": (WARDEN, {"r": blade_carry(105, 45, -0.3), "l": shield_guard()}, "sword+shield"),',
     '"run_warden": (WARDEN, {"r": blade_carry(), "l": shield_guard()}, "sword+shield"),'),
    ('"run_reaver": (REAVER, {"r": blade_carry(110, 55, -0.3)}, "axe"),', '"run_reaver": (REAVER, {"r": blade_carry()}, "axe"),'),
    ('"run_reaver_axes": (REAVER, {"r": blade_carry(110, 55, -0.3), "l": blade_carry(110, 55, 0.3)}, "axes"),',
     '"run_reaver_axes": (REAVER, {"r": blade_carry(), "l": blade_carry(1.0)}, "axes"),'),
    ('"run_arcanist_wand": (ARCANIST, {"r": blade_carry(100, 20, -0.2)}, "wand"),', '"run_arcanist_wand": (ARCANIST, {"r": blade_carry()}, "wand"),'),
    ('"run_stalker_daggers": (STALKER, {"r": blade_carry(115, 25, -0.25), "l": blade_carry(115, 25, 0.25)}, "daggers"),',
     '"run_stalker_daggers": (STALKER, {"r": blade_carry(), "l": blade_carry(1.0)}, "daggers"),'),
]
for x, y in E:
    assert t.count(x) == 1, x
    t = t.replace(x, y)
p.write_text(t, encoding="utf-8")
print("ok")
