# UI design: every element, and why it is the best answer

The interface of Survivor Unchained, element by element. For each: the job
it does, what it was (the audit), the alternatives weighed, the design
chosen and **why it is the best answer**, and how far the code has got
(**Done** is in the game now; **Next** is designed and not yet built).
The reasons rest on `UI_RESEARCH.md` (rules R1-R10 in its section 8); the
art for all of it is specified in `UI_ART_BRIEF.md`.

The method, at the owner's direction: start each element from "what is the
best possible design for this job?", not "how do I improve what is here?".
Where the answer was a rebuild, it was rebuilt (the pack, the shop, the
storeroom, the map, the self, the journal's people, parts of the HUD).

**The second pass.** The owner saw the first pass's windows and said they were
"the literal exact same shapes": a huge empty parchment square with the zone
small at its edge, a big dark box with small items, a wall of text in a box,
and nowhere any material, depth or framing that said "this is Survivor
Unchained". "I don't want to polish, I want to create perfection." So every
major screen was recomposed from its job: two or three concepts each, drawn
from the real game's parts and painted with the local model, the best chosen
with its reasons (section 11). Two things came out of it for every screen:
**the page system** (the day's book and the stores take the whole screen) and
**the frame language** (forged iron, drawn in code by `Ornate.cs` until the
painted art replaces it piece by piece). Sections 4 to 7 describe the screens
as they are now; section 11 records the concepts and the choices.

The game is two halves, and so is its interface:

- **The night** (the prologue's road, the ember arenas): a survivors-like.
  Sparse, glanced at, colour-coded, nothing in the middle but the fight.
- **The day** (the Waystation, the Verge): an ARPG. Browsable, read,
  detailed, a book of five pages.

Both share one frame language (iron, a gold hairline, ember light,
parchment for what is written) and one way of being driven: mouse and
keyboard and pad are equals (R5).

Contents: 1 style guide · 2 navigation · 3 the audit · 4 the HUD · 5 the
draft · 6 the day's book · 7 other screens · 8 accessibility · 9 input from
the feel and items work · 10 what is next · 11 the second pass: concepts and
choices.

---

## 1. Style guide

### 1.1 Palette tokens (`godot/src/Ui/Style.cs`)
Colour is a language (R3): each hue means one thing, and every meaning also
has a word, a mark or a shape, so no-one depends on hue alone.

| Token | Hex | Means |
|---|---|---|
| `Iron0`-`Iron3` | #0b0a0d #15131a #1e1b24 #2a2631 | Plates, wells, slots: the night-iron the interface is forged from |
| `Gold` `GoldHi` `GoldDim` | #d9b56a #f3d9a0 #8a6f3e | The interface itself and what is *yours* |
| `Line` `LineHi` | gold at 35% / 70% | Hairlines, frame edges, dividers |
| `Ember` `EmberHi` | #ff8a3a #ffd07a | The night's power: the ember bar, "fits your build", NEW, the primary action |
| `Focus` | #ffc46a | What has focus (the ring); used for nothing else |
| `Blood` `BloodHi` | #c8323a #ff5a5a | Health, danger, the enemy |
| `Day` `DayHi` | #86b0d8 #d8ecff | The day's growth: experience, the survivor's own level |
| `Shield` | #9ad4ff | Barriers, good statuses |
| `Ink` `InkDim` `InkFaint` | #e8dcc4 #a89c88 #6f6556 | Text on iron: body, secondary, decoration only |
| `Parchment` `ParchmentInk` | #e8dcc0 #2a2118 | Paper and its ink |
| `Good` `Bad` | #8ae05a #ff7a6a | Better and worse, always with a sign and the word |
| Rarity 0-5 | #c8c0b0 #6fd46a #5aa8ff #c070ff #ffb040 #ff6a3a | With its name and 1-6 drawn diamonds (`Style.Gems`) |
| Schools | physical #e8dcc4, fire #ff8a4a, frost #8fd0ff, storm #9ab8ff, nature #8ae05a, arcane #cc88ff, holy #ffd46a, shadow #a87aff | A skill's school |
| Pad face buttons | A #6bc45a, B #ec5a50, X #4a9cf0, Y #f2c440 | Always with the letter |

Contrast: body text (`Ink` on `Iron1`) about 13:1; secondary (`InkDim`) about
6.5:1; `InkFaint` (3.4:1) only for decoration and disabled things;
parchment ink on paper about 12:1.

### 1.2 Type
Cinzel for names carved in stone (headings, places, the things themselves),
Alegreya for what is read (descriptions, speech, the journal), Alegreya
Sans for the interface's own words (labels, numbers, keys). SIL OFL, in
`godot/art/fonts`.

| Token | px at 1080p | Use |
|---|---|---|
| `Hero` | 54 | Fade captions, an arena's name at its end |
| `Heading` | 32 | A screen's subject |
| `Title` | 24 | Card titles, section heads on paper |
| `Lead` | 20 | Kickers, the draft's tip |
| `Body` | 18 | All prose (speech is 23) |
| `Small` | 16 | Labels beside values, buttons |
| `Caption` | 15 | Secondary lines, footers, tags: the floor for anything that must be read |
| `Badge` | 13 | Numerals on badges only |

**Why**: XAG 101 asks 18 px at 1080p for PC text; the old interface set much
secondary text at 12-14. The faces lack ★ ▲ ◆ ◦ ✓ ← →, which fell back to a
system font or a box: marks are now drawn (`Style.Gems`, the D-pad cross),
never typed. All caps only for one- or two-word labels.

### 1.3 Spacing, frames, icons, motion, sound
- **Spacing**: steps of 4 (`Gap1`-`Gap6`: 4 8 12 16 24 32). 36 px from the
  screen's edges. Prose lines under about 80 characters.
- **Frames: the house's language** (`Ornate.cs`; the painted art's soul is
  in `UI_ART_BRIEF.md` 2.6). Every surface says what kind of thing it holds
  by its material and shape:
  - **plates** (forged iron, lit at the top and dark at the foot, a bevel, an
    inset gold hairline, bracketed corners each with a cut stone, a soft
    shadow) for a pane of a page or a window;
  - **wells** (the same iron sunk in, lit along the foot) for grids and lists;
  - **slabs** (raised, a dull hairline, no brackets) for groups inside a plate;
  - **crested cards** (the rarity or school in a crest band and the corners,
    a stone at the head) for choices: the draft, the arts' facets, creation;
  - **paper** for what is written, **the open book** for the journal;
  - **banners** (oxblood iron) for verdicts and names;
  - **medallions** for anything round: a level, an attribute, an art, a
    socket, a step, a number, the pause menu's book;
  - **the title plaque** (Cinzel between gold rules ending in ember stones)
    for every page's name, and **sections** (small gold capitals, a stone, a
    rule running on) inside panes.
  Ornament on edges and corners, never under text. **Why**: the owner's "no
  material hierarchy, depth or framing"; Diablo IV, Grim Dawn and PoE2 read as
  themselves through their frame material before anything else, and drawing
  the language in code made the game say "Survivor Unchained" before any art
  landed.
- **Pages and panels**: reading and planning screens are full pages, and
  what is tweaked mid-play is a side panel (`Overlay.SidePanel`) with the
  world in view (section 6, "Page or panel"). A full page (`Overlay.Page`): the world darkens behind
  (`Backdrop`, an ember glow at the foot), a header band runs across the top
  (the book's tabs at its left, the title plaque in the middle, Close at the
  right), and the screen hands back a 1840 × 920 content area at (40, 112)
  that it fills with framed panes (`Overlay.Pane`). The HUD steps away while
  a page is open. **Why**: these are reading and comparing screens; every
  best ARPG (D4, PoE2, Last Epoch) gives them the screen, and a window inside
  a dark rectangle left most of the screen empty.
- **Icons**: line glyphs for the abstract (a 24-unit square, a 1.6 stroke,
  `data/content/glyphs.json`), photographs of the models for items; painted
  art replaces either by name (`UI_ART_BRIEF.md` §5). Readable at 18 px.
- **Motion**: every press answers within a frame (R6); entrances 0.2-0.5 s
  ease-out; what matters breathes at 0.6-1.2 Hz; nothing strobes; rewards
  count up.
- **Sound** (`Sfx.cs`): hover tick, press, refusal (`Deny` on every refusal),
  page turn (`Page`: the book's tabs, sections, filters, sorting), card taken
  (`Pick`), gear worn (`Equip`), screen open and close.

### 1.4 Art plug-in points (`godot/src/Ui/UiArt.cs`)
Every frame, bar, slot, card, medallion, ornament, cursor and icon asks for
painted art by name under `godot/art/ui/` and keeps the drawn look when there
is none. Made at twice the size shown; frames nine-sliced, their content kept
clear of the painted border. **Why**: art can arrive one piece at a time
with the game whole at every step, and the artist never touches code.
The art pass delivered 282 pieces (plates, buttons, slots, the draft's cards,
tooltips, bars and casings, the minimap's rim, the art's ring, the logo, 211
icons); the redesign's own pieces (well, slab, header, banner, the Self
pillars, the HUD console, the open book, the medallion ring, the globe's rim
and glass) are registered by name and wait for their paint
(`UI_ART_BRIEF.md` 4.9). Where painted and drawn meet, the painted piece wears
the drawn one's job: a painted card keeps the crested card's medallion and
lifted glow, a painted plate keeps the drawn plate's content margins.

---

## 2. Navigation: one input model for three devices

**The job**: every screen fully playable with a mouse, a keyboard alone, or
a pad alone, and moving between them mid-screen without friction.

**The audit**: in a menu, a pad's A was a dash, B a word with someone, X and
Y the art and the draught, so the title and pause menus, rerolls, banishes
and dialogue choices could not be driven by a pad at all. No focus on any
screen but two lists. Prompts always showed keyboard keys.

### 2.1 The button map
| | Keyboard and mouse | Pad |
|---|---|---|
| Move | WASD / arrows | Left stick |
| Dash | Space / Shift | A |
| Art in hand | Q / right mouse | X |
| Draught | R | Y |
| Talk, use | E / F | B |
| The book (opens at the Pack) | I / Tab | View |
| Self, Arts, Journal, Map | C, K, J, M | View, then RB |
| Pause | Esc / P | Menu |
| **In menus** | | |
| Move focus | arrows (held: repeats) or the mouse | D-pad or left stick (held: repeats) |
| Choose | Enter, click | A |
| Back, close | Escape, Backspace | B |
| The focused thing's second and third actions | Delete; buttons on screen | X, Y |
| The book's pages | [ and ] | LB, RB |
| A screen's own pages, filters, zoom | , and . | LT, RT |
| Draft: take a card | 1-4, click | D-pad and A |
| Draft: reroll, banish | X, B | X, Y |

**Done.** In a menu a pad button means its menu meaning first. A held
direction repeats after 0.36 s every 0.11 s (deliberate, after PoE2's "too
fast"). The stick moves focus like the D-pad; the triggers turn sub-pages.

**Why this map**: it is the convention players already know (Jakob's law;
D2R, Diablo IV, PoE2 on pad): A confirms, B backs out, bumpers turn top
tabs, triggers turn sub-tabs, X and Y act on the focused thing. The
keyboard keeps its single-key shortcuts (Nielsen's flexibility) and gains
the same structure.

### 2.2 Focus (`godot/src/Ui/Nav.cs`)
**Done.** Every visible button takes focus by itself; slots, list lines,
dialogue lines and sliders join with `Nav.Mark` and say what A, X and Y do.
Arrows move to the nearest thing that way (things level with the focus win
over nearer ones off-axis). Focus is kept by name across rebuilds. A
direction pressed while a screen is redrawing waits a frame for its layout.

- **The ring**: ember-gold, 2 px, a soft glow, breathing; shown only while
  keys or a pad are in use (Microsoft's 10-foot guidance: "clear and
  unmistakable").
- **Hand-over**: the pointer moves focus; the first direction pressed shows
  where focus is before moving it; moving the mouse hides the ring.
- **First focus**: each screen names it (the first pack slot, the first
  shelf item, the first spendable attribute). Close buttons are left out of
  the order (B and Escape close everywhere), so focus is never wasted there.

**Why spatial focus rather than a fixed order**: our screens are grids and
columns, not forms; nearest-in-direction matches what the eye expects on a
grid (PoE2, Diablo IV) and needs no per-screen wiring, so every new button
is reachable by pad on the day it is added.

### 2.3 Prompts follow the device
**Done.** The last device touched (a key, a click, a real mouse move, a pad
button or stick) decides every prompt at once: the HUD's hands, the use
prompt, hints (W A S D become the left stick), the draft, the conversation,
footers, the book's tabs, close buttons, and the words in hints that name a
key ("Space: a quick roll" becomes "A: a quick roll"). Pad buttons are drawn
as themselves: face buttons as dark discs with the letter in its colour;
bumpers, triggers, View and Menu as pills; the D-pad as a cross with the
meant arm lit.

**Why**: a prompt for the wrong device is worse than none (it teaches the
wrong thing). D2R switches its whole interface on the first touch; we
switch every prompt the same way.

---

## 3. The audit, in brief

| Element | Verdict before | Why | Became |
|---|---|---|---|
| The look | Keep | Coherent, themed, colour mostly meaningful | Kept; tokens and type scale formalised; art plug-ins |
| HUD layout | Keep, refine | Sound hierarchy; but the fight's clock and kills by day, empty skill slots by day, 5 px rank pips, no minimap, corner words lost on bright ground, the use prompt far from its thing | Refined (section 4) |
| Pad support | Broken | Menu buttons stolen by play; no focus; keyboard prompts only | Rebuilt (section 2) |
| Draft | Good bones | No view of the build; rarity by colour alone; small text | Redesigned (section 5) |
| Conversation | Good | Locked choices shown with reasons; but no pad focus; the thread lost between lines | Refined (7.4) |
| Pack | Wrong shape | Comparison as deltas only; numbers ambiguous; mouse only; no sort, filter or drag | **Rebuilt** (6.1) |
| Self | Adequate | Small text; empty column; experience in the night's colour; numbers with no source | **Rebuilt** (6.2) |
| Arts | Good | Tabs unreachable by pad | Refined (6.3) |
| Journal | Good writing, weak frame | Sections took the book's keys; people a wall of text | Refined; people **rebuilt** (6.4) |
| Map | Lovely, one bug | Unfogged ink at the right edge; small; nothing to tell you where to go; mouse only | **Rebuilt** as an atlas (6.5) |
| Title, creation | Good | Creation's plate half empty; pad could not choose | Refined (7.1, 7.2) |
| Pause, rest | Adequate | Dead space; refusals unexplained | Refined (7.3, 7.7) |
| Shop, storeroom | Wrong shape | Mouse only; price and quantity both bare numbers | **Rebuilt** (7.5, 7.6) |
| Arena's end | Underplayed | The end of half an hour listed, not celebrated | Refined (7.9) |
| Symbols | Bug | Glyphs the fonts lack | Drawn instead |

---

## 4. The HUD

The HUD is non-diegetic and lives at the edges (R1): what can kill you where
the eye already rests, what you choose at the top edge, what fires by itself
on a console at the foot, where you are and what you seek at the top right.

**The console** (second pass; concept `hud_b_console`): in a fight, health,
the skills and the art in hand are one band along the foot: a forged plate
(`console`, 300-720 wide with the skill count) with the skills standing on
it, the health **globe** at its left end and the art's ring at its right, the
draught and the dash beside the ring. At peace (the town by day) there is no
console: the globe keeps to the bottom-left corner and the rest is gone.
**Why**: Diablo IV and Lost Ark put health, skills and the art in one band
where the eye drops from the fight (proximity, Fitts); the first pass's
corners split attention three ways. Weighed against the corners as they were
(`hud_a_corners`) and a minimal ring round the survivor (`hud_c_minimal`, too
little for an ARPG's day).

**Why not move it all round the survivor** (as some survivors-likes do): our
day half is an ARPG with a town and a map; an ARPG's band and corners (Diablo
IV, PoE) are what its players read without thinking. The night borrows only
the one thing that must be at the centre: health under the feet (4.3).

### 4.1 The bar: ember by night, experience by day (top centre)
**Done**: a medallion with the level; the bar; the word under it, **EMBER**
(ember) or **EXPERIENCE** (day blue); a leading edge that brightens as the
level nears; the fill eased every frame (not stepped at 12 Hz), breathing
from 85%, and on a level it fills, flashes white and drains to what carried
over; the kill count pops as it climbs (the feel work's S-06).
**Why**: one place answers "how far to the next" in both halves, so the
player maps it once; the word says which half's growth it is; the goal in
sight (goal-gradient) is the strongest pull in the loop.

### 4.2 The clock and the tally (under the bar)
**Done**: in an arena the clock **counts down** to what rules it ("29:30
BEFORE WHAT RULES IT COMES"), then counts up past the half hour; under a
minute it burns ember. By day the clock and kills are gone (they mean
nothing in a town); gold stays. The night's phases are named under the
clock, each in its colour, popping in as they turn: Dusk, Gloaming, the
Witching, Ashfall, the Coming, Beyond (S-21).
**Why**: a countdown makes the half hour a goal the player is approaching,
not time passing; one number replaces the objective line repeating it.

### 4.3 Health
**Done**: a **globe** of blood in a gold rim (132 px) at the console's left
end: its level, a pale trail that catches up behind a fall (a big hit is
*seen*), a shield's arc round the rim, its number on the glass, statuses as
chips above it (a status with no end shows no count). Below 35% it beats and
pulses and the screen's edge bruises. **Health under the survivor** at
night: a 76 px bar under their feet with the shield, easing in with the
fight (setting "Health under you").
**Why both**: a globe reads at a glance as a level, not a number (Diablo's
own answer, and the console's anchor); the under-bar is where the eye is in a
horde (Vampire Survivors, 20 Minutes Till Dawn). Red is never alone: the
number, the beat and the bruise all say "low". The art pass's health bar,
its casing and the heart medallion belonged to the first pass's corner and
are not shown; the globe's painted rim and glass are asked for instead
(`UI_ART_BRIEF.md` 4.9).

### 4.4 Skills (on the console)
**Done**: each skill a 67 px slot standing on the console, its glyph in its school's colour, a shade
sweeping as it readies, a flash when it fires; the rank as a **numeral on a
badge** over a segmented strip (was 5 px pips); a skill ready to evolve
breathes gold until the draft offers it. Six places at night (a promise of a
full build), none empty by day. Blessings and passives as chips above.
**Why**: a numeral is read at a glance where pips must be counted (Miller,
recognition over recall); the breathing slot tells the player an evolution is
coming before the card does, so they feel clever when it arrives.

### 4.5 Hands (the console's right end)
**Done**: the art's ready-ring (painted: six of the binders' coins and the
seventh link pried open) with its seconds at the console's right end, then
the draught and its count and the dash charges; each with its key or button
for the device in hand.

### 4.6 The corner: minimap, place, quest (top right)
**Done**: a **minimap** (200 px) drawn from the zone itself (the big map's
ink), north up, fog as blank parchment, the zone's outside darker, dimmed at
night. Marks for quests, the way out, danger, mysteries, people (dots: a
town has many). What is *sought* (a quest, its next step, the way out) stays
on the rim pointing the way when off the disc. Not in arenas. Under it the
place's name and line, and the tracked quest's steps. A soft shade behind
the corner keeps the words legible over bright cobbles.
**Why**: "finding what you need how you need it" is the owner's own test; a
minimap with pinned objectives is the ARPG standard (Diablo IV, Lost Ark),
and drawing it from the zone (not a radar) keeps it in the world's hand.

### 4.7 What matters off the screen (**Done**)
An arrow at the edge, with its glyph, for what rules the arena, the nearest
three elites and chests, when they are off screen, inside the HUD's bands.
**Why**: the arena camera shows a lot but not all; a boss walking in from
off-screen should never be a surprise (fairness), and a chest seen at the
edge starts the chase (S-09's "the cue before it").

### 4.8 What comes and goes
- **The use prompt** (**Done**): floats over what it is for ("E Choose a map
  The Wayfinder's Table" above the table), falling back to the bottom when
  that is off screen. **Why**: the eye is on the thing, not on the bottom
  edge; one glance joins verb and object.
- **Toasts**: kind by edge and icon; a burst of discoveries or loot gathers
  into one toast that lists them (**Done**).
- **Hint**: parchment, at first contact, its keys drawn for the device.
- **Speech, announcements, the boss bar**: as before, sizes raised.
- **Names over heads** quieter (**Done**: they rivalled the zone's title).

---

## 5. The night's choices: the draft (`Panels.cs`, `DraftPanel`)

**The job**: every minute or so, a choice made in seconds that shapes the
night, understood at a glance and never regretted for want of information.

**Alternatives weighed**: Vampire Survivors' compact list (fast, but text
small and the build out of sight); HoloCure's stats beside the options;
Hades' boon cards (rich, framed by source, say what they replace). Ours is
Hades' cards with HoloCure's "your build beside the choice".

**Done** (second pass: concept `draft_c_crested_cards`, over `draft_a_cards`
and `draft_b_rows`): the cards rise over the ember's fire (the world darkens,
the fire glows from the foot: "the night's power"), under a great heading
("A GREAT BLESSING", "EMBER 12") on the title plaque.
- **Crested cards** 320 × 500: the rarity in the crest band, the corners and
  the hairline (painted: the rarity as a road through the world, iron, the
  Verge's bramble, the Low Ford's rime, the binders' violet, the Order's dawn
  gold, the breaking chain); the lifted card glows in its rarity and its
  medallion lights. A ribbon saying what it is and **NEW** when new to the
  build; the icon on a medallion in its school's colour; the name; a rank strip
  (held dim, this one bright); the text at 18 px; tags lit where the build has
  them and **Fits your build**; a passive that a held skill needs to evolve
  says so in gold (**Evolves Butcher's Cleaver at rank 8**); rarity in word,
  colour and diamonds; its key.
- **Your build** on a slab under the cards: the skills (with ranks) in six places, the
  blessings and passives; the lifted card **lights what it touches** (the
  skill it raises, the place a new skill takes, the blessing it deepens, the
  skill it would let evolve).
- Mouse hover lifts and click takes; 1-4 take; arrows or D-pad lift, Enter or
  A take; X rerolls; B or Y banishes (a red state that says what banishing
  does). Nothing can be taken for 0.38 s after the cards rise (a held key
  cannot spend a level). The chosen card swells and the rest fall away.

**Why this is the best answer**: the hardest thing in a survivors draft is
"rank 3 to 4 of what, and does it matter?"; lighting the build answers it
without words (recognition over recall, R4) and teaches synergy by showing
it (R7). The evolution line is Vampire Survivors' "needed to evolve", the
genre's most loved hint.

---

## 6. The day's book

**The job**: everything about the survivor and their story, browsed at
leisure, with one way in and one way between pages.

**Alternatives weighed**: five separate windows (the old way: three were
unreachable by pad except through the pause menu); a radial (fast, but these
are reading screens); one book of tabs (Diablo IV, PoE2 on pad). **Done**:
Pack, Self, Arts, Journal and Map are five pages of one book, each a **full
page** (1.3): the tabs in the header band's left, each with its key; LB/RB or
[ ] turn pages with a page sound; a page's own key, or View on a pad, closes
it; Close at the band's right.
**Why**: one button (View) reaches everything; the tabs teach the keys by
showing them; turning pages keeps the player's place (Hick: five clear
choices at the top, depth behind each).

**Page or panel, screen by screen** (the owner: "full page screens in general
aren't really great on some things"). The test is the job: a screen opened to
**read, plan or find** at leisure, with nothing in the world to watch, earns
the whole screen; a screen opened to **tweak mid-play or glance at** keeps the
world in view. And the world: every screen pauses it **only in a fight** (an
arena, the night's road), where the horde would not wait; elsewhere the world
goes on behind it (the owner's rule). The pause menu always stops it.

| Screen | Form | Why |
|---|---|---|
| Pack | **Panel at the right** (880 wide); the thing read closely at the left; the survivor steps aside into the gap (the camera's `ScreenShift`) | The most-used screen mid-play: swap a ring, drink, compare a drop. Diablo IV, PoE and Last Epoch all keep the inventory as a side panel with the hero in view; the gear is seen on the survivor in the world as it changes |
| Self | Full page | A planning sheet: four attributes with previews, traits for the build, every number with its sources. Too much to read in a panel without hiding the reasons, and it is not tweaked in the heat of play |
| Arts | Full page | Mastery and facets are planned, changed only "where it is safe" (D4's and PoE's skill trees are full screen) |
| Journal | Full page (the open book) | Reading at leisure |
| Map | Full page | Opened to find something: the whole screen is the map (D4, Elden Ring). The glance is the minimap's job |
| Shop, storeroom | Full page | Trading is deliberate, in a safe place, comparison-heavy across three things (their wares, your pack, the thing in hand), and the merchant is a person on the page. Nothing in the world to watch |
| Pause | Side column | The world stays in view, paused (D4, Elden Ring) |
| Conversation, draft | Over the world | The person, or the fire, is the scene |
| Last Lamp, Wayfinder's table | Windows | A quick choice in the place itself |
| Arena's end, chapter's end, creation | Full page | Moments, not tools: they are the screen |

### 6.1 Pack (`Pack.cs`, **rebuilt**)
**The job**: answer "is this better?" and "what do I do with it?".
**Composition** (third pass: a panel, see "Page or panel" above; the second
pass's `pack_b_two_panes` became the panel's halves stacked): a panel down the
right. At its head the book's tabs, Close, the plaque and who the survivor
is; then the survivor drawn with what they wear round them in 72 px slots
(head, amulet, body, cloak at the left; weapon, off-hand, two rings, relic at
the right), their standing in a well beneath; then the filters and sort, what
they carry in a well of 84 px slots (8 by 3), gold and how full the pack is.
The thing chosen (or focused, with a pad) is read closely at the screen's
left over the world, the worn thing's card under it; the survivor stands in
the gap between, in the world, wearing what they wear. **Why**: the owner's
"a big dark mostly-empty box with small items" first, then "full page screen
in general aren't really great on some things": the pack is the screen the
player opens in the middle of play.
**Design**: the survivor and what they wear on the left, with their
**standing**, which shows what a hovered or focused thing would change
("Health 212 to 236 better"); what they carry on the right with **filters**
(All, Gear, Draughts, Materials, Quest; LT/RT), **sort** (Y), **NEW** marks
until looked at, and the chosen thing read closely with its actions. The
hovered thing's card has **the worn thing's card beside it** (WORN NOW).
**Drag and drop**: from the pack onto the body to wear, off it to take off,
along the pack to move. Right-click or double-click wears or uses. On a pad
A wears, uses or takes off; X leaves behind, **asking twice** (it cannot be
undone).
**Why**: Diablo IV and Grim Dawn show the worn item beside the hovered one,
because comparing two cards is recognition and remembering one is recall;
the live standing turns the question "is it better for me?" into an answer
before the click. Drag is what every ARPG player's hand tries first. Filters
and sort keep a growing pack scannable (Hick, chunking).

### 6.2 Self (`Book.cs`, **rebuilt**)
**The job**: answer "what am I becoming, and where do my numbers come
from?".
**Composition** (second pass, `self_b_pillars` over `self_a_columns` and
`self_c_paper_sheet`): three panes. **Why**: the owner's "a dense wall of
text in a box"; each kind of thing now has its own shape.
**Design**: who they are on the left (figure, the level on a medallion,
experience in the day's blue, the art in hand, the calling, what they know
and what it opens, conditions); the four attributes in the middle as
**pillars**, the number the hero on a 120 px medallion at each head, each
saying what a point gives, and with points to spend the **+ previews** the
point's change in the standing (+1.1% faster, +2% area); traits under them as
cards, with the places still to fill (a trait at level 4, 6, 8) shown locked.
On the right the whole standing on slabs, grouped by
purpose (staying alive, dealing death, moving, fortune); **any line, hovered
or focused, says where it comes from** (the calling, the attributes, each
thing worn by name, traits, conditions).
**Why**: PoE and Last Epoch players live in their stat sources; a number
without a source teaches nothing. Previewing a point before spending it is
error prevention (R9) and makes the choice a choice (autonomy).

### 6.3 Arts (`ArtsScreen.cs`)
**Design** (second pass, `arts_b_altar` over `arts_a_list` and `arts_c_tree`):
two pages (the art in hand; skills by day) on LT/RT. The art in hand is an
**altar**: the known arts as medallions on slabs with their rank, then those
to learn, dim, in the left pane; the chosen art as a great medallion with its
two facet sockets (rank II, rank IV), its words, its rank and progress; four
**facet cards** (crested, "opens at rank II"); and the **road to mastery**, five
rank medallions joined by a line, each saying what it brings. Skills by day:
the learned ones and the unseen ones as "?" medallions, and three cards that
teach how a skill comes to you (seen, learned, carried).
**Why**: arts are few and precious; medallions with progress round the ring
say so. A tree overstates a five-rank system; a list hid what is coming. It
still shows what is coming before it can be had (progressive disclosure that
teaches).

### 6.4 Journal (`Book.cs`)
**Design** (second pass, `journal_b_open_book` over `journal_a_sheet` and
`journal_c_board`): **a book lying open** (`OpenBook`: tooled leather,
parchment darkening into the spine, the leaves' thickness), the list on the
left leaf and the page on the right; Quests, People, Deeds and Codex are
**silk ribbons** over its top edge (red, green, blue, gold) on LT/RT; the day
and whose journal it is at the leaves' feet; reading text at 18 px; empty pages
say what will be written there. **Why**: it is the survivor's own book; two
leaves give list and page side by side; leather and parchment are the
material the owner asked for. **People rebuilt** as a
list and a page: those met with how each feels in a word; the one chosen
drawn as they look, trust, warmth, respect and fear as measures with words
("much fond of you"), what is on their mind and what they know you did.
**Why**: relatedness (PENS) is the town's heart; a page per person, with
their face, makes "they remember" felt rather than listed.

### 6.5 Map (`MapScreen.cs`, **rebuilt** as an atlas, then full bleed)
**Design** (second pass, `map_b_full_bleed` over `map_a_square` and
`map_c_table`): the zone drawn from itself takes the whole screen under the
header band; it opens **fitted to what you know** (every walked cell and
where you stand, with a margin), never on the whole zone with the known part
small at its edge. **Unwalked land is dark**, opaque and the same dark as
past the paper's edge, so the known world is a lit island; the view is held
so the paper covers it wherever the paper is large enough (opened at the
Verge's west edge, a third of the view used to be past it). Beside it, on a
plate at the right, **where to go, the people, the places and what to beware
of**, nearest first, each with how far and which way ("15 m north-east"),
then the legend and the prompts. A line hovered or focused **glides the map
to its mark and rings it**; chosen, it draws closer. Zoom, find-me and "all I
know" on a slab at the map's foot; a compass at its head. Pad: the D-pad
walks the list, the triggers zoom, Y finds you; mouse: the wheel zooms, a
drag pans.
**Why**: a map is opened to answer "where is X?"; a list answers it
directly and the map shows the way, and a pad needs no cursor to use it. The
owner's complaint was "a huge empty parchment square with the zone tiny at
its edge": the screen is the map now, and it opens on what matters.

---

## 7. Other screens

### 7.1 Title
The fire, the stranger, the painted logo (the broken chain through the
letters), the house's rule under it (one gold rule with its ember stone), a
short menu with an ember marking focus and its key, the last journey under
Continue; side panels on plates with plaques take focus. **Why kept**: short
(Hick) and in the world; only light touches in the second pass.

### 7.2 Making a survivor
**Composition** (second pass, `create_b_crested` over `create_a_rows`): a
forged column down the left (the painted plate, running off the screen's
edge), the figure by the fire in the middle, the choice read closely on a
plate at the right, and who they are becoming on a **banner** at the figure's
feet ("NAMELESS · Hunter Warden"). In the column: the four steps as a **road
of medallions** (I Calling, II Arms, III Origin, IV Name) on LB/RB, then the
choices as crested cards, each with its medallion mark, a name and a line.
The figure changes at once. Pad: A takes a choice, A again moves on;
left/right move the figure slider; on the name step a pad is offered "a name
from the road" (it cannot type). **Why**: every choice shows its consequence
before the commitment (R9), a pad can finish creation without a keyboard, and
the fire stays the centre of the screen.

### 7.3 Pause
**Composition** (second pass, `pause_b_side` over `pause_a_box`): the game
stays in view, paused, and a forged column runs down the left: PAUSED on its
plaque, where you are, the day and what you are about, the menu, and the
book's five pages as medallions with their keys at its foot; settings and
controls open beside the column and take focus. **Why**: Diablo IV and Elden
Ring keep the world in view behind the pause; a box in the middle hid the
moment the player paused on.

### 7.4 Conversation
**Composition** (second pass, `talk_b_portrait` over `talk_a_boxed` and
`talk_c_column`): the person large, head to hip (`Portrait`, half framing),
standing over the left end of the words as across a table; their name on a
banner, what they are and how they feel about you under it; the words and
the answers on a plate along the foot. **Why**: relatedness is the town's
heart (Disco Elysium, BG3, Hades); a 228 px bust in a box made them furniture.
The person as they look to you; speech at its pace; what you can say back,
numbered; badges for what a background or kit opens; what you cannot say,
greyed, with the reason. **Done**: focus on the lines (up and down, A or
Enter says it; the use key only answers when there is one thing to say);
**what was said just before stays above the line** (your answer, or their
last). **Why**: the pace of speech hides the thread; a recalled line means a
choice is never made blind.

### 7.5 Shop (**rebuilt**)
**Composition** (second pass, `shop_b_counter` over `shop_a_box` and
`shop_c_two_grids`): a full page laid out as a **counter**. The merchant is a
person first, on the left: their face, how they feel about you, their usual
prices, what they buy, when new stock comes, what is on their mind. The wares
large in the middle in a well, the chosen thing read closely under them with
its price and what it would replace; your pack and purse at the right.
Prices on a dark tag with a coin, **red when more
than you have**; quantity as "×3" (never confused with a price). Buy or sell
by right-click, double-click, A, or **dragging across**. **Why**: the
decision (price against worth against what you wear) is made in the middle
column, between the two things it is about.

### 7.6 Storeroom (**rebuilt**)
A full page: the store's large grid (48 places) on the left, your pack and
the thing read closely on the right, with how full each is; a click, A, or a
drag moves a thing across.

### 7.7 The Last Lamp
Sleep (with its price), wait for night, not yet; refused, it says why ("You
need 5 gold; you have 2"). The morning on paper at body size.

### 7.8 The Wayfinder's table
Three maps as cards: tier with diamonds, name, who holds it and what rules
it, their bane, the oaths (asks, gives, what answers them), Enter at the
foot. The plate fits.

### 7.9 The arena's end
**Composition** (second pass, `result_b_spoils` over `result_a_boxes`): the
verdict on a **banner**, the arena's name, the night's numbers on **counting
medallions** whose rings fill, what you take out on a forged plate, and the
lost build as grey medallions on ash beside it. **Why**: peak-end; the
numbers are the trophy, so they are the largest things on the screen.
The verdict, the name, the tally **counting up** one after another (time,
slain, ember, past the half hour), "your longest yet", what comes out
against what stays; how it ended in a line: who brought you down and when,
and how near what ruled it was ("6 minutes before the Pack-Mother would have
come"; S-16). **Next**: the run's peak (the biggest blow, the evolution's
minute), which needs the fight to keep them. **Why**: the end of half an hour is what the player remembers of it
(peak-end).

### 7.10 The chapter's end
The survivor's book read back from the world. Enter keeps walking.

---

## 8. Accessibility

**Done**: every action rebindable on the keyboard; the pad for everything;
prompts that follow the device; text floor 15 px, prose 18 px; contrast as
in 1.1; colour never alone (rarity's diamonds and names, better and worse in
words, pad letters, the low-health beat); screen shake, gore and health-
under-you settings.

**Next**, by how many players they help (IGDA top ten): text size (100, 125,
150%) and a plain-sans option; subtitle backing and size; an effects-opacity
slider for the survivor's own effects (Soulstone's lesson; the feel work's
S-19); hold-to-press options; a colour-blind preset for better/worse; pad
remapping.

---

## 9. Input from the feel and items work

Weighed against the research, taken where it makes the interface better.

| Proposal | Source | Decision |
|---|---|---|
| Bars that flow; glow from 85%; flash on the level | feel S-06 | **Done** (4.1) |
| The night's phases named on the clock | feel S-21 | **Done** (4.2), with the countdown |
| An end screen that tells the run's story | feel S-16 | **Done** for the cause and the near miss (7.9); the run's peak is next |
| The chest as a sequence | feel S-09 | Adopt as a panel like the draft; needs `ArenaRun.OnPickup` to hand the chest to the host (logic owner) |
| The evolution's name card | feel S-10 | Adopt the HUD's part (the slot flares, the name card); the slow motion is FX |
| Off-screen warnings for charges and missiles | feel S-19 | Extends 4.7's edge marks; needs the telegraph data |
| Damage numbers that merge and cap, with a setting | feel S-13 | FX, not the HUD; agree, and the setting belongs in Settings |
| Rarity is the frame, not the picture | items VISUALS §8 | Already so (slots, cards, tooltips); kept |
| Set pieces marked by a corner | items VISUALS §8 | Adopt when sets exist: a corner mark on slots and cards (art brief) |
| Proposed item tiers (Plain, Fine, Rare, Marked, Named, Storied) | items | When the item system lands, the rarity ladder (1.1, art brief 2.4) maps onto it one for one |
| The spoils reveal, Named last | items VISUALS §9 | With the chest panel |

---

## 10. What is next, in order

1. Bring the rest into the frame language, each from its job: the item card
   (a crested tooltip, the comparison as two cards with a delta column);
   buttons, segments and tabs drawn by Ornate with every state; the
   Wayfinder's table (three maps as cards on a table, in the painted wooden
   map frame); the Last Lamp; the chapter's end; toasts, the hint,
   announcements, the boss bar; the Journal's deeds and codex inside the book.
2. The painted pieces of `UI_ART_BRIEF.md` 4.9 (the UI art lead).
3. The feel work's remaining interface pieces (section 9): the chest panel,
   the evolution's name card.
4. Text size setting (needs the HUD anchored rather than placed at 1080p).
5. Hold-to-read detail on cards and items (pad Y, keyboard Alt).
6. The remaining accessibility settings (section 8).

---

## 11. The second pass: concepts and choices

`tools/comfy/ui_concepts.py` drew each layout from crops of the real game and
painted it with the local Krea model (img2img, the darkbrush LoRA at 0.6,
denoise 0.55); each image in `docs/ui_review/concepts/<screen>_<a|b|c>_<name>.jpg`
is the drawn layout beside its painting. The before, first pass and second
pass of every screen side by side are in `docs/ui_review/<screen>.jpg`
(`tools/comfy/ui_review.py`).

| Screen | Weighed | Chosen | Why |
|---|---|---|---|
| HUD | A corners (as it was), B console, C minimal | **B console** | Diablo IV and Lost Ark put health, skills and the art in one band where the eye drops from the fight (proximity, Fitts); the corners split attention three ways. Health as a globe reads at a glance as a level; the ember bar stays top centre; health under the feet stays at night |
| Pack | A box, B two panes, C hero centre | **B two panes** | The survivor large on the left with what they wear round them and their standing beneath; what they carry on the right in 112 px slots with filters, the chosen thing read closely, gear beside what it would replace (D4, Grim Dawn: comparison is recognition, not recall) |
| Self | A columns, B pillars, C paper sheet | **B pillars** | Who they are; the four attributes as pillars with the number the hero and a + that previews its change; traits as cards with the places still to fill; the standing grouped on slabs with sources on hover. Answers "a wall of text" by giving each kind of thing its shape |
| Arts | A list, B altar, C tree | **B altar** | Arts are few and precious: medallions with rank progress; the chosen art as a great medallion with its facet sockets; facet cards; a road of five ranks. A tree overstates a five-rank system; a list hid what is coming |
| Journal | A sheet, B open book, C board | **B open book** | The survivor's own book; two leaves give list and page side by side; ribbons are the book's own tabs; leather and parchment are the material asked for |
| Map | A square, B full bleed, C table | **B full bleed** | Opened to find something: the whole screen, fitted to the walked land and you, unwalked land dark so the known world is a lit island; the list at the right; zoom and find-me at the foot |
| Draft | A cards, B rows, C crested cards | **C crested cards** | Hades' cards with rarity in the frame; the ember's fire behind says "the night's power"; the build strip beneath (HoloCure) |
| Conversation | A boxed, B portrait, C column | **B portrait** | The person large, head to hip, over the left end of the words as across a table (Disco Elysium, BG3, Hades) |
| Shop | A box, B counter, C two grids | **B counter** | The merchant is a person first; the wares large in the middle, the thing read closely; your pack and purse at the right |
| Creation | A rows, B crested | **B crested** | A forged column of crested calling cards; the steps as a road of medallions; the choice read closely; who they are becoming on a banner; the fire stays the centre |
| Pause | A box, B side | **B side column** | The game stays in view, paused (D4, Elden Ring): a forged column with the place, the day and the task, the menu, the book as medallions; settings open beside it |
| Arena's end | A boxes, B spoils | **B spoils** | Peak-end: a verdict banner, the night's numbers counting on medallions, what you take on a forged plate, the lost build as grey medallions on ash |

**The art and the redesign together** (the UI merge): the painted art fills
the new layouts rather than either winning by default. The painted plate,
paper, slots, tooltips, buttons, tabs, prompts, toasts, hint, bars and their
casings, the minimap rim, the art's ring and the logo wear the new layouts
directly; the painted draft cards wear the crested card's medallion and
lifted glow, with the words kept 40 px inside their iron; the creation and
pause columns wear the painted plate; the globe stays the health (the
painted health bar belonged to the old corner); the map stays full bleed (the
painted wooden frame moves to the Wayfinder's table when it is rebuilt).

**Focus routes** are walked by the game itself: `--navcheck` with a picture
(`--shot`) prints, for the open screen, how many things can take focus, how
many the four directions reach from where focus starts, and any that are
unreachable, off the screen or without size (`Nav.Audit`).
