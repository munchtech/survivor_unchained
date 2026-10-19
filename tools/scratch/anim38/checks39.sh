#!/bin/bash
# checks39.sh: animation 39's scoped post-merge checks then the 48-frame shoot and grid, sequential, one log each.
W=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a6b5a13d0be70144d; P=/c/Python314/python; S=$W/tools/scratch/anim38
cd $W
$P tools/anim/motion.py crossbow_shoot stalker_show stop_stalker_l stop_stalker_r idle_stalker idle_stalker_break idle_stalker_daggers idle_arcanist arcanist_show flare_burns_twice --outfits > $S/rb_motion.log 2>&1; echo "motion $?"
$P tools/anim/motion.py stalker_show stop_stalker_l stop_stalker_r idle_stalker idle_stalker_break idle_stalker_daggers --hero > $S/rb_motion_hero.log 2>&1; echo "motion_hero $?"
$P tools/anim/armscheck.py --sockets --keep --jobs 4 > $S/rb_arms.log 2>&1; echo "arms $?"
for p in axe crossbow dagger_l daggers staff sword viking_sword; do $P tools/anim/fistfit.py $p > $S/rb_fist_$p.log 2>&1; echo "fist_$p $?"; done
$P tools/anim/audit.py > $S/rb_audit.log 2>&1; echo "audit $?"
(cd godot && dotnet test SurvivorUnchained.sln > $S/rb_dotnet.log 2>&1; echo "dotnet $?")
for t in 1 2 3; do sh $S/gshoot2.sh $S/shots38.txt $S/shots_final > $S/shots_final.log 2>&1 && break; echo "shoot try $t failed"; grep -q 'NO TURN' $S/shots_final.log || break; done
grep -c ' ok$' $S/shots_final.log; grep 'MISSING\|IMPORT\|PACKED' $S/shots_final.log
$P $S/grid.py $S/shots_final $S/shots38.txt $S/shots_final/_grid.jpg
echo CHECKS DONE
