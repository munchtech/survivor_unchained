import sys, re
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
def rep(old, new, count=None):
    global s
    assert old in s, old[:80]
    s = s.replace(old, new) if count is None else s.replace(old, new, count)

rep('"Something old has fallen."', '"This one has a name."')
rep("""4. **The word.** A line under the HUD: "This one has a name." (the story lead's words).""",
"""4. **The word.** A line under the HUD: "This one has a name." (the story lead's words; when the
   dark's debt pays it, "The dark settles up.").""")
rep("""on the night's and the map's result, a row of marks and a line in the story's voice. It never
  switches off.""", """on the night's and the map's result, a row of marks under "What the dark owes you" (the story
  lead's words), and "The dark settles up." when it pays. It never switches off.""")
rep("| **Forty-One Mouths** |", "| **Nan's Cleaver** |")
rep('"The Roost\'s cleaver. It fed forty-one mouths on whatever the road brought in, and the road brought in a great deal."',
    '"Firepot Nan\'s, from the Roost\'s kitchen. It has jointed everything the road brought in, and the road brought in a great deal. She will want it back."')
rep('"It has hung by Rook\'s fire for a week and it is still wet."',
    '"Wrung out, it is wet again by morning. Whoever wore it last went into the ford in it, and did not come out."')
rep('"Notched along the spine, in tens, where somebody kept count of something. The book wrote him down as a deserter."',
    '"Notched along the spine in tens, the way a man counts nights on a post nobody relieves. The Watch\'s book has him down as a deserter."')
rep('"Pulled out of the ditch on the Low Ford road, wound and loaded. Whoever loaded it never fired it."',
    '"Pulled out of the ditch on the Low Ford road, wound and loaded, with weed in the stock. Whoever loaded it never got to fire it."')
rep('"Charred to the grip. In the fever year they burned the bedding of the dead, and somebody did it with this."',
    '"Charred to the grip. In the fever year they burned the bedding of the dead, and somebody stirred the fire with this until it was done."')
rep('"A spare wheel off the Dig\'s pump, beaten flat and strapped for an arm. It still weeps."',
    '"A spare wheel off the Dig\'s pump, beaten flat and strapped for an arm. It still weeps green."')
rep('"It came back up the shaft on its own, still lit. Nobody has asked it where Kell is."',
    '"It came back up the shaft on its own, still lit. Kell did not."')
rep('- "Eleven men, a year unpaid, and every one of them still oils his mail."',
    '- "Eleven men on a wall built for sixty, and every one of them still oils his mail."')
rep("Ashford Levy Colours (cloak, on the\n  traveller's cloak)", "Levy Colours (cloak, on the\n  traveller's cloak)")
rep("""Story lead: the lore lines are mine and narrator-voiced; please rewrite any in the valley's
voice, and none says an act's answer early (`STORY_BIBLE.md`).""",
"""The lore is the story lead's (WRITING_PASS §25), verbatim: none says an act's answer early
(`STORY_BIBLE.md`), the Kerchiefs' town stays unsaid, and "Forty-One Mouths" stays C06's.""")
rep("""(The names are the items plan's; "Legion" and "Heartwrought" want the story lead's yes.)""",
"""(The story lead's yes: "Legion" is the valley's word for the old empire's best iron, from about
Act 2; "Heartwrought" never before Act 2's end, which level 32 keeps.)""")
open(p, 'w', encoding='utf-8').write(s)
print("ok")
