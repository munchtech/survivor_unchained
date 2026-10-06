#!/bin/sh
# The successor's judging runs: sh judge_runs.sh [drive|hollow|map|dead|deadday|chest]
E=/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/experience
F="--quick warden --sex female --log 10"
for w in "$@"; do
  case $w in
    # The drive (the Hollow's third stage) begun on its own, a frame every 1.5 s for two minutes.
    drive) python "$E/play.py" jd_drive --timeout 900 -- $F --night hollow --stage 2 --auto --seconds 3 --every 1.5 --count 80 | head -3 ;;
    # The Hollow whole, on the autopilot, a frame every 10 s.
    hollow) python "$E/play.py" jd_hollow --timeout 2400 -- $F --night hollow --auto --seconds 8 --every 10 --count 80 | head -3 ;;
    # A map: the start, then its ruler.
    map) python "$E/play.py" jd_map --timeout 600 -- $F --zone map --tier 1 --people dead --auto --seconds 5 --every 8 --count 12 | head -3
         python "$E/play.py" jd_ruler --timeout 300 -- $F --zone map --tier 1 --people dead --at boss --auto --seconds 5 --every 6 --count 10 | head -3 ;;
    # Thirty bodies down at once, then lying: the death poses, by night and by day.
    dead) python "$E/play.py" jd_dead --timeout 300 -- $F --zone arena --people dead --time night --tier 1 --lab --give "judgement_disc:8,axe_gyre:8" --horde 34 --dist 4 --spread 6 --seconds 3 --every 1.5 --count 6 | head -3 ;;
    deadday) python "$E/play.py" jd_deadday --timeout 300 -- $F --zone arena --people dead --time day --tier 1 --lab --give "judgement_disc:8,axe_gyre:8" --horde 34 --dist 4 --spread 6 --seconds 3 --every 1.5 --count 6 | head -3 ;;
    # A map's strongbox at her feet at 3 s, its opening shot every 0.3 s.
    box) python "$E/play.py" jd_box --timeout 300 -- $F --zone map --tier 1 --people dead --auto --strongbox --chest-at 3 --seconds 3.2 --every 0.3 --count 22 | head -3 ;;
  esac
done
