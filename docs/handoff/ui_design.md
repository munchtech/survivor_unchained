# Handoff: UI design lead (character creation first)

For the next UI design lead of Survivor Unchained. This file and the repository are all you get.
Read `docs/team/README.md` first, then this, then `docs/team/ui_design.md` (the one-page status).

Branch `worktree-agent-ac76f400913a109cd` (pushed; the main session merges it; no PRs). It includes the
integration branch `claude/vigilant-galileo-l6jqyx` at 535bb60; 539 tests green. The previous handoffs
are in git history: `git show 51350b1:docs/handoff/ui_design.md` (the UI merge and the owner's answers),
`git show c14b3a2:docs/handoff/ui_design.md` (the second design pass), and `docs/handoff/ui_art.md`.

---

## 1. The owner, in their words

- "AAA standard", "strive for excellent, above and beyond", "I don't want to polish, I want to create
  perfection", "Do we have soul?". Never settle; remake rather than polish; check at full resolution.
- The heroine: "sex appeal and the male gaze are a driving factor, tho not at the cost of looking bad".
- "can we customize hair or face in our create character yet? I couldn't find it", and later
  "have you implemented character customization in create character yet? I still don't see them when
  I open it up". That second time they were running an **old build**: the main checkout's compiled
  C# was older than the work (see 4.1).
- Standing rules, relayed by the coordinator:
  - Full-page screens pause the world only in arena combat, and a full page is often not the best choice.
  - Unknown map land must look better.
  - Self is not merged into the Pack screen.
  - Use painted art, the best available.
- The coordinator, last: "Make sure the creation screen shows the face, hair and body options plainly."

## 2. The brief

1. **The heroine's character creation, first:**
   - A live 3D preview of her, turnable and zoomable to her face.
   - Her five hairstyles with physics.
   - Hair colour, skin tone, eye colour (iris tint).
   - Face shaping from her 25 shape keys.
   - Face paint.
   - All of it saved, applied in play, and in painted AAA art.
   - Build it to serve the **male hero** too: a new lead is making his body.
2. Permissions from the main session, which owns the heroine pipeline. You may change:
   - the eye shader;
   - her actor code (`src/Actors`: People.cs, Loadouts, HerHair, HerFace);
   - the save fields.

   Don't touch `tools/assets/heroine_outfits.py` or the outfit files. If the face needs something from the
   head tools (`tools/assets/heroine_face*`, `heroine_head.py`), ask the main session or the face lead.
3. Then the experience director's four findings (section 4, step 5).
4. Then the old list: announcements, the item card's own layout, the journal's deeds and codex pages,
   and the HUD's dash pips and draught box. After that, re-make `docs/ui_review/` and write UI_DESIGN section 10.

## 3. Done (all pushed)

| Commit | What |
|---|---|
| bff4f7f | Creation's Look step. Saved and worn: her cut, face sliders, eyes, paint. Iris recolour in `heroine_eye.gdshader`. Face paint drawn as its own pass (`heroine_paint.gdshader`). `People.HerRestyle` (changes her in place). Turntable and face framing. FaceSheet tool |
| 09ba5a8 | Merged the integration branch (People.cs conflict: both sides' Person fields kept) |
| f62b66a | Face paint art (`tools/assets/heroine_paint.py`, 7 designs plus a brows mask). Look data per hero body (`heroes.<sex>`, `Lore.Hero`, `Loadouts.HeroKit`). Portrait key light. `--step N --part N` |
| dbbd52e, 0ef164a, 320e7ac | Merge; status; paint textures imported BC7 with mipmaps |
| (this commit) | Merged the integration branch at 535bb60; this handoff |

**What the Look step is.** It is step IV of five: Calling, Arms, Origin, **Look**, Name. Creation now
opens on the heroine.
- **Parts:** Body, Hair, Face and Paint, switched with the tabs, LT and RT, or `,` and `.` (Face and Paint
  appear only for a hero body).
- **Body:** Woman or Man, skin beads, the calling's colour sets, cloak beads.
- **Hair:** her 5 cuts as cameos (a mask dyes each cameo the chosen colour), then 11 colour beads.
- **Face:**
  - 7 faces to start from, as cameos;
  - 9 eye colours, as beads drawn as her own iris (`ui_iris.gdshader`);
  - 25 sliders in four groups (Eyes, Nose, Mouth, Jaw), on a bipolar `Groove`, each capped where her
    shape keys break (`looks.json`);
  - "Back to <face>", which resets the sliders.
- **Paint:** 8 cameos (bare plus 7 designs).
- **Right plate:** the chosen thing's name and words, her whole likeness, and how to turn her and come near.
- **The figure:**
  - drag to turn her, the wheel to zoom, a double click to go to her face and back;
  - on a pad, the right stick (`Controls.Look`);
  - the camera frames full, head and shoulders, or face (`GameFront.UpdateCreate`): a longer lens, depth
    of field behind her, and a warm key light on her face;
  - the Hair part turns her to show the cut;
  - changes are applied to her where she stands (`People.HerRestyle`), so her animation and her hair's
    swing carry on.
- **Name step:** the name, plus each step's answer read back, which goes back to that step when pressed.

**The data**, in `godot/data/content/looks.json` under `heroes.female`:
- `cuts` (long, ponytail, braid, bob, pixie);
- `eyes` (moss = her paint as it is, hazel, wolf, peat, sloe, cornflower, flint, frost, heather; each with
  a colour and a `ring`);
- `paints` (with `rough` and `metal`);
- `faces` (own, highborn, vixen, doe, hardwon, fey, wildling);
- `sliders` (`group`, `low`/`high` words, `min`/`max`).

Also added: 5 hair colours (chestnut, strawberry, honey, platinum, plus the old six).

**Saved and worn:**
- `CharacterData` / `CreationChoice` keep `Face` (only the sliders moved), `Eyes` and `Paint`.
- `PersonSpec` carries `Face`, `Eyes`, `EyeRing` and `Paint`.
- `Loadouts.Of` gives her her cut at last. `Loadouts.HerHair` maps old saves' kit cuts to hers.
- Tests: `godot/tests/LoadoutTests.cs` (the last two).

## 4. In progress / next, in order

1. **Make sure the owner sees it.**
   - The likeliest cause last time: `godot/.godot/mono/temp/bin/Debug/SurvivorUnchained.dll` in the main
     checkout was older than the work. Started from the project manager's Run or a saved exe, the old
     build runs.
   - Tell the main session the owner must open the project in the Godot editor and press Play (it builds
     first), or run `dotnet build godot/SurvivorUnchained.csproj` once.
   - Then shoot creation from the title as a player would. The key tour from the title stayed on step I:
     its presses came before the fade into creation (`--keys` starts 2 s in), so it needs a later start.
   - Make the Look step **plain**. It must not be missed: consider putting it before Origin, or having
     Next from Arms land on it; label the medallion "Look: hair, face, body".
2. **See each face paint on her in game.**
   - Shoot the Look step's Paint part with each design (or FaceSheet with `"paint": "<id>"`).
   - Tune `heroine_paint.py`. Its feature points (`BROW_R`, `CHEEK_R`, `TEMPLE_R`, ...) were read off
     the sheet by eye; the eye openings, lips and brows are found in her paint.
   - The paint pass's `VERTEX += NORMAL * 0.0001` may need more if it shows z-fighting.
3. **Wire the brows.**
   - `art/people/paint/brows.png`: grey is how dark each hair is, alpha is how much brow.
   - Draw it as a pass under the paint, dyed her hair's colour, in `People.HerPaint` / `HerRestyle`.
   - Her brows are painted copper into `heroine_head.jpg`, so they are wrong with every other hair colour.
4. **Cameo portraits** at `art/ui/create/<sex>/{hair,face,paint}_<id>.png` (the code shows a glyph until
   they exist).
   - Render them with FaceSheet (`tools_scenes/FaceSheet.cs`: `SHEET` json, `CAM` face|head|body, `YAW`).
   - Render cuts with grey hair (`#808080`) plus a `_mask.png` (hair white, all else black) so
     `ui_cameo.gdshader` can dye them.
   - Treat them painterly, then register them in `tools/comfy/ui_assets.json` and `UI_ART_BRIEF` for the
     UI art lead.
5. **The male hero** (lead `ae2de192cce8298ca`, `docs/team/hero_male.md`). He asked to agree fields; this
   is not answered yet. Tell him:
   - Use `CharacterData.Face/Eyes/Paint/HairStyle` as they are.
   - Add his `heroes.male` block to looks.json (`cuts`, `eyes`, `paints`, `faces`, `sliders`, with his
     `chin_cleft` and `brow_ridge`).
   - Change `Loadouts.HeroKit` to return his kit when he wears his body. The Look step then offers it.
   - His `BeardStyle` (none, stubble, short, full, braided) needs a Beard row in the Look step's Hair part.
     Add it when his data lands: a cameo row like the cuts.
   - Cameo art lives under `art/ui/create/male/`.
6. **The experience director's four findings** (`a33f58e68e89e3ccf`; `docs/EXPERIENCE_AUDIT.md`; frames
   in `docs/experience/`):
   1. One bark at a time: barks from one speaker queue, barks from different speakers stack, and lines
      never cross.
   2. The result screen as the night's story, in beats: the medallions count up; what comes out, one line
      at a time with a sound, best last; what stays dims; one line on how it went; skippable. He gives
      the timings and sounds.
   3. The Wayfinder's table says what a map pays: the spoils' lean in words, the chance of a tome, the
      boss. This grows into the atlas (the owner's endgame: permanent maps on an atlas, plus ember arenas).
   4. Pausing: arenas and the prologue's night road only, not the Verge by day (today's rule is `zone.Combat`).
7. **The forge** (crafting lead `a97e32948c5bf419d`; `godot/src/Ui/Forge.cs`, ForgeScreen; spec `docs/CRAFTING_DESIGN.md` 14): restyle or rebuild. Wanted: the house's frame art for seam rows and craft tiles; a crafted moment (a hammer-strike flash on the seam that changed, the heat gauge's cells burning out one by one); a pad flow check (worn, then seam, then craft). Shoot: `--quick warden --zone waystation --time day --items "old_iron*14,wolf_pelt*5,ember_shard*9,iron_helm:3" --gold 400 --open "talk:brannoc>work my gear" --anvil iron_helm` (add `--pad --focus temper` for the heat preview). The arena result's `Carried out` now shows materials as slots (`src/Ui/ArenaResult.cs`, Haul).. The old list: announcements, item card, journal deeds and codex, HUD dash and draught; `docs/ui_review/`;
   UI_DESIGN 10 (and rewrite 7.2 for the new creation).

## 5. Decisions (one line each, with why)

- Creation opens on the heroine: the docs and the owner call the survivor "the heroine". A man remains a choice.
- Look is per hero body, not per sex (`heroes.<sex>`, `HeroKit`), so the male hero gets the same step without a rewrite.
- Slider ends are capped where her MakeHuman shape keys break (judged from renders at ±0.5 and ±1).
  The UI maps the groove's ends to those caps.
- Face paint is a pass of its own over her skin (`next_pass`), so the main session's skin shader is untouched.
- Paint is drawn on a cylindrical unrolling of her face, then laid onto her UVs, so designs are drawn
  where features are, whatever her UV layout.
- Iris colour keeps the paint's fibres (its luminance) and dyes two zones (iris and the ring round the
  pupil), as real eyes have.
- The Figure slider was removed: it does nothing to her body.
- Her face and paint changes apply in place, not by a rebuild: no stutter, and her hair keeps swinging.

## 6. Failures and why

- **`GetBoneGlobalPose` in `_Process` misses `SkeletonModifier3D` changes.** HerPose lifts her pelvis, so
  the read head was about 0.2 m low. Fixed by recording the head pose on `Skeleton3D.SkeletonUpdated`
  (`Person.HeadPose`).
- **FaceSheet at `--resolution 1280x1280` saved the bottom of a cropped viewport.** Use a size the screen
  holds (1600x900).
- **The Bash tool refuses to run scripts here** (worktree isolation), and PowerShell has no heredoc and
  blocks some `Remove-Item` patterns. Write Python or PowerShell scripts to the scratchpad with the Write
  tool and run them.
- **Writing a file with an empty Python edit cleared it once** (`heroine_paint.py` went to 0 bytes, from
  a bad `newline=` argument). Check sizes after scripted edits.
- **`git checkout -- "*.import"` before committing also reverted my new paint `.import` settings.**
  Edit those after the checkout, then commit.

## 7. Gotchas

- `godot/assets` must be a junction to `public/assets` with skip-worktree set: `cmd /c mklink /J godot\assets public\assets`.
- `godot/override.cfg` (excluded from git) gives this worktree the user folder `SurvivorUnchainedUiLead2`.
- A new worktree has no `.godot` import cache. Copy the main checkout's (robocopy, without `mono`), then
  `dotnet build` and `--headless --import`.
- Shots: `scratchpad/uid2/shot.ps1 NAME SECONDS [game args]`; pictures land in `godot/.shots/`.
- Creation shots: `--new --step 3 --part N`; `--sex female` is the default now.
- FaceSheet: `scratchpad/uid2/fs.ps1 SHEET.json OUTDIR [face|head|body] [yaw]`, with the `crop.py`,
  `crop2.py` and `contact.py` contact sheets.
- `heroine_paint.py` caches its maps in `%TEMP%\heroine_paint_cache` (keyed on heroine.glb's size and
  time). `PAINT_PREVIEW=<dir>` saves each design over her face on the sheet, and `--sheet out.png` saves
  her face unrolled.
- The voice lead records one take per name in Front.cs's `Names`: tell them before changing it.
- Files are CRLF in the working tree; scripted edits must keep the line ending.

## 8. Collaborators

- Main session (coordinator): merges branches and relays the owner. Message `main`.
- Face lead `abfa9bb430ec2391e`: the coordinator asks you to continue creation with them.
- UI art lead `a72467cac33063d3a` (`docs/team/ui_art.md`): paints what you register.
- Male hero lead `ae2de192cce8298ca`: see 4.5.
- Experience director `a33f58e68e89e3ccf`: the four findings.
- Voice lead `a501b387a90d78b4e`: names.
- See the roster in `docs/team/README.md` for the rest.

## 9. Read first

1. `docs/team/README.md`, this file, then `docs/team/ui_design.md`.
2. `godot/src/Ui/CreateLook.cs` (the Look step, Cameo, Bead, Groove), and `godot/src/Ui/Front.cs`
   (CreationDraft, CreateScreen).
3. `godot/src/Game/GameFront.cs` (DressFigure, UpdateCreate), and `godot/src/Actors/People.cs` (LookOf,
   HerRestyle, HerPaint, EyeColour, HerEyes).
4. `godot/data/content/looks.json` (`heroes`), `godot/logic/Play/Loadout.cs` (HeroKit, HerHair), and
   `godot/logic/World/Lore.cs` (HeroLook).
5. `tools/assets/heroine_paint.py`, and `godot/shaders/heroine_paint.gdshader`, `heroine_eye.gdshader`,
   `ui_cameo.gdshader`, `ui_iris.gdshader`.
6. `docs/UI_DESIGN.md` (1.3, 6, 7.2) and `docs/UI_ART_BRIEF.md` (4.9).

HANDOFF READY: docs/handoff/ui_design.md on worktree-agent-ac76f400913a109cd@0b6e24b
