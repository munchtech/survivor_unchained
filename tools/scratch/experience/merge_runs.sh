#!/bin/sh
# The landed merges, judged in play: sh merge_runs.sh [dead|hollow|stages|map]
E=/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/experience
F="--quick warden --sex female --log 10"
for w in "$@"; do
  case $w in
    # Thirty bodies down at once, then lying: the death poses side by side.
    dead) python "$E/play.py" mg_dead --timeout 300 -- $F --zone arena --people dead --time night --tier 1 --lab --give "judgement_disc:8,axe_gyre:8" --horde 34 --dist 4 --spread 6 --seconds 3 --every 1.5 --count 6 | head -1 ;;
    # The Hollow whole, on the autopilot, a frame every 15 s.
    hollow) python "$E/play.py" mg_hollow --timeout 1200 -- $F --night hollow --auto --seconds 10 --every 15 --count 52 | head -1 ;;
    # Each stage begun on its own.
    stages) for n in 0 1 2 3; do python "$E/play.py" mg_stage$n --timeout 300 -- $F --night hollow --stage $n --auto --seconds 6 --every 8 --count 6 | head -1; done ;;
    # A map: the start and its ruler.
    map) python "$E/play.py" mg_map --timeout 300 -- $F --zone map --tier 1 --people dead --auto --seconds 5 --every 10 --count 6 | head -1
         python "$E/play.py" mg_ruler --timeout 300 -- $F --zone map --tier 1 --people dead --at boss --auto --seconds 5 --every 6 --count 10 | head -1 ;;
  esac
done
