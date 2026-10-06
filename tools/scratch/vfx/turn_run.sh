#!/usr/bin/env bash
# Wait in line for a turn of KIND (turn.py --wait keeps our place in the queue), run SCRIPT, and
# give the turn back whatever happens:
#   bash turn_run.sh godot "skills: b1 ..." b1.sh
cd "$(dirname "$0")"
TURN=/c/Users/munch/Desktop/survivorsunchained/tools/turn.py
KIND="$1"; WHO="$2"; SCRIPT="$3"
python "$TURN" take "$KIND" "$WHO" --wait 120 || { echo "no turn"; exit 1; }
trap 'python "$TURN" give "$KIND" "$WHO"' EXIT
echo "turn taken $(date +%T)"
bash "$SCRIPT"
echo "script done $(date +%T)"
