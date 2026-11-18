# Asset provenance: status

Agent a80ff0c7fd988b178. Branch `worktree-agent-a80ff0c7fd988b178`, from the integration branch.

## Current state (2026-10-04)

The first full audit is done and pushed:

- `docs/legal/ASSET_PROVENANCE.md`: 102 inventory rows, with a summary, the top risks, owner questions, the AI table, licence quotes, and an appendix of all 323 AI-made shipped files;
- `public/assets/CREDITS.md`: corrected and completed;
- `docs/legal/REPLACEMENT_PLAN.md`: a staged plan with owners.

Nothing has been removed or replaced.

Rows by risk:

| Risk | Rows |
|---|---|
| none | 18 |
| low | 54 |
| medium | 10 |
| high | 9 |
| UNKNOWN | 11 |

All licences were checked at the source:

- Poly Haven: 78 ids, through its API;
- ambientCG: 10 ids, through its API;
- Sketchfab: 15 models, through its API, including their descriptions;
- Quaternius, KayKit and Kenney pack pages;
- OpenGameArt entries;
- Zenodo;
- MakeHuman and MPFB licence files;
- Hugging Face model cards;
- the licence PDFs embedded in the models.

## Top findings

- **The boar**: CC BY label, but its page says "personal use only". The legal lead rules it a blocker.
- **The heroine's body (`234.glb`)**: the generator and source picture are unknown. The same gap covers the hero's and the older woman's figures, and the reference sheet.
- **Krea 2 Community License**: outputs may be used commercially only under US$1M revenue, and Krea can terminate on 30 days' notice. Krea painted 225 UI files, the marks and both faces.
- **The Chevalier Sword and Medieval Shield**: modelled from other artists' concept art.
- **No licence notices ship**, and `all_resources` exports unused third-party files.
- **CREDITS errors fixed**:
  - added KayKit (five packs), nine Poly Haven outfit textures, MakeHuman, Mixamo and Kimodo, and the engine, fonts and AI disclosure;
  - credited the mace's modeller (Yavuz Temel);
  - recorded Peter Nox's earlier name;
  - corrected the paths of the Poly Haven models.

## Key decisions

- `CREDITS.md` stays in `public/assets`, and keeps the line formats the fetch tools check, so re-running them adds no duplicates.
- Risk scale: "UNKNOWN" counts as high until the owner answers. No licence has been guessed.
- "Ships" means the Godot export as configured (`all_resources`, through the `godot/assets` link), not only the files the game loads.

## Next

1. Get the owner's answers to the seven questions in `ASSET_PROVENANCE.md`, then update PE-05, PE-06, PE-09, UI-05, AI-14, AI-15, DA-02 and DA-03.
2. Re-run the AI appendix and file counts before release (`git ls-files`).
3. Audit again after each replacement lands.

## Blockers

Owner answers (questions 1 to 7).

## Notes for other areas

- **Legal (aa12c130ddf4b904c):** findings sent. Their rulings so far:
  - the boar is a blocker;
  - Krea 2 is a business risk at US$1M;
  - the unknown bodies are blockers until answered;
  - the sword and shield should be fixed;
  - the notices and the export filter should be fixed;
  - Moonfire, Starfall and Fan of Knives should be renamed;
  - The Ember Watch (DA-02) is a blocker until the owner confirms he owns it;
  - the anime body is to come out of the build for ratings as well as licence reasons;
  - a Meshy plan question is added to owner question 1.

  Their brief: `docs/legal/LEGAL_BRIEF.md`, issue 5 (f52c1b4d on `worktree-agent-aa12c130ddf4b904c`).
- **Everyone:** add any new third-party or AI asset to `public/assets/CREDITS.md` and `docs/legal/ASSET_PROVENANCE.md`, with its source URL and licence, before it lands. Never ship `tools/make3d` output.
- **UI art:** the Krea-made list in the appendix assumes every `chrome.py` piece is painted over. Please confirm the boundary.

## Ours, painted from nothing

- `godot/art/world/flora/den/` (den_rock_a-d.gltf/.bin, den_rock_atlas.png; 15 Nov 2026): ours, built and painted from nothing by `tools/look/den_rocks.py` (meshes from `tools/assets/env_rocks.py` mesh --form den: an ellipsoid cut by planes, in code; the atlas painted in code from the meshes' own points); no photo, scan, paid credit or Meshy. Risk: none.
- `godot/art/dungeon/den/` (albedo, normal, arh, layers.json; 15 Nov 2026): ours, painted from nothing by `tools/look/ground_paint.py`, set "den" in `godot/data/look/ground.json`; no photo, scan or outside source. Risk: none.
- `godot/art/dungeon/den/decals.png` (+ `decals.json`; 15 Nov 2026): ours, painted from nothing by `tools/look/den_decals.py` (the den floor's bones, rib cages, skulls, hides, fur, twigs, leaves, blood, roots and pebbles, drawn in code); no outside source. Risk: none.
- `godot/art/dungeon/den/bank_albedo.png`, `bank_normal.png`, `bank_arh.png` (+ `bank.json`), `bank_decals.png` (+ `bank_decals.json`) and `roots_preview.jpg` (15 Nov 2026), and `floor_decals.png` (+ `floor_decals.json`) and `floor_preview.jpg` (15 Nov 2026, `build floor`: long floor roots, the camera-side frame masses, whole pits in plan with their lip, far wall and void; the floor kind repainted 15 Nov (long thin roots, same source rule); FPAL lip and slate colours set by number FROM den_boss.png's pits): ours, painted from nothing by `tools/look/den_roots.py` (the den's root bank and root-cluster decals, a height-field tube compositor drawn in code; the palette sampled by number from the owner-approved den targets); no outside source. Risk: none.
- `godot/art/dungeon/den/pit_decals.png` (+ `pit_decals.json`, `pit_decals.png.import`) and `pit_preview.jpg` (15 Nov 2026, `build pits`, round 7: two big pits painted at the game holes' own size, mouth r 5.5 m in a 15 m rect, slate risers and shelves falling to black, roots along, over and hanging across the mouth; four shallow walkable hollows, dish r 1.4-2.4 m, damp earth, raised rim, leaf litter, thin roots; PPAL colours set by number FROM den_boss.png's pits and hollows): ours, painted from nothing by `tools/look/den_roots.py` (same height-field tube compositor and palettes as the rows above; the preview shows a crop of the owner-approved den_boss.png beside them for comparison only, nothing copied); no outside source, no paid credit. Risk: none.
- `godot/art/dungeon/den/boulders_paint.png`, `boulders_form.png` (+ `boulders.json`; 15 Nov 2026, paint pass 3 round 7: six companion boulders and two big ones): ours, painted in code from nothing by `tools/look/den_boulders.py` (forms are ellipsoids cut by planes in code, cast along the play camera and painted in 2D: values, light shards, knife-chip strokes, moss, cracks, ink); the lit and shade colours set by number FROM the owner-approved den_room.png, its forms by eye; the preview shows crops of den_room.png beside them for comparison only, nothing copied; no photo, scan, model, outside source or paid credit. Risk: none.
- `godot/art/dungeon/den/set_src/B1.png` (15 Nov 2026; the den's painted set, round 10): made by ChatGPT image generation on the owner's account (the ChatGPT imaging route the owner allows), prompted with the owner-approved concepts `den_room.png` and `den_boss.png` as references (prompt and file size in `set_src/PROVENANCE.txt` and `survivorsunchained_inputs/gpt_den/PROVENANCE.txt`); built into `art/dungeon/den/set/` by `tools/look/den_set.py`. Risk: as the ChatGPT imaging route (owner's account; log kept).
- `godot/art/dungeon/den/set_src/B1b.png` (15 Nov 2026; the den's painted set, round 10): made by ChatGPT image generation on the owner's account (the ChatGPT imaging route the owner allows), prompted with the owner-approved concepts `den_room.png` and `den_boss.png` as references (prompt and file size in `set_src/PROVENANCE.txt` and `survivorsunchained_inputs/gpt_den/PROVENANCE.txt`); built into `art/dungeon/den/set/` by `tools/look/den_set.py`. Risk: as the ChatGPT imaging route (owner's account; log kept).
- `godot/art/dungeon/den/set_src/B2.png` (15 Nov 2026; the den's painted set, round 10): made by ChatGPT image generation on the owner's account (the ChatGPT imaging route the owner allows), prompted with the owner-approved concepts `den_room.png` and `den_boss.png` as references (prompt and file size in `set_src/PROVENANCE.txt` and `survivorsunchained_inputs/gpt_den/PROVENANCE.txt`); built into `art/dungeon/den/set/` by `tools/look/den_set.py`. Risk: as the ChatGPT imaging route (owner's account; log kept).
- `godot/art/dungeon/den/set_src/B2b.png` (15 Nov 2026; the den's painted set, round 10): made by ChatGPT image generation on the owner's account (the ChatGPT imaging route the owner allows), prompted with the owner-approved concepts `den_room.png` and `den_boss.png` as references (prompt and file size in `set_src/PROVENANCE.txt` and `survivorsunchained_inputs/gpt_den/PROVENANCE.txt`); built into `art/dungeon/den/set/` by `tools/look/den_set.py`. Risk: as the ChatGPT imaging route (owner's account; log kept).
- `godot/art/dungeon/den/set_src/B3.png` (15 Nov 2026; the den's painted set, round 10): made by ChatGPT image generation on the owner's account (the ChatGPT imaging route the owner allows), prompted with the owner-approved concepts `den_room.png` and `den_boss.png` as references (prompt and file size in `set_src/PROVENANCE.txt` and `survivorsunchained_inputs/gpt_den/PROVENANCE.txt`); built into `art/dungeon/den/set/` by `tools/look/den_set.py`. Risk: as the ChatGPT imaging route (owner's account; log kept).
- `godot/art/dungeon/den/set_src/B3R.png` (15 Nov 2026; the den's painted set, round 10): made by ChatGPT image generation on the owner's account (the ChatGPT imaging route the owner allows), prompted with the owner-approved concepts `den_room.png` and `den_boss.png` as references (prompt and file size in `set_src/PROVENANCE.txt` and `survivorsunchained_inputs/gpt_den/PROVENANCE.txt`); built into `art/dungeon/den/set/` by `tools/look/den_set.py`. Risk: as the ChatGPT imaging route (owner's account; log kept).
- `godot/art/dungeon/den/set_src/B4.png` (15 Nov 2026; the den's painted set, round 10): made by ChatGPT image generation on the owner's account (the ChatGPT imaging route the owner allows), prompted with the owner-approved concepts `den_room.png` and `den_boss.png` as references (prompt and file size in `set_src/PROVENANCE.txt` and `survivorsunchained_inputs/gpt_den/PROVENANCE.txt`); built into `art/dungeon/den/set/` by `tools/look/den_set.py`. Risk: as the ChatGPT imaging route (owner's account; log kept).
- `godot/art/dungeon/den/set_src/B4R_2.png` (15 Nov 2026; the den's painted set, round 10): made by ChatGPT image generation on the owner's account (the ChatGPT imaging route the owner allows), prompted with the owner-approved concepts `den_room.png` and `den_boss.png` as references (prompt and file size in `set_src/PROVENANCE.txt` and `survivorsunchained_inputs/gpt_den/PROVENANCE.txt`); built into `art/dungeon/den/set/` by `tools/look/den_set.py`. Risk: as the ChatGPT imaging route (owner's account; log kept).
- `godot/art/dungeon/den/set_src/B5.png` (15 Nov 2026; the den's painted set, round 10): made by ChatGPT image generation on the owner's account (the ChatGPT imaging route the owner allows), prompted with the owner-approved concepts `den_room.png` and `den_boss.png` as references (prompt and file size in `set_src/PROVENANCE.txt` and `survivorsunchained_inputs/gpt_den/PROVENANCE.txt`); built into `art/dungeon/den/set/` by `tools/look/den_set.py`. Risk: as the ChatGPT imaging route (owner's account; log kept).
- `godot/art/dungeon/den/set_src/B6.png` (15 Nov 2026; the den's painted set, round 10): made by ChatGPT image generation on the owner's account (the ChatGPT imaging route the owner allows), prompted with the owner-approved concepts `den_room.png` and `den_boss.png` as references (prompt and file size in `set_src/PROVENANCE.txt` and `survivorsunchained_inputs/gpt_den/PROVENANCE.txt`); built into `art/dungeon/den/set/` by `tools/look/den_set.py`. Risk: as the ChatGPT imaging route (owner's account; log kept).
- `godot/art/dungeon/den/set_src/O1.png` (15 Nov 2026; the den's painted set, round 10): made by ChatGPT image generation on the owner's account (the ChatGPT imaging route the owner allows), prompted with the owner-approved concepts `den_room.png` and `den_boss.png` as references (prompt and file size in `set_src/PROVENANCE.txt` and `survivorsunchained_inputs/gpt_den/PROVENANCE.txt`); built into `art/dungeon/den/set/` by `tools/look/den_set.py`. Risk: as the ChatGPT imaging route (owner's account; log kept).
- `godot/art/dungeon/den/set_src/O2.png` (15 Nov 2026; the den's painted set, round 10): made by ChatGPT image generation on the owner's account (the ChatGPT imaging route the owner allows), prompted with the owner-approved concepts `den_room.png` and `den_boss.png` as references (prompt and file size in `set_src/PROVENANCE.txt` and `survivorsunchained_inputs/gpt_den/PROVENANCE.txt`); built into `art/dungeon/den/set/` by `tools/look/den_set.py`. Risk: as the ChatGPT imaging route (owner's account; log kept).
- `godot/art/dungeon/den/set_src/O3.png` (15 Nov 2026; the den's painted set, round 10): made by ChatGPT image generation on the owner's account (the ChatGPT imaging route the owner allows), prompted with the owner-approved concepts `den_room.png` and `den_boss.png` as references (prompt and file size in `set_src/PROVENANCE.txt` and `survivorsunchained_inputs/gpt_den/PROVENANCE.txt`); built into `art/dungeon/den/set/` by `tools/look/den_set.py`. Risk: as the ChatGPT imaging route (owner's account; log kept).
- `godot/art/dungeon/den/set_src/F1.png` (15 Nov 2026; the den's painted set, round 10): made by ChatGPT image generation on the owner's account (the ChatGPT imaging route the owner allows), prompted with the owner-approved concepts `den_room.png` and `den_boss.png` as references (prompt and file size in `set_src/PROVENANCE.txt` and `survivorsunchained_inputs/gpt_den/PROVENANCE.txt`); built into `art/dungeon/den/set/` by `tools/look/den_set.py`. Risk: as the ChatGPT imaging route (owner's account; log kept).
- `godot/art/dungeon/den/set_src/F2.png` (15 Nov 2026; the den's painted set, round 10): made by ChatGPT image generation on the owner's account (the ChatGPT imaging route the owner allows), prompted with the owner-approved concepts `den_room.png` and `den_boss.png` as references (prompt and file size in `set_src/PROVENANCE.txt` and `survivorsunchained_inputs/gpt_den/PROVENANCE.txt`); built into `art/dungeon/den/set/` by `tools/look/den_set.py`. Risk: as the ChatGPT imaging route (owner's account; log kept).
- `godot/art/dungeon/den/set_src/F3.png` (15 Nov 2026; the den's painted set, round 10): made by ChatGPT image generation on the owner's account (the ChatGPT imaging route the owner allows), prompted with the owner-approved concepts `den_room.png` and `den_boss.png` as references (prompt and file size in `set_src/PROVENANCE.txt` and `survivorsunchained_inputs/gpt_den/PROVENANCE.txt`); built into `art/dungeon/den/set/` by `tools/look/den_set.py`. Risk: as the ChatGPT imaging route (owner's account; log kept).
- `godot/art/dungeon/den/set_src/F4.png` (15 Nov 2026; the den's painted set, round 10): made by ChatGPT image generation on the owner's account (the ChatGPT imaging route the owner allows), prompted with the owner-approved concepts `den_room.png` and `den_boss.png` as references (prompt and file size in `set_src/PROVENANCE.txt` and `survivorsunchained_inputs/gpt_den/PROVENANCE.txt`); built into `art/dungeon/den/set/` by `tools/look/den_set.py`. Risk: as the ChatGPT imaging route (owner's account; log kept).
- `godot/art/dungeon/den/set_src/F5.png` (15 Nov 2026; the den's painted set, round 11, batch 4: tileable cel floor tile, 1254x1254, into the 5-layer `set/floor.png`; F1-F4 retired from the floor list, kept in source): made by ChatGPT image generation on the owner's account (the ChatGPT imaging route the owner allows), prompted with the owner-approved concepts `den_room.png` and `den_boss.png` as references (prompt and file size in `set_src/PROVENANCE.txt` and `survivorsunchained_inputs/gpt_den/PROVENANCE.txt`); built into `art/dungeon/den/set/` by `tools/look/den_set.py`. Risk: as the ChatGPT imaging route (owner's account; log kept).
- `godot/art/dungeon/den/set_src/F6.png` (15 Nov 2026; the den's painted set, round 11, batch 4: tileable cel floor tile, 1254x1254, into the 5-layer `set/floor.png`): made by ChatGPT image generation on the owner's account (the ChatGPT imaging route the owner allows), prompted with the owner-approved concepts `den_room.png` and `den_boss.png` as references (prompt and file size in `set_src/PROVENANCE.txt` and `survivorsunchained_inputs/gpt_den/PROVENANCE.txt`); built into `art/dungeon/den/set/` by `tools/look/den_set.py`. Risk: as the ChatGPT imaging route (owner's account; log kept).
- `godot/art/dungeon/den/set_src/F7.png` (15 Nov 2026; the den's painted set, round 11, batch 4: tileable cel floor tile, 1254x1254, into the 5-layer `set/floor.png`): made by ChatGPT image generation on the owner's account (the ChatGPT imaging route the owner allows), prompted with the owner-approved concepts `den_room.png` and `den_boss.png` as references (prompt and file size in `set_src/PROVENANCE.txt` and `survivorsunchained_inputs/gpt_den/PROVENANCE.txt`); built into `art/dungeon/den/set/` by `tools/look/den_set.py`. Risk: as the ChatGPT imaging route (owner's account; log kept).
- `godot/art/dungeon/den/set_src/F8.png` (15 Nov 2026; the den's painted set, round 11, batch 4: tileable cel floor tile, 1254x1254, into the 5-layer `set/floor.png`): made by ChatGPT image generation on the owner's account (the ChatGPT imaging route the owner allows), prompted with the owner-approved concepts `den_room.png` and `den_boss.png` as references (prompt and file size in `set_src/PROVENANCE.txt` and `survivorsunchained_inputs/gpt_den/PROVENANCE.txt`); built into `art/dungeon/den/set/` by `tools/look/den_set.py`. Risk: as the ChatGPT imaging route (owner's account; log kept).
- `godot/art/dungeon/den/set_src/F9.png` (15 Nov 2026; the den's painted set, round 11, batch 4: tileable cel floor tile, 1254x1254, into the 5-layer `set/floor.png`): made by ChatGPT image generation on the owner's account (the ChatGPT imaging route the owner allows), prompted with the owner-approved concepts `den_room.png` and `den_boss.png` as references (prompt and file size in `set_src/PROVENANCE.txt` and `survivorsunchained_inputs/gpt_den/PROVENANCE.txt`); built into `art/dungeon/den/set/` by `tools/look/den_set.py`. Risk: as the ChatGPT imaging route (owner's account; log kept).
- `godot/art/dungeon/den/set_src/O4.png` (15 Nov 2026; the den's painted set, round 11, batch 4: bone drifts sheet, 1536x1024, into `set/O4.png`, 2 pieces at the far banks' feet): made by ChatGPT image generation on the owner's account (the ChatGPT imaging route the owner allows), prompted with the owner-approved concepts `den_room.png` and `den_boss.png` as references (prompt and file size in `set_src/PROVENANCE.txt` and `survivorsunchained_inputs/gpt_den/PROVENANCE.txt`); built into `art/dungeon/den/set/` by `tools/look/den_set.py`. Risk: as the ChatGPT imaging route (owner's account; log kept).
- `godot/art/dungeon/den/set_src/O5.png` (15 Nov 2026; the den's painted set, round 11, batch 4: blood pools, spatters and smears sheet, 1536x1024, into `set/O5.png`, 5 pieces; prompted by the owner by hand in ChatGPT after the tool refused the prompt (his own wording, not logged by us)): made by ChatGPT image generation on the owner's account (the ChatGPT imaging route the owner allows), prompted with the owner-approved concepts `den_room.png` and `den_boss.png` as references (prompt and file size in `set_src/PROVENANCE.txt` and `survivorsunchained_inputs/gpt_den/PROVENANCE.txt`); built into `art/dungeon/den/set/` by `tools/look/den_set.py`. Risk: as the ChatGPT imaging route (owner's account; log kept).
- `godot/art/dungeon/den/set_src/O7.png` (17 Nov 2026; the den's painted set, round 18, batch 6: bone litter, ten pieces, into `set/O7.png`): made by ChatGPT image generation on the owner's account (the ChatGPT imaging route the owner allows), prompted as `set_src/PROMPTS.md` Batch 6 O7; per-image line in `set_src/PROVENANCE.txt`.
- `godot/art/dungeon/den/set_src/O8.png` (17 Nov 2026; the den's painted set, round 18, batch 6: the lair's standing bone arc, six groups, into `set/O8.png`): made by ChatGPT image generation on the owner's account (the ChatGPT imaging route the owner allows), prompted as `set_src/PROMPTS.md` Batch 6 O8; per-image line in `set_src/PROVENANCE.txt`.
- `godot/art/dungeon/den/set_src/O9.png` (17 Nov 2026; the den's painted set, round 18, batch 6: carcass pieces, five, into `set/O9.png`): made by ChatGPT image generation on the owner's account (the ChatGPT imaging route the owner allows), prompted as `set_src/PROMPTS.md` Batch 6 O9; per-image line in `set_src/PROVENANCE.txt`.
- `godot/art/dungeon/den/set_src/H3.png` (17 Nov 2026; the den's painted set, round 18, batch 6: the lair's glowing pits, two, into `set/H3.png`): made by ChatGPT image generation on the owner's account (the ChatGPT imaging route the owner allows), prompted as `set_src/PROMPTS.md` Batch 6 H3; per-image line in `set_src/PROVENANCE.txt`.

## Sound lane F (16 Nov 2026)

- `godot/art/sound/{den_ambience,den_pits,den_pack_far,music_den_explore,music_den_boss,music_den_falls}_*.wav`, `voice_{wolf,wolfb,boar,yearling,packmother}_*.wav`, `her_{grunt,leap,land,dodge,perfect,stance,heartbeat}_*.wav` (+ their `.wav.import`): the owner's own ElevenLabs generations, made 15-16 Nov 2026 (the folder `survivorsunchained_inputs/sounds_demo/`, 56 files, with the owner's `PROVENANCE.txt`); no attribution needed, nothing in them needs a credit. Ingested, trimmed, looped and levelled by `tools/sound/demo_ingest.py` (the per-take table and the loop-seam checks: `tools/sound/demo_ingest_table.md`); the heartbeat file is cut into four single-beat takes. The events that play them: `tools/sound/demo_events.py` into `godot/data/content/sounds.json`. Risk: none known (his own ElevenLabs generations, no credit needed, as he says; the terms of his plan are his).
- `godot/art/sound/{skill_sunder,skill_groundbreaker,skill_bladestorm,tree_open,tree_close,tree_focus,tree_path,tree_denied,ui_hover,ui_click,ui_equip,loot_generic,loot_rare,equip_plate,equip_helmboots,set_complete}_0.wav` (+ `.wav.import`): the owner's second batch, 16 Nov 2026 13:01-13:42, made by the owner in ElevenLabs (`survivorsunchained_inputs/sounds_demo/`: sunder, groundbreaker, Bladestorm, skill tree open/close/focus/path click/denied, hover, click, equip ui, Generic/Rare loot pickup, Equip plate armor, "Equp helm or boots" (sic), set complete). No attribution needed (owner, 16 Nov 2026). Ingested by `tools/sound/demo_ingest.py` (table `tools/sound/demo_ingest_table.md`); events by `tools/sound/demo_events.py`.
