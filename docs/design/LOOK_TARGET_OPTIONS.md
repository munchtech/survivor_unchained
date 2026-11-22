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

## Questions for the owner (yes/no)

1. May foes stay darker than the floor if they get a strong rim and an ink outline? (D3 as written says no.)
2. Is the written direction enough to pick now (A, B or C), with the paintings made after the pick?
3. May the paint-over be made by hand, or from a painted floor set, since the local route did not reach the bar?

## After the pick (not started)

- The look is frozen as numbers, measured from the picked painting with `tools/look/look_spec.py`.
  - That tool and its page, `docs/design/look_spec_ref_19nov.md`, were brought over from the art-color branch; only these two files came over.
  - The spec JSON and the region boxes did not come over, so the picked painting needs its own measurement and regions.
- Each prop is cut out of the picked painting as a clean reference image.
- The painting is kept as the placement target at the same camera.
- Meshes wait for the environment bake-off after the slice.

**What the next one costs.** The colour pre-grade, the masks-by-value step and the gates (edge sharpness, the blur-8 margin, the brightest share, the palette gamut) are reusable, and they measure any future paint-over in minutes. The figure masks would become exact and free with an actors-only render pass. The floor is the one piece that needs a painter, or a model we don't have.
