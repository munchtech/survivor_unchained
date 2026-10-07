# UI design: status

Agent (successor, 6 October), branch `worktree-agent-adba22c3df8f39418`. Pictures: `docs/ui_review/build9/` (the HUD keystone), build8 and earlier before it. The design and its research: `docs/design/UI_RESEARCH.md`, "The HUD".

## Current state (built; seen at 1080 and 1440, at 1:1 on the instrument)
- **The instrument** (`src/Ui/Instrument.cs`, `shaders/hud_vessel.gdshader`): her irons along the foot, 850 px, symmetric. Life in the left cuff (blood with a living surface, a trail, the shield's light, a heartbeat when low), the art in the right (its charge rising gold, its line glyph, the seconds), the draught and the dash beside them, six places between (night: all six, empties quiet; day: only what is carried, centred), the ember as heat along the chain under them, the level on a padlock at its middle that springs as she rises. Always shown, at peace too. Drawn iron until UI art's is in (build9/13).
- **Top:** a boss's bar at the top edge (name, groove, stagger, title); nothing else there. **Lower right:** the night's word, clock, slain, gold. **Tips:** full size from the first, below a boss's bar, held while a banner shows (build9/12).
- **Minimap:** the cuffs' iron as its bezel, north an ember notch, the day's path over its top (the old dial folded in); steps marked with the house's diamond.
- **Journal and Map** in the book's half panel with "Open wide" (Z / R3): the Journal as two columns of type, wide as the parchment book over the world; the Map's window 844 by 600 with the road under it, wide across the screen with the full list (build9/6 to 10).
- **The tab chain:** quieter key caps, the chain closer under the names, cold links dulled, the leather end squares gone (it ends in its eyes) (build9/11).

## Next
1. **Shoot the last fixes, unseen:** the map opens filling its window (cover) and "All I know" shows all; the wide map's list room fix; the People heading at 20 px in the panel; loot labels keep off the instrument and tally.
2. Self-critique at 1:1 of the whole HUD against "the best HUD in any game" before showing the owner; then UI art's pieces in.
3. Portraits when the face lead messages (see the handoff). Review combat's `StoryChoices` at 1:1.

## Key decisions
- One instrument, mirrored: round for what she lives and acts by, square for what fires by itself.
- The chain means the book's tabs and, in play, the ember: one object a screen (the HUD hides when the book opens).
- The top edge is the boss's; the tally waits in a corner; tips and banners never share the upper third.
- Art glyphs in the HUD are line glyphs (the painted arts cover the glass).

## For UI art (start here; the code already asks for each file by name and draws a stand-in until it is there)
All at twice the shown size (UiArt halves them), lit from the upper left like the chain's links, warm forged iron, restrained (no filigree, gems or skulls: the owner's "no muddy textured borders"). Shown sizes:
- **`hud/cuff.png`** (the left cuff; the code mirrors it for the right): glass radius 60, iron band 60 to 73, centred in a 174 px square (348 file). A hinge's knuckle on the outer (left) side at 9 o'clock, about 12 by 26, standing 9 px out; the chain's eye on the inner side 32° below level, its ring centred 75 px out, its hole open (the chain's end runs under it). The glass (r < 60) fully transparent. Two rivets by the hinge at most.
- **`hud/cuff_small.png`** (the draught's and the dash's): glass radius 23, band 23 to 29, in a 70 px square; a plain band.
- **`hud/socket.png`** and **`socket_empty.png`**: 58 px squares; a forged square ring 3 to 4 px wide, its seat sunk; the middle (inset 4) transparent on the filled one; the empty one quiet, its middle dark at about 60%.
- **`hud/lock.png`, `lock_open.png`, `lock_hot.png`**: a padlock about 30 by 38, its shackle's top at the file's top middle (the anchor hangs it from the chain's middle link); a plain body face (the code stamps the level at 23 px down its middle); open: the shackle's left leg sprung out; hot: the closed lock glowing, laid over it by the heat.
- **`minimap/bezel.png`**: disc radius 100, band 100 to 109, in a 226 px square; the cuffs' iron; the code draws the north notch and the day's path.
- **`hud/boss_groove.png`**: a nine-slice (16, 8, 16, 8; tiled; 8 out) for the 850 by 16 bar: a plain groove, iron clamps at its ends, its middle open for the fill.
- **`hud/globe_glass.png`**: used as it is over both vessels (good); repaint at the new size only if it helps (its glass's edge at 91% of the file).
- **The chain:** the book's links at 0.8 scale; please check the heat ramp at that size (the reached body uses warm, the leading links hot).
- **No longer used by the HUD:** `hud/globe_rim.png`, `ring_art.png`, `medal_level.png`, `medal_heart.png`, `frames/console.png`, `frames/weapon_slot.png`, `bars/casing*.png`, `bars/track_boss.png`, `bars/ember_fill.png`, `experience_fill.png`, `health_fill.png`, `minimap/frame.png`, and the tab chain's end `chain/tab.png`. Their registry entries are gone; remove or reuse the files as you judge.

## Notes for other areas
- **Everyone:** new action `Act.Expand` (Z, pad R3) for the book's wide pages. `GameHud.TopClear` is 24 without a boss (the ember no longer sits at the top). Switches for pictures: `--journal-wide`, `--map-wide`.
- **The experience director:** the day dial now rides the minimap's bezel where there is a map (DayDial remains where there is not).
