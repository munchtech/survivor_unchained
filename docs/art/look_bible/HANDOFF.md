# Handoff: art direction, the look bible (look bible 4: DONE)

Written by look bible 4 (agent a87527351a82e53df, su-lead-high), 18 October 2026. Read README.md beside this page first (the owner's words, the page index).

## State: the bible is complete
- **Boards 1a-1j:** passed by the owner ("The look bible boards 1c-1j pass. Build the tutorial to them.", OWNER_NOTES 18 Oct).
- **Page 11 budgets** (`11_budgets.md`), **page 12 inventory** (`12_inventory.md` + `12_inventory.csv`, 323 rows: keep 35, rework 33, build 236, test 15, cut 2, n/a 2; regenerate with `look_bible_refs\inventory\mark.py`), **page 13 launch checklist** (`13_launch_checklist.md`, 12 beats). Judged at xhigh: round 1 FAIL on all three (`look_bible_refs\judge\r1_11-13_verdict.md`: the perf run never left the road, so the Warden, dawn and gate are unmeasured; CPU, hitch, UI and texture budgets were missing; the test rule had no criterion), every fix applied (3b843d53); round 2 PASS on all three with four short replacements, applied by the lead, plus its optionals.
- Where we work: the main checkout, `docs/art/look_bible/` only, commit `-- docs/art/look_bible`, never push (main pushes).

## Open (for whoever picks the bible up; none blocks the build)
1. Board 1i's cost line (`09_npcs.md`, generated from `look_bible_refs\tools\boards_text.py`) could add "plus a hero head map where a close-up needs one" to match page 11's close-up NPC row. Page 11 governs meanwhile.
2. Page 11 added four armor visual slots to armor.md's Budgets line (skirt and cloak as large, legwear as a pair, head at most 15k) and the equip-time merge (her play draws 40 until it lands, then 20): sent to main to relay to the armor-and-weapons pipeline lead.
3. The first perf run is the tutorial environment lead's: Release build, a run that reaches stage=Exit, `lf_off_her` and `lf_off_volfog` re-run, `lf_off_terrain` added, the road's 70-170 s peak and post split by part.

## Tools (`look_bible_refs\tools\`)
- `boards_text.py` (captions, tiles with focus and zoom, panels) -> `python gen_boards.py [03 ..]`; `python gen_pages.py` writes pages 03-10 from the same text plus its EXTRA dict. Edit the text there, never the generated .md.
- `tilestrip.py OUT.jpg key ...`: renders chosen tiles exactly as the boards crop them, with their scale.
- `steam_pull.py OUTDIR appid:slug ...` (store search: `https://store.steampowered.com/api/storesearch/?term=...`); `sheet.py` contact sheets; `docs/art/look_bible/tools/lumstats.py`.
- Judge brief: `judge\judge_brief_common.md` (owner's words, finish line, whole-frame gate, checklist).

## Gotchas
- **Pictures cost ~7-10k tokens each in context:** 19 contact sheets took this lead from ~45k to ~245k. Shrink to ~1300 px, one look per question, and let judges see boards full size.
- Store shots: crop the HUD and logos (`area=` in `ref()`); check every caption against its crop.
- Judges write no files: save a verdict with `python tools/scratch/coordinator/lastmsg.py <agent-id> <out.md>` from the session's subagents folder.
