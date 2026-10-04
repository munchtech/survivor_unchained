# Animation: status

Branch `worktree-agent-a1e3002b800ee55ac` (took over from `aa4f5fc266b043035`). The brief, history and gotchas are in `docs/handoff/animation.md`.

## Paused (owner's usage limit), exact state

- Merged the integration branch; nothing new is in the game yet.
- Started on `death_back`: the three Kimodo `knockdown_*` takes were retargeted whole (scratch `try_takes.py`: `generated.make(..., place="keep")`), packed as `k_knockdown_*`, then removed again before any sheet was judged. The library is the committed 64 clips.
- Found for `death_back`: `Battle` keeps `Player.LastKiller` (an `Enemy` with X, Z), so PlayerView can choose the fall by where the killer stands against her facing (in front: on her back; behind: today's face-down `death`). `face_forward` averages the whole take, so a knockdown that rolls needs its facing taken from the first frames instead; crop the take to the fall with `warp=[(a, b, b - a)]` and hold it (`"hold": True`).
- Combat (`ac4ec5bbd2763a0df`) will send a motion list once their new defs land: likely a kneel-to-shoot (crossbowman), a howl (wolf caller) and a slam wind-up (heavies); the shamble suits their Risen variants. Not yet answered.
- Fresh-worktree setup that sheets need (rendered blank without it): `godot/assets` checks out as a text file, so replace it with a junction to `public/assets` (then `git update-index --assume-unchanged godot/assets`), and copy the `*.import`/`*.uid` files under `public/assets` from a worktree that has them, then `--import`.

## State

- **Hers in the game:** 64 clips in `godot/art/anim/heroine.res`. `tools/anim/manifest.json` lists every one.
- **Her arts** (`tools/anim/clips/arts.py`, all keyed and checked in the running game):
  - `vault`: a split leap; she vaults forward like this when moving.
  - `vault_back`: a tucked back spring into a three-point landing, used when she vaults standing.
  - `bull_rush`: one gait-solver stride cycle, pitched behind the shield, then a planted shove.
  - `chain_haul`: flown in flat with the axe cocked, held until she arrives.
  - `chain_strike`: played when the haul ends; the blow lands in its second frame.
  - PlayerView picks the vault by her travel against her facing, and holds her facing in the air.
  - Any art's landing gives way to her run once she moves (`ArtTail`).
- **Townsfolk** (`tools/anim/folk.py`, `godot/art/anim/folk.res`, `FolkClips.cs`): 20 clips, each made for the women's and the men's kit skeletons. They cover walk, idle, talk, arms crossed, sitting on a chair, sitting on the floor, cheer, wave, work and pick-up. Unarmed townsfolk play them through `People.Clip`, and their walk runs at a rate that keeps the feet planted. Checked in the Waystation.
- **Kimodo:** all 25 prompts × 3 takes are in `C:/Users/munch/Tools/mocap/kimodo/`, and all were judged on contact sheets.
  - Townsfolk takes: good. They are used.
  - Arts (vault, bull rush, chain haul, leap): they lose to the keyed clips.
  - Hits: too subtle and too long for a survivors-like flinch.
  - Knockdown (all three takes fall backward, roll and rise): good, and unused so far.
  - her_hip_idle ignored its prompt; her_walk, kneel and shrug are usable; the bow is too deep.
- **Kimodo's LoRA warning** is harmless: I reproduced it in the venv with a tiny model, and the adapter merges exactly.

## Key decisions

- Mixamo or Kimodo takes that don't fit the game's action are rejected, not bent to fit; the four arts are keyed.
- Clips are made per skeleton. The kit's women and men differ from the library's skeleton (neck up to 23°), so each folk clip is made for both bodies.
- Armed people (guards, bosses) and the crowd keep the library, so a guard never walks like a shopper.
- Unjudged clips stay out of full builds: `arts.py` has a `JUDGED` set, and HerClips plays anything in her library at once.

## Next

1. A backward death for her: a variant of `death` from Kimodo `knockdown_*` (the fall, held down).
2. Her walk in town, if she ever walks: Kimodo `her_walk_*`, or Mixamo's feminine walk retargeted onto her.
3. Crowd shamble: Kimodo `shamble_*` for the undead. The crowd is VAT-baked (`Vat.cs`, bump `Vat.Version`); coordinate with Combat, who is varying crowd tints.
4. Polish: the strike's crouch on landing; a heavier flinch layered over runs.

## Notes for other areas

- Combat: `CrowdView` tint hook, I agreed to their option (b): they add the lines themselves.
- `--cast T --still` casts the art standing (for pictures of the back spring).
- `anim_review.gd` renders the kit bodies too: `MODEL=female|male PARTS=<kit parts>`, clips `folk/...`.
