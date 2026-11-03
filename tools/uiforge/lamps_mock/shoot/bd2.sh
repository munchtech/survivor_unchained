#!/bin/bash
# UI 25 reshoot: world-only frames (--nohud) and foot frames with 5 pinned seats + level 14; C's night book base.
W=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/ui-25
T=C:/Users/munch/Desktop/survivorsunchained/tools/turn.py
python $T take godot "ui25: backdrops 2" --wait 3000 --root $W || { echo "TURN REFUSED"; exit 1; }
P='ember=0.6,draught=2,art=0.6,dash=2,level=14,seats=f5:f4:f5:f3:f4'
python shot.py u25_town_day_foot   --quick warden --zone waystation --time day --seconds 12 --hud-pin "$P" --no-banners --teach-end
python shot.py u25_town_day_nofoot --quick warden --zone waystation --time day --seconds 12 --nohud --no-banners --teach-end
python shot.py u25_ford_night_foot   --quick warden --zone lowford --time night --seconds 7 --hud-pin "$P" --no-banners --teach-end
python shot.py u25_ford_night_nofoot --quick warden --zone lowford --time night --seconds 7 --nohud --no-banners --teach-end
python shot.py u25_today_lamps_night --quick warden --zone lowford --time night --board --open arts --xp 3000 --keys SubNext,SubNext --seconds 7 --no-banners --teach-end
python $T give godot "ui25: backdrops 2"
cp $W/godot/.shots/u25_*.png out/ 2>/dev/null; ls -la out; echo "DONE $(date +%T)"
