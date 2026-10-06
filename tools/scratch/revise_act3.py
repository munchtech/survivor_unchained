import os

p = os.path.join(os.getcwd(), 'docs', 'cinematics', 'act3_outline.md')
s = open(p, encoding='utf-8').read()


def rep(a, b):
    global s
    assert a in s, a[:80]
    s = s.replace(a, b)


# C40: the rule that lets Jessop speak
rep("""- **Key lines.** Jessop, to nobody, over and over: "The road is shut. The road is
  shut. Go round by the forest track." (The lie he was paid ten for, on his lips
  forever.)""",
    """- **The rule.** The risen do not speak anywhere else in the game, so the stair
  states its exception before Jessop shows it: the dead the Legion holds keep
  their last errand. The armoured dead lining the stair are still standing the
  watch they died on (it is why they come to attention); a clerk who died on an
  errand is still running it. Vonnra says it if she is there, a step behind the
  survivor ("They keep what they were doing. The Legion was very thorough."), and
  the Barrow Lord's kneel in C13 has already shown it. Without Vonnra, it is the
  picture alone: the soldiers at their posts, then the clerk at his.
- **Key lines.** Jessop, to nobody, over and over: "The road is shut. The road is
  shut. Go round by the forest track." (The lie he was paid ten for, his errand,
  on his lips forever.)""")

# C41: the plain verb, the twenty-fifth, silence
rep("""- **Key lines.** "I drowned twenty-six people to find you. I wrote every one of
  them down. Payment, always." / "You are the only thing I have ever bought that I
  could not afford.\"""",
    """- **Key lines.** "I drowned twenty-six people to find you. I wrote every one of
  them down." (The plain verb, after a whole game of "arranged": that is her
  change.) Then, later, unasked, in the middle of something else: "The smith's
  girl was the twenty-fifth." And silence: no music, nobody moves, and the
  survivor does the arithmetic (she came after the twenty-sixth). The ledger in
  C09 is the page these lines land on.""")

# C42: Is it morning? instead of Keep the lights lit
rep("""  he goes dark with every Unchained. He wants her to choose without him in it.
  Pays `chid.note`, `chid.long`, C03's "Keep the lights lit".""",
    """  he goes dark with every Unchained. He wants her to choose without him in it.
  Pays `chid.note`, `chid.long`, and C03's "Is it morning?": the Warden was the
  Order's keeper of the Low Crossing, a man once, and Chid knew him. He asks the
  survivor whether the Warden said anything at the end. She can tell him (a
  choice: "He asked if it was morning. I nodded."), or say nothing. Either way
  Chid says the man's name, which nobody else in the game knows; only if she tells
  him does he learn what she answered.""")
rep("""- **Key lines.** "I wrote that to Ashe. He kept the north road with forty lamps and
  came back with one, and I wrote him a note, because I couldn't think what else to
  give him. ...Don't choose for me. You'll want to. Don't.\"""",
    """- **Key lines.** "I wrote that to Ashe. He kept the north road with forty lamps and
  came back with one, and I wrote him a note, because I couldn't think what else to
  give him. ...Don't choose for me. You'll want to. Don't." / On the Warden: "He
  always asked that. Every night, at the end of the watch, and we'd say 'Not yet',
  and he'd go back to it. ...Tobin. His name was Tobin." / If she tells him she
  nodded: "(A long time.) You told him yes. ...Good. Somebody should have." (The
  Order's answer to "Is it morning?" was "Not yet": the keeper kept watching. The
  survivor's nod in C03 was the first "yes" he had been given. The Barrow Lord's
  "Nondum" in C13 is the same answer in an older tongue, given to her.)""")

# C43 pays C12's new line
rep("""Pays
  C03 (the theft), C12 ("It knows you").""",
    """Pays
  C03 (the theft, "ever so grateful"), C12 ("It went ever so QUIET!").""")

# C50: the ledger line struck
rep("""  her; the last shot is the Waystation at dawn, every lamp lit, and her name in
  Vonnra's ledger with the link beside it, inked over.""",
    """  her; the last shot is Vonnra at her table on the tower roof at dawn, every lamp
  in the town below still lit, opening the ledger at C09's page and drawing one
  ruled line through the twenty-seventh entry, as through the others. Then she
  closes the book, and does not touch the coin.""")
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('ok')
