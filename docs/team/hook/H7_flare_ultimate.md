# H7 Flare: an ultimate

Lead: `su-lead-high` in worktree `.claude/worktrees/flare-h7` (branch `flare-h7`, from the integration HEAD). Est ~0.6M (VFX and sound ~0.4M, one max judge). Read first, by section: `docs/handoff/lead_brief.md`; `docs/team/DEMO_GATE.md` "Phase 3b" (N29 and N37 are yours); `docs/team/DEMO_PLAN.md` "demo-rc2 verdict" (the H7 row); `docs/handoff/flare.md` top (VFX 12: the eight Flares, what is marked today, `FlareFx.*`, `Flare.DropFresh`); `docs/design/FLARE_LOOK.md` §0, §1.6, §4.1, §4.4; `docs/handoff/audio.md` top and `docs/team/audio.md` (H3's bank `sounds.json`, the gen tool, the ElevenLabs route: the key is `ELEVENLABS_API_KEY` in the environment, never printed); `docs/design/LOOK_BIBLE.md` rule 9 (spells: one family per school, `Palette.Of(school)`). Your handoff: `docs/handoff/flare.md` (add your section above VFX 12's).

## The owner's words (demo-rc2, 4 Nov)
"flare looks weak - no indicator of what its hitting - tho it does pick the target you hover which is nice, it just dosn't feel epic like a time stop or fit the bill of super epic finisher ultimate thingy." "sounds are better but still meh. especially our flare." The standing rule (memory, 29 Oct): every press visible; the Flare is a BOOM button.

## The ultimate, as one family (data; the eight Flares are instances)
On press, in this order, every Flare:
1. **The stop** (0.25-0.4 s): a hit-stop on the sim's view (the crowd and her freeze; the sim may keep its clock), the grade drops toward moon indigo with her ember the only warm light (bible rule 3), a low intake sound. The hovered priority target brightest.
2. **The marks**: every foe the Flare will hit gets a mark before the blow (a lit ring or line in the Flare's school color, `Palette.Of`), the hovered one brightest. The count of marked foes is the count that dies or takes the blow: no mark, no hit; a mark, a hit. This is the owner's "indicator of what it's hitting".
3. **The blow**: the Flare's own shape (keep each one's identity from FLARE_LOOK), with a screen-wide read: one shock band from her out over the frame, the kills popping on the beat (`DeathHeld` lands with it), the damage numbers in one burst, the camera a 2-4 px kick, the loot on the beat (`DropFresh` already).
4. **The recovery**: her pose settles over 0.3-0.5 s (animation's clip stays; time the release to it), the grade eases back over 0.5 s, the ember's pool at x1.3 for 2 s.
5. **The sound**: two beats generated at H3's bar (the stop's intake, the blow with its tail), per school, plus the mark tick; mixed under the fight's -20 LUFS with the blow allowed 6 dB over; `sounds.json` events, the gen tool. The synth stays for nothing a sample does better.

## The gate
One `su-lead-max` judge (`effort: "max"`) on a 6 s clip of each of the Warden's Flares at 1:1, the play camera, in a tier-1 night with a crowd (the standing H1 night harness: `--zone arena --offer 0 --auto` with a Flare press at a known second), against the owner's line and the best ultimates in Hades (the Calls) and Vampire Survivors' evolutions: "is it epic; do I know what it hit; is it the same game as the rest of the frame?" Then the other callings' Flares as the same family (a spot check, not a judge each). Round cap 2. Frame time: the stop and the band within 0.5 ms GPU at the play camera (`--perf`).

## Scope
The Flare's look, timing and sound only. Not: its numbers or targets (H6 combat is running beside you in `combat-h6`; the Flare's role as the save of the closing ring is H1's, unchanged), her clip (animation), the HUD. If H6 changes the closing's shape, your marks read its foes the same way: coordinate once by SendMessage.

## The workflow
Merge integration into `flare-h7` first (the junction rule: `cmd /c rmdir godot\assets` before the merge, remake it to your OWN `public\assets` after, `git update-index --assume-unchanged godot/assets`); `--import` once. Godot shots and clips take `python tools/turn.py take godot "flare-h7: <what>"` (H6 and H8 share the machine), given back at once; ElevenLabs runs need no turn. Commit as you go; the full suite green before the MR; push `flare-h7`; your handoff top gets `MR READY flare-h7@<commit>` and you SendMessage the coordinator the same line with the clip paths (`survivorsunchained_inputs\flare_h7\`), the judge's verdict in two lines, the credits spent, and your cost. First report within your first few turns: the five beats with each one's state and an honest estimate.
