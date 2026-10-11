# Survivor Unchained: rules for every agent

Start with `docs/team/README.md` (how we work, safety, the roster), then `docs/team/RESUME.md` and your handoff.

## Disk and worktrees (the owner, 10 October 2026)

C: went from 317 GB free to 13 GB in three days: 85 agent worktrees (about 4 GB each) never removed after their work merged, plus about 44 GB of session scratch in `%LOCALAPPDATA%\Temp\claude`. So:

1. **A worktree is removed as soon as its work is merged,** in the same turn as the merge. Whoever merges does it (usually the main session). Use `powershell -NoProfile -ExecutionPolicy Bypass -File tools/scratch/coordinator/wt_remove.ps1 <path>`, which runs `git worktree remove` after rule 4's link check and handles Windows long paths. It refuses if there are uncommitted edits. Pass `-Force` only when the edits were checked and are discarded on purpose.
2. **Commit as you go.** No worktree sits with uncommitted work at the end of a task: commit to your branch even if it's WIP (say so in the message). Discarded experiments are reset, not left lying around. Built art you can't commit yet (unjudged) is the one exception, and your handoff names it.
3. **At most 8 worktrees on disk at once.** Before creating one (including spawning an agent with `isolation: "worktree"`), count `.claude/worktrees`. At the cap, remove finished ones first.
4. **DANGER: links.** Some worktrees had `godot/assets` as a junction into the main checkout's `public/assets`. Never point a worktree's link at the main checkout: link to the worktree's own `public/assets`. Before removing any worktree, remove its junctions and symlinks first (the link only), so no delete can follow a link into the real assets. `wt_remove.ps1` does this. **Blender files link too:** a .blend may load its images from another worktree's path. When that worktree is removed, its exports come out unpainted (11 October: face, outfits and animation all hit it). Keep a blend's images inside your own worktree or packed (`tools/assets/blend_relink.py` relinks and packs), and check they resolve before an export.
5. **End-of-day sweep** (the main session): `python tools/scratch/coordinator/wt_audit.py` lists each worktree's size, last commit, merged or not, and uncommitted edits. Remove the merged and clean ones. Report any older than 48 hours that are unmerged or dirty.
6. **Scratch:** clear a session's `Temp\claude` scratchpad when that session's task is done: back up scripts and texts to `C:\Users\munch\Desktop\survivorsunchained_inputs\scratch_<session>\`, then send the rest to the Recycle Bin. Keep render or test output only if a doc references it. Large generated output belongs in a git-ignored folder inside the repo, not in Temp.
7. **Disk guard:** before any job expected to write more than 5 GB (renders, model downloads, big builds), check free space on C:. Under 50 GB free, run the sweep first and tell the owner (leads tell the main session).

Never delete permanently what isn't checked: the Recycle Bin is the default, and the owner empties it. Never move long-path folders (worktrees) to the bin: use `wt_remove.ps1`.
