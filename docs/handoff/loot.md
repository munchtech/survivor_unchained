# Handoff: loot and itemisation

For the next loot lead. Read this, then `docs/team/README.md`, then `docs/team/loot.md` (one-page
status), then `docs/design/LOOT_DESIGN.md` (the approved design). Branch
`worktree-agent-a9a9c345a35e1fcad`; merge `origin/claude/vigilant-galileo-l6jqyx` first.

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
