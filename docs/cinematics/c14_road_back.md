# C14 · The Road Back

**Brannoc goes for Nell.** Priority 2 · Act 1 · conditional (only if she told
Brannoc the truth) · four parts: dusk 18 s + choice, the road 30 s, the
arrival 10 s, dawn 48 s · skippable

## What it does

On the evening of the day she told him, Brannoc banks the forge before dark. He
takes a lantern, his hammer and a folded blanket, and goes to get his daughter.
He doesn't ask the survivor to come. He says she knows the place, which is true:
she put Nell down there.

If she goes with him, they walk south down the Low Ford road in the dark. The
road is lit all the way down to the ford by ember burning blue in new black irons:
his irons, with his mark under every socket. He walks past every one of them and
doesn't look up. At the ford itself the three posts stand black and broken where
the Warden smashed them, and the dark there is where the Warden was. They wade it
and go on to the wagon on its side and the ditch beside it.

While he climbs down into the ditch, the drowned stand up out of the river, in the
blue of the nearest road iron, and come towards the brightest thing in the dark,
which is her. At their head walks a big man in a carter's coat, with a copper
token tucked in his hatband where carters keep them: Wat, who said he'd be over
the ford by dark.

It is the night's fight, and Brannoc fights in it, at the edge of his lantern's
light, with his hammer. At dawn Wat is down. Brannoc kneels by him, says his name,
and takes the token from his hat. He has watched Wat's light go into the
survivor's hands. Then he goes down into the ditch and lifts his daughter, and
carries her home up the road in the sunrise, past his own irons, which are still
burning, pale in the daylight. At the gate Chid walks out past the guards to meet
him, and walks beside him up the street.

- **Brannoc wants** to bring her home with his own hands, and to do it before
  anyone can offer to help. **He hides** that he has already begun to work out
  whose coin paid for the irons; the token tells him the rest. **He changes**: by
  dawn he knows whose road it was, and says nothing about it for an act. In C27 he
  says "Tell her no," and he says "her".
- **The survivor wants** to make it right, and can't. **She is** the one person who
  knows where Nell lies, because she put her there. Each ember she takes from the
  drowned tonight is one of them: Wat, the carters. Nobody knows that yet.
- **Wat wants** nothing. He is doing what he was doing when he died: crossing the
  ford by dark.
- **Plants:**
  - Brannoc watching Wat's light go into the survivor's hands (Act 3, C43: at the
    bottom of the stair he looks at her hands again, knowing what the light was);
  - the toll-token (C27: on the anvil, with "Tell her no.");
  - Wat burned by the survivor (Act 2: the first memory that comes in at dawn when
    one goes is a grey mare who would not take a bit in winter);
  - the irons still lit on the road (Act 2: he breaks the last two; the Kiln Ford
    stays dark);
  - Brannoc's breath and hers in the lantern's light (he notices; he says
    nothing);
  - Chid, at the gate at sunrise, seeing her breath begin to smoke.
- **Pays:**
  - C07 (the truth, and the place she knows);
  - the prologue's ambush ("One of them is still holding the reins.");
  - "Wat went. Wat's not back." (the notice board);
  - `brannoc.nell` ("Said he'd be over the ford by dark.");
  - C03 shot 12 (the road's lamps are his irons) and C02's broken posts;
  - the merciful routes' missing night: telling him the truth earns the act's
    hardest fight.

## Trigger and facts

- **Dusk** (`DATA + CODE, to do`): the evening of the day `nell.told` became
  `gone` or `risen`, the first time she passes the smithy after the hammer has
  stopped. Brannoc is at the forge banking the fire. A new node in his
  conversation, `brannoc.road`:
  - **Entry:** `nell.told` in `gone` or `risen`; not `nell.buried`; time dusk or
    night; npc flag `say:road` not set.
  - **Text:** line P (below).
  - **Choices:** "I'll show you." (sets `nell.road` = `with`, npc flag
    `say:road`) and "Not tonight." (sets `nell.road` = `alone`, `say:road`).
- **The road and the arena:** a story fight `night:road_back`, offered that night
  only, when `nell.road` = `with`:
  - people `dead`;
  - the place: the Low Ford road at the wagon (best: the Lowford zone itself at
    night, the prologue's ambush stage reused; otherwise an arena dressed as the
    road and the ditch);
  - an ally: Brannoc (an allied NPC with a hammer, who holds the edge of the
    lantern's light and does not chase);
  - boss: Wat.
- **Dawn:** the arena's win. `OnWin` sets `nell.brought_home` and gives nothing.
  Brannoc is not a reward. A loss: he brings her home alone, and the morning is
  the same morning.
- **The morning report** (`rules.json`, `nell.burial`):
  - It already tells his going alone: dusk, a lantern, back at sunrise with the
    blanket in his arms, Chid walking out to meet him.
  - With `nell.brought_home` (to add with the fight), it drops its first two
    sentences, because she was there. It says only "They are burying her this
    morning, behind the shrine, next to the old captain. Nobody has been asked to
    come."
- **Alone** (`nell.road` = `alone`, or she never passes the smithy): no
  cinematic. He goes; the next morning is the burial either way.
- **Reads:** `nell.told` (C07's variant); calling (the fight); sex (nothing).

## Place, time, light

- **The smithy** (the Waystation, (13.4, 14.2)) at dusk. The forge is banked to a
  red seam under ash; the rack of two irons is in shadow, and the old boots hang
  on their nail.
- **The Low Ford road at night** (Lowford): from the north gate (0, -112) south to
  the ford (0, -44), then on to the wagon on its side at (5, 60).
  - Along the road, on new black posts and brackets, Brannoc's irons burn
    ember-blue, down to the river's edge on both banks (lights 12 to 14, and
    more).
  - The ford's own three posts (lights 4 to 6) stand black, broken at the
    brackets where the Warden ran through them in C02 and C03, and give no light.
    The Warden's pool is black water, nothing standing in it, between the last
    blue iron on one bank and the first on the other.
- **Time:** dusk; night; dawn.
- **Light:**
  - Two kinds of light and nothing between them:
    - Brannoc's lantern, which burns oil: yellower and smokier than any ember
      flame, warm and low, swinging at his knee;
    - his irons' blue on the road.
  - Her ember's red at night, from inside her.
  - Dawn comes up on their right as they walk north. The irons go pale against
    it, still burning.
- **Mood:** a man doing a job. Then a father.

## Cast and marks

- **Brannoc:** his apron off for once, in a coat. A lantern in his left hand, his
  hammer through his belt, a grey blanket folded over his shoulder.
- **The survivor:** beside him, half a pace ahead on the road (she knows the
  way), dropping back at the ditch.
- **Wat:** a big man in his forties, in a carter's coat black with river, with
  weed in his hair and beard. A copper toll-token stamped with three roads is
  tucked in the band of his hat. He walks at the head of the drowned the way he
  would walk at the head of a team.
- **The drowned:** the rest of the twenty-six who did not come up in the ditch,
  out of the river.
- **Nell:** in the ditch beside the wagon, where the prologue left her: red hair
  under the weed, new boots. Seen only as the blanket and the boots.
- **Chid,** at the Waystation's south gate at sunrise.

## Shot list

### Dusk: the smithy

| # | Shot | Lens | Camera | Framing and action | Dur. |
|---|---|---|---|---|---|
| 1 | LS | 35 | Static, from across the lane | Dusk. The smithy with no hammer in it. Brannoc at the forge, shovelling ash over the fire until only a red seam shows. | 4.0 |
| 2 | MS | 50 | Static, side-on | He hangs the hammer through his belt. He takes the blanket off the shelf, folds it once more and puts it over his shoulder. He lights a lantern from a spill and closes its door. He doesn't hurry. | 6.0 |
| 3 | MCU | 50 | Static, from her side | He turns and sees her in the lane. Line P: "You know the place." Not a question. He waits. | 4.0 |
| 4 | 2S | 35 | Static | Choice: "I'll show you." / "Not tonight." *(Not tonight:)* he nods once, goes past her and out of the south gate alone; the lantern goes down the road and out. End. *(I'll show you:)* he goes past her, and she falls in beside him. | 4.0 + choice |

### The road (`night:road_back`, before the fight)

| # | Shot | Lens | Camera | Framing and action | Dur. |
|---|---|---|---|---|---|
| 5 | ELS | 24 | Static, high over the road behind them, looking south | Night. The road going down into the dark, lit at intervals by blue points: his irons on their posts, down to the river, and a gap of black where the ford is, and the blue going on beyond it. Two small figures on the road, and one warm light swinging between them. | 5.0 |
| 6 | MS | 50 | Tracking backward ahead of them at walking pace | They walk into the blue of an iron and out of it. Over Brannoc's shoulder the iron burns on its post: new, black, a bracket of his own making. He doesn't look up. His breath smokes in his lantern's light; hers doesn't. He looks at her mouth once, as he would at a weld, then at the road. | 7.0 |
| 7 | LS | 28 | Static, low, at the water's edge, looking south across the ford | They wade the ford where the Warden stood, in the dark between the irons: the water to his thighs, the lantern held high and dry, the three broken posts black against the blue of the far bank. He doesn't look at the water. | 6.0 |
| 8 | MS | 50 | Static, at the ditch's lip | The wagon on its side. She stops at the edge of the ditch and looks down into it. He follows her look. He gives her the lantern without a word, and gets down into the ditch. | 6.0 |
| 9 | LS | 35 | Static, behind her, looking north back up the road | Behind them, in the blue of the nearest iron on the bank, the river moves. Something stands up in it, then another. Bars out. Play. | 6.0 |

### The arrival (the boss spawn, 30 minutes)

| # | Shot | Lens | Camera | Framing and action | Dur. |
|---|---|---|---|---|---|
| 10 | LS | 85 | Static, low, compressed, from beside the ditch looking up the road to the river; `WorldRate` 0.3 | Out of the river, walking up the middle of the road between two blue irons, a big man in a carter's coat, weed in his beard, a copper token in the band of his hat. The drowned walk behind him like a team. | 4.0 |
| 11 | MS | 50 | Static, on Brannoc at the edge of the lantern's light, the hammer in his hand | He sees who it is. He doesn't move. Title: **WAT** / *Over the Ford by Dark*. Back to play. | 6.0 |

### Dawn (the win)

| # | Shot | Lens | Camera | Framing and action | Dur. |
|---|---|---|---|---|---|
| 12 | MS | 50 | Static, low; `WorldRate` 0.2 on the blow, then 1 | Wat goes down on his back in the road, his arms out. The rest of the drowned stop where they are and sit down in the road like tired men, and are still. | 4.0 |
| 13 | CU | 85 | Static, on her hands | Wat's light comes up out of him and goes into her, as ember does: a red thread across the road into her open hands. | 3.0 |
| 14 | MCU | 85 | Static, on Brannoc, past her shoulder | He watches it go into her. He looks at her hands for a long time, the way he looks at iron. He says nothing. | 4.0 |
| 15 | MS | 50 | Static, side-on, low | He kneels by Wat, as a smith kneels, on one knee. Line W: "...Wat." He puts his hand flat on Wat's chest, the way he held the anvil down in C07, and leaves it there until he is sure. Then he takes the token out of Wat's hatband, turns it to the light (three roads, the Toll Tower's stamp) and puts it in his coat. | 7.0 |
| 16 | LS | 35 | Static, from the ditch's far side | First light behind the trees. He gets down into the ditch, kneels, and works for a while with his back to us. When he stands, she is in the blanket in his arms, and he climbs out with her without using his hands. | 8.0 |
| 17 | INSERT | 85 | Static | The blanket's end, and two small new boots out of it. | 2.0 |
| 18 | ELS | 24 | Static, high over the road, looking north, as 5 reversed | They walk north up the road in the sunrise, him carrying her and her beside him with the lantern, past the irons. The sun is on their right. In the daylight the irons' blue is pale and small, still burning. Her breath smokes now; his always did. | 8.0 |
| 19 | MS | 50 | Static, at the Waystation's south gate, from inside | The gate opens. Chid is there already, as if he has been waiting all night, which he has. He walks out past the guards to meet Brannoc, and turns, and walks beside him up the street, a hand not quite touching the blanket. | 6.0 |
| 20 | MCU | 50 | Static, on the survivor at the gate | She stops in the gateway with the lantern. Up the street, Chid looks back at her once: at her face, and at her breath smoking in the cold. Then he goes on. Somebody up the street is baking. Bars out, or straight into C08. | 6.0 |

## Lines

Conversation `cin_road_back`, speaker `brannoc`. Two lines in the whole
cinematic.

| VO id | Shot | Line | Note |
|---|---|---|---|
| `cin_road_back.place` | 3 | You know the place. | Not a question and not a request. Low. She told him in C07 that she put Nell down; he is telling her he needs her to show him where. |
| `cin_road_back.wat` | 15 | ...Wat. | A man's name said to a man he drank with. No grief in it yet. |

The choices at shot 4 are read, not voiced. In the data they belong to
`brannoc.road` (Trigger, above); `cin_road_back` holds the two voiced lines, for
casting and checking.

## Performance

**Brannoc.**
- He does everything tonight the way he does a job: banking the forge, folding
  the blanket, lighting the lantern, the order of it.
- On the road he never looks up at the irons. That is the whole performance of
  shot 6.
- He fights at the edge of the light, not in the dark: short, heavy strokes, a
  smith's economy, never chasing. He is holding a line, not winning a fight.
- At Wat he is still for a long moment before the title.
- At dawn he kneels to Wat as a smith kneels, as he will at the grave in C08. The
  hand flat on the chest is the anvil's gesture, holding something down until it
  stays.
- He carries her as if she weighed what she weighs, which is not much, and he
  never shifts his grip.
- No face rig: everything is the head, the hands and the walk.

**Wat.** Mindless, and still a carter: he walks with his shoulders forward like a
man leading a team up a hill. He does not snarl. He keeps coming.

**Chid.** At the gate he is not cheerful and not delighted, for the only time in
Act 1. He walks at Brannoc's pace. The look back at the survivor is short; what he
sees in her breath he already knew.

**The survivor.**
- *Shot 3.* `brows_sad` 0.3. Her gaze drops, then comes back to him.
- *Shot 6.* Gaze ahead on the road (she is leading).
- *Shot 8.* At the ditch's lip, gaze down into it, `brows_sad` 0.5, `frown` 0.2.
  She does not look at him while he climbs down.
- *Shot 13.* Her hands open as the light comes; she does not look at them. Her
  gaze is on Wat.
- *Shot 14.* She feels Brannoc looking, and looks at him; she holds it.
- *Shot 20.* `brows_sad` 0.35. She meets Chid's look, then watches them both go up
  the street until they turn the corner. She doesn't follow.

## Sound

- **Music.**
  - Dusk: none. The lane, a dog, the forge's last breath.
  - The road: the `Night` mood's lowest drone, very quiet, and the irons' hum as
    they pass each one; at the ford, between the irons, no hum at all.
  - The arrival: the horde music drops out under the drowned rising; one long low
    note on the title, then the `Boss` mood.
  - Dawn: music cut on the blow, and silence while he kneels. On the walk home, a
    single line of the burial hymn's tune ("Lie Down", C08) on one instrument,
    once through, slowly, ending as they reach the gate. It is the first time the
    player hears the tune; C08 is the second.
- **Effects.**
  - the shovel in the ash; the lantern's door; boots on the road; the irons' hum;
  - water to the thigh; the ditch's mud; Wat's boots in the river;
  - the hammer's blows, dull: iron into flesh, not iron into iron;
  - the gate; the town waking.

## VFX

- The lantern (oil: yellow, smoky) and the irons (ember: blue), never mixed.
- Her ember's red at night; the red thread from Wat to her hands (13); her breath
  starting at dawn (18 to 20).
- Breath-smoke on Brannoc all night.
- The drowned sitting down in the road at Wat's fall.

## In, out, skip, subtitles

- **Dusk.** Bars in as she nears the smithy at dusk with the trigger met. Out
  after the choice into play (*Not tonight*), or straight into the road (*I'll
  show you*).
- **The road.** Into the fight, bars out on shot 9.
- **Arrival.** As C10.
- **Dawn.** From the win's last blow, before the reckoning. Out at the gate into
  the morning, which is the burial's: C08 picks up from its shot 2 as she crosses
  the square.
- **Skip.** Each part on its own. Skipping dawn lands at the gate.
- **Subtitles.** The two lines, under "Brannoc".

## What it needs

- **A story fight in a place that already exists:** the prologue's Lowford road at
  night, reused, with the ambush's wagon and ditch, the road's irons lit and the
  ford's three posts broken and dark.
- **An allied NPC in a fight:** Brannoc, holding the edge of a light.
- **A boss built from a risen:** Wat, a big drowned carter with a token in his
  hatband.
- **The horde told to stop and sit down.**
- **The report's variant** for `nell.brought_home`.
- **Clips:**
  - banking a forge (shovelling);
  - folding a blanket;
  - wading thigh-deep with a lantern held high;
  - climbing down into a ditch and out of it carrying;
  - carrying a small body in a blanket (in the README's list);
  - kneeling on one knee by a body with a hand flat on its chest;
  - walking beside someone, a hand not quite touching.
- **The ember-to-hands thread** (exists in play; framed here).
- **Breath:** Brannoc's breath in a lantern's light, and hers absent until dawn.
- **An oil flame:** yellower and smokier than the ember lamps.
- **The burial hymn's tune** as a solo line (C08's melody).
