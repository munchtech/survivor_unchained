# L1 the look, lead 6 (9 Nov, coordinator ad002ada): Stage C's color to VIBRANT, the 13 frames, GATE G2

Area: L1 the look (PIPELINE row P12). Worktree `C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\look-l1`, branch `look-l1`, at 46cb4d5ea. Handoff: `docs/handoff/art_style.md` top block (lead 5's), in your worktree; `docs/design/LOOK_BIBLE.md` is law. Role `su-lead-max` (taste throughout).

**Standing:** `docs/handoff/lead_brief.md` (all of it), OWNER_NOTES top blocks. **The owner, 8 Nov:** "we need to solidify our art style as visually stunning cel shading painterly with vibrant colors." That is the check the last wave failed: WEEK_WRAP row look-l1 says structure toward the targets, color not there (a mauve day cast, a brown night pool), only frame 02 would ship. Vibrant means the correct colors, more alive (OWNER 19 Oct: "the 'correct' colors just somehow more vibrant"), shadows that keep color, brights that stay rich, skin protected. The G1 target sheet the owner picked ("love it", 4 Nov, `look_l1\g1\`) is the reference for every judge.

**Steps (the handoff's "step one next week", then G2):**
1. The day key's warm cast fixed at its root in the grade (never a per-frame patch), the color chain re-run (`tools/look/color_chain.py`, `data/look/swatches.json`); the night pool's brown to the boards' night. Numbers first (`palette.py` rules 1-4, lookdev), then your own half-size look.
2. The ground check on the Hollow and the Barrow through the painted ground system.
3. The 13-frame shoot; one max judge with the whole-frame question first ("would this ship in a AAA game as it stands, and is it the G1 sheet's game?"), on all 13 as one game; the judge's notes go to the blocks (the shading model, the material library, the rigs, the chain), never to a frame.
4. Stage D as the handoff defines it; then **GATE G2 READY look-l1@<sha>** in the handoff top and to main (SendMessage "main"), with the 13 frames as A (today) | B (G2) pairs at half size (`python tools/half.py`) in `survivorsunchained_inputs\look_l1\g2\` for the owner.

**The ARPG pivot (`docs/design/ARPG_DIRECTION.md`):** the look does not change with the loop; shoot the 13 frames as they are. Two things for you: (a) the skills lead (worktree skills-p7) builds a Heroic Leap and a Cyclone/Bladestorm now and needs the FX band language's rules for spells (colors by school, the ink under effects, what a cast, a travel and a hit look like in cel): write them as a short page `docs/design/FX_LANGUAGE.md` from Stage B's FX band work early in your run (within your first few turns, ~1 hour) and tell main; (b) "vibrant" applies to spells most of all: a Flare or a skill is the most saturated thing in the frame.

Report shape: "P12: the app can now X; cost Y." Budget from the wrap: ~1.0M + $12-17 to G2. GPU: take turns through `tools/turn.py`; the P1 lead shoots too. Hand off at ~300k.
