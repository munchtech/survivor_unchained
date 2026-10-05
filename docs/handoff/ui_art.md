# Handoff: the interface's art (UI art lead)

For the next agent carrying on the UI art of Survivor Unchained. Read `docs/team/README.md`
first (the team's bar, how we work, safety, roster), then this whole file, then
`docs/team/ui_art.md` (the one-page status). The previous handoff is in this file's git
history at `a2bd171`; what still matters from it is folded in here.

Branch: `worktree-agent-a1a394643aabfb169`, merged into the integration branch at `53c5857`
(565 tests green). Worktree on this PC:
`C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a1a394643aabfb169`.

**Before any build, copy the cached paintings and renders** (ignored by git, ~1.6 GB; every
build reuses them, and the picks below point into them). Copy, never move or delete:
`C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a1a394643aabfb169\tools\comfy\out\uiforge\`
into your own worktree's `tools/comfy/out/uiforge/` (robocopy `/E`; its exit code 1 means "copied").
It holds my predecessor's caches as well as mine (`emblems/`, `card3/`, `items_t2i/`,
`relief/`, `paintover/`, `guides/`).

---

## 1. The owner's bar (quotes)

- "I don't want to polish, I want to create perfection." AAA, "above and beyond".
- "Do we have soul?": unique to this world, never generic dark-fantasy UI.
- "painted art is generally better right? ... I want the best."
- Latest, on the pages' persistent framing and backdrop (the themed panel frames, the leather
  backdrop, the flat panels): **"looks a little drab and low effort and low def"**. The
  coordinator's reading: remake frame and backdrop at true resolution for 1920x1080 and up, crisp,
  no upscaled texture, with depth, material and craft (forged iron with real light, worked leather,
  tooling or vellum, not flat black), readable behind text; agree the layout with the UI design
  lead; **show the owner before/after at full resolution**.

## 2. My brief, in full

From the coordinator, in order: 1) the 24 skill icons redesigned as modelled objects (two were
painted; the wraith read as purple fog): finish them and replace the game's icons; 2) the weak item
icons (pelt, hide, dust, seed, root, the blasting ember); 3) louder uncommon and rare cards; 4) a
modelled logo; 5) hover-state screenshots; 6) portrait cards for character creation, with the UI
design successor. Wiring the stat icons into Book.cs is UI code: agree it with the UI design lead.
ComfyUI is shared: batch many paintings as one job, `POST /free` between jobs, never kill it.
Commit and push at milestones; `dotnet test` in `godot/tests` before every commit; British
spelling; check everything in game at full resolution; hand off at ~500k.

Added later: the owner's "drab" note became **the priority** (section 1). The UI design lead
(a69858664f1d3dd29) reworked the layout (the live world blurred and warmed behind every page,
frameless columns that fade downward, iron only on what is acted on: pillars, cards, buttons,
wells) and asked for six pieces (section 5). The legal lead asked that prompts never name a
product (done, section 7).

## 3. The soul (locked; `docs/UI_ART_BRIEF.md` 2.6)

Brannoc's iron, the binders' gold, the Morrow's light: smith's work from the Waystation (strap
iron, planished, ragged edges, lamp-iron brackets with outward scrolls), the binders' twisted wire
and square coin with its round hole, the ember asleep in the holes and awake where there is power.
Emblem: the seven-link chain with one link pried open, ember at the break. Rarity is a road
(common road iron, uncommon the Verge, rare the Low Ford's rime, epic the binders' violet,
legendary the Order's dawn gold, evolution the chain breaking).

## 4. Done (all merged)

- **Icons, 33 modelled emblems** (`tools/uiforge/emblems.py`; picks in `emblems.PICKS`; `build.py
  emblems`, which runs after `icons`): mirror, wraith, leap, blink, smoke, echo, feint, hourglass,
  embers, aegis, howl, expand (a Ford lamp), retaura, frostaura, pyre, risen, herd, tether,
  umbral, consecrate, drain, static (a twisted-iron conduit), book (a wayfinder's chart), and the
  arts that still showed people: boot (Sprint), horns (Bull Rush: a bull-helm with a binders'
  ring), chain (Grapple Chain), shield (Shield Bash), mark (Mark Prey), wing (Vault). Method: each
  design is shapes (signed distances in a 100-unit square) with heights, materials and grain
  (`Emblem.lay`, `Emblem.rope` for the twisted wire), lit by the house matcaps, set in its school's
  glow (the guide), painted over on the Krea at 0.5-0.65 (`paint_many` = one queued graph), and cut
  on the guide's silhouette (`fit`). Seen in game (arts list, HUD art slot, draft).
- **Items** (`items.py`): pelt, hide, root, seed, dust, bomb repainted from words (`items.T2I`,
  picks in `items.PICKS`). The pelt's first take was a living wolf's head (reads as a summon);
  now a tied fur bundle (seed 1110).
- **Logo** (`logo.py`, `build.py logo`; `build.py painted` no longer fits the old one):
  SURVIVOR over UNCHAINED in Cinzel's variable font at weight 900 (OFL, kept in
  `tools/uiforge/fonts/` with its licence), forged steel with a deep chamfer, the seven-link
  chain between the words, its middle link pried open with the ember in the break and its glow
  on the air, strap iron out to two binders' coins. Seen on the title at 1080.
- **Cards** (`cardcolour.py`, picks in `cards.PICKS`): the common card dressed before the paint.
  Uncommon: bramble with leaves up both sides, moss low, the iron a little green (painted at
  0.46). Rare: crystalline rime and hoarfrost on every edge, icicles, a cold sheen (painted at
  0.3 and laid back over its dressing, `merge` keep 0.6).
- **Page pieces** (`pages.py`, `build.py pages`): `frames/header.png` remade (worked oxblood
  leather, tooled only where nothing is written, a slim forged rail with the binders' wire; seen
  in game). Built but not yet wired: `page/backdrop_grain.png`, `page/backdrop_edges.png`,
  `frames/column_divider.png`, `frames/column_divider_stone.png`, `ornaments/section_mark.png`.
- **Prompts** name no product (c457cc9): "hand-painted with painterly brushwork" etc.
- `shots.py` has a `pack_mats` screen (the materials in the pack).

## 5. In progress: the six pieces for the UI design lead

Agreed with a69858664f1d3dd29 (they wire them in code; tell them each file's margins as it
lands). All files at twice the shown size (UiArt halves them); margins below are in shown px.

| piece | file | state | slice / use |
|---|---|---|---|
| header | frames/header.png 1024x200 | built, seen | (0,0,0,12) Tile, as before |
| backdrop | page/backdrop_grain.png 512x512; page/backdrop_edges.png 1920x1080 | built, previewed over a shot only | grain tiled, edges stretched, over the blurred world, under the shade |
| column divider | frames/column_divider.png 48x1120 + column_divider_stone.png 64x64 | built | (0,24,0,24) Tile; the middle is exactly one 512-shown period; the stone drawn at each divider's middle in code |
| hero plate | frames/hero_plate.png 512x512 | **code written, not rendered** | (56,56,56,56) Tile, Out 12; frames Self's figure (536x560) and the Pack's (~300x360) |
| light card | frames/card_light.png 320x320 | **code written, not rendered** | (20,20,20,20) Tile; tooltips and the result's cards (crest_card stays on choice and trait cards) |
| section rule | ornaments/section_mark.png 24x24 | built | ~10 px before 14 px heavy caps on their baseline |

Layout facts from them: page columns run 920 tall at x 40-1880 with 24-30 px gaps for dividers.

**The new PNGs have no `.import` files yet** (header.png had one already). Run
`<godot console exe> --headless --path godot --import` (shots.py does this), commit the new
`.import` files, and restore the unrelated ones Godot rewrites (section 9).

## 6. Next, in order

1. `python tools/uiforge/pages.py hero_plate card_light`; look at both at file size and over a 1080
   shot; fix the corner brackets' reach and the vellum's tone as needed.
2. Import (above), commit, send the margins (section 5) to a69858664f1d3dd29.
3. When they are wired: before/after shots at full resolution for the owner. "Before" = the
   integration branch's pages before 0165e94 / my h1-h2 shots in `godot/.shots/` (ignored); "after" =
   shots once wired (self, pack, arts, journal, stash, shop).
4. **Crashing Leap** (`leap`): weak at 90 px in the HUD's art slot (a grey arc on a dark disc). Every
   take (seeds 1310/1320/1330, 0.5-0.7) shares it, so it is the concept: needs a bold silhouette
   with value contrast (e.g. a forged iron spike or maul driven into a lit crater, or the arc made
   crisp and warm). The physical school's prompt drains colour (see `emblems.COLOURS`).
5. Judge the crafting lead's three new item icons (moon_draught, flask, fur_braid, their branch at
   dcd68cd) against the set; repaint if they drift.
6. Portrait cards for creation (UI design side registers them; read `docs/team/ui_design.md`).
7. Hover-state shots (no hover option in the shot harness yet; `--pad --keys` exists).
8. Before launch, the legal lead's check: each shipped icon/frame side by side with the named
   commercial icon sets; remake any close to a specific one.
9. Still open from before: the remaining soft icons in the old painted family (zone_*, nova_*,
   tether2/_mark, siphon, herd_great/_hunt, command, kindling, living_flame, scent, execute, beam_*)
   as emblems, judged with the whole family; stat marks wiring (UI design's call; keys are
   `stat_<Stat lower>`); `Plaque._Draw` draws the mirrored rule through the title (reported to UI
   design, fix with `DrawSetTransform` scale -1).

## 7. Decisions (why)

- Icons: the thing itself, never a person; modelled for the silhouette, painted for the hand.
- The guide's whole-shape halo never lies over the object (it washed the first lamp and mirror),
  and is faint for steel and shadow (`HALO`): a dark thing in a fog of its own colour loses its edge.
- Every design sits inside the guide's glow circle (radius ~46 units): `Emblem(school, zoom, at)`
  scales a design to fit instead of redrawing it; the saved mask is faded with it.
- Prompts in plain words, no product named (legal lead aa12c130ddf4b904c).
- Logo letters from the game's own face at weight 900: exact and heavy; at 600, wide-set, it read
  like a book cover.
- Cards: colour laid into the guide before the paint; the words must ask for it too.
- Page pieces: reliefs at twice size, no paint-over on thin strips (a painting is made at a
  megapixel and softens a 100-px band). Nine-slice surfaces are periodic over exactly the repeat
  (`pages.periodic`), so no seam blending.
- Backdrop in two layers (tiled grain, stretched edges): one 4K grain PNG would be ~25 MB.

## 8. Failures and why

- Wraith 1: purple fog (halo). Wraith 2 (side view, separate rags): an octopus. Front-view hood worked.
- Feint as a crescent beside a blade: a scythe, three times. A curved arrow round a standing blade works.
- Smoke as bevelled circles: grapes/cauliflower; soft-edged lay (`soft=`) plus paint fixed it.
- Leap: the physical school's "cold white steel" words painted it grey; `COLOURS` overrides help
  but the concept is still weak (section 6.4).
- Horns at 0.55 painted colour static; 0.65 was clean.
- My `replace_fn` patch helper swallowed the module tables after the last design (it skipped to
  the next `def`); restored from git. Bound replacements by the next design, not the next def.
- Cards: the base words said "a few" leaves, "faint" light, rime "along the top", so paintings
  stayed quiet. At 0.5 Krea also invented extra coins and chains on the rare. Merging back onto
  the guide fixes colour but ghosts where shapes differ; at keep 0.6 over a 0.3 paint it is clean.
- Logo v1: pink chain (an over-strong warm tint), a pinprick ember; v2 fixed both (glow layer).
- `coin_piece`: a coin set on its point needs its diagonal to fit (0.62 of the box), and an
  ember is a crusted coal, not a flat orange disc.

## 9. Gotchas

- This worktree refuses compound shell commands (heredoc + other commands, `&&` chains with
  scripts): write patch scripts to the scratchpad with Write and run them with one `python` call.
- `godot/assets` must be a junction to `public/assets` (`New-Item -ItemType Junction`), then
  `git update-index --skip-worktree godot/assets`.
- Godot rewrites unrelated `.import` files (`godot/art/people/paint/*`): `git diff --name-only --
  godot/art/people > list` then `git checkout --pathspec-from-file=list --`. Many others show as
  modified only through autocrlf; `git diff` is empty for them; stage by path.
- ComfyUI's queue is shared with long jobs: a 46-painting graph took ~20 min. `krea.i2i_many`
  returns a dict; `cardcolour.paint` returns a list. Always `POST /free` after.
- Emblem guides and masks must be regenerated together; `fit` cuts on the saved mask. Rendering all
  guides takes ~2-3 min (the rope is a fast union now).
- Icons are shown inside round medallions on dark discs: judge at 128/44/17 px and on a dark disc.
- Blender: `C:\Users\munch\Tools\blender-4.5.14-windows-x64\blender.exe`; the logo renders in ~3-4 min.
- My viewing scripts (look sheets, at-size discs, crops) lived in my session's scratchpad and are
  gone; they are a few lines each over `emblems.fit` and PIL.

## 10. Collaborators

- Coordinator / main session: `main`.
- UI design lead: a69858664f1d3dd29 (the page layout; wires the six pieces).
- Legal lead: aa12c130ddf4b904c (prompts; pre-launch icon check).
- Crafting lead: a7debf1459f14dfe7 (painted three item icons with the pipeline, dcd68cd).
- Face lead, skills lead and video jobs share ComfyUI. Roster: `docs/team/README.md`.

## 11. Read first

1. `docs/team/README.md`  2. this file  3. `docs/team/ui_art.md`  4. `docs/UI_ART_BRIEF.md` (2.6)
5. `tools/uiforge/pages.py` (the page pieces), `build.py`
6. `tools/uiforge/emblems.py`, `cardcolour.py`, `logo.py`, `relief.py`
7. `godot/src/Ui/UiArt.cs` (frames and their slices), `Overlay.cs` (Page, Backdrop)
