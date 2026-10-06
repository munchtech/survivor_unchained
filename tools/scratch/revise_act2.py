import os

p = os.path.join(os.getcwd(), 'docs', 'cinematics', 'act2_outline.md')
s = open(p, encoding='utf-8').read()


def rep(a, b):
    global s
    assert a in s, a[:80]
    s = s.replace(a, b)


# C20: Tam's Pa is in his forties
rep("""Tam's Pa (Penhale, Somerset, swearing): "Forty years I've ploughed that. Forty.
  ...Go on, then, take it.\"""",
    """Tam's Pa (Penhale, Somerset, swearing): "My father ploughed that. And his.
  ...Go on, then, take it.\"""")

# C21: chapter four, older, terser, one sign wrong
rep("""- **Chapter four** (Keegan reads it; this is the handbook's own text):
  "Of the Unchained, and Their Return to the Dark. One. That they do not
  breathe the cold of night as the living do. Two. That they come back, and that
  they come back more often than is reasonable. Three. That the dead are quiet
  round them, and beasts are not. Four. That their past goes out of them, the
  names first. The knight who has seen these signs shall return the Unchained to
  the dark, with mercy, at once, and shall not be persuaded.\"""",
    """- **Chapter four** (Keegan reads it; this is the handbook's own text, two
  hundred years older than she is, and it sounds it): "Of the Unchained, and
  Their Return to the Dark. Their breath showeth not by night. They return. The
  dead make way for them; the hound will not. They lose their mothers' names
  before their faces. They cannot abide running water. The knight that hath seen
  these signs shall return the Unchained to the dark, with mercy, and shall not be
  persuaded."
- **The wrong sign.** The last sign is false, and Keegan knows it: she has
  watched the survivor wade the Thornwater at the Verge's ford, twice, and say
  nothing about it. That is what she means by "badly written". It also tells the
  player the handbook is a book, written by people who guessed.""")
rep("""- **Key lines.** "I have been watching your breath. At night. For three weeks. I
  have kept a table." / (the slip) "I don't— I do not want to be right." / To a lie:
  "You are not breathing, and you are lying to me. One of those is not your fault.\"""",
    """- **Key lines.** "I have been watching your breath. At night. For three weeks. I
  have kept a table." / (the slip) "I don't— I do not want to be right." / To a lie:
  "Your breath does not show, and you are lying to me. One of those is not your
  fault." (Her breath is the only one in the shot: the survivor's exhale is
  audible, as in C01, and leaves nothing in the cold.)""")

# C26: Redcowl does not count
rep("""- **Key lines.** Redcowl to Holloway: "You counted our boots once. Count our
  blades." Rav, in the hat:""",
    """- **Key lines.** Redcowl to Holloway: "You turned the wagons back once,
  Captain. Turn us." (Holloway's count belongs to C22 and C23; Redcowl's grievance
  is the relief that never came up the road.) Rav, in the hat:""")

# C25: Pell's number must not collide with Holloway's eleven men
rep("""- **Key line.** "I'm not a good man. I'm a careful one. ...Carefully, then: you
  have eleven days.\"""",
    """- **Key line.** "I'm not a good man. I'm a careful one. ...Carefully, then: you
  have nine days.\"""")

# C29: Sallow; no breath beat (left to the effects)
rep("""- **Beats.** Silver cages in a cold hall, the risen in them sitting very upright,
  breathing no smoke; Sallow at a desk""",
    """- **Beats.** Silver cages in a cold hall, the risen in them sitting very upright
  (the cold hall's breath effects do the rest; no shot is built on it); Sallow at
  a desk""")
rep("""- **Key lines.** Sallow: "You've come back more often than anyone in the book.
  I'm afraid that makes you an asset.\"""",
    """- **Key lines.** Sallow: "You've come back more often than anyone in the book.
  I'm afraid that puts you on the credit side.\"""")

# C30: pays Lie down; names instead of the window; Chid's lines
rep("""Every Act 1 seed lands here: the prints, the breath, "I
  gave you to the water", "You smell like downstairs", the far bank, the mother's
  face.""",
    """Every Act 1 seed lands here: the prints, the breath, the
  Warden's "Lie down." (the Order's word for the dead, said to her), "You smell like
  downstairs", the far bank, the mother's face.""")
rep("""- **Beats.** The shrine at night, one candle. Chid tells it as a story about
  someone else, then stops pretending. The survivor's hands. A long silence. She
  breathes on the cold window: no mist. Then the cost going forward: the names.""",
    """- **Beats.** The shrine at night, one candle. Chid tells it as a story about
  someone else, then stops pretending. The survivor's hands. A long silence. Then
  Chid asks her mother's name again, as he did in Act 1 (`chid.names`), gently, and
  waits, and this time the camera waits with him on her face for as long as she
  takes. (If he never asked in Act 1, he asks for the first time, and says so.) No
  breath beat here: C21 had it, and C52 will.""")
rep("""- **Key lines.** Chid: "You were cold when they brought you in. Properly cold.
  And then you weren't. ...I said I'd forgotten how it looks. I hadn't. I lied to
  you. I'm sorry; it was a kind lie and they're the worst kind." / "Am I still
  me?" "You're asking. That's most of it.\"""",
    """- **Key lines.** Chid: "You were cold when they brought you in. Properly cold.
  And then you weren't." / *(Only if she heard him say it in Act 1, the once-only
  choice "You look like you've seen this before.")* "I said I'd forgotten how it
  looks. I hadn't. You don't." / "Am I still me?" "The ones in the ditch don't
  ask.\"""")
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('ok')
