# Handoff: the signature art style (style frames)

## Status: round 2, step 1 DONE; step 2 started (art-style lead 2, 20 Oct); next lead picks up step 2
The brief for round 2 is main's spawn brief (the owner, 20 Oct: Krea is fine for PREVIEWS; reference frames never ship). The order: 1) a painted target, 2) the in-engine proof judged against it.
- **Step 1, the target: DONE.** Files: `survivorsunchained_inputsrt_style2\` (`target_<frame>.png`, `sheet_<frame>.png` = today | A | target, `target_alts\`). Main's full-size verdict:
  - town: a real YES, the best frame yet; the seams are fine at 1:1.
  - close: the world is a YES, but she reads pasted-in. So plan a painted touch on her LIGHT only (a softer specular, a painted rim, fire bounce), never her face shape or texture.
  - ford: v1 painted the drowned as astronauts. v2 keeps every figure's engine pixels: a SAM mask, inpainted out before painting, composited back. Main hasn't seen v2.
- **How the target is made** (`tools/scratch/art_style/krea_r2.py`; scratch in the coordinator's scratchpad `art_style2\`: src, paint, tiles, masks):
  - `prep` gives the A frame plus B's light block-in. A single img2img pass re-imagines the top-down camera (edge score 0.29).
  - `tile` (2x upscale, 12 overlapping 1536x864 tiles, each captioned by Qwen3-VL, darkbrush 0.8, d 0.40-0.42) holds the layout (0.59) and gives finer strokes. The close-up is a single pass at d 0.42, seed 3.
  - The ford source is lit brighter first (`ford_L2`: light x1.6, exposure 1.3, gamma 0.85).
  - The reference-latent (edit) mode holds the layout but wrecks the colour: dropped.
- **Step 2, in progress:**
  - **E2 brush filter:** coder `a65c85b7a01d82e91` (su-lead-high, medium, background) is building it in this worktree. Its edits are still uncommitted: `godot/src/World/Brush*.cs`, PlayerView/Game/GameFront/ZoneView.cs, frames.py. Don't touch them until it commits. Brief: `tools/scratch/art_style/brush_brief.md`. **It reports by SendMessage to the old lead's id (a03b1e5e8623b71d6): tell it to report to you instead.**
  - **E1 light:** no new code needed. `--air-tune` (Atmosphere.cs ~138: keyc, key, hemisky, hemiground, hemi, env, ember, mist, haze, fogc) does it, with `--lamp-inner`, `--ford-inner`, `--campfire-wash/-bounce` and `--ember-range`. Tune to the target (warm key, blue-violet fill, stronger pools) on the first engine shot, and keep it cheap until that shot shows it's on track (main).
  - **E3 re-textures:** brief ready, `tools/scratch/art_style/e3_retexture_brief.md`. It covers the painted setts, a reusable kit-sheet painter for the well, one stall, one folk palette; all behind flags, built with our own tools (never Krea).
  - Plus her light touch (above).
  - **Then:** frames.py shots → judge (su-lead-max, xhigh, foreground, the whole-frame gate first, against the targets) → perf ABAB in Release (runner) → a fix round (cap 2-3) → `sheet_<frame>` as today | A | target | engine, plus `proposal.md` (the remake cost per asset) → an MR of the flags and tools only. Finish with "STYLE R2 READY".
- **Left behind:** the scratch `art_style\` (r1 `solver\` and `r2\`) isn't backed up yet. The ~1,146 line-ending-only `.import` files and the `.uid` files: never commit them.

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
