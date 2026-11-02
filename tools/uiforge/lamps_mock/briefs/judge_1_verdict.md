Judge r1 (su-lead-max xhigh, Item lamps-mock-judge, 1 of 3 rounds used; 86k). Crops: SCR\judgecrops\

RANKING: C first, then A, then B. Ship C (book half panel) as the default view with A as its "Open wide"; drop B. All 8 frames gate NO; C and A CLOSE, B FAR.
Why: matches the owner's half-panel choice (Journal/Map), she is seen at full color (mean luma 56 vs A 31, B 28); A is the best full board (her build reads first, least chrome, the pools = real soul); B's bronze is flat brown beside the HUD's sculpted bronze and adds borders.

GATE NOs:
- A day: the board has no edge: lamps/roads run behind the header and through the girl's crown and the keeper's hood. A night: wick panel 3 px from the girl's hair (x 628); x0.30 world reads as a black void (generic dark tree). A valley: structure unreadable; 10 labels float over a murky courtyard.
- B day/night: at Road zoom the ring is a random arc crossing the keeper and his bowl; double-ruled plates. B valley: ring overflows the field (behind the seat bar, "THE HUNT" at y 990, the girl's hair); bosses sit on names ("DAW●S", "E●WILD").
- C day: lamps hard-clipped at the board's 1 px inner frame (two blue lamps and the hearth's left spokes cut at x ~1032; hearth 80 px from the edge). C night: card cuts a blue lamp and its "16"; ~400 px of board with the hearth clipped.
Glance (A and C): count and road read; the NEXT LAMP fails (the path to the focus looks like the other 12 fuses).

MUST-FIX, C (A's board fixes apply too: A is its wide view):
1. No hard clip: feather the board to 0 alpha over 48 px inside the field edge; delete the 1 px inner frame (x 1030-1875, y 232-872).
2. Center the build on open: the lit cluster's bbox center at the field center, every lit lamp >= 96 px inside the edge.
3. Card never cuts a lamp: shift it vertically up to +-120 px; with the wick open, slide the view so the focused Turn's road sits in the free band above y 635.
4. Path preview readable (A too): path roads 3 px #ffd27a 100%, dash 6/4; ordinary fuses 2 px at 60%; on-path lamps get the 40% inner glow.
MUST-FIX, A:
1. Field mask: alpha fades to 0 over y 84->124 and y 900->960, plus a 32 px soft knockout around the girl, the seat panel and the keeper; Old Road labels above y 900 ("DAWN'S LIGHT" at y 843 sits over the keeper's head).
2. L3/R3 render as bare crescents ("( Find", ") Home"): real stick key caps at 22 px like Y/B.
3. Wick panel 640 px (x 650-1290), >= 24 px clear of both statues.
4. Valley legible: roads 1.5 px at 40% (now ~1 px 20%), unlit dots >= 3 px at 50%, three faint concentric guides (hearth, roads, Old Roads) 1 px 18% (B's engraved circles are why its valley reads).
5. Night grade x0.30 -> x0.38, lit pools at full color.
MUST-FIX, B (only if kept): ring <= 860 px at Valley (y 92-952) never behind the bar/figures, fade the arc where it crosses the HUD at Road zoom; bosses between names; unlit collets 35%; the band in the HUD's sculpted bronze (patina, specular), plates a single 1 px rim; card off the engraving.
NICE-TO-HAVE: wrap the Turn's line to 2 lines (ellipsis cuts "heav..."); a real three-ply braid ~40 px before the strands part (the soul hook to her braided hair, missing now); blue lamps read as plastic Christmas balls (specular glint + darker core = cobalt glass); one gate notch at the road's door instead of four "16" chips per lamp (1220-1300, 395-470); link lamps = empty pills (add a 1 px inner chain-link stroke); valley labels >= 40 px from the header and the card ("THE STORM" y 109; "STEEL AND BLOOD" 20 px above the card).
