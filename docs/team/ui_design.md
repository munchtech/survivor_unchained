# UI design (and the UI merge): status

Agent ac76f400913a109cd, branch `worktree-agent-ac76f400913a109cd` (integration branch merged in at 765a575).
Predecessor's handoff: `docs/handoff/ui_design.md`.

## How the owner reaches character customisation
**New Journey, then step IV "Look"** on the road of medallions at the top left (click it, or Next three
times, or `]` / RB). Its parts are Body, Hair, Face and Paint (click the tabs, or `,` `.` / LT RT). The
figure turns when you drag her, and the mouse wheel or a double click brings the camera to her face.
- **Why the owner may not see it:** the main checkout's built C# (`godot/.godot/mono/temp/bin/Debug/
  SurvivorUnchained.dll`, 10/3 23:43) is older than the creation work. Started from the Godot project
  manager's Run, or the game exe, it runs that old build (four steps, no Look). Fix: open the project in
  the Godot editor and press Play (it builds first), or run `dotnet build godot/SurvivorUnchained.csproj`
  once and then start the game. New textures (the face paint) are imported when the editor opens.
- Checked in this worktree with the integration branch merged in: the five steps show and the Look step
  works (shots `godot/.shots/c2_part*.png`, `c3_part*.png`). A key-tour shot from the title stayed on
  step I, because the tour's presses arrived before the fade into creation. That is a harness timing
  issue, not a player bug; use `--new --step 3 --part N` for shots.

## Current state (pushed, 520 tests green)
- Saved and worn: her cut, hair and eye colour, face (25 sliders, 7 faces), paint; skin as before.
- Look data is per hero body: `looks.json` `heroes.female` (`Lore.Hero(sex)`, `Loadouts.HeroKit`).
  The male hero (ae2de192cce8298ca) can fill `heroes.male` and change `HeroKit` to give him the same step.
- Face paint art: `tools/assets/heroine_paint.py` (unrolls her face from heroine.glb, paints 7 designs,
  lays them on her UVs) -> `art/people/paint/*.png` (BC7, mipmaps). Rerun it when her head is rebuilt.
  **Not yet seen on her in the game**, and the brow layer (`paint/brows.png`) is **not wired** yet.
- Creation: portrait key light and DOF when near; hair turned to show the cut; `--step N --part N`.

## Next (in order)
1. See each paint on her in game (FaceSheet with `"paint"`, then the Look step) and tune.
2. Wire the brows: a pass under the paint, dyed her hair's colour (`People.HerPaint`/`HerRestyle`).
3. Cameo portraits for cuts, faces, paints (FaceSheet renders: cuts in grey plus `_mask`); register
   them for the UI art lead (`tools/comfy/ui_assets.json`, UI_ART_BRIEF).
4. Reply to the male hero lead with the field names (`CharacterData.Face/Eyes/Paint`,
   `HairStyle`, `Lore.Hero`), and agree `BeardStyle`.
5. The experience director's four findings (barks overlap, the result screen as the night's story,
   the table says what a map pays, pausing only in arenas and on the night road), then the handoff's
   list (announcements, item card, journal, HUD dash and draught).

## Key decisions
- Creation opens on the heroine. Slider ends capped where her shape keys break. Paint is a pass of its
  own over her skin (the skin shader is untouched). Look is per hero body, not per sex.

## Notes for other areas
- Main session: at close range her long and ponytail hairlines show a hard cap edge and a bare strip
  at her left temple, and strands clip into her neck.
- Voice lead: the `Names` list in Front.cs is unchanged (it carries one recorded take per name).
- Scratchpad: `scratchpad/uid2/` (`shot.ps1`, `fs.ps1` face sheets, `crop*.py`, `paintsheet.py`).
