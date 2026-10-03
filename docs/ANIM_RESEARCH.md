# Animation research: getting AAA motion onto the heroine

What exists for making character motion on this PC (RTX 5080, 16 GB shared
with ComfyUI and other agents; Blender 4.5; Godot 4.5.1; local ComfyUI
0.38), what each source's licence allows us to ship, and how the ARPGs
and survivors-likes we measure ourselves against build their motion.
Written October 2026. The design that follows from it is
`docs/ANIM_DESIGN.md`; the pipeline is `tools/anim/`.

**The rule throughout: nothing ships unless its licence lets a commercial
game ship it.** Every clip's source and licence is in
`tools/anim/manifest.json`, and the sources are credited in
`public/assets/CREDITS.md`.

## 1. What the game asks of an animation

Read from the code before any of the research (the full list is in
`ANIM_DESIGN.md` §1):

- **The survivor is nearly always running.** Base move speed is 5.0–5.6 m/s
  by calling (`data/content/archetypes.json`), reached in about 0.2 s
  (`Battle.cs`: `1 - e^(-14 dt)`). Standing still and running flat out are
  the two states that matter; a walk is only ever seen for a few frames.
  The run cycle at ~5.3 m/s is the single most-watched animation in the game.
- **Attacks fire themselves** and play on the upper body over the run
  (`PlayerView.cs`: a filtered one-shot). The damage, the swing clip and the
  arc effect all start in the same frame (`Weapons.cs` sets `AttackAnim` as
  damage is dealt; `BattleFx` draws a 0.22 s arc whose head crosses in
  0.12 s, mirrored on alternate swings). There is no time for wind-up
  *before* the hit: anticipation has to be compressed into the blend-in and
  the first frames, the blade must cross during those 0.12 s, and the weight
  has to come from follow-through and recovery.
- **The dash is 5.5 m in 0.2 s** (27 m/s), then a burst of pace. A roll
  cannot read in 0.2 s; a low lunge that settles into the run can.
- **The camera is far and high**: 31 m and 64° in arenas (closer by day). At
  that distance a 1.8 m figure is a few dozen pixels tall. What reads is the
  silhouette, motion in the screen plane, lean, stride, and timing.
  Movement toward or away from the camera (an overhead chop seen from above)
  foreshortens and reads poorly.
- **She is the heroine** (`art/people/heroine.glb`): the Universal Animation
  Library's skeleton turned onto her body (`tools/assets/build_heroine.py`),
  69 bones with breast and glute springs. Her legs are longer than the
  library's bodies (her pelvis stands at 1.07 m against the library's
  0.92 m), her hips wider; `HerPose.cs` patches every library clip at run
  time for this (pelvis height, arms brought in, fingers eased, a hip tilt).

## 2. Sources of motion

### 2.1 Motion libraries

| Source | What | Licence | Ship it? |
|---|---|---|---|
| **100STYLE** (Ian Mason, Edinburgh, 2022), [Zenodo](https://zenodo.org/record/8127870) | 4M+ frames of optical mocap, one performer, 100 styles (Neutral, Proud, Strutting, WiggleHips, Heavyset, Crouched, Swat, Angry, Elated, Old, Stiff, …), each as forward/backward/sideways walk and run, idle, and transitions; BVH | **CC BY 4.0** | **Yes**, with credit and a note of changes |
| **CMU Graphics Lab** mocap database | 2,600 takes, everyday motion, sport, some fighting and dance; ASF/AMC, community BVH/FBX conversions ([4TU FBX](https://data.4tu.nl/datasets/0448aab2-3332-449f-a8e2-d208cb58c7df)) | "You may include this data in commercially-sold products, but you may not resell this data directly, even in converted form" | **Yes** (as part of the game, never as a pack) |
| **Quaternius Universal Animation Library** 1 and 2 | ~120 game clips, generic bodies | CC0 | Yes (the game's current set and our fallback) |
| **Mixamo** (Adobe) | ~2,500 keyframed and mocap clips | Free with an Adobe account; royalty-free in games; raw files may not be redistributed as assets ([Adobe FAQ](https://community.adobe.com/t5/mixamo-discussions/mixamo-faq-licensing-royalties-ownership-eula-and-tos/m-p/13234775)) | Yes in principle, **but needs the owner's Adobe login**; this session cannot create or use accounts |
| **Bandai Namco Research Motion Dataset** 1 and 2 | 3,000+ stylised clips (fighting, dance, gestures) | CC BY-NC 4.0 (some sources say NC-ND) ([GitHub](https://github.com/BandaiNamcoResearchInc/Bandai-Namco-Research-Motiondataset/blob/master/README.md)) | **No**: non-commercial |
| **Ubisoft LAFAN1** | 77 takes of locomotion, fighting, falls | CC BY-NC-ND 4.0 | **No** |
| **AMASS / HumanML3D / Motion-X / BEAT / ZEGGS** | Research corpora | Non-commercial research | **No** |
| **BONES-SEED** (Bones Studio, 2026) | 288 h, SOMA and Unitree G1 skeletons, text-annotated | Its own "BONES-SEED License", gated; annotations CC BY 4.0 ([HF](https://huggingface.co/buckets/adhdmi/bonesseed)) | **Unknown**: needs the owner to read and accept it |
| **Unreal's Game Animation Sample / Lyra**, **Unity Starter Assets** | AAA-grade locomotion sets | Engine-locked EULAs (Unreal-only, Unity-only) | **No** (not in Godot) |

### 2.2 Text- and constraint-to-motion models

| Model | Licence of the weights | Notes | Ship its output? |
|---|---|---|---|
| **Kimodo** (NVIDIA, March 2026), [GitHub](https://github.com/nv-tlabs/kimodo), [HF](https://huggingface.co/nvidia/Kimodo-SOMA-RP-v1) | **NVIDIA Open Model License** for the SOMA and G1 checkpoints ("ready for commercial use"); the SMPL-X checkpoint is R&D only | 282M-parameter diffusion transformer trained on 700 h of Bones Rigplay optical mocap (made for games: locomotion, combat, gestures). Text **plus keyframes, end-effector targets and root paths**; 10 s at 30 fps; foot-skate post-process. ~3 GB VRAM with the text encoder on the CPU | **Yes** (SOMA-RP), but its text encoder is LLM2Vec on **Meta-Llama-3-8B-Instruct, a gated model**: the owner must accept the Llama 3 licence on Hugging Face and give the pipeline a read token |
| **ARDY** (NVIDIA, July 2026), [GitHub](https://github.com/nv-tlabs/ardy) | NVIDIA Open Model License | Real-time autoregressive version of the same idea, Bones Rigplay, "Core" and G1 skeletons (SOMA "coming soon") | Yes; same gated Llama dependency |
| **HY-Motion 1.0** (Tencent, Dec 2025) | Tencent Hunyuan Community Licence (territorial exclusions) | 1B-parameter flow model, SMPL-H output, **24–26 GB VRAM minimum** | No: doesn't fit the GPU, and the licence's territory terms are a risk for a game sold worldwide |
| MDM, MoMask, T2M-GPT, MotionGPT, MotionLCM, … | Code MIT/Apache, but every checkpoint is trained on HumanML3D (AMASS), which is **non-commercial** | Research quality, SMPL skeleton | **No** |

**Kimodo is the most promising generator for this game** (commercial
weights, game-oriented training data, and keyframe constraints, which let an
animator pose the key moments and have physically plausible motion in
between). It is blocked only by an owner action: see §5.

### 2.3 Markerless video mocap

| Method | Licence | Ship its output? |
|---|---|---|
| **SAM 3D Body** (Meta, Nov 2025) with the **Momentum Human Rig (MHR)** | SAM License (commercial use allowed; owners own derivatives; the usual weapons/military exclusions) for the model; **MHR is Apache 2.0** | **Yes**. It is already in local ComfyUI core: `SAM3DBody_Predict` (per frame), `SAM3DBody_Smooth` (savgol/gaussian temporal smoothing), `BuildPoseFile` (animated GLB or **BVH**). The weights (`sam_3d_body_dinov3_*.safetensors`) are not downloaded yet |
| GVHMR (SIGGRAPH Asia 2024), WHAM (CVPR 2024), TRAM, 4DHumans/HMR 2.0, CameraHMR, PromptHMR | Code variously MIT or non-commercial, but **all output SMPL/SMPL-X**, whose licence forbids commercial use without a paid Meshcapade licence (GVHMR's own weights are non-commercial) | **No** (unless the owner buys an SMPL commercial licence) |
| MediaPipe BlazePose | Apache 2.0 | Yes, but 3D quality is far below the others |

Video mocap needs video we have rights to: the owner filming a performer,
or clips generated locally (LTX 2.5 is installed; its community licence
allows commercial use under a revenue cap). Generated video's physics is
unreliable (floating contacts, limbs that change length), and per-frame
mesh recovery adds jitter, so this route is best kept for broad,
performative moves (gestures, emotes, a death) rather than combat timing.

### 2.4 Retargeting and clean-up

- **Our own retargeter** (`tools/anim/retarget.py`, numpy): source globals
  re-expressed on her bones through a calibration T-pose built from her own
  rest (each bone swung, never twisted, onto the source's rest direction),
  pelvis height scaled by leg length, then two-bone leg IK onto the
  source's (scaled) foot path, foot locking on detected contacts, loop
  extraction by pose distance and seam blending, root motion measured and
  removed (the game moves her). It writes clips straight onto her skeleton
  as Godot sees it, so nothing is lost to an exporter's axis conversions.
- **Blender**: its BVH importer and constraint-based retargeting (copy
  rotation in world space with offsets) work but need careful rest-pose
  matching and add an export round trip; we use Blender only for her
  source scene.
- **Rokoko Studio Live** (free Blender add-on) retargets well between
  humanoids; parts of it ask for a Rokoko account (not usable from here).
  **Auto-Rig Pro** (paid) is the industry's Blender choice.
- **Godot's own retargeting** (BoneMap with `SkeletonProfileHumanoid`, the
  rest fixer) works at import time between humanoids; it would suit a
  Mixamo or Kimodo export dropped into the project, but gives less control
  over feet and loops than our own pass.
- **Cascadeur** (Nekki): physics-assisted keyframing with AI posing; a good
  tool for a human animator, but GUI-only and its free tier is
  non-commercial.

## 3. How the games we measure against build their motion

### 3.1 Isometric ARPGs (Diablo IV, Path of Exile 2, Last Epoch)

- **Animation drives the combat's timing.** Path of Exile 2 makes "attack
  patterns, visual effects, character movement and damage positioning
  animation driven", with a fixed contact point scaled by attack speed, and
  lets the dodge roll cancel almost any animation
  ([poewiki](https://www.poewiki.net/wiki/POE2),
  [Mobalytics](https://mobalytics.gg/poe-2/guides/dodge-roll-mechanic)).
  Diablo IV and Last Epoch likewise speed attack clips up with attack speed
  around a fixed contact frame; Last Epoch players' main complaint is
  clips that feel unresponsive, i.e. too much wind-up before contact
  ([forum](https://forum.lastepoch.com/t/making-skills-feel-more-responsive/17085)).
- **Anticipation, contact, follow-through**: player attacks have very
  short anticipation (2–6 frames at 30 fps), a held or overshooting contact
  pose (the "hit-hold" that hit-stop extends), and a long, readable,
  cancellable recovery. Weight is sold in the recovery, not the wind-up.
- **Readability from above**: big lateral sweeps rather than overheads;
  weapons and arms held away from the body so the silhouette breaks; long
  smears and arcs (our arcs already do this); clear lean on starts, stops
  and turns; idles that settle into a strong, character-defining stance.
- **Mocap for locomotion and reactions, keys for attacks.** Both studios
  capture locomotion and hit reactions and hand-key (or heavily
  re-key) attacks and skills, because readable combat poses are pushed past
  what a performer does.
- **Locomotion systems**: starts and stops (Unreal's "distance matching"),
  procedural lean and bank into turns, speed matching (playback scaled to
  ground speed so feet don't slide), **orientation warping** (legs follow
  the velocity, the upper body turns to the target), foot IK on slopes, and
  additive breathing and idle variations. Diablo IV's movement is immediate
  (no momentum) with these layered on top to sell weight.

### 3.2 Survivors-likes (Vampire Survivors, Halls of Torment, Brotato, Deep Rock Galactic: Survivor, Soulstone Survivors)

- Auto-attacks never stop movement; the character is small; the run cycle
  and a flourish of the weapon are almost all the player sees of them.
- Readability comes first: the player must find themselves in the crowd
  in a glance (see `docs/feel/SUGGESTIONS.md` S-19). A distinctive gait and
  silhouette per character does that work as much as colour.
- Halls of Torment (the nearest in look) uses short, punchy one-shots
  laid over a constant run; nothing longer than a fraction of a second.

### 3.3 From the game-feel study (`docs/feel/`)

- Weight is reaction, time and sound. The swing and the damage are
  simultaneous, which is right for auto-weapons (AUDIT §1); so the swing
  clip must *start* in its cocked pose and cross during the arc.
- Hit-stop is gated and local (WorldScene.Weigh); a held contact pose in
  the clip gives it something to hold.
- Flinches at 31 m must be big to read (S-17); the same holds for her hit
  reactions.

## 4. What this means for us

1. **Locomotion and idles from 100STYLE** (CC BY 4.0), retargeted onto her,
   one style per calling's carriage: the cleanest licence, real weight
   shift, and starts, stops, sidesteps and backpedals in the same styles.
2. **Combat keyed by code** (`tools/anim/keyed.py`): poses authored as an
   animator thinks of them (hips, spine, a grip position on an arc about the
   shoulder, where the blade points, feet), timed to the game's arc, with
   overshoot and settle, solved by IK onto her skeleton.
3. **Kimodo when the owner opens the Llama gate**, for in-betweening keyed
   poses and for reactions, deaths and emotes from text.
4. **SAM 3D Body** for anything the owner can perform on camera (emotes,
   town gestures), when its weights are downloaded.
5. The **Universal Animation Library stays as the fallback** for every clip
   not yet remade, played through `HerPose` as before.

## 5. Owner actions that would unlock more

- **Kimodo / ARDY**: accept the Meta Llama 3 licence at
  huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct and save a read token
  to `%USERPROFILE%\.cache\huggingface\token`. Then `pip install
  git+https://github.com/nv-tlabs/kimodo.git` in a Python 3.10–3.12 venv and
  run with `TEXT_ENCODER_DEVICE=cpu` to stay under 3 GB of VRAM.
- **Mixamo**: an Adobe login to download specific clips (the licence is
  fine for the game).
- **BONES-SEED**: read its licence; if it allows commercial use it is 288
  hours of game-oriented mocap on the same SOMA skeleton Kimodo uses.
- **SAM 3D Body**: the weights for ComfyUI's model manager, and video of a
  performer (even a phone, side-on, full body, plain background).
