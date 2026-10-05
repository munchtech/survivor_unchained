# Legal and Steam compliance: status

Agent af0973d59a5b2817a (third lead), branch `worktree-agent-af0973d59a5b2817a`. Not a lawyer: I find and organise the issues, cite primary sources, and recommend. The owner and the main session decide. To resume cold: this page, then `docs/handoff/legal.md`.

**Paused by the owner after the fit-fix pass** (5 Oct). Wake me for a new outfit, a store-page review, or before submission.

## Blockers (3)

1. **The mature-content survey:** it waits on the motion check passing on the main session's **fit-fix build**. The draft answers are in `STEAM_CHECKLIST.md` D1 and D2.
2. **The boar:** our own replaces it. A new creatures lead makes it locally with Krea 2 and TRELLIS 2, which puts it in the Krea footprint. Its picture comes from text alone, never from the Sketchfab boar or others' art (brief 5(a)). The old boar must not ship.
3. **The AI disclosure:** ready to paste (`STEAM_CHECKLIST.md` D3). **Raise it at submission, not before** (the owner, 5 Oct).

**Done:** the licences screen, seen in game on 5 Oct (every section and licence page). Also done: export and debug paths; the placeholder voices; the explicit placeholders; "Warmed"; The Ember Watch.

**Waiting on the owner, to raise before submission:** sign `docs/legal/records/BODIES_RECORD.md`; paste the disclosure; give his state of residence and business structure; say whether "Munchtech" is registered; run the USPTO search.

## The motion check: results

On the tuck build, 35c5dc3a. Five views: chest, 45°, side, below, and over (looking down into the neckline). Jiggle on. Margins are past the areola's edge; negative means it shows.
- **Codes:**
  - fp: 80 frames of all four outfits, no false pixel;
  - every outfit's tuck mask covers the areolas.
- **Warden** (2,080 frames):
  - the areola rim shows in 14 frames: chain_haul, chain_strike, dash and bull_rush, in the 45° view;
  - a 1 px nipple-tip poke-through in cast_bolt and axe_fore;
  - the strip shows lying on her back (death_back, low view), either side of the thong's rear;
  - the closest edges are the right cup's inner and upper inner, at +0.05 and +0.08, seen from over.
- **Arcanist** (2,180 frames):
  - the strip shows either side of her crotch strap in most standing clips (below and 45° views);
  - the areola's outer rim shows in 17 frames of big arm swings (chain_haul, bull_rush, cast_bolt, axes, daggers, sword, throw).
- **Stalker:** cut short by a rebuild (13 of 46 clips). Provisionally clean (right breast lower outer -0.28 in 1 frame, under 6 px).
- **Reaver:** not run on this build.
- **Tucked skin in view:** mostly inside bracers, under lifted pauldrons and at the knee plate.
- **The main session's fix build** answers all of these:
  - cup and neckline edges keep her skin's weights;
  - the tuck scales with closeness, up to 8 mm;
  - 2.8 cm gussets on every crotch, a new one under the Reaver's G-string.

  **Next:** when the main session sends its commit (it holds rebuilds in the main checkout until I report), re-run the Warden's and the Arcanist's finding clips, then the Stalker and the Reaver in full. Send the numbers, update brief issue 2 and checklist D2, and tick the motion check if it passes.

## How to run the check

Tools: `tools/legal/motioncheck/`. Read `run.sh`'s header and `count.py`'s docstring. Pictures go to the scratchpad only; calibration pictures show her bare.
1. Merge integration. The generated script is built from this worktree's `lookdev.gd`, which must match the build.
2. Make sure nothing imports or rebuilds in the main checkout. Godot runs there (`PROJECT=`), because this worktree has no import.
3. Use the turn scripts in `scratchpad/legal3/`. Each takes a Godot turn (`take ... --wait 30`), runs, gives the turn back, and counts:
   - `tuck_a.sh <tag>`: tuckcalib, calib, fp and cup;
   - `findings.sh <tag>`: the Warden's and the Arcanist's finding clips;
   - `run_outfit.sh <outfit> <tag>`: every clip for one outfit, about 10 minutes;
   - `cup_only.sh <tag>`: the Warden's sprint.
4. Read `<folder>/summary.txt`: per breast and edge margins with clip, view and frame; areola and strip flags; tucked-skin patches. Crops are in `crops/`, each with the TEST TINT banner.
5. If a clip shows 0 frames in its log, an outfit failed to load: the checkout was mid-import. Re-run it.

## Key decisions (with why)

- **The check measures; it never asks for more garment.** The owner: "pixel perfect no extra stuff hidden at all".
- **No genitals are modelled.** The strip is checked so the survey stays true, not because anything is there.
- **Every crop carries the TEST TINT banner:** the owner once took the tint for the game.
- **The disclosure names only what ships,** and says "rebuilt and rigged for the game", not "by hand".
- **Path B's picture models** (brief 5(g)): Qwen-Image, Z-Image-Turbo and FLUX.1 [schnell] (Apache-2.0) are fine; FLUX [dev] and SD 3.5 are not.

## Notes for other areas

- **Creatures lead (the boar):** follow brief 5(a) and 5(g): text-only pictures, a ledger line, and the Sketchfab boar out of the build when yours lands.
- **Anyone adding a tool or model:** send me its licence link.
