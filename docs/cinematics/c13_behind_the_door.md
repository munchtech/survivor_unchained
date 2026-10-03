# C13 · Behind the Sealed Door

**The Barrow Lord: arrival and the kneel.** Priority 3 · Act 1, optional (the
vault, with the sigil's fragment, after dark) · door 12.5 s, arrival 8 s, kneel
16 s · skippable

## What it does

She sets the wedge of black stone in its notch after dark, and the violet sigil
wakes like an eye opening, and the door lets her in: a stair going down, older
than the door, and the Seventh Legion's dead coming up it. At the half hour
their officer comes up out of the dark: the Barrow Lord, armour green with age,
a crest of iron. He looks at her and says one word in the old empire's tongue,
and the dead come on. When he falls he does not fall: he goes down on one knee
before her and bows his head, and says one more word, and the dead stop, and
crumble, and the way back up is open. Below, far down the stair, someone is
standing with his back to her, holding a little lantern with violet glass in it.
He does not turn round.

- **The Barrow Lord wants** what the Legion has wanted for two thousand years:
  the inner door held. **He reveals** that the dead know what she is: they have
  been waiting for her, and she is early.
- **She wants** to know what is behind the door. **She learns** that something
  down there was expecting her.
- **Pays:** the bones at the door ("It was never locked from the outside"); the
  bootprints going in and none coming out, and the toll-token in one (Jessop);
  Vonnra's "you know better than to ask me what is behind it" (`vonnra.arcana`);
  the words over the door. By day, in `Verge.cs` (`vaultdoor`), the door is
  inscribed in the old empire's tongue: HIC LEGIO SEPTIMA SEPELIVIT QUOD URERE
  NON POTUIT. A reader (arcana, or the scholar's lens) sees it translated ("Here
  the Seventh Legion buried what it could not burn."); anyone else sees only the
  dead tongue. So the language is on the page before he speaks it, and his two
  words are a reward for the reader and a sound for everyone else.
- **Plants:** "Nondum" and "Redi" (Act 3: the dead part for the Morrow's own light);
  Jessop on the stair (Act 3, the stair); the violet glass in his lantern
  (Vonnra's colour).

## Trigger and facts

- **The door:** the story fight `vault` (`night:vault`) when chosen.
- **Arrival:** the boss spawn in `vault_opened`. **The kneel:** the boss's death
  there.
- Reads: `knows arcana` or `hasTag scholar_lens` (the Latin is translated in the
  subtitles only for a reader); `knows faith` (the bones' voice in the door shot);
  `vonnra.asked_jessop` (nothing changes; the stair is the same).
- Sets nothing (the arena's `OnWin` sets `vault.opened` and the rest).

## Place, time, light

- **The door:** the Verge's sealed door (-106, -56), at night: black stone,
  smooth as glass, the sigil of seven notches violet and waking.
- **The arena** (people `dead`, theme `blight`) for the fight; the kneel staged
  from his fall; its last shot looks down "the stair" (a set dressed at the
  arena's way out: steps cut in black stone going down into the dark).
- **Light:** violet from the sigil; cold green-grey in the arena's blight; the
  dead's eye-lights; and far below on the stair, one small violet point.

## The door

| # | Shot | Lens | Camera | Framing and action | Dur. |
|---|---|---|---|---|---|
| 1 | INSERT | 85 | Static | Her hand sets the black wedge into the empty notch. It fits. | 2.0 |
| 2 | CU | 50 | Static, on the sigil, then a slow tilt up | Under her hand the whole sigil wakes, violet, from the notch outward along the seven arms, like an eye opening; its light climbs the stone and finds the cut letters over the door, HIC LEGIO SEPTIMA..., one by one. *(Faith: the bones at the door whisper, very low: "It was never locked from the outside.")* | 4.5 |
| 3 | LS | 35 | Static, low, behind her | The door does not swing: it sinks into the ground. Behind it, a stair cut in black stone going down into the dark. Coming up it, slowly, shapes with points of light for eyes. | 6.0 |

## Arrival

| # | Shot | Lens | Camera | Framing and action | Dur. |
|---|---|---|---|---|---|
| 1 | MS | 35 | Static, low; `WorldRate` 0.3 | The dead part. Through them comes an officer of the Legion, taller than they are, armour green with age, an iron crest. He stops and looks at her: a long look, the eye-lights narrowing. | 4.5 |
| 2 | MCU | 50 | Static | Line B1. He raises his sword, and the dead come on. Title: **THE BARROW LORD** / *Of the Seventh Legion*. | 3.5 |

## The kneel

| # | Shot | Lens | Camera | Framing and action | Dur. |
|---|---|---|---|---|---|
| 1 | MS | 50 | Static, low; `WorldRate` 0.2 on the blow | The blow. He does not fall. He goes down on one knee before her, sword point to the ground, and bows his head. Around them every one of the dead stops where it stands. | 4.0 |
| 2 | CU | 85 | Static, low, up at his bowed helm | Line B2. | 3.0 |
| 3 | LS | 28 | Static | The dead crumble where they stand, all together: bone, rust, dust on the wind. The Barrow Lord last. The way out stands open at the head of the stair. | 4.0 |
| 4 | ELS | 135 | Static, from the stair's head, looking down it, compressed | Far down the stair, below the last of the light, a man in a clerk's coat is standing on a step with his back to her, quite still, holding up a little lantern with violet glass in it. He does not turn. Hold. | 4.0 |
| 5 | to the reckoning | | | Into the reckoning; the door shuts behind her as the arena ends ("the Seventh Legion's dead let you out again"). | 1.0 |

## Lines

Conversation `cin_behind_the_door`, speaker `barrow_lord` (*casting:* a dry,
enormous whisper, no age, the Latin said like an order given a thousand times;
no reverb, as if right at her ear).

| VO id | When | Line | Subtitle for a reader (arcana or the lens) | For anyone else |
|---|---|---|---|---|
| `cin_behind_the_door.nondum` | Arrival | Nondum. | *Not yet.* | *(He speaks in a dead tongue: "Nondum.")* |
| `cin_behind_the_door.redi` | Kneel | Redi. | *Go back.* | *(Again, the dead tongue: "Redi.")* |

The bones' whisper at the door (faith) reuses the existing line from the bones
(`Verge.cs` `vaultbody`), recorded with the same dry voice.

## Performance

**The Barrow Lord.** Every movement is drill: two thousand years of the same
posture. The long look in the arrival is the only thing he does that is not
drill. The kneel is a salute, not a surrender: precise, one knee, sword point
down, head bowed to exactly the same depth an officer bows to a superior.

**The survivor.** *Door:* `brows_up` 0.25, gaze on the sigil, its violet in her
eyes. *Arrival:* `brows_angry` 0.3; on "Nondum" (if she reads it) `brows_sad`
0.2 flickers through. *Kneel:* `eyes_wide` 0.3, `mouth_open` 0.1; she does not
lower her weapon. *Shot 4:* gaze down the stair, held; `brows_sad` 0.3.

## Sound

- **Music.** The door: the `Mystery` mood's bell, struck as the sigil wakes,
  and the low pad. Arrival: `Boss` mood in on the raised sword. Kneel: music cut
  on the blow; silence when the dead stop (all the horde's sounds at once:
  nothing); the crumbling (a long, dry rush); then, from far down the stair, very
  faint, a single bell (the lamp motif), once.
- **Effects.** The wedge into stone (a perfect click); the sigil's hum against
  the teeth; the door sinking (stone on stone, deep); the dead's rattle; the
  kneel (armour); the dust on the wind.

## VFX

The sigil waking (an emissive sweep along seven arms); the door sinking; eye-lights
on the dead; the crumble (bones to dust, a particle burst on every body); the
violet point far down the stair.

## In, out, skip, subtitles

- **The door:** bars in on the interaction; out into the arena's start.
- **Arrival, kneel:** as C10.
- **Subtitles.** As in the table: translated only for a reader. Speaker "The
  Barrow Lord".

## What it needs

The door's sigil waking and the door sinking; a stair set at the arena's way
out; the horde told to stop and to crumble together; a kneel on one knee with a
sword (a salute pose); Jessop's figure on the stair (a person in a clerk's coat,
back turned, a lantern with violet glass), seen only from far away.
