#!/bin/sh
# The day clock's checks at 1920x1080 (play.py runs from the experience worktree): sh clock_runs.sh [which...]
E=/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/experience
F="--quick warden --sex female --log 5"
run() { name=$1; shift; python "$E/play.py" "$name" --timeout 600 -- $F "$@"; }
for w in "$@"; do
  case $w in
    dusk)   run cl_dusk --zone waystation --clock 590 --facts hollow.hostile=true --auto idle --seconds 3 --every 20 --count 8 ;;
    answer) run cl_answer --zone waystation --clock 714 --facts hollow.hostile=true --auto idle --answer 9 --seconds 3 --every 3 --count 8 ;;
    verge)  run cl_verge --zone verge --clock 714 --auto idle --seconds 3 --every 4 --count 5 ;;
    nightout) run cl_nightout --zone verge --clock 1062 --auto idle --seconds 3 --every 4 --count 9 ;;
    nudge)  run cl_nudge --zone waystation --clock 897 --auto idle --seconds 5 --count 1 ;;
    fall)   run cl_fall --night hollow --stage 3 --auto idle --choose rise --die 10,26 --seconds 4 --every 3 --count 22 ;;
    letgo)  run cl_letgo --night hollow --stage 3 --auto idle --choose letgo --die 10 --seconds 4 --every 3 --count 16 ;;
    pauses) run cl_pauses --zone waystation --clock 60 --open inventory,journal,map,rest --every 5 --seconds 24 --count 1 ;;
  esac
done
