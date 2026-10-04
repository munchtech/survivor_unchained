# C12 · The Dig Boils Over

**Grimtunnel, roused: arrival and retreat.** Priority 3 · Act 1, optional (the
Dig turned against her) · arrival 9 s, retreat 11 s · skippable

## What it does

At the half hour of the night fight at the Dig's edge (`dig_boils`), the ground
splits and Grimtunnel climbs up out of it, bigger than at the ford, and changed:
a cold blue light shows through the cracks of his hide where the Warden's heart
has been keeping him company in the dark. He does not die. He goes back down,
bleeding and delighted, shouting up the hole after her that he has told
downstairs about her, and it went quiet.

- **Grimtunnel wants** her to stop interrupting the work. **He believes**:
  downstairs is patient, downstairs will be grateful, and he talks to it. **He
  reveals**, as a believer shares good news, that he told it about her and it went
  quiet (paying C03's "You smell like downstairs").
- **Plants:** the heart's light in him (Act 3: he carries it to the bottom); the
  Morrow going quiet at her name (the fortune has it "turning over in its sleep";
  Act 3 answers why it listened).

## Trigger and facts

- **Arrival:** the boss spawn in `dig_boils`. **Retreat:** the boss's death in
  that arena (he is not killed: the death plays as a retreat).
- Reads: `dig.pump` (his first line), sex (nothing spoken changes).
- Sets nothing (the arena's `OnWin` sets `dig.broken` and the rest).

## Place, time, light

The arena (people `lamplings`, theme `wood`), staged from his spawn. Night; the
lamplings' head-lamps (warm orange points everywhere in the horde); his own
light cold blue through his hide.

## Arrival

| # | Shot | Lens | Camera | Framing and action | Dur. |
|---|---|---|---|---|---|
| 1 | LS | 24 | Static, low; a long shake (0.5) | The ground between her and the horde splits in a line; the lamplings scatter from it, squealing, lamps bobbing. `WorldRate` 0.3. | 3.0 |
| 2 | MS | 35 | Static, low, up at him | Grimtunnel hauls himself up out of the crack, scale 2.1: blue light in the seams of his hide, his head-lamp burning. Line G4. | 4.0 |
| 3 | MCU | 50 | Handheld (0.4) | He spreads his arms like a man welcoming guests. Title: **GRIMTUNNEL** / *Ever So Grateful* (his own words at the ford, C03; Act 3 pays it: "Why isn't it grateful?"). Play. | 2.0 |

## Retreat

| # | Shot | Lens | Camera | Framing and action | Dur. |
|---|---|---|---|---|---|
| 1 | MS | 35 | Static; `WorldRate` 0.25 on the blow | The blow; he reels, bleeding light as much as blood, and tumbles backward into the crack he came out of, clutching the edge. | 3.5 |
| 2 | MS | 35 | Static, at the crack's lip, down at him | Hanging by his claws, grinning up at her, the blue in his seams and his head-lamp lighting the rock round him. Line G5. (A medium shot: he has no face rig; the line is in the whole body, swinging from the claws.) | 4.0 |
| 3 | LS | 24 | Static, down the crack | He lets go and drops into the dark, still laughing; his head-lamp goes down and down, a spark, and the blue with it, then nothing. The crack grinds shut. | 3.5 |

## Lines

Conversation `cin_dig_boils_over`, speaker `grimtunnel` (*casting:* Snib's
family, bigger and lower, a cackle, a cave reverb).

| VO id | When | Line | Note |
|---|---|---|---|
| `cin_dig_boils_over.pump#0` (pump broken, blown or moved) | Arrival | Surface-m— ...You broke my PUMP. ...Doesn't matter. Downstairs doesn't mind. Downstairs is PATIENT. | He starts the old insult and can't finish it (C03: she smells of downstairs); outrage, then calm: a believer remembering his faith. |
| `cin_dig_boils_over.pump#1` | Arrival | Surface-m— ...Killing my lads, are we? ...Doesn't matter. Downstairs doesn't mind. Downstairs is PATIENT. | |
| `cin_dig_boils_over.quiet` | Retreat | I told it about you! It went ever so QUIET! | Delighted, as if he has a present for her; homely ("ever so", as in C03). Shouted up the hole as he falls. |

## Performance

**Grimtunnel.** Toad-still, then quick. He is not angry for long about
anything: the heart is with him, downstairs is patient, and everything is going
to be wonderful. The retreat is not a defeat to him: he is going home. "Ever so
QUIET" is said with awe, as a churchgoer tells you the bishop knew his name.

**The survivor.** *Arrival:* `brows_angry` 0.35, `squint` 0.2 at the blue. *On
G5:* `brows_angry` eases, `brows_sad` 0.2; she looks down the crack after him
for a beat after it has shut.

## Sound

- **Music.** Arrival: the horde music cut by the ground's split; the `Boss` mood
  in on his arms spreading. Retreat: music cut; his cackle falling away down a
  well; the crack grinding shut; silence; the lamplings' squeals scattering.
- **Effects.** Rock splitting; earth; his claws; the cold hum of the heart's light
  in him (the same hum as the heart in C03, deeper); the fall.

## VFX

The crack (a ground decal with depth: a dark, smoking split); blue light in the
seams of his hide (an emissive mask on the Grimtunnel look); lamplings' head-lamps;
his lamp and the blue going down into the dark.

## In, out, skip, subtitles

As C10. Subtitles under "Grimtunnel".

## What it needs

A ground split that opens and closes (decal and a collider gap); Grimtunnel
climbing up out of it and dropping back (the burrow style is close); an emissive
seam mask on his skin; hanging by the claws (a held pose).
