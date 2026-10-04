# Handoff: combat systems (skills, upgrades, balance, enemies, bosses)

Written by the agent `a09e0860794ed3e5c` ("Skills, upgrades and balance
overhaul") for its successor, at a clean checkpoint: everything below is
committed and pushed on branch `worktree-agent-a09e0860794ed3e5c`, tests
green (453 passing). Read this, then the ten files listed at the end, before
touching code.

---

## 1. The owner's bars, word for word

These apply to everything in this area. The coordinator relays them; the
owner is not in the chat.

- The original ask: "Go over skills, acquiring them, and balancing and
  synergies. How things are offered, or favoured, or any number of game
  theory. Research all the popular survivors-type games and build an
  extensive upgrade cohesion, balance, diversity, fun." AAA quality, with
  "an exhausting amount of time and effort with research and
  implementation".
- The standing note to every agent: **"I don't want to polish, I want to
  create perfection."** The coordinator's gloss: "don't limit yourself to
  tuning what exists. If the research shows a better structure, build it
  new ... Revisit anything you've already only tweaked, and ask whether it's
  actually the best design or just better than before. Record why each final
  design is the best answer in docs/SKILLS_DESIGN.md."
- The soul test: **"do we have soul?"** "They want one game in a million,
  not one soulless game of many ... mechanics and synergies with identity,
  rooted in this world (embers that sleep by day and burn at night, the
  callings, the Verge), and builds that feel like discoveries. Generic '+10%
  damage' design fails, however well balanced." For enemies and bosses: "The
  owner's 'soul' and 'perfection' bars apply: bosses and enemies with
  identity from this world, not generic."
- From the owner's memory notes (`MEMORY.md` in the user's Claude
  project): wants amazing, not improved; remake rather than skip; verify at
  full resolution. Don't stop to ask; keep going.

## 2. The rules of the work

- Repo `munchtech/survivor_unchained`. Work in the worktree
  `C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09e0860794ed3e5c`
  on branch `worktree-agent-a09e0860794ed3e5c` (or your own worktree, merging
  this branch first). Commit on the branch, `git push -u origin HEAD`. **No
  PR.**
- The game is the Godot 4.5.1 .NET project in `godot/`. Root `src/` and
  `tests/` are the old web build: **do not edit them.**
- **Do not touch** `tools/assets/`, `godot/art/`, `godot/shaders/`,
  `godot/src/Actors/` (the art, hair and animation sessions own them).
- **Do not rewrite story text** (dialogue, quests, lore: the writer agents
  own it). Item and skill names and descriptions are ours, as are enemy and
  boss move names, barks for boss moves and the boss announcements.
- **Never commit or print API tokens or secrets.**
- `cd godot/tests && dotnet test` green before **every** commit.
- Every commit message ends with
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- British spelling in docs, comments and player text. Comments are short
  prose saying **why**. Commit messages in the same voice (see `git log`).
- Commit and push often (usage cut-offs have hit this work three times).
- The git stash is shared with every other session: **never a bare
  `git stash`**; use a WIP commit instead.
- May use the computer freely: Godot, Blender, Python, the GPU, local
  ComfyUI at `http://127.0.0.1:8188` (`tools/comfy/comfy.py`; Krea 2 for
  images, qwen3vl for vision; models in
  `%LOCALAPPDATA%\Comfy-Desktop\ComfyUI-Shared\models`), web research, free
  reputable packages. No paid cloud services. The GPU is shared: keep
  generation reasonable.

## 3. The full brief, in order

1. **Original task** (coordinator for the owner): own the skill and upgrade
   design: (1) research the genre exhaustively into `docs/SKILLS_RESEARCH.md`
   (Vampire Survivors, Brotato, Halls of Torment, 20 Minutes Till Dawn,
   Soulstone, DRG: Survivor, HoloCure, Death Must Die, Rogue: Genesia,
   Magicraft, Spirit Hunters, Army of Ruin, Boneraiser Minions, Vampire
   Hunters, Nordic Ashes, Hades, Diablo IV, PoE, Last Epoch, Slay the Spire,
   Balatro); (2) audit everything with a headless balance harness (seeded
   runs per build and calling, bots greedy/on-archetype/random; TTK,
   survival, damage share, offer/take rates, win rate at 30 min, power over
   time); (3) `docs/SKILLS_DESIGN.md` (archetypes, synergy families,
   evolutions, the offer algorithm, slots, day feeding night, targets and
   power curve, boss and elite pacing, diversity; every skill a reason and
   two builds that want it); (4) implement it all with UI (synergy hints,
   recipes, why an offer was favoured), tests for the offer's guarantees,
   every recipe, archetype viability and no dominant strategy; verify in
   Godot by screenshot. Report: branch and commits, research highlights,
   before/after numbers, tests, what is open. **Done** (see section 4).
2. Owner: free use of the computer (above).
3. Owner's standing note "perfection" (above).
4. Cut-off notice, plus the `godot/assets` junction fix (section 9).
5. Merge `origin/claude/vigilant-galileo-l6jqyx` (`docs/items/`,
   `docs/feel/`, CI, an allocation fix in Battle.cs and Ai.cs); "fold item
   affixes and skills together into one coherent system if that is the
   better design". **Done** (kindled gear, section 6).
6. The soul test (above). **Done** for skills (SKILLS_DESIGN.md section 2).
7. The cloud balance lab (`godot/tests/BalanceLab.cs`, deft bot, CSVs):
   "Weigh it against your own harness and merge whatever makes yours better,
   ending with one coherent tool rather than two." Also the five open
   decisions in `docs/items/` (level cap, skill ranks, cosmetics, calling
   bias, endgame): decide, record reasoning, list in the report. Merge the
   story explorer. **Done** (SKILLS_DESIGN.md sections 14 and 15).
8. Two more cut-off notices.
9. **The current task** (2026-10-03 23:50), verbatim in substance:

   > New work in your area (combat systems). `origin/claude/vigilant-galileo-l6jqyx`
   > now has three cloud studies merged; merge that branch into yours first.
   > - `docs/bestiary/`: enemy roles, the roster, counters, hordes, depth. Its measurements:
   >   a crowd's danger is its biggest single blow; guards are the only hard counter;
   >   Seeking Motes and Arcweb are far ahead of every other skill, and Mirror Step is a must-pick.
   > - `docs/bosses/`: audit, survivors and ARPG bosses, mechanics, a 12-step build order.
   >   Its findings: the arena boss spawns as an elite, so no boss logic runs; Mark Prey
   >   executes it below 20%, and it drops no chest; it lives 16–20 s, and a weak build can
   >   kite Grimtunnel forever.
   > - `docs/cloud/balance-lab.md` with its raw sweeps, `tools/balance/compare.py`, and 4
   >   small tunings (lamplings, sappers, risen bowman).
   >
   > Treat them as input, not orders, and own the result. Do:
   > 1. **Bestiary quick fixes:** chilling a frozen creature keeps it frozen (frost locks
   >    even heralds), so add a thaw immunity window; poison on the survivor makes no sound
   >    or sign, so give it a read and credit deaths to poison correctly; champion guards at
   >    60%; champions ignore Mirror Step; reprice the blight and champions oaths. Test each.
   > 2. **The bosses' "day of fixes":** flag the boss as a boss (boss logic runs, no Mark
   >    Prey execute, the best chest); heralds stop playing the boss music; an entrance on
   >    camera; cone telegraphs drawn as cones. Then proceed through its build order as far
   >    as quality allows: fight-length governance, the Ford-Warden port, Grimtunnel, the
   >    telegraph language, and so on.
   > 3. **The bestiary's bigger ideas:** champion "Signs", the unused verbs (Orbit, Trail,
   >    Split, multi-shot) as new creatures, and signature events per people. Build those
   >    that make the game better, at the quality bar.
   > 4. **Balance:** run the full sweep (6 seeds, 45 min, both bots, using your drafting
   >    policies, not first-card) and decide on the lab's 4 tunings with data. Also address:
   >    the Barrow Lord's length; the endless phase's growth versus a Dawn at 60:00; the
   >    Pack and the Lamplings being easy; the passives being under-tested by first-card bots.
   > 5. **The open decisions:** the bestiary's 7 and the bosses' 10, overlapping on oaths,
   >    Signs and the endless phase. Decide each yourself with reasoning recorded in your
   >    design doc, since you own the area. Escalate only what truly needs the owner, with
   >    your recommendation. Include in the report any that change the story (e.g.
   >    Grimtunnel never dying in an arena, Keegan's duel timing, story outcomes from fights).
   >
   > The owner's "soul" and "perfection" bars apply: bosses and enemies with identity from
   > this world, not generic. Keep the tests green, commit and push often, and report
   > concisely with before/after numbers.

10. The handoff request (this document).

**When the current task is finished, report to the coordinator**:
concisely, with before/after numbers, the decisions, and the
story-changing ones called out.

---

## 4. What is done

### Skills and upgrades (tasks 1–8, finished)

Everything is described, with the reasoning, in `docs/SKILLS_DESIGN.md`
(17 sections). The commits, oldest first:

| Commit | What |
|---|---|
| `cc7f2d6` | `docs/SKILLS_RESEARCH.md`: the genre, game by game, then the lessons |
| `9bcbaf6` | the balance harness (`godot/balance`) |
| `a3aba70` | skills that do what they say; thin families filled |
| `dea997e` | the offer rebuilt (`Sim/LevelUp.cs`), day joined to night, unions, first tuning |
| `c900b1f` | the draft says why: paths, reasons, recipes, the arsenal, a skip key |
| `baefd41` | tests: the draft's promises, every recipe, path balance; the tome a choice |
| `728fc36` | `--give` takes ranks, evolutions and passives |
| `5ad7454` | great blessings by role (power, ward, answer, quickening) |
| `861d577` | kindled gear (items feed the ember), great hands dealt by role, a horde that melts |
| `58f3d8a` | the valley's own: skills named for its things, banked embers, the night's hours |
| `7394c5a` | each calling's own great blessing; riders for the plain passives |
| `befbdab` | one balance tool: the lab's sweep runs on the harness |
| `e13d65a` | a tier is three levels; the table's oaths in the harness; level thirty |
| `8bbeefe` | Dusk: a tier's strength comes in over the first three minutes |
| `c88620b` | a calling's own great once a night; balance probes take six seeds |
| `dd0ff09`, `6b4b909`, `590122b`, `01362b0` | SKILLS_DESIGN.md: soul, passives, decisions, numbers, open |
| `10cd381` | harness null view takes a bark's voice |

Final skills numbers (deft bot, story level, table oaths): tiers 1/2/3 won
97/92/90%; a tier above the survivor (level 10) tiers 4/5/6: 79/80/49%;
paths at tier 2: 82–100%; one skill's mean share 21% (was 39%); ember at
minutes 1/15/30: 6/31/50. Full table: SKILLS_DESIGN.md section 16.

### The current task (item 9), so far

| Commit | What |
|---|---|
| fast-forward to `e5bca09` | `origin/claude/vigilant-galileo-l6jqyx` with the bestiary, bosses, balance lab and story explorer merged in (no conflicts) |
| `f120ca2` | **Bestiary quick fixes, all five, tested** (`godot/tests/BestiaryTests.cs`, 6 tests): frost thaw window (a creature just thawed cannot refreeze for 3 s, a champion 5 s: `Enemy.ThawT`; more chill no longer refreshes Frozen); poison and burning on the survivor show a small coloured number once a second (`Ev.PlayerHit.Dot`), a quieter hurt sound, and a death by them is credited to them (`FellTo`, harness `KilledBy`); champion guard capped at 60%; champions and bosses see through Mirror Step (Ai.cs, Arts.cs Reflect); raised dead carry no ember (`Enemy.Raised`); oaths repriced in `Maps/MapOffers.cs` (blight Gear 1.6 with text, champions Gear 1.3); the Lamplings' champion and heralds are the digger `lampling` (closes) rather than the thrower |
| `6c3841f` | **The boss contract and four bosses** (details below; `godot/tests/BossTests.cs`, 12 tests) |
| `f5b6217` | `--minute M` for pictures of the boss; `ArenaRun.SkipTo(seconds)` passes over heralds and greats the skipped stretch would have brought |

**The boss contract** (`godot/logic/Play/Bosses/ArenaBoss.cs`):

- `IBossArena` (implemented by `ArenaRun`): the boss's view of its arena
  (spawn, can-stand, say, bark, horde share, won).
- `ArenaBoss`: three `Phase(Name, Mark, Floor, Ceiling)`; a phase ends at its
  health mark or its 60 s ceiling, never before its floor (15/20/15 s). The
  gate is `Enemy.HpFloor`: damage past the mark piles into `Enemy.Overflow`
  and comes out as the **Break** (`Ev.Break`, a big gold "BREAK N") when the
  phase turns. A transition is 2.5 s untouchable (`TakenMul 0`), a bit longer
  with a big Break. Soft enrage at 180 s (moves a quarter quicker, horde share
  back to 1); hard at 300 s (signature on a loop). Crowd control fills a
  **stagger bar** (`Battle.AddStagger`; stun, fear, charm, knockback, chill)
  instead of locking it: full = 3 s staggered, ×1.25 damage taken, then 18 s
  of resisting. Each boss names a **weakness** school; that school breaks its
  channel. Moves are `Hold`/`DashTo` plus shaped telegraphed blows
  (`Battle.EnemyBlow`: Circle, Lane, Cone, Band; dash i-frames slip them).
  `HealthMul(tier)` defaults to `12 + 2·tier` over the people's champion's
  health (×3 elite); `DamageMul` 1.3.
- The four (`ArenaBosses.cs`), three phases each, phase names in brackets:
  - **Pack-Mother** (`wolf_alpha`; Drive / Moon / Den), weakness fire: the
    Drive's crescent and lane, Hamstring cone + slow, the moon-howl channel
    with lanes (6% of her health or fire breaks it), lunge chains, the last
    pack ring; hard enrage halves the survivor's light.
  - **Barrow Lord** (`barrow_knight`; Drill / Testudo / Who Would Not Lie
    Down), weakness holy, `HealthMul 9 + 1.5·tier` (he was long): Close Up (a
    line of risen warriors), pilum lane, testudo ring and the century's
    charge lanes, gladius cone, "Hold!" band. At 1 HP he must be **laid
    down**: stand within 3 m for 3 s (holy halves it), or he rises with 25%.
  - **Grimtunnel** (`grimtunnel_roused`; Dig / Collapse / Boil), weakness
    frost: three lamps (red, blue, green) flare and break when hit while
    flaring (pools of 8% of his health); the Under (dash underground, burst
    on surfacing; frost catches him under); sinkholes (collision circles) in
    phase 2; moths; the boil's bands; the pick cone. **He never dies**: at
    the end he goes back down the hole (releases lamplings, a bark, the
    arena is won, his chest thrown up). The story keeps him for Act 3.
  - **Red Hand** (`enforcer`; Toll / Cages / Hand), weakness storm: the Toll
    rings and takes the best weapon for 8 s (`WeaponInst.DisabledT`) until
    his thief (a footpad elite, 12 s) is caught (storm on the thief makes it
    drop it); volley of five lanes; the cage (posts as colliders, a wall
    ring); the levy (bruisers); maul circle; sweep cone; the bell that "takes
    everything" for 6 s.
- The arena (`Play/Zones/ArenaRun.cs`): a sign two minutes out (`RunUp`, a
  bark per boss, a light on the edge at the bearing it will come from); the
  boss arrives 13 m away at that bearing (`Ev.Focus` turns the camera to it
  for 1.6 s), its 8 m cleared of the horde, ten of its people's first
  creature round it; the announcement names its weakness; horde held at 40%
  while it lives; `boss.Boss = true` (so Mark Prey's execute and every
  boss rule apply); its chest (`Ref "boss"`) holds 3 upgrades, 5 from tier
  3, +1 for a Break of 10% of its health, +1 if none of its telegraphed
  blows landed (`Battle.BossBlowsTaken`).
- View: telegraph language in `src/Fx/Palette.cs` and `src/Fx/BattleFx.cs`
  (amber `#ff9a1a` a blow, filled; violet ground, hatched; pale blue stand
  here, dashed; grey solid, hard edge; cones drawn by `ConeMark`; a move's
  name floats over it); the HUD bar (`src/Ui/GameHud.cs`) shows phase marks,
  stagger and Break; `Game.SetBoss` plays boss music only when
  `BossBar.IsBoss` (heralds pass `IsBoss: false`).

---

## 5. In progress, exact state

Nothing is half-made. The last thing done was a picture check of the Red
Hand (`--minute 29.95`, five frames): the boss arrives, the bar shows the
name, title and two phase marks, the horde is the Kerchiefs. **Not yet seen
on screen**: a cone telegraph (is `ConeMark`'s rotation right? the sim test
`A_cone_is_a_cone` proves the hit, not the drawing: `Rotation.Y =
atan2(cos angle, sin angle)` was reasoned, not looked at), the hatched,
dashed and wall textures, move labels, the BREAK number, the stagger strip,
the camera's turn to the arrival. The pictures were taken with an ember-1
build at minute 30 (so level-up panes cover frames as the ember pours in);
give a real build with `--give` and use `--auto` so the survivor fights and
takes its cards.

---

## 6. What is next, in order

1. **Look at every boss on screen** at full resolution (section 9 has the
   command). Check cones point where the blow lands, each telegraph kind
   reads, labels are legible, BREAK and the stagger strip show, the camera
   turns to the arrival, Grimtunnel's lamps and pits read, the Red Hand's
   cage posts and thief read. Fix what is wrong; commit.
2. **Teach the bot the bosses** (`godot/balance/Harness/Pilot.cs`) before
   any sweep, or the sweep measures the bot's ignorance: step out of
   `Battle.Blows` by shape (circle, lane, cone, band; it is public), stand
   over the Barrow Lord when he lies at 1 HP, chase the Red Hand's thief,
   hit Grimtunnel's lamps while they flare. A relaxed human does each of
   these after one death.
3. **Calibrate boss health** per boss with the harness: target 90–120 s at
   par, 45–60 s for an absurd build (the floors make about 50 s the least),
   an enrage for a weak one. Read `BossTtk` and `BossLeft` in the report.
   Before the contract, bosses died in 42–57 s by tier (16–20 s in the
   cloud probe).
4. **The full sweep**, as asked: 6 seeds, 45 minutes, both bots, drafting
   policies not first-card. Suggested:
   `arena --callings all --policies greedy,random,paths --seeds 6 --tiers 1,2,3 --level tier --oaths table --cap 46 --beyond 15 --bot deft --out out/full_deft.jsonl --csv out/csv_deft`
   and the same with `--bot plain`. **Gotcha**: peoples are dealt by seed
   (`peoples[(s + w) % 4]`), so 6 seeds give two peoples two runs and two
   one; run with `--people pack`, `dead`, `lamplings`, `kerchiefs` separately
   (or 8 seeds) for even coverage. Then use it to:
   - decide the lab's tunings, which are **in the code now** (lampling 16→20
     health, 7→8 damage; sappers weight 2.5→3.5 from minute 4; risen bowman
     cooldown 2.8→3.3 s, damage 7→6; in `Content/Enemies.cs` and
     `Maps/MapOffers.cs`): keep or revert each with numbers;
   - the Pack and the Lamplings being easy (96–100% in the lab): the
     bestiary's ideas (Signs, the Wick, the Ridge-Runner, signature events)
     are the better lever than more health;
   - the Barrow Lord's length (now `9 + 1.5·tier`; re-measure with the
     lay-down);
   - passives under-tested: the report's card table compares runs that took
     a card by minute 15 against those that had not; read it for passives
     under greedy and paths.
5. **The endless hour**: decide the Dawn at 60:00 (my recommendation: yes,
   see section 7), build it if so (a line of daylight crossing the arena
   from 55:00; the ember drains; the run ends with the dawn's reward).
6. **The bestiary's bigger ideas** (`docs/bestiary/COUNTERS.md` §4,
   `ROSTER.md`, `HORDES.md` §3–4, `IMPLEMENTATION.md`):
   - champion **Signs** (one-verb affixes with a tell and two answers each;
     eight build from verbs the code has), none at tier 1 before minute 10;
   - **new creatures from the unused verbs**, with existing visuals only:
     Ridge-Runner (wolf + Orbit + Lunge), Slurry Sow (boar + Trail), Bone-Heap
     (skeleton warrior at scale 1.5 + Split), Wick (lampling at 0.75, packs),
     Levy Crossbow (a Kerchief shooter, multi-shot 3). The Lamp-Pole and the
     Blasting-Cart need art: ask the art session, do not make it;
   - **signature events** per people (the Ring, the Ford Rises, the Shield
     Wall, the Dig Opens), each with a tell, about three times a run;
   - **telegraph caps** (wind-ups, burrowers, bursts, enemy ground) like
     `RangedCap`.
7. **The rest of the bosses' build order** (`docs/bosses/IMPLEMENTATION.md`
   §4): the Kindling at minute 15 (an ember-core and the boss's lieutenant;
   break the core in time and the great blessing is drawn from four); the
   **Ford-Warden** echo port (`Play/Zones/Prologue.cs` `WardenTick`, line
   ~222) as the first echo at the Wayfinder's table; **oaths on bosses**
   (`MapRules.StaggerTaken` exists and `AddStagger` reads it; no oath sets
   it yet: the iron oath should); boss telegraphs drawn above the survivor's
   effects and the survivor's effects dimmed while a boss lives.
8. **Record the decisions** (section 7) in `docs/SKILLS_DESIGN.md`, as a new
   section "Enemies and bosses" before "Before and after", each with **Why
   this is the answer**; add the boss and bestiary rows to the before/after
   table; update "Open".
9. **Report to the coordinator** (concise; before/after; decisions; the
   story-changing ones).

---

## 7. Decisions: made, and my recommendations for the rest

### Made (and built)

- **Items plan's five** (SKILLS_DESIGN.md section 14): level cap thirty;
  skill ranks and the Edge; cosmetics; calling bias as a lean; the endgame.
  Read the section for the reasoning.
- **Kindled gear** folds item affixes into the draft (a level, a redraw, a
  banishing, a fourth card, a fourth great choice, a stand-in for a passive
  at rank 8) instead of a parallel stat system: one system, and gear has a
  night-time identity.
- **One balance tool**: the lab's arena sweep delegates to the harness
  (`BALANCE_LAB=arena`); the lab's story walk stays its own.
- **Bosses are scripts on a contract**, not more health: the cloud probe
  showed 16–20 s lives and a kited Grimtunnel; health alone drags slow
  builds past two minutes while fast ones still skip it. Floors, ceilings
  and the Break let fast builds be shown off and slow builds be paced.
- **Crowd control staggers a boss, never locks it**: the bestiary measured
  frost holding even heralds for good.
- **Grimtunnel never dies in an arena**: he goes back down the hole and the
  arena is won (bosses decision 5). **This changes the story's surface**:
  report it; the bible keeps him for Act 3, so this follows the story.
- **Clear and thin**: clear 8 m round the entrance, hold the horde at 40%,
  full at the soft enrage (bosses decision 2).
- **Mirror Step**: kept strong against the crowd; champions and bosses see
  through it (bestiary decision 2).
- **The Lamplings' champion** is the digger now; the Blasting-Cart when its
  art exists (bestiary decision 7).

### To decide and record (my recommendation, and why)

Bestiary (`docs/bestiary/README.md`, "Decisions for the owner"):

1. *Enemy hazards hurt the horde?* Yes, at half, for hazards the horde makes
   (pots, death bursts, burning ground from creatures), not oath ground.
   The sweaty player gets tools, the relaxed one loses nothing, the oaths of
   embers and ruin keep their price.
3. *Signs, how many and how soon?* The proposal: none at tier 1 before
   minute 10, one at tiers 1–3, two from tier 4, three on late heralds.
4. *Contested ground?* Keep it for the endless hour (or a tier-4 oath): the
   first half hour teaches one people's question at a time.
5. *Thieves?* Ember stones on the ground only, never what is held; caught,
   the thief drops all of it and a purse. The Red Hand's Toll (a weapon for
   8 s, won back by catching the thief) is a boss's verb and recoverable.
6. *Weight as a number?* Yes, beside the words (Hades' heat): planners need
   the sum; the words keep the flavour.

Bosses (`docs/bosses/README.md`, "Decisions for the owner"):

1. *Fight length*: 90–120 s at par, held by floors and ceilings, the
   surplus shown as a Break. Built; calibrate (section 6, step 3).
3. *A boss takes ember: do cards go?* No. The bar and the level step back;
   the build stays (the Mithrix lesson).
4. *The endless hour's end*: **the Dawn at 60:00** (the bible: the ember
   drains at dawn). **Escalate**: the original brief says "endless play
   after the win", so ending it is the owner's call; recommend yes.
6. *Keegan's duel at first light or by night?* Story and day half, not
   mine. **Escalate** with the bosses doc's recommendation (first light, by
   her own handbook's rule, a day fight without ember).
7. *New story outcomes from fights* (Greymuzzle let go, the Roost's crates,
   Edric lost, the pump): **escalate** to the owner and the writers; none
   are built. Recommend accepting Greymuzzle let go (it fits the Pack-Mother
   fight's shape) and leaving the rest until their zones exist.
8. *Banes shown or secret?* Learned by day, recorded in the bestiary once
   seen, never hidden for good. The weakness is already named on arrival.
9. *The Silver Penitent?* Yes, last, behind a flag (not started).
10. *Oaths on bosses?* Yes, lightly: each oath changes the boss in one
    visible way (iron: `StaggerTaken` halved, and so on); the horde carries
    the rest.

Escalate to the owner only 4, 6 and 7 (and confirm 5, which is built).

---

## 8. Tried and failed, and why

- **Probe-only tuning** over-nerfed area skills (Dawnpulse, Hallowed): the
  probe's crowd shape favours whichever skill it suits (a wide circle
  favoured projectiles, a tight one melee, a dense one novas). Fixed by
  arena-like spawning, a moving pilot, and blending probe numbers with whole
  arena shares (`tune_blend.py`).
- **The plain bot stood in boss combos** and made fragile ranged builds look
  worse than they are: the pilot now gives ground round a champion at arm's
  length. Expect the same with the new boss blows until step 2 above.
- **Boss floors first failed** (the scripted boss died in 30.7 s): `PhaseT`
  was not reset on a new phase and the last phase was ungated. Fixed: the
  last phase holds at 1 HP until its floor (`e.HpFloor = DiesAtZero &&
  PhaseT >= ph.Floor ? 0 : 1`).
- **ArenaTests that one-hit the boss** broke with the contract; they now
  call a `Defeat(s)` helper that fights it through its phases.
- **Balance tests flaked** (a timed MapGen test under parallel probes; RNG
  in grave and storm crowds): the balance collection runs alone
  (`[Collection("Balance")]`, `DisableParallelization`), six probe seeds.
  `BossTests` is in that collection too.
- **The lab's Kerchief pillager and stalker tunings** were reverted by the
  lab itself on main's numbers; do not re-apply them.
- **Rare droughts** of twenty levels under the first offer rewrite: fixed by
  a hard rare floor (10) and protecting kept cards from the advancing swap.

---

## 9. Gotchas

- **Godot**: console exe
  `C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe`.
  Build first: `cd godot && dotnet build SurvivorUnchained.csproj -v q`.
  A boss picture:
  `"$GODOT" --path . --resolution 1920x1080 -- --quick warden --zone arena --people kerchiefs --tier 2 --minute 29.95 --give "oathblade:6,dawnpulse:5,+might:3" --auto --shot boss_rh --seconds 9 --every 1 --count 8`
  (frames land in `godot/.shots/`, which is not committed). `--auto` lets a
  crude player drive and take cards (`src/Game/Autopilot.cs`); `--auto idle`
  only takes the cards and stands still. Peoples: `pack`,
  `dead`, `lamplings`, `kerchiefs`. See `docs/HANDOFF.md` for `--auto`,
  `--horde`, `--cam`, `--cast`, `--blast`, `--drops`. A shot taken before the
  game is up shows a draft pane: `--give` and `--minute` clear owed greats.
- **`godot/assets`** must be a directory junction to `public/assets` (it is
  in this worktree). In a fresh worktree, from its root, in PowerShell:
  `Remove-Item godot\assets; cmd /c mklink /J godot\assets public\assets; git update-index --skip-worktree godot/assets`,
  then `--headless --path godot --import` once before screenshots.
- **Godot import rewrites `.import` files** under `godot/art` etc.: never
  commit them; `git checkout -- godot/art godot/data/zones godot/icon.png.import`.
- **Tests**: `cd godot/tests && dotnet test` (about 35 s, 453 tests).
  `Tests.csproj` compiles `../balance/Harness/**`, so a harness change can
  break the tests.
- **The harness** (`godot/balance`): `dotnet build -c Release`, then
  `dotnet bin/Release/net8.0/Balance.dll arena|probe|weapons|report ...`
  (SKILLS_DESIGN.md section 15 has the commands and what each reports).
  While a long sweep runs, it locks `bin/Release`: build anything else with
  `-o bin/probe` and run from there. Long sweeps: run in the background
  (`run_in_background`) and write `--out out/NAME.jsonl`; `report --in` re-reads
  one. `--cap` is the run's last minute (default 40), `--beyond` the minutes
  played after the boss falls. `ARENA_TRACE="calling/policy/tN/people/sSEED/wW@MIN"`
  prints one run's blows. `BALANCE_LAB=arena LAB_SEEDS=6 dotnet test --filter BalanceLab`
  runs the lab's sweep through the harness. `tools/balance/compare.py`
  compares two lab sweeps.
- **The cloud probes** in `docs/bestiary/probe` and `docs/bosses/probe` are
  separate console projects the cloud sessions used; prefer the harness.
- **The shell sandbox** refuses bash commands it cannot prove stay in the
  worktree (`cd` into another directory plus a heredoc, shell variables
  with git, `cmd /c`). Write Python scripts to the scratchpad with the Write
  tool and run `python path/to/script.py`; keep git commands plain.
- **Bash heredocs** turned `\\n` into newlines once in C# sources: use the
  Edit tool or a Python script for code edits.
- **The scratchpad** is shared with other sessions of the coordinator
  (`C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad`):
  name files distinctly.
- **Boss tests** start a fight with `b.Time = 30 * 60 - 0.05` and step the
  zone, battle, host and frame together (`BossTests.At30`); copy that for
  new boss tests.

---

## 10. Collaborators

- **The coordinator** (the main session): relays the owner; talk only by
  the final report. Integration branch: `claude/vigilant-galileo-l6jqyx`.
- Other agents (by id, with their worktree branch
  `worktree-agent-<id>`), whose areas you must not edit:
  - `ad1a039caf3923eec` UI research and design overhaul (draft and HUD
    panels: when you change `src/Ui/*`, keep to their look);
  - `abd496197891ea843` UI artwork;
  - `a50313d92b0c7aba2` the animation set;
  - `a69687764fdd5047c` story writing, Act 1 (with `adf97e52f8dfede35`, the
    story editor); `a473fbc4762172b02` story phase one;
    `a26f4d6a900ab8201` the writing spec implemented; `a599a56175d28f702`
    the story audit;
  - `a2da9a388ceb1b987` voice-over; `a0597738c6356970f` voice evaluation.
- Cloud sessions (finished; their branches are merged):
  `claude/cloud-bestiary`, `claude/cloud-bosses`, `claude/cloud-balance-lab`,
  `claude/cloud-story-explorer`.

---

## 11. Read these first

1. `docs/SKILLS_DESIGN.md`: the design, the reasoning, the numbers, the open list.
2. `docs/bosses/README.md`, then `docs/bosses/IMPLEMENTATION.md` (build order, §4) and `docs/bosses/SURVIVORS_BOSSES.md`.
3. `docs/bestiary/README.md`, then `docs/bestiary/IMPLEMENTATION.md` and `COUNTERS.md` §4 (Signs).
4. `docs/cloud/balance-lab.md`: the lab's sweeps and tunings.
5. `godot/logic/Play/Bosses/ArenaBoss.cs`: the contract.
6. `godot/logic/Play/Bosses/ArenaBosses.cs`: the four bosses.
7. `godot/logic/Play/Zones/ArenaRun.cs`: the arena (horde, ladder, heralds, run-up, boss, chest).
8. `godot/logic/Sim/Battle.cs`: hits, statuses, stagger, `EnemyBlow`, hooks (large; search for what you need).
9. `godot/balance/Harness/Pilot.cs` and `ArenaSim.cs`: the bot's hands and the run it plays.
10. `godot/tests/BossTests.cs` and `BestiaryTests.cs`: how the new rules are held.

Also: `godot/logic/Sim/LevelUp.cs` (the draft), `godot/logic/Content/Paths.cs`,
`Maps/MapOffers.cs` (peoples, oaths, rules), `src/Fx/BattleFx.cs` (telegraph
drawing), `docs/HANDOFF.md` (the game's run options).
