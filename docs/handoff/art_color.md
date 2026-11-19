# Lane J: art and colour (day/night as data, painted cel that is ours)

## TOP BLOCK (state file; read first) — HANDOFF READY art-color (19 Nov, lead 1 stopped at its 250k budget)
- Lead 1: lane J art-color lead (su-lead-high), reporting to coordinator #15. Brief: C:\Users\munch\Desktop\survivorsunchained_inputs\scratch_coord15\briefs\J_art_color.md (read whole). Owner ref: ...\scratch_coord15\owner_frames\owner_ref_night_day_colors_19nov.webp (split copies in the worktree's godot/.shots/ref/ref_day.png, ref_night.png).
- Worktree: C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a4d7d9ecb5b5bf562 (godot/assets is a junction to its OWN public/assets, assume-unchanged; .godot/imported seeded). Branch art-color off origin/claude/vigilant-galileo-l6jqyx@446daf74d; tip = the commit that adds this block (pushed).
- Items: art-day-night (3 judge rounds, 0 spent), art-cel-unique (3 rounds, 0 spent). Gate: one fresh su-lead-max judge per item, `Effort tier: always-seen`, effort max, 1:1 frames beside the ref. Nothing judged yet; nothing shown to the owner.
- Shoot: `SECS=14 bash C:/Users/munch/Desktop/survivorsunchained_inputs/scratch_coord15/lane_j/shoot_j.sh TAG 1 "name|--zone verge --time day"` (build+import+shoot; frames godot/.shots/TAG_name.png; logs godot/.shots/logs_TAG/). Measure: `python tools/style/palette.py a.png b.png`. Pairs: night left, day right, half size.

### Built (step 1, day and night as data)
- rigs.json top-level "palettes" (wild_day, wild_night), named by rigs day_wild / night_wild ("palette"; ravine sets null). Per class leaf, grass, ground, path, stone, bark: ramp [dark, mid, lit] sRGB over sqrt(albedo lum) in range, amount. Palette-level: "value" (0 ramp's value .. 1 albedo luminance kept; day .4, night .4), "ember" {near, far, keep} (night: her pool keeps its own ground), "glow" (night sources).
- Code: logic/Look/Palettes.cs (flatten 6x12+4, Blend), Rigs.cs (palettes, Glows, Lit sets Palette/GlowName/GlowK), Zone.cs (AtmosphereSet fields), Atmospheres.Blend, src/World/Atmosphere.cs (SetPalette -> 19 globals pal_*; `--pal off`; glow_k), shaders/palette.gdshaderinc (pal_ramp, pal_keep, per-tree leaf shift 0.3*hash), calls in kit.gdshader (leaf, bark, stone), grass_own.gdshader, terrain.gdshader (ground; path by its own sharper mask smoothstep(.55,.66,pm.r)). NightGlow.cs + glow_cap.gdshader (caps at tree feet, light on 40% of clusters), built by ZoneView.
- Rig light: night_wild key #9c98e8, exposure 1.6, sky #b0a8ff, ember 4.0 #ffb070; day_wild exposure .8, fill #a080ff .3.
- Commits: 29a83b6d3 plumbing, 96a9e6677 ember keep, 90ad37e41 value/shift, 878a8fc8a night glow, then this one (j7 data, glow spread/light share, path mask).
- Frames: j0 baseline, j4 (sent to main), j6, j7 in godot/.shots; durable copies survivorsunchained_inputs/scratch_coord15/lane_j/frames/ (j0, j4 pairs).
- Numbers j7: day Lp50 .54 key 1.42 shH 26 shC .040 midC .134; night Lp50 .25 key 1.57 shH 281 shC .073 midC .086. Ref: day .51/1.50/7/.049/.133; night .37/2.15/274/.076/.160.

### Coordinator's read of j4 (19 Nov, not a judge), to fix before ink
"Night: one flat hue ... Give the base less chroma and a lower value, and put the hue in the sources and their pools. Her orange fire pool is the only accent now, and it reads as a stain. Day: it reads salmon and pink, not autumn ... Pull red toward orange and gold, keep the leaf shadow areas deep, and give the path a defined shape rather than a glow band. Both: values must keep the dark frame edges and the lit path through the middle. Check her skin band on both." Done since: night base darker and less chroma, foliage violet/teal apart from the ground (j6/j7); leaves moved toward orange (h 35 -> ref 42); path mask sharper. NOT yet: glow visible, gold leaves, path edge reading, skin check.

### NEXT, in order
1. BUG: the night glow does not show (j6 = j7 night frames identical though 866 clusters / 331 lights built). Suspect GlowK never > 0 on the play air (NightGlow hides under 0.01) or Atmosphere.Set reads GlowK off the unlit preset; check with a GD.Print of Atmosphere.GlowK in a night shot. Then tune caps/light (energy 2.2, range 3.6) so each cluster tints the ground round it.
2. Day: leaves still read salmon at the near crown (L .65); push gold tips (lit stop reached on sunlit sprays, or shift), deepen leaf shade, path edge; shadows to violet-brown (shH 26 -> ~0-10).
3. Her pool at night (orange stain): make it part of the palette (paler gold, smaller) or tint it by the glow; her skin band check (demo_look_check.py rows for her skin) day and night.
4. Dusk/dawn palettes (the base Dusk/Dawn presets name no rig; Blend null-fades), then the den toward the night panel (lane E's PASS den is warm umber: touch lightly, the coordinator to rule).
5. Step 2 cel push: world ink and inner lines on rocks/roots/leaves, flat bands, one-scale strokes, coloured shadows; 2-3 signature ideas sheet (one frame each) to main BEFORE building any.
6. Step 3 skills on both palettes; step 4 perf (den 30+ foes, 1080p/1440p, before/after; lane E's cap +1.0 ms; NightGlow's 331 lights need a cost number).
- Agents: workers af7e1691bb4a4d057 (plumbing), a6b5e58fc6523e008 (glow), both done. Cost: lead ~250k, workers ~175k.
- Scratch: lane_j shoots j1-j3, j5 superseded (godot/.shots, git-ignored, go with the worktree).
