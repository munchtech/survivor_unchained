# Legal and Steam compliance: status

Agent af0973d59a5b2817a (third lead; successor to aab20546fe06daa89), branch `worktree-agent-af0973d59a5b2817a`. Not a lawyer: I find and organise the issues, cite primary sources, and recommend. The owner and the main session decide. Handoff from my predecessor: `docs/handoff/legal.md`.

**Launch blockers (4):**
- the AI disclosure: **ready to paste** (`STEAM_CHECKLIST.md` D3); the owner fills it in at submission;
- the mature survey: waiting on the motion check of the main session's **tuck build**;
- the licences screen: **seen in game** (5 Oct, the credits page); its licence pages are being shot;
- the boar: **no one owns its replacement**; recommend the owner buys the commercial version now.

## State (5 October 2026, small hours)

- **The motion check's codes are proven in Godot** (on the current build, before the tuck):
  - calibration: the nipple tips and the crotch are found where they should be (tips at about ±0.11, 1.42, 0.16; crotch underside y 0.925; mons 0.967). 157 vertices fall in the areolas and 94 in the strip. The pictures show the codes centred on each nipple and the strip at the crotch, nowhere else;
  - false positives: 64 frames of all four outfits, no codes drawn, under the linear tonemapper. **No pixel** passes as skin near a nipple, or as the strip, even at a 1-pixel threshold;
  - the Warden's sprint, 64 frames: no areola and no strip. The closest visible skin to an areola is +1.0 cm past its edge, on each breast.
- **New in the tools:**
  - a third code for **tucked skin in view** (a dent or a gap), read from the outfit's channel of her vertex colours: cyan, paler the shallower the tuck. Near a nipple it rides on the blue code;
  - **margins per breast and per edge of the rim** (upper, upper inner, inner and so on), measured from each nipple tip as posed, so each edge of a cup can be trimmed by its own margin;
  - `tuckcalib` (each outfit's pieces hidden, so its tucked skin shows) and `PROJECT=` (run from a worktree against the main checkout's import);
  - crops enlarged, with a ring on the closest pixel and the TEST TINT banner naming all three colours.
- **The Quaternius base bodies** (townsfolk, Risen, the male survivor): no nipples and no genitals modelled. Their skin textures paint underwear (a bra and briefs). Their normal maps: being checked.
- **The AI disclosure:** a paste-ready text for the release as exported now, and a bullet to add for each thing that may ship later (`STEAM_CHECKLIST.md` D3). Valve's Content Survey page was re-read on 5 Oct: unchanged.
- **Standing check:** the face lead's new references (`face_refs.py`) are Krea 2 Turbo from text alone, naming no real person; MoGe-2's weights are MIT. Credits line ready for when her MoGe face ships (checklist E).

## Key decisions (with why)

- **The motion check measures; it never asks for more garment.** The owner: "pixel perfect no extra stuff hidden at all", "showing as much as we possibly can". It proves the areolas and the narrow strip stay covered, and measures how much more could show.
- **Genitals:** none are modelled, and the Warden's thong is by design. The strip is checked because the survey must be true, not because anything is there.
- **Every crop carries the TEST TINT banner:** the owner once took the tint for the game.
- **Landmarks are posed as the renderer skins her** (her mesh's own transform, then the bone): the first calibration showed the skeleton's transform alone put them about 12 cm low. The fix is being re-checked.
- **The disclosure names only what ships.** It says "rebuilt and rigged for the game", not "by hand": agents did much of the rebuild.

## Next

1. **The tuck build** (the main session will send the commit): merge; `tuckcalib`, `calib`, `fp`, `cup`; then `all`, one outfit per turn. Send the main session, per outfit: each breast's margin by edge, with clip, view and frame; any strip flag; any frame showing tucked skin.
2. Update brief issue 2 and checklist D2 with the results; tick the motion check.
3. Cinematic poses (`--cine`) and creation's Look poses: not yet in `run.sh`.
4. Standing check: new assets and tools from every lead. Before launch, re-read the live Steam forms and the Krea, LTX, ElevenLabs and Suno terms.

## Blockers on others

- **The boar:** arena art says creatures aren't theirs; the models planner lists it as number 2; animation would rig it. Nobody has it scheduled. Recommendation to the owner: buy the Fab or Patreon commercial version now, keep the receipt, and replace it later.
- The owner's state of residence and business structure (lawyer questions 12 and 2); whether "Munchtech", the name on the credits screen, is a registered name.
- A person must run the USPTO search (it sits behind a bot challenge).

## Notes for other areas

- **Main session:** the motion check is ready for the tuck build. If `vertex()` writes `COLOR`, tell me: the tuck code reads her vertex colour in `fragment()`.
- **UI design (aab47bfdab5955dac):** two index labels run over the credits page's divider (details to follow).
- **Models planner:** `MODELS_TO_MAKE.md` still says the bodies came from Krea's website and Hunyuan3D. They didn't: local Krea 2 Turbo pictures and local TRELLIS 2 (brief 5(b)). The bodies are kept, with conditions.
- **Anyone adding a tool or model:** send me its licence link.
