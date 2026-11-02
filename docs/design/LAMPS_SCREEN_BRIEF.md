# The Lamps screen: the UI design brief

UI 25, 2 November 2026. This is the design for the real Lamps screen (PHASE2_SCOPE.md item 5): the board v2, the Wicks, the layouts and respec, on one screen. It follows CLASS_IDENTITY_AND_TALENTS.md §3.2-3.6, which the owner approved on 27 October. The owner answered PHASE2_SCOPE's order question on 2 November with "Board + Lamps first". The look is the owner's pick from the directions in §12. Everything else here is the UI lead's design and holds for any direction. Classes' functional pages (ArtsScreen behind `--board`) keep working until this screen lands.

## 1. The owner's words this answers
- "as simple to figure out as just clicking and having fun, but as complex to master to have fun planning" (skill trees, 11 October).
- "we really need to get going on our skill trees and class identity" (1 November).
- "we like to see our beautiful game": no whole-screen pages, panels over the world. On the Journal and the Map: a full screen "feels bad"; he chose the half-window panel "with an option to expand".
- "those borders are just ugly, adding more of them dosn't make them better". Generic fantasy ornament spread evenly reads as "ai looking". Soul comes from meaning, placed once.
- "things should hit what their tooltips say": no hidden multipliers.
- The HUD needs soul (27 October): the Drowned Girl in bronze. This screen is that HUD's sibling.

## 2. What the screen is for
1. **A glance (one second):** what's my build, how many lamps can I light, and where can I go next.
2. **Click and have fun:** the next lamp glows. Light my way lights it for you. A far lamp lights its whole road in one press.
3. **Plan for hours:** find by what a lamp feeds, preview paths, see blue lamps' prices, crossings, *Unhoused*, wick plans, and three layouts.
4. **Respec for free**, by day, at a town's lamp-post. Elsewhere you can only light lamps.

## 3. What the best do, and what we take
| Game | Best | Worst | We take | We avoid |
|---|---|---|---|---|
| Path of Exile 1/2 | One shared board where distance is the price; the path preview; allocating the whole path in one click; search rings | Icon soup at overview; ornament on every node; a full-screen opaque page | The shared board, path preview, light-the-path, search rings | Ornament per node; the opaque page |
| Grim Dawn, devotion | Constellations of light on a dark sky; a lit build reads as shapes | Tedious affinities; cramped | Light on dark: the lit build is the brightest thing on screen | Its sky backdrop that hides the game |
| Diablo IV, skill tree | Legible clusters; the skill bar stays on screen for assignment; a pad cursor that snaps to nodes | The paragon board's gray tiles | The skill bar stays (our HUD's seats become the wick tabs); snapping focus | Grids of identical tiles |
| Final Fantasy X, the Sphere Grid | Pad movement along the paths of a huge board | Slow travel | The stick walks the roads lamp to lamp | Moving a token to spend |
| Last Epoch | Per-skill trees right beside the skill | Many trees to read | The Wick as a compact panel over the chosen skill | 20-node trees |
| Ori, Hades II | Light as reward; one diegetic object with meaning | Small scope | The flame catching as the reward moment | |

## 4. Layout at 1920 by 1080 (all directions, except C's panel in §12)
- **The world stays live.** The play camera doesn't move. The sim pauses by day (nothing hunts her in town) and the world keeps its motion (flames, foliage, her idle). The grade over it is the direction's (§12).
- **The header** sits at y 20-76, with no plate.
  - Left: the three layouts (§9).
  - Center: **"3 LAMPS TO LIGHT"**: the number in Cinzel 700 at 30 px and the words in Cinzel 600 at 16 px letterspaced, warm gold. Under it, in Alegreya Sans 14 dim: "15 lit · 13 from levels, 2 from the story". At a lamp-post by day a third line adds, warm italic: "At the Waystation's lamp-post: lamps go out free".
  - Right: Light my way, Find, Close, each a word with its key cap.
- **The board's field** runs x 0-1920, y 84-960.
- **The foot is the HUD's own instrument, in place:** the girl, the panel and the keeper.
  - Its six seats are the **wick tabs**.
  - **The keeper's fire is the Flare's tab.** Focusing it marks the Flare's lamps on the board, and its card is the Flare's.
  - The flask and dash drop to 45% (they have no wicks). Life and the level coin are as in play.
  - This follows Diablo IV, whose skill bar stays under its tree. It also keeps the screen in the HUD's family: same bronze, same light.
- **The prompts** run in the lower right, where the tally sits in play (right of the keeper, x 1610-1900), right-aligned, 3 short lines. They are the device's keys: LT RT Zoom, LB RB Next lamp, R3 Home, View Layouts, L3 Find.
- **The focus card** sits beside the focused lamp (§7). **The wick panel** rises over the chosen seat (§8).

## 5. Reading 574 lamps at a glance
**Three zoom stops.** The mouse zooms continuously between them; the pad steps between them (LT/RT). Sizes are lamp diameters in px at 1080; at 1440 scale everything by 1.333.

| Stop | px per board unit | Nearest lamps | What shows | Purpose |
|---|---|---|---|---|
| **Valley** | 0.337 (the board fills the field's height) | 14 px | Dots (start 14, blue 10, entry/Strike 9, notable 7, link 7, rite 6, others 4); roads 1 px; labels for the 4 callings, the Ford and the 10 Old Roads | Orientation: the whole build as one lit path |
| **Road** (default) | 0.80 | 34 px (p10 40) | Full lamp shapes (below); roads with lit/fuse/cold; labels for hearths, roads, bridges, crossings and Old Roads | Working: a hearth, its two roads and the bridge in one view |
| **Lamp** | 1.25 | 52 px | Shapes ×1.3; each notable's feed glyph inside; names under notables, blue lamps, entries and Strikes (Alegreya Sans 700 14 caps, 80%) | Reading closely |

On open, the board is at the Road stop, centered where she left off; the first time, on her frontier.

**The hierarchy at a glance**, brightest first:
1. Her lit lamps and the roads between them: the light is the build.
2. The frontier, the lamps she can light now, breathing an ember rim.
3. The blue lamps: the only cool color, cobalt glass.
4. The Flare's lamps: the keeper's fire color.
5. Everything else: cold glass on silver roads.
6. Labels: low contrast, letterspaced Cinzel caps.

**Kind by shape, state by light; color only for meaning.** These silhouettes are shared by all directions. Diameters are at the Road stop.

| Kind | Shape | Size |
|---|---|---|
| start (the hearth) | round, a heavy collet, 4 short rays; the calling's weapon glyph inside (warden shield, reaver axe, arcanist staff, stalker bow) | 34 |
| entry (a road's door) | round, double ring | 24 |
| ultimate (Strike, Stand) | an 8-ray sunburst, Flare fire | 26 |
| ultimateMod, flareLamp | a flame drop / round, Flare fire | 12 / 16 |
| blue | round with a 4-prong collet (prongs at 45°), cobalt glass | 28 |
| notable | round, rim + inner ring; its feed glyph at the Lamp stop | 20 |
| rite | lozenge (the house's diamond); its tag glyph at the Lamp stop | 18 |
| link | one chain link (a stadium ring, the game's *Unchained*); when lit, its bound skill's glyph beside it | 22 × 14 |
| hand | round with the palm glyph | 18 |
| form / reflex / reflexUp | round with a dash chevron / with a parry arc / plain | 14 / 16 / 12 |
| small / attribute | a round bead / a rounded square stud | 12 / 10 |

**Roads** are straight, rim to rim (each end stops 2 px short of the lamp).
- Unlit: 1.25 px.
- Lit (both ends lit): 2 px, with a soft glow.
- The fuse (lit to available): a warm dashed line, 4 px on, 4 px off.
- A path preview: the fuse's dashes running toward the focus at 30 px/s.

**Labels** sit beside their group's center, pushed outward from the Ford and placed clear of lamps (the build checks overlaps). Cinzel 600, 15 px (16 px at the Valley stop), letterspaced 0.16 em, ink #d8cfbd at 75%, with a 4 px dark halo.

## 6. States
| State | When | Look (A's light language; B and C restyle the material, not the logic) |
|---|---|---|
| **Lit** | lit | Warm glass glowing from within (core #fff0c4, rim #e9b45c); a halo 1.8× its size; its roads to lit neighbors gold |
| **Available** | next to a lit lamp, gate met | Cold glass with an ember rim (#ff9a3c) breathing, 60-100% over 2.6 s; the fuse from its lit neighbor |
| **Unlit** | not yet reachable | Cold dark glass, a silver rim at 50% |
| **Blocked** | its road's gate isn't met | Unlit, the rim at 30%; a gate numeral (4, 8 or 16) in a small notch at its lower right, at the Road and Lamp stops only |
| **Dim** | it feeds nothing she carries (§3.6) | Glass desaturated, the rim dotted, 50% opacity; the card says why in one line |
| **Asleep** | lit but dim | A small gray-blue pilot flame (#a9b4c2) instead of the warm one; its roads stay gold, since it still holds the road |
| **Focus** | under the cursor or the pad's focus | A crisp 1.5 px gold ring (#e8c87a) at r+5, a soft outer glow at 30%, the lamp ×1.1 |
| **On the path** | between the lit lamps and a far focus | A warm inner glow at 40%; the fuse running |
| **Found** | matches Find, or feeds the chosen skill | A white-gold ring pulse; the rest drop to 45% |

Color-blind safe: no state is told by hue alone. Lit is brightness, available is a moving rim, blocked a numeral, dim a dotted rim with low contrast, and blue lamps a distinct collet.

## 7. The focus card (the one-line rule)
- **Size and place.** 380 px wide (300-420), padding 16. It goes right of the lamp when the lamp is left of x 1300, else left, 22 px from the lamp's rim. It is centered on the lamp vertically, clamped to the field, and never over the header or the foot.
- **Contents, in order and ruled** (the house's tooltip order):
  1. The name in Alegreya 700, 21 px; at the right, the kind as a chip (Alegreya Sans 700 12 caps: NOTABLE, BLUE LAMP in cobalt, RITE, LINK, FLARE in fire).
  2. The place in Alegreya Sans 13 caps, dim: ROAD OF THE SUNDERER.
  3. A rule.
  4. **The one line** in Alegreya 17 px. One sentence; it may wrap to two lines at 380 px.
  5. **Feeds:** the line glyphs of what it feeds (16 px) and the words "Feeds Sunder, Oathblade". Carried skills are gold, others gray.
  6. A blue lamp's **price, in one red line** (Alegreya italic 16, #e0705a).
  7. A rule, then the **state line**:
     - "Light it: 1 lamp"
     - "3 lamps away · you have 3"
     - "Opens at 16 lit on this road · 9 lit"
     - "Sleeps: carry a fire skill to wake it"
     - "Lit · lamps go out at a town's lamp-post, by day"
  8. The **prompts** for this lamp only: "A Light · X Hold: put out".
- **Links** add their pick: "Fires: Rebuke (change: A)". A press opens an inline row of her carried skills' glyphs to choose from.
- **Wick lamps** use the same card, above the wick panel.

## 8. The wick panel
- **Opening it.** Choose a seat in the foot: the pad goes D-pad down, then A; the mouse clicks the seat. Tab toggles it. It rises over the seat in 0.2 s.
- **Size and place.** 780 by 228 px, bottom at y 968, centered on x 960. The chosen seat gets a gold ring, and a 2 px gold **wick stem** with a soft glow rises from the seat to the panel. The board's view slides up to keep the focus clear.
- **Left block:**
  - the skill's own seat art (56 px);
  - its name in Cinzel 700, 22 caps;
  - "DAY RANK V" in Alegreya Sans 700 13 caps, gold;
  - "5 of 12 lit · 8 planned" in Alegreya Sans 14, dim.
- **The braid.** The three strands leave the skill's knot as one braid and part into three rows, 52 px apart. A wick is braided from strands (and her own hair is braided). Each row holds:
  - the strand's kind, small, above its start: CALLING · LIGHT MY WAY, SHAPE, SCHOOL, BIND;
  - three lead-in lamps (22 px) at a 70 px pitch;
  - the **Turn** (34 px, flame-crowned);
  - the Turn's name in Alegreya 700 18, and its one line in Alegreya 15, ellipsized (in full in the card).
- **The plan.** Planned lamps carry their order, 1 to 8 (Alegreya Sans 800 12, gold, upper right).
  - Lamps up to her rank burn.
  - Planned lamps not yet lit wear the ember rim: the night lights them in this order as the ember climbs.
  - Unplanned lamps are cold.
- **One Turn a skill.** Once a Turn is planned, the other two Turns are crossed by a thin dark bar, and their line reads "One Turn a skill".
- **The whole sum** runs in one line along the panel's foot, from the sim: "Damage 142 = 100 base · Hand ×1.15 · rites +12% · Turn: every 2nd swing heavy" (§3.6, no hidden multipliers).
- **In the panel:**
  - the stick walks the lamps (rows and pitch);
  - A plans or unplans;
  - Y lays Light my way's suggested strand;
  - B closes the panel.
- **Learned skills she doesn't carry** have wicks too. A seventh tab after the seats, "All learned", opens a short list above the foot.

## 9. Layouts (three) and respec
- **The three layouts** sit at the header's left:
  - three bronze coins (32 px), I, II and III, the active one lit;
  - then the active layout's name in Alegreya 700 17, named for her type: "The Sunderer";
  - on focus, a card: "II · The Sunderer · Long Cut · 15 lamps", and the glyphs of its carried skills.
  - A layout is a whole build: the board, the Wicks, the carried skills and the Flare.
- **Switching** works only by day at a town's lamp-post, never mid-night or mid-map. Elsewhere the coin's card says where.
  - Out: the lit lamps go out from the tips inward (0.25 s).
  - In: the new layout lights outward from her hearth (0.45 s).
  - The seats' and the keeper's glyphs turn over.
  - "Copy to II / III" is in the coin's card.
- **Putting lamps out** works by day at a lamp-post: X held 0.35 s, or a right-click held. A lamp that others hang on keeps the hold going to 0.9 s, and its branch goes out from the tips. "All out" is in the header, held 0.8 s. **Changing her type** is on the other road's entry: "Walk this road (every lamp goes out)".
- **Lighting** works anywhere out of a fight. Ask Classes for a **session undo**: the lamps lit since the screen opened can go out anywhere until it closes. A slip shouldn't need a walk to town.
- **By night** the board is read-only and says so in the header. (The night's own growth is the Wicks, lit by the ember.)

## 10. Navigation
**Pad** (Xbox names; the prompts show the device in hand):

| Input | Does |
|---|---|
| Left stick | Moves focus along the roads to the connected lamp nearest the stick's direction (±50°). With none, it goes to the nearest lamp in a ±35° cone within 260 units; with none, a soft tick and no move. It repeats after 0.32 s at 7 a second. The view follows when focus nears the outer 22% of the field (0.18 s ease). |
| Right stick | Free pan, up to 1400 units/s scaled by zoom. When it's released, focus snaps to the lamp nearest the center if it left the view. |
| LT / RT | Zoom out / in by stops, 0.22 s, about the focus |
| A | Light. On a far lamp, light its cheapest path if the points allow (the path was already previewed while focused). |
| X (hold) | Put out (§9) |
| Y | Light my way: lights the suggested lamps for every spare point, one by one, 0.09 s apart |
| LB / RB | Previous / next lamp she can light now, clockwise from her hearth |
| D-pad down / up | Into the foot's seats (wick tabs) / into the header (layouts, Find, Light my way); left/right walks them; A picks |
| L3 | Find: a row of chips (her carried skills, the schools, blue lamps, links, rites, the Flare). The chosen chip marks what it feeds. |
| R3 | Home: her hearth, or her frontier |
| B | Back: closes the wick, then leaves the header, then closes the screen |

**Mouse and keyboard:**
- Hover is focus: the card shows, and a far lamp previews its path.
- Left click lights (the path, for a far lamp). Right click held puts out.
- The wheel zooms continuously about the cursor.
- Dragging on empty board (left button), or with the middle button anywhere, pans.
- WASD and the arrows pan; F is Find (typing filters by name, line or tag, and Enter steps through the matches); H is Home; 1, 2 and 3 are the layouts; Space is Light my way; Tab is the wick; Esc closes.

**Where it opens from:**
- the book's chain, as a new tab "Lamps" (L), which opens this screen;
- a level gained with a point brings a small "A lamp to light (L)" over the HUD's coin for 6 s;
- at a town's lamp-post, "Tend the lamps" (E) opens it ready for respec.

## 11. Motion and sound
Every motion is short. Reduce-motion stills the breathing, the flicker and the running fuse.

| Moment | Motion | Sound (for the audio lead) |
|---|---|---|
| Open | The world's grade fades in over 0.35 s; the lamps fade in from her hearth outward (radial stagger 0.25 s); the lit lamps' halos bloom last (0.15 s) | Ambience ducks 9 dB over 0.3 s; a lantern shutter opens (a soft clack and a low whoomp); a quiet night bed at -24 dB |
| Close | Reverse, 0.2 s, no stagger | The shutter closes; ambience back over 0.4 s |
| Focus move | The ring glides 0.10 s; the card cross-fades 0.08 s | A quiet glass tick, pitched by kind (small high, notable middle, blue low), ±2 semitones, at most 12 a second |
| Light | The flame runs along the road from the lit neighbor (0.16 s, a bright head with a short tail); the lamp catches (×0.85 to 1.0, a 0.12 s bloom, 3-5 sparks rising 12 px); its halo grows (0.3 s) | A match strike and a breath of flame (fuller for a notable) |
| Light a path | Lamp by lamp, 0.09 s apart | One strike, then quick ticks |
| Blue lamp lit | Plus a cool ring (white-blue, 60 px, 0.4 s); the screen's light cools 5% for 0.3 s | A low bell with a cold shimmer |
| A gate opens (the 4th, 8th or 16th on a road) | A shimmer runs along the road's lamps (0.4 s); the numerals fade | A latch, then a rising shimmer |
| Put out | The flame gutters (0.18 s); a smoke curl rises 16 px and fades (0.5 s); the road's gold drains (0.2 s) | A soft snuff and a hiss |
| Denied | The focus ring shakes ±3 px (0.15 s); the card's state line flashes | A dull wooden knock |
| Layout switch | Out from the tips (0.25 s), in from the hearth (0.45 s) | A gust, then a chain of strikes |
| Wick: plan a lamp / a Turn | Light rises along the strand / the Turn's tip flares (0.3 s) | A thin tick / a deeper whoomp |
| Lit lamps at rest | Luma flicker ±4%, each lamp its own phase, at the Road and Lamp stops only | none |

## 12. The directions for the owner's pick
All three share §4-§11. They differ in what the board *is*.

**A. Nightfall: light on dark, no frame.**
- When the screen opens, night falls over the live world (by day a dusk: luminance ×0.42, a warm gray; by night ×0.30, cool). She and the world stay faintly seen.
- The board is drawn only in light. Cold glass beads sit on thin moonlit silver roads; her lit lamps burn as small warm flames on gold roads.
- **Each lit lamp throws a soft pool that gives the world back its own colors around it:** her build lights the valley.
- The header and labels are plain type. The card and wick panel are smoked glass with the HUD's 1 px gold rim (#cdae72). The one ornament on screen is the HUD's foot.

**B. The Lamplighter's Wheel: a bronze astrolabe.**
- The board is an object in the HUD's own material: a crisp polished dark-bronze ring at the Old Roads' outer edge, with a gold inlay line inside and out and the Old Roads' names engraved in the band. Four small bosses sit at the quarters; there is no other ornament.
- Inside the ring is smoked glass over the world (luminance ×0.28, a 2 px blur, a faint warm reflection from the upper left). The world outside the ring is dimmed ×0.55.
- Thin concentric engraved circles mark the hearths, roads and crossings, so the wheel reads as an instrument at any zoom.
- Unlit roads are engraved grooves, and lit roads are gold wire inlay. Lamps are glass cabochons in bronze collets: unlit dark smoky glass, lit warm amber glass glowing from within.
- The card and the wick panel are the HUD panel's bronze plate.

**C. The Day's Book: a half panel, then open wide.**
- The board lives in the book's right-hand panel (the house's side panel, about 1040 px), as the Journal and the Map do. She and the world stay at full brightness on the left (the book's camera shift).
- "Open wide" (Z or R3) spreads it across the screen as A.
- A's lamps and roads are drawn on the panel's dark ground.
- The wick tabs are a row of her carried skills along the panel's foot, and the wick opens in the panel's lower third. The HUD hides, as for every book page.
- **For:** it matches the other screens and the owner's half-panel choice, and she is seen.
- **Against:** half the board area means more panning, and the board loses its sweep.

## 13. Performance
- **The board is three draw calls.**
  - The lamps: one MultiMesh of 574, with per-instance kind, state and phase; shapes drawn as SDFs in one shader, so no atlas is needed.
  - The roads: one mesh of 591 quads with per-vertex state and an anti-aliased line shader.
  - The halos: one additive pass, at most about 90 soft quads.
- **Labels** are at most about 60 visible, culled by stop. The card and the wick panel are ordinary Controls.
- **The grade** is one full-screen shader over the 3D. B and C read the screen texture at half resolution for their blur.
- **Budget** at 1080 on the dev machine: GPU at most 0.25 ms, CPU at most 0.2 ms a frame. Measure ABAB against the screen closed.
- **Hit testing** uses a 64-unit grid. Pad moves use precomputed neighbor lists with direction cones.

## 14. Data the screen needs from Classes (ask main; ids, kinds and positions are frozen)
1. The **road links' gate 8** (board_v2 fe334726c had 0; Classes is fixing it).
2. Each lamp's **one line** (the texts, Phase 2 session 1) and what it **feeds**: tags or skills, for the glyph row and for dimming. One field per lamp, `feeds`, or a `Lamps.Feeds(id)` call.
3. `LampBook.PathTo(ch, w, id)`: the cheapest lamps to light to reach a lamp, honoring gates.
4. `LampBook.Sleeps(ch, id)`: why a lamp is dim, as a reason the card can word.
5. Link picks: get and set the bound skill.
6. The suggested lamps, for Light my way's preview.
7. A session undo (§9).
8. The wick's whole sum per skill (base, Hand, rites, Turn), as numbers.

## 15. Checks before it ships (the build's judge list)
- **The whole-frame gate:** would this frame ship in a AAA game as it stands? Day and night, at 1:1, at the play camera.
- The glance: in one second, a judge names her build's road, the count to light and the next lamp.
- Every lamp is reachable from her hearth by stick moves alone (a test walks the graph).
- No label overlaps a lamp or another label at any stop (a test).
- Text is at least 13 px at 1080. The card never needs hover-only information on a pad.
- Perf ABAB within §13.
