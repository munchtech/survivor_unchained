Context budget: 140k

You are a fresh max-effort judge, round 3 (the last round), for Survivor Unchained's armor pipeline (worktree C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\armor-1). Read-only: return your verdict as your final message; write no files.

First read tools\scratch\armor4\judge_brief.md in that worktree: the finish line, the whole-frame gate, the owner's words, what is shown and the checklist all hold. Then read tools\scratch\armor4\verdict_r2.md (round 2, summarized).

**Important:** rounds 1 and 2 were shot with a stale C# build, so the metal shader setup was older than the passed worn-metal standard. Every frame below is on a fresh build. So judge the metal afresh, including the blue steel at the creation camp (round 1's F3), which may have been the stale build.

## Changed since round 2
- **F2, etched:** the vine is its own steel film taking the cup's own sky and curvature, outside the shader's rim-dirt band (the dirt band made it read flat cream). The `blacksteel` ground is about sRGB 74 at roughness 0.3. The vine is a smooth wave with leaves.
- **F7:** her skin is tucked 3 mm or more under the gore plate's footprint. Minimum clearance in each calling's idle: warden 3.04, stalker 2.96, arcanist 2.96, reaver 3.03 mm.
- **F5:** when a pauldron is worn, the part of the top's strap it covers isn't drawn (it ends 5 mm inside the pauldron's rim).
- New motion frames: m_run_a and m_run_b (the town run, sheathed, mid-stride), plus m_fore and m_back (the forehand and backhand swings, offered as kinder poses than the heavy swing, whose tray-flat shield is animation's).
- F1 (gilded) passed in round 2. Confirm it still holds on the fresh build.

## Frames (godot\.shots\armor4\)
- tier_strip_close.png and tier_strip_look.png: plain | etched | gilded, 1:1 crops of the top at the close and Calling cameras. Whole frames: j_{plain,etched,gilded}_{close,look}.png.
- j_mix_stalker_close.png (F7, the etched top on the ranger).
- m_swing_a, m_swing_b, m_swing_c (heavy swing; F5's strap in m_swing_c), m_run_a, m_run_b, m_fore, m_back.

## Return (under about 700 words)
1. A row per frame: whole-frame gate YES/NO on armor's own account (routed non-armor items don't count; name any NEW non-armor item with its owner), plus checklist marks.
2. F1, F2, F5, F7, and the metal (checklist 2): PASS or FAIL each. For a FAIL, give the one fix, or say "restage" or "cut" and which frame.
3. Which motion frames, if any, should be cut from the set as poor staging (they'd fail the gate for a reason armor can't fix).
4. Etched is 33.7k triangles at LOD0 against a 30k cap (the vine film). Does its look at 1:1 justify keeping it, or would a coarser vine (fewer leaf triangles) read the same?
