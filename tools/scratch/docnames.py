p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ac4ec5bbd2763a0df\docs\SKILLS_DESIGN.md"
s = open(p, encoding="utf-8").read()
pairs = [
("**The Blight-Mother**", "**Greenbelly**"), ("| The Blight-Mother |", "| Greenbelly |"),
("**The Caller**: a howl", "**Old Blue**: a howl"), ("| The Caller |", "| Old Blue |"),
("Old Howlers join", "Howlers join"), ("| Old Howler |", "| Howler |"),
("**Old Quarrel**", "**The Scorpion**"), ("| Old Quarrel |", "| The Scorpion |"),
("**The Drowned Reeve**", "**The Weed-Wife**"), ("| The Drowned Reeve |", "| The Weed-Wife |"),
("**The Ford Bell**: a bell that hastes and wards the dead, raises them; bell-ringers and grave-callers join",
 "**The Signifer**: a standard that hastes and wards the dead, raises them; horn-blowers and grave-callers join"),
("| The Ford Bell | a risen ringer under a great bell yoke · 1.5 · brass glow · a bell on a yoke · rings; the dead around it quicken |",
 "| The Signifer | the Legion's standard-bearer, VII on a rag that was red once · 1.5 · bronze, faded red, a glow · a standard · plants it; the dead round it quicken |"),
("| Bell-Ringer | a risen in a Watch tabard with a hand-bell · 1.0 · brass and grey · a hand-bell · stands off and rings (needs a ring clip) |",
 "| Horn-Blower | a risen legionary with a curved horn · 1.0 · bronze and grey · a cornu · stands off and blows (needs a horn clip) |"),
("**The Bombardier**", "**The Chucker**"), ("| The Bombardier |", "| The Chucker |"),
("**The Fuse-Boss**", "**The Perfect of Fuses**"), ("| The Fuse-Boss |", "| The Perfect of Fuses |"),
("The Ganger", "Gutterwick"), ("the Ganger", "Gutterwick"),
]
for a, b in pairs:
    if a not in s:
        print("missing:", a[:60])
    s = s.replace(a, b)
open(p, "w", encoding="utf-8", newline="").write(s)
print("ok")
