# Handoff: skills look and feel

For the next skills lead. Read in this order:

1. `docs/team/README.md` (the bar, how we work, heavy work takes turns).
2. `docs/team/RESUME.md`.
3. This page.
4. `docs/team/skills.md` (status, what is seen and what is not, the judgements waiting).

Branch: `worktree-agent-ad059388f00c19f9f` (pushed). Merge `origin/claude/vigilant-galileo-l6jqyx`
into your own worktree, then this branch if the main session hasn't merged it yet.

## The owner's words

- "we are striving for perfection". "AAA standard". "I don't want to polish, I want to create
  perfection." "Do we have soul?" Never settle: remake rather than skip.
- "leveling up all our skills ... leverage our gpu as always to create amazing effects and be
  careful of crop/squaring issues". Judge at full resolution, in a packed crowd.
- On loot (relayed): the old beams were "solid pastel tubes"; the Legendary's "a huge solid cream
  bar slanting across the screen". Lights must read as light, not geometry.

## The brief

You own how every skill looks, sounds and feels in play: arts, auto-attacks, evolutions, unions,
blessings, her rise, the enemy's verbs, loot's light (LOOT_DESIGN.md §8), and the story's looks that
combat asks for. Each skill must read at a glance in a horde, keep its school's colour and shape,
land every hit, and grow with rank. Combat owns mechanics and numbers: propose, never make them.
Batch shots in one Godot turn and look once. Krea only through the `gpu` turn (the face lead uses
it a lot: queue fairly). Commit and push at milestones; open no PRs. `dotnet test` (in
`godot/tests`) before every commit. British spelling. Hand off at about 500k tokens.

## The main session's rulings (applied)

- Elites are capped too: two flash white at once on top of the three ordinary bodies.
- The Legendary's night foot glow about 180 px (measured 196, from 328).

## Done this round (all seen at 1920×1080 unless marked)

- **The night won** (`Ev.Victory` in `BattleFx.cs`): one ember-amber shaft with motes riding up it
  (`loot_beam.gdshader` kind 7's parameter is now its motes), a warm flash. Its foot fades over a
  breadth that goes with its width (it ended in a line across her feet). *The foot change is not
  yet seen.*
- **The way out** (`BattleFx.Story.cs`, `WayOut`): the cream hoop round her was ArenaRun's pulse,
  drawn as a holy-gold decal band. Now loot's batch draws a soft cold-blue band (kind 8) that comes
  2.4 s after the fall, as its prompt does. *The band is not yet seen at full strength (won5 queued).*
- **A chest's column**: seen, a soft gold shaft (fine; its core goes a little cream).
- **Moonbrand**: crescent glint at the hand (was a lilac sigil every cast); the brand silver on a
  dark bed with violet jets (moonfire tongues are now the pack's crisp `muzzle` jets, not its
  smoke-soft `flame`s); thinner trail; moonlight is silver-blue, moonfire deep violet.
- **Firepot** (`PotBurst`): crack, flame jets turned along their way on the screen
  (`Spin = atan2(-sx, sy)` from the camera's basis), burning powder, clay sherds, char smoke, a
  small heart.
- **Ticks are no blows** (`Enemy.LastDot`, view-only): no white flash, no flinch.
- **A slow is not frost** (`Enemy.HeldUntil`, view-only): a non-frost ground's hold draws no rime.
- **Fed deadfalls** (`BattleFx.Story.cs`): flame along the trunk (fire_wall cards pressed to a
  line), embers, guttering smoke in the last 4 s, a rush when fed. `--lit S` lights them S seconds.
- **"His age" / "She missed"**: the wolf's breath smokes in pale puffs with each pant.
- **Unions**: Frostfire Comet's own art `frostfire` (ice heart, frost tail, half-flame half-frost
  burst with ice round its rim, burning ground in a frost rim); Butcher's Wheel in steel arcs with a
  blood wake; Rotwood `zone_rot` (rotten thorns in a blight stain); the Tempest and every storm bolt
  electric blue (no white balls); a survivor's falling blow is marked by a faint gathering light,
  never a ring.
- **Frost ribbons** (`ribbon.gdshader` style 5): glints are soft points (lit cells were pale squares).
- **Sound per skill** (`Audio/Sfx.Skills.cs`, routed in `SoundBridge`): a voice per art on cast, on
  landing and on hit; strikes, chains and beams now sound. *Not heard: checked as spectrograms of
  the game's own mix only (`--wav PATH` records it; `vfx/spec.py` draws it).*
- Seen after the fixes: Gyrestorm's wind thinned; the shield's break a shockwave, not a ring;
  Thunderclap's burst blue. Eight skills taped: no clipping after the palm and pot were lowered.
- *Not yet seen*: Moonfall's arcane burst skipped (it was pink-white balls under each moon);
  Frostfire's frost ribbon removed (it drew pale squares even with round glints); the won night's
  softer shaft foot and the way out's band (`won5` was shot, not looked at).

## Next, in order

1. Shoot and look: Moonfall, Frostfire Comet, `won5` (the way out late in the won night).
2. The evolutions still wrong (all swept; sheets in `vfx/v1/`, triage sheets `vfx/v1a..d.png`,
   rechecks `vfx/u3a.png`, `u3b.png`):
   - hoops: Rend and Mend and The Harrowing (their opened sweeps still read as wide bright arcs:
     thinner and darker, or a scythe seen to travel), Winter Ward and Absolute Zero (`nova_frost`
     fronts), the Wild Hunt's green rings;
   - white bars: Skybreak (`arc_sky`, a wide white column), Ford Ice (`spear_ice`, a white bar),
     Sunlance (`beam_sun`, a thick cream beam);
   - Dawn's Judgement's discs read as soft gold blobs; Barrow Host's knights as pale ghosts.
3. The arts (Ev.Ability), then the arts' and the grounds' sound.
4. The judgements on the status page (the struck flare's white; a listen to the sounds).

## Decisions (why)

- **No hoops**: a ring on the ground with a bright edge reads as interface or geometry. A band of
  light is soft both sides, and only where a place must be marked (the way out). A fire's reach is
  its own light: a flat disc of firelight out to 5 m read as an orange circle painted on the ground.
- **Light upright on the screen, gaussians never an edge, held below the knee** (inherited).
- **A union is its own thing**: never another skill's art borrowed whole.
- **The view is told what a thing is** (`LastDot`, `HeldUntil`): never guess a tick from a blow.
- **Measure**: warm-glow widths by R−B along a row (`vfx/warmth.py`); sound by spectrogram.

## Failures, and why

- **Shader branch order**: kinds 8 and 9 fell into kind 7's `kind > 6.5` branch and drew as blue
  shafts. Bound each branch both ways.
- **The fire's room** (kind 9) read as a painted orange disc; removed.
- **The deadfall as an ellipse** of cards was a hoop of flame round a cold log; pressed to a line.
- **Two breath puffs** a pant were lost from 30 m up; three bigger, paler ones read.
- **Big sheets cost context**: a 4×8 sheet is ~5k tokens. Use `vfx/pick.py` (one frame a run,
  `max` picks the frame furthest from the run's mean) and `crops.py` at full resolution.

## Gotchas

- **Setting up a worktree** (as before): junction `godot/assets` → `public/assets` and
  `git update-index --assume-unchanged godot/assets`; robocopy `.godot` from a recent skills
  worktree (2 GB); copy `public/assets/**/*.import`; build and import twice (`vfx/imp.sh`).
  `vfx/repoint3.py` is the model for pointing the tools at a new worktree.
- **The worktree guard** refuses `cd X && git ...` chains and Python heredocs that write files.
  Write `.py` files with the Write tool and run them; `vfx/ed.py` does exact replacements and keeps
  each file's line endings (most files are CRLF in the worktree).
- **Shots**: `--on boss` adds frames at each boss move (`NAME_<label>_N`), `--won` the fall
  (`NAME_fall_N`); `--wav PATH` tapes the mix (works with `--shot`).
- Godot picks up an edited `.gdshader` at its next launch, without an import.

## Collaborators

- **Main session**: merges; rules on judgements.
- **Combat** (`a427a874da78cba8b`): the fed deadfall, "His age"; Rotwood's and Frostfire's art keys.
- **UI design** (`aa1f430bd64b8d1ce`): the way out's band sits under their prompt.
- **Animation** (`aa15f092820132274`): `CrowdView` (the flare caps, `LastDot`, `HeldUntil` are in it).
- **Arena art** (`aba487928a1515c93`): the deadfalls; BattleFx draws the fed flame over their fires.
- **Performance** (`a0eb8c612c94d4aa5`): costs on the status page.

## Files to read first

1. `docs/team/skills.md`
2. `godot/src/Fx/BattleFx.Story.cs`, `BattleFx.Loot.cs`, `shaders/loot_beam.gdshader`
3. `godot/src/Fx/BattleFx.Skills.cs` (flights, hits, `PotBurst`, `FrostfireBurst`, grounds)
4. `godot/src/Audio/Sfx.Skills.cs`, `SoundBridge.cs`
5. `godot/src/Actors/CrowdView.cs` (flare caps)
