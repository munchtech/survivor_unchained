# Handoff: the signature art style (style frames)

## Status: round 1 DONE, 20 October (art-style lead 1); waiting on main
- **Delivered:** `survivorsunchained_inputs\art_style\r1\`: today/A/B/C for town, ford and close; three sheets; `overview.png`; `proposal.md`. Frames: town_00 (spot 3,3), ford_03 (0,-38), close_03 (-9.5,92.5,1,0). They come from `tools/scratch/art_style/frames.py`: `--no-labels` hides the world text; "g" runs dump the live table.
- **The gate: NO on all nine.**
  - **A** is proven in engine: `--grade-try` (e19baf80) matches its numpy twin `grade_try.py` on all but 1.5% of pixels, and the default grade is untouched. It's a free colour gain, but it can't fix the town's assets.
  - **B and C fail to preview a painted surface.** Z-Image paints in a flat comic style: above about 45% repaint it invents content, and below that it adds no brushwork. Their gain is light, which the engine can do.
  - The solver's method is in `paintprep_r1.py` (light block-in, a stroke filter that follows edges) and `paint.py` (fixed for this ComfyUI's MoGe).
- **Merge candidate:** only `--grade-try` + `--no-labels` (godot/src/World/Atmosphere.cs, godot/src/Shots.cs; both shots-only).
- **Open (main's call):** the next step. The lead recommends A's grade plus B's lighting design, then the in-engine proof (masked stroke post-filter plus 3-4 re-textured assets). Alternatives: a painter's paint-over of A_town/A_ford, or a Krea 2 + darkbrush try (needs main's call under the replace-Krea policy).
- **Left behind:**
  - The scratch in the coordinator's scratchpad `art_style\` (including `solver\`) is not yet backed up.
  - The worktree shows about 1,146 `.import` files as modified (line endings only; their content diff is empty) and 32 untracked `.uid` files. These are by-products of the first import: never commit them.

## Start here
The owner approved exploring a signature look before we remake the world's assets (19 October, night: "I love your ideas, lets do it. exciting !"; OWNER_NOTES 19 Oct, "A signature art style"). This stretch is step 1 only: **style frames for the owner to pick from.** Nothing in the game changes this stretch.

**The direction to explore:** painterly realism plus colourful light.
- **Forms stay realistic:** believable anatomy, architecture and proportions (slight exaggeration of shapes is fine: chunkier stone, leaning roofs, stronger silhouettes).
- **Surfaces are treated like a painting:** simplified texture detail, visible but controlled brushwork at one consistent scale, fewer micro-details, a deliberate value structure. Dishonored is the nearest example. This is a description for you, not a prompt: never put a game, studio or living artist's name into a generation prompt, and describe the qualities instead.
- **Light carries the colour:** warm ember against cold water and moon; dawn gold; lantern amber; spells pure and strong. Shadows keep colour (deep blue, violet, green), never grey-black. Vibrance, not saturation: dull midtones (mud, stone, cloth) gain the most, skin hues are protected, and brights stay rich instead of bleaching to white.
- **The owner's words on colour:** "extra vibrant colors? like the 'correct' colors just somehow more vibrant".
- **She stays realistic.** Her face, hair, skin and outfits are our biggest investment. Only her lighting may change. A paint-over that redesigns her face fails. No Arcane-style or cel stylization.
- **Why** (the reasons the owner approved): one surface treatment makes a mixed-source library (Marionette AI sculpts, the shared base, procedural ground, kits) read as one game; it is cheaper per asset and runs faster than chasing realism; it ages well; it leads into the drawn storybook cinematics.

## Steps (estimate 1-2 h of work, plus turns)
1. **Frames.** From the latest integration (E3's ground merged), capture three frames at 1920x1080 (one Godot turn for all): the town by day at the play camera; the Low Ford at night at the play camera; the camp close-up on her face at its closest zoom. Shoot each one in your worktree, graded as built AND with `--grade off` (the raw frame for the paint-overs). Use the cinematics' and env shot tools (grep `--tonemap` / `--grade` in `godot/src/Shots.cs`; env lead 7's batches are in `survivorsunchained_inputs\scratch_env7\ground_d\`).
2. **Three directions per frame:**
   - **A, today's look with the vibrant grade:** done IN ENGINE, not with AI. There is no command-line override for the grade yet, so add a shots-only flag in your worktree (say `--grade-try mute=0,vib=1.2,shadow=#2a3550,hi=rich`) that adjusts the live grade in `godot/src/World/Atmosphere.cs` (`Mute`, vibrance with skin hues protected, a coloured shadow tint, a richer highlight rolloff) and leaves the default untouched. Commit it on your branch: it becomes the tool for the in-engine proof later. A medium `su-lead-high` coder or `su-worker` can write it while you set up the paint-overs.
   - **B, painterly realism:** a paint-over on the local ComfyUI (img2img with depth/lineart control from the frame, so composition, her pose and the layout hold). `tools/comfy/` has the client and graphs. GPU turn: `tools/turn.py take gpu "style: paint-overs"`, given back between batches. Local models only: no API spend.
   - **C, bolder painterly:** the same, pushed further (stronger brushwork, more graphic shapes and light) to show the range.
   For B and C on the close-up, mask her face out of the repaint or restore it, and only relight it. Generate several seeds, keep the best one per frame.
3. **Contact sheet:** one sheet per frame (A | B | C, with today's graded frame as a small inset), plus a 3x3 overview. Save to `C:\Users\munch\Desktop\survivorsunchained_inputs\art_style\r1\`.
4. **One-page proposal per direction** (`proposal.md` next to the sheets): palette and shadow colour; texture treatment (brush scale, texel density, detail level); shape language; the one shader touch that would carry it in engine (a painted rim, a stylized specular, a light ramp); what it costs to build per asset (how a remake changes for a rock, a fir, a wall, an NPC outfit); perf; what changes on her (light only); risks.
5. **Self-check before main sees it:** the whole-frame gate applies. Would each frame make a player stop and say "that's a beautiful game"? If a direction can't get there, say so plainly rather than polishing it.
6. **Report to main:** "STYLE FRAMES READY" with the folder and a three-line pitch per direction. Main looks at full size and sends the owner the good ones. Then stop. The in-engine proof (step 2 of the plan: 3-4 assets re-textured plus the grade, judged at the play camera) is a later stretch, after the owner picks.

## Rules
- Context budget: 200k. Pictures are the biggest cost: half-size copies and contact sheets (`python tools/half.py`) for your own looks.
- Your scratch goes in a subfolder `art_style` of the coordinator's scratchpad; the deliverables go to `survivorsunchained_inputs\art_style\`.
- Worktree: main makes `.claude/worktrees/art-style` (branch `art-style`) from the latest integration, with its own `godot/assets` junction to ITS OWN `public/assets`. Never link to the main checkout. Commit as you go. The default grade never changes this stretch.
- Never kill processes by name; free ComfyUI with `POST /free`, never by killing it.
