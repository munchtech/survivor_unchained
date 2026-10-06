import os

D = os.path.join(os.getcwd(), 'docs', 'cinematics')


class Doc:
    def __init__(self, name):
        self.p = os.path.join(D, name)
        self.s = open(self.p, encoding='utf-8').read()

    def rep(self, a, b):
        assert a in self.s, (self.p, a[:80])
        self.s = self.s.replace(a, b)

    def save(self):
        open(self.p, 'w', encoding='utf-8', newline='\n').write(self.s)


# ---------------------------------------------------------------- C10
c = Doc('c10_hollow_by_night.md')
c.rep("""When he falls, he lies on his side breathing
hard, and looks at her, and then past her at something only he can see, and
stops. Nobody speaks. If she knelt to him once and promised, he does not look
away.""",
      """When he falls, he lies on his side breathing
hard, and looks at her, and then past her, at the mouth of his den, where his
sick are lying; and stops. Nobody speaks. If she knelt to him once and promised,
he does not look away from her.""")
c.rep("""- **Greymuzzle wants** to die on his feet, in his own place, and he does not
  get to. **He reveals** that he remembers her (if she promised).""",
      """- **Greymuzzle wants** to die on his feet, in his own place, and he does not
  get to. What he thinks of last is not her and not himself: it is the den, and
  the ones in it who cannot get up. **He reveals** that he remembers her (if she
  promised): then she is the last thing he looks at, and the player knows what
  that look is asking.""")
c.rep("""- **Pays:** C05 (the kneeling, the promise); Maeca's cave (if her lover).""",
      """- **Pays:** C05 (the kneeling; the sick wolves in the dirt that do not get up;
  the promise).""")
c.rep("""- Reads: `promise.pack` (his look), `maeca.lover` (where he looks last),
  calling (nothing changes), the arena's own ground.""",
      """- Reads: `promise.pack` (his look), calling (nothing changes), the arena's own
  ground.""")
c.rep("""| 4 | CU | 100 | As 2 | His eye leaves her and looks past her, away, at something only he can see. *(Maeca's lover:* toward the south-east, where the Blind would be.*)* *(If she promised:* his eye does not leave her.*)* The breathing stops. The smoke from his muzzle thins and stops. | 4.0 |""",
      """| 4 | CU | 100 | As 2 | His eye leaves her and goes past her, to the den: a black mouth under the roots at the Hollow's edge (the arena's set dressing; behind her, out of focus). It stays there. *(If she promised:* his eye does not leave her.*)* The breathing stops. The smoke from his muzzle thins and stops. | 4.0 |
| 4a | LS | 50 | Static, past his head toward the den | *(Not if she promised.)* The den's mouth in the moonlight. Nothing comes out of it. | 2.0 |""")
c.rep("""The look past her is the most important beat: an old animal
seeing something that isn't there, or is.""",
      """The look past her is the most important beat: not a vision,
not the sky; the den, and the sick in it, and who will see to them now. It is
the same look he gave the den in C05 before he let her in. If she promised, he
does not spend it on the den: he spends it on her, and that is worse.""")
c.rep("""- **Effects.** Paws; the ring's low growl; the howl (old, cracking at the top,
  answered); his breathing, close; the last breath.""",
      """- **Effects.** Paws; the ring's low growl; the howl (old, cracking at the top,
  answered); his breathing, close; the last breath. In 4a, from the den, a thin
  whine, once, that nobody answers.""")
c.rep("""The horde told to back off into a ring (an arena-director hook); a wolf's slow
walk and a howl; a wolf lying on its side breathing (an additive breath on the
ribs); breath-smoke on wolves at night; the death's head-turn.""",
      """The horde told to back off into a ring (an arena-director hook); a wolf's slow
walk and a howl; a wolf lying on its side breathing (an additive breath on the
ribs); breath-smoke on wolves at night; the death's head-turn; a den's mouth (a
set piece placed at the arena's edge behind her when the boss falls).""")
c.rep("arrival 9 s, death 14 s", "arrival 9 s, death 16 s")
c.save()

# ---------------------------------------------------------------- C11
c = Doc('c11_raid_on_the_roost.md')
c.rep("""If she ever said
"Ashford" to his face, it is that word: the name he never let anyone say twice.
If not, it is a message for his brother, about a leg.""",
      """If she ever said
"Ashford" to his face, it is that word, and a laugh: he told her she could say it
once in his camp, and now he has said it too, and they are square. If not, it is
a message for his brother, about a leg.""")
c.rep("""- **Pays:** C06 (the children, the standard); `redcowl.ashford` (she said it
  once);""",
      """- **Pays:** C06 (the children, the standard); `redcowl.ashford` ("You get to say
  that once in my camp. You've said it.");""")
c.rep("""| 3 | CU | 85 | Static | His last line (R2 or R3). | 4.0 |""",
      """| 3 | MS | 50 | Static, at his kneeling eye-height, a little closer than 2 | His last line (R2 or R3), said up at her. (A medium shot: he has no face rig, so the line is carried by the head, the shoulders and the hands on the haft.) | 4.5 |""")
c.rep("""| `cin_raid_on_the_roost.last#0` (`redcowl.ashford_said`) | Death, shot 3 | ...Ashford. | The word he never says, once, to the one who said it to him. Not a cry; a name, quietly, like a man telling you where he's from. |""",
      """| `cin_raid_on_the_roost.last#0` (`redcowl.ashford_said`) | Death, shot 3 | ...Ashford. *(a laugh)* There. Now we've both said it. | The word he never says, once, to the one who said it to him: quietly, like a man telling you where he's from. Then the laugh, which costs him, and the rest as a joke between equals. It pays "You get to say that once in my camp." |""")
c.rep("arrival 10 s, death 16 s", "arrival 10 s, death 17 s")
c.save()

# ---------------------------------------------------------------- C12
c = Doc('c12_dig_boils_over.md')
c.rep("""He does not die. He goes back down,
bleeding and delighted, shouting up the hole after her.""",
      """He does not die. He goes back down,
bleeding and delighted, shouting up the hole after her that he has told
downstairs about her, and it went quiet.""")
c.rep("""- **Grimtunnel wants** her to stop interrupting the work. **He reveals**, gloating,
  that the thing below knows her (paying C03's "You smell like downstairs").
- **Plants:** the heart's light in him (Act 3: he carries it to the bottom);
  "It knows you" (Act 2's turn; Act 3).""",
      """- **Grimtunnel wants** her to stop interrupting the work. **He believes**:
  downstairs is patient, downstairs will be grateful, and he talks to it. **He
  reveals**, as a believer shares good news, that he told it about her and it went
  quiet (paying C03's "You smell like downstairs").
- **Plants:** the heart's light in him (Act 3: he carries it to the bottom); the
  Morrow going quiet at her name (the fortune has it "turning over in its sleep";
  Act 3 answers why it listened).""")
c.rep("""| 2 | CU | 50 | Static, at the crack's lip, down at him | Hanging by his claws, grinning up at her. Line G5. | 4.0 |""",
      """| 2 | MS | 35 | Static, at the crack's lip, down at him | Hanging by his claws, grinning up at her, the blue in his seams and his head-lamp lighting the rock round him. Line G5. (A medium shot: he has no face rig; the line is in the whole body, swinging from the claws.) | 4.0 |""")
c.rep("""| `cin_dig_boils_over.pump#0` (pump broken, blown or moved) | Arrival | Surface-meat! You broke my PUMP. ...Doesn't matter. The heart doesn't mind. The heart is PATIENT. | Outrage, then the oily pleasure of a secret. |
| `cin_dig_boils_over.pump#1` | Arrival | Surface-meat! Killing my lads, are we? ...Doesn't matter. The heart doesn't mind. The heart is PATIENT. | |
| `cin_dig_boils_over.knows` | Retreat | It knows you! Downstairs! It KNOWS you! | Delighted, as if he has a present for her. Shouted up the hole as he falls. |""",
      """| `cin_dig_boils_over.pump#0` (pump broken, blown or moved) | Arrival | Surface-meat! You broke my PUMP. ...Doesn't matter. Downstairs doesn't mind. Downstairs is PATIENT. | Outrage, then calm: a believer remembering his faith. |
| `cin_dig_boils_over.pump#1` | Arrival | Surface-meat! Killing my lads, are we? ...Doesn't matter. Downstairs doesn't mind. Downstairs is PATIENT. | |
| `cin_dig_boils_over.quiet` | Retreat | I told it about you! It went ever so QUIET! | Delighted, as if he has a present for her; homely ("ever so", as in C03). Shouted up the hole as he falls. |""")
c.rep("""**Grimtunnel.** Toad-still, then quick. He is not angry for long about
anything: the heart is with him, and everything is going to be wonderful. The
retreat is not a defeat to him: he is going home.""",
      """**Grimtunnel.** Toad-still, then quick. He is not angry for long about
anything: the heart is with him, downstairs is patient, and everything is going
to be wonderful. The retreat is not a defeat to him: he is going home. "Ever so
QUIET" is said with awe, as a churchgoer tells you the bishop knew his name.""")
c.save()

# ---------------------------------------------------------------- C13
c = Doc('c13_behind_the_door.md')
c.rep("""- **Pays:** the bones at the door ("It was never locked from the outside"); the
  bootprints going in and none coming out, and the toll-token in one (Jessop);
  Vonnra's "you know better than to ask me what is behind it" (`vonnra.arcana`).""",
      """- **Pays:** the bones at the door ("It was never locked from the outside"); the
  bootprints going in and none coming out, and the toll-token in one (Jessop);
  Vonnra's "you know better than to ask me what is behind it" (`vonnra.arcana`);
  the words over the door. By day, in `Verge.cs` (`vaultdoor`), the door is
  inscribed in the old empire's tongue: HIC LEGIO SEPTIMA SEPELIVIT QUOD URERE
  NON POTUIT. A reader (arcana, or the scholar's lens) sees it translated ("Here
  the Seventh Legion buried what it could not burn."); anyone else sees only the
  dead tongue. So the language is on the page before he speaks it, and his two
  words are a reward for the reader and a sound for everyone else.""")
c.rep("""| 2 | CU | 50 | Static, on the sigil | Under her hand the whole sigil wakes, violet, from the notch outward along the seven arms, like an eye opening. *(Faith: the bones at the door whisper, very low: "It was never locked from the outside.")* | 4.0 |""",
      """| 2 | CU | 50 | Static, on the sigil, then a slow tilt up | Under her hand the whole sigil wakes, violet, from the notch outward along the seven arms, like an eye opening; its light climbs the stone and finds the cut letters over the door, HIC LEGIO SEPTIMA..., one by one. *(Faith: the bones at the door whisper, very low: "It was never locked from the outside.")* | 4.5 |""")
c.save()
print('ok')
