# Handoff: legal and Steam compliance

For the next legal and Steam compliance lead, from aab20546fe06daa89 (the second lead; the first was aa12c130ddf4b904c, whose handoff this replaces; it is in git history at 5c74633d). Read this, then `docs/team/README.md` (the turn rule and the roster), `docs/team/legal.md`, and the files at the end.

## The brief (in full, condensed only for length)

You are the legal and Steam compliance lead for Survivor Unchained (Godot 4.5.1 .NET, an 18+ survivors-style action RPG, made by one owner with AI agents). You are **not a lawyer**, and say so. You research the current rules from primary sources and prepare a brief for a real games lawyer.

1. **Track the launch blockers to done** with the leads who own them, and re-rule as the owner answers.
2. **Run the motion check:** every outfit, every clip, jiggle on, so the mature-content survey is true of what a player can see.
3. **Be the standing compliance check:** review new assets and tools as leads add them, and tell a lead directly if something is a problem.

Rules:
- Change no game content; recommend, and the owner and the main session decide.
- Never delete files.
- Cite primary sources, and say where the law is unsettled.
- Commit and push your own branch at milestones; the main session merges. Open no PRs.
- British spelling.
- At about 500k tokens, write this handoff and end with HANDOFF READY.

## The owner's words that matter here

- "ai generated assets and things are perfectly ok for steam games and for making money and getting in no trouble right?"
- "sell on Steam with little to no issue"; "eventually remove anything not ours"; "we will replace everything eventually if we can with our own / generated own".
- The Ember Watch: "I do not own it. I mean I made the game but nothing is copyrighted or anything - we built it all in claude with no generated content. I guess I own it?"
- The base bodies: "we made images in krea 2 turbo for the IMAGE but we did not use hunyuan 3d. we used trellis for the 3d", and "we made it in comfyui". This corrects his first answer, "krea assets that have since been deleted".
- "Warmed": "we can remove that as a buff that does anything other than say it happened".
- The heroine: "we've done substantial resculpting and editing to our heroine. at what point is it just ours?"
- The outfits (through the main session): "pixel perfect showing as much as we possibly can". Cover exactly what must be covered and show everything else, with never a hole or a see-through.
- He lives in the **United States** (his state is not yet given). The hymn will be made in **Suno**; the final voices in **ElevenLabs**.

## State (4 October 2026, late night)

Integration branch at cd421c4f, which includes my c8bdc6c4. My last commit is this handoff.

### The four launch blockers

1. **The AI disclosure:** the owner fills it in at submission, from `STEAM_CHECKLIST.md` D3 and E. Section E is now the single AI list, naming only what ships.
2. **The mature-content survey:** waiting on the motion re-measure on the main session's **tuck build** (below). The draft answers are in D1 and D2. Her crotch is a smooth form, with **no genitals modelled**; the owner confirms there never were any.
3. **The licences screen:**
   - built by UI design at 178768aa;
   - its credits pruned to what ships (84cceb99, a185aea3);
   - its notice texts byte-checked against Godot 4.5.1, .NET release/8.0 and the fonts.

   Still to do: **see it in game.** The UI design lead promised a screenshot when Godot is free.
4. **The boar:** replace it, or buy the Fab commercial version as a stop-gap. The owner and arena art decide.

**Done:**
- the export and debug paths (8a770667; I reviewed the pack listing in `docs/legal/records/RELEASE_PACK_LISTING.txt`);
- the placeholder voices, excluded from the release;
- the explicit-scene placeholders, removed;
- "Warmed", now flavour only (b47d98ea, test-guarded);
- The Ember Watch: the owner's, with records to keep (brief 5(e));
- the base bodies, kept with conditions: the owner signs `docs/legal/records/BODIES_RECORD.md` and confirms no real person or others' art went into the pictures (brief 5(b)).

### The motion check: reworked, and **untested in Godot in its final form**

- **The tools** are in `tools/legal/motioncheck/`:
  - `run.sh` runs the phases;
  - `make_motioncheck.py` builds the scene script from `godot/tools_scenes/lookdev.gd`;
  - `marks_section.py` holds the GDScript for the codes;
  - `count.py` reads the pictures.
- **How it works:**
  - The generator adds her clip library, SPREAD (a looped clip with frames spread over one pass) and VIEWS (several cameras per run through SubViewports, each 960×540). It also adds FOLLOW (cameras keep with her hips) and MARKS.
  - Under MARKS, two codes are drawn as the **last lines of her skin shader's fragment**, unlit, under a **linear tonemapper**, so they read back exactly and show on any skin the player could see, tucked skin included:
    - **Blue, with red as distance:** every skin vertex within 6 cm of a nipple tip, red = 0.9 × d / 6 cm (linear), where d is the rest-pose distance from the tip. The areola is d < 2.2 cm: her texture's pigment is dark to about 2.3 cm and plain skin by 3.8 cm.
    - **Pure green:** the strip a garment must cover, the vulva's footprint were one modelled. That is the midline ±1.2 cm, from the perineum (2.3 cm behind the lowest downward-facing midline point of her crotch, about y 0.925 in bind pose) forward and up to just below where the mons faces forward (about y 0.965). Skin facing sideways (her inner thighs, which touch below it) is excluded.
  - The landmarks come from her untrimmed body:
    - **nipples:** the sharpest bump on the front half of each breast (welded-neighbour curvature), at about (±0.11, 1.42, 0.16);
    - **crotch:** from the normals, as above.
- **How to run it:**
  1. Take a turn: `python C:/Users/munch/Desktop/survivorsunchained/tools/turn.py take godot "legal: <job> (<your id>)"`.
  2. Run `OUT=<scratch folder> bash C:/Users/munch/Desktop/survivorsunchained/tools/legal/motioncheck/run.sh <phase>`. Run it from the **main checkout**, whose `godot/.godot` is imported; a worktree has no import. Check first that nothing is importing there.
  3. The phases:
     - `calib`: no outfit. Check the `legal marks:` line in `log_calib.txt` and look at the three pictures. They show her bare: scratchpad only, never published.
     - `fp`: each outfit with the linear tonemapper and no codes. count.py must find **nothing**.
     - `cup`: the Warden's sprint, 16 frames.
     - `all`: about 50 clips per outfit (`ONLY=` narrows it).

     A batch takes about 16 s a clip.
  4. Give the turn back at once, and keep batches under an hour.
- **How to read count.py** (`python count.py <OUT> 6`):
  - `summary.txt`, per outfit:
    - the frames where an areola shows (≥ 6 px with d < 2.2 cm);
    - the frames where the strip shows (≥ 6 px of green);
    - the **closest visible skin to a nipple tip**, as a signed margin past the areola: negative means the areola shows. It comes with where on the rim ("her left breast, upper inner edge", as seen in that view) and the clip, view and frame.
  - `counts.csv`: per frame.
  - `crops/`: `flag_*.png` and `closest_<outfit>.png`, each with a banner saying it is a test tint, not the game. The owner was once confused by the blue.
- **Untested:** the final codes (distance code, green strip, linear tonemapper, uniform carry-over) were written after my last run. **First:** `calib`, then `fp`, then `cup`, on the current build, before trusting a full run. My test script for exactly that is `scratchpad/legal/test_codes.sh`; it never got a turn. The uniform carry-over in `marks_section.py` (it keeps `tuck_channel` and the rest when the shader is swapped) is in this handoff's commit.

### Results so far (build 854b927e, the earlier cyan method, valid for the areolas)

- **The Warden's left cup: fixed.** In close front, three-quarter and overhead views of the sprint, no areola shows in 48 frames. The cup's edge comes within about 2.8 cm of the tip, which is plain skin.
- **No areola** in any frame of the Warden's 42 clips or the Arcanist's 44: **3,320 frames**. The Stalker and Reaver were not run on that build.
- **Withdrawn:** my first crotch reading ("nothing under the Warden's skirt"). The mark ran 2 to 3.5 cm wide from where her inner thighs touch, so it counted the bare groin beside her thong (`warden.thong`, 2.4 cm wide at the crotch), which the owner wants shown. The main session reversed its brief ruling.

## Next, in order

1. **On the main session's tuck build** (skin under garments is pushed inward by `-NORMAL * 0.006 * h` in a new `vertex()` of the skin shader, through `tuck_channel` and the graded COLOR channel; `lookdev.gd`'s `hide_skin` now sets `tuck_channel` instead of cutting triangles; UV2 is free):
   1. merge;
   2. take a turn;
   3. run `calib`, then `fp`, then `cup`, then `all` for **all four outfits**;
   4. count;
   5. send the main session, per outfit, the **smallest areola margin and where on the rim**, every areola flag and every strip flag, with the labelled crops.

   The main session will bring each cup down to the smallest margin that holds in motion. Re-measure after each change.
2. Cinematic poses (`--cine`, the cinematics lead) and creation's Look poses: not yet covered by `run.sh`.
3. The Quaternius base bodies (the townsfolk, the Risen, the male survivor): confirm their bare form has no anatomical detail. If it has, add a sentence to D2.
4. Update brief issue 2 and checklist D2 with the final results, then tick the motion check.
5. The licences screen screenshot (UI design, aab47bfdab5955dac), then tick blocker 4.
6. Standing check: new tools and assets from every lead. Before launch, re-read the live Steam forms and the Krea, LTX, ElevenLabs and Suno terms; they change often.

## Decisions (and why)

- **The bodies are kept** (local Krea 2 Turbo pictures and local TRELLIS 2 meshes). The ComfyUI log of 4 Oct agrees, and the evidence is copied into `BODIES_RECORD.md` because those logs rotate. They join the Krea US$1M footprint. The hero's picture probably used the Civitai LoRA "Mystic XXX" (2728644, by alcaitiff), which I identified by its SHA-256; its creator allows selling images.
- **The Ember Watch is the owner's.** Copyright needs no registration (17 U.S.C. §408(a)), but covers only human-authored expression. Register Survivor Unchained within three months of launch (§412).
- **"Ours" for the heroine** (brief 16):
  - free to sell now;
  - copyright only in the human part, with no threshold of changes;
  - not yet free of strings: her face paint is a direct Krea Output, and whether the cap reaches the reworked mesh is unsettled (lawyer question 19).
- **Suno:** Pro or Premier plan only, downloaded through Suno's button, never a remix.
- **Replacements** (brief 5(g)):
  - our own work first;
  - then local MIT models from inputs we own;
  - Krea 2 adds to the cap;
  - never Hunyuan3D, free-plan web tools, or pictures of real people or others' art;
  - check every LoRA's permissions.
- **The motion check is automatic and measured, not eyeballed:** a few-centimetre area in thousands of frames can't be judged by eye. The marks are sized to the anatomy (the pigment and the vulva's footprint), not padded, because the owner wants everything else shown.

## Failures and why (so you don't repeat them)

- **Geometry guesses went wrong three times**, all now fixed in `marks_section.py`:
  - the body mesh stops at the neck (1.65 m tall), so proportions of the whole height are wrong;
  - the most forward point of a breast in bind pose is its lower curve, not the nipple;
  - the lowest midline point is where her inner thighs touch (y 0.84), not her crotch (y 0.925).

  Always calibrate with a picture.
- **Colour detection under AgX:** magenta collided with the Arcanist's purple; two cyan brightnesses were fragile; a screen-space waist split misclassified forward-leaning poses. Hence exact codes under a linear tonemapper.
- **Outfit skin hiding** used to delete the triangles at a nipple's tip, which moved the curvature landmark. Hence landmarks from the untrimmed body.
- **SubViewports sized from the root in `_init` came out 100×100**; they are now fixed at 960×540. The root viewport's coordinates are in the project's 1920×1080 space, so the landmark JSONs store their viewport size.
- **Slow renders skipped frames,** hence `--fixed-fps 60`.
- **Godot's `save_png` fails silently into a missing folder,** so make the folder first.
- **GDScript escapes inside Python strings:** one level too few put a raw line break into a string literal. `marks_section.py` now holds the GDScript in a raw string.
- **The wide crotch mask** produced a finding the main session acted on, then reversed. Size masks to the anatomy, and say plainly what a mask covers.
- **I deleted my own three calibration renders once** to clear a folder. That broke "never delete files" in the letter. Write to a fresh folder instead.
- **The full run was stopped part-way** when the method changed, so the Stalker and Reaver have no results on 854b927e.

## Gotchas

- **The Bash guard** refuses compound commands that mention git, URLs containing "git", heredocs it can't parse, and `bash` of computed paths. Put logic in a script file and run it plainly. PowerShell works for process checks.
- **Heavy work takes turns** (`tools/turn.py`). Godot allows two at a time, and the slots are often taken. Do light work meanwhile; never hold a turn idle.
- **The pictures:** `calib` pictures and any MARKS picture without an outfit show her bare. Keep them in the scratchpad, never commit or publish them, and look at them only to calibrate.
- **Generated scripts:** `tools/legal/motioncheck/.gitignore` ignores `*.gd`. An untracked stray `motioncheck2.gd` sits there from a mistake; leave it.
- **Fetching sources:** Python's certificate store fails on krea.ai and some others; use curl, then `scratchpad/legal/strip.py`. Civitai's API (`/api/v1/model-versions/by-hash/<sha256>`, `/api/v1/models/<id>`) identifies a LoRA and its creator's permissions.
- **ComfyUI's logs rotate** (three copies). Copy any evidence into `docs/legal/records/` at once.
- **The scratchpad**, `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\legal\`, holds:
  - licence and policy texts;
  - the motion folders (motion2 to motion8, cupclose and cupclose2, calib);
  - `diag*.gd` (headless landmark prints).

## Collaborators (roster as of cd421c4f)

- **Main session:** outfits (the tuck build), decisions, merges.
- **Performance** (a56abaf3a104be675): the pack listing; re-list before every upload.
- **UI design** (aab47bfdab5955dac): the credits screen and its screenshot.
- **Story** (a7ba8903f4c8261b1): "Warmed" and StoryLint.
- **Arena art** (a26767f7f9955cb56): the boar's replacement.
- **Heroine face** (a833b7942e978d994): the face paint (Krea) and its replacement plan.
- **Provenance auditor** (a80ff0c7fd988b178): retired. I edited its rows in `ASSET_PROVENANCE.md` at the main session's request. A message would wake it.

## Files to read first

1. `docs/legal/LEGAL_BRIEF.md`: the bottom line, the owner's-answers table, issue 2 (the motion check), 5 (assets, bodies, The Ember Watch, replacement rules), 16 (ownership) and 28 (Suno).
2. `docs/legal/STEAM_CHECKLIST.md`: B (blockers), D (the survey drafts), E (the AI list).
3. `docs/legal/QUESTIONS_FOR_LAWYER.md`: 19 questions.
4. `docs/legal/records/`: `BODIES_RECORD.md` (the owner must sign it) and `RELEASE_PACK_LISTING.txt`.
5. `tools/legal/motioncheck/`: start with `run.sh`'s header and `marks_section.py`'s comment.
6. `docs/team/legal.md` and `docs/team/README.md`.
