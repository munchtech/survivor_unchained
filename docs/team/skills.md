# Skills: how every skill looks, sounds and feels

Status page for the skills lead (ad059388f00c19f9f, branch `worktree-agent-ad059388f00c19f9f`; took
over from a191ed81e2df462cf). Tools and sheets live in the session scratchpad's `vfx/` (see the
handoff).

## Current state (2026-10-05, handed off; see `docs/handoff/skills.md`)

Tests green (747). Everything below seen at 1920×1080 unless it says otherwise.

- **The main session's rulings, done:**
  - Two elites at most flash white at once, on top of the three ordinary bodies (`CrowdView`).
  - The Legendary's night foot is about 196 px of warm ground, from 328 (lamp 2.8 m reach, 1 m up;
    pool 0.52 of its width). By day the foot still reads.
- **The night won**: one ember-amber column with the ember riding up it (motes in the shaft), a
  warm flash (no longer white-gold over the whole field). The cream hoop round her was the way
  out's pulse (a holy-gold decal band): it is now a soft band of cold light that comes only after
  the fall has landed. *The band itself is not yet seen after the change (shot queued).*
- **A chest's column**: seen; a soft gold shaft, reads as light. Its core goes a little cream.
- **Moonbrand**: the lavender was a lilac sigil at her hand on every cast, smoke-soft flames and a
  stardust haze at each hit, and a half-metre lilac smear for a trail. Now: a silver crescent glint
  at the hand, the brand stamped silver on a dark bed with violet jets of moonfire, a thin trail.
  Seen near her and at range: violet-blue fire, no lavender puff. The crescent itself is small.
- **Firepot**: a pot of blasting ember, not a fireball: a yellow-hot crack, tongues of flame
  jetting out (each turned along its way on the screen), burning powder, dark clay sherds, char
  smoke, a small deep-orange heart. Seen.
- **Burn and poison ticks** no longer flash bodies white (they turned three bodies a frame into
  white cut-outs on burning ground) and no longer flinch them (`Enemy.LastDot`).
- **Combat's asks**:
  - *A fed deadfall*: flame stands the length of the dead tree (fire_wall cards pressed to a line),
    embers go up, it sinks and smokes in its last four seconds and goes out; it takes with a rush
    when fed. Its reach is its own light. Seen at full, guttering and out (`--lit 9`).
  - *His age*: the pale-blue ring was already there; the old wolf's breath now smokes in thick pale
    puffs with each pant (also Whitethroat's "She missed"). Seen.
- **Unions** (all nine swept): Frostfire Comet has its own art (`frostfire`: an ice heart and frost
  tail in the fire; a burst half flame, half frost, with ice standing round its rim; a burning
  ground in a rim of frost). Butcher's Wheel's cleavers turn in steel arcs with a blood wake (it was
  one red ring). Rotwood (`zone_rot`) is a thicket of rotten thorns in a blight stain. A slow from a
  ground that is not the cold no longer draws frost on the bodies (`Enemy.HeldUntil`). The
  Tempest's bolts and bursts are electric blue, not white balls, and every survivor's falling blow
  is marked by a faint gathering light, not a ring.
- **Frost ribbons**: their glints were lit square cells (pale squares on a wide ribbon); now soft points.
- **Sound per skill** (`Audio/Sfx.Skills.cs`): each skill's own voice as it leaves her, as it lands
  and a little on each hit (bowstring, cold chime, fuse, chain, clay crack, thunder, glass); strikes,
  chains and beams make sound now (they were silent). *Built; checked only as spectrograms of the
  game's own mix (`--wav`), not heard.* Eight skills taped: each has its own shape, none clips
  after the palm and pot were lowered (they hit 1.0). The owner or main session must listen.
- **Seen after the last fixes**: Gyrestorm's thin wind ring; Aegis Wheel's break as a shockwave;
  Thunderclap's burst blue. **Still wrong**: Rend and Mend and The Harrowing still read as hoops
  (their open sweeps are wide bright arcs); Moonfall was pink-white balls from the arcane school's
  burst under each moon (now skipped; not yet seen); Frostfire's frost ribbon drew pale squares
  even with round glints (removed; not yet seen).

## Next step (exact)

1. Shoot Moonfall, Frostfire Comet and the won night's foot and way-out band (`won5` was shot,
   not yet looked at) after the last fixes.
2. Evolutions (all swept, sheets in `vfx/v1/`): the reaving novas' hoops (Blades arcs: thinner and
   darker, or a scythe that is seen to travel), Skybreak's and Ford Ice's white bars, Sunlance's
   cream beam, Winter Ward's and Absolute Zero's rings, the Wild Hunt's green rings.
3. Dawn's Judgement's discs read as soft gold blobs; Barrow Host's knights as pale ghosts.
4. The arts; sound for the arts and the grounds.

## Judgements needed (the experience director is paused)

- **The struck flare's white**: three ordinary bodies (and two elites) still go wholly white for a
  frame or two. Over the pale dead they read as flat white cut-outs. A warmer, shaded flash would
  keep the hit without the cut-out. Keep white, or warm it?
- **Sound**: the skill voices want a listen before they are judged.

## Key decisions

- **Light upright on the screen**, gaussians never an edge, held below the tone curve's knee.
- **No hoops**: a band of light on the ground is soft both sides and only where it must be (the way
  out); a fire's reach is its own light, never a disc painted on the ground.
- **Measure, don't guess**: warm glow widths by R−B along a row (`vfx/warmth.py`).
- **A slow is not frost; a tick is not a blow**: the view is told which (`HeldUntil`, `LastDot`).
- **A union is its own thing**: never another skill's art borrowed whole.
- Inherited, still true: a crowd is told by its first few; nothing lights her but her own moments;
  danger keeps its language; a decal's emission ignores alpha.

## Notes for other areas

- **Combat**: the fed deadfall and "His age" breath are built (`BattleFx.Story.cs`); `--lit S` lights
  the deadfalls for S seconds only. Frostfire Comet's art is now `frostfire` and Rotwood's `zone_rot`
  (looks only). `Enemy.LastDot` and `Enemy.HeldUntil` are view-only fields.
- **UI design**: the way out's ground band (cold blue, after the fall) sits under your prompt.
- **Arena art**: the deadfalls' flames are drawn over your fires by BattleFx while fed.
- **Performance**: each fed deadfall is one 48-card mesh; the way out is one quad in loot's batch.
