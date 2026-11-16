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

## Sound lane F (16 Nov 2026)

- `godot/art/sound/{den_ambience,den_pits,den_pack_far,music_den_explore,music_den_boss,music_den_falls}_*.wav`, `voice_{wolf,wolfb,boar,yearling,packmother}_*.wav`, `her_{grunt,leap,land,dodge,perfect,stance,heartbeat}_*.wav` (+ their `.wav.import`): the owner's own ElevenLabs generations, made 15-16 Nov 2026 (the folder `survivorsunchained_inputs/sounds_demo/`, 56 files, with the owner's `PROVENANCE.txt`); no attribution needed, nothing in them needs a credit. Ingested, trimmed, looped and levelled by `tools/sound/demo_ingest.py` (the per-take table and the loop-seam checks: `tools/sound/demo_ingest_table.md`); the heartbeat file is cut into four single-beat takes. The events that play them: `tools/sound/demo_events.py` into `godot/data/content/sounds.json`. Risk: none known (his own ElevenLabs generations, no credit needed, as he says; the terms of his plan are his).
