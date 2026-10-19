# Judge: the AAA ship gate on the Prologue cinematics' restaged and relit shots (cinematics 3, round 2: k12), effort xhigh

Context budget: 200k

You are a fresh judge for Survivor Unchained, a dark-fantasy ARPG (Godot). You work for the cinematics 3 lead (agent a688d6f8e4fca8912): your final message is the verdict and goes back to that lead. Edit nothing; write no files. Worktree: C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a59432fe3bfc6eb92 (frames in godot/.shots/, 1920x1080). Open each image once, at its own size: no crops, no enlargements. Keep the verdict under 90 lines.

## The finish line and the gate
A judge rules at the cameras the player has, at 1:1, critically: it must look perfect there. Marks seen only enlarged are closed, not logged.
For each frame, first: **"would this frame ship in a AAA game as it stands?"**, as a player watching at 1:1, about the whole picture: her anatomy and pose, face and hair, lighting, camera angle, staging. The owner, on frames our judges had passed: "that quality is nowhere near what we are supposed to be pushing for." Calibrate first on the owner's three failing frames (all NO): godot/.shots/o1_lying_neck_adams_apple.webp (her lying, camera over a stretched masculine throat, face upside down), o2_hunched_at_log.webp (head collapsed onto her chest, gray unlit back of the neck, a floating pauldron), o3_spin_profile.webp (a jarring snap spin at the log; waxy flat skin, mouth hanging open).

## Detail tiers (the owner, 18 October): judge each thing by its tier
- Tier 1, full detail: she, her spells, her animation, bosses.
- Tier 2, good on a budget: the open world (terrain, trees, water, castle) and story NPCs (the drowned, the warden, Grimtunnel). They pass if they look good IN THE SHOT; they don't have to match her. Darkness, mist, silhouette and backlight are legitimate ways to make them look good.
- Tier 3, cheap: fodder mobs.

## Who owns what (name the owner on every NO)
- **STAGING (this lead; must reach YES or be restaged or cut, never closed as known):** camera, lens, framing, blocking, her pose choice and head cues, cut timing, the shot's own lights, grade, exposure and mist.
- **TOUCH-UP lead (not this lead's fail; name it):** her skin material (waxy, face-vs-neck tone in the material), her armor metal, her throat shape, her hairline, the braid tab, the Reaver cord.
- **ENV / NPC art / ANIM:** say so with the fix they need, or CUT if the shot can't be made to look good in-shot by staging and the scene reads without it.
If a frame fails only on touch-up items, mark it `NO (touch-up only)`.

## This is the last round
Round 1 (k10) passed 1 of 33. Two solver rounds (k11, k12) restaged since. There is no further polishing round: every NO you give will be fixed by ONE concrete action from you (a reframe, a light change, a cut-in time) or CUT. So for each NO give the single most effective fix, and say CUT when the scene reads without the shot (name the shots either side and whether the cut between them works). A frame that fails only on touch-up, env, NPC or clip items still doesn't ship as it is: say how to frame around the problem (darker, tighter, wider, backlit, silhouette), or CUT.

## What changed since round 1, so you know what to check
- A darker night of each scene's own with pools of light from real sources (fire, lamps, moon), and low mist (C01, C02). The C02 river's light is down; the ford's post globes are dimmed in cinematics; C02 s8's warden lamp no longer flares at her temple.
- Side and three-quarter keys on the close-ups (look bible: never a flat frontal key; fill at 1/4-1/8; warm bounce; under the moon skin may be cool but shadow edges stay warm, never grey or blue). C01 s8, s8b, s10 carry a per-shot saturation grade so the 2700 K fire doesn't flood her face orange; check the fire still reads warm and the frame isn't washed out.
- C01: s0 and s5 cut. s2/s3 now on her back (death_back's held pose), the head turned to the coals, face on its side for s3 (eyes open at 2.0; the owner's o1). s6 opens on her heels (o2). s10: static three-quarter, head snaps screen-left, cut on the rise (o3). s11: she takes the sword from the log on the clip's turn, seen from behind, coming round to screen-left. s8a: the ford's three lamps as small blue lights, the far gold lamp high. s12 opens at s11's level, thin mist.
- C02: s3 cut. s1/s11 reframed with thick mist; s2 backed off; s4/s8 keys toward pale steel; s10's rows lit. C03 s3b keyed from his lamp with a moon rim. C04 A: sa6 cut; sa5 is now a medium close-up from her left-front so sa5 to sa7 reads as a cut-in; sa7 eyes off the lens; sa8 trucked right.
- The solver's own calls, to check rather than trust: C01 s3 close but NO (half-moon light doesn't read, irises near black and staring into the lens, chest skin in the left third); C01 s2 borderline (a knee up, midriff to the lens); C02 s4 and s8 porcelain-cool faces; C02 s1 the gibbet at frame centre (a prop we can't move in this round).
For s3, s6, s10, s11 and s12 (C01), C02 s5 and s12, and C04 A sa7, look at all three stills in order and say whether the motion could read as a snap or a slide.
Shot notes (the intent): godot/data/cinematics/<cine>.json, each shot's "note" (grep `"id": "<shot>"` and read only that note line, only if a frame's intent is unclear).

## Your frames
- C02: godot/.shots/k12bc02_c02_s<id>_<n>.png, still _2 of each shot (all three for s5 and s12), shots in order: s1, s2, s4, s5, s6, s7, s8, s9, s10, s11, s12.
- C03 s3b: godot/.shots/k11bc03_c03_s3b_1.png, _2, _3.
- C04 A: godot/.shots/k11bc04a_c04a_sa<id>_<n>.png, still _2 of each (all three for sa7; use whatever stills exist), shots in order: sa1, sa2, sa3, sa4, sa5, sa7, sa8.

## Output
One line per shot: `<cine> <shot>: YES | NO | NO (touch-up only) - the main reasons, most visible first - owner: STAGING | TOUCH-UP | ENV | NPC | ANIM - fix: <concrete change; for STAGING give numbers or directions a solver can act on; or CUT and why the scene reads without it>`.
Then: the one-action fixes for every NO as a numbered list in priority order; the shots you'd CUT; the non-staging items by owner (one line each with frame ids); and whether the darker grade + mist pass worked overall (2-3 lines).
