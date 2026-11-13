# Build-direction lanes: what every bd-* lead shares (coordinator #9, 13 Nov 2026)

Read first: `CLAUDE.md`, `docs/team/README.md` ("How we work", "Safety", "Working lean"), the TOP block of `docs/team/RESUME.md`, then `docs/design/BUILD_DIRECTION.md` in full and `docs/design/BUILD_UNLOCKS.md` (the ladder: every level number comes from it; to change one, edit that page in its own commit and tell the coordinator). BUILD_DIRECTION overrides `docs/design/ARPG.md` section 3 (six keys); its rounds 7-8 override its earlier rounds.

Scope: the **Warden only**, fully built as the melee bruiser (Act 1 and the demo). Other callings must still compile and pass their tests, but get no new content. Saves are expendable: migrate when cheap, otherwise reset cleanly; never crash on an old save.

Workflow:
- Your worktree is already made (junction to its own `public/assets`; no `.godot/imported` cache: this is a code lane, you run `dotnet test`, not Godot shots). Never `git stash`, `reset --hard` or `checkout .` in it (README junction DANGER). Never touch the main checkout.
- Commit as you go on your own branch, push it (`git push origin <branch>`). Open no PR. Merge `origin/claude/vigilant-galileo-l6jqyx` in before you finish (another bd lane may have landed); if the merge fails, follow README "A failed git merge" (remove the junction link first, merge, remake it to your OWN `public/assets`).
- `dotnet test` in `godot/tests` green before every commit that claims done (baseline 2349 passed / 0 failed / 11 skipped; the suite takes ~9 min, run it as a background job). A test that encodes the OLD rule (six keys, 15 slots, cap 30) is rewritten to the new rule, never deleted to go green; say which ones in your report.
- Code is coding: spawn helpers at `effort: "medium"` (su-worker for decided changes, su-runner for suite runs and greps). No judges: this lane has no pictures.
- Stay in your files (the brief lists them). If you must change a file another bd lane owns, make the smallest edit, say so in the commit message, and tell the coordinator.
- Done: `MR READY <branch>@<sha>` as the first line of your final report, then: suite numbers, what the game can now do (one line each), tests rewritten, anything left or routed, tokens spent. If you stop short: `HANDOFF READY docs/handoff/<lane>.md on <branch>@<sha>`.
- Owner questions are never guessed: put them in the report; the coordinator takes them to the owner. Design calls inside your lane are yours: make them, write them one line each with the why in your report.
