# Skins: add a direction as skins/<x>.py (copy skins/a.py), run `python frames.py B all`
Layers are premultiplied float RGBA 1920x1080 (draw.layer()); `L` = drawn over, `Lhalo` = added light (screen blend).
- `grade(rgb, tod) -> rgb`: the world's grade (tod 'day' | 'night'); rgb is the nofoot frame, float 0-1.
- `pools(graded, world, lit_px, stop) -> rgb`: light the world gives back around lit lamps (return graded to skip).
- `roads(L, Lglow, segs, stop)`: segs = dicts a, b (screen px, already trimmed rim to rim), kind cold|lit|fuse|path, phase.
- `road_glow(rgb, Lglow, stop) -> rgb`, `light(rgb, Lhalo) -> rgb`: how glow layers land.
- `lamp(L, Lhalo, x, y, kind, st, stop, dim, focus, onpath, gate, seed)`: st lit|available|unlit|blocked; kinds incl. wick (22) and turn (34).
- `label_size(text, stop) -> (w, cap_h)`, `label(L, x, y, text, stop)`: centered on (x, y).
- `card_height(c) -> h`, `card(L, x0, y0, c)`: c = name, kind, place, line, feeds [(glyph, carried)], feeds_text, price, state, state_color, prompts [(pad icon, word)].
- `header(L, Lhalo, h)`: h = count, sub, post, night, coins (active index), layout_name, keys [(pad icon(s), word)].
- `prompts(L, rows)`: lower right, rows of [(icons, word)].
- `wick(L, Lhalo, w) -> {'turn0': (x, y, r), 'lamp<row>_<i>': ...}`: w = rect, glyph, name, rank, counts, strands, sum.
- `seat_ring(L, Lhalo, (x, y, r), panel_bottom)`: the chosen seat's ring and wick stem (drawn after the foot).
Shared, not skinned: board.py, state.py (the mock state), view.py (stops, lamp sizes), foot.py (the HUD foot), text.py, draw.py (Patch: 3x SDF patches).
Order (frames.py): grade, pools, roads, glow, halos, lamps, labels, wick, card, header, FOOT, seat ring, prompts.
Direction C (half panel) needs its own frames layout: pass a different View/field and skip foot.composite.
Optional hooks (B): `begin(view, tod)` before grade (the skin gets the view); `ornament(rgb, view) -> rgb` after pools, under the roads; `LABEL_SKIP` (group kinds whose labels the skin draws itself); `VALLEY_DY` (px the Valley view sits lower).
`lamp(...)` also gets `fade` (1 / 0.65 / 0.40 by road steps from the lit set, brief §5) and `near` (within 3 steps: blue keeps its cobalt); frames passes gate=0 where notches don't show. foot.paint_seat repaints seat 3 as Sunder.

## Running it (UI 26, 2 Nov)
The layout is the scratch folder's: `lamps_mock/` = the old SCR, with `mock/` (this), `shoot/` (bd2.sh + shot.py shoot the backdrops into `shoot/out/`), `c_work/` (caches: the cleared panel grounds, her masks from `she_mask.py`) and `board_v2.json` at the top (copy `godot/data/content/board_v2.json` there). The repo keeps code and briefs only; the backdrops and caches are in `survivorsunchained_inputs/scratch_ui25/` (copy `shoot/out/` and `c_work/` back beside `mock/`).
Run from `mock/`: `python frames_c.py all` (C), `python frames.py A all` (A), `python owner_sheet.py` (the owner's sheet). B is cut (skins/b.py kept for the record).
The HUD foot is swappable: set `LAMPS_HUD_WT` to the checkout whose HUD art and `hud_a_geo.json` to use, and `LAMPS_FOOT_TAG` to the prefix of a foot/nofoot shot pair taken with that HUD. A's `WICK_RECT` (frames.py) is still fixed for UI 24's HUD; the build places it from the geometry (brief §16).
Briefs: `briefs/` holds every builder and judge brief, judge r1's verdict and judge r2's (condensed).
