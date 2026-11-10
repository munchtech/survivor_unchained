# The chained swing: a cut is a share of the blow (M3 MR 3, 10 Nov)

Sunder and Oathblade are written as BLOWS (Sunder 28 every 1.6 s, Oathblade 22.81 every 1.05 s) and swung, when held, as a chain of CUTS (`press.chain.period`, 0.70 s). The record keeps the blow; the chain block only says how long a cut is. A reader that knows nothing of chains (the arena, the kindled form, a tool) gets the blow as written.

**The weight.** A cut weighs the share of the blow's wait that its own period takes: Sunder 0.70 / 1.6 = 0.4375, Oathblade 0.70 / 1.05 = 0.6667; a heavy cut on a longer clip weighs more by its period (`SwingChain.PeriodScale`). The weight is live only inside the cut's cast (`WeaponInst.CutW`, as `FireMul` is): cards, echoes, DoT ticks and zones read the written blow.

**Rates hold per second.** Damage, Resolve, Flare fill, lifesteal, knockback travel, boss stagger, heavy counts (own, Hand, rite), stack and chill build, flat procs. Counts are kept in written blows with the part carried (`Sim/Blows.cs`), never reset.

**Events keep the blow.** A heavy's extras land whole (Sunder's line at 28, the heavy's Resolve and shove extra). The opening cut of a count is a whole blow (the first heavy comes no later than about today's: Sunder cut 8 at 4.9 s). An opener crit lands whole on the first cut. A Shock is eaten by one blow's worth of cuts. A death burst and a DoT's size read the blow the cut is a share of. Once-per-firing keys are once per written blow.

**Rule for lamp and wick writers (owed, logged by the coordinator).** Code counts a blow's worth, never cuts: "every third blow" is 3 blows' worth of cuts (6.86 Sunder cuts, 4.5 Oathblade cuts), and what it throws is blow-sized. So lamp WORDS must never say "every third swing", "once a swing" or "in one swing": a player counts cuts and the number will not match. Say a time ("every 3 s of cutting throws a crescent"), or name the heavy ("each heavy cut"), which the player can see. A "kills N in one swing" lamp is counted over one blow's worth of cuts.

Design and audit: `survivorsunchained_inputs\scratch_combat_m3\lead10\s3_weight_design.md`, `s3_audit_A.md`; the first audit `lead9\s3_audit.md`. Acceptance (crit off, 63.9 s held, chained against unchained): Sunder one foe damage +0.50%, Resolve +0.54%; Sunder three foes +0.50% / +0.54%; Oathblade -1.61% / -1.49%; heavies equal.
