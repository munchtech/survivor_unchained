# Judge: the AAA ship gate on the Prologue cinematics' restaged and relit shots (cinematics 3, round 3: k13, the confirmation), effort max

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

## Round 3: the confirmation (the round cap)
Round 2 (k12) passed 2 of 32 and gave one fix per NO; a solver applied the fixes that carry over to the new art (light rigs off-axis, grades, softer fire shadows, the globe and lantern tint and halos, mist, cut points, the cuts) and skipped fixes tuned to today's assets. There is no round 4. Each shot you see either SHIPS (the gate says YES) or is CUT now, and the next wave re-stages it on the new art. So for each shot: SHIP or CUT. For every CUT: name the shots either side as the scene will play and say whether that cut works (a jump cut, a lost line, a broken eyeline), and name the owner whose art brings the shot back (TOUCH-UP, NPC, ENV, ANIM) or STAGING. If cutting a shot would break the scene (the opening establishing shot, the hand-over into play, a shot carrying a line), say so and give the frame-around that would let it ship instead (one action, numbers).
For each shot marked "cut check", the shot is an unchanged round-2 NO; look at it once and confirm the cut, or say why the scene can't lose it.
For shots with all three stills listed, say whether the motion between them could read as a snap or a slide.
Shot notes (the intent): godot/data/cinematics/<cine>.json, each shot's "note" (grep `"id": "<shot>"` and read only that note line, only if a frame's intent is unclear).

## Your frames
C01 (files godot/.shots/k13ac01_c01_s<id>_<n>.png). The scene now plays: s1 (black, sound; passed) -> s3 -> s6 -> s7 -> s8 (passed in round 2, unchanged) -> s8a -> s8b -> s9 -> s10 -> s12 -> play.
- Changed, still _2: s7, s8a, s9. All three stills: s3, s6, s10, s12.
- Cut check (unchanged NO: her lips hang parted; no lip-close shape exists): s8b _2. It carries part of the voice's lines: check whether s8 and s9 can carry them.
- The hand-over into play (s12's crane blends into the game camera): godot/.shots/k13ac01_ho_c01_000_1.png, _010_1, _020_1, _030_1, _040_1 in order: must be smooth, no jump.

## Output
One line per shot: `<cine> <shot>: SHIP | CUT - the main reasons, most visible first - owner - for CUT: the neighbours and whether the cut works; if it can't be cut, the frame-around fix`. Then: the final list of shots to cut, any frame-around fixes that must be applied before the MR (keep these few and exact), and 2-3 lines on the set as a whole. Under 70 lines.
