# Lane E's rules for lane B: skill effects in the den (16 Nov)

Copy of `docs/design/LOOK_BIBLE.md` "Effects in the den: the rules for lane B" on `demo-look` (the bible copy wins once demo-look merges). The bands: the same file's "The demo frame: the den" table. Judge 1 on the den frames: FAR; every fx row MISS.


1. **Steel is the only loud thing.** Every pixel of her skill strokes sits in the steel row's bands (edge 0.63 / 0.149 / 58, mid 0.81 / 0.165 / 79, core L 0.90+ at C 0.05 or under: `fx_language.json`, the physical school). The stroke's colored part reaches C 0.14-0.19. These are the only world pixels at C 0.14+ in the den. Measured 16 Nov: the Sunder crescent is C 0.064 (cream, it vanishes on warm earth); the Bladestorm arcs are C 0.10.
2. **Hit puffs are dust or steel, never pink.** Impact puffs and sparks sit at h 55-80. No fx pixel at C 0.04+ falls in h 290-25 (magenta, pink, violet). Measured: the puffs read h 18-21.
3. **Blood is dark red.** Droplets, sprays and fx blood decals use the blood row: L 0.36-0.52, C 0.072-0.110, h 25-42. Measured: droplets at C 0.164, decals at h 21-24.
4. **Sunder reads at the dungeon camera** (the PoE/Diablo play camera, 1080p):
   - (a) Its ground mark is a shock ring plus a crack, drawn at the skill's real hit radius, so what shows is what it hits.
   - (b) At its peak the mark spans at least 1.5 times her on-screen height (she is about 85 px tall at 1080p), and it lies on the ground in front of her. It never sits under her body or her HP plate.
   - (c) The core holds L 0.90+ for at least 3 frames at 60 fps, which puts it 0.35+ over the den floor (L 0.40-0.56). The steel edge then fades over 0.25-0.4 s.
   - (d) The crack decal stays at least 1 s, as a deeper tone of the ground (the line row, L 0.08-0.22). It is never black.
5. **Bladestorm is a full ring.** Steel arcs go all the way round her, with at least 3 visible in any frame, at C 0.14-0.19.
6. **Boss telegraphs** (E and B; whoever builds them): a hostile-red edge (`ui_language` 0.565 / 0.192 / 30) and a fill at 15% opacity or less. No flat hatched slab: the 16 Nov lair frame had one covering about 9% of the play area.
7. **Check before the judge.**
   - Shoot at the play camera. E's Sunder frame: `--auto idle --horde 10:wolf --horde-hp 40 --horde-arc 0:120:2.5:2.5:6 --no-spawn --slots sunder --press 1:6.3:3,0:hold=0.6`. For Bladestorm, use `--horde-arc 0:360:2.5:3:9 --grant-union bladestorm --resolve-at 0.5:100 --press 1:2:0,0:hold=6`.
   - Add an `fx_steel` box (and a `blood` box where blood shows) to a masks manifest. Use the format of `tools/style/demo_look_masks.json`.
   - Run `python tools/style/demo_look_check.py frame PNG --masks M.json`.

