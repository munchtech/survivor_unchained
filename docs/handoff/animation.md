# Handoff: animation

For the next animation lead. Read `docs/team/README.md`, then this page, then `docs/team/animation.md` (status and the per-clip sign-off log). Written by a7dd95d00c4a6a017, branch `worktree-agent-a7dd95d00c4a6a017`. Before me: a03acf30b3e9bdd70, and the leads before them.

## 1. The owner's bar

- "AAA", "we are striving for perfection", "not polish, perfection". Remake rather than polish.
- Motion should be "weighty, characterful, readable at the game's camera", with personality, not stock-library motion.
- From the latest tests: "noticing a lot of reverse weird wrist motions ... stuff that isn't flowing naturally. it seems to be attempting to correct". And: "were looking for natural / correct movements. just want it to be skeptical". Treat every clip as guilty until it is shown natural.
- The heroine carries sex appeal "tho not at the cost of looking bad". The tone is 18+.

## 2. The brief

- You own character animation:
  - her (`heroine.res`), the hero (`hero.res`) and the folk (`folk.res`);
  - the crowd's keyed motion (`crowd.py`) and the beasts' (`Beasts.cs`);
  - the cinematics' clips.
- Tools are in `tools/anim/`. In `godot/src/Actors/` change only animation mapping and playback.
- Judge everything at full resolution: on sheets, at the game camera, and in the cinematic at its own cameras.
- Take a turn for every Godot run, packs included (`tools/turn.py take godot "animation: ..." --wait N`). Godot has three slots; the owner runs 3 to 5 agents at once.
- Run `dotnet test` in `godot/tests` before commits (666 pass). Commit and push your branch. Open no PRs. Use British spelling.

## 3. Done (pushed: 52cdc0ab, 0881e32d and d31b84dc)

- **C04 A6 `flask_drink`:**
  - the cork pulled with her teeth, the smell, the long drink;
  - keyed over a 100STYLE standing, the hands placed by the flask on her face;
  - judged in C04. The cinematics successor has the cues, a camera move to her front-left and the prop spec.
- **C01:**
  - remade `lie_side_wake`, `sit_back_heels` and `reach_coals`: the knees and forearm went through the ground;
  - new: `letter`, `kneel_to_stand_snap` (ends turned 55° left), `take_from_log` (ends turned 110° left; the grip in hand at 0.6 s) and `cup_hands`.
  - All are judged on sheets. They wait on cinematics to block them in.
- **C04 walks** (`clips/walks.py`, from 100STYLE straight stretches): `walk_tired`, `walk_uphill` and `wade`.
- **Rook:** `f_unfold_arms` (`clips/rook.py`).
- **The Warden:**
  - `lie_arm_up` is rise_stiff's first frame held, with the current swaying the forearm;
  - `wade_drag` is 100STYLE Heavyset over his body, the lamp up and the sword trailing;
  - Kimodo's wade_drag takes were rejected: they hunched and paddled.
  - Neither is judged in C02 yet.
- **The wrist and natural-motion pass.** Every library was rebuilt. The causes and fixes are on the status page.

## 4. Next, in order

1. **Finish the wrist pass.**
   - The audit stands at 894 flagged frames, down from 9,945.
   - Re-key the 13 clips that still roll a hand over 90° in a frame. They are listed on the status page.
   - **Start with `warden_show`.** It regressed: the sword arm now comes up across her face in the hold. Compare it with `anim4/sh/ba_warden_show.png`.
   - Then judge the strikes at speed in the game (`--on casts`).
   - The before and after strips of the worst five are `anim4/sh/ba_*.png`. Send them to the coordinator: they haven't gone yet.
2. **Judge in the cinematics** once cinematics has blocked them:
   - C01's seven clips and C04's flask, walks and Rook;
   - the Warden's `lie_arm_up` and `wade_drag` in C02.
   Use a local cue swap (scratch `cue.py`, never committed).
3. **Grimtunnel's** `burst_hug`, `sniff`, `laugh` and `dive`, and the lampling's slam. These are `Beasts.cs` compositions.
4. **Polish:** the chain haul's landing crouch, and a heavier running flinch (a `Gestures` gesture fired with the hit).
5. **The male hero's library,** with ab82cbe99e2937ddd: re-dump `hero_skeleton.json` when his body lands, then `build.py --body hero`.
6. **The boar:** the creatures lead (af551cacc6292152f) is keying the first pass on a new shared quadruped rig. Review and own the clips.

## 5. Waiting on others

- **Combat:** the slam and shot plants and the kerchief_crossbow repoint are on worktree-agent-a5115633c7006e4d4@3760c299, waiting to be merged. Check them in the game.
- **Cinematics:** the props (flask, cork, letter) need small builders. Everything else is in their handoff, under "Incoming from animation".

## 6. Decisions and why

- **Fix at the source.** The flips came from the tools, so the tools were mended, not the clips patched over.
  - Directions are slerped.
  - Aims are made whole and put in one frame before blending.
  - Elbows and knees bend on their hinges.
  - The forearm takes half the roll.
  - Limits: twist 95°, wrist 80°.
  - The elbow swings at most 42° off the keyed pole. A wider search gave poses the animator never asked for: the arm across the chest or face.
  - The elbow's path and the hinge through straight stretches are settled over the whole clip (`keyed.solve_frames`).
- Clips whose keys asked the impossible were re-keyed:
  - `catch_breath`: the hand's path round the front;
  - `death_back`: the arms don't pass straight;
  - the armed slam: the axe swung up in front of the shoulder.
  - The pattern to look for: **a hand path through or within 15 cm of its shoulder, or a hand that must turn over in a frame or two.**
- **Strikes roll the hand 40–56° a frame for 3 or 4 frames.** That is a fast cut at 30 fps, played at 1.6 times. Judge it in the game before changing it.
- **Contacts are measured**, with `held.py` and scratch `ground.py`. Her arms are short for her legs (0.47 m against 0.95 m): kneeling, her hands can't reach the ground.

## 7. Gotchas

- **The worktree guard** refuses `cd ... && git` chains, heredocs that touch the worktree, and `sed` with computed values. Write patch scripts to the scratchpad and run them plainly.
- **A full rebuild** (`build.py --no-pack <names>`) takes 25 to 40 minutes for her and for the hero, and about 10 for the folk. Run them in the background. Pass names, or a full build drops the clips no module makes any more.
- `hero.res` holds her story clips too, built on his skeleton. His audit numbers count those.
- After changing `keyed.py`, rebuild everything, or the libraries mix old solves with new.
- Never commit `.uid` or `.import` files. Add files by name.

## 8. Scratch tools (`<scratchpad>/anim4`)

- `audit.py` (in the repo) is the check.
- `dbg_arm.py module fn side f0 f1` traces an arm per frame.
- `ground.py spec` checks contacts.
- `stick.py` and `metrics.py` triage takes.
- `rsheet.py` renders anim_review sheets with any env (`OFF`/`LOOKOFF`/`FIXCAM` set a cinematic's camera).
- `strips.py tag` makes before/after strips.
- `cue.py cine edits.py|off` swaps cues locally. `cine.py` renders a cinematic's stills.
- `try_takes.py` writes whole Kimodo takes.

## 9. Collaborators

- The coordinator (main);
- cinematics (the successor of a79b6d8c81e14dc63);
- combat (the successor of a5115633c7006e4d4);
- the male hero (ab82cbe99e2937ddd);
- creatures (af551cacc6292152f).

## 10. Read first

1. `docs/team/animation.md`
2. `tools/anim/keyed.py`: `Rig.solve` (arms, `_bend`, `_strain`), `Track`, `_aims`, `_whole_aims`, `_one_frame` and `solve_frames`
3. `tools/anim/held.py` and `tools/anim/audit.py`
4. `tools/anim/clips/story.py` (C01), `story_c04.py`, `walks.py`, `warden.py`, `rook.py`
