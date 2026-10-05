# Character models: status

The character models planner (agent acc580b6b79f28e28, branch `worktree-agent-acc580b6b79f28e28`). The brief: list what the owner needs to make so that every character and creature is ours, covering generic men and women, the named cast, and creatures. The deliverable is `docs/art/MODELS_TO_MAKE.md`.

## State (4 October)

- **`docs/art/MODELS_TO_MAKE.md` is written.** It lists 23 models:
  - 6 must-make: the heroine's body, the hero's body and the boar (the three launch blockers); the Ford-Warden; and the average man and woman;
  - 12 should-make;
  - 5 later.

  Everyone else is a reskin. It includes the legal lead's replacement rules (LEGAL_BRIEF 5(g)) and gives every model a path:
  - **A:** the team builds it on CC0;
  - **B:** the owner makes it with TRELLIS 2 locally, from his own picture;
  - **C:** as B from a Krea 2 picture, which falls under Krea's cap.
- No art made. Under the GPU hold, nothing was rendered, imported or run in Godot, ComfyUI or Blender. The tests are green (600).

## Key decisions

- **People are built on MakeHuman's CC0 body, with one mesh per sex.** It is legal's first choice, and every outfit then fits every build. The crowd's cost is in outfits, not bodies.
- **8 generic bodies:** 4 men (average, strong, heavy, old), 3 women (average with the figure range, heavy, old) and 1 child. With 3 heads, 16 crowd faces and 13 outfit sets, that is enough: the town builds each walker from parts, and silhouette is what reads at 31 m.
- **Own models go only where a base can't give the shape or the close-up:**
  - the heroes;
  - the Ford-Warden, a giant held in close-up;
  - Vonnra: the longest close-up, and her height and bearing;
  - Sella: a romance lead, who would otherwise read as the heroine's twin or a townswoman;
  - Grimtunnel;
  - the Barrow Lord, who becomes the Legion base;
  - later, the Kiln Ford Warden.
- **Redcowl and the Red Hand are one model,** as the cinematics ask.
- **The arena bakes one look per kind** (`Vat.cs`), so creature variety comes from variants (paint, shape keys, props), not from more models.

## Next

1. The main session merges this branch and puts the list to the owner.
2. Get answers to the open questions (MODELS_TO_MAKE appendix D):
   - legal: which local picture generator, if any, counts as path B;
   - the main session: who owns the Ford-Warden;
   - the hero and animation leads: MakeHuman's rig onto UAL.
3. As models land, keep the list current and add a ledger line for each (legal 5(g)).

## Blockers

None for the list. The models themselves wait on the GPU and on the owner's call.

## Notes for other areas

- **Male hero (ab82cbe99e2937ddd):** legal rules `ComfyUI_00008.glb` (his body) a launch blocker (5(b)). Polish on the current body is lost work. His rebuild on MakeHuman (`REPLACEMENT_PLAN.md` 1.3) is number 3 in the order. The generic men's builds fit your pipeline after him.
- **Heroine face (ade92e8285938438f) and the main session:** her body is number 1. Her outfits, hair and face paint refit; the 26 cameos are re-shot.
- **Arena art (a26767f7f9955cb56) and animation (a435f4dd0ac80df75):** the boar is number 2. The wolf shares its skeleton later; the lampling keeps its own.
- **Cinematics (a3058a45eee41d695):** the Ford-Warden is number 4. His brief, from C02, is in MODELS_TO_MAKE §3: his lamp on its own bone, a hood that dyes, and no face rig.
- **Legal (aab20546fe06daa89) and provenance (a80ff0c7fd988b178):** the rules are carried into the list; one question is in appendix D.
