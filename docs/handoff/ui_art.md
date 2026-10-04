# Handoff: the interface's art (UI art lead)

For the next agent carrying on the UI art of Survivor Unchained. Read `docs/team/README.md`
first (the team's bar, how we work, safety, roster), then this whole file, then
`docs/team/ui_art.md` (the one-page status).

Branch: `worktree-agent-a72467cac33063d3a` (pushed; no PR; the main session merges it into the
integration branch `claude/vigilant-galileo-l6jqyx`). At handoff it equals the integration branch
at `535bb60` (539 tests green). Worktree on this PC:
`C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a72467cac33063d3a`.
Start your own worktree, `git merge origin/claude/vigilant-galileo-l6jqyx`, and copy the raw
folder `tools/comfy/out/uiforge/` (ignored, ~650 MB) from this worktree into yours: every build
reuses the paintings and renders cached there.

---

## 1. The owner's bar

- "I don't want to polish, I want to create perfection." AAA, "above and beyond".
- **"Do we have soul?"**: unique to this world, never generic dark-fantasy UI.
- "painted art is generally better right? ... I want the best": painted or modelled art for
  every frame and ornament where it is better; code draws only the dynamic parts (arcs, numbers,
  accents).
- Never settle; remake rather than skip; verify at full resolution, at the size the player
  sees it; be critical of your own work and go back to what you missed.

## 2. My brief (from the coordinator), in full

You are the UI art lead, continuing from a predecessor (handoff in this file's git history at
`5b94d2e`). Merge its branch, read its handoff. The UI design lead owns UI code; work only on assets
(godot/art/ui, tools/uiforge, Blender and ComfyUI sources) until it says its merge is pushed, then
merge and build on it. The list: 1) level and heart medallions modelled in Blender like the art's
ring; 2) skill icons that show a person instead of the thing (leap, smoke, mirror, echo, wraith,
feint) and any soft at 17 px; 3) weak item icons (pelt, hide, dust, seed, root); 4) uncommon and rare
cards quieter than the legendary; 5) a modelled logo; 6) stat icons as assets; 7) hover states
screenshotted. Ask "do we have soul?" of every piece, judged at its shown size. One rebuild command:
`tools/uiforge/build.py`. The GPU is shared: free ComfyUI between jobs. Keep `docs/team/ui_art.md`
as a one-page status. Commit and push at milestones with tests green.

Later, from the coordinator: after the redesign merge, in order: the pieces the new layouts ask
for (globe rim and glass, medallion ring, well, slab, header, banner, pillar, console, open book;
the draft cards refit to 320x500); adapt the heart medallion's idea to the globe; screenshot and
iterate; remake the icons that read as blobs the modelled-and-painted way. Latest: wire the stat
marks; finish the emblems; the redesign's pieces. The UI design successor (ac76f400913a109cd) is
building character creation and will register portrait cards for you to paint.

## 3. The soul (locked; `docs/UI_ART_BRIEF.md` 2.6)

Brannoc's iron, the binders' gold, the Morrow's light: smith's work from the Waystation (strap
iron, planished, ragged edges; frames hang from lamp-iron brackets with outward scrolls), the
binders' twisted wire and square coin with its round hole, the ember asleep in the holes and
awake where there is power. Emblem: the seven-link chain with one link pried open, ember at the
break. Rarity is a road (common road iron, uncommon the Verge, rare the Low Ford's rime, epic the
binders' violet, legendary the Order's dawn gold, evolution the chain breaking).

## 4. What is done (all pushed and merged)

- **New method, reliefs** (`tools/uiforge/relief.py` + `blender_relief.py`): a piece is drawn
  in numpy as height + materials (iron, iron_dark, gold, chain, ember, stone, bone, leather,
  paper, silk, glass, soot) at render resolution, worn by curvature (bright on convex edges,
  grime in hollows; computed in file px so any supersampling wears alike), emission where it
  burns; Blender renders it as a one-vertex-per-pixel mesh under the house light (the same world
  and suns as `blender_frames.py`). Then `paintover.py` at 0.15-0.30 gives the hand, with small
  exact parts (wire, chain), emissive parts and calm middles protected; the painting is cached by
  the render's content hash. Helpers: `rope` (twisted wire round a circle), `coin` (the binders'
  coin), `bar` (drawn strap iron along a path), `ragged`, `hammered`.
- **Round pieces** (`medals.py`, `build.py medals`): `hud/medal_level.png` (the Legion's seal:
  planished ring forge-welded at its foot, wire, seven notches, ember in the gap at its foot);
  `medallion/ring.png` (every design medallion: chamfered band, wire in a channel at 88% where the
  code's arc runs, four binders' coins with sleeping ember, open inside 78%); `hud/globe_rim.png`
  (the heart's idea grown: the binders' chain coiled round the globe in a channel, the open link
  with its ember held in a lamp-iron collar at the head, short scrolled arms); `hud/globe_glass.png`
  (light only: a leaded window caught upper left, a cool rim lower right, a shade at the edge).
  Also `hud/medal_heart.png` and the heart-stone `icons/glyph_color/heart.png` (no longer shown:
  health is a globe now).
- **Frames** (`pieces.py`, `build.py pieces`; `chrome.py` for the Blender-curve ones):
  `frames/header.png` (plain band, heavy foot strap with wire and nails; repeats 512),
  `pillar.png` (stele: strap and wire, raised collar seat for the 120 px medallion, plinth with two
  coins, brackets at the shoulders), `crest_card.png` (strap, wire, coins, brackets, a paler crest
  plate the code tints), `crest_row.png` (low rows: no crest plate, the code's tint is the crest),
  `banner.png` (oxblood-stained face, brackets; the centre stone is the code's), `book/open.png`
  (oxblood leather, blind-tooled, iron corner caps with coins, laid paper pages with chain lines,
  a gutter that curves, stitching; pages kept even where the words go), `book/ribbon.png` (pale
  ivory silk, swallowtail, the code dyes it), `ornaments/plaque_rule.png` (coin with ember, wire
  thinning to a knop), and in `chrome.py`: `console.png`, `well.png` (sunk, shadow along the top,
  light along the foot), `slab.png` (raised block). Draft cards lengthened to 736x1096 through their
  calm middle (`cards.lengthen`, run by `build.py cards`).
- **Stat marks** (`valueglyphs.STATS`, `build.py glyphs`): `icons/glyph/stat_<Stat enum lower>.png`
  for the 15 standing lines (value art, the code tints). **Not wired** (see Next).
- **Seen in game** at 1920x1080 (shots `godot/.shots/m3_*`, ignored): HUD (globe, console, ring),
  Self (pillars, medallions, slabs), Journal (book, ribbons), creation (crest rows, banner),
  arts (crest cards, ring), draft (cards), result (banner, ring), talk (banner), pack (well).

## 5. In progress

- **Emblems** (`tools/uiforge/emblems.py`): icons remade as modelled emblems: shapes (signed
  distances in a 100-unit square), materials and heights, lit by the house matcaps
  (`forge.Surface.shade`), burning parts emissive, the school's glow round them (the guide); then
  Krea img2img at 0.5 (`paint` one by one, or `paint_many` = one queued graph via `krea.i2i_many`);
  then `emblems.fit(key, src)` cuts it on the guide's silhouette into `icons/glyph_color/KEY.png`.
  24 designs written (mirror, wraith, leap, blink, smoke, echo, feint, hourglass, embers, aegis,
  howl, expand, retaura, frostaura, pyre, risen, herd, tether, umbral, consecrate, drain, static,
  book). Painted: mirror and wraith (seed 1200, raw in `tools/comfy/out/uiforge/emblems/`). The
  painted mirror (a cracked hand mirror) is far better than the old figure; the wraith reads as a
  purple fog. **No icon file is replaced yet; no pick recorded.**
- **Weak items**: `items.T2I` prompts (pelt, hide, root, seed, dust, bomb) and `items.t2i()`;
  `items.fit(key, (1100, j))` takes a pick. Not painted yet.

## 6. Next, in order

0. **First: the UI design lead's (a69858664f1d3dd29) requests on the owner's "drab, low effort,
   low def" note.** It is cutting frame nesting: panes lose their frames, full pages show the live
   world blurred behind them, boxed sub-panels become group headers, and frames are kept only on
   things you act on. It asks for, at true resolution:
   (a) a **column divider**, vertical, about 24 px wide, tileable in height (e.g. a gold line with a
   stone at its middle; the stone must sit outside the tiled part);
   (b) **one heavy frame for the hero plate** (the figure on each page);
   (c) a **lighter card frame** for cards and tooltips;
   (d) a **backdrop texture layer**: RGBA, mostly transparent (grain, a little smoke at the edges,
   ember light) laid over the blurred world, not an opaque fill;
   (e) a **section-header ornament** if `plaque_rule` is wrong for small headers.
   It will message when the frameless layout is pushed; merge it and paint to where the pieces
   sit. `pieces.iron_card` (strap, wire, coins, brackets as options) and `relief.bar` / `relief.coin`
   are the quickest starts for (a)-(c).
1. **Wire the stat marks** (the coordinator asked; it is UI code, so tell the UI design lead or do
   it yourself if they agree): in `godot/src/Ui/Book.cs` (the standing, ~line 48) put
   `Glyphs.Icon($"stat_{stat.ToString().ToLower()}", 16, Style.GoldDim)` before each label; the
   keys are exactly the `Stat` names lower-cased. Screenshot `--open character`.
2. **Emblems**: in `Emblem.guide`, lower the whole-shape halo for dark schools (0.35 -> ~0.15) so
   a dark silhouette sits on black with a rim, not in a fog; then `python tools/uiforge/emblems.py
   --many`; compare each against the old icon at 128/44/17 px; `fit` the better; record the picks
   in `emblems.py` (a PICKS table like `iconpicks.py`) and add an `emblems` group to `build.py`
   after `icons`. Then the remaining soft ones (zone_*, nova_*, tether2/_mark, siphon, herd_great/
   _hunt, command, kindling, living_flame, scent, execute, beam_*); judge the whole family together.
3. Weak items (5 above); uncommon and rare cards louder (`batch.py cards2`, 0.66-0.70).
4. Portrait cards for creation when ac76f400913a109cd registers them (read its status page).
5. Logo as a relief (`relief.py` suits letters); hover-state shots (`shots.py` has pad variants
   via `--pad --keys`; no hover option exists in the harness).
6. Known code bug to chase with the UI design side: `Plaque._Draw` draws the mirrored painted
   rule through the title (a negative-width rect is not a flip); I reported it with a fix
   (`DrawSetTransform` with scale -1). It shows on JOURNAL, ASHE, A GREAT BLESSING.

## 7. Decisions (why)

- Reliefs over Blender curve specs for round and shaped pieces: any form (notches, links,
  facets, deckle) with real light, exact and scriptable; Blender curves stay for tiling straps.
- Paint-over only adds the hand (0.15-0.30); higher melts small parts.
- The globe carries the heart's idea (the chain anchored in a heart) rather than a heart icon.
- The crest row has no crest plate: at 92 px high a plate crowds the words; the code's tint is it.
- Icons: the thing itself, never a person (prompts with an action paint people).
- Stat marks as value art (tinted by the code) like the interface's other marks, not colour.

## 8. Failures and why

- First level medallion: notches too big, the well glowed like a sign (fixed: thin gap glow, short
  notches). First book: pages blotchy and pink (paper grain off, ivory tone, chain lines faint).
- Header with lapped lames read as grey bricks at 50% (simplified to a plain band and a foot).
- Glass rendered in Blender: two big blobs, read as a ball; painted procedurally instead.
- A paint-over put out the globe's ember (fixed: emissive parts protected).
- A Blender wear term scaled with supersampling, so ss=2 pieces looked ghostly (fixed in
  `relief.paint`).

## 9. Gotchas

- Godot loads the import: run `--headless --path godot --import` (shots.py does) and commit PNG
  and `.import`. Godot rewrites hundreds of unrelated `.import` files: restore them with
  `git checkout --pathspec-from-file=LIST --` (this worktree refuses compound git commands; write
  the list to a file first).
- `godot/assets` must be a junction to `public/assets` (README in `docs/handoff` history); untracked
  `*.cs.uid` can block a merge: delete them.
- ComfyUI (127.0.0.1:8188) is shared and the queue can hold long LTX video jobs (an i2i waited
  15 min): batch with `krea.i2i_many`/`t2i_many`; free models after (`POST /free`); never kill it.
  It crashed once on 2026-10-04 and was restarted headless (`.venv\Scripts\python.exe main.py
  --listen 127.0.0.1 --port 8188 --extra-model-paths-config <AppData\Roaming\Comfy Desktop\
  instance-model-paths\inst-*.yaml>` from `ComfyUI-Installs\ComfyUI\ComfyUI`).
- Blender is at `C:\Users\munch\Tools\blender-4.5.14-windows-x64\blender.exe`; a relief of
  3400x1704 (the book) takes ~4 min; most pieces 30-60 s.

## 10. Collaborators

- Coordinator / main session (relays the owner): `main`.
- UI design lead (its handoff is written; successor ac76f400913a109cd builds character creation).
- Face lead (generating faces on the shared ComfyUI), voice, animation, story, combat: roster in
  `docs/team/README.md`.

## 11. Read first

1. `docs/team/README.md`  2. this file  3. `docs/team/ui_art.md`  4. `docs/UI_ART_BRIEF.md` (2.6, 4.9)
5. `tools/uiforge/build.py`  6. `tools/uiforge/relief.py`, `medals.py`, `pieces.py`
7. `tools/uiforge/emblems.py`, `icons.py`, `iconpicks.py`  8. `godot/src/Ui/Ornate.cs`, `UiArt.cs`

HANDOFF READY: docs/handoff/ui_art.md on worktree-agent-a72467cac33063d3a@HEAD
