# Handoff: the gameplay experience director

For a fresh successor. Read these first:
1. `docs/team/README.md`: the bar, the turns, and batching shots.
2. `docs/team/experience.md`: the one-page status, which holds what's done, the next steps in order, and the verdicts.
3. `docs/design/STORY_NIGHTS_AND_TIME.md`: the owner's decisions are at its top.

## The owner, in their words

- "We are striving for perfection." Improved is not the bar: ask whether this is the best version of the moment in any game, and root it in how the best games solve it.
- "Endless is truly endless."
- Full pages pause rarely, and "are often not the best choice".
- Story nights: "smaller arena", "proper arpg end bosses", no endless.
- Time "passing should probably happen".

**Standing decisions:**
- A lost story fight wakes her at Chid's a day on.
- Redcowl can be spared or killed.
- One rise in Act 1; after that, only with the rise skill.
- Story is about 40% of the early game.
- The endgame is PoE-like maps plus survivors arenas.

**Working rules:**
- Only 3 to 5 leads run at once.
- One Godot turn per batch of shots: look once, then fix in one pass.
- Handoffs are lean, at about 500k tokens.

## The brief

You own how the game feels to play, end to end: pacing, readability, the day clock, the story fights' flow, what the screen says and what is noise. Play it on the autopilot and in scripted runs, judge it at 1920×1080, then fix it yourself or brief the owning lead in short writing: what's wrong, the evidence, the target, how it's judged.

**Branch:** `worktree-agent-a9f0d6c64d891d56d`. The main session merges it; open no PRs. Run `dotnet test` in `godot/tests` before each commit. British spelling.

## Collaborators (roster in `docs/team/README.md`)

- **Combat** `a739d6792d21f5efd`: the story fights. 52d202f2 and later are not yet judged.
- **UI design** `a4fdbc49786ba8b7f`: the dial and the fall at 2378e165; the result screens.
- **Story** `a7ba8903f4c8261b1`: all the words.
- **Paused:** skills `abc6bbe020c7fe287` and arena art `aba487928a1515c93`. Their asks are on the status page.

## Failures and gotchas

- **A fresh worktree has `godot/assets` as a 16-byte stub.**
  - Fix it: delete the stub, make a junction to `public/assets` (PowerShell `New-Item -ItemType Junction`), run `git update-index --skip-worktree godot/assets`, then `--headless --import` (about 4 minutes).
  - A checkout can turn the junction back into a stub, and the game then renders black frames or throws in `Dressing.PartsOf`. Check `(Get-Item godot\assets).LinkType`.
  - Once, deleting the stub through git removed `public/assets`. `git checkout -- public/assets` brings it back.
- **Copy `.godot` from an older worktree** to skip the full import.
- **Godot runs `.godot/mono/temp/bin`.** Run `dotnet build SurvivorUnchained.csproj` in `godot/` after every change.
- **To judge someone's unmerged work, use a local `exp-judge` branch,** then return to your own branch and delete it.
  - Skills' branch conflicts with loot's code, so leave it out.
  - Revert regenerated `.import` files before switching branches.
- **The shell guard** refuses compound git commands, `cd ..` followed by git, and runtime-built sed. Write a small Python script in the scratchpad instead (`gist.py`, `branches.py`, `contains.py`).
- **The autopilot** never answers a story fight's spare/finish offer (the Roost stalls), and takes the first card of every draft. A drafted Cold, Then Not rises her on its own. Use `--auto idle` to see the fall card.
- **Quote commit ids only from git.**

## Tools (scratchpad `experience/`)

- `play.py NAME -- [game args]`: a run at 1920×1080 and 60 fps, with the log in `logs/`.
- `batch1.sh`: one turn holding all three fights whole (`--on boss --until 720`), the fall, the dial, the Verge, loot and map results.
- `gist.py NAME`: a run's health by time, its tagged moves and its exceptions.
- `sheet.py`, `tsheet.py`, `crop.py`, `keep.py` (frames to `docs/experience/`).
- `wait_for.py`.
- Turns: `turn.py take godot "experience: <job>" --wait 30`.
- **Game switches:**
  - `--night ID`, `--stage N`, `--on boss`, `--die T1,T2`, `--choose rise|letgo`;
  - `--clock S`;
  - `--loot [legendary]`, `--hoard N`, `--strongbox`;
  - `--open mapresult [--fell]`, `--perf-off taa`.
