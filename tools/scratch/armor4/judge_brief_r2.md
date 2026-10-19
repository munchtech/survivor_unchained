Context budget: 120k

You are a fresh max-effort judge, round 2, for Survivor Unchained's armor pipeline (worktree C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\armor-1). Read-only: return your verdict as your final message; write no files.

First read C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\armor-1\tools\scratch\armor4\judge_brief.md: the finish line, the whole-frame gate, the owner's words and the checklist all hold. Read round 1's verdict summary there too: tools\scratch\armor4\verdict_r1.md.

## What changed since round 1 (rule on these only)
- **F1, gilded:** the cups' whole rolled rim and the gore plate are gilded. The band is a 12 mm half-round bead (lit line over a shadow line). The sapphire is 13.8 mm in a 16.6 mm gold bezel.
- **F2, etched:** the band is now `blacksteel` (metal, dark, roughness 0.45, some sky sheen), with leaves along the vine.
- **F7, the mixed look:** the gore plate is rigid (one blend of bones at its center: 0.000 mm bend in every test pose but a twist, 0.5 mm).
- **F5, fit in motion:** three new close-camera frames of the gilded top in the warden's heavy swing (held at 0.35 s and 0.5 s, three-quarter views): m_swing_a/b/c. The play-camera run and fight frames are cut from this set. Their failures were environment (pond, canopy) and are routed.

## Closed or routed: don't rule on these again
- F3, the blue steel at the creation camp (the Calling tab), and F4, the warden's sword mirroring the dark sky, go to the metal standard and lighting owners. For the Calling frames, rule only on whether the three tiers can be told apart.
- F6: by the numbers, deep vs fair have the same exposure (cobble mean 106.8 in both) and the same clipped share on the cups (0.67% vs 0.68%). The deep tone's brighter-looking steel is contrast with her skin only.
- Every non-armor gate item from round 1 (skin, hair, environment, the Calling idle) is routed to its owner. Name a new one only if it is new.

## Frames (godot\.shots\armor4\)
- tier_strip_close.png: plain | etched | gilded at the close camera, a 1:1 crop of the top. The whole frames are j_plain_close, j_etched_close, j_gilded_close.
- tier_strip_look.png: the same at the Calling camera (1:1 crop). The whole frames are j_*_look.
- j_mix_stalker_close.png: the etched top over the ranger's own pieces (F7).
- m_swing_a.png, m_swing_b.png, m_swing_c.png (F5).

## Return (under about 600 words)
For each of F1, F2, F5 and F7: PASS or FAIL, with the frame and what you see. For a FAIL, give one concrete fix. Then one line on the tiers at the Calling camera. Then: does the armor work as it stands pass the whole-frame gate on armor's own account (ignoring the routed items)? Answer YES or NO, and why.
