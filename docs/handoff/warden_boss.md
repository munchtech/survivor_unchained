# The Ford-Warden: boss-tier model rebuild (handoff)

## Start here / Paused here; next:
**Lead:** Warden lead 1 (21 Oct). Worktree `.claude/worktrees/warden-1`, branch `warden-1` (from integration 84cb7f7d). `godot/assets` is a junction to THIS worktree's `public/assets` (assume-unchanged). Scratch: coordinator c4134bd3's scratchpad `warden\`.
**State:** plan sent to the coordinator (below). Next: concept sheet (Krea 2 on local ComfyUI, 3 options, turnaround + head bust + gauntlet), half-size sheet to the coordinator for the owner's pick.

## The brief (owner, 21 Oct)
"Treat the Warden as boss-tier art: route his model to a full-detail rebuild." Judged at her bar: `su-lead-max` max at his close cinematic framings, xhigh at the play camera; whole-frame gate first; 1:1 game cameras only; round cap 2-3.
Done = new model in game, rigged and animated for C02/C03 (and the fight), max PASS at the closest framing, merged; then C03 s1, s3, s4, s5 go back to the cinematics lead.

## Facts (checked)
- Today: `godot/src/Actors/BossViews.cs` `WardenView` = a Quaternius townsman (ranger outfit, hood dyed `#3a3e44`) through `PersonView` at `0.8 * 2.6` scale, Sketchfab zweihander in the right hand, `LampIron` (code-built) hung from `hand_l` by a BoneAttachment, emissive eye materials (`Eye` in the name), an OmniLight.
- Clips he plays: fight `Sword_Idle`, `Sword_Attack`, `Idle_Shield_Loop`, `Jog_Fwd_Loop`, `Hit_Head`, `Spell_Simple_Idle_Loop`, `Death01`, `LayToIdle`, `Zombie_Walk_Fwd_Loop`; cinematics `folk/m_kneel_lamp`, `folk/m_lamp_down`, `folk/m_fold_forward` (c02.json, c03.json). All on the shared UAL skeleton.
- Look (docs/cinematics/c02_none_cross.md, docs/art/MODELS_TO_MAKE.md "The Ford-Warden"): hooded giant, long beard heavy with river and weed, two points of cold blue light for eyes deep under the hood, the old Watch's kit soaked (blue tabard `#34508c` over mail, the lamp badge: docs/items/VISUALS.md), "an ancient gauntlet, black with river and grown with weed" holding a NEW clean black lamp-iron (C02 s3, 135 mm insert). No face rig. "Every movement is a tired man's, made enormous."
- Closest framings: C02 s3 (gauntlet + lamp, 135 mm), s5 (rising, water off hood and beard), s7 (2S profile, lamp to her face), s9 (CU, face under the hood lit from below, 85 mm); C03 s1 (head MCU), s3 (CU, low, lamp before his face), s4 (insert beside the left fist).
- Loader: a baked Marionette package `godot/art/npc/NAME/` (body.glb on the game skeleton, lod.glb, manifest.json `baked: true`) builds through `PersonSpec.Body = "npc:NAME"` (`godot/src/Actors/NpcPackage.cs`). The generated guard (npc-2) passed xhigh r3 at chest-up on this path.
- Godot 4.5: `SpringBoneSimulator3D` is available for cloak and beard chains.
