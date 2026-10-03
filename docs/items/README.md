# Items: the itemization plan

A design plan for the whole of Survivor Unchained's gear, low to high: what
items are for, how they are built and found and changed, how they grow, what
they are, how they look on the survivor, and how to build it all in this
codebase. It is a plan for the main session to build from: **nothing here is
in the game yet**, and every number is a proposal for the balance lab.

## The files, in reading order

| # | File | What it is | Read it if you are... |
|---|---|---|---|
| 1 | `VISION.md` | What items are for in this game, the feel from low to high, fourteen principles, the tone, what to avoid. | anyone; start here |
| 2 | `SYSTEM.md` | The machine: what exists today, the shape of an item, rarities, slots, bases and tiers, the stat model, affixes and item level, Marks, Named items, sets, Storied, notches and sigils, and the synergies with callings, schools, blessings, oaths and the ember build. | building it |
| 3 | `PROGRESSION.md` | The curves: level bands, the power budget against creature scaling, affix values by grade, upgrade cadence, **how gear and the ember stay in balance**, what keeps the top fresh. | the balance lab |
| 4 | `ACQUISITION.md` | Where gear comes from: arena drops by tier, oath and people; day drops, places, quests, the nemesis; items opened by story choices; pity, duplicates and target farming; shops; the toll lots. | building drops, writing content |
| 5 | `CRAFTING.md` | Materials, heat, Brannoc's forge, Wenna's tinctures, the binders' book, Chid's shrine, the slurry gamble, sigils, the tailor; the gold economy; how the story can take a crafter away. | building crafting |
| 6 | `CATALOGUE.md` | The content: bases per slot and tier, about seventy affixes with ranges, thirty-three Marks, Rare name lists, thirty-two Named items with powers, homes and lore, ten sets, twelve sigils and twelve Watchwords, example rolls. | writing content |
| 7 | `VISUALS.md` | How gear changes the survivor: material tiers (rags to relic), slot by slot and calling by calling, what reuses the Quaternius, KayKit and heroine pieces and what needs modelling, the night glow, dyes and the tailor, icons and loot beams. | doing art |
| 8 | `IMPLEMENTATION.md` | Five phases mapped to the code: schemas, the save migration, UI, tests, what to build first, and the owner's decisions. | planning the work |
| – | `RESEARCH.md` | The genre research behind it: Diablo II–IV, Path of Exile 1–2, Last Epoch, Grim Dawn, Torchlight, Titan Quest, Lost Ark, Hades, Vampire Survivors, Elden Ring, Darkest Dungeon; the chase, fatigue, pity, target farming; 28 lessons, with sources. | wondering why |

## The idea in one paragraph

Gear is what the survivor keeps: the ember is borrowed each night and lost each
dawn, so items are the only power that crosses between the day's story and the
night's arena. By day gear is the survivor's strength and their standing in the
world (a wolf-fang necklace is a statement to a wolf). By night it **shapes the
ember without owning it**: the weapon brings a skill into the arena at up to
rank 4 and an Edge that rewards drafting its kind; gear damage is *increased*,
so it adds with the ember's passives rather than multiplying them and its share
falls as the night's build grows; a few capped "kindled" affixes start the
ember sooner, add a card, or stand in for a passive in an evolution. Above the
Rares sit Marked items (a power burned in by the dark), Named items with homes
you can hunt, small sets in a people's colours, and Storied items that carry a
history the world wrote. The look follows the gear, rags to relic, and the best
of it burns only at night, as the survivor does.

## Top ten recommendations

1. **Give items grades, ranges and an item level** (`SYSTEM.md` §6). Move the
   affixes into data with six grades gated by item level and a range within
   each. Today two drops of the same rarity are identical and depth means
   nothing. This is the foundation everything else stands on.
2. **Make weapons the centre: bases in five tiers that roll, with the Edge**
   (`SYSTEM.md` §4.2). The weapon is a skill (keep that). Give it tiers (Worn,
   Sound, Wrought, Legion, Heartwrought), affixes, a starting rank (capped at
   rank 4 in the arena) and an Edge, a "more" multiplier on its own kind of
   skill. That makes weapon upgrades the biggest moments, keeps damage in step
   with creature health, and ties the day's gear to the night's draft.
3. **Hold the line between gear and ember with rules, not dampeners**
   (`PROGRESSION.md` §5). Gear damage is *increased*, never *more*, except the
   Edge and one per named power. Gear skills stop at rank 4. Kindled affixes
   are capped. Gear never grants blessings or evolutions. The targets: gear is
   ×3 of a survivor's power at minute 0 and settles to ×1.5–2 by the half hour.
   The balance lab should test this before content is built on it.
4. **Drop by people, oath and tier, and gather it in a spoils screen**
   (`ACQUISITION.md` §2–4). Replace the nine-base `PlainGear` list with people
   tables, ilvl from the arena tier, and a loot identity for each oath. Gather
   arena drops into the run's spoils, shown at the end with keep and salvage.
   Choosing a map becomes choosing what to hunt; no pack Tetris mid-run.
5. **Ship presentation and a filter with the first drops** (`IMPLEMENTATION.md`
   phase 2). A five-layer tooltip, compare in the arena's terms, beams by
   rarity, and a toll bell for Named items heard across a horde. Add a simple
   loot filter with auto-salvage and a materials pouch. Presentation is half
   the reward, and the 24-slot pack needs relief.
6. **Make the figure follow the gear, cheaply** (`VISUALS.md` §2–3). Use one
   material-tier parameter in the person shader (rags, leather and mail, plate,
   Legion lacquer) plus lists of which pieces show. The woman survivor's
   outfits are already many separate pieces (pauldrons, vambraces, greaves), so
   showing more of them as gear climbs is mostly data. The KayKit helmets, hats,
   capes and shields can be attached. Today armour changes nothing on the
   figure.
7. **Add the Marked layer and the binders' book before more uniques**
   (`SYSTEM.md` §7, `CRAFTING.md` §5). A Mark is a rule burned into a Rare
   ("your dash leaves a ring of holy fire"). Every Mark seen is kept in
   Vonnra's book, and the best copy upgrades the page. This gives the middle
   game build-making powers and makes duplicates progress (Diablo IV after
   Loot Reborn, Kanai's Cube).
8. **Give every Named item a home, a price and a line of lore that respects
   the acts** (`CATALOGUE.md` §6, `ACQUISITION.md` §6–7). Thirty-two to begin.
   Each is hunted from a people, a boss, a place or a choice, and some exist
   only on one branch of the story (Pelt of the Pack or Greymuzzle's Collar).
   Back them with a visible pity tally at the Wayfinder's table and a test that
   no lore is seen before its act.
9. **Craft through the town's people, transparently, with heat and no
   ruin** (`CRAFTING.md`). Brannoc tempers and reworks, Wenna's tinctures
   guarantee an affix, Vonnra keeps the book, Chid consecrates and Rav
   tailors. Every craft shows its cost, chance and range first. Heat runs out,
   but a failure never destroys the item. When the story costs the survivor a
   crafter (Brannoc, if they lie to him about Nell), the service moves to
   someone worse rather than vanishing.
10. **Keep sets small and let history make the best items** (`SYSTEM.md` §9).
    Use 3- and 4-piece sets in a people's colours, with at most one "more" each
    and a ring that frees a slot. Add Storied items: a Named item lifted a
    grade by three deeds the world writes down (a story fight won with it, the
    item taken back from your nemesis, a boss beyond the half hour). That makes
    the top of the chase personal, not only rare, and it uses the `History`
    field the save already has.

## Status

Written by a design session on branch `claude/cloud-itemization`; no game code
or content was changed. Numbers are proposals; another session is tuning combat
numbers, and its results should overrule anything here that disagrees.
