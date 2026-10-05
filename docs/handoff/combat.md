# Handoff: combat (skills' mechanics, enemies, encounters, bosses, balance, the maps)

Written by agent `a1d4562f44c7f6feb` for its successor, past the 500k mark.
- **State:** everything is committed and pushed on `worktree-agent-a1d4562f44c7f6feb` and merged into the integration branch `claude/vigilant-galileo-l6jqyx`.
- **Tests:** green (600 on the integration branch).
- **Parked:** one piece of work, on the side branch `combat-wip-runups` (section 4.1).
- **Predecessors:** `ac4ec5bbd2763a0df` and `a09c5a65f5a84319e`. What they knew that still matters is folded in below.

Read these first, then the files in section 9:
- `docs/team/README.md`: the rules and the roster;
- this page;
- `docs/team/combat.md`: the one-page status;
- `docs/SKILLS_DESIGN.md` §16–17:
  - §16.1: bosses;
  - §16.3: the long night;
  - §16.4: the charge director;
  - §16.5: stretches, minibosses and Signs;
  - §16.6: story nights;
  - §16.7: corrections;
  - §16.8: open decisions;
  - §16.9: the third tier asks the draft;
  - §17: the maps, with §17.8 what was built.

---

## 1. The owner's words

- **The bar:** "AAA standard", "strive for excellent, above and beyond", "I don't want to polish, I want to create perfection", "do we have soul?" Make things of this world, not generic. Remake rather than polish. Check at full resolution, and don't stop to ask.
- **Endless:** "endless is truly endless - just keep ramping up till its impossible (or not if the users get better and better and finding ways to win haha)". A table night goes on after its win until a fall or the way out.
- **Encounters:**
  - "in our charge mechanic once quite a few overlapping constantly. periods of that are exciting, non stop can be a little weird."
  - "consider mechanics that ramp along with the level time and don't appear till certain mini bosses and minion types show up."
  - "variety of minion types elites and mini bosses instead of all just the same models of wolves."
- **Structure:**
  - "end game is two types of arenas - permanent and our normal arenas. permanent is our arpg build maps like poe and the normal arenas are for mindless survivors fun."
  - "story should be 40% of the game early on."
  - Story nights are 20 minutes; the Wayfinder's table nights are 30.
- **The three lengths, as given to the owner:**
  - **A story night (20 minutes):** a timer, then a goal. Survive, the foe comes at 20:00, and the night ends when it falls.
  - **A table night (30 minutes):** a timer, then a choice. The ruler comes at 30:00; win, then stay in the endless long night or leave.
  - **An atlas map (about 10 minutes):** a goal with no timer. Walk the way to the ruler and kill it; it ends at its fall or your third fall.
- **The machine is shared.** When the coordinator says the owner needs it: no Godot, GPU or sweeps. Light code and tests only.

## 2. The brief

You own:
- skills' mechanics;
- enemies, elites, minibosses and bosses;
- encounters;
- balance;
- the maps' mechanics (MapRun, charts, the atlas's hooks, and MapGen for maps).

The experience director owns:
- the night's shape: `ArenaPacing`, breathers, floods, the hush, which turn comes, `Building`;
- the victory beat;
- the maps' shape and loop;
- staging (chest ceremony, the fall).

What spawns and what it does is yours.

In order, from the coordinator and the experience director:
1. **The run-ups** (section 4.1). On hold until the coordinator lifts the GPU and sweep limit.
2. **The Kerchiefs and Lamplings spread at tier 3** (section 4.2).
3. **Then:**
   - ground hazards hurting the horde at half;
   - the Ford-Warden echo (an atlas pinnacle);
   - weight as a number;
   - the Signs Warded, Mending and Leader;
   - Echoes in the long night (`docs/bosses/SURVIVORS_BOSSES.md` §10).

## 3. Done (this agent)

All of these are on the integration branch.

- **Boss floors hold for every ending.** An ending that is not a death (the Barrow Lord laid down, Grimtunnel down his hole, Greymuzzle let go) waits for the last phase's floor (`ArenaBoss.Spent`). A late build used to lay the Barrow Lord down in about 35 s. A test drives an absurd build at all six rulers through the game's wiring: 60–77 s.
- **Oaths on bosses** (SURVIVORS_BOSSES §0.12), each said on the boss's card (`ArenaBoss.Sworn()`):
  - winter: its heavy blows chill;
  - embers: its marked blows leave fire;
  - blight: it leaves blight where it walks;
  - ruin: it bursts at each phase turn;
  - vigil: floors ×2/3, moves 1/5 quicker;
  - iron: `StaggerTaken` 2/3;
  - champions: a signed lieutenant;
  - swarm: its adds ×1.5.
- **The tier-3 brief** (§16.9): from tier 3, a careless draft loses noticeably more often. `ArenaRun.Asks`:
  - dusk lasts 5 minutes;
  - the crowd's easing is at 0.4 of its slope;
  - fodder blows grow to ×2 from minute 8 to 30;
  - champions, heralds and minibosses are ×1.25 from minute 6 (not the boss).

  Measured, deft bot, table oaths: planned 87% / careless 71% (8 seeds); 85% / 62% (32 seeds). Tiers 1–2 stay forgiving. The experience director accepted it.
- **Dusk for the oaths' bites** (§16.7): the blight's poison and cut and the winter's chill come in over the first 3 minutes (`ArenaRun.Dusk`). At tier 3 the blight alone had felled a fifth of its runs in minutes 1–5.
- **The Kindling at minute 15** (SURVIVORS_BOSSES §9):
  - At 14:30 an ember-core rises toward the arena's middle (`ember_core`, drawn by `EmberCoreView` and `shaders/ember_core.gdshader`).
  - Beside it stands the ruler's keeper, with one of its ruler's verbs: `lt_pack`, `lt_dead`, `lt_lamplings`, `lt_kerchiefs`.
  - The keeper has a fifth of the boss's health and a full chest; the core has half of that.
  - Broken within 60 s, the core adds a card to the great blessing (`Battle.GreatExtra`). The blessing is owed either way.
  - Broken by 54% of planned drafts and 30% of careless ones.
- **Peoples evened:**
  - footpads are 31 health and 9 damage a blow (from 36 and 10);
  - the Lamplings' champion is `lampling_ganger` (460 health): their heralds were a 20-health digger, down in 4 s;
  - the Pack-Mother, the Barrow Lord and the Red Hand are raised twice, to `41+6.8t`, `17+2.9t` and `29+4.7t`;
  - five slow minibosses are softened (the Decurion to 380, the Weed-Wife to 400, the Chucker to 300, the Lamplighter to 380, Firepot Nan to 300).
- **Boss TTK** (8 seeds, tiers 1–3): Pack 88, Barrow 84, Gutterwick 87, Red Hand 80 s. The contract asks 90–120 at par: greedy runs about 75–85 s, random about 95–110 s.
- **The long night's square is 0.004** (`ArenaRun.Hardening`): the median run past the half hour went 22 → 26 minutes. The dark's oaths and the crowd end it, not the square.
- **Gold** (crafting's probes, a Kerchief night now about 350–450): arena `FodderGold` 0.0015 and `ChampionGold` 0.07. Bosses and minibosses pay in full.
- **Marks** (`Sim/Marks.cs`, for crafting):
  - `CombatKit.Marks` (id → strength 0–1) and `CombatKit.SkillMods` (skill id → `WeaponMods`);
  - worn only in maps, by `Battle.Wear`;
  - SkillMods fold into a skill taken up later (in `AddWeapon`).
  - The first four: of the Ravine, of the Falling Star, of the Open Gate, of the Gyre. Each has a test in `MarkTests`.
- **The crossbow's aim** (for animation): `RangedSpec.Aim`, 0.55 s on the levy crossbows, the Scorpion and the Levy Sergeant.
  - The shooter kneels as `Casting` with `CastKind.Aim`, Anim Windup, `AnimT = 0`.
  - Its line is fixed (`LungeX/Z`, `AimReach`), so a step off is a dodge.
  - The deft hands read it.
- **Maps** (§17, §17.8):
  - `Play/Zones/MapRun.cs` on MapGen's winding way. It runs by day, with camera (62, 24).
  - Packs are set down within 46 m and rest until 14 m (the day's Wake and Leash). They charge in waves of two.
  - Magic packs (1 in 4) and rare packs (1 in 10); altar keepers are the people's minibosses.
  - The ruler runs its night script on floors ×0.65, with 3.5× its body's health; what it calls is softened.
  - The shape is the experience lead's: 3/4/5 clearings at tiers 1–2/3–5/6+ (`MapSpec.Clearings`; the rest are Bends). An altar is in each clearing but the first. The last way is empty, with the ruler's sign at its edge.
  - Packs: 0.8 of the clearings' spots and 0.62 of the ways'.
  - The event: the first lit altar asks the people's question three times over about 50 s, then gives a strongbox (3–5 gear and a chart chance), shown through `G.Chest` with `ChestItemKind.Gear`.
  - Three falls a map; each spills half of what was picked up there and wakes her at the last lit altar.
  - Charts (`Maps/Charts.cs`): tier, people, seed, rarity and mods. Prefixes are the table's oaths and the map's own; suffixes are new `MapRules` (ArmourMul, DashRecharge, RegenMul, DraughtMul). Each is a `wayfinder_chart` item with `ItemInstance.Chart`.
  - The atlas (`Maps.Atlas`): (people, tier) clears, points, and five biases as hooks (people's road, twice lit, keeper's due, ruler's hoard, marked men).
  - Game: `--zone map [--tier --people --mods --seed --at boss]` and `Game.EnterMap(chart)`. The autopilot reads a map's ruler.
  - Measured (96 maps, a day build at the map's level, gear rarity 2):
    - minutes to clear: 9.8 / 10.3 / 11.9 at tiers 1 / 2 / 3;
    - cleared: 100% / 96% / about 90%;
    - the ruler: 59–70 s;
    - a pack every 12–16 s.
- **Harness:**
  - `map` (MapSim, NavField: a flow field over walkable ground at the survivor's radius, player-only edges included);
  - `RunResult.CoreBroken`, reported;
  - Pilot's `onward` for maps;
  - the deft hands go to the ember-core and step off aimed lines.
- **Tools in `tools/combat/`:**
  - `stretches.py`: the run-ups table;
  - `policies.py`: won and falls by policy;
  - `sub.py`: exact edits that keep CRLF.
- **The map tests no longer use the wall clock.**

## 4. In progress, and next

### 4.1 The run-ups (parked: `combat-wip-runups@e63e74fd`, not merged)

**The brief** (the experience director's, in `docs/handoff/experience.md`), while `pacing.Building` (7.5–10, 17.5–20, 25–28.5):
- 10–20% of runs under half health in each run-up;
- 3–5% under a quarter;
- wins within two points of today's;
- the hush (28.5–30) stays calm.

Fodder melts at those minutes (a 0.03–0.05 s TTK), so the count cannot carry it.

**Measured** (192 nights, tiers 1–3, 8 seeds, table oaths, deft, cap 34). The figures are under half health in run-ups 7–10 / 17–20 / 25–28:

| Version | Under half | Won |
|---|---|---|
| Before (`out/fin2`) | 10 / 2 / 4% | 88% |
| Levers (pincer spikes, champions ×2 signed, ranged and aura kinds ×2) | 6 / 3 / 4% | 89% |
| With forerunners (two signed champions ×1.5 from either side, twice a run-up) | 8 / 1 / 5% | 85% |
| Forerunners at half a herald each | 9 / 2 / 8% | 84% |

**The next step:** one forerunner pair per run-up at herald strength (×(4 + tier), damage ×1.2), and drop the champion-share lever. Measure with `python tools/combat/stretches.py godot/balance/out/X.jsonl`. Merge only if wins hold within two points. The forerunners' shouts are placeholders for the story lead.

### 4.2 The peoples at tier 3

32 seeds, planned / careless:

| People | Planned | Careless |
|---|---|---|
| Pack | 96% | 59% |
| Dead | 87% | 59% |
| Kerchiefs | 68% | 50% |
| Lamplings | 87% | 81% |

- **The Kerchiefs** are still the hardest. Under iron, blight and embers they win 18–41%. The new ravine arena (`Maps/Arenas/Ruts.cs`, arena art) halved them before the footpad cut.
- **The Lamplings** don't separate careless from planned. Toughening the tunnellers (25 health, 10 a blow) moved nothing and was reverted. Look at what the Lamplings ask of a build (their burrowing keeps contact low).

### 4.3 Next after those

- Ground hazards hurting the horde at half (§16.8).
- The Ford-Warden echo and the story's foes as atlas pinnacles (§17.6).
- Weight as a number.
- The Signs Warded, Mending and Leader.
- Echoes in the long night.
- Maps above tier 3: creature levels run to 40 at tier 16 while the character stops at 30. Gear must carry them once item levels exist (crafting).

## 5. Decisions (why: in SKILLS_DESIGN §16–17)

- **From the third tier the night tests the draft; below it, choice is expression.** Stronger levers (champions ×1.5, easing at 0.3) cost the planned draft as much (71% / 56%).
- **A night is lost to the draft, not to its first minutes:** a longer dusk from tier 3, and the oaths' bites come in over dusk.
- **The Kindling makes the great blessing better, never worse:** the blessing is owed whatever happens; breaking the core adds a card.
- **Maps use one ruler health (3.5× its body)** rather than the night's per-ruler multipliers. Those were set against the ember's builds and Breaks: a day build met them unevenly (the Pack-Mother 173 s, the Barrow Lord 67 s).
- **Maps by day:** at dusk the way was black past the start's fire. The blight veins smoulder by day (`#3d6420`).
- **Maps thin MapGen's spots rather than changing the generator,** so nights and old pictures keep their ground. The shape comes from `MapSpec.Clearings` (0 is the old map).
- **The NavField sees the battle's own collision with player-only edges:** `Blocked` leaves those out, and the bots stuck on them.
- **Inherited and still standing:**
  - charges are directed, not timed;
  - a verb is shown before it spreads;
  - Signed champions are cloned defs keeping the kind's id;
  - one rallying voice on the field;
  - verb timers draw dice only when a creature has the verb;
  - the probe's yardstick is the day's rank and file;
  - one night clock;
  - bosses are gates with floors and Breaks.

## 6. Tried and failed, and why

- **Stronger tier-3 levers** (champions ×1.5, easing at 0.3): the gap didn't widen, and planned drafts lost too.
- **Lampling tunnellers at 25 / 10:** no change in the careless/planned split. Reverted.
- **The core at the keeper's full health:** broken by 17% planned / 6% careless. Halved: 54% / 30%.
- **The Kindling's core 11 m away:** off the picture. Now 8 m.
- **The core as a plain orb:** an overexposed cream disc. Now a shaded lump with fissures that open as it breaks.
- **The maps' ruler at a third of the night's multipliers:** about 100 s, and a Pack-Mother wall. At its full night blows she took a level-10 warden from full in 8 s; blows are now the champion's.
- **MapGen's full snake for every map:** 14 minutes with a pack every 8 s. Cut to 12 turns for three clearings, it ran 7 minutes; now 15 / 14 / 16 turns.
- **The map bot:**
  - following the ways' points cut corners into trees;
  - a flow field over the ground alone walked into props;
  - one with `Blocked` missed player-only edges and pinned the hands.
  
  The NavField fixed all three. A progress-based stuck check covers burrowed tunnellers the hands waited on.
- **Dusk for the oaths alone** didn't fix blight+vigil at tier 3; the longer dusk from tier 3 did.

## 7. Gotchas

- **Shell sandbox:** it refuses `cd X && git ...` into computed paths, `$(...)`, and heredocs aimed at other worktrees.
  - Write edit specs with the Write tool and run `python tools/combat/sub.py SPEC.py` (FILES = {path: [(old, new)]}).
  - It keeps CRLF and needs exact, unique matches.
- **CRLF files:** many C# files are CRLF. Python edits must normalise (`sub.py` does).
- **Committing part of a file:** use `git hash-object -w` on a copy plus `git update-index --cacheinfo` (used for the gold commits).
- **The harness:**
  - `cd godot/balance && dotnet build -c Release -o bin/maps`, then copy to `bin/probe2` for a long sweep, so a running sweep doesn't lock the build;
  - 192 nights take about 6 minutes; 96 maps about 10;
  - `ARENA_TRACE=KEY@MIN`, `MAP_TRACE=1` and `MAP_BLOWS=1` trace why a run fell.
- **Seeds and peoples in `arena`:** the people goes by seed index (`peoples[(s + w) % n]`) and the table oaths by seed. With 8 seeds the Kerchiefs at tier 3 always meet blight+vigil and deep+embers. Use 16–32 seeds or `--people` before believing a people's number.
- **The worktree's `godot/assets`** must be a junction to `public/assets`. Mine was a 16-byte file: the pictures came out black and the Pine model failed to load.
  - Fix: `cmd /c mklink /J`, then `git update-index --assume-unchanged godot/assets`.
  - Then `--headless --import` (about 30 minutes).
  - Revert the `.import` noise with `git checkout -- ':(glob)godot/**/*.import'`.
  - Delete untracked `.uid` files that block a merge.
- **Pictures:**
  - `python tools/combat/shots.py NAME PEOPLE --minute 14.45 --seconds 2.5 --every 3 --count 2` for the Kindling;
  - maps: Godot `--zone map --people dead --tier 1 [--at boss --auto] --shot NAME`.
  - The `--quick` character has one skill, so fights in pictures are not balance.
- **`ArenaRun.Minute`** is the night clock: 30 at the boss whatever `Spec.Minutes` is.
- **The enemy pool reuses slots:** track `(Id, Seed)`.
- **Text goes through the story lead.** Placeholders to hand over:
  - the Kindling's names and lines;
  - `lampling_ganger`;
  - the forerunners' shouts (WIP);
  - the chart mods' names;
  - the `wayfinder_chart` item text;
  - the map ruler's sign barks.

## 8. Collaborators (the live roster is in `docs/team/README.md`)

- **Experience director:** `ad1f5623590e09883` handed off. Their successor has:
  - the run-ups' targets;
  - staging the strongbox's Gear items and a smaller fall for maps (item 2 in `docs/handoff/experience.md`).
- **Crafting** (`a7debf1459f14dfe7`):
  - gold numbers agreed;
  - the Marks API in hand (they fill `Kit.Marks`/`SkillMods` from items);
  - the moonpetal draught agreed at 60%, drunk when 55% or more is missing;
  - maps pay gold at the day's rate (a Kerchief map about 500).
- **Animation** (`a435f4dd0ac80df75`):
  - the kneel and aim are built to their ask;
  - they key the slam to the cast timing (raise to 0.8 s, smash at 1.0) and add a `kerchief_crossbow` visual.
- **Skills VFX:** the ember-core could take sparks and heat haze (`EmberCoreView`).
- **Arena art:** the Kerchiefs' ravine (`Ruts.cs`) changed their difficulty a lot; tell them if you change it back.
- **Story:** the placeholders in section 7.

## 9. Files to read first

1. `docs/SKILLS_DESIGN.md` §16.1, §16.7–16.9, §17 (§17.8 for what was built).
2. `godot/logic/Play/Zones/ArenaRun.cs`:
   - `Asks`, `Dusk`, `Level`, `Harden`;
   - the Kindling (`Kindle`, `Kindling`, `Midnight`);
   - `Minibosses`;
   - the long night (`Hardening`).
3. `godot/logic/Play/Zones/MapRun.cs`, `godot/logic/Maps/Charts.cs` (Charts, Atlas), and `godot/logic/Maps/MapGen.cs` (MapSpec.Clearings, Bends).
4. `godot/logic/Play/Bosses/ArenaBoss.cs` (Spent, FloorScale, oaths) and `ArenaBosses.cs`.
5. `godot/logic/Sim/Charges.cs`, `Sim/Ai.cs` (Aim, Verbs, Run), and `Sim/Marks.cs`.
6. `godot/logic/Content/Enemies.cs` (the Kindling's creatures, minibosses) and `Content/Signs.cs`.
7. `godot/balance/Harness/ArenaSim.cs`, `MapSim.cs`, `NavField.cs`, `Pilot.cs`, `Report.cs`.
8. `godot/tests/BossTests.cs`, `ArenaTests.cs` (the Kindling), `MapTests.cs`, `MarkTests.cs`, `EncounterTests.cs` (the aim).
9. `docs/bosses/SURVIVORS_BOSSES.md` §0.12, §9, §10 (Echoes), and `docs/handoff/experience.md` (the run-ups, the maps' shape).
