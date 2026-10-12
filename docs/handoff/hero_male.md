# Handoff: male hero lead

From lead ac39445bca5508eaf (12 October, about 250k), branch `worktree-agent-ac39445bca5508eaf`. Status and the full plan: `docs/team/hero_male.md` (read it whole). Earlier handoffs are in git history.

## The owner, in their words
- 12 Oct: "Begin work on Hero, using the lessons we learned making Heroine to hopefully do it in a fraction of the time and effort and tokens."
- 12 Oct: "you can totally make a new one from scratch if ours is lame. but remember sex appeal. muscular defined, attractive". This replaced "his body stays".
- "we are striving for perfection"; "I don't want to polish, I want to create perfection"; sex appeal drives, "tho not at the cost of looking bad"; check at full resolution.

## The brief (coordinator)
1. Plan (done, top of the status page). 2. Head finish: brow cards over painted brows (`brow_dye`), stubble via `HisShadow`, two or three beards as cards with the head's shape keys, lit lashes; judge. 3. The base garment (braies or loincloth, always worn), then four outfits (`hero_male_outfits.py`, the heroine's generator with a body parameter; outfits lead paused, don't touch its branch `worktree-agent-a5ca10091b08dc429`); judge each. 4. Hair once `face/hair-swing` is on integration (the coordinator says when), then the Look step's data and wiring (`heroes.male`, `BeardStyle`). Full-res face/front/side/back sheets go to the coordinator only after a judge's pass. Every taste verdict to a fresh `su-lead-max` judge (Context budget: 150k), foreground. Turns via `tools/turn.py`. `dotnet test` green before each commit; commit and push your branch; no PRs; ask the coordinator to merge each judged step. Never enter the Marionette repo.
Inserted before step 2 (coordinator): judge the current body against the owner's bar; if short, rebuild (path A).

## Done
- Worktree set up (junction `godot/assets` -> this worktree's `public/assets`, assume-unchanged; `.godot` copied; built; imported).
- **Judge j0: REBUILD, path A, donor variant** (`docs/hero_male/verdict_j0.md`: the targets the next judge checks).
- **`tools/assets/hero_male.py`** (new, stage 1 = the body): MakeHuman man, T by LBS, CC subdivision, per-bone donor registration, donor-detail relief bake, UAL fold. See the status page for its numbers and env (`HM_STOP=shape|body`, `HM_GAIN`, `HM_DETAIL`, `HM_MUSCLE`, `HM_WEIGHT`, `HM_DEBUG`).
- His 73 clips rebuilt on the new skeleton (`tools/scratch/hero_male/clips.sh`, about 15 min in a godot turn).
- `lookdev.gd`: his `him` library loads with `BODY=hero`.

## Run
```
blender -b --python tools/assets/hero_male.py -- tools/comfy/out/heroes/hero_donor.glb public/assets/people/UAL1.glb tools/comfy/out/heroes/hero_male.blend godot/art/people
```
(Blender: `C:\Users\munch\Tools\blender-4.5.14-windows-x64\blender.exe`; about 8 min with the bakes; `hero_donor.glb` is the old `hero.glb`: `git show b08e8bdf:godot/art/people/hero.glb > ...` if it is gone.) Then `CLIP=him/idle_warden EXTRA="NECK=0" bash tools/scratch/hero_male/shoot2.sh <out dir>` in a godot turn (it imports first), `python tools/scratch/hero_male/sheet2.py <dir> look.jpg 520 hero_front:c hero_side:c hero_back:c hero_q:c`. After any change to his joints, re-run `clips.sh`.

## Next
The status page's "Next (exact)": definition (one try at a clean donor relief, else a solver on authored definition), shoulders (T-pose LBS lifts the deltoid: consider MH's own rest), the head stage, the skin, then judge j1 beside her.

## Decisions
- Rebuild on MakeHuman (owner's 12 Oct words + j0). Donor only for surface detail; its volume is off (measured: MH matches it).
- T-pose rest like hers, via LBS on MH weights (revisit: shoulders).
- One body mesh with MakeHuman's UVs, its head to be split with shared boundary points (no graft).

## Failures and why
- Donor bake v1: garbage relief (dark patches, streaks): rays missed (black texels) and the donor's arms sat 8 cm off his. Fixed by per-bone registration and a hit mask.
- Volume transfer: a wide smoothing used to remove the donor's misplacement also removed the girth (it averaged half a limb). Per-bone means fixed that; then the volume turned out not to be needed.
- UAL's `Idle` hunches the MH skeleton (clips are frame-specific); use `him/...`.

## Gotchas
- Isolated-worktree Bash refuses compound commands with `cd` or computed values: put them in a script file and run `bash <file>`, or use Edit.
- Godot's window caps at 2526x1421 on this screen; body shots are landscape, cropped to the middle.
- MH targets are named by file stem; `X-` means both sides; `measure-*` have no side.
- `People.Hero` and lookdev still use `NeckPitch 22` (old body); set 0 for the new one when it ships.

## Uncommitted on purpose (unjudged built art)
`godot/art/people/hero.glb`, `godot/art/anim/hero.res`, `godot/art/anim/hero_clips.json`, `tools/anim/data/hero_skeleton.json` (new body and its clips). Never commit the many `.import` files the Godot import dirtied. `git checkout -- <file>` returns the old ones.

## Files to read first
`docs/team/hero_male.md`, `docs/hero_male/verdict_j0.md`, `tools/assets/hero_male.py` (by section), then for the head stage `tools/assets/hero_male_head.py` lines 52-118 (config), 1211-1430 (paint, masks), 1431-1640 (parts, shapes, export).
