# Handoff: art direction, the look bible (look bible 1 -> 2)

Written by look bible 1 (agent a16fe961b1958e71b, su-lead-max), 18 October 2026, at its context budget. Read README.md beside this page first: it holds the owner's words and the page index.

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
- **1a, her armor metal:** `01_armor_metal.md`, board `look_bible_refs\boards\01_armor_metal.jpg`. Passed main, pushed (c1e1b888), relayed to touch-up 2 (a680d86c94df0eae7) and the armor pipeline (a6985f1db7321f528), and with the owner.
- **1b, her skin:** `02_skin.md`, board `boards\02_skin.jpg`. v2 swapped the child's face for an adult's (2fc3e33c). Main is taking it to the owner.

## In progress
- **The perf runner** (su-runner a2ec5dc8e65576b86, approved by main).
  - It runs `look_bible_refs\tools\perf_lb.py` in the main checkout under the godot turn, with `--stale-ok` because the heroine and hair imports there are stale (10 models). Main's conditions: no import, build or edits; a temporary `godot/override.cfg` (perf user dir), deleted after; a `git status` check for modified files.
  - Output goes to `C:\Users\munch\Desktop\survivorsunchained_inputs\look_bible_perf\`: `summary.md` (tables), plus `.json/.csv/.log` per case.
  - Measured HEAD cff7b440, C# build 17 Oct 23:17 (Debug): CPU main-thread ms are overstated, so budget from draws, primitives, VRAM and GPU ms.
  - First result, lf_hi (lowford at 1440p high, 300 s of the autopilot's prologue): GPU 5.5 ms mean / 15.8 p99, 408 draws + 2246 shadow draws, about 4.9M primitives, VRAM 2405 MB.
  - Its final report comes to a16fe961. If you don't get it, read summary.md and ask main whether the runner reported modified files.
- **The inventory extraction** (done, partial): `look_bible_refs\inventory\inventory.csv` (323 rows) and `summary.md`.
  - Code-made pieces (graves, fences, crypt, walls, towers, lamp posts, tents, the Warden, grass, flame cards) have no triangle counts.
  - Outfit triangle totals sum every variant in the file, not one worn outfit (PERF_AUDIT has the worn numbers).
  - The NPCs and the risen are Quaternius "Person" builds (Visuals.cs, npcs.json).
  - Title and creation are the lowford camp itself.
- **Technique sources** (done): `look_bible_refs\tricks_sources.md`, topics 1-10 with verified quotes. The strongest: Ghost of Tsushima's "stylized realism" (Patry, SIGGRAPH 2021), Filament's metal values, Sea of Thieves' shore foam, Valve's flow maps, Quilez and Mikkelsen anti-tiling, and Diablo IV's "old masters" / "Darkness does not mean bleakness".

## Next, in order
1. **Boards 1c-1j**, one per subject, same format. The ISN'T frames and their causes per area are in the audit verdicts: `.claude\worktrees\agent-a59432fe3bfc6eb92\tools\scratch\cin6\judge\gateA_verdict.md` and `gateB_verdict.md`, frames `godot\.shots\playc2_<cine>_s<id>_1.png`. Gameplay frames: `playc2_00..61.png`, `playw_*.png`.
   - Copy every frame you use into `frames/` (as with c04a_sa6 etc.): that worktree is removed when cinematics merges.

   | Board | ISN'T frames | Candidate refs (store shots in `look_bible_refs\steam\<game>\`) |
   |---|---|---|
   | 1c light, grade, mist (the biggest cheap lever) | C01 s7/s9, C04 B sb1 | diablo4_01/04/05/06 (play camera, pools of light, mist), lotf2023_02/07, liesofp_08, eldenring_00/07 |
   | 1d water and shore | C03 s12, C04 A sa1 | titanquest2_09/10 (iso shore), seaofthieves, avowed_00/08, rdr2 |
   | 1e foliage | C01 s7, C04 A sa2, sa8 | tsushima, kcd2_04/06, titanquest2_01/03/13, witcher3, hzd, kena |
   | 1f terrain and road | C01 s0, C04 B sb5 | kcd2_06, titanquest2_12/13, diablo4_08/09 |
   | 1g stone and the castle | C01 s8a | eldenring_04, liesofp_05/06, kcd2_07 |
   | 1h the town | C04 B sb1-sb5, playc2_51/54 | kcd2_01/07, witcher3, titanquest2_00, bg3_05, oblivionrm |
   | 1i NPCs | C02 s1/s9, C03 s1/s10, C04 B sb4/sb4b, playc2_30 | kcd2_09, banishers_02/12, dd2_03, bg3_00 |
   | 1j story props and flames | C01 s8a, C03 s6, C04 B sb4a | bg3_13, banishers_02, liesofp_00 |

   - Not yet viewed: tsushima, witcher3, seaofthieves, rdr2, hzd, kena, valheim, vrising, enshrouded, poe2, nrftw. Make a thumbnail sheet first with `tools\sheet.py`.
   - Tier 2 and 3 tricks go on 1i: shared base and atlas, tint variation, VAT. A tier-2 face in a cinematic close-up is staged (a hood, backlight, mist, the Warden's "two blue points" of eyes) or gets a hero head.
2. **Budgets page:**
   - Inputs: summary.md, PERF_AUDIT (heroine pieces: Warden 727k triangles and 95 draws a pass before merging; the hub's 6091 shadow draws), and the inventory.
   - State the target hardware (the owner's RTX 5080 at 1440p; pick and justify a min-spec, e.g. 60 fps at 1080p medium on a Steam-survey-median GPU), and set per-tier triangles, texture sizes, materials and draws.
   - Write the measured HEAD and the stale-import note on the page.
3. **Inventory page:** mark each CSV row keep, rework or build, and its owner. Tutorial environment lead: terrain, water, trees, castle, road, town. Story characters via Marionette: the drowned, the warden, Grimtunnel, villagers. Cinematics: staging. Touch-up and the armor pipeline: her.
4. **The checklist:** the first 20-30 minutes, from `docs/cinematics/shoot/animatics/prologue.txt` (C01 -> the road -> C02 -> the Warden fight -> C03 -> the ford at dawn -> C04 A -> the road north -> C04 B -> the town). Add the title and creation (the lowford camp at the fire), and DONE for each beat.

Left: about 4 h for the boards, about 1.5 h for the budgets, 1.5 h for the inventory, 1 h for the checklist, and 1-2 h for the owner's round.

## Tools (`look_bible_refs\tools\`; copies in the coordinator's scratchpad `lb\`)
- `board.py spec.json`: builds a board from a JSON spec (rows of tiles with crop boxes and captions, then text panels; `"fit": "contain"` keeps our letterboxed frames whole). Examples: `b01_armor.json`, `b02_skin.json`.
- `sheet.py OUT COLS THUMB_W files...`: thumbnail contact sheets.
- `steam_pull.py OUTDIR appid:slug ...`: official store screenshots (24 max per game) into `steam\<slug>\`, logged in `sources.csv`.
- `perf_lb.py`: the perf cases, described above.

## Gotchas
- Crop boxes guessed from thumbnails miss: the God of War crop landed on a shoulder. Preview a crop at 480 px before building the board.
- Store screenshots are mostly action shots, with few material close-ups. Crop hard, and caption what the crop teaches.
- Keep pictures out of long contexts: view each board once at full size, then fix by numbers.
- In perf summary.md the fps and ms columns read "-": the harness's JSON names those keys differently. Read frame times from each case's .json or .csv; the GPU ms, draws, primitives and VRAM columns are right.
