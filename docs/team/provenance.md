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
| low | 55 |
| medium | 10 |
| high | 9 |
| UNKNOWN | 10 |

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

1. Get the owner's answers to the seven questions in `ASSET_PROVENANCE.md`, then update PE-05, PE-06, PE-09, UI-05, AI-14, AI-15 and DA-03.
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
  - Moonfire, Starfall and Fan of Knives should be renamed.

  Their brief: `docs/legal/LEGAL_BRIEF.md`.
- **Everyone:** add any new third-party or AI asset to `public/assets/CREDITS.md` and `docs/legal/ASSET_PROVENANCE.md`, with its source URL and licence, before it lands. Never ship `tools/make3d` output.
- **UI art:** the Krea-made list in the appendix assumes every `chrome.py` piece is painted over. Please confirm the boundary.
