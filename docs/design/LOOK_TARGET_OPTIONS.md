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

**Afternoon of 22 Nov:** the owner picked C ("C: cool shade, warm light (Recommended)") and allowed one more judged round on its fixed frames. A third lead started round 4 and was stopped by ChatGPT's image limit after one frame. That frame is not judged and the round is not spent. See "Round 4 on option C" below.

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

## Round 4 on option C (third lead, 22 Nov): stopped at ChatGPT's image limit after one frame; not judged

**The owner's answers (22 Nov 2026, word for word).**
- Look direction: "C: cool shade, warm light (Recommended)"
- How the next paint-over is made and judged: "Fix it, one more judged round (Recommended)". This allows a fourth judged round on this item: one round, no more.
- How foes read on option C: "Dark, pale rim, ink line (Recommended)". The option's text: wolves stay near-black charcoal with a thin pale rim light and an ink outline; she and the danger marks are the light, warm things; the rule gets rewritten to say so. The ruling is also recorded under D3 in `docs/team/GAME_PLAN.md`.

**What the owner was not asked.** Whether floor light pools may be brighter than the heroine, and hard-edged cut light against a soft glow (questions 4 and 5 below). Round 4 works to the third judge's fix: pools darker than her, with cut edges. That is the judge's fix, not the owner's ruling.

**What happened.** One picture was made, frame 1, and then ChatGPT refused the next request. The page said: "You're out of image creations for now. Try again at 6:42 PM." It offered an upgrade, which was not touched. Nothing was retried and no other route was used. Frames 2 and 3 were not made. **The judged round was not spent**, since only one of the three frames exists. It is still the one round the owner allowed.

**Frame 1 (`C4_f1_v1`), not judged.** Measured with the third judge's own script, against round 3's frame 1:

| Fault the judge named | Round 3 | Round 4 | Target | Met |
|---|---|---|---|---|
| Light pools brighter than her (floor lightness p95 against her lightness) | 51 against 38 | 40.7 against 41.1 | below hers | barely |
| Mauve-pink floor at the pool edges | 5.5% | 0.8% | near 0% | yes |
| Floor detail at wolf scale, the 10-30 px band (source 5.7) | 7.2 | 6.3 | at or below 5.7 | no |
| The glowing spot at (1025, 925) | shrunk to a dot | a clear burst, lightness 95, the brightest thing on the floor | the brightest point | yes (my reading) |
| Paint missing at an edge after the fit | does not apply to frame 1 | 0.00% | 0% | yes |

- Also measured: layout drift median 1.4 px, with 4% of matched patches past 6 px; no color outside the reference (0.0% past the judge's limit); foes at lightness 9 against a floor at 16.
- The fine grain of the floor is above the source (9.5 against 7.3 by my own gate; 6.8 against 6.1 in the shade).
- My reading at 1:1, not a verdict: two large cut pools in dusky ochre with clean edges, the pack and the heroine in place and shape, wolves near-black with a thin pale rim and an ink line, the pit still a pit.
- What is left on frame 1: the pool sits only just below her, and the 10-30 px band is above the source. One correction was written for both (pools darker and duller, same shapes). It was sent and not generated.
- Not checked: frames 2 and 3, since they do not exist. So nothing here says whether frame 3's left edge or frame 2's top-edge roots are fixed. The padding that removes the edge fill is proven on frame 1 only.

**Where it is kept** (reference pictures only, never shipped, nothing built from them):
- The one-row sheet, source beside paint at 1:1: `C:\Users\munch\Desktop\survivorsunchained_inputs\scratch_look\gpt\sheets4\look_option_C_r4_C4_f1_v1_NOT_JUDGED.png`.
- The picture: `...\scratch_look\gpt\fit4\C4_f1_v1.png`. As downloaded: `...\gpt\raw4\`. Uploads: `...\gpt\up4\`.
- Nothing was added to `...\gpt\options\` or `...\gpt\closest\`, because there is no verdict.
- Provenance, the log and how to resume: the top block of `...\scratch_look\STATE.md`. The prompt "C v3" and its correction: `...\gpt\prompts.md`. Round 4's scripts: `...\gpt\scripts4\`.

**What the rest of round 4 costs.** About five more images in the same chat once the limit resets: frame 1's correction, frames 2 and 3, and one correction each if needed. Then a few minutes of measures, the sheet, and the one judged round. Every script is written and has run on frame 1. The limit is the cost that is new. Known: the second lead made ten pictures this morning, this round made one, and the next request was refused. Not known: how many pictures the allowance holds, or what else used it. My reading, not checked: a full option set should start on a fresh allowance.

## Round 5 on option C (fourth lead, 22 Nov): stopped at ChatGPT's image limit before any picture; not judged

**The owner's words (22 Nov 2026, word for word).**
- Look direction: "C: cool shade, warm light (Recommended)". Foes: "Dark, pale rim, ink line (Recommended)".
- On round 4's first frame (`C4_f1_v1`), when shown: "that frame you just showed me looks great!!!"
- Later the same day: "reviewing c again for the painted overlay, it still wasn't perfect.  you may continue work on that till you pass it.  a little more detail perhaps in the floor? not sure, some things appear to be floating - ANYWAY the images should work again it reset usage"

**How those words are read here (the coordinator's reading, not the owner's words).**
- "till you pass it" lifts the old limit of one judged round on this item.
- "some things appear to be floating" is a fault to fix.
- "a little more detail perhaps in the floor? not sure" is a lean, not a ruling. It gets its own version of frame 1, shown beside one without it.
- Still not ruled by the owner: whether floor light pools may be brighter than her, and hard-edged cut light against a soft glow (questions 4 and 5 below).

**What happened.** No picture was made. The first request of the round was refused about six minutes in. The page said: "You're out of image creations for now. Try again at 6:42 PM." It offered "Upgrade to Pro", which was not touched. The model's reply: "You've hit the Plus plan limit for image generations requests. You can create more images when the limit resets in 1 hour." So the allowance had not reset at 5:22 PM (measured: the page's own words). Nothing was retried and no other route was used. **No judged round was spent and no judge was spawned.** There is no round-5 sheet.

**What floats in `C4_f1_v1` (the "before"), looked at 1:1.** My reading, by kind:

| Thing on the floor | Shadow where it meets the floor | Floats |
|---|---|---|
| Bones: ribs, the jawbone, bone bits (about 12) | none | yes |
| Feather tufts (about 7) | none | yes |
| Orange leaf piles (about 14) | none; they read as stickers | yes |
| Stone stakes (about 12) | none on the dark floor; a thin dark side on the lit patch | yes |
| The antler skull by the pit | a few ink marks, no shadow shape | yes |
| Wolves: the ring of about 12 and the three at the bottom | none under body or paws; clearest on the lit patch | yes |
| The woman | none at her feet (she is small from this camera) | yes, least visible |
| The fallen log on the left | none under it | yes |
| The small pale carcass, and the pale lump at the right wall | none | yes |
| Sticks and twigs | thin and dark, they read flat on the ground | no |
| The pit, the root walls, the mushrooms | inked into the ground; the pit is darker inside | no |

**The same fault, measured.** A new check (`ground5.py`) counts each thing in the game frame that is much darker or lighter than the floor. A thing counts as grounded when the floor just off its lower-right side is clearly darker than the floor a little further out.

| Frame | The game frame itself | Round 3's paint | Round 4's paint |
|---|---|---|---|
| 1 | 77 of 140 grounded (55%) | 58 of 140 (41%) | 50 of 140 (36%) |
| 2 | 61 of 104 (59%) | 46 of 104 (44%) | not made |
| 3 | 41 of 115 (36%) | 33 of 115 (29%) | not made |

- On frame 1 the game grounds 62 of its 96 dark things. Round 4's paint grounds 28 of them.
- My reading: the game draws a soft dark blob under each wolf, and the paint-over drops it. That fits "some things appear to be floating".
- The check is crude: small dark specks by the walls count as things. It is a gate beside the 1:1 list, not in place of it.
- Round 5's own gate, mine and not a judge's: each frame at or above the game frame's share, and every row of the list above answered "no".

**What is ready and not yet sent** (in full in `...\scratch_look\gpt\prompts.md` under "Round 5"):
- **Frame 1:** one correction to `C4_f1_v1` in the same chat, so the picture the owner reacted to is kept. It asks for a short dark contact shadow under every thing named in the list above, the light patches slightly darker, and her slightly lighter. This is the request that was refused.
- **Frames 2 and 3:** round 4's recipe with the same contact-shadow block. Frame 2 also names the top-edge roots and the boulder as fixed in place. Frame 3 is uploaded with the four-side pad, and the fit script refuses any fill.
- **Frame 1 with more floor detail:** a one-thing edit of the new frame 1, so the pair differs in the floor only.

**Floor detail against the third judge's gate (my reading, not checked on a picture).** The judge wanted the floor no busier than the game frame at wolf scale (the 10-30 px band). In round 4 the shaded floor is quieter than the game frame at that scale (4.1 against 4.9), and the lit patches push the whole-floor number over (6.3 against 5.7). So there is room for more detail in the shade before that gate is crossed. If the detailed version crosses it, the page will say so and keep both versions: the owner's lean is why the version exists.

**Not checked.** Whether any of the four prompts works: none produced a picture. Whether short contact shadows show on a near-black wolf over a dark floor. How many pictures the allowance holds after the reset.

**Where it is kept.** Nothing new goes to the owner from this round: no picture exists. The 1:1 crops behind the list: `C:\Users\munch\Desktop\survivorsunchained_inputs\scratch_look\gpt\peek5\r4f1_*.png`. The per-thing lists: `...\gpt\peek5\ground_*.txt`. Scripts: `...\gpt\scripts5\`. State and how to resume: the top block of `...\scratch_look\STATE.md`.

**What the rest costs.** Four pictures make the set (frame 1, 2, 3, and frame 1 with floor detail), about 90 seconds each, plus one correction each if a named fault is left. Then one command per measure, the sheet, and a judged round. The prompts and every script are written; the grounding check has run on rounds 3 and 4. Unknown: the size of the allowance. Known: ten pictures this morning, one at 2 PM, then refusals at 2:08 PM and 5:22 PM.

## Questions for the owner (yes/no)

1. **Answered 22 Nov: "Dark, pale rim, ink line (Recommended)".** May foes stay darker than the floor if they get a strong rim and an ink outline? (D3 as written says no.)
2. Is the written direction enough to pick now (A, B or C), with the paintings made after the pick?
3. May the paint-over be made by hand, or from a painted floor set, since the local route did not reach the bar?
4. (From the third judge.) May light pools on the floor be brighter than the heroine, or do they count as ground and stay darker than her?
5. (From the third judge.) Is the den's light hard-edged cut patches, as the reference paints sun on its path, and not a soft glow?
6. **Answered 22 Nov: "C: cool shade, warm light (Recommended)".** (From the third judge.) With its listed faults fixed, is C's direction (cool shade, warm light, inked walls) the game?
7. **Answered 22 Nov: "Fix it, one more judged round (Recommended)".** Do you want to look at C's three frames as the closest result even though they failed, and may one more judged round be spent after the fixes? (The cap of three is used up.) That round is not spent yet: see "Round 4 on option C" above.

Questions 4 and 5 are still open. Questions 2 and 3 were not put to the owner on 22 Nov.

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

**The third lead's note, 22 Nov (afternoon).** The owner picked C and allowed one more judged round ("Fix it, one more judged round (Recommended)"). That round is not spent: round 4 stopped at ChatGPT's image limit after one frame (the section "Round 4 on option C").

**What the next one costs on the ChatGPT route.** One image takes about a minute to generate and about three tool calls to drive, in the owner's Chrome with the extension connected; a one-thing correction in the same chat costs the same. Reusable as they are, in `C:\Users\munch\Desktop\survivorsunchained_inputs\scratch_look\gpt\`: the prompts (`prompts.md`), the padding and reference cuts (`scripts\prep_up.py`), the registration back onto the game frame (`scripts\register.py`), the gates (`scripts\gates.py`), the sheet builder (`scripts\sheets.py`) and the judge's measures (`judge\measure.py`). So a fixed C is about three images and a few minutes of checks. What it does not have is a judged round.

**What the next one costs on the local route.** The colour pre-grade, the masks-by-value step and the gates (edge sharpness, the blur-8 margin, the brightest share, the palette gamut) are reusable, and they measure any future paint-over in minutes. The figure masks would become exact and free with an actors-only render pass. The floor is the one piece that needs a painter, or a model we don't have.
