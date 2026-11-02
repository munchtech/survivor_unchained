You are the mockup builder for the UI design lead UI 26 (agent id a51ec0ede69eafdfc; SendMessage it only if blocked). Context budget: 130k. Item: lamps-mock-fix.

Survivor Unchained (a 3D action RPG). Static 1:1 mockups (1920x1080 PNG) of the Lamps screen (the talent board) in Python (PIL, numpy, scipy, cv2). SCR = C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\45b9ec4e-5fc1-47d3-beda-6b269744e6f9\scratchpad\ui25 . No Godot, no GPU, no git, no Agent tool. Work only in SCR\mock (and SCR\c_work). Don't touch skins\b.py. First copy the current out\A_*.png and out\C_*.png into out\r2\ (keep them).

Context: the previous builder applied round 1's fixes (SCR\briefs\fix_r2.md says what; don't redo them). The round-2 judge passed C_day and failed C_night, A_day, A_night and A_valley on the four blockers below. Fix exactly these, plus the listed small items, nothing else. Don't redesign: keep the state, the lamp and road language, the colors and the type. READ only: SCR\mock\SKINS.md, then grep and read just the code you change (frames.py, frames_c.py, skins\a.py, skins\c.py, foot.py, text.py). The code is the previous builder's: grep for the wick panel, card, stem, prompts and mask functions rather than reading whole files.

BLOCKERS (judge's values unless marked lead):
1. Night, both directions: the focused Turn gets one home.
   - While focus is inside the wick panel, show NO floating card.
   - The Turn row carries it all: the name (as now), its line wrapped to at most 2 lines at the row's text width (at least 210 px; widen into free space if there is any), Alegreya 14 px (never under 13), then the card's state line under it in Alegreya Sans 13 px gold #e8c87a ("Lit · 4th in the plan · the ember lit it at day rank IV").
   - The Turn node's plan number "4" moves to the node's upper left (-16, -16 from its center); the row's label starts 14 px past the node's ring.
   - A: the wick panel loses its box as C's did: smoke at 88% fading to 0 over 24 px at its edges, no gold rim. All its text at least 24 px inside the panel's edge. A's short stem from the seat up to the panel stays.
   - A's lower-right prompts with the wick open (lead): "A Unplan" / "Y Light my way" / "B Back". C's bottom row stays "Click Plan · Space Light my way · Tab Board".
   - C: recenter the board in the freed space (the band between the header row and the wick band, now free of the card): the hearth, its spokes and every lit lamp at least 96 px inside the board window, none in the edge fade.
   - A night: with the card gone, she must be in view; check it.
2. A day and A valley: she is drawn over the board. Mask the board (lamps, roads, fuses, halos, hub spokes, labels) to 0 inside her silhouette with a 10 px feather, so nothing crosses her and she reads as standing on her road. Get her silhouette from the nofoot backdrop (cv2.grabCut on a small rect around her, about 130 x 200 px; clean it with a 2 px close), cache it in SCR\c_work, and check it at 1:1 (it must follow her edges, not a box). Do the same in A night if any board element crosses her there.
3. C night, the wick stem (lead and judge): it now reads as a column divider. Make the stem the braid's root: it rises from the top of the chosen tab (about 1268, 880) to y 762, bends right on a 20 px radius, and runs straight into the start of the braid's twist (about 1295, 742; use the braid's real start point). Delete the stem's run above that (y 633 to 742) and drop the hairline rule at the band's top (y 633): the band's feathered top is its edge. One continuous gold line, same weight and glow as now: the wick rises from the skill and braids into its three strands.
4. A valley: zoom out to x0.9 (the ring 840 -> 756 px, spanning about y 142-898), so the whole ring sits inside the unfaded area (y 124-900). The outer labels move in with it.

SMALL ITEMS (do them all):
- C day card 14 px down (top edge at 644) so both unlit lamps above it clear its edge by at least 6 px. A day card 10 px down to clear the "16" chip and the pill above it.
- Number chips (plan numbers, gate numerals) fade with their lamps (the edge feather and the reach fade): no chip floats alone (C night had "3" at 1045,390 and "8" at 1053,568).
- Find shows once (lead): A keeps it in the header ("Y Light my way · L Find · B Close"); the lower-right board prompts become two rows: "LT RT Zoom · LB RB Next lamp" / "R Home · View Layouts".
- The Drowned Girl's knockout widens to 48 px at her face (a lamp ring floats 25 px in front of her face at 438,880 in A).
- Night grade x0.38 -> x0.5 with a cool moonlight tint (multiply about 0.85, 0.93, 1.10), so the world outside the pools reads at a mean luma of about 18 of 255, not black. Pools stay at full color.
- Edge labels at least 64 px inside the screen edge ("THE WILD" sits 14 px from it).
- Valley labels that sit on roads (WARDEN, REAVER, THE STORM) get a 3 px dark halo at 60%.
- Blue lamps: the shine becomes a 2 px crescent at the upper left; the cobalt core a little darker. They still read as glossy marbles.
- On-path lamps' warm inner glow 40% -> 60% (lead: it's barely visible).
- C: a 15% warm glow on the page under the lit cluster (a soft radial, warm #ffcf86, about 1.6x the cluster's bbox), echoing A's pools on the book's page.

RUN (from SCR\mock): python frames_c.py all ; python frames.py A all . Then python C:\Users\munch\Desktop\survivorsunchained\tools\half.py on the five frames (out\C_day, C_night, A_day, A_night, A_valley .png), and one contact sheet SCR\mock\sheet_r3.jpg of the five half frames (2 columns, small labels, quality 88). Check what you changed on small 1:1 crops (the silhouette mask, the stem into the braid, the Turn row, the chips, the valley ring), never whole full frames.

THEN THE OWNER'S SHEET: write SCR\mock\owner_sheet.py and run it. Output C:\Users\munch\Desktop\survivorsunchained_inputs\ui25_lamps\lamps_owner_sheet.jpg (quality 93; make the folder) and copy the five full frames (PNG) beside it. Dark ground (#0e0e10), type from text.py (Cinzel for titles, Alegreya / Alegreya Sans for captions, light ink #e6dccb, dim #a99f8d), 24 px gutters.
- Top title: "THE LAMPS SCREEN: PICK A DIRECTION" (Cinzel 30). Under it, one line each (Alegreya Sans 20):
  "Option 1 (recommended): C, The Day's Book, as the default, with A, Nightfall, as its Open wide (Z)."
  "Option 2: A only, full screen."
  "B, The Lamplighter's Wheel: tried, far behind: cut."
- Then the centerpieces at 1:1, never scaled, 2 per row, each with one caption line above it (Alegreya Sans 18):
  1. C day: the book panel's board and card (crop about x 1000-1910, y 140-1000). "C, day, 1:1: the board lives in the book's panel, like the Journal and the Map. The gold dashes lead to the lamp you point at."
  2. C night: same rect. "C, night, 1:1: a skill's wick open. The wick rises from the skill and braids into three strands; the night lights them in the order you plan."
  3. A day: the tightest rect holding the lit cluster, her, and the card, plus 60 px. "A, day, 1:1 (Open wide): the world dims to dusk, and each lit lamp gives the cobbles back their color. Your build lights the valley."
  4. A night: the lit cluster down to the wick panel and both statues' heads. "A, night, 1:1: the same wick panel between the Drowned Girl and the keeper; the board is light on the dark."
- Then the five full frames at half size (960 x 540), 2 per row, each with 3 caption lines under it (Alegreya Sans 17):
  C_day: "C, The Day's Book (default), day." / "Half panel: she and the town stay in full color on the left." / "Matches your half-window choice for the Journal and the Map."
  C_night: "C, night, the wick open on Sunder." / "The board slides up; the Turn's words live in its row." / "By night the board is read-only: the wick is the night's growth."
  A_day: "A, Nightfall (Open wide), day." / "Full screen over a dusk grade; the HUD's seats become the wick tabs." / "Her lit lamps' pools are the soul: her build lights the world."
  A_night: "A, night, the wick open." / "A cool night grade; the pools keep full color." / "The keeper's fire is the Flare's tab."
  A_valley: "A, the whole board (the Valley stop)." / "Four callings around the Ford, the Old Roads at the rim." / "Her build reads as one lit path."
- Also save lamps_owner_sheet_half.jpg (the whole sheet at half size) in SCR\mock\ for the lead's look.

RETURN (under 200 words): one line per blocker and small item (done / changed value and why / not done); the paths (sheet_r3.jpg, the owner sheet, its half copy); anything a judge would still catch. Context budget: 130k.
