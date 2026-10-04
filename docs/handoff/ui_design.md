# Handoff: UI design and the UI merge

For the next UI design lead of Survivor Unchained. This file and the repository are all you get.
Read `docs/team/README.md` first, then this, then `docs/team/ui_design.md` (the one-page status).

Branch `worktree-agent-a5629aff0f215ea4a` (pushed; no PR; the main session merges it). Worktree on this
PC: `C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a5629aff0f215ea4a`.
The previous handoff (the second design pass) is in git history:
`git show c14b3a2:docs/handoff/ui_design.md`. The art pass's is `docs/handoff/ui_art.md`.

---

## 1. The owner's bar, in their words

- "AAA standard", "strive for excellent, above and beyond", "I don't want to polish, I want to create
  perfection", "Do we have soul?". Never settle; remake rather than polish; verify at full resolution.
- On the first pass: "the literal exact same shapes" (a huge empty parchment square, a big dark box
  with small items, a wall of text in a box; nothing said "this is Survivor Unchained").
- Answers to the open questions (relayed by the coordinator, this session):
  - **Pausing**: "full page screens should pause the world in arena combat, otherwise no. and full page
    screen in general aren't really great on some things". Reconsider, screen by screen, which should
    be full page at all; where it is not the best design (things glanced at or tweaked mid-play) use a
    panel or overlay that keeps the world in view; decide from the research; record why.
  - **Unwalked map land**: "i don't care about dark or blank parchment but it needs to look better".
  - **Self** stays its own screen, not merged into the pack.
  - **Painted art**: "painted art is generally better right? ... I want the best". Painted, modelled
    art wherever it is better (most frames and ornaments); code-drawn only where it truly serves
    better (dynamic arcs, numbers).

## 2. The brief

The coordinator's task for this agent:
1. Read both predecessors' handoffs. Merge `origin/claude/vigilant-galileo-l6jqyx`, then the design
   branch (`worktree-agent-ad1a039caf3923eec`), then the art branch (`worktree-agent-abd496197891ea843`).
2. Reconcile so the redesign's composition and the painted art work together.
3. Register the art the new layouts ask for by name.
4. Screenshot every screen at 1920x1080 with mouse and with pad.
5. Fix what is broken (the Verge map's view past the zone's edge; the unwalked dark letting the
   drawing through; pad focus routes not walked).
6. Push; message the main session ("UI merge pushed: <branch>@<commit>") and the UI art lead.
Then: the screens not yet in the new look; UI_DESIGN.md, UI_ART_BRIEF.md and ui_assets.json up to
date; the open questions. Keep `docs/team/ui_design.md` as a one-page status. Later: merge the
integration branch again (it had moved), then act on the owner's answers above, the re-shots and
focus checks, and the chapter's end once seen on screen. Hand off past about 500k context.

## 3. Done (all pushed)

| Commit | What |
|---|---|
| 0f8e734 | The merge: art fills the layouts (globe stays health; draft keeps crested card + medallion + glow under the painted card; map full bleed; well/slab/header/banner tiled; pillar and console registered) |
| ed542b3 | Map pan held so the paper covers the view; unwalked dark opaque; ink clipped; draft words 40 px inside painted cards; slot captions inside painted wells; creation/pause columns wear the painted plate; title rule; Self standing changed in place (pad focus no longer lost); medallion/globe ring hooks; `--navcheck` (`Nav.Audit`); brief 4.9; UI_DESIGN second pass |
| c14b3a2 | Merged the integration branch again (faabea9): a fast-forward for it |
| 40a0b71 | Pause only in a fight (`zone.Combat`) or the pause menu; the map's unknown land as a cartographer leaves it |
| bcf13d0 | The pack as a right-hand panel; the camera steps the survivor aside; page-or-panel table in UI_DESIGN 6 |
| 0416a23 | The chapter's end as the survivor's open book |
| d20f855 | The Wayfinder's table as map sheets on his table; the Last Lamp as three crested choices |
| fcbd225 | Every Ornate look gives way to its painted piece by name; crest_card, ribbon, plaque_rule registered |
| 9b4eaf1 | At the art lead's asking: banner and crest_card tile; `crest_row` for low crested cards (picked by height); the banner's stone drawn by the code |
| ddd3656 | Merged the integration branch again (d2a2eab); 470 tests green |

**Last full shot pass** (`m8`, after fcbd225, every screen with mouse and pad, `--navcheck`): no
errors; every audited screen reaches all its focusable things; nothing off screen. The title and
pause menus keep their own focus lists (MenuList), so the audit reports none for them; the skills
page with nothing learned has nothing to focus. Pictures: `godot/.shots/m8_*.png` (ignored by git).

## 4. In progress / next, in order

**0. First: the heroine's character creation** (the owner, arriving at handoff: "can we customize hair
or face in our create character yet? I couldn't find it"). The coordinator's brief: creation worthy of
her, a live 3D preview turnable and zoomable to her face, with her own five hairstyles (with their
physics) and hair colour, skin tone, eye colour, face shaping as tasteful sliders or presets, face
paint if the system supports it; it must save, apply in play, and look AAA with painted art.
What exists (scoped, not built):
- Her body is "heroine" (`People.cs:94-102`, `art/people/heroine.glb`): `HerHair(p, style, colour)`
  with `HerHairs = long, ponytail, braid, bob, pixie`; `HerFace(p, face)` with 25 shape-key sliders
  (`HerSliders`, -1..1: eyes size/spacing/height/tilt/open, brows, nose, lips, mouth, cheekbones,
  cheeks, jaw, chin, ears) and expressions; `Look.Face` carries them.
- Not wired: `Loadout.cs:79` gives her no hairstyle (`Hair = her ? null`), so `People` falls back to
  "long"; `CharacterData` (`Rpg/Character.cs:122`) keeps Skin, Hair (colour), HairStyle but **no face,
  eye colour or paint**; `heroine_eye.gdshader` has **no iris tint** uniform; no face paint system.
- Creation's look step (`Front.cs` ~410-460) hides the cut for her ("her hair is her own").
Plan: add `Face` (slider dictionary), `Eyes` and `Paint` to the saved character and its Loadout/Look;
let her hairstyle through `Loadout`; an iris tint in the eye shader (that shader and `src/Actors/`
belong to the heroine pipeline, now the main session: agree the change with it); in creation, a look
step with the figure turnable (drag / right stick) and a zoom to the face, her five cuts as painted
portrait cards, swatches for hair, skin and eyes, face shaping as a few presets plus grouped sliders
(eyes, brows, nose, mouth, jaw and chin), all on the house's plates. Shoot it at full resolution.

See `docs/team/ui_design.md` "Next" for the rest. In short: read the last full shot pass and fix what it shows;
announcements (bare text), the item card's own layout, the journal's deeds and codex, the HUD's dash
pips and draught box; re-make `docs/ui_review/`; UI_DESIGN section 10.

## 5. Decisions (one line each, with why)

- Globe for health, not the art's bar: the console HUD is the redesign's researched choice (D4's band).
- Painted draft cards keep the crested card's medallion and glow: the art is the material, the code
  the state.
- Pages vs panels (UI_DESIGN 6): pack is a panel (tweaked mid-play, D4/PoE/LE); self, arts, journal,
  map, shop, storeroom are pages (read or planned at leisure); pause a side column; lamp and table windows.
- Pause only in a fight: the owner's rule; the pause menu always pauses.
- Unknown map land: blank aged paper with a tide line, not a flat fill; the sheet on a leather table.
- `OrnateBox.Painted`: every drawn look uses its painted piece wherever it is made, keeping only the
  accent (crest band tint, hairline, glow).
- Focus audited by the game (`--navcheck`), not by eye.

## 6. Failures and why

- Editing a shot batch script while bash ran it garbled the run (bash reads scripts as it goes):
  copy the script (`run_mN.sh`) before running it in the background, never edit the running copy.
- Quick runs (`--quick`) save over slot 0: the story save must be put back before each `--continue`
  shot (the batch does it).
- Rebuilding Self's standing on every preview freed the controls the pad had in its focus list:
  change in place instead; `--navcheck` found it (8 of 23 reachable).
- The sandbox refuses compound shell commands that mix `cd`, heredocs, variables and git: write a
  Python script to the scratchpad and run it plainly, or use the Edit tool.

## 7. Gotchas

- **The scratchpad is shared between agents.** Mine is `scratchpad/uilead/` (shot.sh, shots_all.sh,
  qasaves/, logs/). Use your own subfolder.
- Shots: `bash scratchpad/uilead/shots_all.sh PREFIX "regex"` (copy it first for background runs).
  Pictures land in `godot/.shots/`. `shot.sh` passes `--navcheck`; `nav ...` lines are the audit
  (unreachable / off screen / no size are the ones to fix; one-way steps are information).
- `godot/override.cfg` (local only, excluded) gives the game the user folder `SurvivorUnchainedUiLead`;
  the story save comes from `QA_SAVES=<dir> dotnet test godot/tests/Tests.csproj --filter QaSaves`
  (it reports a failure but writes the saves).
- `godot/assets` must be a junction to `public/assets` (see the README's fix), skip-worktree set.
- Before committing: `git checkout -- "*.import"` (Godot rewrites them on import); don't add the
  untracked `.uid` files under tests/logic/Actors.
- Files are CRLF in the working tree (autocrlf): scripts that edit them should keep the line ending.
- Don't build while a background shot run is starting a game: wait for it.

## 8. Collaborators

- Main session (coordinator): merges branches; relays the owner. Message "main".
- UI art lead `a72467cac33063d3a` (`docs/team/ui_art.md`): paints from `UI_ART_BRIEF.md` 4.9 and
  `tools/comfy/ui_assets.json`; its step 0 is merging this branch.
- Gameplay experience director `a33f58e68e89e3ccf` (may send UI briefs); crafting lead `a7862117a0240deb5`.
- Story `a7622ae77d19e31dc`, combat `a09c5a65f5a84319e`, animation `aa4f5fc266b043035`, voice
  `a2da9a388ceb1b987` (see the roster in `docs/team/README.md`).

## 9. Read first

1. `docs/team/README.md`  2. this file  3. `docs/team/ui_design.md`
4. `docs/UI_DESIGN.md` (sections 1.3, 6 "Page or panel", 7, 11)  5. `docs/UI_ART_BRIEF.md` 2.6 and 4.9
6. `godot/src/Ui/Ornate.cs`, `Overlay.cs` (Page, SidePanel), `UiArt.cs`, `Nav.cs` (Audit)
7. `godot/src/Ui/Pack.cs` (the panel), `MapScreen.cs` (Fog), `MapTable.cs`, `Menus.cs`
