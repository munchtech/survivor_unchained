# bd-ui2: the build screens bd-ui left (coordinator #11, 13 Nov 2026)

Read `common.md` first, then `ui.md` (same rules: seeded worktree, Godot turns via `tools/turn.py take godot ...`, ONE `su-lead-max` judge at `effort: "max"`, judged at the game's cameras at 1:1, whole frame first: "would it ship in a AAA game?", at most 3 rounds per item). Also `docs/team/ui_design.md` and RESUME's COORDINATOR #11 block. bd-ui merged at integration `e798d2d64`: the 4-key bar, socket panel, gem drop and wardrobe are DONE and judged. Don't redo them; match their language (the bar's glyphs, the panel's rows, the wardrobe's panel).

Worktree `.claude/worktrees/bd-ui2` (branch `bd-ui2` from `e798d2d64`, seeded). The Warden only, her only.

Ship, each judged:
1. **The 8-slot paper doll** in the Pack (weapon, offhand, head, body, boots, amulet, two rings; BUILD_UNLOCKS "Gear slots"). Every slot shows what she wears. Known bug: the Pack doll's material path is broken (a grey pauldron).
2. **The stance swap's visuals:** what the swap looks like in a fight, its key binding shown, and the swap strike landing; the stance discs from bd-ui are the HUD half. Readable without text.
3. **The gift drop:** the moment a unique that grants a skill she can't get otherwise drops (bd-gear's uniques with `ItemDef.Auto` or a skill grant). It needs a look and a sound, above a normal unique and in the gem drop's family. Use the sound library or an existing cue; ask the coordinator before any paid generation.
4. **The Quench row at Brannoc's forge** (bd-gear's crafting: heat plus a rare gamble). Make it readable, its cost shown, and the gamble's odds honest.
5. **The subclass road page** (bd-ranks: her road at level 6, changeable at a lamp-post, its passives and maybe a skill), and **character creation without the road row**, since the road is chosen in play.
6. **Small fixes:**
   - The selected Union row must read as selected.
   - If the level-10 card still says "A NEW KEY", fix it: level 10 opens auto slot 3.
   - Check the pad's Y/A break concern and the weapon glyphs from bd-ui's report.
   - Remove the unused `Small()` if nothing needs it.

Files: `godot/src/Ui/` screens, `GameHud.cs` (swap only), `GamePostMenu.cs`, `PostScreen.cs`, the Pack and forge screens, character creation. `godot/logic/` read-only, except a data hook a screen truly needs; name it in the report.

Out of scope, routed elsewhere (don't fix, don't fail a judge on them):
- her skin's look under look_day;
- outline specks;
- dye shader finish and the greaves' metal finish;
- gear data looks (Forged Cuirass, the shared skirt);
- foliage under the depth of field.
The judge passes or fails this lane's own work; list anything new of that kind in the report with its frame.

Hand off at ~200k (`HANDOFF READY docs/handoff/bd_ui2.md on bd-ui2@<sha>`). Done: every item judged PASS (or closed by the coordinator's 1:1 check for a measured layout fix), suite green on the final tip with the integration branch merged in, `MR READY bd-ui2@<sha>`.
