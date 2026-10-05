# Combat: skills, enemies, encounters, bosses, balance

Status page for the combat lead.
- **Agent:** `a708da2c97bf85c95` (successor to `a1d4562f44c7f6feb`).
- **Branch:** `worktree-agent-a708da2c97bf85c95`.
- **Read first:** `docs/handoff/combat.md` (the predecessor's knowledge), `docs/design/STORY_BOSSES.md` (the current work), then `docs/SKILLS_DESIGN.md` §16–17.

## Current state (2026-10-04)

**The machine is the owner's.** No Godot, GPU, Blender or balance sweeps until the main session says so. Design, code, `dotnet build` and `dotnet test` only.

**Story nights redesigned, awaiting the owner's approval.** The owner: story nights "should be much more specialized and fun - smaller arena - and they don't need endless - they have proper arpg end bosses". `docs/design/STORY_BOSSES.md` is the combat half of the experience director's `docs/design/STORY_NIGHTS_AND_TIME.md`.
- **Shape:** each fight is 10–14 min (12 at par): a way in of three beats ended by goals, never by a clock, then a 3–4 min boss.
- **Ember and levels:** the ember is paid about ×2.5, and waves are finite, so she meets the boss with a table night's minute-20 build. Creature levels are fixed per beat.
- **The bosses:**
  - Greymuzzle: the Pack's ring as a living wall, fires she lights, the cold of the moon-howl, his age as his opening; let go by her choice.
  - Redcowl: his own fight, replacing the Red Hand's script; the laugh before the Hook, a cage whose door he waits at, the levy, the child's cry, Rav's leg as the bane.
  - Grimtunnel: lamps, Under, pits, Snib's barrel kicked into him, the heart splitting the ground.
  - The Barrow Lord: lines, the testudo's standard, the ranks closing in a front, laid down and then the hand at the gate.
- **Simulation:** what it needs is listed in §5 of the design: the `StoryNight` runtime, checkpoints, the `StoryBoss` contract, moving bounds, prompts in battle, BossSense's objectives, and the `story` harness.

**Agreed with experience** (their doc fitted at `worktree-agent-ab406cf9ddd22b03b@c59a9490`). **Build nothing until the owner approves.** The main session will say.

## Next (in order)

1. **On approval, story nights:** the runtime, the contract and the Hollow by Night as the template (STORY_BOSSES §5.6), with tests. Then measure with the `story` harness once the machine is free.
2. **When the machine is free:** the run-ups re-measure (`combat-wip-runups@e63e74fd`; the handoff's §4.1 has the exact next step).
3. **The Kerchiefs at tier 3** (68% planned / 50% careless) stay the hardest people.
4. **The Lamplings** don't separate careless from planned drafts (87% / 81%).
5. **The rest of the bestiary:** ground hazards hurting the horde at half, the Ford-Warden echo, weight as a number, the Signs Warded, Mending and Leader, Echoes.

## Key decisions

- **A story's outcome is never decided by the build by accident.** The crates go up by a prompt, Greymuzzle is let go by a choice, and a cage post breaks where she stands. Auto-fire would otherwise burn the Coyle crates for a fire build.
- **The way in teaches the boss.** Each beat's named foe previews one of its mechanics (Nightreign's gauntlet).
- **The waves are finite and creature levels are fixed per beat,** so the build at the boss is set by the content, a slow beat is not a harder one, and a rise replays the same beat.
- **Story bosses are their own scripts.** The table's rulers are unchanged.
- **Inherited:**
  - from tier 3 the night tests the draft;
  - a night is lost to the draft, not its first minutes;
  - endings that are not deaths wait for the last floor;
  - maps use one ruler health (3.5× its body) on 0.65 floors.

## Notes for other areas

- **Experience (`ab406cf9ddd22b03b`):** the Roost's third beat is the levy, with the crates as an optional shortcut, so a night without crates keeps its set piece. The checkpoint snapshot is ours.
- **Story (`a73ca9d35d0c487a9`):**
  - the beat list and the lines needed are in STORY_BOSSES §6;
  - two outcomes to confirm: freeing the caravan's men sets `caravan.survivors` to `rescued`, and Greymuzzle's let-go is her choice.
  - Placeholders from before also want your pass: the Kindling's names, `lampling_ganger`, the chart mods.
- **Arena art (`a26767f7f9955cb56`):** each place's spaces and sizes are in STORY_BOSSES §1–4. Walkable ground and colliders that change mid-fight are ours.
- **Animation (`a435f4dd0ac80df75`):** the new poses are listed in STORY_BOSSES §6.
- **Cinematics (`a3058a45eee41d695`, handed off):** C13's shot 1 following the laying down, and C10's two prompts, are recorded as pending approval (their handoff, Next 8). Each fight needs its arrival and end hooks (README 11a); the arrival hook knows a rise from a first arrival.
- **Crafting (`a7debf1459f14dfe7`):** a story night pays for its own length now; the shards formula's 20-minute assumption changes with it.
