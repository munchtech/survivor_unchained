# Experience: the game as a player lives it

Status page for the gameplay experience director. The last lead was `a9f0d6c64d891d56d` (branch
`worktree-agent-a9f0d6c64d891d56d`), handed off at the context limit: read `docs/handoff/experience.md`.
The audit is `docs/EXPERIENCE_AUDIT.md`; the approved design is `docs/design/STORY_NIGHTS_AND_TIME.md`;
evidence frames are in `docs/experience/`.

## Current state (2026-10-05)

**Built and seen (this lead), all on the branch:**
- Hostile lanes fill as they come. A named move draws at a boss's strength.
- Move words stand under the HUD's top stack.
- Captions keep off the banner's line.
- Struck flare: only three bodies a frame go white. The rest keep their flinch and a breath of rim.
- Chest ceremony:
  - names gear as its tooltip does, in its rarity's colour;
  - sends each piece down to where it lies;
  - holds toasts until it ends.
- **The first Legendary ever** is held in the world on `Journey.FirstLegendaryTaken`: the bare ceremony with its name, its kind and its power.
- The autopilot steps onto gear. `--strongbox` puts a strongbox in a map.

**Judged at 1920×1080. The story fights are on builds before combat's 52d202f2, so read these for staging, not danger:**

| Fight | Length | Lowest health | Verdict |
|---|---|---|---|
| Hollow | 7:50–8:20 | 88–92% | Reads well. Too short and too soft for a practised reader. |
| Roost | stalled | 56% | First real danger, before his knee. Then it stalls there (`roost_stalled_at_his_knee.jpg`): the spare/finish prompts only show within 3.4 m, and no banner names the choice. |
| Dig | about 10:10 | 65% | Boss 5 min, against a 3–4 min target. |

- Combat has all three findings.

**The UI** (UI design `a4fdbc49786ba8b7f` has the verdict):
- The tips and ground labels as type read well.
- The map result's loot column is dead space (`map_result_dead_column.jpg`).
- A loss's quest toast prints over the still-moving fight (`loss_toast_over_fight.jpg`).
- The dial and the fall card are not yet judged.

## Next

1. **The autopilot answers a story fight's offers** (walk to `story:finish` or `story:let_go` and press Use). Without it, Roost runs stall at the knee.
2. **Judge combat's Hollow, Roost and Dig** on `worktree-agent-a739d6792d21f5efd` (52d202f2 on): length 10–14 minutes, the way in dipping under half in 20–35% of runs, the boss touching a practised reader.
3. **The day dial and the fall card** (UI's 2378e165):
   - `--clock 590/710/890/1070` in the Waystation; crop the zone-name block, about x 1400–1900, y 400–520.
   - The fall: `--night hollow --stage 3 --auto idle --die 10 --choose rise`. Use the idle pilot: a drafted Cold, Then Not rises her first.
4. **Skills' noise fixes when they land:** grounds dimmed while a boss is up, enemy ground violet, Dawnpulse's ring, the Dig's looks. Skills is paused and its branch conflicts with loot's code in `BattleFx` and `Game`, so the main session merges it.

## For paused leads (when they wake)

- **Arena art:**
  - The atlas maps use the low-poly kit and canopy that covers rulers (`map_ruler_cover_and_kit.jpg`). Queued after their five arena items.
  - The Waystation at night is near-black across the frame.
- **Skills:**
  - With TAA on, a body struck as it flies smears pale.
  - Keep move words under `GameHud.TopClear`; `GameHud.Banner` is there for anything drawn near the banner.

## Decisions (with why)

- **A named move draws at a boss's strength, whoever makes it:** a mechanic a stage teaches must not sit at the crowd's 0.28.
- **A charge fills as it comes:** two edges alone read as one more line on the ground.
- **Words never share a line:** a caption beside a banner reads as one sentence.
- **The first Legendary is held in the world, not paused on a page:** the owner wants full pages rarely.
- **Only the light of a struck body is capped, never its flinch:** a crowd struck at once reads by its flinch, a few by their flare.
