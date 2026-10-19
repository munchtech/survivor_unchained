Context budget: 150k

You are a fresh max-effort judge for Survivor Unchained's armor pipeline (armor lead 4, worktree C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\armor-1). Read-only: write nothing but your verdict (return it as your final message). Don't run builds or measuring scripts; if you need a number, ask for it in the verdict.

## The finish line (the owner's rule, verbatim from the team README)
A judge rules at the cameras the player has: the play and town camera, the close-up camera at its closest zoom, and character creation's Look camera for the face, day and night, at full size and critically. It must look perfect there. A mark that only shows enlarged is closed. The frames below are game-camera frames at 1:1 (1920x1080). Don't ask for enlargements.

## FIRST, per frame: the whole-frame gate
Before any checklist: *would this frame ship in a AAA game as it stands?* Answer as a player watching at 1:1, about the whole picture: her anatomy and pose, face and hair, lighting, camera angle, staging. A NO fails the frame, whatever the checklist says. Calibrate on the owner's three failing frames in C:\Users\munch\Desktop\survivorsunchained_inputs\owner_frames_18oct\ (a masculine throat under an upside-down camera; a collapsed hunch with a gray neck and a floating pauldron; a hard pale hairline, a detached braid tab, waxy flat skin). The owner said of frames our judges had passed: "that quality is nowhere near what we are supposed to be pushing for". She is tier 1 (full detail). Things outside our scope (the environment, other characters, the face and skin shader, which belong to other leads) still count for the gate. But name the owner of each, so the lead can route it: armor, face/skin, hair, animation, environment.

## The owner's words on this work
"smart bras and bikinis, smart all parts really - we can adorn them and make them obviously higher level and epic but making new armor shouldnt cost us hours of animation and body edits - it should just work". "the waxy skin and plastic armor certainly needs some work - moreso the armor as it will cover most skin as we get better armor". The costume direction: sex appeal leads, but it never looks bad; full cups with big cleavage are fine.

## What is shown
A new smart slot part, the `top` shell built from her own body surface (style plate), in three tiers that add only adornment:
- **plain forged** (plate_top_plain): steel cups and a gore plate, a rolled edge, rivets, and a leather back band buckled at the spine.
- **etched** (plate_top_etched): as plain, plus a blackened band with a bright vine etched as gaps.
- **gilded** (plate_top_gilded): as plain, plus gilt rivets, a raised 5 mm gold band and a sapphire at the gore.
Her other slots are filled from her calling's outfit (warden; the two `j_mix_stalker_*` frames are the etched top over the ranger's own bottom, belt and boots: the mixed look).
The metal shader is the worn-metal standard (look bible docs/art/look_bible/01_armor_metal.md, "DONE means" and "As built"), already passed by a judge on her outfits.
Her gameplay LOD (a cut model drawn when the camera is past 18 m): `lod_off_<calling>` is the full model and `lod_on_<calling>` is the gameplay model, at the same play frame.

Frames, all in C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\armor-1\godot\.shots\armor4\:
- Tiers: j_{plain,etched,gilded}_{play,close,look}.png
- Motion and fit: j_gilded_run_play, j_gilded_run_close, j_gilded_fight_play (a fight, arms working), j_gilded_side_look (90 degree turn)
- Skin edges: j_gilded_deep_close, j_gilded_fair_close (darkest and lightest tones)
- Mixed: j_mix_stalker_close, j_mix_stalker_look
- Play crops at 1:1 (she's small at the play camera): crop_*.png, each the native-pixel box around her
- LOD: lod_cmp_<calling>.png (left: full model, right: gameplay model, same frame, 1:1 crops), for warden, arcanist, stalker, reaver; plus lod_on_fight_warden.png (a fight with the gameplay model)

## Checklist (after the gate)
1. **Tiers:** at the close-up and the Look camera, plain, etched and gilded can be told apart at a glance, and each tier reads as a step up ("obviously higher level"). At the play camera they need only look good. The cups are about 6 px there, and the coordinator accepted that they can't be told apart.
2. **Metal:** worn metal, not chrome and not plastic. Nothing clips (sRGB 250+) beyond pinpoint glints. Darker than her skin in the midtones. The highlights take the scene light's hue. The gold reads as gold, not orange or yellow plastic.
3. **Form:** the rolled edge catches a line of light, the rivets read as real, the etched vine reads as an etched pattern (not a glyph or a smudge), and the gold band is raised.
4. **Fit:** no skin through the cups or the band; no floating gap; the cups sit on her breasts like fitted plate (not balloons); the side band doesn't sink or push out visibly with her arms working (run, fight); the seam to her other slots reads clean, mixed look included.
5. **Skin edges:** at the darkest and lightest tones, where skin meets the top: no halo, no dark line, no tuck hole.
6. **LOD:** in each pair, is any difference visible at 1:1 (metal speckle, shadow-edge flecks, the Reaver's fur and loincloth edges, missing pieces)? A visible difference fails that calling's LOD.

## Return (under about 900 words)
- A table, one row per frame: gate YES/NO (one line why), checklist marks, PASS/FAIL.
- For each FAIL: the cause as you read it, and a concrete fix (what to change, and where you'd look) with its owner. Restage or cut a shot that can't pass the gate. Don't close it as known.
- One line per checklist item: overall PASS/FAIL.
- Anything outside armor that fails the gate, by owner, in one list.
