# Handoff: combat (skills' mechanics, enemies, encounters, bosses, balance, the maps, the story's nights)

Written by agent `a708da2c97bf85c95` for its successor, past the 500k mark.
- **State:** everything is committed and pushed on `worktree-agent-a708da2c97bf85c95` (`aa68f38e` and this page), and merged into the integration branch `claude/vigilant-galileo-l6jqyx`.
- **Tests:** 661, all green.
- **Parked:** one side branch, `combat-wip-runups@e63e74fd` (section 4.3).
- **Predecessors:** `a1d4562f44c7f6feb`, `ac4ec5bbd2763a0df`, `a09c5a65f5a84319e`. What they knew that still matters is folded in below.

**The machine is the owner's** until the main session says otherwise:
- no Godot, GPU, Blender or balance sweeps;
- code, `dotnet build` (the game's project builds too: `godot/SurvivorUnchained.csproj`) and `dotnet test`;
- a few dozen headless nights at a time, at most.

---

## 1. The owner's words

- **The bar:** "AAA standard", "strive for excellent, above and beyond", "I don't want to polish, I want to create perfection", "do we have soul?" Make things of this world, not generic. Remake rather than polish. Check at full resolution, and don't stop to ask.
- **Story nights (4 October):** "story nights are what? arenas that happen because of the story? if were going to do that they should be much more specialized and fun - smaller arena - and they don't need endless - they have proper arpg end bosses right?"
- **Getting up:**
  - "GET UP TWICE IS TOO GENEROUS. get up once i guess is ok? but only in early game. as we move on you shouldn't get to rise and keep fighting unless you have a trait for it. thats a balancing nightmare"
  - "the trait can just be a skill/spell right - can get it in arenas or learn it for story etc"
- **The owner's decisions on story nights** (the top of `docs/design/STORY_NIGHTS_AND_TIME.md`):
  - losing a story fight wakes her in town a day on;
  - Redcowl gets "Spare him" or "Finish it" at his knee, like Greymuzzle;
  - 12-minute days;
  - time passes outside fights;
  - several fights a night by intent.
- **Endless:** "endless is truly endless - just keep ramping up till its impossible (or not if the users get better and better and finding ways to win haha)".
- **Encounters:** "periods of that are exciting, non stop can be a little weird"; "variety of minion types elites and mini bosses instead of all just the same models of wolves."
- **Structure:** "end game is two types of arenas - permanent and our normal arenas. permanent is our arpg build maps like poe and the normal arenas are for mindless survivors fun." "story should be 40% of the game early on."

## 2. The brief

You own:
- skills' mechanics;
- enemies, elites, minibosses and bosses;
- encounters and balance;
- the maps' mechanics;
- **the story's nights:**
  - the runtime;
  - each fight's stages and boss;
  - the checkpoints and the rise;
  - the bots that read them, and the `story` harness.

Others own:
- **The experience director:** the night's shape, staging (the fall card, the fade), the day's clock and the loss's wake in town.
- **Story:** the words.
- **Arena art:** the places' look.

## 3. Done (this agent)

### 3.1 Story nights (the owner approved the design; the Hollow is the template)

- **The design:** `docs/design/STORY_BOSSES.md`. Section 8 says what is built, what was measured and what is left. It covers all four fights.
  - **The Hollow by Night:** Greymuzzle.
  - **Raid on the Roost:** Redcowl, in his own fight, no longer the Red Hand's.
  - **The Dig Boils Over:** Grimtunnel.
  - **Behind the Sealed Door:** the Barrow Lord, at the head of the stair only.

  Each has three stages ended by goals and a boss of 3–4 minutes.
- **The runtime:** `Play/Zones/StoryNight.cs`.
  - The game makes a story night of any story fight that has a script (`StoryScripts.For`, in `Game.Make`). The other three still run as `ArenaRun` told quicker.
  - Stages end on their goals, never a clock. The story's sight comes between them, with six seconds of quiet.
  - Each stage has a finite crowd, softened by the table minute it stands for, and an ember floor at its end.
  - Ember pays ×2.5 (`EmberPace`).
  - A great blessing comes as the night opens and another at the boss's opening.
  - The boss arrives on its own ground. Victory calls `Arenas.Won(j, spec, spared)` before the end hook.
  - `--stage N` starts at a stage; 3 is the boss.
- **The fight's pages:**
  - `Play/Story/StoryPlace.cs`: spaces made of capsules, gates (each opening a space) and named points; the walls; and the spaces open now, which bound arts and spawns.
  - `Play/Story/StoryFight.cs`: the `StoryBeat` and `StoryFight` bases, `Deadfall`, `IStoryArena` and `StoryScripts`.
  - `Play/Story/Hollow.cs`: the place (`HollowByNight.Ground`) and its three stages: Old Blue's howl on his three rocks; the sick water's deadfalls with Greenbelly; Whitethroat's drive.
- **The boss:**
  - `Play/Bosses/StoryBoss.cs`: the contract, with floors 25/30/25, ceilings of 75 s, the soft enrage at 4:30 and the hard one at 6:00.
  - `Play/Bosses/Greymuzzle.cs`:
    - the Pack's ring: 20 scripted, untargetable wolves that shove, bow round fed fires and bite;
    - the old way: lunges, hamstring, and his age (a pant, taking ×1.25);
    - the moon: the guard before the den, the howl, the cold closing from the ring and his dead's lanes;
    - on his feet: shake, chains of three, and the ring breaking at 15%;
    - the end: lying down, then "Let him go" or "Finish it" where `OnSpare` is set.
- **The battle:**
  - `Sim/Checkpoint.cs`: a journal of the build's verbs (`Built`); `Snapshot` and `Restore` replay it through the same verbs. Also `ShovePlayer`, which buys no grace.
  - `Battle.CancelBlows`; `HurtByGround(..., named)` made public.
  - `Enemy.Scripted`: a creature whose mind is the zone's `BossTick`.
  - `ArenaBoss.SoftAt` and `HardAt` made virtual.
- **The rise** (`SKILLS_DESIGN.md` §16.10):
  - one rise a fight (`PlayerState.Rose`);
  - Act 1's story fights give one, and none from Act 2 (`chapter.done`);
  - the art **Not Yet** (`cold_then_not`, held in the art's place, from `keepers_office`, *The Keeper's Office*);
  - the blessing **Cold, Then Not** (`from_the_ashes`): rank 2 gets her up whole, rank 3 with her dash whole and a moment's grace, never twice;
  - the **Second Wind** trait is removed;
  - `MapRun.FallsAllowed = 1`: a fall ends a map.
- **The hands:**
  - `BossSense.Steer(..., aim)` reads the stage's goal, the cold (to a fed fire, or to light one) and the ring as a wall.
  - `Pilot.Steer(..., goal)`.
  - `NavField` over a box, for the place.
- **The harness:**
  - `story` (`balance/Harness/StorySim.cs`; `--fight --tiers --seeds --policies --bot plain,deft --act2 --choice spare|finish --out`) prints STORY_BOSSES §0.6's table.
  - `STORY_TRACE=KEY` traces one night: hits, announcements, position, the way, and leaving the place.
- **Tests:** `StoryNightTests` (19) and `CheckpointTests` (5), plus updates to `BlessingTests` and `MapTests`.
- **The game layer** (built, never seen): `Game.cs` and `Autopilot.cs` know `StoryNight` (the camera, saves, the clock booking, the autopilot's goal).
- **Pay:** `Arenas.XpFor` pays a scripted story night for its own minutes.

### 3.2 From before (still standing; the predecessor's, summarised)

- **Boss contract:** floors hold for every ending (`Spent`); the oaths on bosses; the bosses' TTK at the table is 80–88 s.
- **The tier-3 brief** (`ArenaRun.Asks`): from tier 3, a careless draft loses more often (85% planned against 62% careless at 32 seeds). Dusk applies to the oaths' bites.
- **The Kindling** at minute 15: an ember-core and the ruler's keeper.
- **Atlas maps:** `MapRun`, `Charts`, `Atlas`, the strongbox event; 9.8–11.9 minutes to clear at tiers 1–3. Now one fall.
- **Marks** (`Sim/Marks.cs`) for crafting; gold rates; the crossbow's aim.

## 4. In progress, and next

### 4.1 Tune the Hollow (first, when the machine is free)

**Measured** (tier 1, small samples):

| Hands, draft | Runs | Won | Night (min) | Way in (min) | Stages (s) | Boss (s) | Under half on the way in | Boss on its first life |
|---|---|---|---|---|---|---|---|---|
| deft, greedy | 12 | 92% | 4.8 | 1.6 | 34 / 28 / 19 | 154 | 33% | 92% |
| plain, greedy | 8 | 75% | 4.8 | 1.6 | 42 / 39 / 25 | 144 | 50% | 75% |
| plain, random | 8 | 75% | 5.5 | 1.7 | 44 / 33 / 43 | 209 | 63% | 75% |

At tier 3 (before his blows were softened to ×1.0), plain hands won 17–25%.

**Targets** (STORY_BOSSES §0.6):
- a night of 10–14 minutes;
- a way in of 6–9 minutes, no stage over 3;
- a boss of 3–4 minutes;
- 20–35% of runs under half on the way in;
- the boss winning on its first life 55–70% of the time;
- with plain hands, planned drafts winning 90% or more and careless ones 70–80%.

**In order:**
1. **The way in is a third of its target.** Give each stage more to do, not more health: more of Old Blue's rocks and howls, the deadfalls held while the reeds come, more drives.
2. **The danger is in the wrong place:** too much on the way in, too little at the boss. Soften the crowd's teeth a little, and give Greymuzzle one more true threat.
3. **Tiers 2–4.**
4. **Measure:** `cd godot/balance && dotnet build -c Release && dotnet run -c Release --no-build -- story --fight hollow --tiers 1,2,3 --seeds 8 --bot plain,deft --policies greedy,random --out out/story.jsonl`. 96 nights take about a minute.

### 4.2 Check in the game (none of it has been seen)

- **The place:** the walls stand invisible inside the old round Hollow arena until arena art builds the outline (they have it). The gates are only rows of posts.
- **The ring:** twenty wolves standing, facing in. Does it read as a wall, and does a shove read as a shove?
- **The deadfalls:** only a light coming on today. They need wood and fire (skills VFX or arena art).
- **The cold:** a band of violet ground closing. Is it readable over the ring and the lanes?
- **Greymuzzle:** panting (the pale-blue ring), lying down, the two prompts, his walk to the den.
- **The words:**
  - the stage lines between stages;
  - "You get up." and its fade (experience stages `StoryFall`);
  - the cinematic hooks tried are `c10_arrival`, `c10_end` and `c10_spared` (cinematics should name the real ids).
- **The camera:** 22 m on the way in and 27 m at the boss. Is the den floor whole in view?
- **Not Yet in the arts screen:** it has no active use, no facets, and the blessing's icon.
- **How to look:** `--story`, or Verge `night:hollow`, with `--stage 3 --auto` for the boss. Shots via the experience scratchpad's `play.py`.

### 4.3 Then

0. **Skills' proposal for the rise's beat (`a94ac6b67f1279213`, handed off; their look is on `worktree-agent-a94ac6b67f1279213@4577e2f5`):**
   - `Battle.HurtPlayer` now emits `Ev.Rise { X, Z, Radius, Grace, Delay, Ember, Rank }` before `RiseBurning`, and the radius is `RiseRadius(rank)`. No mechanics changed.
   - **Yours to decide:** "You go cold. Then the ember catches." wants a beat. Today every body within 8 m burns in the frame the cold begins, while the fire's front takes 0.3 s to run out.
     - Best: burn each body when the front reaches it (delay about 0.3·(1-(1-d/r)^(1/3)) s).
     - Simplest: `RiseBurning` about 0.15 s after the rise.
     - Either way, set `Ev.Rise.Delay` and the look stretches to match.
   - `--fall-at T` gives a killing blow at T, for pictures (with `+from_the_ashes` for the ember).
   - The skills successor holds our earlier asks: a fed deadfall, the cold's band, the "His age" ring.
0. **Animation's ask (`a03acf30b3e9bdd70`, small, code only):**
   - **After a slam lands** (the Slam cast ending in `Ai.Verbs`): keep the slammer planted about 0.65 s, with no movement and no new melee strike. Today the Heap strikes again about 0.3 s after its blow and Barn-Door walks off at once, which cuts the get-up clip (the blow lands at 1.0 s; it stands by 1.67 s). It is also a punish window after a heavy blow.
   - **After an aimed shot** (the Aim cast ending in `Shoot`): keep the shooter planted about 0.7 s before it strafes or backs off, for `kneel_shot`'s rise. This covers the levy crossbows, the Scorpion and the Levy Sergeant.
   - The view plays both on `e.AnimT`, so no new state is needed. Send them the numbers chosen; they fit the clips' tails to them.
   - When their `kerchief_crossbow` visual lands: point `levy_crossbow` and `mb_levy_sergeant` at it, and add it to the rigs list in `EncounterTests`. The Scorpion (`skeleton_rogue`) gets the kneel too.
0. **Cinematics' asks (`a79b6d8c81e14dc63`, small, code only; nothing changes in play until their timelines exist, since `CanCinematic` is false):**
   - **The ids** match StoryNight's `{cinematic}_{part}`: `c10_arrival` / `_end` / `_spared`; `c11_arrival` / `_end` / `_spared`, plus `c11_again` (his laugh on a rise, optional); `c12_arrival` / `_end`; `c13_door` (before the fight), `c13_arrival` / `_end`. `c13_end` is for when he is laid down and won't stay down, not a death.
   - **Marks:** pass them to `G.Cinematic`, as the Prologue does for C03: `boss` [x, z, heading] where he stands or lies, `her` [x, z, heading], and for C10 `den_mouth` [x, z]. Their cameras are offsets from these.
   - **The spared part plays at the choice:** call `c10_spared` in `Greymuzzle.Choose(true)`, not after the walk. The cinematic owns his getting up and his walk to the den; on its done callback, release him and call `Ended(spared: true)`. If `CanCinematic` is false, keep today's walk. Redcowl's spare works the same way.
1. **The Roost, the Dig and the Vault**, in the Hollow's shape: a `StoryFight` per fight, its place and stages, a `StoryBoss`, and `StoryScripts.For`.
   - Redcowl's spared end plays `.spared` then `.flit`.
   - Freeing the caravan's men runs `Verge.OpenCage`'s effects.
   - "Fire the crates" is a prompt, only while `be.crates` is unset or `redcowl`.
   - `bane.pole` is read by the Vault's standard.
2. **The run-ups re-measure:** `combat-wip-runups@e63e74fd`, not merged.
   - The target, while `pacing.Building`: 10–20% of runs under half health in each run-up, 3–5% under a quarter, and wins within two points.
   - Next: one forerunner pair per run-up at herald strength (×(4 + tier), damage ×1.2), and drop the champion-share lever.
   - Measure with `python tools/combat/stretches.py`.
3. **The Kerchiefs at tier 3** (68% planned / 50% careless; 18–41% under iron, blight and embers), and **the Lamplings** not separating careless from planned (87% / 81%).
4. **The rest of the bestiary:** ground hazards hurting the horde at half; the Ford-Warden echo; weight as a number; the Signs Warded, Mending and Leader; Echoes in the long night; maps above tier 3.

## 5. Decisions (why: STORY_BOSSES §0 and §8, SKILLS_DESIGN §16.10)

- **A story night's yardstick is a table night's twelfth minute** (ember about 30, about 32 cards), not its twentieth. Measured: a table night has killed about 1,000 by minute 3, 8,000–9,000 by minute 12 and 20,000 by minute 20. A twelve-minute night in a small place cannot feed that.
- **Each stage has a finite crowd at its minute's softening, plus an ember floor at its end.** Nothing is farmed, a quick stage is not a weaker night, and a rise replays the same stage.
- **The build is a journal of its verbs,** replayed by a restore. A field-by-field clone would miss whatever is added to a verb later.
- **A story's outcome is never decided by the build by accident:** crates by a prompt, Greymuzzle by a choice, posts by where she stands.
- **Living walls are never targets:** the ring, the guard, the Legion's front.
- **One rise a fight, for a price.** The price is her art (Not Yet) or a great pick (Cold, Then Not); in Act 1 the story's own rise counts. The trait went.
- **Arts and spawns are bound by the spaces open now.**
- **Story bosses are their own scripts;** the table's rulers are untouched.
- **Inherited:**
  - from tier 3 the night tests the draft;
  - a night is lost to the draft, not its first minutes;
  - endings that are not deaths wait for the last floor;
  - maps use one ruler health (3.5× its body) on 0.65 floors;
  - charges are directed;
  - a verb is shown before it spreads;
  - one rallying voice on the field.

## 6. Tried and failed, and why

- **The story night at a table night's minute-20 build:** the first runs met the boss with 10 cards. A short night can't feed that ember. Fixed by the crowds, the floors, and the minute-12 yardstick.
- **Stages of waves alone:** the stages ended in under a minute. The crowd made them a night. Even so, the way in is still short (section 4.1).
- **Walls as boxes alone:** a blink or a leap carried a bot over a shut gate, into the old arena, with its goal out of reach. Fixed with `InBounds` over the open spaces.
- **The ring's shove with a bite every time:** a bot was shoved ten times running, for 10 each, to death. Fixed: a bite at most every 2 s, and the guard shoves onto the den floor.
- **The drive's "hit" read from DamageTaken:** it counted anything that hurt her. Fixed: the lane's own shape and her hurt flash.
- **Greymuzzle lying down "Stunned":** a stunned creature's mind (and so its script) doesn't run, so the choice never resolved. He lies `Idle` now.
- **The bots' goal behind the crowd's urgency:** they never went to light a fire. The goal now comes before engaging, with `NavField` round the walls, a way point three metres on, and the ring read as a wall.
- **Inherited:** stronger tier-3 levers cost planned drafts too; Lampling tunnellers at 25/10 changed nothing; the core at the keeper's full health was rarely broken.

## 7. Gotchas

- **Shell:** many C# files are CRLF. Exact edits keep line endings with `tools/combat/sub.py` or a script that reads and writes raw text. The Edit tool works too.
- **The story night's ids:** the spec ids are `hollow_by_night`, `roost_raid`, `dig_boils` and `vault_opened`; `StoryFights.Spec` takes `hollow`, `roost` and so on. `StoryScripts.For` keys on the spec id.
- **`StoryLint`:** a fact the fights read must come off the seed list (`bane.fires` and `bane.pole` already have).
- **Restore drops the events the replay emits** (`EventStream.Since`). If a test checks events after a restore, drain them before it.
- **A story night's hostile count leaves out scripted creatures** (the ring). `Hostiles()` is what the stages see.
- **The harness:**
  - run `dotnet build -c Release` in `godot/balance` before `--no-build`;
  - `story` takes about a second a night;
  - `arena` 192 nights takes about 6 minutes, maps about 10.
  - Traces: `ARENA_TRACE=KEY@MIN`, `MAP_TRACE=1`, `STORY_TRACE=KEY`.
- **Seeds and peoples in `arena`:** the people goes by seed index. Use 16–32 seeds or `--people` before believing a people's number.
- **The worktree's `godot/assets`** must be a junction to `public/assets` before any picture. Then `--headless --import` (about 30 minutes); revert the `.import` noise.
- **Text goes through the story lead.**

## 8. Collaborators (the live roster is in `docs/team/README.md`)

- **Experience (`ab406cf9ddd22b03b`):**
  - `IZoneHost.StoryFall(risesLeft, rise, letGo)` is theirs to stage. StoryNight calls it with 1 in Act 1 and 0 after.
  - `StoryFights.cs` holds the specs.
  - `ArenaResult.WakesInTown` and `Journey.WakeAfterLoss`; the day clock.
  - Told: the yardstick is minute 12, and the measured night was about 5 minutes.
  - Their staging is on `worktree-agent-ab406cf9ddd22b03b@369b88e2` (`src/Game/GameFall.cs`): a darkened hold, "Get up" or "Let the night go", and a half-second fade. They changed one line in `StoryNight.Rise`: `G.Say(G.Journey.RiseLine())`, the counted rise line.
  - **Owed to them:** the Hollow's numbers again (the way in, under half on the way in, the boss's first life) once the stages are lengthened.
- **Story (`a54dc034ed29f2e02`):**
  - `OnSpare`, `EndSpared`, `SpareVerb`, `Spared` and `Arenas.Won(spared)`;
  - the words: WRITING_PASS §21 (the pulls, the sights, the voices) and the rise's names and texts;
  - `chapter.done` marks Act 2.
  - **Owed:** Chid's node giving `keepers_office`.
- **Arena art (`a26767f7f9955cb56`):** building the Hollow to `HollowByNight.Ground` (paused for the owner). They'll tell you before moving shapes.
- **Skills VFX** (`a94ac6b67f1279213` handed off; see `docs/handoff/skills.md`): the rise's look is built. A fed deadfall, the cold's band and the "His age" ring are on their successor's list.
- **Cinematics (`a79b6d8c81e14dc63`, new lead):** the scripts match the design (C10's prompts in play, C11's "Finish it" as the blow, C13's laying down). The hook ids and their two asks are in §4.3.
- **Crafting (`a7debf1459f14dfe7`):**
  - Marks;
  - gold;
  - `keepers_office` is a value-0 tome;
  - one fall a map;
  - story nights pay XP for their own minutes, and `Crafting.Night`'s minutes-past term is still on the 20-minute spec.

## 9. Files to read first

1. `docs/design/STORY_BOSSES.md`, all of it, §8 first; then `docs/design/STORY_NIGHTS_AND_TIME.md` (the owner's decisions at its top).
2. `docs/SKILLS_DESIGN.md` §16.1, §16.9, §16.10 and §17.8.
3. `godot/logic/Play/Zones/StoryNight.cs`, `godot/logic/Play/Story/*.cs` and `godot/logic/Play/Bosses/StoryBoss.cs` and `Greymuzzle.cs`.
4. `godot/logic/Sim/Checkpoint.cs`, and `BossSense.cs` (the story parts).
5. `godot/balance/Harness/StorySim.cs`, `NavField.cs` and `Pilot.cs`; `godot/balance/Program.cs` (`story`).
6. `godot/tests/StoryNightTests.cs` and `CheckpointTests.cs`.
7. For the table and the maps: `Play/Zones/ArenaRun.cs` and `MapRun.cs`, `Play/Bosses/ArenaBoss.cs` and `ArenaBosses.cs`, `docs/bosses/SURVIVORS_BOSSES.md` §0–4.
