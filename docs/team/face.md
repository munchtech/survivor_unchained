# Heroine face, hair and creation's Look: status

Agent a6784044c82f101d9, branch `worktree-agent-a6784044c82f101d9` (took over from ade92e8285938438f).
Read first: `docs/handoff/face.md` (the handoff) and `docs/FACE_RESEARCH.md` (the science).

## Current state (2026-10-04, evening)
- **FACE v3 is built and painted** (`paintD_s11`), with hair, features and import, in this worktree. Art is **not committed**: it is still not beautiful.
- **Judged at the Look close-up** (`--step 1 --part 1`; the Look is step 1 now):
  - better than v2: the mouth no longer bulges, and the lips read more natural;
  - still wrong:
    - the face is long and gaunt at the cheeks, and the jaw is heavy;
    - a pale fleck sits at the mouth's corners;
    - the eyes are plain;
    - the fire paints an orange smear down her shadow side, and the key light is weak;
    - her hair starts far back, so she reads as bald-browed with a ragged hairline.
- **Presets:** vixen and sunborn are repainted on the v3 head. Sunborn's old paint showed a pale band down her forehead.
- **Play zoom** (`arenaF_c*.png`, reviewed): at 22 to 31 m and a 64° pitch, her face is foreshortened and mostly hidden by her hair's crown. In three of four shots she faces away. They must be retaken with her facing the camera before `far_*` can be tuned.

## The direction I recommend: her face from a picture's own surface
MakeHuman's targets can't make her beautiful: v1 to v3 only moved outlines. A landmark warp against her reference moved points only 1 to 3 mm; the predecessor's fit had already matched her outline. What is wrong is in the volumes: the lips, the lids, the cheeks.

MoGe-2 (MIT, in our ComfyUI) reads a portrait's surface:
- **its normals are excellent:** lid folds, lip volume, nose and cheekbones all come out clean;
- **its depths are smoother and flatter** than its normals.

The tools are `tools/assets/face_moge.py` and `tools/assets/face_warp.py`. The warp is experimental: its docstring says what fails and what to try next.

New front references for her are in `scratchpad/face3/refs_her/`. `her_23` is the best: delicate, with fuller lips.

## Key decisions
- **Judge in game:** at the Look close-up and at play zoom, with hair on (as before).
- **Don't commit art that isn't beautiful.** The art stays on disk; the tools are committed.
- **Presets:** each keeps its own painting (as before). The next step makes each preset's shape its own key from its own reference, not slider values.

## Next
See `docs/handoff/face.md`, "Next (exact)".

## Notes for other areas
- **Main session:** don't take my head or `heroine_built.blend` yet. I'll message you when the head is final.
- **UI design:** the shot flags for the Look's parts are `--step 1 --part N`: 0 Hair, 1 Face, 2 Shape, 3 Paint, 4 Body. The Look close-up would gain a lot from a soft frontal fill light at face zoom (`GameFront.UpdateCreate`): the fire's orange falls on her shadow side. I haven't changed `GameFront`; it's yours to agree.
