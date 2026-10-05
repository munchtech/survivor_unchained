# Handoff: combat (skills' mechanics, enemies, encounters, bosses, balance, the maps, the story's nights)

Written by `a427a874da78cba8b` for its successor.
- **State:** everything is committed and pushed on `worktree-agent-a427a874da78cba8b`, merged with `claude/vigilant-galileo-l6jqyx` at `2d052564` (the fall card's conflict: UI's dark-until-the-result kept, with the controls held).
- **Tests:** 762, all green.
- **Earlier leads:** `a739d6792d21f5efd`, `a5115633c7006e4d4` and before. Their handoffs are in git history (`git log -- docs/handoff/combat.md`).

## 1. The owner's words

- **The bar:** "we are striving for perfection"; "AAA standard"; "I don't want to polish, I want to create perfection"; "do we have soul?" Ask whether it is the best version in any game, check it at full resolution, and don't stop to ask.
- **Story nights:** "much more specialized and fun - smaller arena - and they don't need endless - they have proper arpg end bosses".
- **Decisions** (top of `docs/design/STORY_NIGHTS_AND_TIME.md`): a loss wakes her at Chid's a day on; Redcowl can be spared or killed; one rise in Act 1 only, later only with the rise skill.
- **Working rules (5 October):** 3–5 agents at once; batch the Godot shots in one turn and look once; lean handoffs at about 500k tokens.

## 2. The brief, and where it stands

1. **The 1080 batch. Done** (four turns; the first exposed the autopilot, see 5).
2. **Experience's asks. Done:**
   - the spare-or-finish choice is put to her from anywhere, with a banner and keys (seen at 1080, laid out right);
   - the autopilot answers it (`--knee finish|spare`);
   - the Dig's boss runs to length.
3. **The six capped nights. Traced** (status page): four Dig sinkholes (fixed), one weak Roost night meeting the harness cap as it lost (now bounded), one bot wedged at the levy (hands).
4. **The Vault. Built**, measured and seen at 1080 (whole night 11:25 on the autopilot).
5. **Main session's ask. Done:** a night let go stands down at once (UI design's finding).
6. **The queue. Done:** the stalker's Finesse (+2% projectile damage a point).
   - **Not started:**
     - armour at depth (see 4 below);
     - the Hollow's fourth beat (needs story's words);
     - the Kerchiefs at tier 3, the Lamplings and the bestiary (the arena harness; old notes in `git show 94e1bf59:docs/handoff/combat.md` §4–5);
     - the cinematics hand-off hooks (`docs/cinematics/README.md` §6 item 11a; the Vault's is `c13`, and `BarrowLordStory.Hand` plays sights where no cinematic can).

## 3. What was done, and why (each a cause, measured)

- **`StoryChoice`** (`Play/Zone.cs`): a choice the story puts to her is the zone's, not an interactable.
  - `IStoryArena.Ask`/`Unask`; `ZoneRuntime.Choice`/`Answer(id)`.
  - Shown by `src/Game/GameChoice.cs` and `StoryChoices` in `src/Ui/WorldType.cs`.
  - Keys: use, then her art, held 0.6 s, armed after 0.8 s; keys already down when it comes up must be let go first; her art is not cast by them. A click chooses at once.
  - The boss bar goes while it waits. His lot, a broken levy (`Redcowl.loose`), the cage's men and a broken ring (`Greymuzzle.loose`) keep back; his end clears his marks (`CancelBlows`).
- **Grimtunnel climbs out** of the hole he came up through before it opens (`GrimtunnelStory.ClimbOut`, `holeOwed`). The hands go in on him dazed (`BossSense`).
  - Boss 2:30–3:00 planned, 4:00–4:40 careless; no capped nights.
- **`StoryBoss.Grows`:** past its hard mark every story boss's blow grows 3% a second. Lives of 10–13 minutes ended; careless wins fell about 5 points, still above the 70–80% target.
- **The Vault** (`Play/Story/Vault.cs`, `Play/Bosses/BarrowLordStory.cs`, `VaultTests`, `legion_standard` in `Enemies.cs`):
  - the place: three spaces (south, hall, stair); cover lies across the hall (`Cover`, `Clear` raycasts lanes against it); `StoryFight.Furnish` stands it;
  - the stages: the Decurion behind an eight-man `Levy` (×0.15 through it); the Scorpion (three bolt lanes every 4.2 s, ×0.3 beyond 9 m); the Signifer's three standards (`VaultOpened.Standard`, 0.85 of his health each);
  - the boss: health 130, Teeth 0.22, the ranks on the walls step in at each testudo; lift the standard with `bane.pole`; the front closes to 8 m (5 m when hard), and holy pushes it back.
- **`StoryNight.StandDown`** on a let-go: `Combat` off, marks, shots and patches gone, every creature `Scripted` and still, her controls held; the result still comes 2.2 s on.
- **The camera leans toward a story boss** (`FollowCamera.Toward`, a third of the way, at most 4.5 m). Greymuzzle fought under the HUD at the screen's foot.
- **Finesse:** `Stat.DamageOf(Tag.Projectile)` +2% a point (`Character.Kit`; `SelfScreen`'s line). At tiers 3–4, stalkers' bosses went from 149–204 s to 130–153 s planned, and careless wins from 66–81% to 81–91%.
- **Tools:**
  - `Picker` moved to `logic/Sim`, and the autopilot drafts with it (`--draft`, greedy by default);
  - the harness records `BossTurns`/`BossLife` and takes `--banes`;
  - `--end` ends a picture run at the night's result;
  - `--bosshp F` makes the boss F of its health (pictures of its end).

## 4. Armour at depth (analysed, not built)

- `StatBlock.ArmorReduction = a / (a + 20)` everywhere, whatever the attacker's level.
- Loot flattened armour's make curve to keep a full Heartwrought set near 70% (`data/content/loot.json`, `curves.armor` [1, 1.8, 2.8, 3.4, 4.0]).
- A level-relative fix would pass the attacker's level into `HurtPlayer`, for example `20 × (1 + 0.1 × (level − 1))`. That needs the general make curve back and a measurement in the map harness (`map --tiers ... --gear R`).
- Joint with loot (paused). Agree the target first: what share an at-level plate set should block at depth.

## 5. Failures and gotchas

- **The autopilot is no yardstick for length.** `--quick warden` is a levelled character with gear:
  - with first cards, Greymuzzle and Redcowl ran past seven minutes and never reached the knee;
  - with greedy drafts, the Dig's boss died at its floors (1:40).
  - Judge length in the harness, and staging at 1080.
- **The first `--bosshp`** lowered only his health: the phases' marks healed him back up to them. It now scales his maximum.
- **A `Button` doesn't size to its children.** Measured before its words were in the tree, the two answers ran into each other. Sync `CustomMinimumSize` each frame.
- **KayKit pieces:**
  - the hex flag is 0.28 m tall (the standard uses it at 11×);
  - `rubble_large` is 8 m long;
  - `PieceView` rolls about X only (use `IOrb.Face` for a yaw), and a pillar's origin is its foot.
- **The worktree guard** refuses `cd` and then git, `git -C`, and shell-variable or heredoc commands that touch git. A heredoc into Python works for edits. `.import` files show as modified after an import (line endings only): never stage them, nor the untracked `.uid` files.
- **Godot:**
  - the assets junction, `.godot` copied from an older worktree, and `dotnet build SurvivorUnchained.csproj` after logic changes;
  - the first import after a merge took 8 minutes;
  - a picture run with `--on boss` saves many tagged frames;
  - tools are in `scratchpad/combat7/` (`batch*.py`, `play.py`, `sheet.py`, `phases.py`, `an.py`, `falls.py`, `rep.py`).
- **The harness:** build to a fresh folder (`dotnet build -c Release -o bin/xN`). 1,536 nights take about 18 minutes at `--par 8` beside Godot.

## 6. Collaborators

- **UI design (`a565196002a51af40`):** told about `StoryChoices` (theirs to restyle), the stand-down, and the empty "What you take out" column after a story night.
- **Experience (paused):** to judge the choice, the camera's lean, and the Vault.
- **Arena art (paused):** the Vault's place and its cover's stand-ins.
- **Story (paused):** the Vault's two sights of mine (status page); the Hollow's fourth beat.
- **Cinematics:** the boss hooks.
- **Loot (paused):** armour at depth.

## 7. Files to read first

1. `docs/team/combat.md`, then `docs/design/STORY_BOSSES.md` §0 and §8.3.2.
2. `godot/logic/Play/Zones/StoryNight.cs`, `Play/Story/StoryFight.cs`, `Vault.cs`; `Play/Bosses/StoryBoss.cs`, `BarrowLordStory.cs`, `GrimtunnelStory.cs`, `BossSense.cs`.
3. `godot/src/Game/GameChoice.cs`, `src/Ui/WorldType.cs` (`StoryChoices`).
4. `godot/balance/Harness/StorySim.cs`; tests `StoryNightTests`, `RoostTests`, `DigTests`, `VaultTests`.
