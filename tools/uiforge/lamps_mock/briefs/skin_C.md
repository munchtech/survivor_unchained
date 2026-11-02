You are a mockup builder for the UI design lead UI 25 (agent id a11b06d476892ead3; message it only if blocked). Context budget: 200k. Item: lamps-mock-C.

Survivor Unchained (a 3D action RPG). Static 1:1 mockups (1920x1080 PNG) of the Lamps screen (the talent board) in Python (PIL, numpy, scipy, cv2). No Godot, no GPU, no git, no Agent tool. Work inside SCR only.

READ: (1) the design brief C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\ui-25\docs\design\LAMPS_SCREEN_BRIEF.md (all; §5 has a "Her light reaches so far" rule; §12 C is your direction); (2) SCR\briefs\engine_A.md (the mock state, rendering quality rules, the focus/wick content: all apply); (3) SCR\mock\SKINS.md, skim frames.py and skins\a.py. SCR = C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\45b9ec4e-5fc1-47d3-beda-6b269744e6f9\scratchpad\ui25 .
ANOTHER BUILDER owns the shared engine files right now (it is adding the reach falloff of §5 and new backdrops). Touch ONLY skins\c.py and a new frames_c.py (import the engine; override what you must inside your own files). Re-run your frames at the end so they pick up its engine changes.

DIRECTION C, "The Day's Book" (brief §12 C): the board lives in the house's book panel on the right, as the Journal and the Map do; she and the world stay at full brightness on the left; "Open wide" (Z) spreads it across the screen (that wide view is A's, so you don't draw it).
- BASES (real game frames with the book open at today's functional Lamps page, the camera already shifted for the book): SCR\shoot\out\u25_today_lamps.png (the Waystation, day) and u25_today_lamps_night.png (the Low Ford, night; landing within ~10 min of your start; if it's missing or shows no book, use the day base for both and say so). Look at the day base (a half-size copy first) to find the panel's frame and its content rect.
- Keep the panel's frame, head and tab chain exactly as the game draws them. Clear the content rect of today's list: rebuild its ground from the panel's own clean ground (sample an empty stretch of it, tile or stretch its tone and grain; no smears), so it looks like the same panel, empty.
- In the content rect, top to bottom:
  1. The header row: the layout coins I II III (II active, "The Sunderer") at the left, "3 LAMPS TO LIGHT" at the center, "Light my way [Y]" and "Open wide [Z]" at the right. Same type as A.
  2. The board at the Road stop (0.80 px/unit), clipped to the content rect with 1 px clean edges and no fade, centered on the warden quarter (the lit cluster and the day focus Morning in the Steel's path both in view). Draw A's lamp and road language (import skins\a.py's lamp/road functions) on the panel's dark ground: no world grade or pools inside, because the panel is the ground.
  3. Along the panel's foot, the wick tabs: a row of her carried skills (the 5 carried + "All learned"), using the seat art style of the HUD (crop seat discs from SCR\shoot\out\u25_town_day_foot.png's seats, 56 px), with Sunder chosen (gold ring).
  4. B_night's equivalent here, C_night: the wick panel opens in the panel's lower third (same content and plan as engine_A.md's night frame, laid out to the panel's width), focus on the Splitting Stroke Turn with its card above.
- The focus card stays inside the panel.
- Frames: out\C_day.png (day base, the board + card for Morning in the Steel, path preview), out\C_night.png (night base, wick open), out\C_crops.png (1:1 crops of the panel's board area from both, side by side). No valley frame.

QUALITY: judged at 1:1 against AAA games ("would this frame ship?"). The panel must look like the game's own panel, not a paste. Crisp type, clean edges, no muddy fills. Look at 1:1 crops and fix craft defects; don't judge the design. Then run `python C:\Users\munch\Desktop\survivorsunchained\tools\half.py` on C_day.png and C_night.png.

RETURN (under 250 words): paths, the panel's content rect, deviations and why, stand-ins, the run command. Context budget: 200k.
