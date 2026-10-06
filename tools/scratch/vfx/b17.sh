#!/usr/bin/env bash
# Every column of light now upright on the screen (an evolution's, a chest's, the night's); the
# tether's wider coil; Hallowed Ground's blast in gold; loot's light again (nothing broken).
cd "$(dirname "$0")"
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a191ed81e2df462cf
(cd "$WT/godot" && dotnet build 2>&1 | grep -E " error |Build succeeded" | head -3)
python sweep.py sw3 grave_tether hallowed_ring "hallowed_ring:4@pyre_of_faith" --count 8 --every 0.2
python shot.py lf_tiers_night --quick warden --tier 2 --lab --zone arena --people dead --time night --loot-tiers --loot-at 3 --seconds 6 --count 1
python shot.py lf_tiers_day --quick warden --tier 2 --lab --zone verge --time day --loot-tiers --loot-at 3 --seconds 6 --count 1
echo done
