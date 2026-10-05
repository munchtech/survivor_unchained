# UI research: the pack, the self, the arts and the counters

The UI design lead's study, written before any new drawing. It covers how the best action RPGs and RPGs solve the screens we keep getting wrong, the principles drawn from them (each with its reason), and our own layout for each screen. It studies only. We copy no game's art, frames or layouts one to one.

## Why

The owner, on the pages as they stood:
- "those borders are just ugly, adding more of them dosn't make them better";
- the inventory and the character page "not look rooted in ui research", "ai looking", in need of "considerable help".

The coordinator's diagnosis:
- every panel, card and slot carried the same heavy bevelled frame, so boxes sat inside boxes and nothing had hierarchy;
- empty states took the space (six empty trait boxes, 48 empty storeroom cells, an empty "Read closely" panel, four empty facet cards);
- a flat muddy brown with ornament spread evenly over it.

## What the best do

**Diablo IV**
- **Layout.** The inventory and the paper doll share one panel on the right of the screen, with the world left in view. The doll is the rendered character with the equipment slots in two columns flanking it, roughly at body height: head, chest, gloves, legs and boots on one side; amulet, rings and weapons on the other. The bag is a compact grid of tall cells with tabs by kind.
- **Rarity.** Colour carries it (name, cell tint), backed by a second cue in the border decoration for accessibility. The team toned the icon backgrounds' brightness and saturation down, so rarity reads without shouting.
- **Comparison.** Hovering an item shows its card beside the equipped one, with up and down marks on what changes.
- **Stats.** The attributes come first, then a long list grouped under plain headings, with a hover saying where each number comes from.
- **Vendors.** The vendor's wares sit on the left with buy, sell and buyback tabs, and your own bag stays on the right.

**Path of Exile 2**
- **The doll.** Slots are arranged as a body: the helmet over the body armour, a weapon either side (two sets, I and II, a two-hander filling both), and gloves, boots, belt, rings and amulet where they are worn. It sits above a 5 by 12 grid of 60 cells.
- **Tooltips.** Very dense, but strictly ordered: a header coloured by rarity, then sections divided by thin rules (base, implicit, explicit), with comparison against the equipped item on demand.
- **Stash and vendor.** These open on the left half, so the grid you are moving to or from is always beside your own.

**Last Epoch**
- **The doll.** The same body-arranged doll over a grid.
- **Rarity.** Seven colours, used everywhere the same way: white, blue, yellow, purple (exalted), orange, green and red. An exalted affix is purple inside the tooltip too, so the colour means one thing at every scale.
- **Tiers.** Affix tiers are shown in the tooltip, so the player reads quality, not only kind.

**Grim Dawn**
- A dense doll of many slots around a centred silhouette, with bags as tabs.
- The character sheet splits primary attributes (three, large, with a plus when a point is free) from derived stats (tabbed lists).

**Baldur's Gate 3**
- **Inventory.** A large rendered character with equipment in two columns flanking the figure and weapon sets below. The bag is a list or grid with sorting and filters.
- **Character sheet.** Six abilities in one tight row, then features and resistances in quiet columns. Hierarchy comes from type size, spacing and tonal panels on a dark ground, with thin gold rules, not frames in frames.
- **Tooltips.** Nested: hold to expand a term.

**Elden Ring**
- **Equipment.** Slots grouped by kind in a plain grid, with the selected item's detail beside it.
- **Preview.** The strongest of the set. Whenever a level is spent or an item hovered, every derived number shows its current value beside its new one, blue where it rises and red where it falls, before anything is confirmed.
- **Restraint.** Translucent dark panels, small serif type, hairlines, almost no ornament.

**Hades II**
- **Locked content.** Shown as a dim silhouette with its requirement, never as an empty box.
- **Cards.** Rarity and kind ride on the card's frame colour and a small mark. The large illustrated cards are the screen's one ornamental thing; everything round them is quiet.

## Principles (with the reason for each)

1. **One frame per screen.**
   - What: the window may carry the house's ornament; nothing inside it does. Hierarchy inside comes from spacing, type size and weight, two or three tonal planes, and thin rules.
   - Why: a frame says "this is a thing". When everything is framed, nothing is (BG3, Elden Ring and D4 all frame the window and almost nothing in it).
2. **Colour means something.**
   - What: neutral by default. Colour is spent only on rarity, on state (ready, locked, better, worse) and on the one primary action.
   - Why: this is the first thing that lets the eye find the rare ring in a grid (Last Epoch, D4).
3. **The figure is the hero of the character's screens.**
   - What: she is drawn large, and the gear slots are placed where the gear is worn.
   - Why: a slot by the head reads as "helm" before its glyph is read, and the doll is the player's pride in the build (PoE2, D4, BG3).
4. **Empty is quiet.**
   - What: an empty slot is a recessed tile with a faint silhouette of what goes there, with no border and no colour. A filled slot carries its rarity.
   - Why: it makes the filled ones pop, and an empty pack reads as calm rather than as a wall of boxes.
5. **Empty states collapse.**
   - What: a section with nothing in it is one line ("The pouch is empty: the night's fights fill it"), never a panel.
   - Why: space is for what exists, and a big empty panel reads as unfinished.
6. **Grids are sized to capacity.**
   - What: show the cells you own, in compact rows; growth is shown as more rows or another shelf, not as a sea of locked cells.
   - Why: 48 empty cells on day one is noise, and the count ("8 of 24") does the explaining.
7. **Details live in the tooltip.**
   - What: no permanent "Read closely" panel. Hover (or focus) shows the card beside the thing, with the equipped item's card beside it, and the deltas marked better or worse.
   - Why: a fixed inspect panel is empty most of the time, and comparison is the decision the player is making (D4, PoE2, Last Epoch).
8. **Tooltips are ordered and ruled.**
   - What: name and rarity on top; then kind and base; then what it does, grouped and divided by thin rules; then its price or its seams; the key prompts last.
   - Why: a fixed order is read without effort (PoE2's discipline, kept short).
9. **Numbers line up.**
   - What: stats sit in compact columns, the label left and the value right-aligned in tabular figures, grouped under plain headings, with a hover giving each number's sources.
   - Why: aligned columns are scanned, not read (BG3, D4).
10. **Spend with a preview.**
    - What: a free point shows a plus. Pressing it previews every derived number as current and new, green up and red down, and the spend is confirmed or undone as a whole.
    - Why: the player sees the consequence before committing (Elden Ring's level up).
11. **Progress is a track.**
    - What: levelled choices (traits, ranks) are drawn as a line of nodes: taken (filled, named), next (lit, with its level), and later (small and dim, the level only).
    - Why: it shows both the past and the next goal in one row, where empty boxes show neither.
12. **Locked is a silhouette with a reason.**
    - What: an unlearned art or locked facet is a dim mark with one line saying how it is earned.
    - Why: it promises without filling space (Hades II).
13. **Your goods and theirs side by side.**
    - What: at a counter or the storeroom, their side is on the left and yours on the right, in the same grid language, with prices on the tiles.
    - Why: moving between two grids is the task (D4, PoE2).
14. **Irreversible acts are held.**
    - What: breaking down, unmaking and steeping fill a press over about 0.8 s, with no second dialog.
    - Why: it's safe without nagging, and the same on a pad and a mouse (the salvage pattern in D4 and Destiny 2).
15. **Pad and mouse are equal.**
    - What: every screen is walked by focus, with the prompts for the device in hand along the foot; hover and focus show the same tooltip.
    - Why: the game is played on both.

## Our screens

The greyboxes are in `docs/ui_review/greybox_*.png` (1920x1080). Each screen's choice, and why:

- **Pack (side panel, right, about 1040 px; the world stays in view on the left).**
  - The doll on the left of the panel: her figure about 560 px tall. The slots sit where they are worn: head, cloak, body and relic down her left side; amulet, weapon, off-hand and the two rings down her right.
  - Under the doll, six key numbers in two aligned columns.
  - On the right of the panel: the pack as a compact 6x4 grid ("8 of 24"), a Sort, then the pouch as one row of stacks (collapsing to a line when empty), then the purse.
  - No filter tabs at 24 cells, and no inspect panel: the tooltip with compare does that work.
  - Why beside rather than above: at 1040 px both fit at full size, and the eye moves left and right between an item and its slot.
- **Self (a page of the day's book).**
  - She stands large on the left (about 860 px tall), with her calling, origin and level beneath her.
  - On the right, from the top:
    - the four attributes as one tight row (number, name, what a point gives), with the plus and the preview when points are free;
    - the traits as a level track (taken, next, later), with the traits given for deeds as named chips after it;
    - the stats in three aligned columns (staying alive, dealing death, moving and fortune), showing deltas while a spend is previewed.
- **Storeroom (two side panels, theirs left and yours right).**
  - Rook's shelf is a 6x4 grid, its count in the head. More room comes as another shelf, a second tab (proposed: bought from Rook, a gold sink, for the crafting lead to price).
  - Your pack panel is the same as in the Pack, without the doll.
- **Trader (two side panels).**
  - On the left, the merchant in a compact head (a small portrait, name, standing and prices on one line, what they last said) over their wares as a grid with prices on the tiles. Tabs: Wares and Buy back.
  - On the right, your pack panel.
  - The price shows on the tooltip too, red when you can't pay.
- **The bench (crafting; three columns, the crafting lead's content).** The person, compact; the anvil, the main column (the piece's head, its seams as rows, the crafts for the chosen seam); then gear, pack and pouch with the purse. Break down, unmake and steep are held.
- **Arts.**
  - The arts known as one list of medallions on the left; the art in hand large on the right, with its rank track.
  - The facets as a row of compact entries (taken, open, or locked with "opens at rank II"), not tall empty cards.

## Rules for the art pass

- **The window.** One ornamental piece per screen: the window (or the side panel's edge and head).
- **Panels inside.** Tonal planes only: three steps of the dark, never a frame. Thin rules divide sections.
- **Slots.** Recessed and quiet when empty; the rarity colour as the tile's tint and edge when filled.
- **Type.** Cinzel for titles only; Alegreya for words; Alegreya Sans for numbers and labels, with tabular figures for any column of numbers.
- **Colour.** Neutral and warm-dark. The ember and gold go on the one primary action and on focus, nowhere else.

## Sources

- [Diablo IV Quarterly Update, February 2020 (UI design)](https://news.blizzard.com/en-us/article/23308274/diablo-iv-quarterly-updatefebruary-2020) and [RPG Site's summary](https://www.rpgsite.net/news/9492-diablo-iv-discusses-ui-design-coop-controller-support-and-cannibals-in-first-quarterly-update): rarity by colour plus a border cue, toned-down icon backgrounds, the inventory rebalanced.
- [Diablo wiki: Inventory](https://di.diablowiki.net/Inventory): the doll and the bag on one page.
- [PoE2 wiki: Inventory](https://www.poe2wiki.net/wiki/Inventory), [Equipment](https://www.poe2wiki.net/wiki/Equipment) and [Weapon set](https://poe2wiki.net/wiki/Weapon_set): the 5x12 grid, the body-arranged doll, weapon sets I and II.
- [Last Epoch rarity colours (Upcomer)](https://upcomer.com/last-epoch-loot-rarity-colors-explained) and [tiers 6 and 7 (forum)](https://forum.lastepoch.com/t/introducing-tier-6-and-7-item-affixes/22279): seven rarities, and exalted affixes coloured in the tooltip.
- [Elden Ring: Level (Fextralife)](https://eldenring.wiki.fextralife.com/Level) and [RPG Site on stats](https://www.rpgsite.net/feature/12444-elden-ring-stats-attributes-max-level-explained-what-to-level-up-first): blue and red previews of every derived number before confirming.
- [Grim Dawn: Character Basics](https://www.grimdawn.com/guide/character/character-basics/): primary attributes and derived stats.
- Baldur's Gate 3 and Hades II: studied in play and from screenshots. Players' notes on BG3's inventory ([Steam discussion](https://steamcommunity.com/app/1086940/discussions/0/3471730015126690544)) warn about bag clutter; we keep one grid.
