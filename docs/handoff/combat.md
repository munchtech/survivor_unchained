# Handoff: combat (skills' mechanics, enemies, encounters, bosses, balance, the maps, the story's nights)

Written by `a739d6792d21f5efd` for its successor.
- **State:** everything is committed and pushed on `worktree-agent-a739d6792d21f5efd`, merged with `claude/vigilant-galileo-l6jqyx` at `eea25c28`.
- **Tests:** 733, all green.
- **Earlier leads:** `a5115633c7006e4d4` and before. Their handoff is in git history (`git log -- docs/handoff/combat.md`) for the deep detail of the story nights' runtime.

## 1. The owner's words

- **The bar:**
  - "we are striving for perfection";
  - "AAA standard";
  - "I don't want to polish, I want to create perfection";
  - "do we have soul?"
  - Ask whether it is the best version in any game, check it at full resolution, and don't stop to ask.
- **Story nights:** "much more specialized and fun - smaller arena - and they don't need endless - they have proper arpg end bosses".
- **Decisions** (top of `docs/design/STORY_NIGHTS_AND_TIME.md`):
  - a loss wakes her at Chid's a day on;
  - Redcowl can be spared or killed;
  - one rise in Act 1 only, and later only with the rise skill.
- **Working rules (5 October):**
  - only 3–5 agents run at once, and messages to paused agents wait;
  - batch the Godot shots: one turn, look once;
  - keep handoffs lean, and hand off at about 500k tokens.

## 2. The brief, and where it stands

1. **The Hollow's win rate. Done.** Fixed at its causes (section 3).
2. **The Roost's dips. Done.**
3. **Finish the Dig.**
   - Done: the tests, the tuning, and the time-cap nights (down to 4 in 512; trace one if they matter).
4. **See all three at 1920x1080 and send frames to the experience director (`a9f0d6c64d891d56d`). Next.**
   - Judge Greymuzzle's thirty-wolf ring and its dashed line.
   - The director will judge danger and length on this branch.
   - **Experience's staging asks** (from their last batch, on the build before mine):
     - At Redcowl's knee (and Greymuzzle's `LieDown`), a banner should name the choice ("Spare him, or finish it"), and the prompt should be reachable from anywhere on screen. Today it reaches 3.4 m; a player across the camp stalls at his sliver.
     - The Dig's boss ran 5 minutes for their warden at tier 1. Check it on this build.
     - The experience director has handed off; their successor reads `docs/handoff/experience.md`.
5. **Build the Vault** (`STORY_BOSSES.md` §4, `WRITING_PASS.md` §23.3). Not started.
6. **Then:**
   - cinematics' boss hooks (`docs/cinematics/README.md` §6 item 11a; lead `a7a4c20bcfd7ccfd3`), including the seamless hand-off rule;
   - the run-ups re-measure;
   - the Kerchiefs at tier 3;
   - the Lamplings;
   - the bestiary;
   - drop moments (`LOOT_DESIGN.md`'s first-story-boss legendary; ask the main session);
   - armour at depth (a full Heartwrought set blocks about 70%).

## 3. What was done, and why (each a cause, measured)

- **Calling bias.** A story boss's blow is now `StoryBoss.Teeth` × `Character.OwnHealth` (the calling's base + 8 a level, before attributes, gear and draft). Before, a lunge was 29% of a reaver's health and 47% of a stalker's, and half the stalkers fell against one warden in eight.
  - Greymuzzle 0.38, Redcowl 0.4, Grimtunnel 0.2.
- **Tier bias.** `StoryNight.BossEase` (1 + 0.1 a tier) on boss health; the bosses' `HealthMul` was raised ×1.15 to keep the middle tiers the same. Each boss ran a third longer at tier 4.
- **The brawl.** `StoryBoss.Cuff`: between moves a story boss breaks off round her and strikes only what is across its path. The nip and shoulder had been as much as all the lunges or hooks for blade builds.
- **Greymuzzle:**
  - **the guard:** 3.5 m out of the den, a 2.4 m arc before him, flanks open. Blades never reached him in the Moon (it ran to its 75 s ceiling), which left On His Feet twice as long. This was the biggest single cause.
  - he slips along his ring instead of being pinned;
  - he lands heavy for 0.6 s after odd lunges;
  - his lunge on her lamed is marked 1.4 s;
  - the shake is marked 1.2 s and the chain 0.8 s (`SURVIVORS_BOSSES.md` §0.9).
- **The way in:**
  - `NamedFists` 2: a named foe's contact is half as quick;
  - `StoryFight.CrowdTeeth` per place (the Hollow 1.0, others 0.75);
  - the drive's lane ×7;
  - Whitethroat's health ×12, so she lives through her seven drives.
- **The hands** (StorySim only, via `strikes`): plain hands read lobbed pots' landing circles (`Battle.EnemyStrikes`) and walk out of enemy burning ground (`BossSense.Underfoot`). Before, these were the Roost's and the Dig's biggest way-in wounds.
- **Grimtunnel:**
  - his cracked hide now holds (`Act` used to reset `TakenMul`);
  - the going floor stops at 7 m and takes him in with it, onto free ground (`Footing`);
  - it bites every 2 s as a wall does;
  - pits stop at 1.5× their cap when he is wild.
- **The place holds her:** `StoryNight.Strays` puts her back if something throws her out. One Dig night was thrown past the lip's wall at the Heart's turn; the cause is not found.

## 4. The numbers (r6, 64 nights a row; `out/r6.jsonl`)

| Fight | Won (greedy / random) | First life | Under half on the way in | Boss (greedy / random, min) |
|---|---|---|---|---|
| Hollow | 88–92% / 89–97% | 83–94% | 12–34% | 2.9–3.2 / 4.3–4.9 |
| Roost | 86–97% / 84–91% | 77–91% | 12–33% | 2.8–3.0 / 4.5–4.8 |
| Dig | 95–100% / 88–94% | 80–95% | 19–38% | 3.2–4.0 / 4.8–6.1 |

- **Deft hands** (`out/d2.jsonl`):
  - the Hollow is won 100%, with a night of 8.5–9.4 min and a boss of 3.1–3.5 min;
  - the Roost's boss takes deft hands to a median low of 44–57%.
- **First life sits above 55–70%:**
  - With these hands, a fall once is mostly the build's, so the rise saves only 30–50%.
  - Any first life under about 83% puts "won" under 90%.
  - The first meeting costs about 6–12 points.
  - Raise it only through learnable mechanics (things the rise forgives), never through attrition.
- **Careless (random) drafts win as often as planned ones.** The Picker's policies differ little, so the "careless 70–80%" target cannot be set apart.

## 5. Gotchas

- **The worktree guard:**
  - refuses `cd` followed by a heredoc, a shell variable or a computed argument;
  - refuses `git -C`;
  - use the Edit tool, or scripts run by absolute path.
- **Harness builds:** build to a fresh folder (`dotnet build -c Release -o bin/xN`) while a run holds `bin/Release`. Runs take about 15 minutes for 1,536 nights at `--par 16`, and the machine is shared.
- **Tools** in `C:/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/combat6/`:
  - `sum.py NAME [fight] [--wait]`
  - `rep.py NAME|path`
  - `falls.py` (falls at the boss, by calling, phase and source)
  - `pace.py` (falls by pace and reach)
  - `dips.py FILE fight` (the way in's dips and their sources)
  - `batch.py` (one Godot turn: import, then six runs at 1080)
  - `play.py` (one run)
- **STORY_TRACE** lines now show the boss's `soft`, `hard` and `OUTSIDE-BOUND`.
- **Godot:**
  - the worktree's `godot/assets` is a junction (skip-worktree);
  - `.godot` is copied;
  - the game DLL is built (`dotnet build SurvivorUnchained.csproj` in `godot`; rebuild after logic changes);
  - run `batch.py` inside `turn.py take godot "combat: three fights at 1080" --wait 20` and give the turn back after.

## 6. Collaborators

- **Experience director (`a9f0d6c64d891d56d`, running):**
  - accepted a fourth Hollow beat: the den's mouth and the sick, the Pack herding her, which must teach something Greymuzzle asks;
  - will judge this branch.
- **Story:** words for the fourth beat (when it runs).
- **Animation (`a7dd95d00c4a6a017`):** checks the levy's crossbows and the plants with `--on casts`.
- **Arena art and skills VFX (paused):**
  - the Dig's and the Roost's outlines;
  - looks for the mound, the tubs, the barrel and the gaps.

## 7. Files to read first

1. `docs/team/combat.md`, then `docs/design/STORY_BOSSES.md` §0.
2. `godot/logic/Play/Bosses/StoryBoss.cs` (Teeth, Cuff), `Greymuzzle.cs`, `Redcowl.cs`, `GrimtunnelStory.cs`, `BossSense.cs`.
3. `godot/logic/Play/Zones/StoryNight.cs` (BossEase, NamedFists, Strays), `Play/Story/*.cs`.
4. `godot/balance/Harness/StorySim.cs`, `Pilot.cs`; tests `StoryNightTests`, `RoostTests`, `DigTests`.
