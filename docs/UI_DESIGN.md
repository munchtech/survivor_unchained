# UI design: every element, and why

The interface of Survivor Unchained, element by element: what it was (the
audit), what it should be (the design), and how far the code has got
(**Done** is in the game now; **Next** is designed and not yet built). The
reasons are in `UI_RESEARCH.md`; rules are cited as R1-R10 (its section 8).
The art for all of it is specified in `UI_ART_BRIEF.md`.

The game is two halves, and so is its interface:

- **The night** (the prologue's road, the ember arenas): a survivors-like.
  Sparse, glanced at, colour-coded, nothing in the middle but the fight.
- **The day** (the Waystation, the Verge): an ARPG. Browsable, read,
  detailed, a book of five pages.

Both halves share one frame language (iron, gold hairline, ember light,
parchment for what is written) and one way of being driven: mouse and
keyboard and pad are equals (R5).

---

## Contents

1. Style guide: palette, type, spacing, frames, icons, motion, sound
2. Navigation: the input model for pad, keyboard and mouse
3. The audit, in brief
4. The HUD
5. The night's choices: the draft
6. The day's book: Pack, Self, Arts, Journal, Map
7. Other screens: title, creation, pause, conversation, shop, storeroom,
   rest, the Wayfinder's table, the arena's end, the chapter's end
8. Accessibility settings
9. What is next, in order

---

## 1. Style guide

### 1.1 Palette tokens (`godot/src/Ui/Style.cs`)

Colour is a language (R3): each hue means one thing, and every meaning also
has a word, a mark or a shape so no-one depends on hue alone.

| Token | Hex | Means |
|---|---|---|
| `Iron0` `Iron1` `Iron2` `Iron3` | #0b0a0d #15131a #1e1b24 #2a2631 | Plates, wells, slots: the night-iron the interface is forged from |
| `Gold` `GoldHi` `GoldDim` | #d9b56a #f3d9a0 #8a6f3e | The interface itself and what is *yours*: headings, frames, the selected |
| `Line` `LineHi` | gold at 35% / 70% | Hairlines, frame edges, dividers |
| `Ember` `EmberHi` | #ff8a3a #ffd07a | The night's power: the ember bar, "fits your build", what is new |
| `Focus` | #ffc46a | What has focus (the ring); ember-gold, never used for anything else on a plate |
| `Blood` `BloodHi` | #c8323a #ff5a5a | Health, danger, the enemy's |
| `Day` `DayHi` | #86b0d8 #d8ecff | The day's growth: experience, the survivor's own level |
| `Shield` | #9ad4ff | Barriers, good statuses |
| `Ink` `InkDim` `InkFaint` | #e8dcc4 #a89c88 #6f6556 | Text on iron: body, secondary, tertiary (never for anything that must be read) |
| `Parchment` `ParchmentInk` | #e8dcc0 #2a2118 | Paper (journal, hints, the morning report) and its ink |
| `Good` `Bad` | #8ae05a #ff7a6a | Better and worse, always with a sign and a word |
| Rarity 0-5 | #c8c0b0 #6fd46a #5aa8ff #c070ff #ffb040 #ff6a3a | Common, uncommon, rare, epic, legendary, relic: with the name and 1-6 diamonds |
| Schools | physical #e8dcc4, fire #ff8a4a, frost #8fd0ff, storm #9ab8ff, nature #8ae05a, arcane #cc88ff, holy #ffd46a, shadow #a87aff | A skill's school: its glyph, its card's disc, its slot's tint |
| Pad face buttons | A #6bc45a, B #ec5a50, X #4a9cf0, Y #f2c440 | Always with the letter |

Contrast: body text (`Ink` on `Iron1`) is about 13:1; secondary (`InkDim`)
about 6.5:1; `InkFaint` (3.4:1) is only for decoration and disabled things.
Parchment ink on paper is about 12:1.

### 1.2 Type (Cinzel, Alegreya, Alegreya Sans; SIL OFL, `godot/art/fonts`)

Three faces, three jobs: **Cinzel** for names carved in stone (headings,
places, titles of things), **Alegreya** for what is read (descriptions,
dialogue, the journal), **Alegreya Sans** for the interface's own words
(labels, numbers, keys).

The scale, in pixels at 1080p (`Style.Hero` ... `Style.Badge`):

| Token | px | Use |
|---|---|---|
| `Hero` | 54 | Fade captions, the arena's name at its end |
| `Heading` | 32 | A screen's subject (an art's name, a quest's) |
| `Title` | 24 | Card titles, section heads on paper |
| `Lead` | 20 | Kickers above big headings, the draft's tip |
| `Body` | 18 | Everything read as prose; dialogue lines are 23 |
| `Small` | 16 | Labels beside values, button text |
| `Caption` | 15 | Secondary lines, footers, tags. The floor for anything a player must read |
| `Badge` | 13 | Numerals on badges only (ranks, counts) |

Faces lack some symbols (★ ▲ ◆ ◦ ✓ ← →): marks are drawn as shapes
(`Style.Gems`, the D-pad cross), never typed. All caps only for one- or
two-word labels; sentences in sentence case (XAG 101).

### 1.3 Spacing
Steps of 4: `Gap1` 4, `Gap2` 8, `Gap3` 12, `Gap4` 16, `Gap5` 24, `Gap6` 32.
Screens keep a 36 px margin from the edges (the HUD's safe area: about 2%
of 1920). Plates have 18-22 px padding. Lines of prose stay under about
80 characters (cards and hints are 360-420 px wide for that reason).

### 1.4 Frame language
- **Plates** (screens): iron, a gold hairline, a soft shadow beneath; corners
  slightly rounded. Painted: forged iron with riveted corner plates and a
  thin gold inlay (`frames/plate.png`).
- **Paper** (what is written: the journal, hints, the morning, the
  chapter's end): warm parchment, a darker deckled edge.
- **Cards** (the draft): a tall frame whose border carries the rarity; the
  evolution's is gilded.
- **Slots**: square wells sunk into the iron; the rim carries rarity; an
  item's slot glows faintly in its rarity.
- **Ribbons and chips**: pill shapes for kickers ("NEW", "GREAT BLESSING"),
  statuses and badges.
- **Ornament lives on edges and corners**, never under text (R8, Hades'
  "clarity under pressure and personality everywhere else").

### 1.5 Icons
- **Line glyphs** for everything abstract (skills, blessings, statuses,
  stats, gear slots): one system, a 24-unit square, a 1.6 stroke, round
  caps (`godot/data/content/glyphs.json`). They take a tint: a school's,
  a rarity's, or a state's (dim when not ready).
- **Photographs** for items (`ItemPhotos.cs`): each item rendered from its
  model, as Diablo IV's icons are.
- **Painted icons** (the art brief) replace glyphs one by one; code asks
  `UiArt.Icon("glyph", key)` first.
- Every icon must read at 18 px and be recognisable by silhouette alone.

### 1.6 Motion
- Every press answers within a frame (highlight, scale, tick; R6).
- Entrances 0.2-0.5 s, ease-out; exits faster than entrances.
- Things that matter breathe (low health's heart, a ready evolution's slot,
  the focus ring) at 0.6-1.2 Hz; nothing strobes (WCAG 2.3.1).
- Choices land: the chosen card swells, the rest fall away.
- Numbers that are rewards count up (the arena's end).

### 1.7 Sound (`godot/src/Audio/Sfx.cs`)
Hover tick (`Hover`), press (`Click`), refusal (`Deny`), page turn
(`Page`: the book's tabs, a screen's sections), card taken (`Pick`), gear
worn (`Equip`), screen opened (`Open`) and closed (`Close`), the level's
rise (`LevelUp`), an evolution (`Evolve`), a discovery (`Discovery`). Every
interactive thing has a hover and a press sound; every refusal has `Deny`.

---

## 2. Navigation: one input model for three devices

### 2.1 The button map (`godot/src/Game/Controls.cs`)

| | Keyboard and mouse | Pad (Xbox names) |
|---|---|---|
| Move | WASD / arrows | Left stick |
| Dash | Space / Shift | A |
| Art in hand | Q / right mouse | X |
| Draught | R | Y |
| Talk, use | E / F | B |
| The book (Pack) | I / Tab | View |
| Self, Arts, Journal, Map | C, K, J, M | View, then RB |
| Pause | Esc / P | Menu |
| **In menus** | | |
| Move focus | arrows (held: repeats) or the mouse | D-pad or left stick (held: repeats) |
| Choose | Enter, click | A |
| Back, close | Escape, Backspace | B |
| Second and third action on focus | Delete; buttons on screen | X, Y |
| The book's pages | [ and ] | LB, RB |
| A screen's own pages | , and . | LT, RT |
| Draft: take a card | 1-4, click | D-pad and A |
| Draft: reroll, banish | X, B | X, Y |

**Done.** In a menu a pad button now means its menu meaning first: before,
A was taken as a dash, B as "talk", X and Y as the art and the draught, so
the title and pause menus, rerolls, banishes and dialogue choices could not
be driven by a pad at all. A held direction repeats after 0.36 s every
0.11 s (deliberate, after PoE2's "too fast" complaints); the stick moves
focus like the D-pad; the triggers turn sub-pages.

### 2.2 Focus (`godot/src/Ui/Nav.cs`)
**Done.** Every screen has focus that moves with the arrows, the D-pad or
the stick to the nearest thing in that direction (level neighbours beat
nearer ones off-axis). Every visible button takes focus on its own; slots,
dialogue lines and sliders join by `Nav.Mark`. Focus is kept by name, so a
screen rebuilt after a change still has it where it was. A presses, X and Y
do the focused thing's second and third actions. Lists that move their own
focus (the title, the pause menu) are left to themselves.

- **The ring**: ember-gold, 2 px, a soft glow, breathing gently; shown only
  while keys or a pad are in use (R5: "clear and unmistakable" from a sofa).
- **Hand-over**: the pointer moves focus; the first direction pressed shows
  where focus is before moving it; moving the mouse hides the ring.
- **First focus**: each screen names it (the first pack slot, the first
  shelf item, the selected choice); Close buttons are left out of the order
  (B and Escape close everywhere).
- **Scrolling**: focus moving into a scrolling list scrolls it into view;
  pages with nothing to choose (the journal's People) scroll with up and down.

### 2.3 Prompts follow the device
**Done.** `Controls.UsingPad` flips on the last device touched (a key, a
click, a real mouse move, a pad button or stick); `DeviceChanged` redraws
every prompt at once: the HUD's hands, the interaction prompt, hints (W A S
D become the left stick), the draft's and the conversation's keys, every
screen's footer, the book's tabs (LB/RB or [ ]), close buttons (B or the
screen's key). Words that name keys in hints ("Space: a quick roll") follow
too, through `Game.KeyLabel`. Pad buttons are drawn as their real shapes:
face buttons as dark discs with the letter in its colour; bumpers, triggers,
View and Menu as pills; the D-pad as a cross with the meant arm lit.

---

## 3. The audit, in brief

What the interface was before this pass, judged against the research. Kept
where good; the rest is redesigned below.

| Element | Verdict | Why |
|---|---|---|
| The look (iron, gold, ember, parchment; three faces) | **Keep** | Coherent, themed, readable; colour mostly meaningful |
| HUD layout (health low left, hands low right, skills low centre, place top right) | **Keep, refine** | Sound hierarchy; but the fight's timer and kills showed by day, six empty skill slots by day, rank pips of 5 px, no minimap, corner text lost on bright ground |
| Pad support | **Broken** | A, B, X, Y delivered their play meaning in menus; no focus on any screen but the title, pause and draft; prompts always keyboard; dialogue choices unreachable |
| Draft | **Good bones** | Clear cards, school colour, "fits your build"; but no view of the build (recall, not recognition), rarity by colour alone, small text (17/13 px), keyboard-only prompts |
| Conversation | **Good** | Portrait, typewriter, badges, locked options shown with reasons (teaches that other ways exist); but no focus for pads |
| Pack | **Good bones** | Paper-doll, photographed items, comparison deltas; but deltas only (no worn card beside), quantity and price both unlabelled numbers in the shop, mouse-only |
| Self | **Adequate** | Clear attributes; small secondary text; empty right column; experience bar in ember colour (the night's) |
| Arts | **Good** | Ranks and facets explained in place; tabs as segments not reachable by pad |
| Journal | **Good writing, weak frame** | Paper, sections; empty states bare ("Nothing written yet."); sections took the book's tab keys; mysteries marked with a glyph the font lacks |
| Map | **Lovely, one bug** | Hand-drawn from the zone itself; unfogged ink showed in a strip at the right edge (the frame stretched past its fog); mouse-only |
| Title | **Good** | Short menu, the fire, the logo; menu focus marked with an ember |
| Creation | **Good bones** | Live figure, meaning beside each choice; pad could only change steps; empty half-height panels |
| Pause, rest | **Adequate** | Fixed-height plates with dead space; rest did not say why sleep was refused |
| Shop, storeroom | **Adequate** | Mouse-only; numbers ambiguous |
| Arena's end | **Underplayed** | The end of half an hour, listed rather than celebrated (peak-end) |
| Chapter's end | **Good** | A book read back from the world |
| Symbols | **Bug** | ★ ▲ ◆ ◦ ✓ ← → are missing from the faces (they fell back to a system font or a box) |

---

## 4. The HUD

The HUD is non-diegetic, at the edges, arranged so the eye never hunts
(R1): what can kill you where the eye already rests, what you choose at
the top edge, what fires by itself in a quiet row at the bottom, what your
hands do under your right thumb, the place and the quest at the top right.

### 4.1 The bar: ember by night, experience by day (top centre)
- **Shows**: a medallion with the level; a 900 px bar; the word under its
  start, **EMBER** (ember orange) or **EXPERIENCE** (day blue). **Done.**
- **Leading edge**: a bright tip that burns brighter in the last 40% (the
  goal-gradient effect: the next level is visibly near). **Done.**
- **States**: filling; full (the level pops: the medallion's number swells
  and settles); by day cool blue, slower.
- **Teaches**: the word under the bar names it; by day and night the same
  place holds "how far to the next", so the player maps it at once.
- **Next**: a flare along the bar on the level's rise; the art brief's
  medallion and bar frame.

### 4.2 The tally: time, kills, gold (under the bar)
- **Night**: the fight's clock (24 px Cinzel), kills and gold. **Day**:
  only gold (the clock and kills mean nothing in a town). **Done.**
- **Next**: in an arena, the clock counts *down* to the boss (one number,
  not two: the objective line repeats it today).

### 4.3 Health (bottom left)
- A heart medallion, a 362 px bar with the number in it, quarter ticks, a
  pale trail that catches up after a moment (so a big hit is *seen*), a
  shield as a blue band across its top, statuses as chips above (icon and
  seconds). Below 35%: the heart beats and the bar pulses; the screen's
  edge bruises red (meta UI, the survivor's own pain).
- **Health under the survivor** (**Done**, setting "Health under you"):
  at night, a 76 px bar under the survivor's feet with the shield over it,
  pulsing when low; it eases in when the fight is on. The survivors-likes'
  answer to "the eye is on the character" (R1).
- **Accessibility**: red is never alone: the number, the beat and the
  bruise all say "low".

### 4.4 Skills (bottom centre)
- Each skill in a 67 px slot: its glyph in its school's colour; a shade that
  sweeps off as it readies; a flash when it fires.
- **Rank**: a numeral on a badge at the slot's corner, read at a glance,
  over a strip of eight segments (how far to the top). **Done** (was 5 px
  pips).
- **Ready to evolve**: the rim turns gold and breathes until the draft
  offers the evolution; evolved: a steady gold rim. **Done.**
- **Empty places**: six at night (the promise of a full build, as Vampire
  Survivors shows it); none by day, when only carried skills exist. **Done.**
- **Blessings and passives**: chips above the row, round for blessings and
  square for passives, the rank as a 13 px badge. **Done.**

### 4.5 Hands (bottom right)
- The dash's charges (two pips that refill), the draught (with a count), the
  art in hand (a ring that fills as it readies, the seconds in it), each
  with its key or button and its name. Keys follow the device. **Done.**

### 4.6 The corner: minimap, place, quest (top right)
- **Minimap** (**Done**): a 200 px disc of the zone's own drawing (the
  map's ink and hill shading), north up, the survivor as a red arrow at its
  centre, unwalked ground as blank parchment, beyond the zone darker. Marks:
  quests, mysteries, danger, the way out, people (as dots: a town has
  many). What is *sought* (a quest, a turn, the way out) stays pinned to
  the rim when off the disc, pointing the way (R: "finding what you need").
  Dimmed at night. Not in arenas: the whole fight is already on screen.
- **Place**: the zone's name (Cinzel 29), a line with the sun or moon, the
  day and the region.
- **Objectives**: the tracked quest's name and its steps, right-aligned;
  optional steps in italics with a round box (Zeigarnik: the open thread in
  sight).
- A soft dark shade behind the corner and along the bottom keeps the words
  legible over bright cobbles (the town's sign once fought the title).
  **Done.**

### 4.7 What comes and goes
- **Toasts** (left, a third down): a coloured edge and icon by kind (quest,
  world, relation, warning, lore, level, gold, loot); a burst of the same
  kind (discoveries, loot) gathers into one toast that lists them (**Done**).
  Up to six; each lives five seconds and fades.
- **Hint** (bottom left, parchment): appears at first contact with a thing,
  with its keys drawn for the device (**Done**).
- **Interaction prompt** (bottom centre): the key or button, the verb, the
  thing; locked, it says why, with a lock (**Done**).
- **Speech** (lower centre): who and what, Alegreya 24, shadowed.
- **Announcement** (upper centre): kicker, title, line, between two rules;
  coloured by kind (danger, blessing, story, place).
- **Boss**: name, title, a long bar with phase marks and a trail; a channel
  bar beneath when it calls something up.

---

## 5. The night's choices: the draft (`Panels.cs`, `DraftPanel`)

The survivors half's heart: every minute or so, time stops and three or
four cards rise.

- **Layout**: kicker ("The ember rises", "The fifteenth minute: ..."), the
  heading (EMBER 12, A BLESSING, A GREAT BLESSING), how many more are
  queued, the tip (prologue teaching); the cards (320 × 452, 28 apart);
  a banner for banishing; **your build**; the footer.
- **A card**, top to bottom (**Done**):
  1. a ribbon saying what it is ("New combat skill", "Combat skill · rank 3
     to 4", "Great blessing", "Evolution") and **NEW** when it is new to
     the build (Vampire Survivors' "New!");
  2. its glyph on a 112 px disc in its school's colour;
  3. its name (Cinzel 24);
  4. a strip of its ranks (held dim, this one bright, the rest dark);
  5. what it does (Alegreya 18), centred;
  6. its tags, lit in ember where the build already has them, and
     **Fits your build** with a flame;
  7. its rarity in word, colour and diamonds; its key (1-4, or A on the
     lifted card with a pad).
- **Your build** (**Done**): the skills held (with ranks) in six places,
  then the blessings and passives. The lifted card lights what it touches:
  the skill a rank card raises, the empty place a new skill would take, the
  blessing a card deepens (Hades says what a boon replaces; recognition over
  recall, R4, R9).
- **Interaction**: mouse hover lifts, click takes; keys 1-4 take; arrows or
  D-pad lift; Enter or A takes the lifted; X rerolls; B (keyboard) or Y
  (pad) toggles banishing, Escape or B (pad) stops it. For 0.38 s after the
  cards rise nothing can be taken (a key held from the fight cannot spend a
  level: error prevention).
- **States**: rising (staggered, ease-out); lifted (12 px up, brighter rim,
  glow in its rarity); banishing (cards rimmed red, the lifted one tinted,
  BANISH stamped, the banner says what banishing does); chosen (swells to
  106%, the others vanish, `Pick` sounds).
- **Teaches**: the build strip turns "rank 3 to 4" into "this one, there";
  lit tags teach synergy without a tutorial; NEW and the build's six places
  teach the slot limit; rarity's diamonds teach the ladder.
- **Next**: an evolution card that says what it needs (the passive) when
  that passive is offered ("evolves Oathblade at rank 8"); a hold-to-read
  detail for numbers (PoE's Alt).

---

## 6. The day's book

Pack, Self, Arts, Journal and Map are five pages of one book (**Done**):
tabs on the plate's top edge, each with its key on a keyboard; LB and RB
(or [ and ]) turn pages, with a page sound; a page's own key, or View on a
pad, closes it. View opens the book at the Pack; so a pad reaches every
page from one button (before, three of them were only in the pause menu).

### 6.1 Pack (`Pack.cs`, `InventoryScreen`)
- **Layout**: the survivor in the middle, drawn live, with what they wear
  round them (head, amulet, body, cloak on the left; weapon, off-hand, two
  rings, relic on the right); their stats beneath; the pack's 24 slots; the
  chosen thing's card with its actions; gold and how full the pack is.
- **Hovered or focused**: its card beside it; if it would replace something
  worn, the worn thing's card beside that, marked **WORN NOW** (**Done**:
  the ARPG side-by-side). The card lists what changes, each line with a
  sign, a colour and the word *better* or *worse*.
- **Mouse**: click to choose (the card on the right gets buttons: Use, Wear,
  Take off, Leave behind); double-click or **right-click** to wear or use
  (**Done**: right-click is the genre's habit).
- **Pad**: focus starts on the first pack slot; A wears, uses, or (on a worn
  slot) takes off; X leaves behind; the footer says so (**Done**).
- **States of a slot**: empty (a faint glyph of what goes there), filled
  (rarity rim and a pool of light, finer things brighter), selected (2 px
  rim), focused (the ring), refused (dim), quest items cannot be left.
- **Next**: compare on a held button for pads (Y) when the worn card is
  long; sort; a junk mark.

### 6.2 Self (`Book.cs`, `SheetScreen`)
- The survivor, level and calling, experience in the day's blue (**Done**:
  it was ember), the art in hand with its key, what they know; attributes
  with what a point gives (+ buttons when there are points, ember-lit); the
  standing (health, armour, damage, speed, critical, regeneration); traits,
  to choose and held; conditions, good and bad with an icon and a colour.
- Pad: focus on the + buttons and the traits; A spends or takes.

### 6.3 Arts (`ArtsScreen.cs`)
- Two pages, **The art in hand** and **Skills by day**, turned with LT/RT or
  , and . (**Done**). A list on the left (known first, then not yet learned,
  dim); the chosen one's detail on the right: rank and progress, what a
  rank gives, in hand or "take it in hand", facets (four, two to choose;
  "rank II opens the first").
- Teaches: the facets show what is coming before it can be had.

### 6.4 Journal (`Book.cs`, `JournalScreen`)
- Paper, in the survivor's own hand. Sections **Quests**, **People**,
  **Deeds**, **Codex**, turned with LT/RT or , and . (**Done**: "Journal"
  was both the book's tab and its own section).
- Reading text at 18 px (was 16, 14, 13). Empty states say what will be
  written there (**Done**). Pages without choices scroll with up and down.
- Mysteries are marked "?" (the font has no "◦"; **Done**).

### 6.5 Map (`MapScreen.cs`)
- The zone drawn from itself; fog where unwalked; places named once seen.
  The frame is exactly its size again (**Done**: the right-edge strip of
  unfogged ink). Marks share the minimap's look; the legend uses them.
- Mouse: wheel zooms, drag pans. Pad: stick or D-pad pans, RT zooms in, LT
  out (**Done**).
- **Next**: a cursor on the map with a pad to read a mark's name; pins.

---

## 7. Other screens

### 7.1 Title (`Front.cs`, `TitleScreen`)
- The fire, the stranger, the logo carved over the dark (painted logo
  replaces the type when the art arrives), a short menu with an ember
  marking focus, the focused line showing Enter or A (**Done**), and the
  last journey under Continue. Side panels (journeys, settings, controls,
  credits) take focus when open (**Done**).
- The adults' notice first, once.

### 7.2 Making a survivor (`Front.cs`, `CreateScreen`)
- Four steps (Calling, Arms, Origin, Name) with their numerals; LB/RB or
  [ ] turn them (**Done**: drawn at the step row's ends). Choices are rows
  with an icon, a name and a line; the figure by the fire changes at once;
  the right panel says what the choice means.
- Pad: focus on the choices; A takes one, A again on the taken one moves on
  (so A, A walks through); the figure slider moves with left and right; on
  the Name step a pad is offered "A name from the road" (it cannot type),
  and Begin with no name picks one and waits for a second A (**Done**).

### 7.3 Pause (`Menus.cs`, `PauseScreen`)
- A plate that fits its list (**Done**: it had dead space), the book's keys
  as a reminder (one line on a pad: "View: Pack, Self, Arts, Journal,
  Map"). Settings and controls open in a panel that takes focus.

### 7.4 Conversation (`Panels.cs`, `TalkPanel`)
- The person as they look to you; what they say at the pace of speech (a key
  or click hurries it); what you can say back, numbered; badges for what a
  background or kit opens; what you cannot say, greyed, with the reason.
- **Focus** (**Done**): the first line is lit; up and down move; Enter or A
  says the lit line; 1-9 still pick directly; Escape or B takes the way out.
  The use key only answers when there is one thing to say (so pressing it
  to start talking never picks an answer by accident).

### 7.5 Shop (`Pack.cs`, `ShopScreen`)
- The seller's shelf, the chosen thing, your pack; the plate fits (**Done**).
- **Numbers that cannot be confused** (**Done**): price on a dark tag at the
  top-left with a coin; quantity as "×3" at the bottom-right.
- Pad: A buys or sells the focused thing; the card follows focus.

### 7.6 Storeroom (`Pack.cs`, `StashScreen`)
- Stored (with how full) and the pack side by side; a click, A, a
  double-click or a right-click moves a thing across (**Done**).

### 7.7 The Last Lamp (`Menus.cs`, `RestScreen`)
- Sleep (with its price), wait for night, not yet; refused, it says why
  ("You need 5 gold; you have 2", **Done**). The morning report on paper at
  body size.

### 7.8 The Wayfinder's table (`MapTable.cs`)
- Three maps as cards: tier (with diamonds, **Done**), name, who holds it,
  what rules it, their bane, the oaths (asks in red, gives in green, what
  answers them), and "Enter the arena" at the card's foot. Lost story fights
  above, to take again.

### 7.9 The arena's end (`ArenaResult.cs`)
- The verdict, the arena's name, the tally counting up one after another
  (time, slain, ember, past the half hour; **Done**: the peak-end rule),
  "your longest yet" when it is; what comes out (experience, gold, a tome,
  discoveries) against what stays (the build the ember made); the button
  with its key.

### 7.10 The chapter's end (`Menus.cs`, `ChapterScreen`)
- A book read back from the world: what was done, what waits, who
  remembers you and how, what the world says you did. Enter keeps walking;
  with focus shown, A presses the button it is on (**Done**).

---

## 8. Accessibility

**Done**: every action rebindable on the keyboard; a pad for everything;
prompts that follow the device; text floor 15 px, prose 18 px; contrast as
in 1.1; colour never alone (rarity's diamonds and names, better/worse
words, pad letters, the low-health beat); screen shake and gore settings;
health under you on or off.

**Next**, in order of how many players they help (IGDA's top ten):
1. Text size (100, 125, 150%), and a plain-sans option for reading text.
2. Subtitles' backing and size for speech; speaker names always on.
3. An effects-opacity slider for the survivor's own effects (Soulstone's
   lesson).
4. Hold-to-press instead of repeated presses where it matters (dash).
5. A colour-blind preset that swaps green/red deltas for blue/orange.
6. Pad remapping.

---

## 9. What is next, in order

1. The art (all of `UI_ART_BRIEF.md`): every plug-in point already loads
   by name and falls back to the drawn look.
2. Text size setting (needs the HUD's fixed positions to anchor rather than
   sit at 1080p coordinates).
3. Arena clock counting down to the boss; the level-up flare along the bar.
4. Hold-to-read detail on cards and items (pad Y / keyboard Alt).
5. Map cursor for pads; pins.
6. The remaining accessibility settings (section 8).
