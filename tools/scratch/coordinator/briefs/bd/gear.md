# bd-gear: 8 slots, great drops, small sets, the crafting gamble

Worktree `C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\bd-gear`, branch `bd-gear`. Read `briefs/bd/common.md` first.

**Build (BUILD_DIRECTION "Gear" and round 8):**
1. **8 slots:** weapon, offhand, head, body, boots (today `Feet`), amulet, two rings. **Cut** belt, legs, cloak, bracers, shoulders, hands and relic from `ItemKind`/`EquipSlot`/`Items.Places`, `items.json` (cloak 5, relic 5, legs 4, bracers 4, shoulders 4, belt 3, hands 1 item today), `Wear.cs` groups, crafting, loot tables and filters, and every C# reference (~98; the UI's doll/forge rows need only the edits to compile and show 8 slots; no look work, bd-ui owns that). Body armor covers the whole body except the head, like a matching set: fold the cut pieces' stat budget into body, head, boots and jewellery so her total power at a level is unchanged (test it). Saves: map worn cut pieces to the stash or drop them cleanly; never crash.
2. **The relic's skill-granting affixes** (`of_motes`, `of_the_gyre`, `of_cinders`, ... `AffixDef.Grants`) move to amulet and rings only.
3. **Great drops:** uniques that **rewrite a skill**, **enable a build**, or **grant an auto skill** (data; bd-keys makes item auto skills stack uncapped in battle). A drop that grants a skill she **cannot get any other way** is the big moment: give it its own drop tier/event and wire the existing legendary sound and beam as its stand-in; route the final sound and look to bd-ui in your report. Author at least 3 Warden-usable uniques of each kind.
4. **Sets:** small, **2-3 pieces**, minor perks, never the build. Re-cut any set that leaned on cut slots.
5. **Crafting:** today's heat stays as the safe deterministic steps; add **one rare gamble** (a consumable or a forge action) for a shot at a perfect piece, with a real chance to lose value. Deterministic under a seed, tested.
6. **Item levels** follow the new cap of 75: `Loot.Rules.MaxLevel` 40 -> 75 with the item-level curve stretched to match (bd-ranks owns `Character.MaxLevel`).
7. Single-player now; keep anything co-op would need (per-player drops, no global singletons for loot state) unbroken.

**Your files:** `godot/logic/Rpg/Items.cs`, `godot/data/content/items.json`, `godot/logic/Rpg/Wear.cs`, `Crafting.cs`, `Loot.cs`, `LootFilter.cs`, `Inventory`/save migration, `godot/logic/Rpg/Character.cs` (ONLY the affix-roll region ~230-270), glyphs/loot data, UI files only for compile-level slot edits, and the tests for all of these.
**Not yours:** `Battle.cs`, `SkillBook.cs`, `Weapons.cs`, the loadout region of `Character.cs` (bd-keys), `Character.MaxLevel`/XP/`LampBook` (bd-ranks).
**Acceptance:** `EquipSlot` has exactly the 8; no item, affix, loot table or test names a cut slot; Warden power-at-level within 3% of today at levels 5/10/20 (test); granting affixes roll only on amulet/rings; each great-drop kind exists for the Warden; the skill-grant drop raises its own event; sets are 2-3 pieces; the gamble is seeded and tested; an old save with a cloak and a relic worn loads. Suite green.
