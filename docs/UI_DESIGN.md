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
the feel and items work · 10 what is next.

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
- **Frames**: plates for screens, paper for what is written, cards for
  choices, sunk wells for slots, pills for kickers and badges. Ornament on
  edges and corners, never under text. Plates fit their content (no half-
  empty plates).
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
Proven end to end with a plate, a ring, a fill and the logo.

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
in a quiet row at the bottom, what your hands do under the right thumb, where
you are and what you seek at the top right.

**Why not move it all round the survivor** (as some survivors-likes do): our
day half is an ARPG with a town and a map; an ARPG's corner layout (Diablo
IV, PoE) is what its players read without thinking. The night borrows only
the one thing that must be at the centre: health (4.3).

### 4.1 The bar: ember by night, experience by day (top centre)
**Done**: a medallion with the level; the bar; the word under it, **EMBER**
(ember) or **EXPERIENCE** (day blue); a leading edge that brightens as the
level nears. **Next** (from the feel work, S-06): the fill eased every frame
rather than stepped at 12 Hz; a pulse from 85%; a white flash and a visible
overflow on the level.
**Why**: one place answers "how far to the next" in both halves, so the
player maps it once; the word says which half's growth it is; the goal in
sight (goal-gradient) is the strongest pull in the loop.

### 4.2 The clock and the tally (under the bar)
**Done**: in an arena the clock **counts down** to what rules it ("29:30
BEFORE WHAT RULES IT COMES"), then counts up past the half hour; under a
minute it burns ember. By day the clock and kills are gone (they mean
nothing in a town); gold stays. **Next** (S-21): the night's phases named
on the clock (Dusk, Gloaming, the Witching, Ashfall, the Coming, Beyond).
**Why**: a countdown makes the half hour a goal the player is approaching,
not time passing; one number replaces the objective line repeating it.

### 4.3 Health
**Done**: low left, the heart medallion and the bar with its number, quarter
ticks, a trail that catches up (a big hit is *seen*), the shield over it,
statuses as chips (a status with no end shows no count). Below 35% the heart
beats, the bar pulses, the screen's edge bruises. **Health under the
survivor** at night: a 76 px bar under their feet with the shield, easing in
with the fight (setting "Health under you").
**Why both**: the corner bar holds the numbers and statuses an ARPG player
reads by day; the under-bar is where the eye is in a horde (Vampire
Survivors, 20 Minutes Till Dawn). Red is never alone: the number, the beat
and the bruise all say "low".

### 4.4 Skills (bottom centre)
**Done**: each skill a 67 px slot, its glyph in its school's colour, a shade
sweeping as it readies, a flash when it fires; the rank as a **numeral on a
badge** over a segmented strip (was 5 px pips); a skill ready to evolve
breathes gold until the draft offers it. Six places at night (a promise of a
full build), none empty by day. Blessings and passives as chips above.
**Why**: a numeral is read at a glance where pips must be counted (Miller,
recognition over recall); the breathing slot tells the player an evolution is
coming before the card does, so they feel clever when it arrives.

### 4.5 Hands (bottom right)
**Done**: dash charges, the draught and its count, the art's ready-ring with
its seconds; each with its key or button for the device in hand.

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

**Done**:
- Cards 320 × 452: a ribbon saying what it is and **NEW** when new to the
  build; the icon on a disc in its school's colour; the name; a rank strip
  (held dim, this one bright); the text at 18 px; tags lit where the build has
  them and **Fits your build**; a passive that a held skill needs to evolve
  says so in gold (**Evolves Butcher's Cleaver at rank 8**); rarity in word,
  colour and diamonds; its key.
- **Your build** under the cards: the skills (with ranks) in six places, the
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
Pack, Self, Arts, Journal and Map are five pages of one book: tabs on the
plate's edge, each with its key; LB/RB or [ ] turn pages with a page sound;
a page's own key, or View on a pad, closes it.
**Why**: one button (View) reaches everything; the tabs teach the keys by
showing them; turning pages keeps the player's place (Hick: five clear
choices at the top, depth behind each).

### 6.1 Pack (`Pack.cs`, **rebuilt**)
**The job**: answer "is this better?" and "what do I do with it?".
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
**Design**: who they are on the left (figure, level, experience in the day's
blue, the art in hand, what they know and what it opens, conditions); the
attributes in the middle, each saying what a point gives, and with points to
spend the **+ previews** the point's change in the standing (+1.1% faster,
+2% area); traits under them. On the right the whole standing, grouped by
purpose (staying alive, dealing death, moving, fortune); **any line, hovered
or focused, says where it comes from** (the calling, the attributes, each
thing worn by name, traits, conditions).
**Why**: PoE and Last Epoch players live in their stat sources; a number
without a source teaches nothing. Previewing a point before spending it is
error prevention (R9) and makes the choice a choice (autonomy).

### 6.3 Arts (`ArtsScreen.cs`)
**Design**: two pages (the art in hand; skills by day) on LT/RT; known arts
then those to learn, dim; the chosen one's rank, progress and facets
("rank II opens the first"). **Why kept**: it already shows what is coming
before it can be had (progressive disclosure that teaches).

### 6.4 Journal (`Book.cs`)
**Design**: paper; Quests, People, Deeds, Codex on LT/RT; reading text at
18 px; empty pages say what will be written there. **People rebuilt** as a
list and a page: those met with how each feels in a word; the one chosen
drawn as they look, trust, warmth, respect and fear as measures with words
("much fond of you"), what is on their mind and what they know you did.
**Why**: relatedness (PENS) is the town's heart; a page per person, with
their face, makes "they remember" felt rather than listed.

### 6.5 Map (`MapScreen.cs`, **rebuilt** as an atlas)
**Design**: the zone drawn from itself, as large as the screen allows
(920 px); beside it **where to go, the people, the places and what to
beware of**, nearest first, each with how far and which way ("15 m
north-east"). A line hovered or focused **glides the map to its mark and
rings it**; chosen, it draws closer. Pad: the D-pad walks the list, the
triggers zoom, Y finds you; mouse: the wheel zooms, a drag pans.
**Why**: a map is opened to answer "where is X?"; a list answers it
directly and the map shows the way, and a pad needs no cursor to use it.

---

## 7. Other screens

### 7.1 Title
The fire, the stranger, the logo (painted when the art arrives), a short
menu with an ember marking focus and its key, the last journey under
Continue; side panels take focus. **Why kept**: short (Hick) and in the
world.

### 7.2 Making a survivor
Four steps on LB/RB; rows with an icon, a name and a line; the figure by the
fire changes at once; the right panel says what a choice means; the plate
as tall as its step. Pad: A takes a choice, A again moves on; left/right
move the figure slider; on the name step a pad is offered "a name from the
road" (it cannot type). **Why**: every choice shows its consequence before
the commitment (R9), and a pad can finish creation without a keyboard.

### 7.3 Pause
A plate that fits its list; the book's keys as a reminder; settings and
controls in a panel that takes focus.

### 7.4 Conversation
The person as they look to you; speech at its pace; what you can say back,
numbered; badges for what a background or kit opens; what you cannot say,
greyed, with the reason. **Done**: focus on the lines (up and down, A or
Enter says it; the use key only answers when there is one thing to say);
**what was said just before stays above the line** (your answer, or their
last). **Why**: the pace of speech hides the thread; a recalled line means a
choice is never made blind.

### 7.5 Shop (**rebuilt**)
Three columns: their shelf, the chosen thing with its price and what it
would replace, your pack. Prices on a dark tag with a coin, **red when more
than you have**; quantity as "×3" (never confused with a price). Buy or sell
by right-click, double-click, A, or **dragging across**. **Why**: the
decision (price against worth against what you wear) is made in the middle
column, between the two things it is about.

### 7.6 Storeroom (**rebuilt**)
Stored and carried side by side with how full each is; a click, A, or a drag
moves a thing across.

### 7.7 The Last Lamp
Sleep (with its price), wait for night, not yet; refused, it says why ("You
need 5 gold; you have 2"). The morning on paper at body size.

### 7.8 The Wayfinder's table
Three maps as cards: tier with diamonds, name, who holds it and what rules
it, their bane, the oaths (asks, gives, what answers them), Enter at the
foot. The plate fits.

### 7.9 The arena's end
The verdict, the name, the tally **counting up** one after another (time,
slain, ember, past the half hour), "your longest yet", what comes out
against what stays. **Next** (S-16): the cause ("slain by a Kerchief
cutthroat at 24:13"), the near miss ("6 minutes from Redcowl"), the run's
peak. **Why**: the end of half an hour is what the player remembers of it
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
| Bars that flow; glow from 85%; flash on the level | feel S-06 | Adopt (4.1): presentation only |
| The night's phases named on the clock | feel S-21 | Adopt (4.2) with the countdown |
| An end screen that tells the run's story | feel S-16 | Adopt (7.9); the cause needs the killer recorded in `ArenaResult` |
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

1. The art (`UI_ART_BRIEF.md`); every plug-in point loads by name.
2. The feel work's interface pieces (section 9), bars that flow first.
3. Text size setting (needs the HUD anchored rather than placed at 1080p).
4. Hold-to-read detail on cards and items (pad Y, keyboard Alt).
5. The remaining accessibility settings (section 8).
