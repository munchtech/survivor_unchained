# The shared lead brief (the coordinator pastes this, then adds: the area and its worktree and branch, where the predecessor stopped, and the steps)

Context budget: 300k

You are a fresh successor. The coordinator is the main session: report to it with SendMessage to "main". Read in this order, by section, not whole files: docs/team/README.md ("Working lean", Safety), docs/team/RESUME.md top section, then your handoff's top section in YOUR worktree. Merge the latest `origin/claude/vigilant-galileo-l6jqyx` into your branch first.

The owner's rules for this stretch (17 October; README "Effort by kind of work" and "Focus"):
- "still AAA quality. still 'perfect', just we aren't going in 2x++ zoom anymore. we lost a little bit of focus and our game isn't moving along well enough." Judge only 1:1 game-camera frames (play/town, the close-up at its closest zoom, the Look camera). A mark that only shows enlarged is closed. Finish your fixed list, merge, and free your slot so other areas can build. Round cap 2-3 per item, then close as known.
- You orchestrate on high. Coding (code solvers, numeric solvers, builds) runs at medium: `su-lead-high` with `effort: "medium"`, or the API route `node tools/ai/api_agent.cjs ... --effort medium`. A decided change goes to `su-worker`. Menial work goes to Sonnet or Haiku (`su-worker-medium`, `su-runner`), or one background Bash job when it's a single command.
- Judges: on what the player sees all the time (her face at the Look and close-up cameras, her body and outfits, her core motion) at `--effort max`; anything seen less often at `xhigh`. Run them on the API credits (README "Judges on the API credits"), background Bash.
- Put `Context budget: <n>` in every helper brief and give each helper YOUR agent id so it reports to you, not to the coordinator.
- There are 8 worktrees on disk, the cap: never spawn with `isolation: "worktree"`. Helpers work in your worktree.
- Never kill processes by name; never bare `git stash`, `git reset --hard` or `git checkout .` in your worktree; commit as you go (WIP commits are fine).
- Legal runs once per merge request: `python tools/legal/gate.py --root <your worktree>` as a background Bash job; paste its one line in the MERGE REQUEST. Never while iterating; it skips what coverage can't see.
- Hand off at about 300k: update your handoff's top section and send "HANDOFF READY <branch>@<commit>".

First report, once you're oriented (within your first few turns): your fixed list with each item's state, and an honest estimate of how much is left until your area is DONE and merged (items, rounds, rough hours), so the owner can plan which areas start next.
