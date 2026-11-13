# bd-ui (wave 2): the build's screens (coordinator #10, 13 Nov 2026)

Read `common.md` first, except: this lane DOES shoot pictures, so its worktree gets the `.godot/imported` seed (`wt_new.ps1` without `-NoImport`), it takes Godot turns (`tools/turn.py take godot ...`), and it has ONE `su-lead-max` judge at `effort: "max"` (the HUD is always seen). Also read `docs/team/ui_design.md`, the HUD's "Drowned Girl" centerpiece notes there, and README "The finish line" (judge at the game's cameras, 1:1, whole frame first: "would it ship in a AAA game?").

What it ships, the Warden only, on top of merged bd-keys (and bd-sockets when it lands):
1. **The 4-key bar:** the basic attack in key 1, the skills opening by the ladder (BUILD_UNLOCKS), each key's cooldown or resource read at a glance; dash, the Flare and the swap shown apart from the 4.
2. **The 3 auto slots** (always on, opening at 1/7/10) and item auto skills stacked beside them, uncapped, without crowding the bar.
3. **The stance:** which weapon set is up, what the stance does to her 4 skills (shield = block/stun, twin blades = faster/bleed, mace = stagger), what it costs, and the swap strike's internal cooldown, all readable in a fight without reading text.
4. **The socket panel's look pass:** bd-sockets builds it plain; this lane makes it look right (sockets opening at skill rank 3 and 6, gems that fit, the Union join at a lamp-post).
5. **A collect-to-unlock wardrobe with dyes:** looks collected from gear she has found, worn over any piece; dyes as data. The cloak may return here as customization, never as a drop. Her only; gear cuts per gender (no cross-gender swap).

The UI lead owns every element's look (the owner, 26 Oct). Research how Diablo IV, Last Epoch and PoE2 show a 4-key bar, auto skills and a weapon swap, then make it ours (no generic fantasy ornament spread evenly; "more borders are not better").

Files: `godot/src/Ui/GameHud.cs` (the bar near line 1700 and the union row near 986), `godot/src/Ui/` screens, `godot/src/Game/GamePostMenu.cs`, `src/Ui/PostScreen.cs`. Stay out of `godot/logic/Sim` except read-only.

Judge: one fresh `su-lead-max` judge on contact sheets at 1:1 from the play camera (a dense fight, a stance swap, a level-up opening a key) and the screens (sockets, wardrobe), with the owner's words above and a checklist. 3 rounds per item at most. Done = judge PASS, suite green, `MR READY bd-ui@<sha>`.
