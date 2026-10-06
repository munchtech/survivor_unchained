#!/bin/bash
# Attribution and settings sweeps, after the A/B battery.
S="C:/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad"
W="C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a9586a5171413db0b"
B="$S/dll_new2"
until [ $(grep -c "done:\|timed out\|no result" "$S/perf_ab1.log") -ge 14 ]; do sleep 15; done
cd "$W"
python -u tools/perf/sweep.py hub off "props,landmarks,flora,pieces,sunshadows,lampshadows,her,grass,ssao,volfog" --build "$B" --wait 20 --tag hubA > "$S/sw_hub_off.log" 2>&1
python -u tools/perf/sweep.py hub prop-cell "48,64,1000" --build "$B" --wait 20 --tag hubC > "$S/sw_hub_cell.log" 2>&1
python -u tools/perf/sweep.py hub engine "--render-thread safe|--render-thread separate" --build "$B" --wait 20 --tag hubE > "$S/sw_hub_eng.log" 2>&1
python -u tools/perf/sweep.py dense off "her,crowd,fx,grass,flora,pieces,sunshadows,ssao,volfog,taa,msaa,hud" --build "$B" --wait 20 --tag denA > "$S/sw_dense_off.log" 2>&1
python -u tools/perf/sweep.py dense quality "low,medium,high" --build "$B" --wait 20 --tag denQ > "$S/sw_dense_q.log" 2>&1
python -u tools/perf/sweep.py dense scale "quality,balanced,performance" --build "$B" --wait 20 --tag denS > "$S/sw_dense_s.log" 2>&1
python -u tools/perf/sweep.py hub quality "low,medium" --build "$B" --wait 20 --tag hubQ > "$S/sw_hub_q.log" 2>&1
echo SWEEPS DONE
