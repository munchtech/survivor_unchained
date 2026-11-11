# Handoff: loot and itemisation

For the next loot lead. Read this, then `docs/team/README.md`, then `docs/team/loot.md` (one-page
status), then `docs/design/LOOT_DESIGN.md` (the approved design). Branch
`worktree-agent-a9a9c345a35e1fcad`; merge `origin/claude/vigilant-galileo-l6jqyx` first.

## TOP BLOCK: M9 loot lead 1 (10 November 2026), branch loot-m9

State: MR READY (see the inbox line for the sha). The M9 list is done; nothing is half-built.
Merge `origin/claude/vigilant-galileo-l6jqyx` first. M5 already had captains as carriers
(`Encounters.Carried`), ground loot, the world-tier multipliers and the Prologue Warden hook; M9 did
not rebuild them.

Done, each with tests (`LootM9ZoneTests`, `LootM9WardenTests`, `LootPlusSkillTests`):

1. **Tally retired outside the arena.** `StoryNight.Gear()` no longer sets `Tally`; materials fall on
   the ground and `Journey.Gather` takes them. Only `ArenaRun.cs` still tallies.
2. **"+1 to a skill" affixes.** `AffixDef.Plus`, `ItemDef.Plus` (items.json key `plus`),
   `loot.json` `plusSkills` / `plusNames`; Ring, Amulet, Head, Relic suffixes, rarity 2 and up,
   rolled only when the calling can carry the skill (weight 0.35); no grades, not bindable. The one
   seam is `SkillBook.RankOf` (= Rank + `Character.SkillPlus`, capped at `Weapons.MaxRank`); WickBook,
   LampBook, Journey.Teach and `Battle.SetRank` all read it. A skill rank is its lit wick lamps, so
   +1 is one more lamp. **M7's points system folds in here**: change `RankOf` and nothing else moves.
   `Battle.SetRank` is deliberately not in the build-step journal.
3. **The Ford-Warden's Legendary, designed.** `DropCtx.Grant` names an item; the first roll makes it
   a Legendary if not yet owned (resets LootDebt, sets `FirstLegendary`). `Prologue.WardenGrant` =
   `fordwardens_evening_chain` (Amulet, `plus` heroic_leap 1, its landing rings again in holy light,
   +12 armor and more max health; health scales with item level). It has no `dropsFrom`, so it never
   falls by chance. **Its description and lore are PLACEHOLDERS for the story lead.** The Warden's
   Lamp-Iron (`wardens_lampiron`) is a separate story trophy, left alone.
4. **Leaving a zone.** `Journey.Abandon` (called from `ZoneRuntime.Dispose` in combat zones) moves
   shown rarity 2+ pickups to the first free stash slot and releases them; the rest stay lying. A full
   stash leaves the item lying (unlike `Gather` it breaks nothing down).
5. **Tier weights tested** (I-IV: Rare+ and Legendary share rise, item level +5 at III, +10 at IV,
   ignored when `WorldTierOn` is off). No numbers changed.

Cadence (zone sim, tier II, human bot, `tools/scratch/m9_zone_t2.md`, 2 seeds): the Warden dropped the
Evening Chain 2 of 2 runs (the certain Legendary: on target). Per run the Low Ford gives 10 shown gear
from 16 packs and 148 kills: 0.63 shown per pack against ARPG.md 7.1's 25 per 40 packs = 0.625, so the
drop rate per pack is on target and `loot.json` was not tuned. The per-hour columns read "90 shown an
hour, an upgrade every 1.1 min" only because the zone is 6.3 minutes long (scaled 9.5x); that is the
zone length, not the rates. The upgrade column also counts the first piece of every empty slot (the
bot wears nothing), so it overstates; re-measure once the first hour is an hour of ground.
A 8-seed, three-bot run (`--bots human,deft,standing --seeds 8`) was not completed: the first
attempt's runner produced nothing; the 2-seed human run takes seconds, so rerun it if wanted.

Watch-outs: a Boss roll can still drop a second random Legendary on its later rolls. Known test flakes
(pass alone): `WearTests` migration race, `DraftCardFitTests.Every_draft_card_fits_its_card`,
`ContentTests.Every_item_has_an_icon_a_value_and_words` once. `LootTests.Every_legendary_changes_how_you_play`
exempts the Evening Chain (it demands `DropsFrom`).

Cost: helpers about 215k subagent tokens plus orchestration, well inside the 0.6M line.

## The owner's words (5 October 2026)

- "a very intuitive inventory management is smart. things that can be tucked away like spellbooks
  or stuff is useful, inventory management is a very real concern in these games so we need it, but
  we also don't want to feel cheated with things that should stack, or should not even take up
  inventory spots directly either."
- "we also need to make an item filter and more poe/diablo style drops that can be seen or hidden
  better with better sounds on quality items and we don't have any legendaries (extremely rare) yet
  do we? or sets. ... should have some legendaries even at low lvls for huge dopamine spike."
- "theres far too many common items that we don't need. common items in higher zones can be better
  than greens or even blues (or way later commons even better than early purples) but in general
  items can drop a little less, their drops replaced maybe with crafting stuff."
- "item drops should *mostly* feel good." The bar: "we are striving for perfection".

## The brief

Loot and itemisation lead. Design first (`docs/design/LOOT_DESIGN.md`: research, tiers with
legendaries and sets, item level and zone scaling, drop rates, stacking and slotless stores, the
filter, presentation, loot across story arenas, maps, survivors arenas and crafting), then the rules
in logic with tests, then content (first Legendaries, some early; one or two sets; trimmed commons).
Each Legendary must change how you play and fit the world (`docs/STORY_BIBLE.md`). Legal: our own
art and sound only. Heavy work takes turns (`tools/turn.py take godot "loot: ..."`). Comments
short prose saying why; `dotnet test` in `godot/tests` before every commit.


Older blocks: history/loot.md (grep by keyword, never read whole).
