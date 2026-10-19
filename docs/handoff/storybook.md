# Handoff: the storybook cinematics

## Paused here; next: (storybook 1, 19 October, coordinator wind-down)
- **No style frames for the owner yet.** Only round 1's exploration exists, unjudged and NOT for the owner: `.claude/worktrees/storybook-1/tools/storybook/out/style_r1/sheet_raw.jpg` (git-ignored; 24 pictures: P1, P4, P9 in four hands). Round 2 (`tools/storybook/jobs/style_r2.json`, 18 pictures, about 8 min of GPU) was never run: the GPU was Marionette's. Next: take the GPU, run r2, then the steps in item 2 below. No helpers are running; no turn is held.
- **The player checks (done, tools/storybook/out/checks/):** the busy test plate costs 1.5-1.65 ms a frame at 1080p (GPU 0.64 ms; measured with the card shared) and 2.4-2.7 ms at 1440p, about +0.5-1.0 GB of VRAM. Movie Maker captures picture and sound in sync (33.03 s each). Fixes for the next code pass, in order:
  1. The last subtitle (the sung "Lamps are lit... stay where they reach...") still shows on the black at 89.5 s: end every subtitle by the fade to black.
  2. After SB00's own 2 s of black, the zone loads under 2.5 s more black (91.0-93.0 s), then C01's sound-only shot 1 adds 2.5 s: about 7 s of black in all. Load the zone under SB00's black (start it at P10c's fade) or cut C01's shot 1 silence by the load time, so the seam is the doc's 2 s + 2.5 s.
  3. Skip can't be scripted: `--keys` only fires without `--auto` and presses once, not the 0.8 s hold. Add a test switch (`--sb-skip-at S`) and check skip once. The test run set `seen.sb00` in the saved settings (saves are expendable).
  4. `--resolution 1920x1080` is overridden by the saved Fullscreen setting unless `--shot` or `--perf` is passed: add `--perf` (or `--shot`) to 1080 captures. There is no ffmpeg on PATH: imageio_ffmpeg's copy works.
  5. The smoke preset reads as one round blob; 3 texture RIDs leak at quit (preloaded plates never used).
  Good: the bars are in (184 px) from C01's first frame, no jump; creation holds, fades and goes to black as the doc says.

## Start here (storybook 1 -> storybook 2, 19 October)
- **Area:** the storybook cinematics (drawn, Diablo III act-cinematic style): the format, the player and the look, proved on SB00 "Stay Where They Reach", the game's opening (docs/story/storybook/sb00_stay_where_they_reach.md). Lead on su-lead-max (taste throughout); code to su-lead-high at medium, menial to su-worker(-medium)/su-runner. Worktree `.claude/worktrees/storybook-1`, branch `storybook-1` (off integration 8ba3a4e7). `godot/assets` is a junction: never stash, reset --hard or checkout . there.
- **Fixed list and state:**
  1. **Format and player: BUILT** (d0b6f97a, 367b8554; tests 993/0/8). `docs/storybook/README.md` is the format and the run lines. Checked (see "Paused here" above for the numbers and the five fixes).
  2. **The look: IN PROGRESS.** Round 1 done (`tools/storybook/out/style_r1/sheet_raw.jpg`: P1, P4, P9 in four hands, 2 seeds). Round 2 jobs written (`tools/storybook/jobs/style_r2.json`, 18 pictures), NOT run yet. Next: run r2 (`python tools/storybook/gen.py tools/storybook/jobs/style_r2.json`), sheet it (`tools/storybook/sheet.py`), pick a hand, tune `tools/storybook/hand.py`, make 3 finished style frames (1920x1080 with 2.39 bars, as the game shows them), judge once at max (`tools/storybook/briefs/brief_judge_style.md`: fill FRAMES, SCRIPT, HAND), then send main the frames for the owner's eye. Then all 11 plates.
  3. **Plates, temp VO, sound: sound DONE (temp)** (d4e41e9e: `tools/storybook/sound/`, one 89.5 s bed `godot/art/storybook/sb00/audio/sb00_bed.ogg` + stems, from a cue sheet; -22.4 LUFS, peak -1.87 dBTP, ends in digital zero; the motif read off the Warden's take, `tools/storybook/sound/MOTIF.md`). Plates: not started; plan in `docs/storybook/sb00_plates.md`. The 9 Watchman lines are in the dialogue data (conversation `sb_stay_where_they_reach`); his packet is not regenerated yet.
  4. **Cut judge and MR:** not started.
- **Estimate left:** look 3-5 h (r2, frames, judge, owner), plates 8-12 h, cut judge and MR 2-4 h.

## Round 1, what it taught (read before prompting)
- Z-Image takes similes literally: "like a sleeping whale's back" drew a whale. Describe the thing itself (r2 does).
- It frames pictures as a page with a paper border unless told "full-bleed ... no border" (r2 does). A border can't survive a camera move.
- Poses must be explicit: "drives a spear into the dead man's chest" gave a corpse lying down; r2 says "stands upright".
- The hands: A (ink and watercolor) reads as a children's book; C (etching) as an old sepia print; **B (gouache over ink) and D (charcoal and ink on dark paper) are closest to Diablo III's grim painted plates**; r2 tests grimmer versions of both (B2, D2). Faces drawn in r1 lean cartoon: ask for realistic proportions, grim and serious.
- `hand.py` (our treatment): the palette step greyed everything but fire (too dead: the Watch's slate and the Legion's rust vanished) and kept the dusk sky as "story blue". Fix before using: require high value for the story blue (the cage blue is a bright pale #8ac8ff; a dusk sky is dark), and desaturate gently (about 0.3, not 0.55). Its real job is unity of texture (paper, edge pooling, grain, a consistent black point), not recoloring; keep the ink-line step subtle (invisible at 1:1 is fine).

## Decisions
- Pictures: Z-Image-Turbo bf16 + Qwen3-4B + the FLUX.1-schnell VAE (all Apache-2.0), and the Z-Image Fun ControlNet Union 2.1 (Apache-2.0, for layout control and inpainting behind cut-out layers). Never Krea (its US$1M cap) or its LoRAs. Weight hashes in `tools/storybook/model_hashes.json`; each picture's sidecar JSON is its provenance. MoGe-2 (depth) and BiRefNet (mattes) are on the same server for splitting a painting into layers.
- Working pictures go to `tools/storybook/out/` (git-ignored); shipped layers to `godot/art/storybook/<id>/` (import with `make_test_plates.py`'s `write_import`).
- The soundtrack is one mixed bed played from 0 s; only the Watchman's lines play live (so ElevenLabs takes drop in). The drone is on D (the motif's key) though C01's drone is on A: kept, they are 90 s apart.
- The score is temp (our bowed-string synth) until the owner makes a final one by hand, like the hymn; the Watchman's take is the owner's ElevenLabs recording. Both told to main.

## Gotchas
- GPU: the coordinator wants the turn back the moment a batch ends (Marionette queues behind, RAM is tight). Batch everything you need into one turn. Z-Image took 12-35 s a picture at 1792x1024 under RAM pressure.
- ComfyUI may be down when you get the turn: start it as storybook 1 did (`Start-Process` the venv python `main.py --port 8188 --extra-model-paths-config "%APPDATA%\Comfy Desktop\instance-model-paths\inst-1790761498447.yaml"` in `C:\Users\munch\AppData\Local\Comfy-Desktop\ComfyUI-Installs\ComfyUI\ComfyUI`; up in about 30 s). Z-Image: CLIPLoader type `lumina2`, ModelSamplingAuraFlow shift 3, 9 steps, cfg 1, res_multistep/simple.
- The Watchman's packet: `docs/voice/elevenlabs/watchman.md` is for the DEAD Watchman (a barrow rasp, and the game adds a hollow effect to every watchman line). SB00's lines are the same man alive, at dusk ("plain, low, unhurried and tired", close and dry): the packet needs its own section and casting note, and the game's dead-rasp effect must not touch conversation `sb_stay_where_they_reach`. Regenerate with `tools/vo/elevenlabs.py` (docs/handoff/voice.md).
- Timing: at 2 words a second, L3, L4, L6 and L8 run 0.5-1.5 s past their plates; re-time when there are takes (a placeholder read via `tools/vo/placeholders.py` needs the GPU).
- The sound solver's weakest parts on paper: the formant-synth underwater singing (P8, P10) and the bowed model's timbre (unheard). The owner listens; a judge can't.

## Read first
1. docs/story/storybook/sb00_stay_where_they_reach.md
2. docs/storybook/sb00_plates.md (the plate plan and the hand)
3. docs/storybook/README.md (the format, running it)
4. tools/storybook/out/style_r1/sheet_raw.jpg (once, half size is enough)
5. docs/team/storybook.md (status)
