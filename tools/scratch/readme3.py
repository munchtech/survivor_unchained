import os

p = os.path.join(os.getcwd(), 'docs', 'cinematics', 'README.md')
s = open(p, encoding='utf-8').read()


def rep(a, b):
    global s
    assert s.count(a) == 1, (a[:80], s.count(a))
    s = s.replace(a, b)


rep("""The full table is section 7. In short: thirteen Act 1 scripts, ready to build
(C01 to C13);""", """The full table is section 7. In short: fourteen Act 1 scripts, ready to build
(C01 to C14);""")

rep("""They are short. The longest in Act 1 is the fortune, and only because the
player wrote most of it. Nobody explains anything. The survivor never makes
a speech; she barely speaks at all. The camera notices what the narrator does
not say.""", """They are short. The longest in Act 1 is the fortune, and only because the
player wrote most of it. Nobody explains anything. The survivor never makes
a speech; she barely speaks at all. The camera notices what the narrator does
not say.

### The soul test

The owner's question of every scene is "do we have soul?": is this one game in a
million, or one of many? Every script here has been read against it, and every
new one must be. **If a shot, a line or a beat could be lifted into another
dark-fantasy game and work unchanged, it is not finished.**

What makes a scene this game's and no other's:
- **This valley's debt to the dead.** Everyone here keeps the lights on with a
  debt to the dead they cannot pay, and the light is the dead. A scene earns its
  place when it touches that: who is being burned, who is being kept, who is
  counting.
- **This valley's things.** Lamps held up to faces; ember blue in a new black
  iron; oil burning warm; breath that does and does not show; prints in frost;
  a hammer as the town's clock; boots; a toll-token with three roads; a square
  coin; a ledger in violet ink; weed in red hair. If a scene could swap its
  objects for any other game's, its objects are wrong.
- **This valley's words.** "Lie down." "Is it morning?" "Not yet." "Them
  first." "You know the place." "Nobody's!" The Order's call, the hymn, the
  handbook. People speak in their trades and their histories, never in the
  genre's voice.
- **One point of view.** The narrator's: present tense, plain nouns, one image
  at a time, never what it means. The camera holds a beat longer than is safe,
  looks at hands, and stays with the person who has to live with it.
- **Costs paid on screen, by people we know.** Not "the town suffers": Brannoc
  kneels; Rook steps back and back; Harlan's hand stays on Jory's shoulder.

What fails it, and is cut on sight:
- a villain who explains, or laughs at nothing;
- a hooded watcher who sees the deed and leaves (we cut two);
- prophecy, destiny, the chosen one; "it has begun";
- red eyes meaning evil, rain meaning grief, a tear in close-up meaning sad;
- a dying speech that sums up a life;
- a reveal that is only a fact, rather than something the player did, seen
  again;
- a line any character could say;
- an image that is only beautiful.

Ask it of every shot, in every review, alongside `docs/editorial/REALNESS_AND_EXTREMES.md`'s
four questions about the people in it.""")

rep("""- **ford-lamp blue** (`#8ac8ff`, steady, cold): the Wardens, the chain, the
  Morrow's light as the Watch kept it;""",
    """- **ford-lamp blue** (`#8ac8ff`, steady, cold): ember burning in a Warden's
  iron (Brannoc's new irons on the Low Ford road; the Wardens; the chain). The
  Watch's oil, when it had any, burned warm, like any lamp: a warm lamp at the
  ford means nothing is drinking from it;""")

rep("""**Effects.** Where a cinematic changes the world (a fact set, a journal line),
the change is on its conversation's nodes, so it happens whether the
cinematic plays or is skipped.""",
    """**Effects.** Where a cinematic changes the world (a fact set, a journal line),
the change is on its conversation's nodes, so it happens whether the
cinematic plays or is skipped.

**Love scenes are not cinematics.** There are no NPC faces to hold, and
two-person animation is the dearest thing on this list. Each love scene's
cut-away is narrated, as written in `docs/romance/`, and the screen holds one
object, still, for its length: Sella's bolt going home; Maeca's boots side by
side outside the hides; Keegan's armour laid out in order on a chapel bench;
two cups on Rav's table, one full; Ysolde's spectacles folded on the twelfth
drawing. An insert at 85 to 100, the room's own light, no music but the room.""")

rep("""10. **Sets**: a roof on the toll tower to stand on (C09),""",
    """10. **Sets**: the prologue's Low Ford road at night, reused for a story fight,
    its irons lit along it and the ambush's wagon and ditch (C14); a roof on the
    toll tower to stand on (C09),""")

rep("""**Should have**
12. Ember VFX:""",
    """12. **Allies in a fight**: an NPC who fights beside her in an arena, holds a
    place (the edge of a light) and does not chase (Brannoc, C14; Act 2's war at
    the gate needs many).
13. **Story fights on the merciful routes**: C14 is the first, on the truth
    route; the Act 1 story fights are otherwise all on the violent routes.

**Should have**
14. Ember VFX:""")
rep("""13. A Warden of real presence:""", """15. A Warden of real presence:""")
rep("""14. Water: the ford's surface""", """16. Water: the ford's surface""")
rep("""15. Hand IK for holding hands, taking a coin, reading a palm.""",
    """17. Hand IK for holding hands, taking a coin, reading a palm, closing a dead
    man's eyes, lifting a cord over a head.""")

rep("""| C13 | Behind the Sealed Door | The Verge's door; arena | The door; boss arrival and kneel (the Barrow Lord) | 3 | 12.5 s + 8 s + 16 s | `c13_behind_the_door.md` |""",
    """| C13 | Behind the Sealed Door | The Verge's door; arena | The door; boss arrival and kneel (the Barrow Lord) | 3 | 12.5 s + 8 s + 16 s | `c13_behind_the_door.md` |
| C14 | The Road Back | The smithy; the Low Ford road | Choice; the truth route's night (Wat; Brannoc carries Nell home) | 2 | 18 s + choice, 30 s, 10 s, 48 s | `c14_road_back.md` |""")
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('ok')
