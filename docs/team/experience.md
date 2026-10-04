# Experience: the game as a player lives it

Status page for the gameplay experience director (agent `ad1f5623590e09883`, branch
`worktree-agent-ad1f5623590e09883`; successor to `a33f58e68e89e3ccf`). The audit is
`docs/EXPERIENCE_AUDIT.md`; evidence frames are in `docs/experience/`; the predecessor's brief is
`docs/handoff/experience.md`.

## Current state (2026-10-04)

Merged the integration branch at `f1b822b`. Tests green (540).

**Seen at full resolution (1920×1080) since performance's merge, and judged:**
- **The opening:** three groups in sight by 6 s (`night_opens_in_sight.jpg`). Good.
- **The camera:** 22 m for the first five minutes (the crowd stays under 60), she reads by her
  red hair; it stands back to about 31 m with 300 alive at minute 25. Good.
- **The dead:** pale for about a second, then half value with a cool cast, gone in 8–18 s. They
  read under the living. Problems: every corpse lies in one pose (sent to animation); bones were
  chalk-white, the brightest thing on the field (fixed: old bone, laid flat, skulls face up).
- **The fall:** pillar, rings and slow motion read as the peak. Fixed: the boss's own flat death
  blast (14 m across) under it; the way out's prompt over her at the peak (now after 2.6 s); the
  title over the flash (now 0.8 s after).
- **A story night's end:** it ends on its beat, shows the result and goes back to the road. Fixed:
  the autopilot closed the result as a screen and stranded her on the empty field; a story night
  had a pointless way out (a bright filled disc) and promised its boss "comes again"; the field
  flashed between the result and the fade.
- **The hit flash:** now lives at the rim; struck risen no longer bloom into blobs.

**In progress:** the chest as a sequence (S-09). Built so far: `ChestItem`/`ChestOpened` (what came
out, ranks, icon), the 1/3/5 roll at 84/12/4% (mean 1.4, as before), `IZoneHost.Chest` (headless
hosts still announce), the chest model's hinged lid, the held clock (`WorldScene.Hold`) and its
sounds (`Sfx.ChestShake`, `ChestBurst`, `ChestLand`, `ChestTick`). Next: `ChestCeremony` in the game.

## Next steps, in order

1. **The chest ceremony:** world held (not a screen), the camera in on the chest, the lid thrown,
   a reel per thing landing on the D minor ladder, skippable, quicker from the third chest.
2. **The evolution ceremony** (S-10), the XP ladder (S-02), the level-up on major (S-04), the
   multi-kill swell (S-08), the dash buffer (S-05), rumble (S-14).
3. **The ember carpet:** merge stones past a cap; tiers 2–3 bloom to cream "popcorn"
   (`ember_popcorn.jpg`): give them a saturated ember look.
4. **Onboarding:** the prologue's character levels paid at dawn.
5. **The 40% measured**, then **the endgame maps' design** with combat and crafting.

## Decisions

- **The chest is staged in the world, not on a page:** the world held round her, the chest the
  stage, the things over it. The owner: full pages are often not the best choice.
- **A chest is worth 1.4 things on average, as before;** only its spread changes (the jackpot).
- **The fall is the only screen-filling moment;** the boss's kill adds light and a ring, no blast.
- **A story night needs no way out:** it lets her go by itself.

## Briefs sent (4 October)

- **Skills** (`a63cd93fc73d5ed79`): the pyre ground's rotating orange square
  (`pyre_square_over_her.jpg`); the Hallowed Ground's amber glow hides her all late night
  (`hallowed_ring_late.jpg`); hostile marks as opaque filled discs (`barrow_rise_disc.jpg`,
  `kerchief_lob_discs.jpg`).
- **Arena art** (`ab03c3c85571e5085`): the dead read well; the Ashen Fen's crypt hides her and the
  fight (`crypt_hides_her.jpg`).
- **Animation** (`a1e3002b800ee55ac`): two or three die clips per crowd rig.

## Tools (scratchpad `experience/`)

- `play.py NAME -- [game args]`: a run at 1920×1080, fixed 60 fps by default (`--real` for wall
  time), with a log. The GPU is shared: frame times there mean nothing.
- `sheet.py`, `tsheet.py` (named frames), `crop.py`, `keep.py` (frames to `docs/experience/`).
- The game: `--story` makes `--zone arena` a story night (20 minutes, over at the fall).
