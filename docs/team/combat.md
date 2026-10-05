# Combat: skills, enemies, encounters, bosses, balance

Status page for the combat lead.
- **Agent:** `a708da2c97bf85c95` (successor to `a1d4562f44c7f6feb`).
- **Branch:** `worktree-agent-a708da2c97bf85c95`.
- **Read first:**
  1. `docs/handoff/combat.md`: the predecessor's knowledge.
  2. `docs/design/STORY_BOSSES.md`: the current work. §8 says what is built and what is left.
  3. `docs/SKILLS_DESIGN.md` §16–17, with §16.10 on getting up.

## Current state (2026-10-04)

**Handed off:** `docs/handoff/combat.md` is the successor's brief.

**The machine is the owner's.** No Godot, GPU, Blender or sweeps. Code, `dotnet build` and `dotnet test` only; a few dozen headless nights at a time, at most.

**Story nights are built, with the Hollow by Night as the template.** The owner approved the design. STORY_BOSSES §8 has the detail.
- **The runtime:** `StoryNight`.
  - Three stages ended by goals, each with a crowd and an ember floor.
  - A checkpoint at each stage and at the boss.
  - Greymuzzle as a `StoryBoss`: the Pack's ring, the moon-howl's cold, fed fires, his age, and his end.
- **The harness:** `story`. `BossSense` and the `Pilot` read the stage's goal and the ring.
- **Tests:** all 653 green.
- **The owner's rise rule** (SKILLS_DESIGN §16.10):
  - One rise in Act 1's story fights; none after, unless she carries the one power.
  - That power is the art Not Yet (from Chid's *The Keeper's Office*) or the great blessing Cold, Then Not.
  - One rise a fight. A fall ends a map.
  - The Second Wind trait is gone.
- **First runs** (tier 1, small samples):
  - plain hands won 75%, deft 92%;
  - the boss took 2.5–3.5 minutes;
  - **the way in was 1.6 minutes against a target of 6–9**;
  - the way in was too dangerous (50–63% of runs under half health, against 20–35%).

## Next (in order)

1. **When the machine is free: tune the Hollow** (STORY_BOSSES §8.3):
   - give each stage more to do, not more health;
   - move the danger from the way in to the boss;
   - look at tiers 3 and 4;
   - check it in the game (§8.4 lists what to look at).
2. **The Roost, the Dig and the Vault**, in the Hollow's shape. Redcowl's spared end plays `.spared` then `.flit`.
3. **The run-ups re-measure:** `combat-wip-runups@e63e74fd`; the next step is in the handoff §4.1.
4. **The Kerchiefs at tier 3** (68% / 50%), and **the Lamplings** not separating careless from planned drafts.
5. **The rest of the bestiary:** ground hazards at half, the Ford-Warden echo, weight as a number, the Signs Warded, Mending and Leader, Echoes.

## Key decisions

- **A story night's yardstick is a table night's twelfth minute** (ember about 30, about 32 cards), not its twentieth. Measured: a table night kills 20,000 by minute 20. A twelve-minute night cannot feed the ember that, and should not try.
- **Each stage has a finite crowd, softened by the minute it stands for, and an ember floor at its end.** A quick stage is not a weaker night, and nothing is farmed.
- **The build is a journal of its verbs.** A checkpoint plays it again through the same verbs, so nothing new added to a verb is forgotten by a restore.
- **A story's outcome is never decided by the build by accident:** crates go by a prompt, Greymuzzle by a choice, posts by where she stands.
- **Arts are bound by the spaces open now.** A blink carried a bot over a shut gate.
- **Getting up is one rise a fight, for a price,** however many ways she carries it.
- **Inherited:**
  - from tier 3 the night tests the draft;
  - endings that are not deaths wait for the last floor;
  - maps use one ruler health (3.5× its body) on 0.65 floors.

## Notes for other areas

- **Experience (`ab406cf9ddd22b03b`):**
  - StoryNight calls your `StoryFall(risesLeft, rise, letGo)`; risesLeft is 1 at most, and 0 from Act 2.
  - The night measured about 5 minutes, not 12, because the way in is short. I'll lengthen it, but the 40% sums should wait for the tuned numbers.
  - `--stage N` starts a story night at a stage.
- **Story (`a54dc034ed29f2e02`):** the spare fields are in `StoryFights.Spec` (thanks), so Greymuzzle's choice is live where she promised. Still owed: Chid's node giving `keepers_office`.
- **Arena art (`a26767f7f9955cb56`):** build the Hollow's place to `HollowByNight.Ground` (`Play/Story/Hollow.cs`): spaces as capsules, the two gates, and every point. The walls stand invisible in the old arena until then. The deadfalls need wood and fire.
- **Skills VFX (`a63cd93fc73d5ed79`):** the look of Not Yet, a fed deadfall, the cold's band, and the pale-blue "His age" ring.
- **Cinematics:** the hooks tried are `c10_arrival`, `c10_end` and `c10_spared`, only where `CanCinematic` finds them. Name the real ids.
- **Crafting (`a7debf1459f14dfe7`):**
  - a story night now pays XP for its own minutes;
  - `keepers_office` is a value-0 tome, given, never sold;
  - maps: a fall ends the map, so the three-falls economy is gone.
