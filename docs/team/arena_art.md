# Arena art: how every arena looks, and reads

Status page for the arena art lead (agent `a52b851395b3ab3f4`, branch
`worktree-agent-a52b851395b3ab3f4`). Sheets and concepts in `docs/arena/`.

## The brief

Own every arena's look: ground, dressing, landmarks, light and air, the fight's
readability on it, and how each tells its place in the valley. The endgame has two
kinds, each with its own identity: the **ember scars** (the survivors arenas, a
night each, `ArenaRun`) and the **Wayfinder's atlas** (the permanent build maps,
"like PoE"; story: "the places the road forgets", in Ysolde's hand, never the four
scars by day).

## Current state (sheet `docs/arena/wip2.jpg`)

| Place | Grade | State |
|---|---|---|
| Barrow | ~3 | the road reads; the ring now a thin burning line; howe and gate still not seen on screen; cobble edges stair-step |
| Ruts | ~3 | unchanged this pass; a grey ball (the cauldron?) at the camp reads as a placeholder |
| Hollow | ~3.5 | warm leaf litter, moss cushions, the slurry stream (threads of sick light, mist), pale bank stones, dark crowns; den still dark and unread |
| Dig | ~3 | ochre clay and stone, rails with sleepers and bright tops, tubs, a timber headframe over a pit with fire at the bottom; rust drifts and spoil still read as flat blobs |

**The ring is tamed:** black char in plates and ash; one thin white-hot line just
past where she can stand; veins and coals; the curtain dark. Judged at full res.

**Concepts** (Krea 2, local): `docs/arena/concept_hollow_{0,1}.jpg`,
`concept_dig_0.jpg` are the targets. Barrow and ruts have none yet
(`concepts.py` has their prompts).

## Key decisions

- **A scar is its people's own ground** (story confirmed): never "a fen" for the Risen.
- **Landmarks at the edge only; cover inside under 2.2 m** (thin poles excepted;
  the headframe stands over the pit, at the edge): held by a test.
- **Ground values raised, colour kept** (Hollow, Dig): the old targets (all under
  0.1, sat ~0.5) made every place grey mud; now 0.08–0.1 with full hue, still well
  under the living. Readability comes from hue and value both.
- **The ring is a line, not a field:** only the line and its veins glow, drawn
  by true distance (`dl`) so its width never swells.
- **Moss is the shader's** (splat3 R: domes at two sizes); the slurry's light is
  splat3 G and its own stream shader; the slurry stays faint so it never reads as
  hurting ground (the Slurry Sow's trail does hurt).
- **Arena crowns dark** (KitLook `Shade`): trees frame the fight, never outshine it.

## Next

1. Hordes at minute 25 on all four (`after2.txt` in the scratchpad) and judge the
   living, the dead and her light over each ground.
2. Dig to 4–5: break up the rust drifts and spoil blobs (texture and edge), dry grass
   tufts, scattered stones and timber, light the headframe from below.
3. Hollow to 4–5: the den (fallen giant) on screen, roots that read, fewer flat moss
   islands, the dapple as moon pools.
4. Edge landmarks on screen: the barrow's howe and gate, the Roost's camp (replace
   the grey ball), the Dig's headframe (done).
5. Grass that reads from 30 m (lean blades with the wind, clumped; never stars).
6. Barrow and ruts concepts, then their passes.

## Notes for other areas

- **Skills / experience:** in the Dig the lamplings carry blown-out white-gold
  discs (some effect on them) that burn out on the new, brighter clay; worth a look.
- **Experience (ad1f5623590e09883):** the ground is brighter and warmer in the Hollow
  and the Dig; wolves read dark on the litter. Confirm with a horde run.
- **Performance:** new per arena: a third splat (1024²), moss voronoi only where moss
  lies, the stream and two mist sheets, rails (one multimesh + one mesh), a vent
  (48 particles), the headframe (two meshes), tubs.
- **Story:** the slurry is drawn "faintly glowing" yellow-green, as the clue text has it.
