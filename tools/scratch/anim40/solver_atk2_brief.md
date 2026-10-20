# Solver brief: her attack poses, part 2: chain_strike and cast_flick (animation 41, item 2, round 1)

Context budget: 220k. You report to animation 41 (the agent id in your spawn message), not the coordinator. Hand back at about 200k with what you built and measured.

## Where and how
- Worktree `C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\anim-40`, branch `anim-40`. `godot/assets` is a junction: NEVER `git stash`, `git reset --hard` or `git checkout .`. Commit as you go (WIP is fine), named files only. Never commit `godot/art/anim/heroine.res`, `*_clips.json`, `tools/anim/manifest.json`, `arms_rest_godot.json` or `*.import` (build by-products).
- Build clips: `python tools/anim/build.py --no-pack <names>` (writes `tools/anim/out/clips/<name>.json`; a name matches by substring).
- Shoot 1:1 game frames: `bash tools/scratch/anim40/shoot.sh <list> <outdir>`. It takes the Godot turn, imports, packs the library and shoots each line `NAME|QUICK|WEAPON|CLIP@SECONDS|TIME|CLOSE|FACING|SEX`. See `tools/scratch/anim40/shots_atk0.txt` for the baseline list. CLOSE 1 = the close-up at its closest zoom, 0.6 = mid zoom (attacks: the closest crops her hands off), 0 = the play camera. WEAPON `gyre_axes` gives her two axes.
- **The hold is now play-true** (commit 7b00ce4b): an upper-layer clip (`meta layer "upper"`: axe_fore, axe_heavy, axes_*, cast_flick) is shown over her idle's hips and legs, as play's upperShot filter does, with her head levelled by play's HeadLevel (0.8). A whole-body clip (chain_strike) keeps its own legs and head. So judge and key against what play shows. Only the spine and above of an upper clip reach the screen, so the keyed hips and feet in `clips/axe.py` don't matter on screen, but the spine's yaw and pitch do.
- Baseline frames (play-true, before you): `tools/scratch/anim40/shots_atk0/`. Contact sheet: `tools/scratch/anim40/contact_atk0.jpg` (cropped, quarter size). Look at the sheet; open full-size frames only when a detail needs it, and at half size (`python tools/half.py <files>`) where you can.
- Measure: `python tools/anim/audit.py <clips>` (wrist and spin flags), `python tools/anim/armscheck.py <clips> --sets axe,axes --outfit reaver --jobs 3` (the axe into her body, mm), `python tools/anim/fistfit.py axe` and `python tools/anim/fistfit.py wand` (fists on the grip: keep axe 21/21 and wand 3/3), `python tools/scratch/anim40/axdir.py <clip> viking_axe@hand_r hand_r` (per frame: the hand relative to the pelvis in cm, the axe head's direction, and the axe head's height).
- Turns: Godot only through shoot.sh (it takes and gives the turn). CPU checks need no turn. Stop only processes you started, by PID.

## The owner's bar
"still AAA quality. still 'perfect', just we aren't going in 2x++ zoom anymore." These are her main attacks, seen all the time. **Whole-frame gate:** would each frame ship in a AAA game as it stands, for a player watching at 1:1? The owner's failing calibration frames are in `C:\Users\munch\Desktop\survivorsunchained_inputs\owner_frames_18oct\`: a collapsed head-down hunch, a jarring spin, and so on. From the owner on motion (6 Oct): "bad, unnatural movements with respect to wrists - follow through motion joint to joint, some elbow pinching or arms going thr## The job (judge round 1's notes, re-checked against the play-true baseline)
Solver 1 already re-keyed the axe swings and the runs' free hand (commits 1d6bea5e and 37fbc052). Don't touch `clips/axe.py` or `clips/run.py`. Its play-true measuring tools are in `tools/scratch/anim40/solver_atk/`: `atkm.py CLIP --play idle_reaver` (per frame: the hands, the axe head, its screen angle and how flat it shows to the camera), `comp.py`, `auditx.py`. Use them; don't rewrite them.
1. **chain_strike f3 (`tools/anim/clips/arts.py`, `_strike_keys` and `chain_strike`):** the two-handed slam she lands off the chain. It's a whole-body clip, so play keeps its own legs and head and does NOT level the head. At f3 the axe is buried at the ground edge-on (it reads as a saw), her head is down so the face is lost, and the second hand doesn't read on the haft. The owner ruled on 17 Oct: "if it was meant to be two-handed, then two handed". But `TWO_HANDS` is off in the shipped clip, and the round-3 notes in arts.py list what failed when it was on. Read those notes first. Make f3-f6: the axe's face (not its edge) toward the 315 camera, the head lifted so her face shows (about 15-25 deg), and, if you can do it cleanly, both hands on the haft (the left below the right). If the two hands can't be made clean within your budget, keep one hand and say exactly why.
2. **cast_flick (`tools/anim/clips/actions.py`, `cast_flick`; arcanist, wand):**
   - At f0 the wand hand is behind her head, and the wand's crystal pokes out of the wide hat's crown (flick0_m). Bring the wind-up hand out beside the brim, about 20 cm, so the wand shows beside or in front of the hat and never through it. Allow for the hat's wide brim.
   - At f4-f8 the wand arm points at the foe, which reads now (flick4_c). But the free arm is flung straight out to the side like a T (flick8_m). Bring it in to a natural balance: elbow bent, hand at about hip-to-ribs height, slightly out.
   - audit flags f1's forearm spin of 65 and f2's hand spin of 54 in the whip. If the new f0 lets you, take them under 30. Don't make the whip slower: the clip plays at 1.6x.
   Check the hat with `--weapon -` on the arcanist (her default outfit has the hat).

d sprint_arcanist_wand still pair).

## Acceptance (numbers before pictures)
- audit: no new flags on the changed clips (compare with `python tools/anim/audit.py` before your first edit; save it).
- armscheck (`--sets axe` for chain_strike; `--sets wand --outfit arcanist` for cast_flick): no row deeper than before your edit.
- fistfit axe 21/21, wand 3/3 still.
- Shoot your fixed frames (the shots_atk0 lines plus any frames you need) to `tools/scratch/anim40/shots_atk2/` and make a contact sheet. Don't judge the look yourself beyond a working look: a fresh max judge rules after you hand back.

## Return (under 40 lines)
What you changed per clip (file and function), the numbers before and after, the commit(s), the shot folder, and anything you couldn't fix with why.
