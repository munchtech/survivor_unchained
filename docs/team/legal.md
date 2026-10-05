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

Latest: the main session's fix build, **0e35921f** (5 Oct). Five views: chest, 45°, side, below, and over (looking down into the neckline). Jiggle on. "Shows" means 6 px or more at 960×540. Margins are past the areola's edge; negative means it shows. Details and crops: `scratchpad/legal3/fix1/<outfit>/summary.txt` and `crops/`.
- **Codes:** fp is clean (80 frames, all four outfits), and every outfit's tuck mask covers the areolas.
- **Warden** (its 12 finding clips) and **Arcanist** (its 11): no areola shows.
  - Left for "pixel perfect":
    - the Warden's 1 to 4 px of the right cup's rim in chain_haul and chain_strike (45° view);
    - 1 px nipple-tip pokes in axe_fore, cast_bolt and dash (chest);
    - strip slivers beside the gusset: the Warden lying on her back (death_back) and in the leap from below; the Arcanist in 60 frames, mostly 6 to 13 px, worst 84 px (bull_rush below 05).
  - The tightest edges are the Arcanist's right outer and lower outer (+0.02 and +0.05).
- **Stalker** (all 46 clips): no areola shows; 1 to 2 px of the left breast's lower rim from below in 11 frames; the strip in 13 frames (sit_log low, vault, death_back), worst 40 px.
- **Reaver** (all 46 clips): **fails: the areola shows in 26 frames.**
  - Mostly the over view of the run, sprint, catch_breath and axe clips: her left breast's band gapes at its top edge, to 0.96 cm from the tip.
  - Also her right breast at 45° in chain_haul, bull_rush and vault_back.
  - Sent to the main session. Re-run the Reaver after its fix: `run_outfit.sh reaver <tag>`.
- **Tucked skin in view** is nearly gone on the fix build (under 70 px anywhere).
- **Not yet covered:** the Warden's and the Arcanist's other clips on the fix build (only their finding clips were re-run). Run them in full before submission.

**Next:** the Reaver after its fix; then the Warden and the Arcanist in full. Then update brief issue 2 and checklist D2, and tick the motion check if every outfit passes.

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

**Reading count.py's output without me** (`<folder>/summary.txt`, which `run_outfit.sh` prints at its end):
- **First line per outfit:** frames; "areola shows in N" and "genital strip shows in N" count frames with 6 px or more (the pass bar); "tucked skin seen" counts frames with any patch of deep-tucked skin, a dent or a gap; "the edge ring" is the shallow 1/3 tuck at a piece's edge, which shows by design.
- **Per breast:** the closest visible skin to the areola's edge in any frame, then by edge of the rim (as seen in that view; "inner" is towards her midline). It is a signed margin: +0.40 cm means 4 mm of skin still covered beyond the areola; negative means the areola shows. A margin of -2.20 means d = 0, the nipple tip itself, usually a 1 px poke-through.
- **Under 6 px:** frames below the bar are not listed. Find them in `counts.csv` (columns `areola_px`, `genital_px`, `tucked_seen_px`), e.g. every row with `areola_px` of 1 or more.
- **Crops** in `crops/`: `flag_*` for flagged frames, `closest_<outfit>_breast_l/_r` for each breast's closest pixel (ringed), and `tuck_<outfit>_N` for the largest tucked patches. Every crop carries the TEST TINT banner.
- **The outfit passes** when areola and strip show in 0 frames. Then update brief issue 2 and checklist D2.
- **Before trusting a run,** check the "clips with no frames" line is empty.

## Key decisions (with why)

- **The check measures; it never asks for more garment.** The owner: "pixel perfect no extra stuff hidden at all".
- **No genitals are modelled.** The strip is checked so the survey stays true, not because anything is there.
- **Every crop carries the TEST TINT banner:** the owner once took the tint for the game.
- **The disclosure names only what ships,** and says "rebuilt and rigged for the game", not "by hand".
- **Path B's picture models** (brief 5(g)): Qwen-Image, Z-Image-Turbo and FLUX.1 [schnell] (Apache-2.0) are fine; FLUX [dev] and SD 3.5 are not.

## Notes for other areas

- **Creatures lead (the boar):** follow brief 5(a) and 5(g): text-only pictures, a ledger line, and the Sketchfab boar out of the build when yours lands.
- **Anyone adding a tool or model:** send me its licence link.
