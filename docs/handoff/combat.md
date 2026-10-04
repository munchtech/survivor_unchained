# Handoff: combat (skills, enemies, bosses, balance, encounters)

Written by agent `a09c5a65f5a84319e` for its successor, at a clean checkpoint at about 560k context. Everything is committed and pushed on `worktree-agent-a09c5a65f5a84319e`, tests green (475), merged with `origin/claude/vigilant-galileo-l6jqyx` as of 2026-10-04.

Read these, then the files in section 10:
- `docs/team/README.md` (the team's rules);
- this page;
- `docs/team/combat.md` (one-page status);
- `docs/SKILLS_DESIGN.md` section 16 (enemies, bosses, the long night, decisions).

---

## 1. The owner's words

- The standing bar: "AAA standard", "strive for excellent, above and beyond", "I don't want to polish, I want to create perfection", "do we have soul?" For enemies and bosses this means identity from this world, not generic. Remake rather than polish; verify at full resolution; don't stop to ask.
- **The endless phase** (answered this session): "endless is truly endless - just keep ramping up till its impossible (or not if the users get better and better and finding ways to win haha)". The coordinator's gloss: no Dawn; it climbs steadily past what any build survives; it stays readable and fair and varied (new pressure, not only bigger numbers); and a great player with a broken build can still push it a long way.
- **Encounter notes** (the newest, not yet built: your first task, section 4):
  1. "once quite a few overlapping constantly. periods of that are exciting, non stop can be a little weird." This is about charges. Govern them:
     - cap how many are live or telegraphed at once;
     - stagger them into waves with lulls (a director with a cooldown and a budget);
     - make overlap a deliberate spike, not the steady state;
     - keep it readable.
  2. "consider mechanics that ramp along with the level time and don't appear till certain mini bosses and minion types show up". Build an escalation schedule:
     - mechanics (charges, projectiles, zones, summons, auras, shields, splits) unlock as the clock advances and as specific minibosses and minion types arrive;
     - each stretch of a run teaches something new;
     - it feeds the endless ramp.
  3. "variety of minion types elites and mini bosses instead of all just the same models of wolves - we don't need to adjust models yet thats another pass but we should be having varrying things in place". On the models and rigs we have (retint, rescale, gear, behaviour, silhouette):
     - distinct minions, elites and minibosses per people and zone;
     - each with its own behaviour, role in the horde and readable identity, plus the compositions and waves that mix them;
     - for each new type, a model brief in the design doc for the later model pass.

  Record the design in the docs. Coordinate pacing with the gameplay experience director (`a33f58e68e89e3ccf`).

## 2. The rules of the work

- The repo is munchtech/survivor_unchained.
  - Work in your own worktree and merge `origin/claude/vigilant-galileo-l6jqyx` first and often.
  - Commit and `git push` your branch. No PRs.
  - Every commit ends with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- `cd godot/tests && dotnet test` must be green before every commit (about 45 s, 475 tests).
- The game is the Godot 4.5.1 .NET project in `godot/`. The root `src/` and `tests/` are the old web build: don't edit them.
- Don't touch these; their owners are in the roster:
  - `godot/src/Actors/` (animation and art);
  - `godot/art/`;
  - `godot/shaders/`.
- Don't rewrite story text. Ours:
  - item, skill and enemy names, notes and move names;
  - boss move barks and boss announcements.

  The Barrow Lord's orders are the story editor's (Latin, plural).
- Use British spelling. Comments are short prose saying why. Never print or commit tokens.
- The GPU is shared (ComfyUI at 127.0.0.1:8188).

## 3. The brief this session, in order

1. Merge the integration branch. Read the team page and the predecessor's handoff.
2. Check all four bosses on screen with `--minute`:
   - the arrival and the camera turn;
   - every telegraph type (cones point right);
   - the BREAK, the stagger bar, each boss's script.

   Fix what's wrong. **Done.**
3. Teach the bot the bosses before any sweep. **Done** (`BossSense`).
4. Apply the story lead's view (`docs/STORY_BIBLE.md`, "The nights"):
   - Grimtunnel never dies in an arena (**done**, and the table fields the Ganger);
   - Keegan's duel at first light (a day fight; nothing to build here);
   - Greymuzzle let go, narrowly (**done**).
5. Keep `docs/team/combat.md` as a one-page status with before and after numbers.
6. The owner's endless answer: build the ramp deliberately; record the decision in the design doc and status page. **Done** (the long night).
7. The next steps, in order:
   - the on-screen check (**done**);
   - boss length toward 90–120 s (**done**, see section 5 for the last nudge);
   - **the full sweep (not started)**.
8. **The owner's encounter notes** (section 1). **Not started:** this is your first task.

## 4. Your first task: the encounter notes

My recommended shape follows. Design it properly, record it in SKILLS_DESIGN (a new subsection of 16, or a section 17 "Encounters"), and test each rule.

**4.1 The charge director.**
- **Where:** charges and lunges start in `godot/logic/Sim/Ai.cs`. The branch is `if (e.RangedT <= 0 && dist < lunge.Range && dist > 2 && ...)`, around line 165: it sets `EnemyState.Windup` and emits the lane telegraph.
- **The gate:** add `&& b.Charges.MayStart(e)`, a small director on `Battle`:
  - a cap on live charges (Windup plus Lunging), e.g. 3 + tier;
  - a budget that refills at N charges a second, with a cooldown after a burst;
  - every 30–45 s a **spike** window of 3–4 s with a higher cap, announced by the people's own tell (a howl from the Pack, a whistle from the Kerchiefs), then a lull;
  - a refused enemy keeps closing at a walk, and retries a little later (jitter its `RangedT`).
- **Scope:** elites and bosses outside the budget, or with their own small one. The predecessor capped ranged throwers the same way (`ArenaRun.RangedCap`).
- **Tests:** never more than the cap outside a spike; spikes happen and end; a crowd of 60 wolves still charges in waves, not all at once.
- **Measure:** the harness's ByMinute has no charge count; add one (Ev.Telegraph lanes from non-bosses, or enemies in Windup per minute).

**4.2 The escalation schedule.**
- **What exists now:** each people has `Arena` entries `(Def, Weight, FromMinute)` in `godot/logic/Maps/MapOffers.cs`. New kinds join at fixed minutes, and events cycle ring, champion, stampede, swarm.
- **Build:** per people, a schedule of *mechanics* as well as kinds. Each stretch (about every 4–6 minutes) introduces one new verb, first shown by a **miniboss** that wears it, after which minions with it join the horde. Bake the verbs into it:
  - charges;
  - projectiles (lobbed and straight);
  - ground zones;
  - summons;
  - auras (a buffing shaman);
  - shields (guards exist: `GuardSpec`);
  - splits (`SplitSpec` exists, unused);
  - trails (`TrailSpec`, unused);
  - orbit.

  The code has most verbs already (the bestiary study listed the unused ones: Orbit, Trail, Split, multi-shot).
- **Hand-off to the long night:** past the half hour the schedule hands over to the dark's oaths (already built). The schedule can continue there: a new miniboss kind at each return.
- **Pacing:** experience director `a33f58e68e89e3ccf` measured the run as flat, not relentless. The share of runs dipping below half health was:

  | Minutes | 0–10 | 10–15 | 15–20 | 20–25 | 25–30 | boss | 35–45 |
  |---|---|---|---|---|---|---|---|
  | Below half health | 16–17% | 28% | 8% | 19% | 9% | 27% | 62% |

  They want:
  - a sawtooth rising into 10, 20 and 27–30, releasing after each;
  - breathers;
  - a signature event per people at each landmark;
  - never the same event twice running.

  **The agreed split:** they own breathers and set pieces in a new `Play/Zones/ArenaPacing.cs` (the horde's target share by minute, the breathers, the next event). Combat owns what spawns and what it does. Read `docs/team/experience.md` (on their branch, then merged).

**4.3 Variety on existing rigs.**
- **Visuals that exist** (`godot/src/Actors/Visuals.cs`, `Beasts.cs`, read-only for you):
  - wolf, wolf_alpha, wolf_blighted, boar;
  - lampling, lampling_sapper, grimtunnel;
  - skeleton_minion, skeleton_warrior, skeleton_warrior_elite, skeleton archer;
  - the Kerchief bodies (footpad, pillager, bruiser, kerchief_enforcer);
  - the warden view.

  Scale is per def (`EnemyDef.Scale`), so new defs can rescale freely in logic.
- **Retint and gear need a hook** in `CrowdView`: a per-def tint (`EnemyDef.Tint`), applied where `Visuals.Tint(e.Def.Visual)` is read. Ask the animation lead (`aa4f5fc266b043035`) to add it, or agree with them a one-line change. Bosses already get a tint through `Named`.
- **The bestiary study's creatures** (`docs/bestiary/ROSTER.md`, `HORDES.md`, `IMPLEMENTATION.md`):
  - Ridge-Runner (wolf + Orbit + Lunge);
  - Slurry Sow (boar + Trail);
  - Bone-Heap (skeleton warrior at 1.5 + Split);
  - Wick (lampling at 0.75, packs);
  - Levy Crossbow (a Kerchief shooter, multi-shot 3).

  Add minibosses per people (one per escalation stretch) and elites with champion **Signs** (`docs/bestiary/COUNTERS.md` §4).
- **Model briefs:** give each new type a short brief (silhouette, size, colour, what it carries, how it moves) in SKILLS_DESIGN for the model pass.
- **Drops:** crafting (`a7862117a0240deb5`) will want drops from the new types. Give each one a loot tag.

## 5. State: done, in progress, next

**Done this session** (commits `f92ad71`, `a96a75f`, `0eff808`, `313d195`, `0f6cce9`, `2c6a78e`, `fbe29bc`, plus the handoff commit):

- **Bosses actually run in the game.** `Game.HookBattle` had copied the zone's hooks before the boss came. `BattleHooks.Following` fixes it, and a test runs a boss through the game's wiring.
- **The on-screen fixes:**
  - move names in their own word pool (`Hits.Word`), said over the boss;
  - the BREAK alone and high;
  - bands drawn as annuli with a clear inside;
  - the stagger bar's groove (it had been clipped inside the health track);
  - cone and band edges antialiased;
  - bosses' own bodies (`boss_pack`, `boss_dead`, `boss_lamplings`, `boss_kerchiefs` in `Content/Enemies.cs`), named, with a softer hit flash;
  - the people make way at the arrival (`ArenaRun.MakeWay`).
- **Bugs fixed:**
  - the howl crash (a channel broken inside its move);
  - a phase turn said "Interrupted!" and kept the old move;
  - a stagger could land while the boss was untouchable;
  - a holy blow broke the laying-down;
  - oath ember was never paid (`MapRules.EmberGain`);
  - the harness's Break used a pooled body;
  - `--give` couldn't rank up a weapon already held.
- **Story:**
  - the Ganger at the table (a Grimtunnel-script mode with one lamp, which dies);
  - Grimtunnel's own night unchanged;
  - Greymuzzle's pronouns, and his lines are narration;
  - **Greymuzzle let go** (`ArenaSpec.Spare`, set in `Verge.MakeStoryFights` when `promise.pack` is set, `promise.broken` isn't, and `StreamClean()` holds).
- **Bots:** `Play/Bosses/BossSense.cs` (reaction 0.45 or 0.25 s, notices 80% or 95% of blows), used by the harness's Pilot and the game's `--auto`. `--bossread 0` gives the old hands. The harness report has "The bosses" and "The long night" tables.
- **Boss health per boss** (`HealthMul`):
  - Pack-Mother `30 + 5t`;
  - Barrow Lord `13 + 2.2t`;
  - Ganger and Grimtunnel `18 + 3t`;
  - Red Hand `21 + 3.5t`.

  Measured TTK, deft hands, tiers 1–3:

  | Boss | Before | After |
  |---|---|---|
  | Pack-Mother | 69 s | 84 s |
  | Barrow Lord | 80 s | 86 s |
  | Ganger | 92 s | 98 s |
  | Red Hand | 72 s | 84 s |

  The Pack and the Red Hand were then raised a further tenth: **re-measure them in the full sweep.**
- **The long night** (`ArenaRun`, "the long night" block):
  - `Hardening(m)`: health `1 + 0.1m + 0.006m²`, blows `1 + 0.035m`, both compounding 3% a minute from +60, pace up to +15%;
  - the dark's oaths every 5 minutes (`DarkDeck`);
  - returns every 15 minutes (`ReturnGrowth` 0.35, `ReturnBite` 0.25);
  - heralds between.

  Deft hands, tier 2: minutes past the half hour, median 21 (p10–p90 11–38), furthest 53.

**Next, in order:**
1. The encounter notes (section 4).
2. **The long night's tail:** the deft bot's best is +53, and great humans will go further. To let great builds reach +60–75, try the quadratic health term at 0.004. Command: `arena --callings all --policies greedy,paths --seeds 4 --tier 2 --level tier --oaths table --cap 160 --beyond 130 --bot deft`, about 25 minutes. The report's "The long night" table is the readout.
3. **The full sweep** (6 seeds, 45 minutes, both bots, drafting policies): `arena --callings all --policies greedy,random,paths --seeds 6 --tiers 1,2,3 --level tier --oaths table --cap 46 --beyond 15 --bot deft --out out/full_deft.jsonl --csv out/csv_deft`, and the same with `--bot plain`. Peoples are dealt by seed (`peoples[(s + w) % 4]`); 8 seeds give even coverage. Use it:
   - to keep or revert each of the balance lab's four tunings (lampling 16→20 health and 7→8 damage; sappers weight 2.5→3.5 from minute 4; risen bowman cooldown 2.8→3.3 s and damage 7→6);
   - to re-check boss TTK;
   - to check passives under greedy and paths.

   **Note:** oath ember is now paid, so table-oath runs level faster than before. Re-read the tier ladder.
4. Then:
   - Signs;
   - oaths on bosses (iron halves `StaggerTaken`);
   - enemy hazards hurting the horde at half;
   - the Kindling at minute 15;
   - the Ford-Warden echo;
   - "weight" as a number on the table.

   All are decided in SKILLS_DESIGN §16.4; none are built.

## 6. Decisions (the reasons are in SKILLS_DESIGN §16)

- Bosses are gates: phases, floors, the Break and enrages, with health tuned to 90–120 s.
- One boss sense, shared by every bot and by the pictures' autopilot.
- The long night: three lines (hardening, the dark's oaths, returns); never the moonless; returns grow by a rule.
- The way out stays after the win. The ramp has no ceiling; death or leaving ends a run.
- The Ganger reuses Grimtunnel's script as a mode, not a copy.
- Bosses wear their own defs: champion bodies about 1.4 times the size, health from the champion's.

## 7. Tried and failed, and why

- **The first long night made the first return a wall.** The returning boss took the night's hardening and its levels on top of its own; runs fell to the Ganger more than to anything. It now grows by a fixed rule.
- **The dark first swore the hunt and the winter early**, and the tail compressed to +39. The grinding oaths now come last.
- **The boss health model "Break means overkill"** over-predicted. Raising health by 2.3 times moved the Pack's TTK only from 69 to 84 s, because floors dominate fast builds. Calibrate by measuring, not by the model.
- **The game's autopilot couldn't reach a boss through the crowd** (it circled a fixed patch). It now circles the boss and uses `BossSense`.
- **An `--give` build at ember 4 is not representative.** The phases ran to their 60 s ceilings. Give 5–6 weapons at rank 8 with evolutions.

## 8. Gotchas

- **Pictures:**
  - Use `python tools/combat/shots.py NAME PEOPLE [options]`, then `python tools/combat/sheet.py OUT.png COLS WIDTH frames...`, then look at what matters at full size.
  - `--on boss --until S` takes a frame per boss move, Break, arrival and announcement.
  - `--marks` gives the telegraph gallery: +X is screen right, +Z is screen down.
  - `--boss grimtunnel_roused:Grimtunnel` puts a story foe at the half hour; `--spare` lets it go.
  - Frames are in `godot/.shots/`.
- **After a merge with new art, run Godot's import** (`Godot..._console.exe --headless --path godot --import`, a few minutes), or the HUD's new textures fail to load.
- **Never commit `.import` files.** Godot rewrites them locally; stage files by name.
- **Untracked `*.cs.uid` files** that Godot generated can block a merge ("would be overwritten"). Delete those files and merge again.
- **`godot/assets` must be a junction to `public/assets`:** `Remove-Item godot\assets; cmd /c mklink /J godot\assets public\assets; git update-index --skip-worktree godot/assets`.
- **The shell sandbox refuses** `cd X && ... heredoc`, `cd ... && git`, and `$(...)` in sed ranges. Write Python edit scripts to the scratchpad with the Write tool and run them with `python path`. Never put `\\n` through a bash heredoc into C#.
- **The enemy pool reuses slots:**
  - a `B.Enemies.Items[id]` kept past a death can be another creature, so track `(Id, Seed)`;
  - a script's `E` after the fight is a stranger;
  - `ArenaBoss.MaxHp` keeps the boss's health at arrival.
- **Game vs tests:**
  - The game wraps battle hooks with `BattleHooks.Following`; the tests share the zone's hooks. Use `BossTests.At30(..., game: true)` to test through the game's path.
  - A Battle's `Rules` (`MapRules`) is the oath state. The dark's oaths invoke `Rule` on it and multiply `EmberGain`.
- **The harness:**
  - `cd godot/balance && dotnet build -c Release`, then `dotnet bin/Release/net8.0/Balance.dll arena ...`.
  - A running sweep locks `bin/Release`: build with `-o bin/probe` meanwhile.
  - `report --in X.jsonl` re-reads a sweep.
  - The machine has 24 threads; a sweep uses 16 by default.

## 9. Collaborators (see `docs/team/README.md` for the live roster)

- **Gameplay experience director** `a33f58e68e89e3ccf`: pacing (`docs/team/experience.md`); owns `ArenaPacing.cs` by our split.
- **Animation** `aa4f5fc266b043035`: owns `src/Actors`; the per-def tint hook is theirs to add or approve.
- **Story** `a7622ae77d19e31dc`: Greymuzzle spared needs their words (the history line, Maeca, C10's variant); they edit boss barks.
- **Performance** `a9586a5171413db0b` measures horde cost. The caps: 380 in the horde, 24 ranged, telegraph caps.
- **Crafting** `a7862117a0240deb5` wants drops from new types.
- **UI design** `ac76f400913a109cd`: the edge marker over the boss title; the HUD's boss bar is theirs (the stagger groove is ours, inside `GameHud.Boss`).
- **Skills look and feel** `a8bafe3cd8a229639`; **cinematics** `a2dfc75e2d351105a`.
- **The main session** relays the owner. Report to it concisely.

## 10. Files to read first

1. `docs/SKILLS_DESIGN.md` §16 (and §11 for the power curve).
2. `godot/logic/Play/Zones/ArenaRun.cs`: the arena (horde, events, heralds, run-up, boss, making way, the long night).
3. `godot/logic/Play/Bosses/ArenaBoss.cs` (the contract), `ArenaBosses.cs` (the four), `BossSense.cs` (the bots' boss reading).
4. `godot/logic/Sim/Ai.cs`: enemy behaviours, charges and lunges (the charge director's hook).
5. `godot/logic/Content/Enemies.cs` and `godot/logic/Maps/MapOffers.cs`: defs, peoples, oaths.
6. `godot/balance/Harness/Pilot.cs`, `ArenaSim.cs`, `Report.cs`.
7. `godot/tests/BossTests.cs`, `ArenaTests.cs` (the long night), `BestiaryTests.cs`.
8. `docs/bestiary/README.md`, `ROSTER.md`, `HORDES.md`, `COUNTERS.md`; `docs/bosses/README.md`, `IMPLEMENTATION.md`.
9. `src/Fx/BattleFx.cs` (telegraphs, words), `src/Fx/Hits.cs` (the word pool), `src/Game/Game.cs` (`--on boss`, `--marks`, `--boss`, `--give`), `src/Shots.cs`.
