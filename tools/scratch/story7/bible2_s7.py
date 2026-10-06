P = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a38d66ae66583ace1\docs\STORY_BIBLE.md"
s = open(P, encoding="utf-8").read()
pairs = [
    ("holds the numbers that say when the chain breaks, and his sister's letter about the boots | Act 1 (why), Act 2 (the numbers, the letter) |",
     "holds the numbers that say when the chain breaks; knows who barred the lid at Ashford, and is waiting for a price | Act 1 (why; that he knows), Act 2 (the numbers) |"),
    ("""so which night the chain goes) and his sister's last letter, about the
  garrison's boots "signed for full".""",
     """so which night the chain goes), and what he found at Ashford: the main
  shaft's lid, barred from the top. He knows who barred it, and is a careful
  man waiting for a price (the decoy, in red ink)."""),
    ("""- `redcowl.who`: "what's left when a town goes into the ground and the Watch
  counts its boots and goes home".""",
     """- `redcowl.who`: "what's left when a town goes into the ground and the Watch
  writes it down and goes home"."""),
    ("""learn who signed for the boots in Act 2, and you may be the one who tells her.""",
     """meet, in Act 2, the woman under the lid, and her hand is the one that pulls you up."""),
]
for a, b in pairs:
    assert a in s, a[:60]
    s = s.replace(a, b)
open(P, "w", encoding="utf-8").write(s)
print("ok")
