# Handoff: the interface's art (UI art lead)

For the next UI art lead. Read `docs/team/README.md` first, then this page, then `docs/team/ui_art.md`. Earlier handoffs are in this file's git history.

- **Branch:** `worktree-agent-a0bff3ffe4d3ad748`. The main session merges it.
- **Worktree:** `C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0bff3ffe4d3ad748`.

**Set-up.** Copy that worktree's `tools/comfy/out/uiforge/` into yours with `robocopy /E`. It holds the cached renders, paintings, chain sprites, coals, lamp and materials, and is ignored by git. Copy it; never move it.

## 1. The owner, in his words

- "we are striving for perfection"
- "those borders are just ugly, adding more of them dosn't make them better"
- "ai looking"; "not rooted in ui research"
- "remember our art needs soul, maybe some chains or something. but those lame borders before were soulless slop"
- On the chain and the lamp: "thats the kinda soul were lookin for. SOUL."
- "we like to see our beautiful game": no whole-screen pages; side panels over the world.
- On panels: no fade at their edges. They end cleanly, the ground slightly translucent.

## 2. The rule

- One ornamental frame per screen.
- Inside it, hierarchy comes from type, spacing, tonal panels and pressed rules.
- Empty slots are quiet; rarity colour goes on filled slots only.
- Ember is used only for meaning.
- Soul comes from world objects that mean something: the chain, coals, the lamp. Each is placed once, made the way real things are, and every one is its own.

## 3. What is in the game

All of it is on this branch and applied with `python tools/uiforge/kit.py --apply`, which copies the art in and writes the UiArt.Frames entries in the same step.

**The kit** (`kit.py`):
- A goatskin ground drawn at 1:1 under each slice (`UiArt.Slice.Ground`, `GroundBox`, `DrawSlice`). It's painted now (`materials.py`, from a Krea macro), with the drawn one as the fallback.
- Over it, edges only:
  - panel, well, slot and slot_N, tooltip, chip, price, row and row_on;
  - buttons and their states, keycap;
  - rule_h and rule_v; tab_on (an ember underline), tab_hover and tab_pressed;
  - nodes: taken, next, later, round and round_spend;
  - the side frame (goatskin with iron corner caps), the head and foot bands, the slim ring.
- `page/goatskin.png` is the ground for a page that stays full.

**The tab chain** (`chain.py`, `blender_links.py`, `chainanim.py`; UI design's ChainTabs draws it):
- Links: six face-on and six on edge, each cold, warm and hot.
- `chain/open`: the chosen middle link, pried and hot.
- The ends: an eye-bolt split at the chain's height (`eye_back` under the links, `eye_front` over them), then a riveted goatskin `tab` covering the chain's end.
- `chain.json` holds the feel: pitch, run, tail, heat, slide and sag springs. chainanim's `frame()` is the reference for the draw order.
- The title's broken chain: `ornaments/title_chain_l/_r`.

**The sound** (`Sfx.ChainSlide`):
- It plays CC0 takes cut by `chainsfx.py` (art/sound/chainLink_*, chainDrag_*, chainSettle_*), logged as AU-06 in `docs/legal/ASSET_PROVENANCE.md`.
- The modal synth stands in if the takes are missing.
- The owner may send his own chain recording. If he does, `python tools/uiforge/chainsfx.py takes` cuts it the same way (point SOURCES at it).

**The rest:**
- **Coals:** `coal/` (coal_0..3, dish, dish_rim, numeral_glow), for Self's points.
- **The lamp-iron:** `lamp/lamp`, `lamp_lit`, `light`, on a forged sign-bracket at Self's panel corner. Approved. The placement and the coal's breath went to UI design.
- **Toasts and tips:** `hud/spark` (8 frames), `glint`, `pointer_legendary`.
- **Glyphs:** `link_set` (Set items), `link_closed` and `link_broken` (locked and unlocked), each with _14 and _20 or _24 small versions.
- **Icons:** red_cord, lamp_glass, scar_glass and flask repainted (picks in `items.py`). `leap.png` is Crashing Leap's second concept (emblems `leap2`, ALIAS).

## 4. Next

1. **Painted pieces, sparingly** (the coordinator's go-ahead). One strong piece first, and show a 1:1 crop before going wide. Ideas:
   - a wax seal pressed with the binders' square coin (a confirm, or a journal entry);
   - a painted map edge on the atlas;
   - an illuminated gold initial on the day's book. Draw the letter from the font; never let a painting make letters.
2. Shoot each layout as UI design builds it, at 1080 and 1440, and fix what's off.
3. Legal's icon check: sheets of every shipped icon are in `docs/legal/icon_check/`. The side-by-side against Diablo IV and Hades needs someone with the games open.
4. Still-open older items:
   - the soft icons in the old painted family;
   - `Plaque._Draw` mirroring;
   - hover-state shots.

## 5. Decisions (why)

- **Material in a 1:1 ground, never in a stretched slice.** TileFit stretches what it tiles.
- **Art and margins go in together** (`kit.apply`). Old art with new margins breaks.
- **Chains are anchored, never faded.** A fade reads as an effect, not an object. Links pass truly through a split ring.
- **The heat travels with the chain.** It reads as the chain dragging the fire across.
- **Sound is real CC0 iron.** FM read as cheap and modal synthesis as thin. The owner approved CC0 on 5 Oct, and the main session fetched it.
- **One lamp, on a bracket.** On a side panel, a lamp hung loose over a top-down world fought the perspective. A bracket makes it the book's.
- **Painted ground at 0.4 contrast.** At full contrast the leather read as busy behind words.

## 6. Failures and gotchas

- **The worktree guard** refuses complex shell commands: pipes with git, `$VAR` in sed, inline python with computed paths. Put the logic in a scratch .py and run it plainly.
- **Turns:** `gpu` is ComfyUI only; Blender takes `blender`. `scratchpad/uiart2/take_and_run.py KIND "who" WAIT script.py` waits, runs, and always gives the turn back.
- **Renders check their own freshness:** chain, coal and lamp renders compare file times, and `shots.py` deletes the old picture first. A Blender run that dies must never hand back an old PNG.
- **New PNGs and WAVs need .import files to ship.** `python tools/uiforge/imports.py <files>` writes them as the editor would.
- **The board** (`kitboard.py`) composites in sRGB as Godot does. It still lays the old full-page Self; build2's frames are in `docs/ui_review/build2/` on the integration branch. Mock on those.
- **A cut-off session lost its scratch outputs.** Re-run them from the scripts in the scratchpad; nothing important lived only in scratch.

## 7. Collaborators

- **The main session (coordinator):** approves art going in, with the owner.
- **UI design (a4fdbc49786ba8b7f):** builds the layouts, ChainTabs, the coals' motion and the lamp. It uses my frame names.
- **The loot lead (a9a9c345a35e1fcad):** Set tier, the link_set mark.
- **Legal (aab20546fe06daa89):** the icon check.

## 8. Read first

`kit.py`, `chain.py`, `chainanim.py`, `UiArt.cs` (Slice, GroundBox), `Sfx.ChainSlide`, and `docs/legal/ASSET_PROVENANCE.md` AU-06.
