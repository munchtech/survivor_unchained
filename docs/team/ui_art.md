# UI art: status

Agent a0bff3ffe4d3ad748 (successor to aa9c11f1e40170a4d). Branch `worktree-agent-a0bff3ffe4d3ad748`.
Full brief and history: `docs/handoff/ui_art.md`.

## State (2026-10-04)

- **The rule:** one ornamental frame per screen (the window). Inside it, hierarchy comes from spacing, type, tonal panels and thin rules. Empty slots are quiet, rarity colour goes on filled slots only, and ember is used only for meaning.
- **The kit has its material** (`tools/uiforge/kit.py`; not applied in the game):
  - **Ground:** the binders' goatskin (`page/morocco.png`, a pin-head grain, the dye uneven, its tone a step above the page). UiArt draws it at 1:1 under each frame, so the grain never stretches. The code is in (`UiArt.Slice.Ground`, `GroundBox`), and it does nothing until a slice names a ground.
  - **Edges:** only light and shade.
    - Raised panels are lit on the top and left edges, worn at the corners, with a soft shadow.
    - Wells and slots are pressed in. A filled slot gets a rarity hairline and a glow rising from its foot.
    - Rules are blind-tooled.
    - The open tab gets an ember underline. Other tabs are words alone.
    - Buttons have their states; primary has an ember foot.
    - Keycaps, chips, price tags, rows and `row_on` (ember edge).
    - The track's nodes are taken, next (ember) and later. Round plus and minus buttons, and a slim ring.
  - **The frame:**
    - the head and foot bands: dark goatskin and a smooth forged rail;
    - the side panel: a goatskin border, a blind fillet, and plain iron corner caps as on heavy books, with the vellum inside at 1:1.
- **Judging:** `tools/uiforge/kitboard.py` lays the kit on a page at 1080 or 1440, blending as Godot does. It can lay a specimen page, or Self and the Pack as UI design's greyboxes lay them. Outputs go to `tools/comfy/out/uiforge/kit/board_*.png`.
- **Greyboxes:** UI design (aab47bfdab5955dac) sent Self, Pack, Storeroom, Trader and the bench to the coordinator. They are waiting for the owner's approval.

## Next

1. Shoot Self and the Pack in game with the kit applied locally, at 1080 and 1440. Send before and after crops to the coordinator. Revert after.
2. GPU batch (`scratchpad/uiart2/gpu_batch1.py`):
   - Krea macro materials (vellum, goatskin), to compare with the drawn ones;
   - the flask (`items.T2I["flask"]`);
   - Crashing Leap's second concept (the guide now has no halo and no rays, and has gold cracks).
3. Page vellum: the current one is blotchy and streaky at 1:1. Replace it with the material that reads truer.
4. Once the owner approves the layouts, dress them (`kit.py --apply` writes the art and UiArt.Frames together).

## Key decisions

- **Material goes in a ground drawn at 1:1, not in the nine-slice.** TileFit stretches what it tiles, and a panel's grain must not change with its size.
- **The kit applies as a set:** art and slice margins together (`kit.apply` patches UiArt.Frames). Old art with new margins breaks.
- **Panels are goatskin, the page is vellum, the frame is goatskin and iron:** one book, three surfaces.
- **No bright specks in the backdrop's grain.** Over the vellum, they read as stars.
- **Shots delete the old picture before a run** (`shots.py`), so a failed run can't pass off a stale one.

## Notes for other areas

- **UI design:** use the frame names from my message:
  - panel, well, slot, slot_N, rule_h, rule_v, side, tooltip, chip, price, row, row_on;
  - button and its states, keycap;
  - nodes: taken, next, later, round, round_spend.

  Tabs need "tab_hover" and "tab_pressed", or hover shows a button plate. The section mark before headings (`Section`) should go under the rule.
- **Legal:** sheets of every shipped icon are in `docs/legal/icon_check/`. We can't fetch others' art here, so the visual side-by-side against Diablo IV and Hades needs someone with the games open.
