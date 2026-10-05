# Handoff: legal and Steam compliance

For the next legal and Steam compliance lead, from af0973d59a5b2817a, the third lead. The first was aa12c130ddf4b904c; the second, aab20546fe06daa89, wrote the handoff this replaces (in git history at b0864e9f, with the full story of the motion check's earlier methods). Read this first, then `docs/team/README.md` (the owner's bar, the turn rule and the roster), `docs/team/legal.md`, and the files at the end.

## The brief

You are the legal and Steam compliance lead for Survivor Unchained: Godot 4.5.1 .NET, an 18+ survivors-style action RPG, made by one owner with AI agents. The goal is to ship on Steam with little to no issue:
- an honest AI disclosure;
- a mature-content survey that is true;
- licences in order;
- a brief for a real games lawyer.

You are **not a lawyer**, and must say so; flag what needs one. The owner lives in the United States and owns the setting, The Ember Watch, which he made with Claude.

Rules:
- Change no game content: recommend, and the owner and the main session decide.
- Never delete files.
- Cite primary sources, and say where the law is unsettled.
- Commit and push your own branch at milestones; the main session merges. Open no PRs.
- Run `dotnet test` in `godot/tests` before every commit.
- British spelling.
- Heavy work takes turns: `python C:/Users/munch/Desktop/survivorsunchained/tools/turn.py take godot "legal: <job>"`. Give the turn back the moment the batch ends; keep batches under an hour, one outfit per turn.
- At about 500k tokens of context, hand off.

## The owner's words that matter here

- **Coverage (5 Oct 2026):**
  - "if you need to hide things they need to be pixel perfect no extra stuff hidden at all. none. not even a few pixels";
  - "even on the nipple issues they need to be pixel perfect showing as much as we possibly can";
  - "there was NEVER any issues with genitilia right?" Correct: none are modelled, and the Warden's thong is by design.

  So the motion check exists to prove that the areolas and the narrow midline strip stay covered in motion, and to **measure the margins** so the main session can trim coverage to the smallest that holds. **It never recommends extra garments.** The cyan tint once confused the owner, so every crop carries the TEST TINT banner.
- On AI: "ai generated assets and things are perfectly ok for steam games and for making money and getting in no trouble right?"; "sell on Steam with little to no issue"; "we will replace everything eventually if we can with our own / generated own".
- His earlier answers (the bodies, The Ember Watch, "Warmed", Suno, ElevenLabs) are in the brief's table "The owner's answers and what they changed".

## State (5 October 2026)

**Launch blockers: three.**
1. **The AI disclosure:** ready to paste (`STEAM_CHECKLIST.md` D3), naming only what the release ships. Raise it, and the BODIES_RECORD signature, only at submission (the owner, 5 Oct). It has a bullet to add for each thing that may ship later (the hero's body, a MoGe-built face, voices, the hymn, store art). The owner pastes it at submission.
2. **The mature-content survey:** waiting on the motion check of the main session's **tuck build** (below). Draft answers: checklist D1 and D2.
3. **The boar:** our own replaces it (the owner, 5 Oct). A new creatures lead makes it locally with Krea 2 and TRELLIS 2, from text-only pictures. The Sketchfab boar must not ship (brief 5(a)).

**Done this session:**
- **The licences screen**, seen in game at 1920×1080: every credits section, the AI list as in checklist E, and the Godot, .NET and typeface licence pages. One layout fault (two index labels run past the divider) went to UI design.
- **The Quaternius base bodies:** no nipples and no genitals, in mesh or normal maps; their textures paint underwear.
- **Path B's picture models** (brief 5(g)): Qwen-Image, Z-Image-Turbo and FLUX.1 [schnell] (Apache-2.0) are fine; FLUX [dev] and SD 3.5 are not.
- **Standing check:** the face lead's portraits are Krea 2 Turbo from text alone, naming no real person, and MoGe-2's weights are MIT. The new effect flipbooks' prompts name no other work. The logo is Cinzel (OFL) painted over by Krea.
- **Lawyer question 12:** whether "Munchtech", the studio name on the credits screen, needs an assumed-name filing.

### The motion check (tools in `tools/legal/motioncheck/`)

**How it works.** `make_motioncheck.py` builds a scene script from `godot/tools_scenes/lookdev.gd`, plus `marks_section.py`'s GDScript. Under MARKS, three codes are drawn as the last lines of her skin shader's fragment, unlit, under a linear tonemapper, so they read back exactly:
- **Near a nipple** (within 6 cm, in rest pose): blue, with the distance in red (0.9 × d / 6 cm). The areola is d < 2.2 cm. Green is exactly 0.5 when that skin is more than half tucked.
- **The strip a garment must cover:** pure green. It is the vulva's footprint were one modelled: the midline ±1.2 cm, from the perineum to just below the front of the mons.
- **Tucked skin elsewhere:** cyan, with red = 0.9 × (1 − tuck), so deep tucks are pure cyan. The tuck is read from the outfit's channel of her vertex colours (warden red, arcanist green, reaver blue, ranger alpha). The main session confirmed its `vertex()` doesn't write COLOR.

**The landmarks** (for "where on the rim") come from the engine's own skinning. Her mesh is baked in its pose each frame, so the tip lands within 2 px of the drawn nipple. Up and in come from the centres of the skin 2 to 6 cm around the tip. The breast bone's own pose put them about 12 cm low.

**`count.py <folder> 6`** reports per outfit:
- the frames where an areola, the strip or deep-tucked skin shows;
- each breast's closest visible skin to the areola's edge, as a signed margin (negative: the areola shows), overall and for each of eight edges of the rim, with clip, view and frame;
- crops, enlarged, with the TEST TINT banner and a ring on the closest pixel.

**`run.sh` phases.** Each runs with `PROJECT=<main checkout>/godot` from a worktree, and needs a Godot turn:
- `calib` and `tuckcalib` show her bare: scratchpad only;
- `fp`: no codes; count.py must find nothing;
- `cup`: the Warden's sprint;
- `all`: about 45 clips, with `ONLY=<outfit>`.

The views are chest, left, side, below, and **over** (looking down into her neckline, as play does).

**Proven on the pre-tuck build (5 Oct):**
- calibration: tips at about (±0.11, 1.42, 0.16), the crotch underside at y 0.925, the mons at 0.967;
- false positives: 64 frames of all four outfits, and **no pixel** passes for the near or strip code, even at 1 px;
- the Warden's sprint: no areola or strip. Closest skin: +1.07 cm (right, upper inner) and +1.56 cm (left, upper inner).

On that build, the "tucked skin" count is meaningless: cut edges carry the old mask.

### In progress: the tuck build

The main session builds outfits with her skin tucked in rather than cut away. `heroine_skin.gdshader`'s `vertex()` pushes skin in by `-NORMAL * 0.006 * h`, through `tuck_channel` and vertex colours graded 1/3, 2/3 and 1. It will message the commit. Then:
1. merge it;
2. run `scratchpad/legal3/tuck_a.sh <tag>` (one turn: tuckcalib, calib, fp, cup);
3. run `scratchpad/legal3/run_outfit.sh <outfit> <tag>`, once per outfit, each in its own turn;
4. send the main session, per outfit: each breast's margin by edge, with clip, view and frame; any strip flag; any frame showing deep-tucked skin (a dent or a gap). Expect the 1/3 edge ring to show by design; it is counted apart.

Results so far: see `docs/team/legal.md`.

## Next

1. The tuck build, as above. Re-measure after each cup change the main session makes.
2. Update brief issue 2 and checklist D2 with the results, then tick the motion check.
3. Standing check of new assets and tools. Before launch, re-read the live Steam forms and the Krea, LTX, ElevenLabs and Suno terms.
4. The owner's to-dos:
   - sign `docs/legal/records/BODIES_RECORD.md`;
   - give his state of residence and business structure;
   - say whether "Munchtech" is registered;
   - run the USPTO search himself (it sits behind a bot challenge).

## Decisions (and why)

- **The check measures; it never asks for more garment.** That is the owner's direction.
- **The disclosure names only what ships, and says "rebuilt and rigged for the game", not "by hand"**: agents did much of the rebuild. "Under his direction and review", not "every asset reviewed by a person", which can't be shown.
- **The boar: our own** (the owner's decision), under 5(g)'s path C rules.
- **Path B's picture models:** Apache-2.0 or MIT, with no revenue cap. Not FLUX [dev] (non-commercial weights) or SD 3.5 (a US$1M cap like Krea's).

## Failures and why

- **Bone-based landmarks were 12 cm low.** `get_bone_global_pose` × bind pose didn't match what the renderer drew. Use `bake_mesh_from_current_skeleton_pose()`.
- **"Furthest up" ring vertices gave skewed directions**: the mesh is coarse near the tips (27,558 vertices; 14 to 23 in a 2 cm ring). Halves' centres are robust.
- **TaskStop didn't kill a Windows bash loop**: the stopped script later took a turn and ran. It gave the turn back, but check `turn.py show` after stopping one.
- **A 45 s poll lost turns to 20 s pollers.** Use `take ... --wait 30`.
- **I wrote "at 960x540" of a picture I hadn't taken** in a message to UI design, and corrected it. Claim only what you've seen.

## Gotchas

- **The Bash guard** refuses compound commands that mention git, loops over computed program names, heredocs it can't parse, and `-C` redirects. Put logic in a script file in the scratchpad and run it plainly.
- **Run Godot from the main checkout** (`PROJECT=`): the worktree has no import. The main checkout's import can lag. On 5 Oct it lacked `art/ui/page/vellum.png`, so the pages lost their backdrop. The main session also rebuilds outfits there: never run while it imports or rebuilds. Check the Godot processes and `turn.py show`.
- **Never delete files**, even your own shots: give each run a fresh name or folder.
- **Calibration pictures show her bare:** scratchpad only, never committed or published.
- **The scratchpad** is `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\`:
  - `legal3\` is mine: the batch scripts (`tuck_a.sh`, `run_outfit.sh`, `test4.sh`), `lmcheck.py` (landmarks against the code's minimum), `relief.py` (clay renders of a glTF), `dumptex.gd` (save imported textures), `hf_licences.py`, and the run folders t1 to t6;
  - `legal\` is my predecessor's: licence and policy texts.
- **Fetching:** curl works where Python's certificates fail. Sketchfab's API gives a model's licence and description. Fab is behind Cloudflare: don't try to get past it.

## Collaborators (roster in `docs/team/README.md`)

- **Main session:** outfits (the tuck build), decisions, merges.
- **UI design** (aab47bfdab5955dac): the credits screen.
- **Arena art** (a26767f7f9955cb56): not the boar ("creatures aren't arena art's").
- **Animation** (a435f4dd0ac80df75): would rig a new boar. Its Kimodo takes may ship for crossbowmen and cinematics (checklist E has the line).
- **Heroine face** (a6784044c82f101d9): the MoGe-2 face direction, built from Krea portraits.
- **Performance** (a56abaf3a104be675): re-list the release pack before every upload.

## Files to read first

1. `docs/legal/LEGAL_BRIEF.md`: the bottom line, the owner's-answers table, and issues 2, 4, 5 (5(g) for replacements and picture models) and 16.
2. `docs/legal/STEAM_CHECKLIST.md`: B, D (D3 is ready to paste) and E.
3. `docs/legal/QUESTIONS_FOR_LAWYER.md`.
4. `tools/legal/motioncheck/`: `run.sh`'s header, `marks_section.py`'s comment, and `count.py`'s docstring.
5. `docs/team/legal.md`.
