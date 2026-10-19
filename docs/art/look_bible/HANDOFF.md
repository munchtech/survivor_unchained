# Handoff: art direction, the look bible (look bible 2 -> 3)

Written by look bible 2 (agent ad893bff74a36d3e8, su-lead-max), 18 October 2026, at its context budget (boards cost more context than planned: ~250k for eight boards). Read README.md beside this page first: it holds the owner's words and the page index.

## Your brief (from the coordinator, unchanged)
- **Where you work:** the MAIN checkout (`C:\Users\munch\Desktop\survivorsunchained`, the coordinator's integration branch).
- **Write and commit only `docs/art/look_bible/`:** `git add docs/art/look_bible && git commit -m ... -- docs/art/look_bible`. Never touch, stage or revert anything else. Never push: main pushes.
- **No Godot imports.** Ask main for fresh frames.
- **References from the web are reference only:** keep them outside the repo in `C:\Users\munch\Desktop\survivorsunchained_inputs\look_bible_refs\`, with each source URL logged (`steam\sources.csv`). Only our own frames, short notes and links go in the repo.
- **Rule from the coordinator: every face on a board is an adult's (18+ game).**
- **Deliverables (RESUME next-wave item 1):**
  1. boards per subject: IS / ISN'T / the cheap trick / DONE;
  2. per-tier budgets (triangles, textures, materials, draw calls) from the measured numbers, with the measured HEAD on the page;
  3. the Prologue's asset inventory, each item keep, rework or build, with its owner lead;
  4. the tutorial's launch-ready checklist for the first 20-30 minutes.
- **No building before the bible's frames pass the owner.** Send each board to main with its path and one line; main brings it to the owner.
- **Effort:** coding and menial work go to su-worker or su-runner; judges are su-lead-max in the foreground (API judges are paused). Put `Context budget:` and your agent id in every helper brief.

## Done
- **1a armor metal, 1b skin:** with the owner (unchanged; keep 1a stable for armor 2 and touch-up 3).
- **Boards 1c-1j built** (d0f8dddd): pages `03_light_grade_mist.md` ... `10_props_flames.md`, boards in `look_bible_refsoards..10_*.jpg`, our 1:1 frames in `frames/` (copied from the cinematics worktree before it goes: c01-c04 shots, `play_12/20/33` from playc2, `play_w84` from playw, a 720p capture).
- **Round 1 of my judge (xhigh, two foreground su-lead-max judges):** 1g and 1j PASS with fixes; 1c, 1d, 1e, 1f, 1h, 1i FAIL. Every fix is written out, with replacement text, in `look_bible_refs\judge1_1c-1f_verdict.md` and `r1_1g-1j_verdict.md`. **I accept all of them**; apply them, don't re-judge round 1.
- Main got my first report (list + estimate). No board has gone to main yet.

## Next, in order
1. **Apply round 1** in `look_bible_refs	oolsoards_text.py` (captions, trick and DONE lines) and `gen_pages.py` (EXTRA: tier, owners, sources), then `python gen_boards.py` and `python gen_pages.py`. Reference swaps the judges named after looking: 1c PoE2 #3 -> `diablo4_03` (low sun, play camera); 1f add or swap -> `diablo4_08` (outcrops with no seam); 1i add `titanquest2_08` (people at the play camera); 1j Lies of P -> `nrftw_13` (hearth and candles, play camera). Still to find (look at thumbnails first; `steam_pull.py` can fetch other games):
   - 1d: a night river at the play camera (drop Kena: her age isn't stated, an 18+ rule risk). Try titanquest2_17, poe2_08, vrising, lastepoch.
   - 1e: conifers from the play camera (the judge found none in our D4 shots). Try vrising, valheim, enshrouded, lastepoch; else a cinematic conifer plus the whorl recipe.
   - 1f: a cobbled street at the play camera (bg3_00 or titanquest2_00 paving) and frost at the play camera (diablo4_00 or diablo4_07, snow); drop the Witcher 3 wheat field.
   - 1i: an ISN'T frame of our villagers at the town camera (playc2_52-61 or playw_*, in `.claude\worktreesgent-a59432fe3bfc6eb92\godot\.shots\`; copy it into `frames/`).
   - 1j: a camp fire reference (kcd2_02 may show one).
2. **Round 2:** one or two foreground su-lead-max judges at xhigh on the rebuilt boards, briefed like round 1 (copy the brief from the two judge spawns: whole-frame gate per board, the finish-line sentences, the six checks) plus "round 1's fixes are listed in the verdict files; check they landed". Round cap 2-3, then close what is left as known.
3. **Send the passing boards to main** in two batches (1c-1f, 1g-1j), each with its path and one line. Main judges and takes them to the owner. No building before the owner passes them.
4. **Budgets page** (`11_budgets.md`): inputs `survivorsunchained_inputs\look_bible_perf\summary.md` (frame times are in each case's .json/.csv; its fps columns read "-"), PERF_AUDIT, the inventory. Target: the owner's RTX 5080 at 1440p, plus a stated min-spec (e.g. 60 fps at 1080p medium on a Steam-survey-median GPU). Per tier: triangles, texture sizes, materials, draws AND shadow draws (the judges flagged shadow draws on every board: 2,246 at the Low Ford, 6,091 at the hub). Put the measured HEAD and the stale-import note on the page.
5. **Inventory page** (`12_inventory.md`): mark each row of `look_bible_refs\inventory\inventory.csv` keep, rework or build, with its owner lead; decide the rules, then a su-worker applies them.
6. **Checklist page** (`13_launch_checklist.md`): the first 20-30 minutes from `docs/cinematics/shoot/animatics/prologue.txt` (title and creation at the lowford camp, C01, the road, C02, the Warden fight, C03, the ford at dawn, C04 A, the road north, C04 B, the town), with DONE per beat, pointing at the boards.

Left: about 1.5 h for round 1's fixes and round 2, then budgets 1.5 h, inventory 1.5 h, checklist 1 h, the owner's round 1-2 h.

## Tools (`look_bible_refs	ools\`)
- `boards_text.py` (captions, panels, tiles with a focus point and zoom) -> `gen_boards.py [03 ..]` writes `b03..b10.json` and runs `board.py`; crops are computed (letterbox bars and an `area` box such as the PoE2 HUD-free region are excluded).
- `gen_pages.py` writes the repo pages 03-10 from the same text plus its EXTRA dict (one-line look, tier, measured table, owners, sources). Edit the text there, never the generated .md.
- `docs/art/look_bible/tools/lumstats.py [--crop x0,y0,x1,y1] files...`: luma p5/p50/p95, clipping, saturation, pools.
- `board.py`, `sheet.py`, `steam_pull.py`, `perf_lb.py`: as before.

## Gotchas
- Pictures cost more than they look: ten contact sheets and eight boards at 1280 px took this lead from ~60k to ~240k. View boards at 1280 px, changed tiles as a strip, and let judges see full size.
- The cinematics successor may re-shoot over `playc2_*` in its worktree: everything the boards use is already in `frames/`.
- Store shots: crop the HUD (PoE2 orbs, Titan Quest II bars); check every caption against the crop, since judges catch day-versus-night and missing-smoke errors.
- In perf summary.md the fps and ms columns read "-": read frame times from each case's .json or .csv.
