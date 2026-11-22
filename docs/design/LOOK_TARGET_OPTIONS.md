# The den's look target: options for the owner's pick (GAME_PLAN task 6, decision 6; 22 November 2026)

Package P5, lead agent-a730ef56e5a3de866, branch `look-target`. **The pick is the owner's.** This page sets out the options and the lead's recommendation. Nothing is built from it until the owner picks: no shader, light or asset work starts before the pick.

**What the spec asks** (GAME_PLAN decision 6, task 6):
- a paint-over of three real den frames at the game camera, approved by the owner, then frozen as numbers;
- "Use your reference's palette only, with the value plan from D3";
- the pass is the owner saying "this is the game".

D3's value plan:
- the ground is the darkest and quietest group;
- the characters are lighter and more saturated than the ground;
- effects are the brightest group.

## Where this stands: no paint-over passed, so the options are written

No painting reached the bar. Two judged rounds failed all three options. After them, two more builds were made: a rebuild on the judge's own route, and a fresh max-effort solver's hybrid. Their own makers read both as failing, so the third and last judged round was not spent on them.

The brief's fallback applies: "stop at the screenshots plus a written description of each option and say so." **No paint-over is shown: none passed the judge.**

**Later on 22 Nov:** a second lead tried the one route left, ChatGPT's image edit, and spent the third and last judged round on it. It also failed, all three options, but it is the closest result so far and its faults are named. See "The ChatGPT image-edit route" below. The sheets are kept marked "did not pass"; none is offered as a pick.

**The screenshots** (the game today: 1:1, game camera 62 degrees down, 24 m, FOV 34, 1920x1080, HUD off; she is about 70 px tall):
- `C:\Users\munch\Desktop\survivorsunchained_inputs\scratch_look\den_frame_1.png` is a Clearing with a pack on her.
- `den_frame_2.png` is a second Clearing with a pack.
- `den_frame_3.png` is the ruler's clearing, with pits. It has a burned-in subtitle; world text shows even with the HUD off.

All three come from the integration head at 0c62da9bb, on Godot 4.5.1, seed 11.

Each option below uses only colours in the owner's 19 Nov reference (`owner_ref_night_day_colors_19nov.webp`; the night panel is the left half, the day panel the right). Every option keeps D3's values.

## Option A: the day palette

The ground becomes warm amber-orange packed earth: the reference's day ground is about L 49, chroma 53, hue 50 in CIELAB (the judge measured it). Its shade is burnt umber. Golden sun patches lie flat where light falls. The roots are red-brown, the stones pale lilac-grey with olive moss on top, the shadows violet-grey.

It changes the den the least from today's brown, and it is the friendliest read. **The risk** is that everything goes one orange. Every A attempt drifted there, and the frame read either mauve or flat orange. A needs the lilac stones and violet shadows as a counterpoint. Its warm ground is also closest in hue to the heroine and the effects, so they can only stand out by value.

## Option B: the night palette

The earth and roots become deep indigo and blue-violet, the stones blue-violet. Pale cyan moonlight patches fall from above, and glowing cyan-teal mushrooms run along the foot of the root walls.

Warm figures and effects stand out by colour as well as value. **The risks:**
- The reference's night light is blue too: its brightest pixels sit at about (a, b) = (-2, -31) in CIELAB. Every attempt at a lit night floor slid toward pink, which is outside the night palette.
- The near-black wolves sink into a dark blue ground unless they get a rim.

B is the only option whose walls already took the inked, two-tone look in the round-2 paintings.

## Option C: cool shade, warm light

The floor and root walls take the night panel's blue-violet shade. Warm gold from the day panel shows only where light falls, as hard-edged patches. The teal mushrooms stay along the root walls.

D3 gets a second axis: temperature as well as value. Warm figures, effects and light stand on a cool ground, which is the split strong top-down ARPGs use for readability (my reading; not measured here). **The risks:**
- The warm patches must be cut-out cel shapes. Every attempt made them blobs or splats.
- The walls need their own detail, or they dissolve into the flat shade.

## The lead's recommendation (mine, not a ruling)

**C, cool shade with warm light, as the direction.**
- It is the only option where D3 is helped by colour as well as by value. Warm danger marks and a warm heroine would stand out on a cool ground. That also attacks the den's top clarity problems (DEN_CLARITY.md C1-C4, C6): the danger mark in the blood's colour, the pools as bright as she is, and the pack swallowing her.
- The round-1 judge ranked C first on direction. Round 2 ranked it last on execution, because its walls dissolved; that is a fault of the painting, not of the palette.
- B is my second choice.

## What was tried, and why it did not reach the bar

Every painting was made on this machine with the art-style lane's paint route (`tools/scratch/art_style/paint.py`):
- Z-Image Turbo (Apache-2.0, `docs/legal/LEGAL_BRIEF.md`) with its Fun ControlNet Union;
- SAM 3 for the masks.

No account, key or credits were used. The scripts are backed up in `survivorsunchained_inputs\scratch_look\scripts\`, and the round-by-round record is in `scratch_look\STATE.md`. The paintings stay in the worktree's git-ignored `godot/.shots/look/paint/` (r1-r8); none is shown, since none passed.

| Round | What | Result |
|---|---|---|
| r1 | Plain img2img over the brown frame | The palettes did not take, and it invented a giant trunk. Not judged |
| r3 | Colour pre-grade from the reference, then img2img | **Judge 1: all fail.** Figures repainted or invented, floor busier than the source, light pools painted as orbs, pits painted as mounds |
| r4-r6 | Masks, a keep map, figures pasted back, a flattened floor | **Judge 2: all fail.** Most foes were lost (SAM found one per word), the pasted figures were neon, the floor turned to fog and mush, the layout drifted |
| r7 | The judge's own route: Canny plus depth control from the source, hard bands, hard light | Not judged. Posterised into flat vector fills, off-colour blobs |
| r8 | Solver hybrid: only the walls painted, floor and figures built by script | Not judged; the solver's own verdict is a fail. Figures and layout pass by construction; the floor reads as flat tones or blobs |

**The two blockers.** These are measured or seen in the rounds; the cures are my reading.

1. **A painted floor.**
   - The local model gives fog, mush or flat vector fill.
   - A script gives either a recoloured copy of today's floor or posterised bands.
   - What would work is a painted floor: an artist's paint-over of the three frames, or a painted ground tile and decal set in the palette laid over them. A texture model trained on painted ground is the third route, but it needs a download, which is outside this brief.
2. **Finding every figure.**
   - At 70 px, SAM 3 finds about one instance per word, so the model repaints the foes. r8 found them by value and colour plus hand-set boxes: not a pipeline.
   - An actors-only render from Godot at the same camera would give exact masks. That needs a small debug flag in the game, which was not built here.

**A design conflict, for the owner.** D3 says the characters are lighter than the ground. The den's wolves are near-black, so lifting them above a dark ground made them read as pale ghosts (r8). The question is in the next section.

## The ChatGPT image-edit route (second lead, 22 Nov): judged, did not pass

**What was made.** Options A, B and C, each over the same three den frames, nine pictures at 1920x1080. Each is one ChatGPT image edit of the game's own frame plus one cut of the owner's reference (the day panel for A, the night panel for B, both for C). No figure was pasted back and no mask was used. The model returns 1536x1024, so each frame was padded to 3:2 before upload and the result was brought back onto the game frame by a fitted affine (median error 0.8-1.9 px). The model sheared every frame 3 by about 3%, which left a wedge at its left edge (up to 48 px) with no paint under it; that wedge is mirror fill.

**The choice made on the foes.** The wolves were kept dark: near-black charcoal with a thin pale rim light and an ink outline. That is darker than the floor, so it goes against D3 as written. The question stays the owner's (question 1 below).

**The judge's verdict (the third and last round; a fresh max-effort judge, whole frames at 1:1), in its words:** "no option passes. C is close, B is second, A is last."

- **C, fail:** "It is the closest result in any round. Layout, figures, pits and walls are right. It fails on the light pools and on one fake shape at an edge."
  - The gold pools are brighter than the heroine (measured by the judge on frame 1: pool lightness 51 against her 38).
  - 5.5% of the floor is mauve-pink at the pool edges, a color the reference does not have there.
  - On frame 3 the mirror-fill wedge reads as an invented rock at the left edge.
  - The floor is quieter than the source in the shade (3.9 against 5.0) and busier where the pools are.
- **B, fail:** "The cyan pools are brighter than her and wrap the pack, and its drift is the worst of the three." It has the cleanest palette, and the judge read its cyan-rimmed figures as the best of the three.
- **A, fail:** "everything goes one orange and she is warm on warm." It has the busiest floor, and on frame 3 her shield was repainted and a pale lump was invented. The judge's reading: "fixes won't save it, because the palette works against D3."
- **Foes darker than the floor, all options:** the judge's reading is that they read in all three, best with B's cyan rim, and that "this alone would not stop the owner."

**What holds on this route, which the local route never reached (the judge's reading and mine agree):** the camera and room stay; every wolf and the heroine stay in place and shape in C and B; pits stay pits; light is painted flat on the floor and not as orbs; the palette takes.

**The judge's shortest fixes for C:** no mirror fill on frame 3 (pad the source on the left and right too); fewer, larger cut light shapes, darker than her, with no mauve at their edges; keep the glowing spot on frame 1 as the brightest point.

**My recommendation (mine, not a ruling).** C's three frames are worth the owner's look as the closest result, marked as failed, because each fault left is named and one image costs about a minute on this route. The judged rounds are spent, so the next step is the owner's: look at C directly, or allow one more round after the fixes.

**Where it is kept** (reference pictures only, never shipped, nothing built from them):
- Sheets, three rows of source beside paint at 1:1: `C:\Users\munch\Desktop\survivorsunchained_inputs\scratch_look\gpt\closest\` (each file name starts DID_NOT_PASS).
- The nine pictures: `...\scratch_look\gpt\fit\`. As downloaded: `...\gpt\raw\`.
- Provenance (prompt, date, source frame, tool, chat) and the full log: the top block of `...\scratch_look\STATE.md`; the prompts in full: `...\gpt\prompts.md`.
- The judge's scripts and output: `...\gpt\judge\`.

## Questions for the owner (yes/no)

1. May foes stay darker than the floor if they get a strong rim and an ink outline? (D3 as written says no.)
2. Is the written direction enough to pick now (A, B or C), with the paintings made after the pick?
3. May the paint-over be made by hand, or from a painted floor set, since the local route did not reach the bar?
4. (From the third judge.) May light pools on the floor be brighter than the heroine, or do they count as ground and stay darker than her?
5. (From the third judge.) Is the den's light hard-edged cut patches, as the reference paints sun on its path, and not a soft glow?
6. (From the third judge.) With its listed faults fixed, is C's direction (cool shade, warm light, inked walls) the game?
7. Do you want to look at C's three frames as the closest result even though they failed, and may one more judged round be spent after the fixes? (The cap of three is used up.)

## After the pick (not started)

- The look is frozen as numbers, measured from the picked painting with `tools/look/look_spec.py`.
  - That tool and its page, `docs/design/look_spec_ref_19nov.md`, were brought over from the art-color branch; only these two files came over.
  - The spec JSON and the region boxes did not come over, so the picked painting needs its own measurement and regions.
- Each prop is cut out of the picked painting as a clean reference image.
- The painting is kept as the placement target at the same camera.
- Meshes wait for the environment bake-off after the slice.

**The coordinator's notes, 22 Nov (after the lane closed).**
- The lane's worktree was removed at the merge. The 1:1 option sheets the two judges saw (r3, r6), the two unjudged builds (r7, r8) and each round's overview sheet are kept in `C:\Users\munch\Desktop\survivorsunchained_inputs\scratch_look\evidence\paint_sheets\`. None passed, so none is offered as a pick.
- Not tried: ChatGPT's image edit (the team's other image route). It needs the owner's Chrome with the Claude extension connected, and no browser was connected overnight. My reading, not tested: it is the next thing to try before a hand painter, since an edit model keeps a frame's layout far better than the local repaint did.
- One judged round of three is left on this item. The cap was not raised.

**The second lead's note, 22 Nov (later).** The two notes above are now out of date: ChatGPT's image edit has been tried (the section "The ChatGPT image-edit route"), and the third judged round is spent. No judged round is left on this item.

**What the next one costs on the ChatGPT route.** One image takes about a minute to generate and about three tool calls to drive, in the owner's Chrome with the extension connected; a one-thing correction in the same chat costs the same. Reusable as they are, in `C:\Users\munch\Desktop\survivorsunchained_inputs\scratch_look\gpt\`: the prompts (`prompts.md`), the padding and reference cuts (`scripts\prep_up.py`), the registration back onto the game frame (`scripts\register.py`), the gates (`scripts\gates.py`), the sheet builder (`scripts\sheets.py`) and the judge's measures (`judge\measure.py`). So a fixed C is about three images and a few minutes of checks. What it does not have is a judged round.

**What the next one costs on the local route.** The colour pre-grade, the masks-by-value step and the gates (edge sharpness, the blur-8 margin, the brightest share, the palette gamut) are reusable, and they measure any future paint-over in minutes. The figure masks would become exact and free with an actors-only render pass. The floor is the one piece that needs a painter, or a model we don't have.
