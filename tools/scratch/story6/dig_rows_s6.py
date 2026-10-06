"""Update WRITING_PASS section 23 with combat's Dig slots and the drive banner (CRLF kept)."""
p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7ba8903f4c8261b1\docs\WRITING_PASS.md"
t = open(p, "rb").read().decode("utf-8")
reps = [
    ('| A windlass broken (sight) | "The windlass goes over, and the shaft falls in on itself." |\r\n',
     '| A windlass broken (sight) | "The windlass goes over, and the shaft falls in on itself." |\r\n'
     '| The first windlass she stands at (`Say`, info) | "Stand at the windlass" / "Close enough to touch, and your weapons break it" |\r\n'),
    ('| The first tub (Snib) | "Mind the tubs! Tubs are EXPENSIVE. Tubs are Boss\'s." |\r\n',
     '| The first tub (Snib) | "Mind the tubs! Tubs are EXPENSIVE. Tubs are Boss\'s." |\r\n'
     '| The Chucker on the roof, out of reach (bar) | "The Chucker" / "Out of reach on the roof until the tubs stop" |\r\n'
     '| The tubs stop, and he comes down (sight) | "The rails go quiet. Down off the brake-house roof comes the Chucker, a pot in each hand." |\r\n'),
    ('| The first drive (`Say`, danger) | "The drive" / "The gap is where she runs: go through the wolves" |',
     '| The first drive (`Say`, danger) | "The drive" / "Out of her line, into the wolves" (one idea for its 1.7 s: the experience director\'s) |'),
    ('the Dig: "Behind you, the tub-way falls in."',
     'the Dig (the neck from the pump-house onto the lip): "Behind you, the ground you came along from the pump-house slumps into the pit."'),
]
for a, b in reps:
    assert t.count(a) == 1, a[:60]
    t = t.replace(a, b)
open(p, "wb").write(t.encode("utf-8"))
print("updated")
