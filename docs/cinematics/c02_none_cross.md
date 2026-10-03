# C02 · None Cross After Dark

**The Ford-Warden: introduction.** Priority 1 · Prologue · about 44 s · skippable

## What it does

The ford at the end of the night: three blue lamps on iron posts, the drowned
standing in the deep water below the stones like a congregation, and an arm
standing up out of the river holding a lamp clear of it. Something under the water
is singing the Order's evening call. It rises, a giant in a hood with a beard of
river, and does what a keeper of a crossing does with a traveller: it lifts its
lamp to her face to see who she is. The light finds the weed in her hair, the same
weed the drowned wear. It gives her an order it gives the dead. Then it gives her
the one it gives the living.

- **The Warden wants** what he has wanted since before the Watch was the Watch:
  nobody across after dark. **He hides** how tired he is: the lamp-arm trembles
  once, the first time anything about him has, and he masters it (C03 lets it go).
  **He reveals**, without a word that says so, that he has seen her before.
- **She wants** to cross. **She is told** something she cannot use yet.
- **Plants:** "Lie down." (the Order's word for the dead, against his own fight
  bark "Rise, you who drowned here"; paid inside Act 1 when Chid's burial hymn at
  Nell's grave begins with it, C08; and by Act 3's choice to lie down in the chain); the lamp-iron in his fist
  is new iron in an ancient gauntlet (someone waded out and put it there: paid when
  she shows it to Brannoc, `brannoc.mark`, and he says "Mine."); the Order's call
  "Lamps are lit. Stay where they reach." (the Waystation still says it at dusk,
  `folk.json`, without knowing where it comes from); the trembling arm (C03).
- **Pays:** C01's weed and wet hair (the lamp finds them); the dead watchman's
  belt-book ("I can hear it singing in the water").

## Trigger and facts

- Replaces `Prologue.StartIntro` / `RunIntro`: plays when she comes within 17 m of
  the ford (`p.Z < ford.Z + 17`) in `Stage.ToFord`.
- Reads: calling (shot 7's blocking).
- Sets nothing. Hands back into `Stage.Boss` as `RunIntro` does now, with one
  change: **the Warden is spawned where the cinematic leaves him**, an arm's length
  north of her, facing her, not at his bed.

## Place, time, light

- **Lowford, the Low Ford.** The river runs east-west at about z -44, its surface
  at y -1.05. The ford proper is a bar of stones knee-deep, crossing north-south at
  x -3 to 5. Downstream (east) of the stones the bed drops into a pool waist-deep,
  x 0 to 12, z -42 to -54: the Warden lies in it and the drowned stand in it. The
  lamps on iron posts: P0 (0, -33.5) on the near bank (light 4); P1 (-9.7, -49.6)
  and P2 (9.7, -49.6) on the far bank (lights 5, 6); all `#8ac8ff`.
- **Time:** the last hour of the night. `Atmospheres.Night`, river mist thick on
  the water, thin above it.
- **Light:** four blue lights (three posts and his lamp); nothing warm anywhere.
  The mist takes the blue and glows. Her ember (if risen tonight) gives a faint red
  at her hands: let it meet the blue on her face in shot 8. (Optional, shot 2: one
  warm point on the northern skyline above the far trees, very small: the toll
  tower's window, beyond the gate. A light sprite on the horizon is enough. The
  drowned face it.)
- **Mood:** a church at night. Then a gate.

## Cast and marks

- **The survivor** walks down the road to the water and stops at the edge beside
  the near post, at (2.5, -31), facing north (heading pi). P0 stands 2.5 m to her
  left and a little ahead.
- **The Ford-Warden** (`WardenView`, 2.6 times a man: a hooded giant, a long beard
  heavy with river, eyes of blue light, the greatsword, the lamp): lies on his back
  in the pool at (6, -46), head to the east, under the surface but for his left
  forearm, which stands straight up out of the water holding his lamp clear of it.
  His greatsword lies beside him on the bed. His wading path to her: from (6, -46)
  north-west to his end mark (3, -33.2), an arm's length from her, clear of P0.
- **The drowned** (12 risen, soaked, weed on them): standing waist-deep in the pool
  in three ragged rows, x 4 to 12, z -48 to -54, all facing the far bank (north),
  heads bowed, unmoving. They turn in shot 10.

## Shot list

| # | Shot | Lens | Camera | Framing and action | Dur. |
|---|---|---|---|---|---|
| 1 | MLS | 28 | Static, 3 m behind her at 1.4 m, looking north | Her back at the water's edge; the near post at frame left; the ford opening ahead, mist, the two far posts. In the pool to the right, an arm stands up out of the river holding a lamp. | 4.0 |
| 2 | LS | 35 | Static, at the water's surface (y -0.95) on the near bank west of the stones, looking east across the pool | The drowned standing in their rows in the water, heads bowed, facing away from her. The mist moves; they do not. The lamp-arm in the middle distance. | 4.0 |
| 3 | INSERT | 135 | Slow push in | The fist and the lamp: an ancient gauntlet, black with river and grown with weed, and gripped in it a lamp-iron that is new: clean black iron, unrusted, its edges still sharp from the forge. Blue light in it, steady. Below, the surface trembles in time with a sound. | 3.5 |
| 4 | CU | 85 | Static, frontal | Her face, listening. Line W1 rises from under the water. | 4.0 |
| 5 | LS | 24 | Static, low over the pool (0.2 m above the water), near his head | He rises: the head comes up first, water sheeting off the hood and the beard; he sits up like a drowned man sitting up, hands on the bed of the river, a pause; he stands, and keeps standing, taller than the far posts. The lamp never touches the water. | 5.0 |
| 6 | MS | 35 | Tracking backward ahead of him at waist height, then settling | He wades to her, not fast, the greatsword dragging on the stones in his right hand, the lamp in his left. He stops an arm's length from her. | 4.0 |
| 7 | 2S | 50 | Static, profile, both in frame | He bends (a long way down) and lifts the lamp to her face, the way the keeper of a crossing looks at a traveller. Her calling's stance (see Calling). Halfway up, the lamp-arm trembles: once, badly. He steadies it. | 4.0 |
| 8 | ECU | 135 | Static | Her face in the lamp's light: the eyes with the flame small in each, the wet hair, and in it the green weed, which the light finds and holds on. The lamp is close enough to her lips that breath would show in its light; none does. Blue on one side of her face; her own ember's red faint on the other. Line W2, very quietly, off. | 3.5 |
| 9 | CU | 85 | Static, low, up at him past the lamp | His face under the hood lit from below: the beard streaming, two points of blue light for eyes. After W2 he holds the look a full second, then straightens. | 3.0 |
| 10 | LS | 35 | Static, low on the water behind his legs, looking east down the pool | Behind him, every one of the drowned turns its face toward her at once, a wave down the rows. | 2.5 |
| 11 | LS | 24 | Static, low on the near bank, the whole ford | Line W3. His eyes flare; all three posts flare with them (a frost nova at each); ice runs out from each post across the water. The drowned lift their heads. Title card: **THE FORD-WARDEN** / *Keeper of the Low Crossing*. | 4.5 |
| 12 | MS to play | 35 to play | Pull back and up into the follow camera | He sets his guard. Bars out; the boss bar and the lamps' tip come up. Control. | 2.0 |

Total: 44.0 s.

## Performance

**The Ford-Warden** (no face rig: the hood, the beard and the eye-lights carry
him). Not a beast: every movement is a tired man's, made enormous. He rises the way
an old man gets out of a cold bath. He does not hurry. When he lifts the lamp he
tilts his head to look, the way you look at a face you think you know. (What a
keeper of a crossing looks for, holding a lamp to a face at night, is the breath:
hers does not show in the lamp's light. Nobody says so; C09 lets it be seen.) The
tremble in shot 7 is the only weakness he shows until C03: a shudder down the arm,
the lamp swinging, and then the arm locked again. W2 is said looking at the weed,
not her eyes. W3 is the gate shutting: the whole body behind it.

**The survivor.**
- *Shot 4.* `brows_up` 0.2: listening. Gaze on the lamp-arm (0, -0.1).
- *Shot 7.* She does not step back. Gaze up into the lamp (0, -0.6); `squint` 0.3.
- *Shot 8.* On W2 her pupils hold. `brows_sad` rises to 0.35 over 1.5 s: not fear;
  the look of someone given an order meant for someone else, and not sure it is.
  A blink half a second after the line.
- *Shot 11 on.* `brows_angry` 0.4, `mouth_open` 0.1. Gaze on his chest.

## Calling (shot 7)

- *Warden:* her shield is up between them; he lifts the lamp over its rim, and
  looks down at her over it.
- *Reaver:* the cleaver hangs low at her side; she lifts her chin into the light to
  let him look.
- *Arcanist:* her hands are lit; his blue and her fire meet on her face, and the
  blue does not win.
- *Stalker:* an arrow drawn on his eye (or a knife turned along her wrist) the whole
  time. He does not care.

## Lines

Conversation `cin_none_cross`, speaker `ford_warden`. *Casting:* a very low bass
with no age and no accent that belongs to the valley now: something older than
every voice in it. A long cave reverb with the water in it. W1 is sung.

| VO id | Shot | Line | Note |
|---|---|---|---|
| `cin_none_cross.call` | 4 | *(sung, under the water)* Lamps are lit... / stay where they reach... | The Order's evening call, slowed to a dirge, heard through water. Twice; the second trails off as he rises. |
| `cin_none_cross.lie_down` | 8 | Lie down. | Quiet. Not a threat: the Order's word for the dead (its burial hymn begins with it, C08), said to her as you would say it over a grave. |
| `cin_none_cross.none` | 11 | NONE. CROSS. AFTER DARK. | The gate shutting. Every word a stone. |

## Sound

- **Music.** `Silence` from her arrival. Under W1 nothing but the song. On shot 5 a
  long cluster swells from below: low strings and a bowed metal plate, building
  through shots 6 and 7, cut dead for W2 (the line in silence). On W3 the `Boss`
  mood enters at full on the downbeat with the **lamp motif** struck under it: the
  `Mystery` mood's bell, a fifth below its usual pitch. (C03, C09 and C13 use the
  same motif.)
- **Effects.** River: wide, slow, the ford's stones chattering. The song through
  water: low-passed, the surface buzzing with it. Rising: water sheeting off cloth
  and beard, a long pour. Wading: heavy displacement, the greatsword dragging on
  stone. The lamp: a faint glassy hum, louder in 7 and 8; the tremble's rattle of
  iron. W3: the posts flaring (the frost-nova sound), ice cracking across the water.

## VFX

- River mist, thick on the water, parting round him as he wades.
- The drowned: soaked, weed on them; their turn a staggered 0.1 s wave down the rows.
- Water sheeting off him; wakes as he wades.
- The lamp's light on her face, its flame in her eyes, a highlight held on the weed
  (shot 8).
- The posts' frost novas and a skin of ice spreading from each across the water for
  2 m.

## In, out, skip, subtitles

- **In.** Captured mid-stride as she crosses the trigger; bars in over 0.6 s; the
  world held (`WorldRate` 0.001, as now); the nearby dead cleared
  (`ClearAround(ford, 30)`) before shot 1.
- **Out.** The Warden spawned at his end mark (3, -33.2), facing her, `Stage.Boss`;
  objectives "Cross at the Low Ford" and "Put out the lamps"; bars out, boss bar in.
- **Skip.** Lands on the hand-back state.
- **Subtitles.** W1 in italics under "The Ford-Warden"; W2 and W3 as said.

## What it needs

`WardenView` lying in water, rising lying to sitting to standing, lifting the lamp
to a face (left arm raised and forward, head tilted), a tremble on the arm; the lamp
on its own bone. A lamp-iron model shared with the `wardens_lampiron` item (it drops
when he dies). Risen standing in deep water. A pool below the stones (the ford's
water deeper east of the bar). Mist that parts.
