# P4 clip specs (`specs/<clip>.json`)

A P4 clip is one spec. Its file name is the clip's game name, and a packed P4 clip replaces the bridge clip of that name on B.
The commands are in `tools/anim/p4.py` (`gen`, `takes`, `build`, `check`). The core is Marionette `tools/motion/`.

| key | what |
|---|---|
| `kind` | `idle` or `gait`: which bible measures apply (`motion/measures.py` `idle()` or `gait()`) |
| `rules` | the bible rules the clip answers to (text) |
| `bands` | `{measure: [lo, hi]}`: the numbers a take is scored against (`measures.score`, 0 = all in band). `build` prints pass or MISS for each |
| `gen.engine` | `kimodo` (MotionBricks is not wired yet) |
| `gen.prompts` | one sentence each (Kimodo reads a full stop as the next prompt) |
| `gen.seconds`, `gen.seeds` (one per prompt, cycled), `gen.takes` (per prompt) | |
| `gen.root2d` | the Root2D path, built from numbers by `motion/paths.py`: `{kind: sway, travel, period, ease, overshoot, start}` or `{kind: straight, speed, ramp}`, plus `every` (constrain every k-th frame) |
| `gen.root2d_scales` | the path's amplitude searched per prompt (job `__p<i>s<percent>`): Kimodo's hips do not follow the path linearly (the idles jump from ~1 to ~17 cm across a narrow scale range) |
| `gen.keys` | hand end-effector keys: `{src: {prompt, scale, pick}, hands: {LeftHand/RightHand: [left, up, forward] B meters from the pelvis head}, aim: {same: added to what is sent, the measured retarget miss}, prompts, scales, start, every, tag}`. Kimodo remakes our own take `src` from its seed, moves its hands onto the targets at every `every` frames and regenerates (`__k<tag><i>s<pct>`). `takes` measures each hand's distance from its target on B (`hand_l_target_cm`, `hand_r_target_cm`) |
| `gen.more` | `{prompts, takes, seed_add}`: more takes of chosen prompts on new seeds (`__m<i>`) |
| `gate` | bands a take must pass to be chosen at all (the gaits' cadence: playback scale cannot fix it); the rest still rank by score |
| `post.loop`, `post.inplace` | as `motion retarget` |
| `post.cycle_s` | `[min, max]` seconds for the loop length (for idles, whole sway cycles) |
| `post.gait`, `post.duty` | the generated-gait foot lock (`footlock.gait_windows`). Each stance is pinned whole. `duty` is the share of the stride the ball is down; the belt is the stance's own ground speed |
| `post.game_speed` | the speed the game moves her at (m/s), so playback scale = game_speed / the clip's `speed_mps` |
| `post.crop` | optional `[a, b]` source frames used first |
| `source`, `bvh`, `sha1`, `take_score` | written by `takes`: the best take, imported to `src/<clip>.npz` (committed, because generation is not reproducible) |
| `fit` | the bible's layers (Marionette `motion/fit.py`, one implementation): each brings a measured component of the take into its band, phase-locked to the gait or the sway (a component's deviation about its own cycle mean is scaled), on B's locals before the foot lock, which re-solves the planted feet after. `stance {shift_cm, drop_cm, roll_deg, foot_l, foot_r}`, `pelvis {yaw_pm, list_pm}`, `thorax {counter_pm}`, `lean {deg}`, `bob {pelvis_cm, head_cm, pelvis_min_cm}` (legs re-solved by IK, feet keep their path), `knee {swing_deg}` (the recovery knee at mid-swing), `shoulders {level_cm, counter_deg}`, `head {ratio, bones}` (head/pelvis travel, eyes level), `arms {l, r}` (swing scale), `limbs {hand_l/hand_r: {at or by, pole, fingers, palm}}` (a held arm pose by IK with an elbow pole), `blade {dir, keep}` and `shield {boss, open_deg, pole}` (the held pieces by the game's seat on B: `p4.pieces()` reads WeaponSockets.cs), `pop {cap, x, span}` (one-frame turns eased, planted frames kept). `build` prints every layer's in/out numbers |
| `fit` (actions, solver F2) | `brace {over: [a, b] s, chest_cm, extend_deg, breaths, out_s}` (the hold frozen on a's pose with slow breaths: the trunk up on the legs, the spine opened; the take after b eased back), `limbs.hand_X.frame "clip"` and `hinge "rest"` (arm_solve's hinge sign from B's rest), `blade.frame "clip"` (a de-rotated spin's turning frame), `shield.frame "chest"` (boss and face ride spine_05); `post.action.retime.pairs [[out s, source frame], ...]` (more warp points); a spin's `pivot` is put on the turn axis on B by the core |
| `fit` (actions, solvers F1, F3) | `limbs.hand_X.soft` (a share of the reach, e.g. 0.9: past it the arm straightens on a soft curve instead of snapping to full extension in one frame), `blade.twist_smooth` (k frames: the forearm's share of a keyed blade's twist eased over k frames; the blade stays exact, the wrist takes the rest), `shield.hand` (`"end"`: the shield hand held at the end pose's local turn instead of B's rest, so the end blend has no hand pop), `step {foot_l / foot_r: [[a, b, lift_cm], ...] s}` (after `end`: over [a, b] the foot's ground point runs from its spot at a to its spot at b on a smootherstep with a sin lift, the leg re-solved by `leg_ik` keeping the foot's world turn; after b it stays on b's spot until its next step; plant it with a `post.action.planted` window after b). `post.action.ground [a, b]` (s or a beat name, `"end"` allowed): the hips' horizontal held on frame a's spot over [a, b] (the knees absorb), the offset kept after, before the travel strip (a charge's impact stops her dead) |
| measures (actions) | `shield_over_eyes_cm` (the shield's top edge over her eyes, taken 11 cm under the head top), `head_behind_cm` (the shield face ahead of her head top along her heading: her head tucked behind it) |
| `held` | `["sword", "shield"]`: the held pieces' numbers (`p4.held`: blade angle below horizontal, its pitch swing, heading, tip height; the shield's boss in her pelvis frame, top edge, face heading) |
| `notes` | free text |

`specs/<clip>.takes.json` logs every take's measures and score, best first.

Kimodo runs in two passes (`motion/kimodo_run.py`). `encode` loads only the text encoder: on the CPU (about 16 GB of RAM) when 18 GB are free, else on the GPU (take the gpu turn): Llama 3 8B in bf16, exact weights, split by accelerate over the free VRAM less 1.5 GB and at most 4 GB of RAM (about 40 s to load, a second a prompt). It writes each prompt once into the embedding cache (`KIMODO_CACHE`). `generate` then loads only the diffusion model (about 3 GB of VRAM) and reads the cache. A prompt missing from the cache is an error; Llama is never loaded silently.

A gait's built clip carries `speed_mps`, its locked stance speed. P4Pack writes it as the animation's `speed` meta, and on B the game plays the gait at that speed (`P4Overlay.Speed`).
