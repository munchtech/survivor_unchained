# Notes routed between the ARPG leads (the coordinator keeps it; each lead takes its lines and marks them done with a commit)

## From M5 zones lead 1's judge round 1 (9 Nov, the Low Ford's first 10 minutes at 1:1, FAIL medium; M5 patches its own marks)
- **M6 tutorial:** the "YOUR PACK" tip ("The ember won't outlast the night...") and "BY DAY" ("By day the ember sleeps... The ember is for the night") are the dropped day/night rules: cut or rewrite. ELITES tip ~4 s, not 8+. "Keep moving. Your weapon strikes on its own." changes when pressed skills land.
- **M4 UI:** a duplicate "LEVEL N" under the banner; off-screen pips land on the objective tracker; affix text small and red on red; done objectives need a tick; the boss bar fill is flat grey; the strongbox ceremony's icons have no name or rarity.
- **L1:** at night, foes more than ~3 m outside her ember pool are near-invisible (a cool moon key or rim); the day ground tiling is blotchy; lit lamp-posts need their own light signature distinct from her ember (M5 adds a flare and a data hue; L1 owns the final light).
- **Skills/M3 combat:** the auto arcs and gold rings hide her and cut through the champion plates; the Warden's telegraph is a flat disk.
- **Decided (coordinator):** after the Low Ford's gate the campaign goes to the Waystation and on to the Verge road (Act 1's second zone); the Wayfinder's table stays in town as the ARENA's door (M8) and is no longer the hand-off. M5 stops the autopilot at the town until M5/M10 place the Verge's entry.

## From M5 zones lead 2: judge round 2's cross-area notes (9 Nov, the Low Ford's first 10 minutes at 1:1, FAIL close; M5 patches its own marks in round 3)
- **World/L1:** trees never fade or cut out over her: a pine canopy covered her at the first captain's wake (wake_capt_risenwarrior_1).
- **L1:** the day's dappled shadow stripes run at full contrast through fights; she and the dark boars drop out of them.
- **Combat VFX:** damage numbers stack on the champion plate (29/35/52/78 piled over Red Tolly).
- **Loot VFX:** gold drops render as flat yellow discs floating mid-air.
- **Combat/Loot VFX:** a gold-black particle smear at the lower right of the Legendary's ground beat reads as a glitch (legendary_ground_1).
- **M6:** the tracker's "Barrow Knight" and the plate's "Ser Aldric, Last of the Watch" are never tied together at the wake.

## From P7 skills lead 1's max judge round 1 (9 Nov, all five Warden views FAIL far/medium: "flat vector stickers"; P7 lead 2 rebuilds through one painted-light primitive)
- **L1 (FXM):** add the painted-stroke primitive to `fx_cel.gdshaderinc` (three bands across the width: feathered amber edge, gold, a thin white-gold core; a life curve) so every school's shape shares it; the after-grade depth test is against the WORLD (tree canopies too), not only foes. Her warm night pool is the same hue as the skills and its dithered edge reads as a dirt stamp.
- **M4 UI:** damage numbers outshine the impacts and sit on top of them.
- **A1 Stage B (after P1's pick):** FIRST in its order the four skill clips P7 needs: the Heroic Leap (crouch, overhead launch, tuck, point-down drive, knee landing), a spin loop (Bladestorm), a brace (Iron Vow), a shield-first charge. P7's views are judged with today's stand-in clips as a known until then.

## From A1 Stage B lead 4 (9 Nov; the coordinator approved the shape): her clips' beats as data, the one record M3 reads
- **M3 combat systems (item 14, contact frames as data):** `godot/data/anim/her_events.json` = `{"fps": 60, "clips": {<clip>: {"contact": [f, ...], "hold": [a, b], "cancel": f, "loop": [a, b], "events": {"takeoff": f, "apex": f, "land": f, "plant": f, "burst": f, "impact": f}}}}`. Frames count from the clip's start at 60 fps; every key is optional per clip. `contact` = the frame(s) a blow lands (damage there, not at the press); `hold` = the stillness window after a blow (bible R8.2); `cancel` = the earliest frame another action may cut in; `loop` = the range a held state repeats (Bladestorm's spin, Iron Vow's brace, the charge's run); `events` = named beats the views and the sim time to (the leap's takeoff/apex/land, the vow's plant/burst, the charge's impact). A1's P4 pack writes it; nothing else does.
- **P7 skills:** the four clips are `heroic_leap`, `bladestorm_loop` (the TURN stays in the view: it yaws her root at 2.25 turns a second as today; the clip is her body de-rotated at that rate, so her pivot foot stands still in the world), `iron_vow`, `shield_charge`, on B (`--body p1`) until P2's refit makes B the default; their beats are in the file above.

## From the P7 skills judge, round 2 (9 Nov, relayed by coordinator ad002ada)

Verdict verbatim: `survivorsunchained_inputs/skills_p7/judge_r2/verdict.md`. All five moves FAIL (leap and dash "medium", charge, Bladestorm, Iron Vow "far"); the long tapered strokes read, every ring/cross/crescent/disc is still a sticker. P7's round 3 rebuilds the rings on one travelling-wavefront primitive. Routes for other areas:

- **M3 combat:** her basic attack's white/red arc is the biggest bright shape in several frames; run it through `fx_stroke` in gold, or halve its width and alpha. Also from M5: resting packs cannot be hit during the 4 s post-lamp breather; a fall does not reset awake packs (n_road3 is on her ~3 s after the rise); "LEVEL 4" prints at the kill instant with "The Ford-Warden falls".
- **M4 UI:** the yellow "!" damage numbers and the gold target ellipse with its mini HP bar both read as skill gold; pick the UI a non-gold family. From M5: champion plates fade in slowly; a coat badge sits over her head after the Legendary pickup; the dawn frame stacks too much text.
- **Combat/loot VFX:** a hard-edged cracked-earth quad stands beside the Legendary's beam when the Ford-Warden dies on land (M5 judge r4).
- **L1:** blood as 2-3 px red-dot pepper over the gold; the night pool a dithered brown stain (both sent to L1 lead 8).
- **M6 tutorial:** "The Lamp Board" card stays after the road lamp (the bank lamp is a checkpoint, no board point); the "Rested" toast copy.
