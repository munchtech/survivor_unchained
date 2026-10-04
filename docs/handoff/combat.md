# Handoff: combat (skills, enemies, encounters, bosses, balance)

Written by agent `ac4ec5bbd2763a0df` for its successor, at a clean checkpoint at about 575k context.
- **State:** everything is committed and pushed on `worktree-agent-ac4ec5bbd2763a0df`, merged with the integration branch `claude/vigilant-galileo-l6jqyx` at `535bb60`.
- **Tests:** 539 green.
- **Predecessor:** `a09c5a65f5a84319e`. What it knew that still matters is folded in below.

Read these first, then the files in section 9:
- `docs/team/README.md`: the team's rules and the roster;
- this page;
- `docs/team/combat.md`: the one-page status, with the latest numbers;
- `docs/SKILLS_DESIGN.md` §16–17:
  - §16.1–16.3: the bosses, the bots, the long night;
  - §16.4: the charge director;
  - §16.5: the stretches, minibosses, kinds, Signs and model briefs;
  - §16.6: story nights;
  - §16.7: two fixes;
  - §16.8: open decisions;
  - §17: maps, designed and not built.

---

## 1. The owner's words

- **The bar:** "AAA standard", "strive for excellent, above and beyond", "I don't want to polish, I want to create perfection", "do we have soul?" Identity comes from this world, not generic fantasy. Remake rather than polish; check at full resolution; don't stop to ask.
- **Endless:** "endless is truly endless - just keep ramping up till its impossible (or not if the users get better and better and finding ways to win haha)". No Dawn. A table night after its win goes on until a fall or the way out.
- **The three encounter notes** (all three are now built):
  1. "in our charge mechanic once quite a few overlapping constantly. periods of that are exciting, non stop can be a little weird."
  2. "consider mechanics that ramp along with the level time and don't appear till certain mini bosses and minion types show up"
  3. "variety of minion types elites and mini bosses instead of all just the same models of wolves - we don't need to adjust models yet thats another pass but we should be having varrying things in place"
- **Structure:**
  - "end game is two types of arenas - permanent and our normal arenas. permanent is our arpg build maps like poe and the normal arenas are for mindless survivors fun"
  - "story should be 40% of the game early on"
  - The coordinator's standing summary: story nights are 20 minutes, the Wayfinder's maps (table nights) are 30, and the endgame is the Wayfinder's atlas plus the ember scars.
- **Voice placeholders are gone**, by the owner's call. Only the 8 cinematic narrator and watchman lines remain. Add no new placeholders.

## 2. The brief

You own:
- skills' mechanics;
- enemies, elites, minibosses and bosses;
- encounters;
- balance.

In order, from the coordinator:
1. **Re-measure after the last tuning** (section 4.1): the Pack-Mother and the Red Hand are in it.
2. **The experience director's two briefs:**
   - **Careless drafts should lose more at tier 3.** Random drafting wins as often as greedy at tiers 1–3. The target, from tier 3: about 60% won for a careless draft against 85% for a planned one, while tiers 1–2 stay forgiving.
   - **The boss floor.** A late `--give` build at tier 1 killed the Barrow Lord in about 35 s, under the 45–60 s floor for an absurd build. The autopilot took no blow in the whole fight.
3. **The full balance sweep, and the long night's tail.** The deft bot's best is +53 minutes past; try a 0.004 quadratic health term so great builds reach +60–75.
4. **Then the maps** (§17.7), with the experience lead (shape and loop) and crafting (chart items).
5. **The story lead's brief for C14, "The Road Back"** (`a035208561a66c171`; script in `docs/cinematics/c14_road_back.md`). Fit it into the queue; build it before the maps if story needs it for Act 1.
   - **The fight:** story fight `night:road_back`, that night only, when `nell.road` = "with". Story writes `brannoc.road` once the fight exists.
   - **Setting:** people dead, 20 minutes. The place is the Low Ford road at the wagon and ditch: the prologue's Lowford zone at night if it can be reused, otherwise an arena dressed as the road (arena art's call).
   - **Boss: Wat,** "Over the Ford by Dark":
     - a big drowned carter: a drowned or risen rig, carter's coat, a copper toll-token in his hatband;
     - the cold trail;
     - silent, with no barks;
     - lesson: "He walks where the water was. Keep off the wet."
   - **Ally: Brannoc** with his hammer:
     - holds the edge of the lantern's light and never chases;
     - never dies (goes down on one knee, gets up);
     - his kills are not credited to the survivor;
     - his blow's word is "Down."
   - **Outcomes:** OnWin sets `nell.brought_home` true and gives nothing. OnLose sets nothing.
   - **Hooks for the cinematics lead's C14 cues:** spawn at the boss's arrival, and dawn at the win.
   - Tell story when it exists. They will add `brannoc.road`, the `nell.burial` morning variant and a RouteTests play.
6. **Then:**
   - oaths on bosses (iron halves `StaggerTaken`);
   - ground hazards hurting the horde at half;
   - the Kindling at minute 15;
   - the Ford-Warden echo;
   - weight as a number;
   - the remaining Signs (Warded, Mending, Leader).

**The split with the experience director (`a33f58e68e89e3ccf`):**
- They own when and how full: `Play/Zones/ArenaPacing.cs` (shape, breathers, floods, the hush, which turn, `Building`), the victory beat, and the maps' shape and loop.
- Combat owns what spawns and what it does, including the bodies of their Signature turns, and the maps' mechanics.

## 3. Done (this agent)

Commits: `c4defa2`, `e9e591d`, `52eb7a9`, `71608a4`, `4b95fc0`, plus merges.

- **The charge director** (`Sim/Charges.cs`, `Battle.Charges`; §16.4):
  - waves of `2 + tier/2` runs at once, 0.7 s apart;
  - lulls of 3–6 s;
  - spikes every 40–55 s, or 18–26 s while `pacing.Building`, after the people's tell (`tell_howl`, `tell_horn`, `tell_fuse`, `tell_whistle`, now with sound from the skills lead);
  - calm in breathers, the hush and a herald's duel;
  - a quiet spike with each Signature turn;
  - while a boss is up, one crowd run and no spikes;
  - champions get their own allowance; bosses are never asked;
  - caps: 8 tunnellers under the ground, 8 bursts fusing, 24 patches of enemy ground (the oldest goes out first);
  - its own `Rng`.

  Measured: charges a minute went from 123–184 to 42–59, and the most at once from 15–22 to 5–7. The harness has `--charges 0` and an "Encounters over the minutes" table.
- **Stretches** (`Play/Zones/Escalation.cs`, `Denizens.Stretches` in `Maps/MapOffers.cs`; §16.5):
  - five per people, at 3, 7, 12, 16 and 22 minutes of a table night;
  - a miniboss shows the verb; then its kinds join the horde and its Signs open;
  - minibosses never come in the hush or a herald's duel; held back 2½ minutes, their kinds join anyway;
  - the long push at 25 minutes brings two back;
  - in the long night, heralds and signed pairs take turns;
  - minibosses get the herald's bar and carry a **one-card** chest (`smallChests`; a full chest made builds too strong).
- **New verbs** (`Content/Enemies.cs` specs; `Sim/Ai.cs` `Verbs`, `Run`, `Call`, `Rally`):
  - `AuraSpec` (haste and ward; one rallying voice on the field);
  - `SummonSpec` (the marks first, then the summoned come there; `BattleHooks.OnCalled` lets the zone soften them);
  - `SlamSpec` (it lands even if the slammer dies; it counts as a run for the director);
  - `Chain` (repeat runs);
  - `RunBursts`;
  - `Bite` (chill or poison);
  - `IronSkin`;
  - fanned multi-lobs;
  - `Ev.Telegraph.Faction` on aura, call and slam marks.
- **Variety:**
  - 13 new kinds and 20 minibosses on existing rigs, with `EnemyDef.Tint` and `Glow` drawn by a 4-line hook in `src/Actors/CrowdView.cs` (agreed with animation);
  - nine Signs in `Content/Signs.cs`: cloned defs with the kind's id, named "Swift, Kindled Barrow Knight", with forbidden pairs;
  - a model brief per type in §16.5;
  - names per the story lead, including Gutterwick ("Second-Best in the Dig") for the table's Lamplings boss.
- **Story nights are 20 minutes** (§16.6):
  - `Verge.Story` sets `Minutes = 20`;
  - `ArenaRun.Minute` is a night clock in minutes of a 30-minute night; past the boss it counts real minutes;
  - ember (`Rules.EmberGain *= Pace`, undone at the win) and `Arenas.XpFor` are paced to match;
  - a story night ends on its boss: no long night, and its people make way;
  - one voice for every night: "The dead of night", "Halfway through the dark".
- **The economy, as agreed with crafting:**
  - `MapRules.FodderGold = 0.02` in arenas;
  - plain gear only from carriers (champion turns, captains, heralds, minibosses, the boss).
- **A fix (§16.7):** bad ground was a blow, and each blow bought 0.45 s of iframes, so standing in fire shielded the survivor from the crowd. Bad ground is now `HurtByGround`, damage over time (armour and resistance only); frost ground chills.
- **Maps designed (§17):** how they differ from nights; the chart item and its mods; packs, champions, altars and the boss at map strength; loot; the atlas's levers; the build order; and proposed changes to the experience lead's brief.
- **Harness:**
  - `--minutes 20` (story nights);
  - per-run `MinibossesMet` and `Minibosses`, and a "The minibosses" table;
  - the probe's crowd is the people's day rank and file (`Denizens.Horde`), so new kinds don't move path balance.

## 4. In progress, and next

### 4.1 Re-measure first

The last tuning is not measured: one-card miniboss chests, the Scorpion at 300 health, the Decurion's guard at 0.6. The sweep before it, against `81429e6`, deft bot, tiers 1–3, greedy and random, table oaths, 96 runs each:

| | Before | After (`71608a4`) |
|---|---|---|
| Won, greedy / random | 98% / 92% | 88% / 94% |
| Won, tiers 1 / 2 / 3 | 97% / 94% / 94% | 94% / 94% / 84% |
| Boss TTK (Pack / Barrow / Gutterwick / Red Hand) | 99 / 90 / 97 / 77 s | 76 / 78 / 101 / 64 s |
| Herald TTK, greedy / random | 19 / 25 s | 20 / 37 s |
| Miniboss TTK, median | – | 9–52 s |

Falls after the change: two at minute 2–4 (tier 3, blight+vigil and swarm+embers), one at 10.9, one at 12.5, and four at the boss.

**The command:**

    cd godot/balance && dotnet build -c Release
    dotnet bin/Release/net8.0/Balance.dll arena --callings all --policies greedy,random --seeds 4 --tiers 1,2,3 --level tier --oaths table --cap 34 --bot deft --par 11 --out out/enc2.jsonl

It takes about 5 minutes. If bosses still die well under 90 s at par, raise `HealthMul` in `Play/Bosses/ArenaBosses.cs`. That is the Pack-Mother and Red Hand re-measure.

**A baseline harness** of any commit: `git archive <sha> godot/logic godot/balance godot/data -o x.tar` into the scratchpad, untar, and `dotnet build -c Release` there. `DataFiles` finds `data/` by walking up from the binary.

### 4.2 Careless drafts at tier 3

**Hypotheses:**
- Tier 3's champions and minibosses now wear Signs and hit harder, so a random draft's weaker single-target damage should show. Measure first with 6 seeds, both bots.
- Levers that punish carelessness without punishing tiers 1–2:
  - raise champion and miniboss health from tier 3 only (`Miniboss()` uses `1.6 + 0.6 × tier`);
  - a second Sign earlier at tier 3;
  - a tier-3-only boss floor rise.

Never raise fodder.

### 4.3 The boss floor

The contract (`Play/Bosses/ArenaBoss.cs`) has phase floors of 15, 20 and 15 s. A 35 s kill means the floors and the Break did not hold.
- Check with `--give` pictures (section 7), or a test that pushes an absurd build through `BossTests.At30(..., game: true)`.
- Check that the charge director's calm (cap 1 while the boss is up) did not make it too easy.

### 4.4 Maps

Build in the order of §17.7:
1. `MapRun` on `MapGen`'s winding layout. Packs come from `PackSpot`, rousing by `Wake` and `Leash`. The boss runs through `IBossArena`.
2. The chart item.
3. Magic and rare packs, and altar guardians.
4. Loot and charts.
5. The atlas, with the experience lead.
6. Chart crafting, with crafting.

Agree §17.7's proposed brief changes with the experience lead first: boss at 45–75 s, kinds open by tier, the moonless as a map suffix, the event lit at an altar.

## 5. Decisions (why: in SKILLS_DESIGN §16–17)

- **Charges are directed, not timed.** Overlap is a told moment, not the weather.
- **A verb is shown before it spreads:** one big body first, then the crowd. That is the escalation's rule, and in maps the atlas's.
- **Signed champions are cloned defs keeping the kind's id,** so nothing downstream needs a special case.
- **One rallying voice on the field at a time:** auras and Bannered.
- **Dice:** verb timers draw from the battle's dice only when a creature has the verb, and the director has its own stream. This keeps balance comparisons honest.
- **The probe's yardstick is the day's rank and file,** not the arena's growing roster.
- **One night clock, inherited by every system,** instead of per-system scaling for short nights.
- **Nights and maps share one bestiary:** a verb learned in one is learned for both.
- **Inherited from the predecessor:**
  - bosses are gates (floors, the Break, enrages), with health tuned to 90–120 s at par;
  - one `BossSense` for every bot and for `--auto`;
  - the long night climbs on three lines: hardening, the dark's oaths, returns;
  - the way out stays after a table win;
  - Grimtunnel never dies in an arena.

## 6. Tried and failed, and why

- **The director first shared the battle's dice.** That moved a balance probe by noise alone: Weave's crowd went 1823 → 2023, failing the 1.35 bound. It now has its own `Rng`.
- **Full chests on minibosses** made builds stronger at the boss: boss TTK fell 12–25 s, and damage a minute at 25 rose 247k → 276k. They now carry one card.
- **The Scorpion (52 s) and the Decurion (49 s)** were kiters behind 75% guards: a chase, not a fight. They were softened, and the change is not yet measured.
- **The probe's crowd took the arena's new kinds** (bone heaps that split), which pushed Host below the 0.7 bound. The probe now uses the day's rank and file.
- **Bad ground as a blow** gave iframes (section 3).
- **Two inherited lessons:**
  - the first long night made the first return a wall;
  - raising boss health by a model over-predicted. Calibrate by measuring.

## 7. Gotchas

- **The shell sandbox refuses**:
  - `cd X && git ...` into another worktree;
  - `$(...)` and variables used as python arguments;
  - heredocs into C#.

  Write python edit scripts to the scratchpad with the Write tool, and run them as `python C:/.../scratchpad/script.py`. Two helpers are there:
  - `edit.py FILE PAIRS.py`;
  - `multi.py SPEC.py` (`FILES = {path: [(old, new)]}`).

  Both need exact, unique matches.
- **Reading other agents' worktrees:** read their files with Read, not git, and never run git in their trees.
- **Run `dotnet test` in `godot/tests` before every commit** (about 50–110 s). Build the game with `dotnet build SurvivorUnchained.csproj` in `godot`.
- **The harness:**
  - `cd godot/balance && dotnet build -c Release`; a running sweep locks `bin/Release`, so build with `-o bin/probe` meanwhile;
  - `report --in X.jsonl` re-reads a sweep;
  - the machine has 24 threads.
- **Pictures:** `python tools/combat/shots.py NAME PEOPLE [options]`, `--on boss`, `--marks`, `--give`, `--minute`. Frames go to `godot/.shots/`.
  - After a merge with new art, run Godot's `--headless --import`.
  - Never commit `.import` files.
  - Delete untracked `*.cs.uid` files that block a merge.
  - `godot/assets` is a junction to `public/assets`.
- **The enemy pool reuses slots.** Track `(Id, Seed)`, as `miniboss` with `minibossSeed` does.
- **Game vs tests:** the game wraps hooks with `BattleHooks.Following`, and any new hook must be added there (`OnCalled` is). Use `BossTests.At30(..., game: true)`.
- **ArenaRun's clock:**
  - `Minute` is the night clock: 30 at the boss whatever `Spec.Minutes` is;
  - `Seconds` and `End` are real time;
  - `Beyond` is real minutes past the boss.
- **Text** (names, notes, lessons, words, tells) goes through the story lead.
  - Canon: never "Ashford" in Kerchief text; no battle at Ashford; no ford bell (the Legion marched to horns and standards); "Boss" is Grimtunnel's alone; the Legion speaks Latin.

## 8. Collaborators (the live roster is in `docs/team/README.md`)

- **Experience director (`a33f58e68e89e3ccf`):** pacing, the victory beat, the maps' loop. Both briefs in section 4 are theirs.
- **Story (`a035208561a66c171`):** all names and lines. The bible's "The nights" holds the rules.
- **Animation (`a1e3002b800ee55ac`):**
  - **Delivered** on `worktree-agent-a1e3002b800ee55ac@eeadae6` (the VAT cache is now v9):
    - the wolf howl as the beasts' "cast" role: wolf, wolf_alpha, wolf_blighted, wolf_spirit;
    - a rally gesture as every person visual's cast. kerchief_brute and skeleton_minion keep their windup until a slam lands.
  - **Keep its two small edits in combat code:**
    - CrowdView's Casting uses `t = e.AnimT`;
    - Ai's grave-caller raise sets `e.AnimT = 0`.
  - kneel_shoot and slam wait on the owner's Kimodo run.
  - Its tool `godot/tools_scenes/crowd_sheet.gd` (VISUAL=, ROLE=, N=, STEP=, YAW=, OUT=) renders any crowd kind's role as a contact sheet. Use it to check the new kinds on screen.
  - has the motion list: a quadruped howl, kneel-to-shoot, a slam, a horn, drum or rally gesture, the shamble;
  - is fine with gear variants (crossbow, pike) as new visual keys later;
  - the tint hook in CrowdView is combat's: exactly those lines.
- **Skills look and feel (`a8bafe3cd8a229639`):**
  - doing spike tell sounds (done), aura rings in the people's colour (`Telegraph.Faction`), slam dust, summon circles, Sign marks, and the haste and ward glints;
  - note: the dead's tell is `tell_horn`.
- **Crafting (now `a97e32948c5bf419d`):**
  - has the 20 miniboss ids (`Loot = "miniboss"`), and will add +2 of the people's material each plus a rare drop;
  - re-checks shards for 20-minute nights.
  - Its endgame design is in `docs/CRAFTING_DESIGN.md` §20: scars pay fire, the atlas pays iron and bases.
  - I agreed these for maps:
    - the chart item gets heat (plain 4, fine 6, rare 8) and a pin slot;
    - map drops carry ilvl = creature level;
    - map materials are tallied at a map's end by `Crafting.Night`'s rules, and a fall spills half;
    - two kits (night and map) are fine.
  - **Open, yours:** Sigils, gear that bends one day skill in maps. Confirm a clean per-skill modifier hook (WeaponInst's evolution `Set` and `Mods` look like the place) or decline.
  - I sent crafting the economy medians per won night (tiers 1/2/3):
    - Kerchiefs' gold went from 45k/53k/43k to 2.6k/3.3k/2.8k (champions keep the day's gold);
    - champions are 864/1052/1079, within 10% of before.
- **Performance (`a9586a5171413db0b`):** caps are horde 380, ranged 24, enemy ground 24; the director scans the pool once a tick.
- **UI design and UI art:** miniboss and herald bars use `BossBar(IsBoss: false)`, with the Signs or lesson as the title line.
- **The arena art lead** (new; see the roster): the arenas' look. The maps' layouts come from `MapGen`.

## 9. Files to read first

1. `docs/SKILLS_DESIGN.md` §16–17 (and §11 for the power curve).
2. `godot/logic/Play/Zones/ArenaRun.cs`: the night clock; `Minibosses`, `Miniboss` and `Sign`; `Harden`; the long night; story ends.
3. `godot/logic/Play/Zones/Escalation.cs` and `godot/logic/Maps/MapOffers.cs` (`Denizens`, `Stretch`).
4. `godot/logic/Content/Enemies.cs` ("the night's other kinds") and `godot/logic/Content/Signs.cs`.
5. `godot/logic/Sim/Ai.cs` (`Verbs`, `Run`, `Call`, `Rally`), `godot/logic/Sim/Charges.cs`, and `godot/logic/Sim/Battle.cs` (`HurtByGround`, `EnemyStrike`, `SpawnZone`'s cap).
6. `godot/logic/Play/Zones/ArenaPacing.cs` (experience's).
7. `godot/logic/Play/Bosses/ArenaBoss.cs`, `ArenaBosses.cs` and `BossSense.cs`.
8. `godot/balance/Harness/ArenaSim.cs`, `Report.cs`, `Probe.cs`, `Pilot.cs`.
9. `godot/tests/EncounterTests.cs`, `ArenaTests.cs`, `BossTests.cs`, `BalanceTests.cs`, `PacingTests.cs`.
10. `docs/bestiary/ROSTER.md`, `HORDES.md`, `COUNTERS.md` §4; `docs/items/PROGRESSION.md` §6 (the Depths and echoes, for maps).
