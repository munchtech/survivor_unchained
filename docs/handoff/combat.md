# Handoff: combat (skills' mechanics, enemies, encounters, bosses, balance, the maps, the story's nights)

Written by agent `afe45df4957917614` for its successor, past the 500k mark.
- **State:** everything is committed and pushed on `worktree-agent-afe45df4957917614` (at `94e1bf59` and the one commit after it, this note), merged with the integration branch `claude/vigilant-galileo-l6jqyx` at `63a42e5b`.
- **Tests:** 681, all green.
- **Predecessors:** `a708da2c97bf85c95`, `a1d4562f44c7f6feb`, `ac4ec5bbd2763a0df`, `a09c5a65f5a84319e`. What they knew that still matters is folded in below.
- **The machine:** the GPU is shared again. Heavy work takes turns: `python C:/Users/munch/Desktop/survivorsunchained/tools/turn.py take godot "combat: <job>"` before a Godot run (exit 1: busy, do light work, try again), `give godot "<same>"` after. `take gpu` for ComfyUI or big Blender jobs. `dotnet test` needs no turn. The balance harness needs none either (it is CPU; mind `--par`, 12 is kind).

---

## 1. The owner's words

- **The bar:** "AAA standard", "strive for excellent, above and beyond", "I don't want to polish, I want to create perfection", "do we have soul?", "we are striving for perfection". Ask whether it is the best version of this in any game; root design in how the best games solve it, then make it ours. Check at full resolution. Don't stop to ask.
- **Story nights (4 October):** "story nights are what? arenas that happen because of the story? if were going to do that they should be much more specialized and fun - smaller arena - and they don't need endless - they have proper arpg end bosses right?"
- **Getting up:** "GET UP TWICE IS TOO GENEROUS. get up once i guess is ok? but only in early game. as we move on you shouldn't get to rise and keep fighting unless you have a trait for it. thats a balancing nightmare"; "the trait can just be a skill/spell right - can get it in arenas or learn it for story etc".
- **The owner's decisions** (top of `docs/design/STORY_NIGHTS_AND_TIME.md`): losing a story fight wakes her at Chid's a day on; Redcowl gets "Spare him" / "Finish it" at his knee; 12-minute days; time passes outside fights; several fights a night by intent.
- **Rules given to this role:** one rise per story fight, in Act 1 only; after that none unless she carries Not Yet or Cold, Then Not. A fall ends an atlas map.
- **Endless:** "endless is truly endless - just keep ramping up till its impossible". **Encounters:** "variety of minion types elites and mini bosses". **Structure:** "story should be 40% of the game early on."

## 2. The brief

You own skills' mechanics; enemies, elites, minibosses and bosses; encounters and balance; the maps' mechanics; and the story's nights (the runtime, each fight's stages and boss, the checkpoints and the rise, the bots that read them, the `story` harness). Others own: the night's shape and staging, the day's clock and the loss's wake (the experience director); the words (story); the places' look (arena art).

The order given to me, and where it stands:
1. ~~Tune the Hollow by Night~~ (done, section 3.1).
2. ~~Look at tiers 2–4~~ (done: every tier is the same night).
3. **Check everything in the game at full resolution**, with the experience director and arena art. The experience director ran the Hollow on the game's autopilot at 1920×1080 and sent notes (acted on: the drive). They are handing off; their successor has the Hollow's judging as item one. Nothing of the Roost has been seen.
4. **Write the Roost, the Dig and the Vault the same way.** The Roost is built, tuned and tested (section 3.2). **The Dig and the Vault are next** (section 4.1).
5. Then the older items (section 4.3).

## 3. Done

### 3.1 The Hollow by Night, tuned (`Play/Story/Hollow.cs`, `Play/Bosses/Greymuzzle.cs`)

| Measure | Target | Measured (64 nights a row, tiers 1–4) |
|---|---|---|
| Night, planned + deft | 10–14 | 8.8–11.2 ("a tight 10 beats a padded 12": the experience director) |
| Way in | 6–9 | 5.0–5.9 planned, 5.7–7.2 careless |
| Boss | 3–4 min | 3.2–4.9 planned, 4.3–6.6 careless |
| Under half on the way in | 20–35% | plain 11–38%, deft 11–25%, naive ~22% |
| Won with the rise, plain | ≥90 / 70–80 | 86–88 / 80–89 |
| Boss on its first life, plain | 55–70% | 78–88% (bots don't learn between tries; to judge at the screen) |
| Cards at the boss | 32 ± 2 | 32 at every tier |

- **The stages have beats with their own pace, not health:**
  - the clough: Old Blue is shamed off a rock by four broken howls (or six howled), his health held at the rock's mark; a ring of yearlings, then a rush down the cut in five files, stand between rocks (he is out of reach behind them);
  - the water: the first light wakes the reeds, seven pulses on a 17 s cadence, Greenbelly with the fourth (her bite and trail thinned; her burst is the lesson), and the stage asks her to keep a fire fed;
  - the drive: Whitethroat guarded (×0.08) but for her pant (×2, 2.5 s); the Pack wheels at half; her yearlings ring the heroine at a quarter; **bounded by her seven drives** (then "spent", guard gone), and the first drive is a lesson (marked 1.7 s, said; her first miss and the first time the gap catches the heroine are told). The game's autopilot chased the gap for 7 minutes before this.
- **Greymuzzle:** stalks between moves (no brawl; a nip of ×0.3 if walked into), lunge every 4.5 s, the Pack's turn (three crossing lanes every 13 s), hamstring then lunge, the Moon's first howl unbreakable (the fires are the answer), chains of three on his feet (0.7 s marks, 2.6 m lanes). DamageMul 2.3, HealthMul 88 flat.

### 3.2 Raid on the Roost, built (`Play/Story/Roost.cs`, `Play/Story/Levy.cs`, `Play/Bosses/Redcowl.cs`)

- **The place:** `RaidOnTheRoost.Ground`, four spaces climbing north (the ruts, the cage yard, the camp's yard, his fire). Arena art has not seen it (their agent could not be resumed when I wrote; tell their successor).
- **The ruts:** pickets lit one after another up the road, each out of reach on the lip (Neutral, TakenMul 0) until three of his pincers (footpads off both banks either side of her) are broken; Firepot Nan with the third picket.
- **The cage yard:** a lock (`StandBy`, 10 s) gives to the one who stands by it, not while Barn-Door (leashed to the yard) stands within 4 m of it; the last frees the teamsters (`Verge.TeamstersFreed`, shared with the day's rescue). With the cages empty, Barn-Door alone.
- **The camp:** the levy (`Levy`: a locked line in step that wheels to follow her, its two end men targets, its front shoving), the Pike-Captain behind it (×0.15 taken through it), re-formed up to twice; the crates by their prompt only (12 m ring, 3 s, the line breaks, the captain to a quarter, `be.crates` = burned, `A.Mark("crates")` for the sight).
- **Redcowl:** the Host (stalk; the Greeting; the laugh, then the Hook, the axe sticks ×1.25; a torch if she keeps away; his lot out of the watchers), Forty-One Mouths (the rally, storm breaks it; the carts become walls; the cage of ten posts with one door, posts give to her standing by them from inside, he dashes to the door and Hooks down its lane; his levy once at half), Mind Where You Swing (chains: Hook, Greeting, charge; the bairns at 15%), his knee ("Spare him" / "Finish it", ids `let_go` / `finish`). All Forty-One: the watchers join and his blows grow 3% a second (it must end a weak build's fight). Rav's `once:redcowl` flag (the leg) lengthens the stuck axe.
- **Measured** (32 a row, tiers 1–4): won 81–97% (one 66% outlier, tier 4 careless deft), way in 3.3–6.2 min, under half on the way in 28–59% (above target: Barn-Door's slam and the levy), boss 2.3–5.6 min. Shorter than the Hollow; not padded.
- **Tests:** `RoostTests` (15): the place holds her, walkable, the picket on the lip, the locks and Barn-Door, the teamsters freed, the levy's locked middle, the crates by prompt only, the floors, spare or finish, the cage's post, the way back shut.

### 3.3 For every story night (`Play/Zones/StoryNight.cs`, `Play/Story/StoryFight.cs`, `StoryPlace.cs`)

- **Every tier is the same night:** `TierEase` (creature health ÷ 1 + 0.3 a tier), `TierTeeth` (bite ÷ 1 + 0.2 a tier), named foes ×2.2 flat (not grown by tier), boss HealthMul flat, ember per kill ÷ the tier's level XP scale, a dusk on stage 1 (a level a tier above the first). The way in's rank and file bite at `CrowdTeeth` 0.75.
- **The old round arena's props inside an unbuilt place are cleared** (drawn and solid) until arena art sets `PlaceBuilt => true` on the fight.
- **The walls are a skin of posts** (`StoryPlace.Posts`: circles 0.8 m every half metre round the outline, a second rank behind), not boxes stepped down diagonals.
- **The boss opens when she is through his ground's gate** (same side as `BossStart`, 2.5 m clear), or after 20 s the ember takes her there; **the way back shuts behind her** with the fight's `ShutSight`.
- New slots: `BetweenSight(a, stage)` (sights that read the world), `Kicker`, `ShutSight`, `PlaceBuilt`; `IStoryArena` gained `FactOf`, `Apply`, `Test`, `Knows`, `Mark`/`Marked`, `After`, `Line(text, speaker)`, `Teeth`, `Foe(..., quiet)`. `StandBy` is "break it by standing at it" (locks, posts).

### 3.4 Fixed on the way (game-wide)

- **Burn Bright** (`glass_cannon`) named its numbers `syn:glass`, so each rank stacked them and a rise kept them (a quarter of her health at rank 3). Now its own; `CheckpointTests` holds every blessing to it. *Table nights' greedy numbers measured before this are too high.*
- **Cold, Then Not** caught every body in 8 m in one frame. Now a 0.35 s cold (`Battle.RiseCold`, sent as `Ev.Rise.Delay`), then each body catches as the fire's front reaches it (`Battle.RiseFront`, the look's own curve: 0.3 s, eased out). The skills lead (`abc6bbe020c7fe287`) suggested 0.15–0.2 s for the beat; I kept 0.35 to be judged at the screen.
- **Hit events carry a landed blow's label** (`Ev.PlayerHit.Label`), so the harness says which move hurt her.
- **The marks' floors raised** (crafting asked): Ravine 35→90%, Falling Star 2→5 s, Open Gate 30→90%.

### 3.5 The harness (`balance/Harness/StorySim.cs`, `Pilot.cs`, `NavField.cs`, `Program.cs`)

- `story --fight hollow,roost --tiers 1,2,3,4 --seeds 16 --bot plain,naive,deft --policies greedy,random --par 12 --out out/x.jsonl [--crates] [--choice spare|finish]`. About 2–3 minutes for 256 nights.
- **Hands:** plain, deft, and **naive** (plain hands that read a boss's marks but walk into the way in's, as the game's autopilot did).
- **Path-following** (`NavField.Path`, replans when pushed off or stalled 3 s); `Pilot.Clearest` slides along walls on a story night. The old slope-following flipped from side to side in a neck for minutes.
- `HurtBy` in the output: what hurt her, by part and source (with blow labels). `place --fight roost` draws a place in text.
- **Traces:** `STORY_TRACE=<key>` (every 5 s: stage, goal, bar, shut/open, the boss's HP/phase/state; PROBE colliders and NEAR creatures every 30 s); add `STORY_TICKS=<seconds>` for quarter-second lines over 8 s from there.
- My analysis scripts were in my scratchpad (`an.py`: falls and dips by stage; `hurt.py`: hurt by source; `lost.py`: losses with where the night stood). They are 20 lines each over the JSONL; rewrite them as you need.

## 4. In progress, and next

### 4.1 The Dig and the Vault (next, in this order)

Build each in the Roost's shape: `StoryFight` with `Ground` (draw it with `place`), three `StoryBeat`s with paced beats (a cadence, a gate, a bounded count: never more health alone), a `StoryBoss`, `StoryScripts.For`, `ShutSight`, tests like `RoostTests`, then measure tiers 1–4 with plain, naive and deft.
- **The words are ready:** `docs/WRITING_PASS.md` §23.2 (Dig) and §23.3 (Door), §23.4 (wild and end), §23.7 (shut sights: Dig "Behind you, the tub-way falls in.", Door "Behind you, a rank of the dead steps across the hall."). On `worktree-agent-a7ba8903f4c8261b1` (merged into integration by now, or merge it).
- **The Dig** (STORY_BOSSES §3): the edge (three windlasses, each shaft boils until broken: a `StandBy` or a part; the Wick-Mother), the tub-way (the Chucker at the brake-house; tubs down the rails as lanes that flatten lamplings too), the pump (the Perfect of Fuses and fuse-runners when `dig.pump` runs, the Lamplighter when it is stopped; `dig.pump` = blown with the win). Grimtunnel: start from the table's `Grimtunnel` in `ArenaBosses.cs` (lamps, Under, pits, moths) and add Snib's barrel (kicked by walking into it), the crack (phase 3 splits the ground), the heart's pulse, the lamp bane (`grimtunnels_lamp`: set it down by a prompt), and his end down the hole (he never dies; `DiesAtZero` false; `Ended(spared: false)` after the hang). Hard name "All Downstairs". Defs exist: `mb_wick_mother`, `mb_bombardier`, `mb_fuse_boss`, `mb_lamplighter`, `lampling`, `lampling_wick`, `lampling_fuse`, `lampling_sapper`, `grimtunnel_roused`.
- **The Vault** (STORY_BOSSES §4): the hall (the Decurion's shield line: `Levy` fits it), the Scorpion down the hall (cover stops his bolts), the three standards (the Signifer; `bane.pole` lets a broken standard be lifted). The Barrow Lord: Iungite lines, pilum lanes that stay as cover, Testudo with the standard, the front closing (a moving bound like Greymuzzle's ring), the lay-down circle (holy twice as fast), the hand at the gate. Never down the stair.

### 4.2 To see in the game

- The experience director's notes on the Hollow (from the autopilot at 1920×1080): the drive was the problem (fixed in 3.1); the water reads; "His age" reads; their own fixes landed (Greymuzzle no longer orange; ember stones as gems). Their successor judges the Hollow again; ask them for the Roost too.
- Not yet seen by anyone: the Roost; the levy's front and its wheel; the cage of posts and its door; the shut gates' posts (they are colliders, drawn only as telegraphs where marked); Not Yet in the arts screen; the deadfalls' wood and fire (skills VFX).
- How to look: `--night hollow` (or `roost`), with `--stage N` (3 is the boss) and `--auto`; `--fall-at T` (with `+from_the_ashes`) for the rise. My worktree has `godot/assets` as a junction to `public/assets` and an import cache copied from another worktree (`godot/.godot`); take a Godot turn first.

### 4.3 Queued (carried from before; none started)

1. **Animation's ask (`a03acf30b3e9bdd70`, code only):** after a slam lands (the Slam cast in `Ai.Verbs`), keep the slammer planted ~0.65 s (no move, no new strike): Barn-Door walks off at once and cuts the get-up clip. After an aimed shot (the Aim cast ending in `Shoot`), keep the shooter planted ~0.7 s (levy crossbows, the Scorpion, the Levy Sergeant). The view plays both on `e.AnimT`. Send them the numbers. When `kerchief_crossbow` lands, point `levy_crossbow` and `mb_levy_sergeant` at it and add it to `EncounterTests`' rigs list.
2. **Cinematics' asks (`a79b6d8c81e14dc63`):** the ids are `{cinematic}_{part}` (`c10_arrival/_end/_spared`; `c11_arrival/_end/_spared`, `c11_again`; `c12_arrival/_end`; `c13_door`, `c13_arrival/_end`). Pass marks to `G.Cinematic` (`boss`, `her`, and for C10 `den_mouth`). The spared part should play at the choice (in `Greymuzzle.Choose(true)` and Redcowl's), the cinematic owning the walk, releasing him on its done callback; keep today's walk when `CanCinematic` is false.
3. **The run-ups re-measure** (`combat-wip-runups@e63e74fd`, not merged): target while `pacing.Building` 10–20% of runs under half in each run-up, 3–5% under a quarter; next, one forerunner pair per run-up at herald strength and drop the champion-share lever; `python tools/combat/stretches.py`.
4. **The Kerchiefs at tier 3** (68% planned / 50% careless) and **the Lamplings** not separating careless from planned (87% / 81%). Re-measure first: Burn Bright's fix moves greedy drafts.
5. **The bestiary:** ground hazards hurting the horde at half; the Ford-Warden echo; weight as a number; the Signs Warded, Mending and Leader; Echoes in the long night; maps above tier 3.
6. **Crafting (`af01b0d61ef656dd4`):** their `Marks.Gyre` → `"of_the_wheel"`, `MapRun.OnLoot`'s `Crafting.RulerMark`, `Chart.Pinned` and `Journey.GiveChart`'s heat are on their branch; keep them when they reach integration.

## 5. Decisions (why: STORY_BOSSES §0 and §8, SKILLS_DESIGN §16.10)

- **No padding.** A stage's length comes from beats with their own pace (a voice, a cadence, a bounded count of drives or whistles), never health alone: a minute-6 build melts fodder, so health-only stages ended in half a minute and sponges are no fun.
- **A stage is bounded:** hands that never learn its lesson are hurt, not held (the drive's seven drives; Old Blue's six howls).
- **A story night is the same fight at every tier.** Its tier is the game's guess at her strength; the table's tier-3 "asks the draft" does not apply.
- **A boss's teeth are in its marked moves.** Between moves it stalks; contact is a nip. Two thirds of what hurt her had been a brawl she could not read.
- **The boss comes on his ground, and the way back shuts behind her.** A fight that drifted back down the way in never ended.
- **The yardstick holds:** a table night's twelfth minute (32 cards) at the boss.
- **Inherited and holding:** each stage a finite crowd softened by its minute with an ember floor; the build a journal of its verbs (`Checkpoint`); a story's outcome never decided by the build by accident (crates by prompt, a choice at his side, locks and posts by where she stands); living walls never targets; one rise a fight; story bosses their own scripts; endings that are not deaths wait for the last floor.

## 6. Tried and failed, and why

- **Stages of more waves:** the bot's AoE clears a pulse of fodder in seconds; the cadence (the pulse comes on its own time) is what lengthened them.
- **Damage reduction on named foes alone:** a ×0.15 guard still let a stun-lock keep Whitethroat open (her pant's clock ran in her mind, which a stun stops). The pant's clock and guard now live in the stage's tick.
- **The boss's contact as his threat:** the bots took it as attrition, and a fall at the boss was decided by the build. Moving his teeth into marked moves made the danger readable.
- **The NavField's slope alone:** it flipped from one side of her to the other at a neck. Fixed with a planned path.
- **Shutting the gate when "on the boss's ground":** the gate's neck belongs to the boss's space, so she could be on the near side; the posts dropped on her and put her out. Now "through the gate" means the same side as the boss's start, clear of it.
- **A hard enrage that doesn't end it:** "the levy every 15 s" left a weak, sturdy build fighting Redcowl for 25 minutes. Now his blows grow.

## 7. Gotchas

- **The worktree-isolation guard** refuses Bash commands that `cd` somewhere and then run anything it can't parse (heredocs, variables). Write helper scripts with the Write tool and run them with absolute paths; my `sub.py` (exact substitutions, keeping line endings) was in the scratchpad and is 20 lines.
- **Story night ids:** spec ids `hollow_by_night`, `roost_raid`, `dig_boils`, `vault_opened`; `StoryFights.Spec` and the harness take `hollow`, `roost`, `dig`, `vault`.
- **`StandBy` and gates:** a gate's posts reach 2 m past its ends; keep points and goals out of that line.
- **The harness:** `dotnet build -c Release` in `godot/balance` before `--no-build`. Its numbers are noisy at 32 runs (±8%); use 64 before deciding.
- **Restore drops the replay's events** (`EventStream.Since`); a test that checks events after a restore drains first.
- **A story night's hostile count leaves out scripted creatures** (the ring, the levy's locked men, the watchers).
- **Text goes through the story lead.** They answer within minutes; send slots, not prose.

## 8. Collaborators (live roster in `docs/team/README.md`)

- **Experience (`ab406cf9ddd22b03b`, handing off):** owns the night's shape and staging; agreed "no padding"; judging the Hollow at the screen.
- **Story (`a7ba8903f4c8261b1`):** wrote every word in both fights; §23.2–23.7 hold the Dig's and the Door's.
- **Arena art (`a26767f7f9955cb56`):** building the Hollow's place; not reachable when I wrote. Tell them: the Roost's outline, `PlaceBuilt`, the post walls.
- **Skills (`abc6bbe020c7fe287`):** the rise's look runs on `Ev.Rise.Delay` and the same front curve; the beat (0.35 s) is to judge together.
- **Crafting (`af01b0d61ef656dd4`):** marks (section 4.3.6).
- **Animation (`a03acf30b3e9bdd70`)**, **cinematics (`a79b6d8c81e14dc63`):** section 4.3.

## 9. Files to read first

1. `docs/team/combat.md` (one page), then `docs/design/STORY_BOSSES.md` §0 and §8, then §3–4 (the Dig and the Vault).
2. `godot/logic/Play/Zones/StoryNight.cs`; `godot/logic/Play/Story/StoryFight.cs`, `StoryPlace.cs`, `Levy.cs`, `Hollow.cs`, `Roost.cs`.
3. `godot/logic/Play/Bosses/StoryBoss.cs`, `Greymuzzle.cs`, `Redcowl.cs`, `BossSense.cs`; the table's `Grimtunnel` and `BarrowLord` in `ArenaBosses.cs`.
4. `godot/balance/Harness/StorySim.cs`, `Pilot.cs`, `NavField.cs`; `godot/balance/Program.cs` (`story`, `place`).
5. `godot/tests/StoryNightTests.cs`, `RoostTests.cs`, `CheckpointTests.cs`.
6. `docs/WRITING_PASS.md` §23.
