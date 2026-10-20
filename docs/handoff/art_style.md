# Handoff: the signature art style (style frames)

## Status: round 2 DONE, ready to merge (art-style lead 4, 20 Oct)
- **Adopted (env lead 9, 20 Oct, G1):** the light and grade are now the default in data (`GradeSettings.Paint*`; environment.md "Now (env lead 9 ..."). The brush post-filter is dropped: its code stays behind `--brush`, off by default; don't build on it. The painted look now comes through the remakes, E4 onward.
Deliverables: `survivorsunchained_inputs\art_style\r2\` (`proposal.md`, `r2_town.png`, `r2_close.png` and `r2_night.png` as today | A | target | engine, `frames\`, `perf\`, both judge briefs). **Verdict: the engine doesn't get there with flags.** Two xhigh judges failed every frame at the whole-frame gate, and round 2 put it "about a third of the way". The light and grade pass their part: blue shadows, a pale-gold sun, ember against moon. No surface reads as painted at 1:1, and the judge says remade assets close the rest, not knobs or a stronger filter.
- **Built this stretch:** setts palette toward cream-grey, then half the per-stone spread with no cream outliers. Stones 1.6x via `--setts-paint-scale` (the default under `--setts-paint`). `paint_tex.py props`: the furniture trim painted, 41 props, plus a `--knee` for pale paint. Night sets `fordc` and `camp` (`--spots-clear`). `sheet.py four`.
- **Perf (Release, brush in/out):** GPU +0.77/+0.86 ms at 1080p and +2.25/+2.27 ms at 1440p; frame time +1.1-1.9 ms at 1080p and +1.8-3.4 ms at 1440p. Recommendation: drop the post filter.
- **Her:** the brush mask is exact. The fix round's lower night key muted her copper hair, so the close sheet uses round 1's flags. Rule: rim at most 3, fire 0.75-0.9. Also mask the grade's shadow tint and vibrance off her.
- **Next (owner's pick):** adopt the light and grade; build the painted look into the remakes (setts with relief and joint dressing, an iron preset for the metal trim, an amber lantern, the firs' bark and foliage preset with a card pass, the camp's floor dressing); judge each at 1:1 against target_town's surfaces. The ford was cut as a style frame (environment remake). Folk idles are animation's.
- Lead 4's scratch is backed up in `survivorsunchained_inputs\scratch_art_style\`.

## Start here (the direction; round 1 history below it)
The owner approved exploring a signature look before we remake the world's assets (19 October, night: "I love your ideas, lets do it. exciting !"; OWNER_NOTES 19 Oct, "A signature art style"). This stretch is step 1 only: **style frames for the owner to pick from.** Nothing in the game changes this stretch.

**The direction to explore:** painterly realism plus colourful light.
- **Forms stay realistic:** believable anatomy, architecture and proportions (slight exaggeration of shapes is fine: chunkier stone, leaning roofs, stronger silhouettes).
- **Surfaces are treated like a painting:** simplified texture detail, visible but controlled brushwork at one consistent scale, fewer micro-details, a deliberate value structure. Dishonored is the nearest example. This is a description for you, not a prompt: never put a game, studio or living artist's name into a generation prompt, and describe the qualities instead.
- **Light carries the colour:** warm ember against cold water and moon; dawn gold; lantern amber; spells pure and strong. Shadows keep colour (deep blue, violet, green), never grey-black. Vibrance, not saturation: dull midtones (mud, stone, cloth) gain the most, skin hues are protected, and brights stay rich instead of bleaching to white.
- **The owner's words on colour:** "extra vibrant colors? like the 'correct' colors just somehow more vibrant".
- **She stays realistic.** Her face, hair, skin and outfits are our biggest investment. Only her lighting may change. A paint-over that redesigns her face fails. No Arcane-style or cel stylization.
- **Why** (the reasons the owner approved): one surface treatment makes a mixed-source library (Marionette AI sculpts, the shared base, procedural ground, kits) read as one game; it is cheaper per asset and runs faster than chasing realism; it ages well; it leads into the drawn storybook cinematics.

## Round 1 steps (history: done 20 Oct)
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
