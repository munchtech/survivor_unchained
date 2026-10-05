# Handoff: combat (skills' mechanics, enemies, encounters, bosses, balance, the maps, the story's nights)

Written by agent `a5115633c7006e4d4` for its successor, at the context limit.
- **State:** everything is committed and pushed on `worktree-agent-a5115633c7006e4d4`, merged with the integration branch `claude/vigilant-galileo-l6jqyx` at `917d1a96`.
- **Tests:** 681, all green.
- **Predecessors:** `afe45df4957917614`, `a708da2c97bf85c95`, `a1d4562f44c7f6feb`, `ac4ec5bbd2763a0df`, `a09c5a65f5a84319e`. What they knew that still matters is folded in below.
- **The machine:**
  - **Heavy work takes turns:** `python C:/Users/munch/Desktop/survivorsunchained/tools/turn.py take godot "combat: <job>" --wait 20`, then `give godot "<same>"` when the run ends.
  - **The rules changed on 5 October:** `godot` has three slots, Blender takes `blender`, and `gpu` is only ComfyUI, TRELLIS and MoGe. Waiters are served in the order they first asked, so keep `--wait 20`.
  - The balance harness and `dotnet test` need no turn.

---

## 1. The owner's words

- **The bar:**
  - "AAA standard", "strive for excellent, above and beyond", "I don't want to polish, I want to create perfection", "do we have soul?", "we are striving for perfection".
  - Ask whether it is the best version of this in any game. Check it at full resolution. Don't stop to ask.
- **Story nights:**
  - "much more specialized and fun - smaller arena - and they don't need endless - they have proper arpg end bosses right?"
- **Getting up:**
  - "GET UP TWICE IS TOO GENEROUS. get up once i guess is ok? but only in early game ... thats a balancing nightmare".
  - "the trait can just be a skill/spell right - can get it in arenas or learn it for story etc".
- **The owner's decisions** (top of `docs/design/STORY_NIGHTS_AND_TIME.md`):
  - a loss wakes her at Chid's a day on;
  - Redcowl can be spared or killed;
  - several fights a night, only by intent;
  - one rise, in Act 1 only; after that only with the rise skill (Not Yet, or Cold, Then Not).
- **Endless:** "endless is truly endless". **Encounters:** "variety of minion types elites and mini bosses". **Structure:** "story should be 40% of the game early on."

## 2. The brief (as given to me, and where it stands)

You own skills' mechanics, enemies, encounters, bosses, balance, the maps' mechanics and the story's nights. Others own the night's shape and staging (experience), the words (story), and the places' look (arena art).

1. **Get the Hollow and the Roost seen.** Done once at 1920x1080 (section 3.1); keep going with the experience director.
   - Greymuzzle's first-try kill rate is now measured honestly (3.2).
   - The Roost's way in dips too much still (3.3).
2. **The Dig and the Vault.** The Dig is built and half tuned (3.4). The Vault is next (4.2).
3. **The queue:**
   - the cinematics hooks;
   - kerchief_crossbow for the levy;
   - the run-ups re-measure;
   - the Kerchiefs at tier 3;
   - the Lamplings;
   - the bestiary (4.3).

## 3. Done (this lead)

### 3.1 Seen at the screen (1920x1080, the game's autopilot, which is deft BossSense)

Frames are in `scratchpad/combat5/`:
- `gm_lunge.jpg`, `gm_moves.jpg`, `gm_rest.jpg`: Greymuzzle's every marked move, from `--on boss`;
- `roost_cage.jpg`, `roost_camp.jpg`, `roost_ruts.jpg`: the Roost's way in, a frame every 3 s;
- `rise_mid.jpg`, `rise_all.jpg`: Cold, Then Not.

Findings, and what was done:
- **Greymuzzle's lanes read.** His ring did not read as a wall: twenty wolves 4 m apart at the picture's edges.
  - It now stands 30 strong (`RingWolves`).
  - A pale Wall-kind dashed line (`RingMarks`, 36 dashes) marks where a further step is a shove, and bows round lit fires.
  - Both are to be judged.
- **The Pack's turn** converges three lanes on her: a six-spoked star. It reads as "get out of the middle".
- **The drive's first lesson** is now said alone, with the banner and no bark, during a 1.0 s crouch. Then the 1.7 s lane follows (`Drive.sayT`, `Mark()`).
- **`--stage N`** now hands her the skipped stages' ember floors and the night's first great blessing (`StoryNight.SkipTo(stage, floors: true)`). Tests keep the old behaviour.
- **The Roost is unbuilt.** Every space reads as one dark field with red seams, so the locks, the door and the camp read as a crowd fight. Arena art has the outline queued after the Hollow, the Dig and the Barrow.
- **The rise.**
  - Killing blow to first body catching is about 1.2 s of real time: the 0.35 s `RiseCold` runs inside Game's `Slow(1.1)`.
  - The front catches each body visibly as it passes.
  - Skills set `RiseCold` to 0.25 (done) and are redrawing the cold as a held beat. They will judge it at the screen.
- **The experience director's verdict on the Hollow:** "the shape is right, it is soft throughout, and the drive's lesson is crowded". Their autopilot never dropped below 91%.

### 3.2 The harness, mended: what the old Hollow numbers were measuring

- **The first meeting** (`BossSense.Meeting`; `StoryRunSpec.Meets`; `--learned` turns it off). BossSense is "what anyone does after dying to a boss once", but the harness used it on the boss's first life, so the target "first life 55–70%" could never be met without breaking "won ≥90%".
  - On the first life, plain and naive hands notice each named move half as often the first two times it is marked (`Lessons` 2, `NewNotice` 0.5).
  - They act on a boss's own answers (the cold's fires, the cage's far post, Snib's barrel) only after `ReadFor` 3 s.
  - A fall at the boss teaches it: the meeting is dropped.
- **Noticing was decided by the blow's shape and place only,** so Greymuzzle's opening lunge from the same spot was unnoticed after every rise and in every run. `EnemyBlow.At`, the battle time, is now in the hash.
- **The ring's steering (a big one).** `BossSense` tested `p + m*1.5` with an un-normalised way, so a way of 13 m toward a boss beyond the ring read as "into the wall" every step. That spun the hands at the den's exact middle (19,-25) for the whole fight.
  - It happened to be the safest spot in the Moon, so the old Hollow numbers were flattered.
  - Fixed by normalising. The guard before the den is now a wall to the hands too (round its ends).
- **Strikes.** On a story night's way in, plain and deft hands now read the crowd's marked circles: a brute's slam, a burst's fuse (`Battle.EnemyStrikes()`, `Pilot.Steer(strikes)`, StorySim only). The table nights are measured as before.
- **Places hold their foes.**
  - `StoryNight.Strays` now brings back any named foe or the boss: outside the open ground, or past the shut gate (`PastGates`).
  - It sends them to free ground near the place's points.
  - Knockback now stops at walls (`Ai.cs`, `Collision.Resolve` after the slide).
  - Before this, Whitethroat ran her lane out through the den's wall, and Grimtunnel was knocked through the shut gate. Each left about 1 in 30 nights stuck until the cap.
- **Gaps** (`Collider.Gap`, `Resolve(overGaps)`): the crack and sinkholes hold walking, and a dash carries over them (`Battle` dash, `ArenaBoss.OverGaps`). BossSense dashes over a gap that lies right ahead.
- **Trace aids:**
  - `FellAt` (each fall: phase, fight seconds, what was left of him, her max) and `MaxHpAtBoss` in the JSONL;
  - hit labels in `STORY_TRACE`;
  - `PICKUP` and `PILOT` lines in the `STORY_TICKS` window (`Pilot.Debug`).

### 3.3 The numbers now (64 nights a row, plain hands, tiers 1–4)

See `docs/team/combat.md` for the latest table (r4).

Before r4:
- **The Hollow, with the hands fixed and the first meeting on:**
  - won 48–67% and first life 45–59%;
  - deaths in the Moon (phase 2) from walking into the guard;
  - the guard was then made a wall, and r4 measures that.
- **The Roost:**
  - won 72–92%, first life 66–86%;
  - **under half on the way in 33–59% (target 20–35)**: stage 3, the levy and the Pike-Captain, 20–39% by calling; stage 2 12–36%; stage 1 10–31%;
  - stage falls 4–6 of 1024.

**The rise still rarely saves a bot at the boss:**
- 10–30% of those who fall there win after the rise.
- With the first meeting the second life should do better. Watch `rise.py` after r4.
- If it doesn't, the falls are the build's: a 120–160 HP stalker against blows of 60–75.
- **Consider scaling the story bosses' blows to her health band** before you push the first-life rate any lower.

### 3.4 The Dig Boils Over: built (`Play/Story/Dig.cs`, `Play/Bosses/GrimtunnelStory.cs`)

- **The place.** `DigBoilsOver.Ground`; draw it with `place --fight dig`. Four spaces up the screen:
  - the edge, a circle at (-14,24), r 10;
  - the tub-way, a strip at x -14 from z 6 to -14;
  - the pump, a circle at (-12,-29);
  - the lip, a circle at (13,-27), r 12.5. The crack runs from (10.2,-20) to (16.8,-34). Snib's perch (23,-36) is on the heap, outside.
- **The edge.**
  - Three windlasses (`StandBy`, Takes 9). Each shaft boils lamplings every 7 s, at most 8 times.
  - A broken one's shaft falls in: a 2.8 m ring, 1.2 s, then a hole.
  - The Wick-Mother (×3.6, teeth ×0.55) comes up from the next shaft after the first breaks. The stage ends when the windlasses are broken and she is down.
- **The tub-way.**
  - Tubs run on their own clock (5.5 s), down the rail nearer her. Each lane is 1.5 s, B.MaxHp×0.22, and flattens lamplings on it.
  - The Chucker (×4, teeth ×0.4, Speed 0, range 18) keeps the roof, out of reach, while 10 tubs run. Then he can be reached, at ×0.25 beyond 11 m.
  - The goal is the tub-way's middle while he's on the roof.
- **The pump.**
  - Running: the Perfect of Fuses (×3.4, teeth ×0.45) stands on the steps out of reach for 8 waves of 3 fuse-runners, 9 s apart. Then he comes down.
  - His fall rolls the crate into the pump: a 10 m ring, 3 s, MaxHp×0.45, everything in it dies.
  - Stopped: the Lamplighter, the same way, with lamp-throwers.
- **Grimtunnel** (HealthMul 95, DamageMul 1.3, phases 0.65/0.30 with floors 25/30/25):
  - lamps every 7 s (a red, blue and green verb, as the table's; each lamp is 8% of him, broken while it flares);
  - Under every 12 s: a homing mound for up to 3 s at half damage. Frost brings him up at once, dazed 8 s; otherwise he bursts (3.5 m, ×2.0) and is dazed 4 s.
  - moths every 20 s (12 s when soft);
  - **The Collapse:** sinkholes as gaps, 5 + tier of them. Snib's barrel from 55% hp, every 25 s: kicked by walking into it, it blows on him for 10% and cracks his hide (×1.25 for 12 s); left 12 s, he throws it (4 m, 2 s, ×3.5).
  - **The Heart:** the crack opens as gap colliders; the heart's pulse runs in three bands; a temper of ×1.33 speed and his pick.
  - **Hard enrage:** the floor caves 2 m every 10 s (an `IBound`). His end: down the crack, hang, drop; `S.Ended(spared: false)`.
  - **The bane:** his lamp (`grimtunnels_lamp`), set down by a prompt. His next two Unders come up under it, dazed 8 s.
- **Measured** (`dig10`, 32 a row, tiers 1–4):
  - won 53–91%, first life 44–88%;
  - way in 3.8–4.5 min (stages about 80/75/92 s), boss 3.0–5.6 min, night 7.2–10.2;
  - **dips 31–56% (high: the Chucker's pots, the pump's bursts)**;
  - **16 of 256 still run to the cap at the boss** (phase 3 with a weak random build; the hands can't find him across the crack).
- **What's left on the Dig:**
  1. the cap runs: trace one (`dig10.jsonl`, key in `rep.py`'s list);
  2. the dips;
  3. the second lives;
  4. tests like `RoostTests` (none yet);
  5. naive and deft hands;
  6. seen at the screen (`--night dig`; take a Godot turn).
- **The words:** §23.2, all in, including story's four later lines (the Chucker coming down, the windlass prompt, the shut sight, the drive banner).

## 4. In progress, and next (in this order)

1. **Re-measure the Hollow and the Roost** with r4's fixes (`out/r4.jsonl`, `python scratchpad/combat5/rep.py r4 boss`).
   - The Hollow's first life should sit in 55–70% and won with the rise ≥90% (planned). If won is low, see 3.3's note on her health band.
   - **The Roost's way in:** stage 3, the levy and the Pike-Captain, are the biggest share of the dips.
2. **Finish the Dig** (3.4's list), then **the Vault** (`STORY_BOSSES.md` §4, `WRITING_PASS.md` §23.3; shut sight "Behind you, a rank of the dead steps across the hall."):
   - the Decurion's shield line (`Levy` fits it);
   - the Scorpion down the hall (cover stops his bolts);
   - the three standards as parts (holy and fire ×1.5; `bane.pole` lifts one);
   - the Barrow Lord: Iungite lines, pilum lanes that stay as cover, Testudo with the standard, the front as an `IBound`, the lay-down circle (holy twice as fast), the hand at the gate.
   - Defs: `mb_decurion`, `mb_old_quarrel`, `mb_ford_bell`, `boss_dead`, `risen`, `risen_warrior`, `risen_archer`, `legionary`.
   - Start Health ~95, DamageMul ~1.6, and measure.
3. **Cinematics' boss hooks.** The new lead is `a7a4c20bcfd7ccfd3`; the contract is `docs/cinematics/README.md` §6 item 11a.
   - Pass marks to `G.Cinematic`: `boss` [x, z, heading], `her` [x, z, heading], and for C10 `den_mouth`.
   - Play the spared part at the choice (`Greymuzzle.Choose(true)`, Redcowl's), with the cinematic owning the walk and releasing him in the done callback. Keep today's walk when `CanCinematic` is false.
   - Ids: `c10_arrival/_end/_spared`, `c11_arrival/_end/_spared`, `c11_again`, `c12_arrival/_end`, `c13_door`, `c13_arrival/_end`.
   - Message them when it's done.
4. **Animation (`a7dd95d00c4a6a017`).** Done: the plants (`Ai.SlamPlant` 0.65, `ShotPlant` 0.7), and `levy_crossbow` and `mb_levy_sergeant` on `kerchief_crossbow` (in `EncounterTests`' rigs). They will check both in the game with `--on casts` once this merges.
5. **Queued from before (none started):**
   - the run-ups re-measure (`combat-wip-runups@e63e74fd`, not merged; target 10–20% of runs under half per run-up, 3–5% under a quarter; `python tools/combat/stretches.py`);
   - the Kerchiefs at tier 3;
   - the Lamplings not separating careless from planned;
   - the bestiary (ground hazards hurting the horde at half; the Ford-Warden echo; weight as a number; the Signs Warded, Mending and Leader; Echoes in the long night; maps above tier 3).

## 5. Decisions (why)

- **A boss's first life is measured as a first meeting.** It is what a first try is, and the only way "first life 55–70%" and "won ≥90%" can both hold for hands that would otherwise never learn.
- **Hands that can't do what a relaxed player does are fixed before the boss is tuned to them.** Bots walking into marked slams, being pinned by bad steering, or reaching for a boss out of reach all made the numbers lie.
- **Named foes, bosses and shut gates are held by the night, not by each script.** A goal out of reach is a night that never ends.
- **Dashes carry over gaps; walls stop knockback.**
- **Inherited and holding:**
  - no padding: a stage's length comes from beats with their own pace (cadences, bounded counts, a roof held for N tubs, waves from the steps), never health alone;
  - every tier is the same night;
  - a boss's teeth are in its marked moves, and between moves it stalks with a nip;
  - the boss comes on his ground and the way back shuts;
  - one rise a fight;
  - a story's outcome is never decided by the build by accident (crates by prompt, windlasses and posts by where she stands, the lamp by a prompt).

## 6. Tried and failed, and why

- **The Chucker's goal left empty while he held the roof:** the hands never left the edge, and the tubs only ran with her on the rails. Deadlock. The tubs now run on their own clock, and the goal is the tub-way.
- **Strays sent home to a place point:** the points filled up with the boss's own holes and the crack, so home came back (0,0) and nothing moved. Free ground is now searched round each point.
- **The crack's ends 3 m from the wall:** the boss was pushed out of the crack through the wall. They are now 4.5 m in.
- **The heart's temper quickening the lamps and Unders too:** phase 3 killed nearly everyone. Only his pace and pick are quickened now.

## 7. Gotchas

- **The worktree-isolation guard:**
  - it refuses Bash that `cd`s and then runs a heredoc or a shell variable;
  - use the Edit tool, or scripts in the scratchpad run by absolute path;
  - `python - <<EOF` after a `cd` is refused.
- **CRLF:** git has `autocrlf=true`; the working tree is CRLF and the index LF. Python rewrites are fine.
- **The Godot import:** a fresh worktree needs `godot/assets` made as a junction to `public/assets` (skip-worktree), and the `.godot` cache copied from another worktree with robocopy.
  - Then run `Godot_console.exe --headless --path <wt>/godot --import` once, or new assets fail to load.
  - It touches many `.import` files: don't commit them.
- **Pictures:**
  - `scratchpad/combat5/play.py NAME --timeout S -- <game args>` runs at 1920x1080; frames land in `godot/.shots/`.
  - `--on boss` takes a frame after every boss move. `sheet2.py OUT COLS WIDTH PREFIX tags... [--crop]` makes contact sheets.
  - Game switches: `--quick warden --sex female --night hollow|roost|dig --stage N --auto`; `--fall-at T` with `--give "+from_the_ashes"` and `--auto` for the rise (without `--auto` the draft sits open).
- **The harness:**
  - `dotnet build -c Release` in `godot/balance`, then `dotnet bin/Release/net8.0/Balance.dll story --fight hollow,roost,dig --tiers 1,2,3,4 --seeds 16 --bot plain --policies greedy,random --par 12 --out out/X.jsonl`. That is 1024 nights in about 10 minutes.
  - Don't rebuild while a run holds the DLL.
- **Summaries:** `scratchpad/combat5/rep.py NAME [hurt-part...]` prints, by fight, tier and draft:
  - won, first life, under half on the way in, and under a quarter;
  - way in, boss and night minutes, and stage falls;
  - the rise's saves, dips by stage and calling, cut-offs, falls by phase, and her max HP at the boss.

  It wraps `an.py` and `rise.py`.
- **Traces:**
  - `STORY_TRACE=<key>` gives a line every 5 s with the boss's state, and every hit with its label;
  - add `STORY_TICKS=<seconds>` for quarter-second lines, plus `PILOT` (the hands' choice) and `PICKUP` lines, over 8 s.
- **Grimtunnel's def:** his firepot lob is removed in `Enter(0)` (a cloned def). The red lamp is his lob now.
- **`IStoryArena`** gained `Piece(id, scale)`, a moving kit piece (`IZoneLook.Piece`, `PieceView`), and `HeightAt`.

## 8. Collaborators (live roster in `docs/team/README.md`)

- **Experience director (`a9f0d6c64d891d56d`):**
  - judges feel;
  - their Hollow verdict is in 3.1;
  - they changed `BattleFx` (a named move drawn at a boss's strength; lanes fill as they come);
  - send them each change with frames.
- **Arena art (`aba487928a1515c93`):**
  - has the Roost's outline (queued after the Hollow, the Dig and the Barrow);
  - set `HollowByNight.PlaceBuilt => true` on their branch: their pieces inside the outline had been stripped;
  - send them the Dig's outline (3.4) and, later, the Vault's;
  - the den's mouth stays at (21,-39).
- **Story (`a7ba8903f4c8261b1`):** three Dig slots and the drive banner are with them (3.4).
- **Skills VFX (`abc6bbe020c7fe287`):** the rise's beat (0.25?), and looks for Grimtunnel's mound, the tubs, the barrel, and the crack and holes.
- **Animation (`a7dd95d00c4a6a017`):** the plants are done; kerchief_crossbow next.
- **Cinematics (`a7a4c20bcfd7ccfd3`, new):** the boss hooks (4.3).
- **Crafting (`ab0b263c720bdbda8`, new):** changed `MapRun.OnLoot` (material only from carriers; lamplings drop iron on maps). I said fine.
- **Loot (`a9a9c345a35e1fcad`):** owns drop rules, with a legendary certain from the first story boss she beats. Coordinate drop moments with them; nothing has been done yet.

## 9. Files to read first

1. `docs/team/combat.md`, then `docs/design/STORY_BOSSES.md` §0 (targets, contract) and §3–4.
2. `godot/logic/Play/Zones/StoryNight.cs` (Strays, SkipTo, PastGates); `godot/logic/Play/Story/StoryFight.cs`, `Hollow.cs`, `Roost.cs`, `Dig.cs`, `Levy.cs`.
3. `godot/logic/Play/Bosses/BossSense.cs` (Meeting, IBound, the barrel, gaps), then `Greymuzzle.cs`, `Redcowl.cs`, `GrimtunnelStory.cs`; the table's `BarrowLord` in `ArenaBosses.cs` for the Vault.
4. `godot/balance/Harness/StorySim.cs`, `Pilot.cs`; `godot/balance/Program.cs` (`story`, `place`).
5. `godot/tests/StoryNightTests.cs`, `RoostTests.cs` (the model for DigTests).
