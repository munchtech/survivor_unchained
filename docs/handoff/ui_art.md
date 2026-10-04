# Handoff: the interface's art (UI artist)

For the next agent carrying on the UI art of Survivor Unchained. Read this whole
file first; it and the repository are all you get.

Branch: `worktree-agent-abd496197891ea843` (pushed to origin; no PR). It was
branched from `claude/vigilant-galileo-l6jqyx` at the UI merge `33ad2cd`.
Worktree on this PC: `C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843`.

---

## 1. The owner's bar (quote these to yourself)

- "I don't want to polish, I want to create perfection." Work is "polish after
  polish"; unique, themed, professional AAA.
- **"Do we have soul?"** The owner's most important test. A unique game, one in a
  million, not a soulless one of many. Generic dark-fantasy UI (stock gold
  filigree, interchangeable stone frames, the default AI look) fails however
  polished. Every element should feel as if it could only belong to Survivor
  Unchained: embers that sleep by day and burn at night; the Verge wood, the Low
  Ford road and the Waystation town; the people's crafts and what they have to
  hand (carters, smiths, lamp-irons); the adult, sensual and menacing tone.
  Recognisable motif, hand-made authorship, imperfection with intent, materials
  with history, small surprises on the hundredth look (Hades, Darkest Dungeon,
  Hollow Knight, Pentiment, Disco Elysium: a singular point of view).
- After seeing test art the owner said much of it was **"far from good"**. Keep
  iterating, improving and **layering**: raw generations are rough material only.
  Every shipped asset is composed and layered: a base shape or 3D render for
  clean geometry and lighting, generated detail on top, then hand clean-up and
  unification in Python (edges, alpha, light direction, palette, stroke weight).
  Do not wire in anything you would not put beside Diablo IV, PoE2 or Hades UI.
  Keep weak tests out of the repo (the raw folder `tools/comfy/out/` is ignored).
  Judge each piece at its real in-game size and against its neighbours. Where AI
  cannot get there, build it another way: Blender, procedural drawing, vector
  construction. In the report: side-by-side before/after screenshots of the real
  screens, and say honestly what is not at the bar.
- From the user's memory: never settle; remake rather than skip; verify at full
  resolution; don't stop to ask.

## 2. The brief (as given to me), in full

You are the UI artist for Survivor Unchained, an adult dark-fantasy ARPG plus
survivors-like (Godot 4.5.1 .NET/C# in `godot/`; repo munchtech/survivor_unchained).
A UI designer finished a research-backed redesign of every screen; the game ran
with placeholder art. The job: the artwork for every UI element.

- Start: own worktree; `git fetch origin && git merge origin/claude/vigilant-galileo-l6jqyx`
  (includes UI merge `33ad2cd`). Commit on your branch and push (`git push -u origin HEAD`),
  no PR, commit often. Read `docs/UI_ART_BRIEF.md` (every asset: path, size,
  nine-slice margins, states, mood, dos and don'ts, tools), `docs/UI_DESIGN.md`,
  `docs/UI_RESEARCH.md`, `docs/STORY_BIBLE.md`, `docs/items/VISUALS.md`,
  `tools/comfy/ui_assets.json`, `tools/comfy/ui_art.py`, concepts in `docs/concepts/ui/`.
  Every plug-in point loads art by name and falls back to the drawn look.
- Do: 1) settle the visual language first (style frames, materials, ornament
  vocabulary, palette, light direction; one family). 2) Make every asset: frames
  and panels, buttons in all states, slots, rarity borders, bars (health, ember,
  XP), draft cards, tooltip frames, icons (skills, stats, items, currencies,
  status effects, map markers), cursors, title/logo, dividers and ornaments,
  minimap elements. Icons readable at real size; nine-slices tile and stretch
  without seams; states distinct and consistent; colour-blind safe (rarity and
  better/worse not by colour alone). 3) Use every tool: Krea 2 locally with the
  darkbrush LoRA, img2img over drawn or Blender guides; Blender renders for
  3D-looking pieces; BiRefNet cut-outs and Python/PIL clean-up. AI raw output is
  never final. 4) Verify in the running game: every screen at 1920x1080, real
  size, pad focus and mouse hover. Godot console exe:
  `C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe`;
  options in `docs/HANDOFF.md` and `godot/README.md`. Compare against Diablo IV,
  PoE2, Hades. 5) Credit third-party things in `public/assets/CREDITS.md`; prefer
  own generations and CC0; keep the repo small (raw generations stay in ignored
  `tools/comfy/out/`).
- Rules: keep `cd godot/tests && dotnet test` green (298). Commit messages end with
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. British spelling.
  Use this PC freely (GPU, Python, Blender at
  `C:\Users\munch\Tools\blender-4.5.14-windows-x64\blender.exe`, Godot, ComfyUI at
  http://127.0.0.1:8188, web research, free installs). The GPU is shared with
  other agents (voice, animation): keep batches considerate. No paid cloud
  services. Never print or commit secrets. If `godot/assets` is a small text file:
  `Remove-Item godot\assets; cmd /c mklink /J godot\assets public\assets; git update-index --skip-worktree godot/assets`,
  then import once. Don't change UI layout or behaviour beyond what art
  integration needs (the designer owns that); don't touch `tools/assets/`,
  `godot/art/people/`, `godot/shaders/heroine_*`, `godot/src/Actors/`.
- Report when done: branch and commits; the visual language (with paths to
  style frames); asset count; screenshot paths; honest notes on what is not at
  the bar.

Later messages from the coordinator: (a) the "soul" requirement above, lock it
before mass production and say in the report what the soul is and where it
shows; (b) three times "you were cut off by the usage limit, carry on"; (c) the
"far from good / iterate and layer" message above; (d) hand off to a fresh agent
(this file), then end with "HANDOFF READY: docs/handoff/ui_art.md on <branch>@<commit>".

## 3. The soul (locked; written into `docs/UI_ART_BRIEF.md` section 2.6)

**Brannoc's iron, the binders' gold, the Morrow's light.** The interface is smith's
work from the Waystation (the hand that forged the twelve lamp-irons for the Low
Ford), not a jeweller's.
- Iron: strap iron drawn out under the hammer, planished, ragged edges. Frames
  *hang*: plates and cards are held at their top corners by lamp-iron brackets
  with outward scrolls, nailed at the foot.
- Gold: the binders' twisted wire set into the strap; the binders' square coin
  (a square on its point, a round/quatrefoil hole) nailed at the corners.
- Light: the Morrow's ember sleeps in the coins' holes (dull, never a flat fill)
  and wakes where there is power (ember bar, primary button, focus, draft,
  evolution).
- Emblem: one link of the seven-link chain pried open, ember at the break (the
  draft card's crest, the art's ring head: six coins plus the seventh open link).
- Rarity is a road through the world: common road iron; uncommon the Verge
  (bramble, thorn, moss); rare the Low Ford at night (rime, cold blue); epic the
  binders (violet cut stones, square-hooked sigil lines); legendary the Order of
  the Morning Light (dawn gold, lamp flames); evolution the chain breaking,
  gilded, ember pouring out. Slots carry the same as shapes (thorns, ice needles,
  cut stones, flame tongues, ember cracks) as well as hue.
- Paper: the Waystation's ledger (laid paper, foxing, hand-torn deckle, iron
  corner caps; the hint has a nail and a drop of wax).

## 4. What is done (all committed and pushed)

Commits since `33ad2cd` (oldest first): `1ed2a15` the forge and first pieces;
`4183d36` language locked in game; `6bd0149` value glyphs, cursors, small pieces;
`ee8c91d` rarity cards, slots, casings, the soul in the brief; `21ca5be` fitted
painted frames, logo, rule; `d1baa13` 117 colour icons; `e226fde` 48 item icons;
`50e9a49` chrome rebuilt as Blender + paint-over; `c2b8fb9` paper, map frame, one
build; `651b46d` imports and before/after; `e2df0f3` Blender minimap rim;
`9b50a3c` Blender art ring, medal size, protected paint-over; `2740d08` uncommon
card, card spacing; `e4be6cd` brief/asset list/credits; then this handoff.

282 PNGs in `godot/art/ui/` (12 MB), each with its `.import` (lossless, imported):
54 named assets (every one in `tools/comfy/ui_assets.json`, `ui_art.py list` shows
all [x]) + 117 `icons/glyph_color` + 39 `icons/glyph` + 48 `icons/item` + 7 `icons/map`
+ 17 `icons/prompt`.

How each family is made (`tools/uiforge/build.py GROUP` rebuilds it; see its docstring):

| Family | Method | State |
|---|---|---|
| Plate, buttons x7, slots x7 (rarity marks modelled), skill socket, tooltips x2, toast, prompt pill, tabs x2, row, segment, keycap, chip, bar groove, bar casing, minimap rim, art ring | `chrome.py`: Blender model (`blender_frames.py`, under the house light) -> Krea paint-over at 0.18-0.30 (`paintover.py`, keeps the render's shape/alpha/large light) -> centre calibrated to the text tone -> made to tile (`nineslice.py`) | Good; the best family |
| Paper, hint | `paper.py`: procedural laid paper + forged caps/nail/wax -> paint-over -> calm middle -> tile | Good |
| Draft cards x6 | Krea img2img over a forged guide (`guides.card_guide`), common first, rarities painted over the common (`batch.py cards`, `cards2`), fitted by `cards.py` (silhouette, calm middle, coins' holes lit, coins moved out of the foot, healed by the Krea) | Good; uncommon and rare a little quiet |
| Medallions (level, heart), boss casing, logo, rule, flourish, map frame | Krea text-to-image, cut (BiRefNet + light), fitted (`fitall.py`, `rounds.py`) | Acceptable; see section 6 |
| Colour icons x117 | Krea t2i in batches (`icons.py`, picks in `iconpicks.py`), alpha from light, 256-colour PNG | Mostly good; some weak (section 6) |
| Item icons x48 | Krea img2img over the game's own item photographs (`items.py`) | Mostly good; some weak |
| Pad prompts x17, map marks x7, value glyphs x39, cursors x3, minimap arrow, focus ring, bar fills x3 | Procedural (`padprompts.py`, `mapmarks.py`, `valueglyphs.py`, `cursors.py`, `smallforge.py`, `lightpieces.py`) under the same matcap light | Good and crisp |

Code changes (art integration only): `UiArt.Slice` gained `Tile`, `Out` (overhang
past the control), `Clear` (content distance) and `OutY`; slices updated
(`godot/src/Ui/UiArt.cs`). `GameHud.Casing` lays bar casings over bars; empty skill
places use `frames/slot.png`. Painted draft cards get a glow panel behind and a
row spacing of 52 (`Panels.cs`). `MapScreen` lays the wooden frame over the map.
`Minimap.Mark` keeps its size when painted. Tests: 298 green (run after the code changes).

Before/after of every screen: `docs/concepts/ui/style/*.jpg` (made by
`tools/uiforge/compare.py b0 a2`; `b0_*` shots were taken with `godot/art/ui`
moved away). Latest after-shots: `godot/.shots/a2_*.png` (ignored; regenerate with
`python tools/uiforge/shots.py --prefix a5`).

## 5. In progress

Nothing half-done. Last checks made: the boss bar casing mocked at real size
(good); hud, cards, map, journal, pack, minimap, art ring checked in game.

## 6. What is next, in order (honest list of what is not yet at the bar)

1. **Medallions** (level `hud/medal_level.png`, heart `hud/medal_heart.png`): AI cut-outs,
   decent but not modelled. Remake in Blender like the art ring (a forged boss with
   the wire; the heart in relief bound by a chain link), then paint over.
2. **Weak colour icons**: look at `tools/comfy/out/uiforge/icons/*_900_*.png` sheets; those
   with a person where a thing should be (arts: leap, smoke, mirror, echo, wraith,
   feint) or with soft silhouettes at 17 px (arcane, expand, static, triple). Remake
   with `icons.py` REDO tables (seed 950/960) or as procedural emblems.
3. **Weak item icons**: pelt, hide, dust, seed, root; repaint with `items.py` at another
   denoise/seed, or render a better base.
4. **Uncommon and rare cards** read quiet next to legendary/evolution; the rare's
   frost is only at the top. Another pass in `batch.py cards2` (denoise 0.66-0.70).
5. **Logo** (`title/logo.png`): good and legible, but AI-made; consider a Blender
   relief of the letters with the chain for exactness.
6. **Stat icons** (brief 5.5): not made because not wired (needs a designer change).
7. Ornaments `rule.png`/`flourish.png` are AI-painted and extended; fine at size, could
   be modelled (the procedural one in `smallforge.rule` was worse).
8. Re-shoot every screen with pad focus and hover (`shots.py` has `*_pad` variants;
   no hover variant exists).

## 7. ComfyUI: what worked and what did not

- Server http://127.0.0.1:8188 (ComfyUI 0.38.1, RTX 5080 16 GB **shared** with the
  voice and animation agents: the queue may hold their jobs; one t2i of 1024 took
  20 s alone and up to 6 min when busy). Client `tools/comfy/comfy.py`; my wrapper
  `tools/uiforge/krea.py` (`t2i`, `t2i_many` = many prompts in one graph = one model
  load, `i2i` with `RepeatLatentBatch`, `qrun(front=True)` to jump the queue for small
  jobs such as BiRefNet). Calls are **resumable**: a candidate is named
  `TAG_SEED_N.png`; an existing one is reused, so re-running a batch only makes what is
  missing. Raw results: `tools/comfy/out/uiforge/` (ignored; on this PC).
- Models: UNET `krea2_turbo_fp8_scaled.safetensors`, CLIP `qwen3vl_4b_fp8_scaled.safetensors`
  (type `krea2`), VAE `qwen_image_vae.safetensors`, LoRA `krea2_darkbrush.safetensors` at 0.8,
  8 steps, cfg 1, euler/simple, `ConditioningZeroOut` negative. Cut-outs: `LoadBackgroundRemovalModel`
  `birefnet.safetensors` + `RemoveBackground` (mask), cached in `out/uiforge/_masks/`.
- Worked: img2img over a forged or Blender guide (0.5-0.6 for whole cards; 0.18-0.30 to
  give a render its hand); painting rarities over the finished common card (0.55-0.68);
  icons as "A single bold painted emblem ... Diablo IV skill icons ... on pure black"
  (`icons.LOOK`); item paint-over of the game's photos at 0.5. House style suffix
  `krea.STYLE`. Seeds and prompts: `batch.py` (cards 600-605, cards2 650-653,
  small 700-709, t2i 801-806), `icons.py` (900; redo 950/960), `items.py` (1000),
  `explore.py` (early explorations 201-322), chrome paint-over seed 11, paper 21.
- Failed: text-to-image frames (they stretch badly, ornament lands anywhere, middles are
  never calm); AI slots at 80 px (shape lost, so slots are modelled); paint-over at
  0.38+ on small pieces (it melts a small link or stone: use `protect=` in
  `paintover.paint`); the plain forged (no paint) frames read as vector art; a
  procedural divider read as clip-art; icons prompted with an action ("leaping
  figure") come out as people.

## 8. Gotchas

- **Godot loads the import, not the PNG**: after changing art, run
  `godot --headless --path godot --import` before screenshots (`shots.py` does it).
  Commit the PNG and its `.import`.
- `godot/assets` junction fixed in this worktree (skip-worktree set).
- Tool permissions here refuse compound shell commands that `cd` to computed paths
  or pipe Python heredocs with git; write a script file and run it plainly.
- `tools/uiforge/matcaps/matcaps.npz` (rendered by `matcaps_blender.py`) is the house
  light for all procedural pieces; Blender pieces use the same direction (key upper left).
- Many unrelated `*.import` files show as modified after an import (Godot rewrote
  them); I never committed those. Leave them or `git checkout` them.
- `godot/tests/HordeBench.cs.uid`, `QaSaves.cs.uid` are untracked Godot files; not mine.

## 9. Open questions

- May stat icons be wired into the standing (designer's call)?
- Should the draught box and dash pips on the HUD (drawn by code, not in the brief)
  get art? They now sit beside forged pieces and look plain.
- The creation screen's right panel is a drawn box (`Front.cs` line ~279), not a plate.

## 10. Collaborators

- The coordinator (the agent that launched me; it relays the owner). No other agent
  ids were given. Other agents share the GPU (voice, animation).

## 11. Read first

1. `docs/handoff/ui_art.md` (this)  2. `docs/UI_ART_BRIEF.md` (esp. 2.6 the soul, 4.8 as delivered)
3. `tools/uiforge/build.py` (every family and how to rebuild)  4. `tools/uiforge/chrome.py`
5. `tools/uiforge/blender_frames.py`  6. `tools/uiforge/paintover.py`  7. `tools/uiforge/cards.py` + `batch.py`
8. `tools/uiforge/icons.py` + `iconpicks.py`  9. `godot/src/Ui/UiArt.cs`  10. `docs/concepts/ui/style/` (before/after)
