import os

p = os.path.join(os.getcwd(), 'docs', 'cinematics', 'act3_outline.md')
s = open(p, encoding='utf-8').read()


def rep(a, b):
    global s
    assert s.count(a) == 1, (a[:80], s.count(a))
    s = s.replace(a, b)


rep("""  survivor does the arithmetic (she came after the twenty-sixth). The ledger in
  C09 is the page these lines land on.""",
    """  survivor does the arithmetic (she came after the twenty-sixth). The ledger in
  C09 is the page these lines land on.
- **Underneath** (never said; played): pride. She is the last of the line that
  kept the Legion's keys, and she cannot bear to be the one in whose time the
  chain broke. Her truth is a chained beast, a failing chain and a necessary
  cruelty, and she believes every word; by now the player holds more than she
  does (Act 2's memory swaps; Edric).
- **Why not Chid**, if the survivor asks (an Unchained across the square for two
  hundred years): "A link must hold the dead, {name}. You fill with them every
  night you burn. He has never burned." Said as a clerk explains a fee.""")

rep("""  "Nondum" in C13 is the same answer in an older tongue, given to her.)""",
    """  "Nondum" in C13 is the same answer in an older tongue, given to her.)
- **The one line.** If the survivor asks who else knew what the lamps were for,
  Chid tells her the worst thing about the gentlest man in the valley, plainly,
  as the one exception to his never being cynical: "I go when the lamps are lit.
  I couldn't have stopped it. I didn't try. I wanted to see one get up." He does
  not say he was there the night she rose. He doesn't need to. (He was in the
  reeds; she walked up out of the water on her own; he watched her go to her
  fire, and didn't follow. C01's prints are hers alone.)""")

rep("""## C43 · The Bottom

- **Trigger.** The bottom of the stair: the Morrow's chamber.
- **Does.** Grimtunnel, holding the Warden's heart up to something vast that is
  praying. A believer at the end of his faith. The heart must be taken back. Pays
  C03 (the theft, "ever so grateful"), C12 ("It went ever so QUIET!").
- **Variants.** Brannoc's cage for the heart (if he knows about Nell and stood with
  the survivor): the heart carried safely. Without it: it burns whoever carries it,
  and an Unchained pays in names (a menu of the survivor's memories, one chosen and
  lost on screen).
- **Key line.** Grimtunnel, at last not gleeful: "It isn't grateful. ...Why isn't
  it grateful?\"""",
    """## C43 · The Names (the bottom of the stair)

The reveal: **ember is the dead** (`STORY_BIBLE.md` section 1). This is Act 3's
major turn, and the game's. It is made of what the player did, not a new fact:
every ember picked up since the first minute, Nell's among them. (C45, "What It
Prays For", is folded into this scene.)

- **Trigger.** The bottom of the stair: the Morrow's chamber. Grimtunnel is there
  ahead of her, holding the Warden's heart up to something vast that is praying.
- **Does.** Pays C03 ("Nobody's!", "ever so grateful"), C12 ("It went ever so
  QUIET!"), the sinkhole's "Not breathing. Praying.", C04's mother's face, C08's
  hymn, C09's ledger, C14's ember into her hands, Act 2's memory swaps. Moves
  everyone who is there.
- **Beats** (the narrator's rules hold: present tense, plain nouns, one image a
  line, never what it means; the player gets the meaning by recognising names):
  1. The praying does not stop when she comes down the last stair. It gets closer,
     the way the sea does.
  2. It is not one voice. It is a great many, very low, all at once, and they are
     not praying. They are saying names. Most she does not know. Some she does:
     *Aldo*, in a woman's voice, from a long way off. *Ewan*, in a boy's.
     Someone saying *Corran*. Someone saying *Dannet*, over and over.
  3. Very near, a girl says *Da*. She says it the way you say a word you have not
     said for a while, to see if it still works.
  4. Grimtunnel, holding up the heart, not turning round, overjoyed: "You hear
     Him? You HEAR Him? All of them, He's got, every one that ever went down.
     Nobody's! Nobody's lost! He keeps them ALL."
  5. Then, out of all of it, a voice she knows better than her own, saying her
     name, the way it did when she was small and late in from the yard. Her
     mother, who died the week before the ford. And for once her face is exactly
     where she left it. Choices: "Mam?" / (Say nothing. Listen.) / "Let them go."
  6. Vonnra, behind her, who hears none of it (only the Morrow's own light can):
     "What is it saying, {name}? ...It has never said anything to me. Two
     thousand years, and it has never once said anything to my family." If the
     survivor tells her ("It's saying names. Your grandmother's is one of them." /
     "It's praying, the way you said." / nothing), the binder learns in one line
     what her family kept. She breaks both halves of her rule, once: "...No. (A
     long time.) I wanted the lamps to stay lit. That is all I ever wanted. I
     wanted it to be morning." (Pays C03's "Is it morning?")
  7. *If Brannoc made the heart's cage* (he knows about Nell and stood with the
     survivor), he is on the stair, and he has heard his daughter. He says
     nothing about it. He looks at the survivor's hands for a long time, the way
     he looks at iron to see what is in it, as he did on the road in C14. Then he
     picks up the cage. Nobody says "you burned her". The player says it.
  8. The heart must be taken back. In Brannoc's cage it can be carried. Without
     it, it burns whoever carries it, and an Unchained pays in names: the
     journal's and the people page's names blur one by one, from the least known
     to the most, and do not come back; her mother's goes last.
  9. Grimtunnel, at the end of his faith, the heart taken from him and the voices
     not slowing for it: "It isn't grateful. ...Why isn't it grateful?" (Because
     the kept do not want keeping. Nobody tells him.)
- **Shots, in outline.** Long lenses and darkness; the Morrow never seen whole
  (pale, segmented, out of focus behind everything, its light the only light);
  the camera on faces and hands. The names are sound, not subtitles, except for
  "Da" and her own name, which are subtitled, unattributed. Music: none at all
  until her mother's voice; then one held note.
- **Variants.** Who is on the stair (Vonnra, Chid, Brannoc, Keegan, a lover); the
  heart's cage or the names; what she says to her mother.
- **Key lines.** Grimtunnel: "He keeps them ALL." / "It isn't grateful. ...Why
  isn't it grateful?" Vonnra: "I wanted it to be morning.\"""")

rep("""- **Key line.** Vonnra, putting the coin in the survivor's palm and closing her
  fingers on it, the only time she touches the survivor's hand except to read it:
  "The toll is the toll.\"""",
    """- **Key line.** Vonnra, putting the coin in the survivor's palm and closing her
  fingers on it, the only time she touches the survivor's hand except to read it:
  "The toll is the toll." (After C43 the coin means more: the dead keep a toll
  because the dead keep accounts, and this one was her grandmother's own way
  home, never spent. Giving it away is giving her grandmother away. She does not
  say so. Her hand stays closed on the survivor's a moment too long.)""")

rep("""## C45 · What It Prays For

- **Trigger.** Before the choice.
- **Does.** The Morrow: vast, pale, segmented, chained for two thousand years. It
  is praying to be let die. The survivor, being of its light, can hear it.
  Pays the sinkhole's "Not breathing. Praying."
- **Beat.** No words from it. The survivor's face as she understands what the
  ember was: its pain, burned in lamps.

""", "")

rep("""Each ending is a cinematic of its own, then a page per person and place (the
epilogue). The variants are who is alive, who came down, and who holds the coin.""",
    """Each ending is a cinematic of its own, then a page per person and place (the
epilogue). The variants are who is alive, who came down, and who holds the coin.
After C43 each means more than it says: A keeps burning the valley's dead for
light, knowing it; B lets them go, two thousand years of them; C takes them all
into one person.

**The ending decides the nights.** After A the ember scars still open, and the
player knows what they are. After B there is no more ember, and the scars never
open again: the last thing the mercy ending costs is the power the player used
all game. After C the scars open, and the survivor is the boss in every one, and
the hordes are the valley's own dead coming for their light. (A hook in the
arenas, not a cinematic; the endings' last shots say it.)""")

rep("""- *Chid* (he offers; his trust high, and she told him the truth about herself): he
  lies down smiling; "Keep the lights lit."; the survivor goes dark at dawn unless
  she holds the coin (then she climbs the stair, alive and cold, breathing smoke).""",
    """- *Chid* (he offers; his trust high, and she told him the truth about herself): he
  lies down smiling; "Keep the lights lit." (his note to Ashe, said at last to
  someone, and he knows exactly what it costs: he has known for two hundred years
  what the lights burn); the survivor goes dark at dawn unless she holds the coin
  (then she climbs the stair, alive and cold, breathing smoke).""")

rep("""properly, the survivor too, except the coin's holder. The coin: kept (she lives,
mortal), or given to Chid (he ages, at last, between one breath and the next), to
Edric, or to the second Unchained. The last shot: the valley at dawn with no lamps
lit and nobody needing them, and Rook lighting a candle in the Last Lamp's window
anyway.""",
    """properly, the survivor too, except the coin's holder. The dead are let go: the
voices of C43 go quiet one by one, not all at once, the way the dogs did in C09,
and her mother's last; and if the survivor is dying, she has her mother's face
back for exactly as long as it takes. The coin: kept (she lives, mortal), or given
to Chid (he ages, at last, between one breath and the next), to Edric, or to the
second Unchained. The last shot: the valley at dawn with no lamps lit and nobody
needing them, and Rook lighting a candle in the Last Lamp's window anyway. The
candle is tallow.""")

rep("""Keegan kneels or dies trying; Grimtunnel worships; Snib survives. The last shot is
the Waystation's people at dawn, every one of them breathing smoke in the cold,
looking up at her.""",
    """A god made of the valley's dead, with two thousand years of names in her and her
own somewhere among them. Keegan kneels or dies trying; Grimtunnel worships, and
is right; Snib survives. The last shot is the Waystation's people at dawn, every
one of them breathing smoke in the cold, looking up at her. (The breath's second
and last scripted payoff, after C21.)""")

rep("""Act 1, each over a held shot of the place at dawn: the Penhale farm (or the hole
where it was), the Roost, the Last Lamp, the north gate, the Low Ford, the Quiet
Garden (Ashe's stone, Nell's iron marker, Rook's lamp).""",
    """Act 1, each over a held shot of the place at dawn: the Penhale farm (or the hole
where it was), the Roost, the north gate, the Low Ford, the Quiet Garden (Ashe's
stone, Nell's iron marker, Rook's lamp). It ends on the Last Lamp, one image for
three endings: in A, Rook lights it, and the survivor (if alive) hears a name in
it; in B, a tallow candle; in C, it lights itself.""")
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('ok')
