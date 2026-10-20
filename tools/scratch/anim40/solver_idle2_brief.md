# Solver idle 2: the reaver's hip loops and the arcanist's wand (animation 44, item 3, round 2 of 3)
Spawn on su-lead-high, effort medium, Context budget 200k. Report in your FINAL message to animation lead 44 (never main).
Read `judge_idle1_verdict.md` (short; fixes 1-3) and `solver_idle1_brief.md` "Where and how" (all its rules hold: no stash/reset --hard/checkout ., no hero, no pack, no shoot, no build.py --help or motion.py --help, commit as you go, push, never commit by-products). All files in tools/scratch/anim40/. Solver 1's measuring script: idlemeasure.py.

## Context
- The sockets are data: `godot/src/Actors/Arms.cs` `Sockets` (HipLoop, HipBelt, Sling; read the comment above the table for the row's frame). They were tuned by the armor 5 solver on 19 Oct to clear her thighs and arms in the armed and town runs and sprints. Any socket move must keep that: hands, arms and thighs clear of the piece in every town idle, run and sprint of the callings that use it. `armscheck.py --sockets` and `tools/scratch/anim37/sweep.py` measure the sheathed piece; ArmsDump (godot/tools_scenes/ArmsDump.cs) writes what armscheck reads, so rerun it after a socket change (it is a Godot run: take the godot turn with tools/turn.py --wait, give it back).
- HipLoop also carries Blunt (a mace): keep it plausible for that or note it.
- Who uses which socket: HipLoop = idle_reaver_town (axe; gyre_axes uses both sides, mirrored), run_reaver_town, sprint_reaver_town. HipBelt = idle_arcanist_town, run_arcanist_wand_town, sprint. Sling = idle_stalker_town, run_stalker_town, sprint (they PASSED: don't break them).

## The job, in order
1. **Fix 1, the reaver's hip loop.** Move it so the axe rides behind her hip at about 5 o'clock (12 = forward), the head at the belt, the haft along the back of her thigh, the blade back; the mirrored left at about 7 o'clock (or both crossed at the lower back if the mirror fails). Measure, every frame of the reaver town idle, run and sprint: the closest distance from each HAND (and the wrist/fingers) to the axe head and the haft top (measure the blade, not the haft axis; the judge asked), and the piece into her thighs/buttocks. Target: at least 10 cm from either hand in the idle, at least 4 cm in the run and sprint, 0 mm into her.
2. **Fix 2, the arcanist.** (a) Her right arm over idle_arcanist_town back to the Warden's track (shoulder and elbow), softened as the reaver's; report the right wrist travel (cm) and the shoulder-abduction range against idle_warden_town, before and after. (b) The wand socket (HipBelt): tip down behind the right hip at about 5 o'clock, about 25 deg back, the grip at the leotard's hip line, so nothing shows beside her breast from the 315 camera. Re-measure the town run's right hand to the wand (now 1 mm; want at least 4 cm) and the sprint.
3. **Fix 3 (optional, only if 1-2 are done with budget left):** the crossbow ~10 deg round its sling, the butt ~8 cm back behind her left buttock; the stalker clips must stay 0 mm.
4. Checks on what you changed: motion.py --outfits on the changed clips (0 mm into body; <= 5 mm into outfit), audit (no flags), dotnet build + `dotnet test godot/tests/Tests.csproj --filter FullyQualifiedName~Sheath`.
5. Write `shots_idle2.txt` (copy lines from shots_idle1.txt): every rv*, rvx*, arw*, rrv*, rrvx*, rarw* line and their _p and _c lines; plus stc_c, stc0_m and rstc0_m if you did fix 3.

## Return (under 30 lines)
Per fix: done / not done, the numbers before and after, what moved; the commits; the shot list; what's open.
