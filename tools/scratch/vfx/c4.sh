#!/usr/bin/env bash
# The unions remade (Frostfire Comet, Butcher's Wheel, Rotwood, the Tempest's colour and quiet marks),
# Thunderhead itself, the way out's band after the fall; then the rest of the evolutions.
cd "$(dirname "$0")"
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-ad059388f00c19f9f
(cd "$WT/godot" && dotnet build 2>&1 | grep -E " error |Build succeeded" | head -3)
python sweep.py u2 frostfire_comet:4 the_tempest:4 rotwood:4 butchers_wheel:4 thunderhead --count 12 --every 0.15
python shot.py won4 --quick warden --tier 2 --zone arena --people dead --time night --minute 29.9 --won --on boss --seconds 4
bash c3b.sh
echo done
