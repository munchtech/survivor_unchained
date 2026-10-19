# Handoff: the storybook cinematics

## Start here (storybook 1, 19 October)
- **Area:** the storybook cinematics (drawn, Diablo III act-cinematic style): the format, the player and the look, proved on SB00 "Stay Where They Reach", the game's opening (docs/story/storybook/sb00_stay_where_they_reach.md). Lead on su-lead-max (taste throughout). Worktree `.claude/worktrees/storybook-1`, branch `storybook-1` (off integration 8ba3a4e7). `godot/assets` is a junction: never stash, reset --hard or checkout . there.
- **Fixed list:** (1) format and player in Godot, hooked before C01; (2) the look locked on 2-3 SB00 style frames, judged (max), then shown to the owner; (3) all 11 plates laid out, animated and timed to a temp VO track, with the Watchman's ElevenLabs packet, the drowning and the score cues; (4) one max judge on the cut, then "MR READY storybook-1@<commit>".
- **State:** (1) the code solver is building it (brief: scratchpad storybook/brief_player.md, copied into "The player brief" below when it reports). (2) tooling done: `tools/storybook/gen.py` (Z-Image-Turbo, logged); round 1 style jobs `tools/storybook/jobs/style_r1.json` (3 frames x 4 hands x 2 seeds), waiting for the GPU turn.
- **Next:** run style r1, pick the hand, build the treatment, style frames, judge.

## The owner's words
- "another cheaper, but stylisticly and artistically STILL PERFECT version of like a storybook type cinematic drawings that can show true anguish much better like a flip book" ... "well not a flipbook, but I think you know the kind of cinematic i'm talking about" (OWNER_NOTES "Cinematics: a second, storybook style").
- SB00 (18 Oct): "before the opening cinematic there is a storybook drawn cinematic explaining what we believe to be true about ember ... have it end with blublublub drowning sounds fade to black - into our cinematic wakeup."
- The drawings carry our own soul (the Ember Watch), no AI look; generated art is ours, local, logged.

## Decisions
- Pictures: Z-Image-Turbo bf16 + Qwen3-4B + the FLUX.1-schnell VAE (all Apache-2.0), and the Z-Image Fun ControlNet Union 2.1 (Apache-2.0) for layout and inpainting. Never Krea (its US$1M cap) or its LoRAs. Weight hashes in `tools/storybook/model_hashes.json`; each picture's sidecar JSON is its provenance.
- Working pictures go to `tools/storybook/out/` (git-ignored); shipped layers go to `godot/art/storybook/<id>/`.

## Gotchas
- ComfyUI: `C:\Users\munch\AppData\Local\Comfy-Desktop\ComfyUI-Installs\ComfyUI\ComfyUI\.venv\Scripts\python.exe main.py --port 8188 --extra-model-paths-config "%APPDATA%\Comfy Desktop\instance-model-paths\inst-1790761498447.yaml"` (cwd: that ComfyUI folder) if nobody has it up. Z-Image: CLIPLoader type `lumina2`, ModelSamplingAuraFlow shift 3, 9 steps, cfg 1, res_multistep/simple.

## Read first
1. docs/story/storybook/sb00_stay_where_they_reach.md
2. docs/storybook/README.md (the format, once the solver writes it)
3. docs/team/storybook.md (status)
