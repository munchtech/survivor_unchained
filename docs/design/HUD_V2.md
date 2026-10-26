# HUD v2: her irons, made

UI design solver for UI 11, 26 October 2026. The owner's bar: the foot and the globes "need to be incredible, its a keystone"; soul like the chain and the lamp ("SOUL"), no borders, nothing "ai looking"; "one composed group, not loose pieces"; judged at 1:1 game-camera frames at 1080 and 1440: "would this ship in a AAA game as it stands?". Written from the o1a/o1b shots (`godot/.shots/`) and the twelve teaching moments. The layout in `UI_RESEARCH.md` ("The HUD") stays, with five small deltas (section 3). What changes is how each piece is made and how they join.

## 1. Diagnosis

**In one line:** the chain is the only thing on the HUD that was *made*. Everything else is *drawn*, so beside the chain it reads as plastic. And because nothing touches anything, the HUD reads as ten pieces lying on the world, not one instrument.

At 1:1 (o1a_foot, o1b_foot):
1. **Two materials in one object.** The chain is Blender iron, lit from the upper left, casting a shadow. The cuffs, sockets, rounds and lock are C# strokes: flat mid-gray rings with no thickness, no light and no shadow. Their value sits at the night ground's own mid-tone, so they are neither on the world nor part of it.
2. **The life glass is a sticker.** It is a uniform, saturated red disc with a white gloss blob and a heavy stroked number dead center. It has no depth, no surface and no light passing through it. The art glass at full is a flat orange disc with a white line icon (a mobile game's button). Empty, it says "0%", which is a loading bar's word.
3. **The sockets are web tiles.** Gray 2 px squares. The empties are translucent dark boxes that read as missing art. The glyphs are white silhouettes in a gray smudge halo (the "AI" look). The rank is a row of 1 px dots.
4. **Four icon styles at once.** The draught is a glossy clip-art flask, the form a cartoon starburst with a sticker badge, the skills smudged silhouettes and the passives tiny colored emoji.
5. **The lock is an emoji.** It is a flat padlock symbol with a number, not a lock.
6. **The labels float.** The keycaps are text on dark pills hanging in the air under each round: four more loose pieces.
7. **Nothing touches.** The sockets hover 26 px above the chain, the rounds hover beside the cuffs and the keys hover below. Perception groups what is *connected* before what is merely near or alike (Palmer and Rock 1994, uniform connectedness; Palmer 1992, common region). Only the chain-to-cuff join is connected, so only that reads as one thing.
8. **Around it.** The minimap's parchment is the brightest large shape on a night frame and out-shouts both her and the instrument. Its header lines and steps are about 13 px type, under the 18 px body-height floor for text read on a PC at 1080 (Xbox Accessibility Guideline 101; it is 26 px on a TV). The boss bar is a flat 16 px gray slider with plastic end caps, and nothing on it says the lamps protect him: the fill just turns gray. The teaching cards wear the vine and gilt frames the owner called "lame borders". The level card uses sci-fi corner brackets. The callout's HUD ring is a fat white stroke.

**What the best do: what to take, and what never to copy**
- **Diablo IV.** Take the bracket: life on the left with the potion beside it, the skills between, all on one baseline in one housing; the orb as living liquid with depth in glass; icons toned down so nothing shouts. Never copy the sculpted angels and demons (ornament for its own sake).
- **Path of Exile 2.** Take the globes' material honesty (thick glass, a surface on the liquid, light passing through), and a flask's charge read as a liquid level. Never copy the gothic filigree frames: they are the borders the owner hates.
- **Grim Dawn.** Take the utilitarian forged iron and rivets that look made by a smith. Never copy two rows of small slots on a long plate.
- **Last Epoch.** Take the compactness and clarity, and the potion's charges beside it. Never copy the generic flat plate with no story.
- **Hades.** Take the few bold shapes, the confident type, and choice cards as the screen's one ornament with everything else quiet. Never copy its comic ink: we are painterly realism.
- **Darkest Dungeon.** Take one diegetic object carrying the core variable (its torch is our chain and its heat), and heavy blacks. Never copy the console that eats the bottom third of the screen.

## 2. The language (every element below follows it)

- **One material, one light, one shadow.** Hand-forged iron, the chain's own material: blue-black scale, hammer facets, edges worn to steel where they would rub, rust only deep in the recesses. Lit by the house light from the upper left. Each piece casts a soft shadow on the world, down and to the right (3 to 5 px, 55% black). No filigree, gems, skulls or textured borders. Values at 1080: the iron's body at 8 to 15% luminance, its worn rims at 55 to 70%.
- **Made, never generated.** Every iron piece is modeled and rendered in Blender in the chain's pipeline, and no two neighbors share a variant. Everything alive (liquid, heat, frost, flame) is a shader. Everything read is type set by the code.
- **Joined.** Every piece is fixed to another (riveted, hung or threaded), so the eye sees three bodies riding one chain: life cuff with the draught, the six seats on their sill, and the dash with the art cuff.
- **Heat means ember.** Ember orange and white-heat are spent only on the ember: the chain, the lock, a seat ready to evolve, the art (the ember's great blow), and her mark on the map. Danger is red (#e0282c), cold wards are ice blue (#7fc8ff), and the HUD's own pointing is bone (#ece2cf).
- **The squint test.** Squint at the frame: the instrument should be one dark, low bar with a red jewel on the left, a gold jewel on the right, an ember thread between them, and nothing else bright.
- **Motion only for change and alarm.** At rest only the liquids breathe (a swell under 2 px). Peripheral vision catches motion and brightness, not detail. So while her eyes are on her, a level, a heartbeat or a flare is how the HUD speaks; numbers are for when the eye comes down.
- **Type.** Cinzel 700 for names and for the two numerals that are objects (the lock and the clock). Alegreya for sentences. Alegreya Sans 700/800 with tabular figures for numbers and labels. Anything *read* (not glanced at) is at least 16 px, which is about 18 px of body height. On the world, type gets a 1.5 px outline at 55% and a soft shadow, for a contrast of at least 4.5:1 (XAG 102).

## 3. The instrument

**Geometry at 1080: the lead's layout with five deltas.** The cuffs stay as they are: glass r 60, band 60 to 73, centers ±352 from the middle, 30 px clear of the foot.
1. The six seats: 58 px with a gap of 6 (was 8), a row of 378 px at x 771 to 1149, y 928 to 986, standing on their **sill** (y 986 to 991).
2. The draught's glass centered at x 720, y 957, joined to the life cuff by a forged **lug** (10 px of iron, two rivets). It sits 22 px clear of the seats. The dash mirrors it at x 1200.
3. The chain leaves each cuff from a **riveted joint** at 32° below level, not from an open eye. Two ears stand 8 px out, with a domed rivet through them and through the first link.
4. The keys are on **iron tags** hanging at 6 o'clock: R under the draught (y 989 to 1005, 7 px clear of the chain), SPACE under the dash, and Q under the art cuff (y 1053 to 1069). The life cuff has none.
5. The art glass loses its "%".

**The cuffs (life on the left, the art on the right, mirrored).** A heavy manacle seen end-on. The band's face is half-round, so the light lays a crescent of worn steel along its upper left and a dark crescent along its lower right. Its inner edge is chamfered and in shade, so the glass sits sunk 3 px inside. The hinge is outside at 9 o'clock: three knuckles and a peened pin, 12 by 26, standing 9 px out. The joint is inside, at 32° below level: the chain's end is captured between two ears by a big domed rivet. That is how a smith shut a slave's irons, with no key; the only lock on her is the chain's. The lug to the small round is at 3 o'clock, and there are hammer facets round the band, a few of them deep.
- **Made as:** rendered `hud/cuff.png` (the back ear, band, hinge and lug), `hud/cuff_front.png` (the front ear and rivet, drawn over the first link), and `hud/cuff_glow.png` (the inner chamfer lit warm by the glass, added by the shader's glow or heartbeat).

**Her life (the left glass).** Blood in thick old glass, lit as a real sphere.
- **The liquid:** near-black crimson in its depth (#1e0205), #8c0d14 near the surface, with slow dark veins turning in it at low contrast. Light enters at the upper left and leaves at the lower right as a rim of #e0302a: the brightest red on the HUD.
- **The surface:** seen from slightly above, a thin ellipse (8% of its chord in height) lighter than the body, its far edge a 1 px meniscus (#ff7a66 at 70%). It swells under 1.5 px at rest and sloshes on a change, settling in 0.8 s.
- **The glass:** the cuff's soft shadow on its upper-left rim (6 px); a refraction ring at the rim (3 px darker, its lower-right inner edge a 1 px bright line); one soft reflection of an arched window at the upper left, at 30% at most and curved to the sphere; one 3 px hot spot. No gloss blob, no window-pane cross.
- **States:**
  - **Full:** no surface showing; liquid to the rim.
  - **Hurt:** the level drops, and above it the glass keeps a film of blood that runs down and clears in 0.6 s. This replaces today's pale trail band.
  - **Low (30% or less):** a heartbeat. The liquid brightens and the cuff's chamfer flushes red on each beat, every 1.1 s (0.75 s under 15%), and the number turns #ff6a5a.
  - **Healing:** lighter, fresh blood swirls up from the foot.
  - **Shielded:** frost (#9ad4ff) rimes the glass from the top, as far round as the shield holds, and cracks away once (0.3 s) when the shield breaks.
  - **Empty:** dark glass with a dried film.
- **The number:** Alegreya Sans 800, 22 px, tabular, bone #f2e8d6, a soft shadow (0, 2, 4 px at 70%) and no stroke. Its center sits 58% of the way down the glass, on the liquid's mass and out of the reflection.
- **Made as:** `hud_vessel.gdshader` v2 in blood mode, with the rendered `hud/glass.png` (the reflections and rim only) screen-blended over it.

**The art in hand (the right glass).** Molten gold in the same glass.
- **Charging:** dull orange (#7a3a0c), with dark skins of slag on the surface, brightening as it rises.
- **Full:** white-gold at the meniscus (#fff0c0), the body #ffb440, its surface boiling slowly, and the cuff's chamfer lit warm (`cuff_glow`). It is the brightest thing on the HUD, on purpose. A word above the cuff, READY (Alegreya Sans 800, caps, 14 px, tracking 120, #ffd07a), shows only when full.
- **The glyph:** the art's glyph is *etched in the glass*: frosted lines 46 px across, faint and pale on empty glass and lit from behind as the gold rises past them.
- **Cast:** the gold drains in 0.25 s and sparks leave the top once.
- **No percent:** the level is the reading. Seconds (Alegreya Sans 700, 18 px) show only when the art charges by time.
- **Made as:** the same shader in gold mode, with the glyph as a texture input.

**The draught.** The same glass, small (r 23), full of the draught's red, a shade warmer than her blood. Its count sits in the glass's lower right (Alegreya Sans 800, 16 px, tabular). While it refills, its level rises; with none left, the glass is dark and the count dim. There is no flask icon: the glass is the flask. Its R tag hangs below.
- **Made as:** `hud/cuff_small.png`, `hud/glass_small.png`, and the shader in draught mode.

**The dash and the form.** The small glass is clear and dark, with the dash's chevrons etched in it. Its two charges are two arcs (150° each) lit bone-white in grooves cut in its band. A spent arc is dark and lights again from its start as it refills.
- **The form** (the next dash is special) lives *inside* the glass, so it can never be taken for a callout ring. The calling's fire fills the glass from below in the calling's hue (Bull Rush is deep orange), and four licks rise 8 px over the band's top. The calling's badge is a 20 px iron medallion riveted to the band at half past one, its sigil inlaid. Its SPACE tag hangs below.
- **Made as:** the shader in dash mode, `hud_flame.gdshader` for the licks, and a rendered `hud/badge_<calling>.png`.

**The six seats.** Each is a hand-forged square collar with a 4 px face. Its outer edges catch the light at the upper left. Its inner walls are lit on the lower right and shaded on the upper left, so the floor (a dark iron plate, #0c0b0e) reads 4 px down. There are six variants, and no two neighbors are alike.
- **The sill:** the seats are riveted to one strap of the same iron, 5 px tall, running under the row, 6 px past each end, with a rivet under each gap. This makes the row one object. By day it is as long as what she carries, centered.
- **The glyph:** an **enamel inlay**, 38 px. The glyph's line is cut into the floor and filled with its school's color, glassy, with a small highlight on each stroke.
- **The rank:** eight dimples punched along the lower bar; the reached ones hold a coal-red glow (#ff8a3a at 85%).
- **States:**
  - **Filled:** as above.
  - **New:** one ember flare that cools in 1.5 s.
  - **Can evolve:** the whole collar goes hot like the chain's leading links, with a slow heat breath.
  - **Empty (night only):** the collar unlit (rims at 35%), the floor at 60%, no glyph and dark dimples.
  - **No flash when it fires:** six weapons firing would blink at the edge of vision all night.
- **Made as:** `hud/seat_K.png`, `seat_empty_K.png` and `seat_hot_K.png` (K < 6), `hud/sill_N.png` (N from 1 to 6), `inlay/<glyph>.png` from `blender_relief.py`, and the heat breath in `hud_heat.gdshader`.

**The chain.** Kept: it is the bar. Its ends now run into the cuffs' riveted joints, with the first link captured so the heat reaches the cuff. Check its heat ramp at 0.8 scale at 1:1: the reached links deep red, the leading three hot, a flare when full. Steel by day.

**The lock.** A real smith's padlock: a round-shouldered iron body, 34 by 42 (was 30 by 38), its heavy shackle truly through the chain's middle link (a back layer and a front layer). It has a plain face stamped with the level (Cinzel 700, 19 px, bone, going ember-white when hot), and a keyhole below the number.
- **States:** closed and cold; hot (the body glows as the chain nears full, `lock_hot` faded in); sprung (the shackle's left leg swings out and the number flips, over 0.8 s, then it closes again).
- **Made as:** `hud/lock.png`, `lock_open.png`, `lock_hot.png` and `lock_link_front.png`.

**The key tags.** A small stamped iron tag hanging from a ring in the band, 16 px tall. Widths are 24 (one character), 32, 40 and 52 (SPACE, SHIFT). The key is set in Alegreya Sans 800 caps at 14 px (SPACE with tracking 60), in bone, with a 1 px dark inner edge so it reads as filled into the stamp. On a pad, the button's glyph sits in the same tag. A rebinding redraws the tag; nothing else does.
- **Made as:** `hud/tag_24.png` to `tag_52.png` and `hud/tag_ring.png`. The same tags serve as the key chips in text (section 4.4).

**Over the instrument.** The passives sit in one centered row 10 px above the seats: line glyphs of 20 px in bone at 75%, each with a rank numeral. The statuses sit over the life cuff at the same size, in their school's color, each with a thin timer arc. Nothing colored above the instrument is larger than 20 px.

**The states at a glance**

| | Ready or full | Charging or cooling | Empty | Alarm or hot |
|---|---|---|---|---|
| Life | blood to the rim | healing: fresh blood swirls up | dark glass, dried film | 30% or less: heartbeat, the number red |
| Art | white-gold boiling, glyph lit, chamfer lit, READY | crusted gold rising | dark, glyph faint | — |
| Draught | full glass and its count | level rising to the next | dark, count dim | — |
| Dash | both arcs lit | an arc lighting from its start | arcs and glass dark | the form: calling's fire, licks, badge |
| Seat | inlay and dimples lit | — | night: unlit collar | can evolve: collar hot, breathing |
| Chain and lock | — | heat creeping link by link, lock warming | cold (steel by day) | full: flare, the lock springs |

## 4. Around it

**4.1 The minimap and its header (upper right).**
- **The disc:** r 100, as now.
- **The bezel:** the cuffs' iron (r 100 to 109), plain, with no hinge. North is a forged pin at 12 o'clock, in bone, not ember. The day's path is an engraved arc over the bezel's top, with a 10 px brass sun (day) or pale moon (night) riding it.
- **The parchment:** it takes the scene's light. At night it is graded to 40% value and cooled; today it is the brightest thing on a night frame. By day it is at full value.
- **Marks:** her mark is the one ember arrow. The steps use the house's diamond as forged studs: iron, ember-hot when active, dim when done.
- **The header:** right-aligned to the disc, at most 380 px wide.
  - The place: Cinzel 700, 26 px, tracking 60, #e2c78f.
  - The time line: Alegreya Sans 700 caps, 15 px, tracking 80, bone at 70% (NIGHT 1 · THORNHOLLOW, SOUTH).
  - Then 10 px of air.
  - The quest: Alegreya Sans 800 caps, 15 px, tracking 60, #c9a86a.
  - Its steps: Alegreya 400, 18 px, bone at 90%; done steps at 50% and struck through.
- **Made as:** `minimap/bezel.png`, `pin.png`, `sun.png`, `moon.png`, `stud.png` and `stud_hot.png`.

**4.2 The boss bar (top center).**
- **The name:** Cinzel 700, 28 px, tracking 60, in bone (not orange).
- **The bar:** a groove forged in a flat iron bar, 850 by 18, with iron clamps at its ends. The fill is the life glass's blood seen from the side: the same shader in bar mode, with depth, a lit top edge, a slow drift and the hurt film draining.
- **Phase marks:** V-notches cut in the groove's lip.
- **The stagger:** a 4 px line along the groove's foot, filling white-gold (#f3d9a0, rising to #fff8e0 at Break).
- **The lamps:** three small lamps (the house's lamp, made cold) hang under the bar's middle.
  - While a lamp burns: an ice-blue flame, a frost film over the fill (the same frost as her shield), and the fill desaturated. It says: he is warded.
  - When one is put out: its lamp goes dark with a wisp of smoke, and the film thins.
  - When all are out: the film shatters once and the blood is red again.
- **The title:** under the lamps, Alegreya italic, 18 px, bone at 70%.
- **The cast bar (a channel):** under the title, a forged groove 420 by 12 filling white-hot from the left. It is the hottest thing at the top of the screen and pulses past 70%. The spell's name sits over it (Alegreya Sans 800 caps, 15 px, tracking 80, #ffd07a). At its left is the tag of what breaks it (SPACE) and the words "to break".
- **Needs:** `BossBar` must carry the lamps (how many of N are lit).
- **Made as:** `hud/boss_bar.png` (one render, 850 wide), `boss_notch.png`, `boss_cast.png`, `lamp_s_lit.png` and `lamp_s_out.png`; the shader in bar mode.

**4.3 The tally (lower right, level with the instrument's foot).**
- The night's word: Alegreya Sans 700 caps, 14 px, tracking 120, bone at 60%.
- The clock: Cinzel 700, 32 px, bone at 90%, each digit in a fixed cell so it never jitters.
- Slain and gold: Alegreya Sans 700, 18 px, tabular, each after a 16 px rendered mark (an iron tally stud, a struck coin).
- **Made as:** `hud/slain.png` and `hud/coin.png`.

**4.4 Teaching and prompts.** Experience decides when and what; this section is how they look. They share one language: bone points at the HUD, ember at the world and ice blue at cold things. Marks are rings and lines, never frames. Words stand on the world with no box, with the title's hot wire under it (kept).
- **Callout (a freeze).** The world dims 30%, her pool of light stays and the HUD stays whole.
  - **Ring:** 2.5 px, in bone (HUD), ember (world) or ice blue (the lamps), with a soft 8 px glow at 25%, breathing between 70 and 100% over 1.6 s (in a shader). Areas get the same as a rounded square (6 px corners), 6 px off a slot and 12 px off a banner. This replaces the orange corner brackets.
  - **Arrow:** a tapered stroke from 3 to 1.5 px with a dark 1 px edge, so it reads on a light ground, ending in an open 10 px chevron that lands on the ring.
  - **Words:** the title in Cinzel 700, 26 px, with the wire; the lines in Alegreya, 20 px; the footer "[E] to go on" in Alegreya italic, 17 px, with its key tag. The dim and the footer's verb say "paused", and the whole HUD says nothing is lost.
- **Off-screen marker.** A 30 px disc of smoked glass with an ice-blue 2 px rim and the thing's line glyph, with a chevron on its outer side pointing off the screen. It is pinned 40 px in from the edge and breathes like the ring.
- **Key chips.** The HUD's iron tags inline, 22 px tall in text, sitting on the baseline, in the same widths.
- **Tip line.** A title (Cinzel 700, 22 px) and one sentence (Alegreya, 20 px) on the world, with the key tags inline.
- **Cards (the skill draft and the great blessing).** Retire `frames/card_*.png`.
  - **One object for the screen:** the chain runs across above the cards, and each card hangs from it on a ring (`cards/ring.png`).
  - **The cards:** tonal, #141218 at 94%, with a 1 px lighter top edge and a darker foot: a pressed plate with no border. 300 by 420 for a skill, 340 by 460 for a blessing.
  - **In each card:** the glyph inlaid in a seat at 1.5 times its size (square, because it fires by itself); the name in Cinzel 700, 24 px; the kind in its school's color (Alegreya Sans 800 caps, 14 px); the one line in Alegreya, 19 px; the rarity as a 3 px line at the card's top and its word at the foot; and its key (1 to N) on a tag hanging from the foot.
  - **Focus:** the card lifts 6 px and its ring and link go hot. The others stay still.
- **Level card at dawn.** No brackets. The lock, large (68 by 84) and sprung, beside LEVEL 5 (Cinzel 700, 44 px). Over it, WHAT THE NIGHT TAUGHT YOU (Alegreya Sans 800 caps, 14 px); the lines under it, with the C tag inline.
- **Interaction prompt.** Over the person: the E tag, then "Talk" (Alegreya Sans 800, 17 px, bone), then "Chid" (Cinzel 700, 18 px, gold), outlined on the world.
- **On the ground (VFX, made by their owners in this color language).** The ember halo uses the chain's heat ramp (it says: pick me up). The red line is a crisp #e0282c edge with hatching at 35%, never orange, with the callout's ember ring drawn 12 px outside it.

## 5. Production

**The pipeline.**
- **A new script:** `tools/uiforge/blender_irons.py` with its spec `irons.json`. It builds on `blender_frames` (the house light `suns()`, `world()`, `camera()`, `rivet()`) and on `blender_chainline` and `blender_links` (`iron_chain_material`, `heated_material`, `mark_wear`).
- **The render:** one scene, with shadows caught on a transparent catcher. Rendered at twice the shown size, 3x supersampled, at 64 samples or more. Cold and hot variants come from the same geometry, as the links do.
- **Surface detail:** hammer facets from seeded displacement and wear from curvature. No image textures and no image generators.
- **The inlays:** rendered by `blender_relief.py` from the glyph vectors.
- **Into the game:** with `kit.py` and `imports.py` (art and margins go in together), imported with mipmaps so the hammered highlights do not sparkle at 1080.

**The files** (under `art/ui/`, at twice the shown size)

| File | Shown px | What it is |
|---|---|---|
| `hud/cuff.png`, `cuff_front.png`, `cuff_glow.png` | 174 square | band, hinge, lug, joint's back ear / front ear and rivet / chamfer glow |
| `hud/glass.png`, `glass_small.png` | 132, 50 square | the glass's light only: reflection, rim, hot spot |
| `hud/cuff_small.png` | 70 square | small band, lug rivet, tag ring, charge grooves |
| `hud/seat_K`, `seat_empty_K`, `seat_hot_K` (K < 6) + `seat.json` | 68 square | collar with its shadow; the dimples' centers |
| `hud/sill_N.png` (N 1 to 6) | 64N + 6 by 10 | the strap under the seats |
| `hud/tag_24`, `tag_32`, `tag_40`, `tag_52`, `tag_ring` | width by 16 | stamped iron tags |
| `hud/lock`, `lock_open`, `lock_hot`, `lock_link_front`; `lock_big_open` (4x) | 34 by 42 (plus shackle) | the padlock; the dawn card's |
| `hud/badge_<calling>.png` | 24 square | form medallion |
| `inlay/<glyph>.png` | 38 square (57 for cards) | enamel-inlaid glyph |
| `minimap/bezel`, `pin`, `sun`, `moon`, `stud`, `stud_hot` | 226 square; 10 to 16 | map iron and marks |
| `hud/boss_bar`, `boss_notch`, `boss_cast`, `lamp_s_lit`, `lamp_s_out` | 870 by 30; 440 by 20; 22 by 32 | boss iron, the lamps |
| `hud/slain.png`, `coin.png`; `cards/ring.png` | 16; 20 | tally marks; a card's ring |

**Shaders.** `hud_vessel.gdshader` v2 has five modes (blood, gold, draught, dash, bar) and adds the surface ellipse, veins, film, frost, heartbeat, etched glyph and boil. Three are new: `hud_heat.gdshader` (heat breath for the seats, lock and chain flare), `hud_ring.gdshader` (callout rings and squares) and `hud_flame.gdshader` (the form).

**Code (su-worker; `Instrument.cs`, `GameHud.cs`, `Minimap.cs`, `Callout.cs`, `Panels.cs`).**
- The five geometry deltas.
- Nodes for the sill, tags and joint.
- Inlay icons in the seats.
- The lamps on `BossBar`.
- Cards without frames.
- Static TextureRects, redrawn only on a change; levels as shader uniforms; no node churn per frame; the HUD under 1 ms, measured with the perf windows.

**Order.** Each step closes on 1:1 game frames at 1080 and 1440, night and day, judged at max effort before the next begins.
1. The first piece (section 6), then the owner.
2. The right half (gold, dash, form; it mirrors the kit), all the seat variants, and the inlays.
3. The top: the boss bar, lamps and cast bar; the minimap and header; the tally.
4. The teaching language: rings, arrows, markers, chips, cards, the level card and the prompt.

## 6. The first piece: the left half of the instrument, finished, in the game

**What.** The life cuff with her blood glass. The draught joined to it, with its R tag. Three seats on their sill: one filled at rank 3 of 8, one hot (it can evolve) and one empty. The chain from the cuff's joint to the lock at the middle, with the ember at 60%; in one shot the lock is hot, near full.

**Why this piece.** Life is the keystone and the most-watched thing on the screen. This slice holds every material (iron, glass, blood, heat, type and tag) and every kind of join that makes one object. The right half is its mirror, so approving this approves the instrument's language before the rest is spent.

**Made.**
- Blender: `cuff`, `cuff_front`, `glass`, `cuff_small`, `glass_small`, `tag_24`, `seat_0` to `seat_2` with their empty and hot variants, `sill_3` and `sill_6`, and the four lock files.
- Shader v2: blood and draught modes.
- Code: the joint, lug, sill, tag and gap deltas.

**Shown.** In-game shots from the existing harness, at 1080 and 1440, on o1a_08 (a night fight) and o1a_36 (day):
- life at 100, at 55 (with the film still draining) and at 18 (on the beat);
- life at 55 with a shield;
- for each, a 1:1 crop of the left half to the lock beside today's same crop (A|B), plus each whole frame.

**Acceptance (for the max judge; any one failure stops the piece).**
1. Whole frame first: the instrument reads as one made object lying on the world, and its iron is the chain's iron (a link and the cuff side by side at 1:1).
2. The glass reads as liquid in thick glass: a surface with its meniscus, depth, light coming through at the lower right, the cuff's shadow on its rim. No blob, no sticker.
3. 100, 55 and 18% are told apart at a glance at 1080. Low life is unmistakable from the corner of the eye without being garish. The hurt film reads as blood running down glass.
4. No stroke reads as a border. Edges are crisp at 1:1 at 1080 and at 1440: no fringe, halo, blur, sparkle or stretched texture. Every shadow falls down and to the right.
5. The number is crisp, with 4.5:1 contrast or better on both full and empty glass.
6. The draught visibly hangs off the cuff (the lug reads), and its count and its R tag read at 1:1. The tag reads as stamped iron.
7. Filled, hot and empty seats are told apart in under a second, and the empty one is quiet. The inlay reads as inlaid, not flat, and the rank can be counted as 3 of 8.
8. The lock is a forged padlock hanging through a real link, not an icon, and its numeral is crisp.
9. No two neighboring links, seats or rivets are identical.
10. In the day frame, nothing is muddy or haloed on the warm ground.
11. The instrument's CPU time is under 1 ms, and nothing but the shaders redraws each frame.
12. The gate: would this ship in Diablo IV's HUD as it stands? Anything visibly below that at 1:1 fails.

**Ask the owner,** showing the A|B crops at 1:1: "Is this the soul and the make for the whole HUD: her life in a forged manacle riveted to the chain, the keys stamped on iron tags? What is off?" Ask nothing else until it passes.

## 7. Decisions for UI 11
- Approve the five geometry deltas in section 3. They are small, and the layout stays.
- `BossBar` needs the lamps (how many of N are lit) from the encounter code; today only `Shielded` says so.
- Enamel inlays replace the color glyphs for every skill: one relief batch.
- The cards hang from the chain, and `frames/card_*.png` is retired.
- The Blender kit is taste work, for the lead or a max solver. The code deltas go to su-worker.

Sources: [XAG 101, text display](https://devdocs.xbox.com/build/game-principles/accessibility/xag-deep-dives/xag-101-text-display.md) (minimum body height 18 px on a PC at 1080, 26 px on a console); XAG 102, contrast (4.5:1 for text); S. Palmer, "Common region" (Cognitive Psychology, 1992); S. Palmer and I. Rock, "Rethinking perceptual organization: the role of uniform connectedness" (Psychonomic Bulletin and Review, 1994); the HUDs themselves, studied at 1:1 in play and screenshots (Diablo IV, Path of Exile 2, Grim Dawn, Last Epoch, Hades, Darkest Dungeon).
