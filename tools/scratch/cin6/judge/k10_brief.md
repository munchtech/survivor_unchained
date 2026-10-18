# Judge: the AAA ship gate on the Prologue cinematics' restaged and relit shots (cinematics 3, k10), effort max

Context budget: 200k

You are a fresh judge for Survivor Unchained, a dark-fantasy ARPG (Godot). You work for the cinematics 3 lead (agent ac7e54435a82fff12): your final message is the verdict and goes back to that lead. Edit nothing; write no files. Worktree: C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a59432fe3bfc6eb92 (frames in godot/.shots/, 1920x1080). Open each image once, at its own size: no crops, no enlargements. Keep the verdict under 90 lines.

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

## What changed in this pass (k10), so you know what to check
- A darker night of each scene's own with pools of light from real sources (fire, lamps, moon), low mist on the ground and the river (C01, C02). Check: does the darkness hide the low-poly world well, does mist read as mist (not blocky, not a dirty lens), are pools of light motivated.
- Side and three-quarter keys from the scene's real source on close-ups (C01 s8, s8b, s10: fire; C02 s4, s8: the lamp/ember; C03 s3b: moon; C04 A sa5-sa7: low dawn sun from her right). Check: the far side of the face falls into shadow, the background sits darker than her face, catchlights live.
- The owner's three shots restaged: C01 s3 (her face on its side on the frozen ground, eyes open at 2.0; o1), C01 s6 (she comes up onto her heels and looks down at her hands; o2), C01 s10 (cut on the lift, no stand or spin; o3) and C01 s11 (she takes the sword from the log on the clip's own turn). For s10 and s11, look at all three stills in order and say whether the motion between them could read as a snap or slide.
- Known misses already: C01 s3 still too orange and its throat may read stretched; C02 s8 face reads pale-white and there's a bright disc at the left edge. Judge them anyway and give the concrete restaging (camera position/angle, lens, which light where and how strong, or a different pose), since a solver acts on your fixes next.
Shot notes (the intent): godot/data/cinematics/<cine>.json, each shot's "note" (grep `"id": "<shot>"` and read only that note line, only if a frame's intent is unclear).

## Your frames
{SET}

## Output
One line per shot: `<cine> <shot>: YES | NO | NO (touch-up only) - the main reasons, most visible first - owner: STAGING | TOUCH-UP | ENV | NPC | ANIM - fix: <concrete change; for STAGING give numbers or directions a solver can act on; or CUT and why the scene reads without it>`.
Then: the STAGING fixes as a numbered list in priority order; the shots you'd CUT; the non-staging items by owner (one line each with frame ids); and whether the darker grade + mist pass worked overall (2-3 lines).
