# Paused, 4 October 2026: how to pick back up

The owner needed the machine, so the team checkpointed and stopped. Everything is pushed. Resume the leads from the roster in `README.md` by SendMessage ("continue from your status page").

## The integration branch

`claude/vigilant-galileo-l6jqyx` is at 87a3f528, with 567 tests green and pushed.

## Pushed, not yet merged

Merge each, then run `dotnet test` and push.

| Lead | Branch@commit | Next step (from their status page) |
|---|---|---|
| Combat | worktree-agent-a1d4562f44c7f6feb@a4cdcf0f | Run-ups WIP is parked on combat-wip-runups (not for merging) |
| Performance | worktree-agent-a7145e18b3eb78294@d6ee19c7 | Prefetch is parked on perf-prefetch-wip (crashes on quit, not for merging); export templates need the owner's OK |
| Crafting | worktree-agent-a7debf1459f14dfe7@37c31d6c | Phase 3: Vonnra's binding, Snib's bench |
| Legal | worktree-agent-aab20546fe06daa89@fbc9bf9b | Motion check of the rest of her clips |
| Experience | worktree-agent-ab406cf9ddd22b03b@f8e26228 | Status tint: burning and frozen bodies at the rim, not white |
| Animation | worktree-agent-a435f4dd0ac80df75@7a646f6c | The keyed slam; the crossbow aim once combat adds it |
| Male hero | worktree-agent-ab82cbe99e2937ddd@0ea15f7 | Head tool tone pass after fix(); hero.glb is unchanged |
| UI design | worktree-agent-a26f87c39952dcd9c@c9148ae0 | Credits and licences screen (a launch blocker) |
| UI art | worktree-agent-a1a394643aabfb169@53c5857 | Hero plate, light card, imports, slice margins |
| Skills | worktree-agent-a63cd93fc73d5ed79@0e6f2e8b | batch10.sh with no game open |
| Face | worktree-agent-ade92e8285938438f@9dc74eda | FACE v3 and its paint; art not committed yet |
| Arena art | worktree-agent-a26767f7f9955cb56@e10255f0 | Judge the new spoil and road; the Dig pass; the moonless fix |
| Story | worktree-agent-a73ca9d35d0c487a9@0a65f095 | Idle: waiting on others |
| Cinematics | worktree-agent-a3058a45eee41d695@d7e56082 | Confirm the toll-tower lamp in C04 B's shot B4a, then write shoot/c02 to c04b.md |

## The heroine's outfits (main session)

- Committed and good: 87ad2f1 (snug cups, the warden's straps, the stalker's top edge, soft nipple rises, minimal skin hiding).
- **outfits-wip@2a856f05** (pushed, not merged) holds the tailoring fixes since, partly unbuilt; its commit message lists what's seen and what isn't. Next:
  1. Check out its `tools/assets/heroine_outfits.py`, then run `bash $TEMP/hs/full_build.sh` and `bash $TEMP/hs/closeups.sh $TEMP/hs/cups.txt`.
  2. Check the arcanist's neckline in Idle: the steps came from the binding's nearest-point weights, now one set per ring.
  3. Check the warden's left cup in the sprint with jiggle on: the nipple disc is now hidden. Use the legal handoff's motioncheck steps.
  4. Check all four outfits for regressions, then merge to the integration branch.
- Then: the arcanist's boot cuffs as level bands; the face lead's new head means re-running `--body` (they'll say when).

## Waiting on the owner

- The Godot export templates download (about 1 GB, from Godot's GitHub releases): the owner's own yes.
- "Warmed" (the love scenes' combat buff): decouple it, for Australia's R18+?
- The provenance questions (docs/legal/ASSET_PROVENANCE.md):
  - what made 234.glb, woman.glb and ComfyUI_00008.glb, and from which pictures;
  - whether the owner owns The Ember Watch;
  - the boar: buy the commercial version or replace it;
  - their country of residence.
- The Wayfinder's maps: 30-minute nights, with permanent maps of about 10 minutes, as read now?
- The placeholder voices: kept out of release builds?
- Who sings the hymn at Nell's grave (C08)?
