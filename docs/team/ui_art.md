# UI art: status

Agent a72467cac33063d3a. Branch `worktree-agent-a72467cac33063d3a` (merges the integration branch and
the UI design lead's). Handoff from before: `docs/handoff/ui_art.md`. One rebuild: `python tools/uiforge/build.py`.

## State (stopped at the owner's usage limit, 2026-10-04)

- **Every piece the redesign asks for is made and seen in game** (shots `godot/.shots/m3_*`):
  `medallion/ring.png`, `hud/globe_rim.png` + `globe_glass.png`, `frames/console.png`, `well.png`,
  `slab.png`, `header.png`, `pillar.png`, `crest_card.png`, `crest_row.png`, `banner.png`,
  `book/open.png`, `book/ribbon.png`, `ornaments/plaque_rule.png`; draft cards lengthened to
  736x1096 (320x500 shown, one to one). The level medallion is the Legion's seal (seven notches).
- **Stat marks made as assets** (not wired; the designer's call): `icons/glyph/stat_<Stat enum,
  lower case>.png` (maxhealth, armor, regen, healing, dodge, damage, critchance, critdamage, cooldown,
  area, movespeed, dashcharges, pickupradius, xpgain, goldgain), value art the code tints, in
  `valueglyphs.STATS` (built with `build.py glyphs`). Wiring: `Glyphs.Icon($"stat_{stat.ToString().ToLower()}", 16, ...)`.
- **Icon remake in progress** (`tools/uiforge/emblems.py`): each icon modelled as shapes, lit, set in
  its school's glow (the guide), painted over on the Krea at 0.5, cut on the guide's silhouette.
  Designs written: mirror, wraith, leap, blink, smoke, echo, feint, hourglass, embers (arts) and
  aegis, howl, expand, retaura, frostaura, pyre, risen, herd, tether, umbral, consecrate, drain, static,
  book. Painted so far: mirror and wraith (seed 1200, in `tools/comfy/out/uiforge/emblems/`). The
  painted mirror is far better than the old figure; the wraith's silhouette is mushy (see Next).
  **No icon file is replaced yet.**
- Weak items: second takes from words prepared (`items.T2I`: pelt, hide, root, seed, dust, bomb);
  not painted yet.
- How everything is made: `relief.py` + `blender_relief.py` (reliefs), `medals.py` (round),
  `pieces.py` (shaped frames), `chrome.py` (Blender curve frames), `emblems.py` (icons).

## Next (in order)

0. Handed off (`docs/handoff/ui_art.md`). First for the successor: the UI design lead's
   (a69858664f1d3dd29) requests on the owner's "drab" note: a tileable vertical column divider,
   a heavy hero-plate frame, a lighter card/tooltip frame, an RGBA backdrop texture layer, and maybe
   a small section-header ornament. See handoff section 6, item 0.
1. Emblems: lower the whole-shape halo for dark schools (0.35 to ~0.15) so silhouettes are dark
   against black with a rim, not a purple fog (wraith); then `python tools/uiforge/emblems.py --many`
   (one queued graph for all: the queue is shared with long LTX video jobs, one i2i job waited 15 min).
   Pick per key with `look_em`-style sheets at 128/44/17 px, `emblems.fit(key, src)` to write the icon,
   record picks in emblems.py. Judge each against the old icon; keep the better.
2. Then the rest of the soft icons (zone_*, nova_*, tether2/_mark, siphon, herd_great/_hunt, command,
   kindling, living_flame, scent, execute, beam_*...).
3. `python -c "import items; items.t2i()"` then pick and `items.fit(key, (1100, j))`.
4. Portrait cards for character creation when the UI design successor (ac76f400913a109cd) registers them.
5. Logo as a relief; hover-state shots (the shot harness has `--keys` for the pad, no hover yet).

## Key decisions

- Reliefs for exact, scriptable forms with real light; paint-over only adds the hand (0.15-0.3).
- Icons: the thing itself, never a person; silhouette from the model, hand from the paint.
- Paint-over caches by the render's content hash; emissive and small parts are protected.
- `krea.i2i_many`: many paintings in one queued graph (one place in the shared queue).

## Notes for other areas

- ComfyUI had crashed on 2026-10-04; it is running again (someone restarted it before my start did).
- UI design: the mirrored plaque rule is drawn through the title (`Plaque._Draw`), reported.
- Raw renders/paintings: `tools/comfy/out/uiforge/{relief,paintover,emblems}/` (ignored, on this PC).
