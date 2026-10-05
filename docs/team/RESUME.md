# Paused, 4 October 2026: how to pick back up

The owner needed the machine, so the team checkpointed and stopped. Everything is pushed. Resume the leads from the roster in `README.md` by SendMessage ("continue from your status page").

## The integration branch

`claude/vigilant-galileo-l6jqyx` is at 87a3f528, with 567 tests green and pushed.

## Merged since the pause

All the leads' paused branches are merged (597 tests green), except two whose own leads are resolving conflicts: face (9dc74eda) and cinematics (d7e56082).

## The heroine's outfits (main session)

- Committed and good: 87ad2f1 (snug cups, the warden's straps, the stalker's top edge, soft nipple rises, minimal skin hiding).
- **outfits-wip@2a856f05** (pushed, not merged) holds the tailoring fixes since, partly unbuilt; its commit message lists what's seen and what isn't. Next:
  1. Check out its `tools/assets/heroine_outfits.py`, then run `bash $TEMP/hs/full_build.sh` and `bash $TEMP/hs/closeups.sh $TEMP/hs/cups.txt`.
  2. Check the arcanist's neckline in Idle: the steps came from the binding's nearest-point weights, now one set per ring.
  3. Check the warden's left cup in the sprint with jiggle on: the nipple disc is now hidden. Use the legal handoff's motioncheck steps.
  4. Check all four outfits for regressions, then merge to the integration branch.
- Then: the arcanist's boot cuffs as level bands; the face lead's new head means re-running `--body` (they'll say when).

## The owner's answers (4 October 2026)

1. **Export templates:** yes, download whatever is needed (the main session fetched Godot's official 4.5.1 mono templates).
2. **"Warmed":** no longer a buff; it only says it happened (the story lead is making the change).
3. **Base bodies:** they came from Krea assets, since deleted. Replace them with our own (see docs/art/MODELS_TO_MAKE.md, being written).
4. **The Ember Watch:** the owner made it with Claude; nothing third-party, nothing registered (the legal lead is explaining what owning it means).
5. **Third-party assets:** replace everything with our own over time.
6. **Map lengths:** the owner wants these explained plainly; the combat lead is writing three lines.
7. **The owner lives in the United States.**
8. **The hymn at Nell's grave:** the owner will make it in Suno.

## Handoffs ready: start their successors when the GPU is free

These are past their memory limit. Each has a handoff in docs/handoff/<area>.md, and their branches are merged:
- animation (67cb4f2c);
- performance (a3513e14);
- crafting (fdb62e76);
- UI art (bfa7bdb);
- skills (0a7e8eff);
- face (5fd76deb).

The combat successor is already running (design only).

## Paused work that needs the GPU or Godot

The owner is using the GPU. No Godot, no ComfyUI, no Blender until the owner says so. Waiting on that:
- the outfit WIP build and checks;
- the face lead's FACE v3;
- the male hero's head;
- UI art's renders;
- skills' batch10;
- arena art's shots;
- animation's slam;
- the experience director's status tint;
- the legal motion check;
- the performance lead's prefetch crash hunt and the release export;
- every full-resolution check.
