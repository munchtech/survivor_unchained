# UI art: status

Agent a0bff3ffe4d3ad748 (successor to aa9c11f1e40170a4d). Branch `worktree-agent-a0bff3ffe4d3ad748`.
Full brief and history: `docs/handoff/ui_art.md`.

## State (2026-10-05)

**The rule**
- One ornamental frame per screen. Hierarchy comes from type, spacing, tonal panels and pressed rules.
- Soul comes from world objects that mean something: the chain, coals, the lamp. Each is made the way the chain is, every one its own, and placed once.
- In the owner's words: "thats the kinda soul were lookin for. SOUL."

**In the game** (applied with `kit.py --apply`, which writes the art and UiArt.Frames together):
- **The kit.** Goatskin ground at 1:1 under:
  - panels, wells, slots (rarity only when filled), buttons, keycaps, chips, rows and the tooltip.

  Over the goatskin:
  - pressed rules, the tabs' underlines, the track's nodes and round buttons;
  - the head and foot bands;
  - the side panel's goatskin border and iron corner caps.
- **The title's broken chain** (`ornaments/title_chain_l/_r`): on page titles that don't ride the tab chain.
- **The tab chain** (`chain/`, UI design's ChainTabs; approved):
  - heavy forged links, cold, warm and hot per link;
  - five heated under the chosen tab, the middle one pried open;
  - anchored in eyelets;
  - its feel set in `chain.json`.

  `chainanim.py` is the motion's reference.
- **The chain's sound** (`Sfx.ChainSlide`): modal, made from struck-iron partials. The A/B against the old FM is in godot/.shots/tabchain_{modal,fm}_*.mp4.
- **Coals and the dish** (`coal/`): Self's points to spend.
- **Toast lights** (`hud/spark`, `glint`) and `hud/pointer_legendary`.
- **The Set mark** (`icons/glyph/link_set`, with _14 and _24 versions).

**In progress**
- GPU batch: vellum and goatskin macros, the four icon repaints (red_cord, lamp_glass, scar_glass, flask) and Crashing Leap.

## Next

1. The watch-lamp (one, a light source in the UI) and painted pieces (sparingly).
2. Glyphs:
   - `link_closed` and `link_broken` (locked and unlocked);
   - `up` and `anvil` (about 14 px).
3. Judge the GPU batch:
   - the icons at 56 px beside the set, rejecting any shape that reads as a letter;
   - commit the flask here and send red_cord, lamp_glass and scar_glass to the crafting branch;
   - the page ground.
4. Shoot each layout as UI design builds it (Self, Pack, Storeroom, Trader, Bench), at 1080 and 1440.

## Key decisions

- **Material lives in a ground drawn at 1:1, never in a stretched slice.**
- **Art and slice margins go in together** (`kit.apply` patches UiArt.Frames).
- **Chains are anchored, never faded.** An alpha fade reads as an effect, not an object.
- **Sound is modal, from real iron's ratios.** FM read as cheap. No third-party recordings: the owner wants everything ours.
- **Every link, coal and spark is its own** (variants per index), so nothing repeats as one image.
- **Renders check they made a new picture.** Shots delete the old one, and chain and coal renders check file times.

## Notes for other areas

- **UI design (a4fdbc49786ba8b7f):** frame names as agreed. The chain.json fields drive ChainTabs. The coal and dish art is at coal/.
- **Performance:** ChainSlide plays about 180 short synth voices over a second.
- **Legal:** sheets of every shipped icon are in docs/legal/icon_check/. The side-by-side against Diablo IV and Hades needs someone with the games open.
- **Turns:** Blender work takes `blender`; ComfyUI takes `gpu`.
