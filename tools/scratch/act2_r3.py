import os

p = os.path.join(os.getcwd(), 'docs', 'cinematics', 'act2_outline.md')
s = open(p, encoding='utf-8').read()


def rep(a, b):
    global s
    assert s.count(a) == 1, (a[:80], s.count(a))
    s = s.replace(a, b)


rep("""- **Chapter four** (Keegan reads it; this is the handbook's own text, two
  hundred years older than she is, and it sounds it): "Of the Unchained, and
  Their Return to the Dark. Their breath showeth not by night. They return. The
  dead make way for them; the hound will not. They lose their mothers' names
  before their faces. They cannot abide running water. The knight that hath seen
  these signs shall return the Unchained to the dark, with mercy, and shall not be
  persuaded."
- **The wrong sign.** The last sign is false, and Keegan knows it: the one she
  is reading it to came up out of a river. She reads it anyway, because it is in
  the book, and her voice goes flat on it. That is what she means by "badly
  written". It also tells the player the handbook is a book, written by people
  who guessed.""",
    """- **Chapter four** (Keegan reads it; this is the handbook's own text, older
  than she is, and it sounds it; the romance's private reading, `keegan.ch4_read`,
  uses the same words): "Of the Unchained, and Their Return to the Dark. One. The
  Unchained is the likeness of the one who died, and walks in their shoes, and
  knows their friends. The knight shall not be deceived by this. Two. Its breath
  does not show by night. By day it is ordinary. It comes back from death. Three.
  It cannot abide running water. The knight shall not converse with it beyond
  what is needful." (She skips; her finger goes down the page past four, five and
  six, which she does not read aloud.) "Seven. The return shall be made at dawn,
  when it is weakest, with a blade the knight has kept clean, and the knight
  shall not be persuaded. Eight. The knight shall make the return kindly, for it
  was a person once." (She stops.) "Nine. The knight shall not grieve."
- **The wrong sign.** Three is false, and Keegan knows it: the one she is
  reading it to came up out of a river. She reads it anyway, because it is in
  the book, and her voice goes flat on it. That is what she means by "badly
  written". It also tells the player the handbook is a book, written by people
  who guessed.
- **Have you done this before?** A choice, in the public scene at the gate, with
  the Watch listening. Her answer is the one place she uses no handbook and no
  figure of speech: "Once. She thanked me. They do, the first time. They're
  frightened." (A girl of fourteen, a mill-race, her first month in the north;
  she never says more, and the duel, if it comes, is a tragedy whichever way it
  goes.)""")

rep("""- **Variants.** *Told the truth:* Brannoc has asked the survivor to sit up with
  him in the forge's dark. The buyer comes: hooded, square coin, Toll Tower violet
  at the cuff. Brannoc puts the two irons on the anvil and breaks them with three
  strokes, and says "Tell her no." The buyer goes. *Lied to:* he sells them; the
  survivor sees it from across the road; later (C28) a grey mare comes up the
  south road alone, and Brannoc reads its saddle-bag, and understands, and looks for
  the survivor.
- **Key line** (truth): "Tell her no." (He says "her". He knows.)""",
    """- **Variants.** *Told the truth:* Brannoc has asked the survivor to sit up with
  him in the forge's dark. The buyer comes: hooded, square coin, Toll Tower violet
  at the cuff. Brannoc puts the two irons on the anvil and breaks them with three
  strokes, and says "Tell her no." *(If she walked the road with him in C14:)*
  before the buyer can go, Brannoc takes Wat's toll-token out of his coat and puts
  it on the anvil among the broken iron, for the buyer to take back with the
  answer. The buyer goes. *Lied to:* he sells them; the survivor sees it from
  across the road; later (C28) a grey mare comes up the south road alone, and
  Brannoc reads its saddle-bag, and understands, and looks for the survivor.
- **Then the boots** (truth only; Act 2's major turn, `STORY_BIBLE.md` section
  5). Next morning, not from Brannoc: Rook, wiping a table that is clean, to the
  survivor. "He bought her those boots with the ford money, you know. Paid
  Kettle the cobbler in square coin. Kettle showed me the coin. ...I didn't think,
  pet. Nobody thought." Then the forge, seen from the lane: Brannoc puts the two
  broken irons in the fire. Then he takes Nell's old boots down off the nail by
  the rack, where they have hung since C07 without anyone framing them, and puts
  them in after, and stands and watches both burn, his hands at his sides. He
  says nothing at all. Nobody says "you killed her" or "it was the boots"; the
  player who has seen the nail does the rest.
- **Key line** (truth): "Tell her no." (He says "her". He knows: the coin, and,
  if she walked the road with him, Wat's token.)""")

rep("""- **Key lines.** Sallow: "You've come back more often than anyone in the book.
  I'm afraid that puts you on the credit side." / Edric, to the survivor: "Ask her if she's
  got the corners right yet.\"""",
    """- **Key lines.** Sallow: "You've come back more often than anyone in the book.
  I'm afraid that puts you on the credit side." / Edric, to the survivor: "Ask her
  if she's got the corners right yet." / Edric, later, the floor of Act 3's reveal
  in one line: "They bleed us for the silver lamps. Every night. And every night I
  know someone else's mother." (Sallow, the wrong person's kindness: Edric is
  fed, warm and read to, and has been for twelve years.)""")

rep("""- **Choices.** "Did it hurt?" / "Who did this?" / "Am I still me?" (each a short
  answer; none a lecture).""",
    """- **Choices.** "Did it hurt?" / "Who did this?" / "Am I still me?" (each a short
  answer; none a lecture).
- **Coda: the next dawn.** From here the night's ember can cost a memory
  (`STORY_BIBLE.md` section 7, beat 11). The first dawn after C30 plays C04's
  language again (the ember back into the ground, the breath smoking) with one
  narrated line, the first memory that goes and the stranger's that comes in its
  place: *"You cannot remember the name of the street you grew up on. You can
  remember, very clearly, a grey mare who would not take a bit in winter, and you
  have never owned a horse."* Wat's mare: the player who walked the road in C14,
  or put the carters down in the prologue, can name whose. Nobody else in the
  scene; nobody says it.""")

rep("""- **Variants.** The roll of who is there (Holloway, Keegan, Maeca and the Pack,
  Redcowl's people or Rav's, Brannoc with a hammer, Harlan's money in the
  Kerchiefs' new boots, the freed from Silverstair).
- **Key image.** Everyone's breath smoking in the torchlight on the wall, and
  hers, and Chid's, and the freed Unchained's, not.""",
    """- **The eve.** The night before is one night, and only one, with one of the
  open romances, or alone, or on the wall (`romance.eve`, `docs/romance/`). Not a
  cinematic: the cut-away holds its one object (section "Love scenes" in the
  README). Whoever she did not choose has one line for her in the morning, and
  none of them is cruel.
- **Variants.** The roll of who is there (Holloway, Keegan, Maeca and the Pack,
  Redcowl's people or Rav's, Brannoc with a hammer, Harlan's money in the
  Kerchiefs' new boots, the freed from Silverstair).
- **Key image.** The wall seen from the north road, from Sallow's side: a line of
  people in their working clothes holding what their trades gave them. A smith's
  hammer, a hunter's crossbow and bare feet, Wenna's beaked masks handed along
  the line, a red hat, Watch grey, Kerchief red, a priest with a candle, a knight
  with a book inside her breastplate. Nobody in uniform but the eleven. (The
  breath is left to the effects tonight: C21 had it, and C52 will.)""")
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('ok')
