# Handoff: rendering (global light, exposure, tonemap, grade, her light vs the scene's)

## Now (Rendering 1, 28 Oct): round 0 judged; round 1 building
- **Worktree** `.claude/worktrees/rend-1`, branch `rend-1` (from integration 7b94438d; `godot\assets` is a junction to its OWN `public\assets`, assume-unchanged). Scratch (coordinator's pad): `...\scratchpad\rend1\` (shoot.sh, r0.txt shot list, measure.py, sheet.py, briefs, verdicts, r0\ frames).
- **Ownership (main, 28 Oct):** Atmosphere.cs, Atmospheres.cs, the close-up/Look rig and the camp lantern (lowford props_own.json `lamps`, one small commit) are ours. Environment 22 owns the town cobble patches (its item 8) unless they come from AO or shadow. Send main the LowFordNight preset commit's hash when it lands (Environment merges it before it judges the wood road).
- **Round 0 (triage judge, max, 150k; `verdict_j0.md`):** 30 baseline frames at 1:1. Only the day Look passes on light. We don't need our own tonemap pass.
  - CLOSED, not visible at 1:1: (1) night crushes her and the dead (at Low Ford it's the opposite, lifted); (2) the lantern blowout from AgX; (6b) the BattleFx discs and halo look hairy.
  - OPEN:
    - (3) She reads spotlit at the night close-up (medium; the rig: key from the named source at ~3:1, a weak cool fill, a fire rim when she faces away, a key at ~3000K; the background toward 6x).
    - (4) Low Ford at night is a lifted violet wash (p50 38-47, pools 0.35; the target is p50 25-30, pools >= 0.55, p95/p50 >= 2.5, the shade a less saturated teal-blue, the moon key kept). Env's earlier judge failed "near-black navy, one hue", so don't overshoot.
    - (5) The camp lantern outshines the fire (close; the lantern 1/3-1/2 of the fire's energy, range 0.6x, the fire's pool larger).
    - (6a) The town light flattens her face at the close-up and the Look by night.
    - New: deep skin goes rust-red at night; the town's day shade is warm brown; her ember is off in town at night (she's dim).
- **Round 1 split:** solver A = the presets (Atmospheres.cs: LowFordNight, the town presets, the town ember) plus the camp lantern and fire. Solver B = her rig (GameCloseUp.cs, the Look rig, a skin guard in Atmosphere.cs GradeLut).
- **Then:** a round 1 judge on the same frames (r0.txt). When it passes, the owner gets one half-size before | after sheet (night close-up, Low Ford at night, camp, town by night), then the MR.
- **Cost so far:** judge r0 150k. Lead ~120k.
