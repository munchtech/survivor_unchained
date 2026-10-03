# C05 · The Kneeling

**Greymuzzle, by day, at the Hollow.** Priority 2 · Act 1 · about 55 to 75 s
with two choices · skippable (the choices still come)

## What it does

The old wolf comes out of the rocks alone. The survivor puts down what she
fights with, the way Maeca told her to, and kneels with an empty hand held out.
He comes close enough to smell the hand, then her face, and his lip lifts off
his teeth, because she smells of something wrong; and then it goes down again,
and he takes her into the Hollow to see his sick. Then she promises, or asks
him to run with her, or leaves them be.

- **Greymuzzle wants** his Pack to live, and he is old and they are dying.
  **He hides** the sick ones until he has decided about her. **He reveals**,
  only to the camera, that he can smell what she is: the first creature in the
  game who knows, and he lets her in anyway.
- **She wants** the killing to stop. **She changes** by binding herself: a
  promise the Pack will keep count of (`promise.pack`), or an alliance with a
  price (Maeca's regard, the Watch's), or a walk away.
- **Plants:** the wolf's lip at her face (Act 2: the Pack, and every animal,
  know the Unchained; Keegan's signs); the promise (broken if she kills a wolf
  after it, `promise.broken`, quoted back by Vonnra's fortune).
- **Pays:** Maeca's advice to each calling (`maeca.say_calling`: "Don't raise it
  in the Hollow", "Leave the big blade", "Fire's the one thing they all
  remember", "Quiet feet") and to everyone (`maeca.speak`: "no wolf blood on
  you, none since you last slept... don't run"); and, for her lover, Maeca's
  story of the cave (`maeca.blind_morning`): the old wolf lay across a cave mouth
  to keep her alive. He smells Maeca on the survivor, and his tail moves once.

## Trigger and facts

- Plays when she interacts with Greymuzzle at the Hollow (`Verge` interactable
  `greymuzzle`, which opens `G.Talk("greymuzzle")`) for the first time (entry
  `greymuzzle.first`). It stages that conversation; its choices are the
  conversation's.
- Reads: calling; `knows beastlore`, `knows hint.greymuzzle`, `hasTag wolf_fang`
  (the kneel's lock); `knows hint.roost` or `caravan/roost_found` (the
  alliance's lock); `maeca.lover`; `met maeca` (shot 13).
- Sets: as the conversation does (`greymuzzle`, `hollow.peace`,
  `promise.pack`, `pack.allied`, the trait, the journal lines).

## Place, time, light

- **Thornhollow Verge, Wolf Hollow**, (-64, -86): a den under a shelf of grey
  rock, beds of flattened grass, old bones, a few birches. The Hunters' Blind is
  on the ridge 47 m south-east at (-26, -40), its smoke visible.
- **Time:** day (he comes out by day only to someone the Hollow is calm for).
  Late afternoon is best: low, warm sun from the west raking across the Hollow,
  the den's mouth in shadow.
- **Light:** warm sun on the open ground, the den's mouth cold and dark, the
  sick wolves lying half in the shadow. Dust in the air.
- **Mood:** a held breath. Respect. Then grief, quietly.

## Cast and marks

- **The survivor** enters the Hollow from the south-east and stops at (-60,
  -78), facing north-west (heading about 2.6).
- **Greymuzzle** (`wolf_alpha`, scale 1.5, grey to the eyes, thin; ribs
  showing; a torn ear): comes out of the den's shadow at (-64, -88) and stops at
  (-62.5, -82), facing her.
- **The Pack:** five healthy wolves on the rocks above the den, standing, still;
  three sick wolves (`wolf_blighted`) lying in the dirt at the den's mouth,
  (-66, -89), (-64.5, -90), (-62, -89.5). One of the sick tries to stand in
  shot 10.

## Shot list

| # | Shot | Lens | Camera | Framing and action | Dur. |
|---|---|---|---|---|---|
| 1 | LS | 35 | Static, low, behind her right shoulder | The Hollow opening out: the rock shelf, the dark den, wolves on the rocks above, watching. Nothing moves but dust. | 3.5 |
| 2 | MS | 85 | Static, low, from the den's side | Greymuzzle comes out of the shadow alone, slowly, and stops. Line `greymuzzle.first` begins. | 4.0 |
| 3 | CU | 100 | Static | His face: grey to the eyes, the eyes yellow and clouding at the rims; he does not growl. He looks at her for a long time. | 3.5 |
| 4 | MLS | 35 | Static, side-on, both of them in frame at the two edges | She holds still. Behind him, in the shadow of the stones, wolves lying in the dirt that do not get up. The line ends. **Choice 1** comes up in the lower bar; the shot holds, breathing (the wolves' flanks, the dust), for as long as the player takes. | 4.0 + choice |
| 5 | MS | 50 | Static, frontal on her | *Kneel:* she disarms (see Calling) and kneels on one knee, then lowers the other, side-on to him, eyes down, and holds out an empty hand, palm up, low. | 5.0 |
| 6 | 2S | 65 | Static, profile, ground level | He comes to her. Stops a nose from her hand. Smells it. | 3.5 |
| 7 | CU | 85 | Static, over his shoulder onto her face | He lifts his head to her face, close, and breathes her in. His lip lifts off his teeth: not a snarl, a flinch. She does not move. | 3.5 |
| 8 | ECU | 100 | Static | His muzzle at her jaw; the lip goes down again. His ears, which were flat, come up. (Maeca's lover: he moves to her collar and stays there longer than anywhere else, and his tail, out of focus behind, moves once.) | 3.0 |
| 9 | LS | 35 | Static, from the rocks above, looking down | He turns and walks into the Hollow; she rises and follows him into the shadow. Line `greymuzzle.show` begins. | 4.5 |
| 10 | MS | 50 | Slow track along the sick wolves at their height | The sick ones: milky eyes, black gums. One of them sees her and tries to stand, and cannot, and lies down again. | 5.0 |
| 11 | MCU | 85 | Static, past her onto him | Greymuzzle looks east, toward the stream, then back at her, and waits. The line ends. **Choice 2** in the lower bar; hold. | 3.5 + choice |
| 12 | (by choice) | | | See Endings. | 4 to 8 |
| 13 | ELS | 135 | Static, from the Hollow up to the ridge south-east | *If she has met Maeca and the Pack is not her enemy:* on the ridge, by the Blind's smoke, a barefoot figure standing among the birches, watching the Hollow. When the camera finds her she turns and goes. | 3.0 |
| 14 | to play | | Blend into the follow camera | Bars out. | 1.5 |

Total, kneeling and promising: about 58 s plus the two choices.

## Endings (shot 12, by the second choice)

- **"I will stop whatever is poisoning you."** (`promise.pack`, `wolf_friend`.)
  MS, 50: she puts her hand flat on the bare earth between them, fingers
  spread, and leaves it there. He looks at the hand. Then he lies down where he
  stands, among his sick, which is the answer. 5 s.
- **"The men in the ravine are no friends of yours. Run with me."**
  (`greymuzzle.ally`, line read.) LS, 24, low: he lifts his head and howls, once;
  it goes up the rock and out over the Verge. Four of the strongest come down off
  the rocks and stand beside her. The old wolf lies back down among the sick. He
  is not coming. They are his answer. Then a CU on one of the four, close to her
  hip, looking where she looks. 8 s.
- **"Leave them in peace."** MS, 35: she rises and backs out of the Hollow,
  facing him, the way Maeca said, until the rocks hide him. He watches her all the
  way. 4 s.

**And at choice 1:**
- **Draw your weapon.** CU on him: the lip comes up and stays up; behind him every
  wolf in the Hollow gets to its feet at once; he backs into the dark without
  turning his eyes from her. Cut to play with the Hollow hostile
  (`hollow.hostile`). 3 s.
- **Back away slowly.** As "Leave them in peace", from shot 4. 4 s.
- **Kneel, locked** (she does not know how): the choice shows greyed with its
  reason; the shot holds; only the other two can be taken.

## Performance

**Greymuzzle.** Old, slow, absolutely sure of his ground. He does not show his
teeth to threaten; in shot 7 his lip lifts because what he smells on her
offends him, the way a dog's does at a corpse, and he is too proud to back away
from it. Shot 8 is a decision you can watch an animal make: ears come up,
weight comes forward. He never wags; the one tail-movement (Maeca's variant) is
as much as he has.

**The survivor.**
- *Shot 4.* Still. `brows_up` 0.1. Gaze on his eyes, then down and to the side
  (0.4, 0.4): she knows not to stare (a hunter knows; anyone told by Maeca
  remembers).
- *Shot 5.* Gaze down at the ground before him (0, 0.7). Breathing slow.
- *Shot 7.* She feels his breath on her face. `blink` once, slow; nothing else
  moves. Her hand stays where it is.
- *Shot 10.* `brows_sad` 0.5 when the sick one tries to stand. Her gaze goes to
  it and stays.
- *Shot 12, promise:* `mouth_open` 0.05, `brows_sad` 0.3, gaze on Greymuzzle's
  eyes, held.

## Calling (shot 5: disarming as Maeca said)

- **Warden** ("Don't raise it in the Hollow. To a wolf a raised arm's a raised
  arm."): she lowers her shield, slowly, and lays it flat on the ground, face up;
  then the blade or disc on top of it. Only then does she kneel.
- **Reaver** ("Leave the big blade at the Blind... They can smell iron that's
  been used."): she drives the cleaver into the earth behind her and walks
  three paces away from it before she kneels. He looks past her at it once.
- **Arcanist** ("Whatever it is you burn with, don't burn it in the Hollow.
  Fire's the one thing they all remember."): she closes her hands on whatever
  light is in them until it goes out; a thread of smoke rises from between her
  fingers as she kneels, and his nose follows it.
- **Stalker** ("Quiet feet."): she lays the bow (or the knives) down without a
  sound, and comes the last two paces on the sides of her feet, so quietly that
  the wolves on the rocks shift.

## Lines

All existing, all the narrator's, conversation `greymuzzle`:

| VO id | Shot | Line |
|---|---|---|
| `greymuzzle.first` | 2 to 4 | *The old wolf comes out of the rocks alone. He is grey to the eyes, and thin, and he does not growl. He looks at you for a long time. Behind him, in the shadow of the stones, wolves lie in the dirt and do not get up.* |
| `greymuzzle.show` #0 (Maeca's lover) or #1 | 7 to 11 | *He comes close enough to smell your hand, then your face, and his lip lifts off his teeth, and goes down again. Then your collar, for longer; and his tail moves, once. He turns and walks into the Hollow, and you follow...* (see `dialogue.json` for the whole of both) |
| `greymuzzle.ally` | 12 | *Greymuzzle lifts his head and howls, once...* |

The narrator speaks `greymuzzle.first` over shots 2 to 4 at a slow pace, with a
pause before "Behind him". `greymuzzle.show` is split across shots 7 to 11:
its first sentence on the smelling (7 to 8), the rest on the walk and the sick
(9 to 11). Choices are read, not voiced.

## Sound

- **Music.** `Silence` mood throughout; the scene is scored by the wind in the
  birches and the Pack's breathing. On the promise (or the alliance), a single
  low flute note, the `Night` mood's, held under the howl or the lying-down, and
  gone. On "Draw your weapon", nothing: the growl is the score, then `Combat`.
- **Effects.** Wind in the birches; dust; a raven somewhere; the healthy wolves'
  panting stopping all at once when he comes out; his paws on stone; his breath
  (close in 6 to 8, a long draw through the nose, a short huff); the sick ones'
  wet, rattling breath; the one that tries to stand (claws scraping, a whine cut
  short); the weapon laid down (wood or steel on earth, never dropped); the howl
  (long, old, cracking at the top), echoing off the rock and coming back from the
  Verge; the Blind's fire faint on the wind in shot 13.

## VFX

- Dust motes in the low sun.
- The sick wolves: milky eyes, black gums (texture variant on `wolf_blighted`).
- The arcanist's smoke from closed fingers.
- Breath-smoke: none (a warm day). Greymuzzle's breath moves the hair at her
  temple in shot 7 (a hair-spring impulse).

## In, out, skip, subtitles

- **In.** On the interaction: bars in, the world held (the Pack's AI paused,
  the other wolves on their marks).
- **Out.** Into play at the Hollow, the Pack neutral (or allied, or hostile);
  shot 13 only if its conditions hold.
- **Skip.** Skips to the next choice, never past one; after the last, to the
  end state.
- **Subtitles.** The narrator in italics.

## What it needs

Kneeling on one knee and on both, and holding out a hand, palm up (missing
clips); laying a shield, a weapon or a bow on the ground (missing); driving a
weapon into the earth (missing); a wolf sniffing (head-turn and muzzle-lift
on the wolf rig: Beasts.cs composes moves over poses, so the sniff can be
composed); a wolf lip-curl (a jaw/lip pose); a wolf lying down from standing
(exists in the beasts' clips as rest); a one-off tail-wag; the howl
(`wolf_alpha`'s); a sick wolf failing to rise. Maeca standing among the birches
on the ridge (her NPC placed for the shot).
