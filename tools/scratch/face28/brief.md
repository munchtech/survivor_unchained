# Judge brief: the heroine's HAIR at the game's cameras (triage), plus a face check at the cinematic close-ups

You are a judge for Survivor Unchained (a dark-fantasy action RPG, an adult heroine). Read-only: open each sheet below ONCE with the Read tool, rule, and write your verdict. Do not write scripts, crop or enlarge. Be exact and short.

## The finish line (the owner's rules)
- "A judge rules at the cameras the player has: the play and town camera, the close-up camera at its closest zoom, and character creation's Look camera for the face, day and night, at full size and critically. It must look perfect there."
- The owner, 16 October: "accept perfect for what the player can see, not at the big zoom." Marks that only show enlarged are closed.
- The owner's bar: AAA, "we are striving for perfection". Hair should read as real, soft, well-groomed hair, moving naturally.

## The owner's words on the hair (17 October, verbatim). This is why you are judging
- "current note for faces, hair physics are a mess, and hair styles even on creation screen clip through and stuff ... but like hair dosn't look good"
- "check stuff like in cinematics walking up to warden you see hair from behind, and in game. actually spin around in character creation etc"

## Sheets (folder `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\59f6a467-b8ce-446c-8f35-44c1d92b7b9a\scratchpad\f28\j\`)
All tiles are crops of native 1920x1080 game frames at 1:1 (no scaling), EXCEPT the `h_look_*` sheets, shown at 0.8x (so a mark there is at least as visible in the game). Each tile is labelled.
Styles: long (loose, to mid-back), ponytail, braid (these three have physics chains), bob, pixie ("cropped").

**HAIR**
1. `h_look_<style>_turns.png` (x5): character creation's Look, Hair part, the figure turned 0-315 degrees in 45-degree steps and at rest (the player spins her with a key).
2. `h_look_<style>_spin.png` (x5): the same, while spinning at 90 degrees/s, every 45 degrees (physics while turning).
3. `h_cu_<style>_across.png` (x5): the town close-up camera at its closest zoom, day, her running across the screen and turning back (Reaver outfit, no hat).
4. `h_cu_<style>_away.png` (long, ponytail, braid): the same camera with her running away from it. At this zoom the camera frames her low back, so little or no hair may show. Say whether any hair shows and how it reads. The framing itself is a camera matter, not hair.
5. `h_cu_<style>_night.png` (long, ponytail, braid): close-up, night, running and turning.
6. `h_misc_hat.png`: the Arcanist with her witch hat (hair under a hat), plus the close-up at zoom 0.5 running away. The camera sits inside her body there, a known camera bug. Ignore it except for the hair.
7. `h_misc_far.png`: the play camera (top-down, far), by day, by night and in a fight. Note whether hair reads at all.
8. `h_cine_back_1.png`, `h_cine_back_2.png`: cinematic shots of her from behind or three-quarter behind at their real cameras. c02 s7 and c03 s2/s5 are the walk up to the Warden the owner names; c01 s7 is the back of her head.
9. `h_reaver_sprint.png`: another judge's frame (the Reaver sprinting, close-up). It saw "the loose hair over her swung arm forms a flat sheet with a hard top edge". Confirm or reject.

**FACE (the cinematic close-ups are the closest cameras in the game; first judgement there)**
10. `cf_<face>_c04a_A5.png`, `cf_own_c04a_A5b_A7.png`, `cf_own_c01_s8.png`, `cf_<face>_c02_s4_s8.png`: her face in the cinematics' close-ups at their real expression cues (mouth open 0.25 at most, smile 0.1, frown 0.2, brows, squint). Faces: own (fair, default), saffron (warm), sunborn (brown). c02 s8 is a 135 mm lens at under 1 m by moonlight.
11. `lk_rest_day.png`: the Look's face camera at rest, three faces (the Look has one lighting).
Rule on what a player would notice in these frames: mouth interior, lips, teeth, skin, eyes, lashes and brows, the hairline at the face, and any hair crossing the face. Also say whether her hair colour reads consistently across the cinematics, since in one c02 frame it looked blonde.

## What to return (verdict.md, under about 1,200 words)
A. **Hair fixed list, worst first.** One line per item:
   - the style or styles, the camera and tile, and what's wrong;
   - its kind: CLIP (hair through body, outfit or itself), MOTION (stiff, jitter, explodes, sheets, wrong swing), REST LOOK (shape, cards, edges, colour, scalp showing, a "plastic" or "helmet" read), or OTHER;
   - severity: obvious, noticeable, or faint but there;
   - your best guess at the cause (card geometry, the physics chain or collision, the shader's alpha or edges, lighting).
   Group items that share a cause.
B. **Per style, one line:** does it meet the owner's bar at these cameras (yes, close, or no)? Name its single biggest problem.
C. **Face at the cinematic close-ups:** PASS, or each visible mark with its tile and severity.
D. **Anything else plainly visible at 1:1** that would embarrass her in these frames, one line each.
E. **Measurements the next round needs** (if any), one line each.
