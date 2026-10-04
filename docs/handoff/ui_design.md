# Handoff: the UI/UX of Survivor Unchained

Branch `worktree-agent-ad1a039caf3923eec` (pushed to origin), worktree
`C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec`.
Everything is committed and pushed. Tests: 435 of 435 pass. The game builds
with no errors.

This file is all a successor gets besides the repository. Read it whole
before touching anything.

---

## 1. The owner's bars

The owner wants the best design there is, not an improvement on what was
there. In their words and the coordinator's:

- **"the best design backed by research"**: every choice must rest on what
  the best games do and why (docs/UI_RESEARCH.md, rules R1-R10).
- **"I don't want to polish, I want to create perfection."** Said when they
  saw the first pass had reskinned the old windows.
- **Build new things, not reskins.** Start each element from "what is the
  best possible design for this job?", never "how do I improve what is
  here?". Rebuild when that is the answer. Add what the best games have
  (comparison, filtering, previews, drag and drop, quick actions, shortcuts).
- On the first pass's result: **"the literal exact same shapes"**. Their
  specific complaints: the map was a huge empty parchment square with the
  zone tiny at its edge; the pack a big dark mostly-empty box with small
  items; Self a dense wall of text in a box; everywhere no material
  hierarchy, depth or framing, and nothing said "this is Survivor Unchained".
- From the owner's standing memory (applies to all agents): never settle,
  AAA; "amazing, not improved"; remake rather than skip; verify at full
  resolution; the game is 18+ dark fantasy; don't stop to ask, carry on.

## 2. The brief, and every later message

**Original task** (from the coordinator): own the UI/UX of Survivor
Unchained (adult dark fantasy; an ARPG by day, a survivors-like roguelite
by night). Five deliverables:

1. Exhaustive research into the best UI/UX of comparable games and the
   principles behind it: `docs/UI_RESEARCH.md` (done).
2. Audit every element of the current interface (done; UI_DESIGN.md §3).
3. Design: `docs/UI_DESIGN.md` (layout, interaction for mouse and keyboard
   and for pad, focus order, states, animation and feedback, sound,
   accessibility, self-teaching, a style guide).
4. Implement the UX and layout in the Godot UI code with placeholder art,
   verified by screenshots for mouse and keyboard and for pad; tests green;
   commit as you go.
5. `docs/UI_ART_BRIEF.md` for the art agent: every asset with its purpose,
   screen, pixel sizes, nine-slice margins, states, file path, style
   references, dos and don'ts, and its plug-in point (code loads art by path
   and falls back to the drawn look).

Report back: branch, commits, key research findings, the changes with
before and after screenshot paths, where the brief is.

**Rules**: every commit message ends with
`Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`; push the branch
(`git push -u origin HEAD`), no PR. British spelling in player-facing text,
docs and comments. Comments are short prose that say why. Do not touch the
art and hair pipeline (`tools/assets/`, `godot/art/people/`,
`godot/shaders/heroine_*`, `godot/src/Actors/`): another session works
there. Do not rewrite story text (a writer agent owns dialogue, quests,
lore). Skill and upgrade mechanics belong to another agent: own their
presentation, change no balance or mechanics. Never commit or print API
tokens or secrets.

**Later messages from the coordinator, in order**:

- Local image generation may be used: ComfyUI at http://127.0.0.1:8188
  (start headless with `ComfyUI-Installs\ComfyUI\ComfyUI\.venv\Scripts\python.exe`
  and the extra-model-paths yaml in `%APPDATA%\Comfy Desktop\instance-model-paths`;
  models in `%LOCALAPPDATA%\Comfy-Desktop\ComfyUI-Shared\models`): Krea 2
  turbo, the darkbrush LoRA, BiRefNet, qwen3vl; `tools/comfy/comfy.py`;
  outputs under `tools/comfy/out/` (gitignored); Blender 4.5 at
  `C:\Users\munch\Tools\blender-4.5.14-windows-x64\blender.exe`. Don't use
  paid Comfy cloud API nodes. Write the tools and workflows into the art
  brief. Assets must be CC0 or our own generations; credit anything
  third-party in `public/assets/CREDITS.md`.
- The owner confirms free use of the computer and its programs (Godot,
  Blender, Python, the GPU, local ComfyUI, web research); free reputable
  tools may be installed. No paid cloud services. The GPU is shared with
  other agents: keep generation jobs reasonable.
- After a usage cut-off: carry on, commit and push often. If `godot/assets`
  is a text file, fix it with
  `Remove-Item godot\assets; cmd /c mklink /J godot\assets public\assets; git update-index --skip-worktree godot/assets`,
  then `--headless --path godot --import`.
- The owner noticed reskinning: "I don't want to polish, I want to create
  perfection." Start from the best possible design for each job; rebuild;
  add what the best games have; revisit the reskinned windows; record in
  UI_DESIGN.md why each final design is best.
- The cloud sessions' `docs/items/VISUALS.md` and `docs/feel/SUGGESTIONS.md`
  were merged into `claude/vigilant-galileo-l6jqyx`: merge them in and weigh
  them against the research (done; UI_DESIGN.md §9).
- **The second pass** (the current work): redesign from first principles,
  screen by screen. (1) For each major screen (HUD, pack, self, arts,
  journal, map, draft, conversation, shop and stash, title and creation,
  pause, arena result) question the whole composition: full screen or
  window, layout zones, where the eye lands, sizes, what the best games do.
  (2) Make 2-3 concept mockups per major screen, using local Krea for the
  look and your own drawn layouts for structure; pick the best with
  reasoning; record the chosen concepts and why in `docs/UI_DESIGN.md`.
  (3) Implement the chosen designs fully (structure and composition) and
  verify them in screenshots. (4) Coordinate with the art agent through
  `docs/UI_ART_BRIEF.md` (update the sizes, pieces and states the new
  layouts need so its work plugs in). (5) Finish with before and after
  screenshots of every screen, side by side, in `docs/ui_review/`. Merge
  `origin/claude/vigilant-galileo-l6jqyx` first. Keep the tests green,
  commit and push often.
- Another cut-off: carry on from the pause menu and its concept; commit and
  push often.
- Hand off to a fresh agent at the next checkpoint (this file).

## 3. What is done

### First pass (merged into `claude/vigilant-galileo-l6jqyx` long ago)
Research (`docs/UI_RESEARCH.md`), the audit and design
(`docs/UI_DESIGN.md`), the art brief (`docs/UI_ART_BRIEF.md`) and its
manifest and tool (`tools/comfy/ui_assets.json`, `tools/comfy/ui_art.py`),
the whole input model (pad, focus, prompts that follow the device), the
day's book of five tabbed pages, rebuilt pack/shop/storeroom/self/map
(atlas), the minimap, edge marks, the draft's build strip, conversation
recall, the feel work's HUD pieces, the art plug-in system (`UiArt.cs`).
Commits there include ef556b9, 66432a6, 7d864c6, 60c5310, 67484fe.

### Second pass (this branch; 14 commits on top of vigilant-galileo)

| Commit | What |
|---|---|
| b09eacb | Foundation: `Ornate.cs` (drawn forged frames, plaque, section, medallion, globe, backdrop), `Overlay.Page/Pane/PageFooter`, Pack and Self recomposed, `tools/comfy/ui_concepts.py` and the 33 concepts |
| b9bc561 | Map: full screen, opened fitted to what you know, dark unwalked land |
| 1b0d24e | Journal: a book lying open (`OpenBook`, `RibbonBox`); pages hide the HUD |
| f1fe0ac | Arts: the altar (medallion grid, great medallion with sockets, facet cards, road to mastery); skills page in the same panes |
| 51194d7 | Shop as a counter (merchant, wares, your pack and purse); storeroom full page; tips placed after layout |
| 1ce2bd5 | Draft: crested cards over the ember's fire |
| f36db36 | Conversation: the person large over the words (Portrait `Framing.Half`) |
| 6447922 | Pause: a forged column down the left, the world beside it |
| ddc5ccd | Creation: column of crested calling cards, step road of medallions, name banner |
| d21fff2 | Arena's end: verdict banner, the numbers on counting medallions, the lost build as grey medallions |
| 069846b | HUD: a console at the foot, health as a globe at its left end, the art's ring at its right |
| 6e7ae5e | Title: the house's rule under the name, plaques on its panels |
| 4ad21f1 | `docs/ui_review/<screen>.jpg`: before / first pass / second pass side by side for 23 screens; `tools/comfy/ui_review.py` |

**Recomposed in the second pass**: HUD (night, day, peace), Pack, Self,
Arts (both pages), Journal (all four sections now sit in the open book),
Map, Draft, Conversation, Shop, Storeroom, Pause (with settings and
controls opening beside the column), Creation (all four steps), Arena's
end. Title: only light touches (the rule and the panel plaques).

**Not yet brought into the new language**: the Last Lamp (rest), the
Wayfinder's table, the chapter's end, the item card/tooltip itself
(`ItemViews.Card`, still a flat StyleBoxFlat tooltip), buttons, segments
and tabs (`Style.Button/Segment`, flat), toasts, the hint, announcements,
the boss bar, the minimap's ring, the corner's words. The Journal's deeds
and codex content kept its old layout inside the book.

## 4. What is in progress, and its exact state

Nothing is half-made in code. Three deliverables of the second pass are
**not done**:

1. **`docs/UI_DESIGN.md` is still the first pass's text.** It must get the
   second pass: the page system and the frame language (Ornate), and for
   each screen the concepts weighed (with the images in
   `docs/ui_review/concepts/`), the one chosen and why (section 6 below has
   all of it), and what is built. Sections 4 (HUD), 5 (draft), 6 (book), 7
   (other screens) describe the old compositions and are now wrong in
   places (e.g. 4.3 health bar, 6.5 map at 920 px, 7.3 pause plate).
2. **`docs/UI_ART_BRIEF.md` and `tools/comfy/ui_assets.json` do not yet
   list the new pieces** (section 7 below lists them with sizes). The art
   agent is working from the old brief.
3. **`docs/ui_review/`** has the sheets, but they should be re-made once
   the remaining screens are done (`python tools/comfy/ui_review.py` after
   re-shooting).

Known issues seen in the last screenshots:

- **Map in the Verge** (`godot/.shots/v2_map_verge.png`): the fit puts the
  view's left third past the zone drawing's edge (plain dark), and the fog
  over unwalked land lets the ink show through at roughly 40% where it was
  meant to read as dark. Look at `MapScreen.Fit` (clamp the pan so the
  drawing covers the view where it can) and `Fog` (alpha after the three
  `Blur` passes; the fog colour is drawn at `alpha * 0.94`).
- Frame ids `pillar` (Self's attribute pillars) and `console` (the HUD's
  plate) are asked for by code but not registered in `UiArt.Frames`, so
  painted art for them would never load. Register them with the brief.
- The Journal's people page (`v2_journal_people.png`) and the Self pad
  shot should be looked at again at full resolution; the last checks were
  before the HUD-hiding change.
- Painted draft-card art (`card_0..4`) would replace the Ornate card and
  lose its glow and crest: when the art lands, check the draft.

## 5. What is next, in order

1. Merge `origin/claude/vigilant-galileo-l6jqyx` (42 commits ahead of this
   branch's base), build, run the tests, re-shoot.
2. Write the second pass into `docs/UI_DESIGN.md` (section 6 below).
3. Update `docs/UI_ART_BRIEF.md` and `tools/comfy/ui_assets.json` with the
   new pieces (section 7 below), register `pillar` and `console` in
   `UiArt.Frames`, and tell the art agent.
4. Fix the Verge map fit and fog.
5. Bring the rest into the language, each from its job first: the item
   card (an Ornate tooltip with a rarity crest, the comparison as two cards
   with a delta column), buttons/segments/tabs drawn by Ornate (a forged
   button with states: normal, hover, pressed, focus, disabled, primary),
   the Wayfinder's table (three maps as crested cards on a table surface),
   the Last Lamp, the chapter's end, toasts, hint, announcements, boss bar.
6. A full pad and keyboard pass over every recomposed screen (focus order
   and reachability: Self's pillars and traits, Arts' medallion grid into
   the facets, Shop's three panes, Stash, the Journal's list, Creation's
   step road, the pause's book medallions which are `Nav.Skip`).
7. Re-shoot everything, re-make `docs/ui_review/`, final report to the
   coordinator (branch, commits, research findings, before and after paths,
   brief location).
8. Then the first pass's remaining list (UI_DESIGN.md §10): the chest
   panel and evolution name card (feel work), a text-size setting,
   hold-to-read detail, the other accessibility settings.

## 6. Decisions and the research behind them

The frame language: forged iron plates (a gradient from a lit top to a dark
foot, a bevel, an inset gold hairline, bracketed corners each with a cut
stone, a soft shadow), sunk wells for grids and lists, crested cards for
choices (the rarity or school in a crest band, the corners and a stone at
the head), slabs for groups inside a plate, parchment for what is written,
banners for verdicts and names, medallions for anything round (a level, an
attribute, an art, a step, a socket, a number), a title plaque (Cinzel
between gold rules ending in ember stones). All drawn in code
(`Ornate.cs`) so the game says "Survivor Unchained" before any art lands;
painted art replaces each piece by name. Why: the owner's "no material
hierarchy, depth or framing"; Diablo IV, Grim Dawn and PoE2 all read as
themselves through their frame material first.

The page system: the day's book screens are full pages, not windows.
`Overlay.Page` darkens the world (a radial `Backdrop` with an ember glow at
the foot), puts a header band across the top with the book's tabs at the
left, the title plaque in the middle and Close at the right, and hands back
a 1840 x 920 content area at (40, 112) that screens fill with framed panes
(`Overlay.Pane`). The HUD steps away while a page is open. Why: the pack,
self, arts, journal and map are reading and comparing screens; every best
ARPG (D4, PoE2, Last Epoch) gives them the screen, and a window inside a
dark rectangle left most of the screen empty, which was the owner's
complaint about the pack.

Concepts: `tools/comfy/ui_concepts.py` draws each layout from crops of the
real game and paints it with Krea img2img (darkbrush LoRA 0.6, denoise
0.55); each image in `docs/ui_review/concepts/<screen>_<a|b|c>_<name>.jpg`
is the drawn layout beside its painting. Chosen, and why:

| Screen | Weighed | Chosen | Why |
|---|---|---|---|
| HUD | A corners (as it was), B console, C minimal | **B console** | Diablo IV and Lost Ark put health, skills and the art in one band where the eye drops from the fight (proximity, Fitts); the corners split attention three ways. Health as a globe reads at a glance as a level, not a number; the ember bar stays top centre; the under-feet health bar stays at night (the survivors-likes' answer) |
| Pack | A box, B two panes, C hero centre | **B two panes** | The survivor large on the left with what they wear round them and their standing beneath; what they carry on the right in a well of 112 px slots with filters, the chosen thing read closely, gear beside what it would replace (D4 / Grim Dawn side by side: comparison is recognition, not recall) |
| Self | A columns, B pillars, C paper sheet | **B pillars** | Three panes: who they are (figure, level medallion, art in hand, calling, knowledge); the four attributes as pillars with the number as the hero, a + that previews its change; traits as cards with the places still to fill (level 2, 4...); the standing grouped on plates with sources on hover. Answers "a wall of text" by giving each kind of thing its own shape |
| Arts | A list, B altar, C tree | **B altar** | Arts are few and precious: medallions with rank progress round the ring; the chosen art as a great medallion with its two facet sockets; four facet cards; a road of five ranks. A tree overstates a five-rank system; a list hid what is coming |
| Journal | A sheet, B open book, C board | **B open book** | It is the survivor's own book; two leaves give list and page side by side; ribbons as sections are the book's own tabs; leather and parchment are the material the owner asked for |
| Map | A square, B full bleed, C table | **B full bleed** | A map is opened to find something: the whole screen, opened fitted to the walked land and you (not the whole zone at 920 px with the zone small at its edge), unwalked land dark so the known world is a lit island; the list of where to go at the right; zoom and find-me at the map's foot |
| Draft | A cards, B rows, C crested cards | **C crested cards** | Hades' cards with rarity in the frame; the ember's fire behind them says "the night's power"; the build strip on a slab beneath (HoloCure's build beside the choice) |
| Conversation | A boxed, B portrait, C column | **B portrait** | The person large, head to hip, standing over the left end of the words as across a table (Disco Elysium, BG3, Hades): relatedness is the town's heart; a 228 px bust in a box made them furniture |
| Shop | A box, B counter, C two grids | **B counter** | The merchant is a person first (their face, how they feel about you, prices against their usual, what is on their mind); the wares large in the middle with the thing read closely; your pack and purse at the right. Storeroom: the store's large grid left, your pack and the thing read closely right |
| Creation | A rows, B crested | **B crested** | A forged column of crested calling cards with medallion marks; the four steps as a road of medallions; the choice read closely on the right; who they are becoming on a banner at the figure's feet; the fire stays the centre |
| Pause | A box, B side | **B side column** | The game stays in view, paused (D4, Elden Ring): a forged column with the place, the day and what you are about, the menu, the book's five pages as medallions; settings open beside it |
| Arena's end | A boxes, B spoils | **B spoils** | Peak-end: a verdict banner, the night's numbers counting up on medallions whose rings fill, what you take out on a forged plate, the lost build as grey medallions on ash |

## 7. Pieces the art brief must gain

All have drawn stand-ins in `Ornate.cs`; painted versions are made at 2x
and halved (`UiArt.Tex` with `SetSizeOverride`).

| Id / path | Used by | Shown size | Nine-slice (2x) | Notes |
|---|---|---|---|---|
| `frames/well.png` | grids, lists | any | 12 | registered |
| `frames/slab.png` | groups in a plate, trait cards, stash/pack sub-plates | any | 14 | registered |
| `frames/header.png` | the page's header band | 1928 x 100 | 0,0,0,12 | registered |
| `frames/banner.png` | verdicts, names (talk, creation, result) | auto | 24,14,24,14 | registered |
| `pillar` | Self's attribute pillars | 188 x 340 | ~24 with a crest | **not registered yet** |
| `console` | the HUD's skill plate | 300-720 x 130 | ~24 | **not registered yet**; stretches with the skill count |
| `book/open.png` | the Journal's open book | 1700 x 852 | none (whole) | leaves' content inset 26 + 52 |
| card crest | draft cards, facet cards, creation choices | 320 x 452 / 287 x 280 / 470 x 92 | crest band 40-120 px | rarity / school as tint |
| medallion ring | levels, attributes, arts, sockets, steps, result numbers, pause book | 44-220 round | none | ring, core, ember glow when lit |
| globe | HUD health | 132 + rim | none | glass, liquid, rim, shield arc |
| ribbon | the Journal's sections | 132 x 66-86 | 0,6,0,26 | silk per section: red, green, blue, gold |
| plaque rules | every title | any | none | gold rule, ember stones |

## 8. Tried and failed (and what replaced it)

- `Skin` clashed with `Godot.Skin`: the art class is `UiArt`.
- The sandbox refuses complex bash in this worktree (heredocs that cd,
  `xargs`, `cd` to a computed dir, chained scripts, `&&` chains that look
  like they might run git elsewhere). Write a Python edit script to the
  scratchpad and run it as one plain command; one `shot.sh` per call or a
  plain script of shot lines.
- The fonts lack ★ ▲ ◆ ◦ ✓ ← →: draw marks (`Style.Gems`, `Style.Dpad`).
- A label not yet in the tree does not know its size: `Plaque` measures
  with `Style.Display.GetStringSize`; stretched, it centres on `Resized`.
- A `TextureRect`'s expand mode must be set **before** its size, or it
  keeps the texture's own size as its minimum (the 1600 px map drawing).
- Wrapped labels know their height only after a frame: `Overlay.Tip` is
  placed, hidden, then placed again deferred and shown.
- A pad move right after a rebuild went nowhere (layout not yet computed):
  `Nav` defers directions a frame.
- An inner VBox not added to its button left the trait buttons empty and
  leaked at exit; build only the controls you show.
- Krea's aspect names are exact (`16:9 (Widescreen)`, not `Panorama`); 2:3
  painted noise, 3:4 works. BiRefNet's `RemoveBackground` returns a mask:
  `MaskToImage`, then `putalpha` in PIL.
- Painted frame content overlapped its border: content margin =
  max(drawn margin, slice x 0.75).
- The map's splat read nearest-neighbour showed squares: bilinear `Splat()`.
- `QaSaves` reports a failure but still writes its saves (three of them).

## 9. Gotchas: how to work here

**Build and test**:

    dotnet build C:\...\agent-ad1a039caf3923eec\godot\SurvivorUnchained.csproj -v q -nologo
    dotnet test  C:\...\agent-ad1a039caf3923eec\godot\tests\Tests.csproj -nologo -v q    (435 tests, about 30 s)

**Screenshots**: the scratchpad's scripts die with the session, so here is
`shot.sh` whole (save it to your own scratchpad):

    #!/bin/bash
    # usage: shot.sh NAME SECONDS [game args...]
    GODOT="/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe"
    WT="/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-ad1a039caf3923eec/godot"
    LOG=<your scratchpad>/log_$1.txt
    name=$1; secs=$2; shift 2
    "$GODOT" --path "$WT" --resolution 1920x1080 -- --shot "$name" --seconds "$secs" "$@" > "$LOG" 2>&1
    grep -iE "saved|error|exception" "$LOG" | head -15

The picture lands in `godot/.shots/<name>.png` (gitignored). The game's
flags: `--quick ARCHETYPE`, `--zone waystation|verge|arena|lowford`,
`--time day|night`, `--open inventory|character|arts|journal|map|maps|pause|rest|stash|shop:ID|chapter|draft|result|talk:ID`,
`--keys A,B` (actions pressed in turn after the screen opens, 0.35 s
apart, e.g. `Right,Down,Confirm,SubNext,TabNext`), `--pad` (as from a pad:
focus ring and pad prompts), `--items ID[:RARITY],...`, `--xp N`,
`--horde N:KIND!`, `--auto idle`, `--new` (creation), `--continue`.

The shots used for `docs/ui_review` (names `v2_*`):

    v2_arena 16 --quick reaver --zone arena --auto idle
    v2_hud_verge 8 --quick warden --zone verge --time day
    v2_hud_town 6 --quick warden --zone waystation
    v2_pack 6 --quick warden --zone waystation --items chain_shirt:2,iron_helm:1,silver_ring:3,wolfhide_cloak:4,bone_charm:1,wolf_pelt,bitterroot,stream_sample,manual_blink --open inventory --pad --keys Right,Right
    v2_self 6 --quick warden --zone waystation --xp 900 --items chain_shirt:2,iron_helm:1 --open character --pad --keys Right
    v2_map 7 --quick warden --zone waystation --open map
    v2_map_verge 8 --quick warden --zone verge --time day --open map
    v2_draft 6 --quick reaver --zone arena --open draft --pad --keys Right
    v2_talk 7 --quick warden --zone waystation --open talk:rook
    v2_shop 7 --quick warden --zone waystation --items chain_shirt:2,iron_helm:1,silver_ring:3,wolf_pelt,bitterroot --open shop:harlan --pad --keys Right,Right
    v2_stash 7 (same items) --open stash --pad --keys Right
    v2_create 8 --new --pad --keys Down
    v2_create_name 9 --new --keys TabNext,TabNext,TabNext
    v2_title 5 --pad --keys Down
    v2_result 8 --quick reaver --zone arena --open result
    v2_rest / v2_table / v2_chapter 5 --quick warden --zone waystation --open rest|maps|chapter
    v2_journal 10 --continue --open journal
    v2_journal_people 11 --continue --open journal --pad --keys SubNext,Down,Down
    v2_arts 10 --continue --open arts
    v2_skills 10 --continue --open arts --keys SubNext
    v2_pause 10 --continue --open pause --pad --keys Down
    v2_pause_settings 10 --continue --open pause --pad --keys Down,Down,Confirm

`--continue` shots use a story save so the journal and arts have content.
`godot/override.cfg` (local only; excluded in `.git/info/exclude`, never
commit it) gives the game its own user folder `SurvivorUnchainedUiShots`.
Make the save with
`QA_SAVES=<dir> dotnet test godot/tests/Tests.csproj --filter QaSaves`
(it reports a failure but writes `ledger_read.json`, `roost_emptied.json`,
`roost_sunk.json`), then copy one to
`%APPDATA%\SurvivorUnchainedUiShots\saves\slot0.json` with a `meta.json`
of `{"last":0}`. It is there now (roost_emptied).

If a run errors with `Unable to open file: res://.godot/imported/...ctex`,
run `Godot..._console.exe --headless --path <worktree>/godot --import`.
It rewrites hundreds of `.import` files with new line endings: put them
back with `git checkout -- "*.import"` before committing. Don't commit the
untracked `.uid` files under `src/Actors`, `tests`, `tools_scenes`.

**Godot UI here**:

- Everything is code-built Controls on CanvasLayers; no scenes. `Overlay`
  is the base of every screen (`Build()`, `Refresh()`, `Key(Act)`,
  `Tip()`); `GameHud` is the HUD; `DraftPanel` and `TalkPanel` live in
  `Panels.cs` on the HUD.
- `OrnateBox : StyleBox` draws in `_Draw(Rid, Rect2)` with
  `RenderingServer.CanvasItemAdd*`. `OrnateBox.Make(Kind, pad, accent)`;
  fields `Crest`, `Glow`, `Corners`, `Shadow`, `Top`, `Foot`.
- Screens lay out with absolute positions inside the page's content area
  plus containers inside panes. `CenterContainer` to centre a grid.
- Fonts (`Style.Display` Cinzel, `Text` Alegreya, `Ui/UiBold/UiHeavy`
  Alegreya Sans) and the type scale and tokens are in `Style.cs`. Text
  floor 15 px, prose 18.
- Focus: `Nav.Mark(control, id, press, alt, alt2, focus, blur, adjust)`;
  `Nav.Id` names a button; `Nav.Skip` takes a control out of focus; ids
  are kept across rebuilds; `Nav.Scope` limits focus to a panel.
- Prompts: `Style.Prompt(Act)`, `Style.Hint`, `Overlay.Footer` draw the
  key or pad button for the device in hand; `DeviceChanged` redraws.
- Art: `UiArt.Frame(id, fallback)`, `UiArt.Art(rel)`, `UiArt.Icon(set,key)`
  under `godot/art/ui/` (not present in this branch yet).
- Concept tool: `python tools/comfy/ui_concepts.py` (needs ComfyUI up and
  the after/v2 shots present; writes `docs/ui_review/concepts/`). Review
  sheets: `python tools/comfy/ui_review.py` (needs
  `tools/comfy/out/ui_concepts/alegreya-sans-700.ttf`, which the concept
  tool makes).

## 10. Open questions for the owner

1. The health globe by day too, or a quieter bar when there is no fight?
   (Now: the globe moves to the bottom-left corner at peace.)
2. Should the full pages pause the world? (They hide the HUD; the world
   runs as before.)
3. Unwalked land on the map: dark (now) or blank parchment (as before)?
4. Self and Pack both show the survivor large. Keep both, or merge Self
   into the pack's left pane as a second tab?
5. Painted art for every frame, or keep the drawn frames where they read
   well and paint only ornaments, medallions and icons?

## 11. Collaborators

- **The UI art agent**: id `abd496197891ea843` ("AAA UI artwork from the
  brief"), worktree `.claude/worktrees/agent-abd496197891ea843`; it paints
  from `docs/UI_ART_BRIEF.md` and `tools/comfy/ui_assets.json` into
  `godot/art/ui/`. It was still running at handoff. It needs the new pieces
  of section 7; reach it through the coordinator or by updating the brief.
- The art and hair pipeline session (owns `tools/assets/`,
  `godot/art/people/`, `godot/shaders/heroine_*`, `godot/src/Actors/`).
- The writer agent (dialogue, quests, lore: do not rewrite text).
- The skills agent (mechanics and balance: presentation only).
- The coordinator (sends the messages above; relay to the owner).

## 12. Read these first

1. `docs/handoff/ui_design.md` (this)
2. `docs/UI_DESIGN.md` (first pass; to be rewritten for the second)
3. `docs/UI_RESEARCH.md` (rules R1-R10 in section 8)
4. `docs/UI_ART_BRIEF.md` and `tools/comfy/ui_assets.json`
5. `godot/src/Ui/Ornate.cs` (the frame language)
6. `godot/src/Ui/Overlay.cs` (Page, Pane, Tip, the book's tabs)
7. `godot/src/Ui/Style.cs` and `godot/src/Ui/UiArt.cs`
8. `godot/src/Ui/Pack.cs` (pack, shop, storeroom: the page pattern)
9. `godot/src/Ui/GameHud.cs` (the console and globe)
10. `godot/src/Ui/Nav.cs` and `godot/src/Game/Controls.cs` (input)
11. `docs/ui_review/*.jpg` and `docs/ui_review/concepts/*.jpg` (look at them)
