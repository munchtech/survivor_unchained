# C14 · The Road Back

**Brannoc goes for Nell.** Priority 2 · Act 1 · conditional (only if she told
Brannoc the truth) · four parts: dusk 18 s + choice, the road 30 s, the
arrival 10 s, dawn 52 s · skippable

## What it does

On the evening of the day she told him, Brannoc banks the forge before dark,
which nobody in the Waystation has seen him do. He takes a lantern, his hammer
and a folded blanket, and he goes to get his daughter. He doesn't ask the
survivor to come. He says she knows the place, which is true: she put Nell down
there.

If she goes with him, they walk south down the Low Ford road in the dark. The
road is lit, all the way to the ford, by ember burning blue in new black irons:
his irons, his mark under every socket. He walks past every one of them and
doesn't look up. They wade the ford where the Warden stood, and go on to the
wagon on its side and the ditch beside it. While he climbs down into the ditch,
the drowned come up out of the ford behind them, towards the brightest thing in
the dark, which is her. At their head walks a big man in a carter's coat, with
a copper token on a cord round his neck: Wat, who said he'd be over the ford by
dark.

It is the night's fight, and Brannoc fights in it, at the edge of the light,
with his hammer. At dawn Wat is down. Brannoc kneels by him and says his name.
He takes the token off Wat's neck and looks at it. Then he goes down into the
ditch and lifts his daughter, and carries her home up the road in the sunrise,
past his own irons, which are still burning, pale in the daylight. At the gate
the watchman takes his helmet off. Brannoc doesn't stop.

- **Brannoc wants** to bring her home with his own hands, and to do it before
  anyone can offer to help. **He hides** that he has already begun to work out
  whose coin paid for the irons; the token tells him the rest. **He changes**: by
  dawn he knows whose road it was, and he says nothing about it for an act. In
  C27 he says "Tell her no," and he says "her".
- **The survivor wants** to make it right, and can't. **She is** the one person who
  knows where Nell lies, because she put her there. Each ember she takes from the
  drowned tonight is one of them: Wat, the carters. Nobody knows that yet.
- **Wat wants** nothing. He is doing what he was doing when he died: crossing the
  ford by dark.
- **Plants:**
  - Brannoc watching Wat's light go into the survivor's hands (Act 3: at the
    bottom of the stair, "He looks at your hands for a long time, the way he looks
    at iron to see what is in it");
  - the toll-token (C27: "Tell her no.");
  - Wat burned by the survivor (Act 2: the first memory that comes in at dawn
    when one goes is a grey mare who would not take a bit in winter);
  - the irons still lit on the road (Act 2: he breaks the last two; the Kiln Ford
    stays dark);
  - Brannoc's breath and hers in the lantern light (he notices; he says
    nothing).
- **Pays:**
  - C07 ("Was it quick?"; the hammer laid down; the boots on the nail);
  - the prologue's ambush ("One of them is still holding the reins.");
  - "Wat went. Wat's not back." (the notice board);
  - `brannoc.nell` ("Said he'd be over the ford by dark.");
  - C03 shot 12 (the road's lamps are his irons);
  - C04 (the gate, the guard, a dawn arrival);
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
- **The road and the arena:** a story fight `night:road_back`, offered that
  night only, when `nell.road` = `with`:
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
- **Alone** (`nell.road` = `alone`, or she never passes the smithy): no
  cinematic. He goes; the next morning is the burial (rule `nell.burial`)
  either way.
- **Reads:** `nell.told` (C07's variant); `brannoc.saw_iron` (in the road shot he
  doesn't look up at the irons; if he saw the Warden's iron in C07, he doesn't
  look up harder); calling (the fight); sex (nothing).

## Place, time, light

- **The smithy** (the Waystation, (13.4, 14.2)) at dusk. The forge is banked to
  a red seam under ash, the rack of two irons is in shadow, and the boots hang on
  their nail.
- **The Low Ford road at night** (Lowford): from the north gate (0, -112) south
  to the ford (0, -44), then on to the wagon on its side at (5, 60). Along the
  road, on new black posts and brackets, Brannoc's irons burn ember-blue:
  - the three at the ford (lights 4 to 6);
  - more along the road on either side of the river (lights 12 to 14).
  The ford is empty now: the Warden's pool is black water with the posts' blue
  on it, and nothing standing in it.
- **Time:** dusk; night; dawn.
- **Light:**
  - Two lights and nothing else between them: Brannoc's lantern (oil, warm, low,
    swinging at his knee) and his irons' blue on the road.
  - Her ember's red at night, from inside her.
  - Dawn comes up behind them in the east as they walk north. The irons go pale
    against it, still burning.
- **Mood:** a man doing a job. Then a father.

## Cast and marks

- **Brannoc:** his apron off for once, in a coat. A lantern in his left hand,
  his hammer through his belt, a grey blanket folded over his shoulder.
- **The survivor:** beside him, half a pace ahead on the road (she knows the
  way), dropping back at the ditch.
- **Wat:** a big man, forties, a carter's coat black with river, his hair and
  beard full of weed. Round his neck on a cord, a copper toll-token stamped with
  three roads. He walks at the head of the drowned the way he would walk at the
  head of a team.
- **The drowned:** the rest of the twenty-six who did not come up in the ditch,
  out of the ford.
- **Nell:** in the ditch beside the wagon, where the prologue left her. Red hair
  under the weed, new boots. Seen only as the blanket and the boots.
- **The watchman** at the Waystation's south gate: the guard from C04.

## Shot list

### Dusk: the smithy

| # | Shot | Lens | Camera | Framing and action | Dur. |
|---|---|---|---|---|---|
| 1 | LS | 35 | Static, from across the lane | Dusk. The smithy with no hammer in it. Brannoc at the forge, shovelling ash over the fire until only a red seam shows. The lane has stopped to watch him do it. | 4.0 |
| 2 | MS | 50 | Static, side-on | He hangs the hammer through his belt. He takes the blanket off the shelf and folds it once more and puts it over his shoulder. He lights a lantern from the seam and closes its door. He doesn't hurry. | 6.0 |
| 3 | MCU | 50 | Static, from her side | He turns and sees her in the lane. Line P: "You know the place." Not a question. He waits. | 4.0 |
| 4 | 2S | 35 | Static | Choice: "I'll show you." / "Not tonight." *(Not tonight:)* he nods once, goes past her and out of the south gate alone; the lantern goes down the road and out. End. *(I'll show you:)* he goes past her, and she falls in beside him. | 4.0 + choice |

### The road (`night:road_back`, before the fight)

| # | Shot | Lens | Camera | Framing and action | Dur. |
|---|---|---|---|---|---|
| 5 | ELS | 24 | Static, high over the road behind them, looking south | Night. The road going down into the dark, lit at intervals by blue points: his irons on their posts, all the way to the ford and past it. Two small figures on it and one warm light swinging between them. | 5.0 |
| 6 | MS | 50 | Tracking backward ahead of them at walking pace | They walk into the blue of an iron and out of it. Over Brannoc's shoulder the iron burns on its post: new, black, a bracket of his own making. He doesn't look up. His breath smokes in his lantern's light; hers doesn't. He looks at her mouth once, as he would at a weld, then at the road. | 7.0 |
| 7 | LS | 28 | Static, low, at the water's edge, looking south across the ford | They wade the ford where the Warden stood. The water to his thighs; the lantern held high and dry. The three posts burn blue round them. He doesn't look at the water. | 6.0 |
| 8 | MS | 50 | Static, at the ditch's lip | The wagon on its side. She stops at the edge of the ditch and looks down into it. He follows her look. He gives her the lantern, without a word, and gets down into the ditch. | 6.0 |
| 9 | LS | 35 | Static, behind her, looking north back up the road | Behind them, in the blue of the ford's posts, the water moves. Something stands up in it, then another. Bars out. Play. | 6.0 |

### The arrival (the boss spawn, 30 minutes)

| # | Shot | Lens | Camera | Framing and action | Dur. |
|---|---|---|---|---|---|
| 10 | LS | 85 | Static, low, compressed, from beside the ditch looking up the road at the ford; `WorldRate` 0.3 | Out of the river, walking up the middle of the road between the blue lamps, a big man in a carter's coat, the weed in his beard, a copper token swinging on his chest. The drowned go behind him like a team. | 4.0 |
| 11 | MS | 50 | Static, on Brannoc at the edge of the lantern's light, the hammer in his hand | He sees who it is. He doesn't move. Title: **WAT** / *Over the Ford by Dark*. Back to play. | 6.0 |

### Dawn (the win)

| # | Shot | Lens | Camera | Framing and action | Dur. |
|---|---|---|---|---|---|
| 12 | MS | 50 | Static, low; `WorldRate` 0.2 on the blow, then 1 | Wat goes down on his back in the road, his arms out. The rest of the drowned stop where they are and sit down in the road like tired men, and are still. | 4.0 |
| 13 | CU | 85 | Static, on her hands | Wat's light comes up out of him and goes into her, as ember does: a red thread across the road into her open hands. | 3.0 |
| 14 | MCU | 85 | Static, on Brannoc, past her shoulder | He watches it go into her. He looks at her hands for a long time, the way he looks at iron. He says nothing. | 4.0 |
| 15 | MS | 50 | Static, side-on, low | He kneels by Wat, as a smith kneels, on one knee. Line W: "...Wat." He closes Wat's eyes with two fingers. He lifts the token on its cord over Wat's head, turns it to the light: three roads, the Toll Tower's stamp. He puts it in his coat. | 7.0 |
| 16 | LS | 35 | Static, from the ditch's far side | First light behind the trees. He gets down into the ditch, and kneels, and works for a while with his back to us. When he stands, she is in the blanket in his arms, and he climbs out with her without using his hands. | 8.0 |
| 17 | INSERT | 85 | Static | The blanket's end, and two small new boots out of it. | 2.0 |
| 18 | ELS | 24 | Static, high over the road, looking north, as 5 reversed | They walk north up the road in the sunrise, him carrying her, her beside him with the lantern, past the irons. In the daylight the irons' blue is pale and small, still burning. Her breath smokes now; his always did. | 8.0 |
| 19 | MS | 50 | Static, at the Waystation's south gate, from inside | The gate opens. The watchman from C04 sees what he is carrying and takes his helmet off. Brannoc doesn't stop. He goes past the watchman and up the street with her. | 6.0 |
| 20 | MCU | 50 | Static, on the survivor at the gate | She stops in the gateway. Up the street the town is waking. Somebody is baking. No hammer starts. Bars out. | 6.0 |

## Lines

Conversation `cin_road_back`, speaker `brannoc`. Two lines in the whole
cinematic.

| VO id | Shot | Line | Note |
|---|---|---|---|
| `cin_road_back.place` | 3 | You know the place. | Not a question and not a request. Low. He is telling her what he has worked out: that she was there. |
| `cin_road_back.wat` | 15 | ...Wat. | A man's name said to a man he drank with. No grief in it yet. |

The choices at shot 4 are read, not voiced. In the data they belong to
`brannoc.road` (Trigger, above); `cin_road_back` holds the two voiced lines,
for casting and checking.

## Performance

**Brannoc.**
- He does everything tonight the way he does a job: banking the forge, folding
  the blanket, lighting the lantern, the order of it.
- On the road he never looks up at the irons. That is the whole performance of
  shot 6.
- He fights at the edge of the light, not in the dark: short, heavy strokes, a
  smith's economy, never chasing. He is holding a line, not winning a fight.
- At Wat he is still for a long moment before the title.
- At dawn he kneels to Wat exactly as he knelt at the anvil and will kneel at the
  grave.
- He carries her as if she weighed what she weighs, which is not much, and he
  never shifts his grip.
- No face rig: everything is the head, the hands and the walk.

**Wat.** Mindless, and still a carter: he walks with his shoulders forward like a
man leading a team up a hill. He does not snarl. He keeps coming.

**The survivor.**
- *Shot 3.* `brows_sad` 0.3. Her gaze drops, then comes back to him.
- *Shot 6.* Gaze ahead on the road (she is leading).
- *Shot 8.* At the ditch's lip, gaze down into it, `brows_sad` 0.5, `frown` 0.2.
  She does not look at him while he climbs down.
- *Shot 13.* Her hands open as the light comes; she does not look at them. Her
  gaze is on Wat.
- *Shot 14.* She feels Brannoc looking, and looks at him; she holds it.
- *Shot 20.* `brows_sad` 0.35; she watches him go up the street until he turns the
  corner. She doesn't follow.

## Sound

- **Music.**
  - Dusk: none. The lane, a dog, the forge's last breath.
  - The road: the `Night` mood's lowest drone, very quiet, and the ford posts'
    hum as they pass.
  - The arrival: the horde music drops out under the drowned rising; one long low
    note on the title, then the `Boss` mood.
  - Dawn: music cut on the blow. Silence while he kneels. On the walk home, a
    single line of the burial hymn's tune ("Lie Down", C08) on one instrument,
    once through, slowly, ending as they reach the gate. It is the first time the
    player hears the tune; C08 is the second.
- **Effects.** The shovel in the ash; the lantern's door; boots on the road; the
  irons' hum; water to the thigh; the ditch's mud; Wat's boots in the river; the
  hammer's blows, dull, iron into flesh, not iron into iron; the token's cord;
  the gate; the town waking; no hammer.

## VFX

- The lantern (warm, oil) and the irons (blue, ember), never mixed.
- Her ember's red at night; the red thread from Wat to her hands (13); her breath
  starting at dawn (18).
- Breath-smoke on Brannoc all night.
- The drowned sitting down in the road at Wat's fall.

## In, out, skip, subtitles

- **Dusk:** bars in as she nears the smithy at dusk with the trigger met; out
  after the choice into play (*Not tonight*) or straight into the road (*I'll show
  you*).
- **The road:** into the fight, bars out on shot 9.
- **Arrival:** as C10.
- **Dawn:** from the win's last blow, before the reckoning; out at the gate into
  the morning, which is the burial's (C08 plays when she next steps out of the
  Last Lamp).
- **Skip:** each part on its own. Skipping dawn lands at the gate.
- **Subtitles:** the two lines, under "Brannoc".

## What it needs

- **A story fight in a place that already exists:** the prologue's Lowford road at
  night, reused, with the ambush's wagon and ditch.
- **An allied NPC in a fight:** Brannoc, holding the edge of a light.
- **A boss built from a risen:** Wat, a big drowned carter with a token on a
  cord.
- **The horde told to stop and sit down.**
- **Clips:**
  - banking a forge (shovelling);
  - folding a blanket;
  - wading thigh-deep with a lantern held high;
  - climbing down into a ditch and out of it carrying;
  - carrying a small body in a blanket (in the README's list);
  - kneeling on one knee by a body, closing its eyes;
  - lifting a cord over a head.
- **The ember-to-hands thread** (exists in play; framed here).
- **Breath:** Brannoc's breath in a lantern's light, and hers absent until dawn.
- **The burial hymn's tune** as a solo line (C08's melody).
