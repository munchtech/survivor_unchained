#!/usr/bin/env bash
# Loot's light as light (a line in a glow, threads, a shimmer), by day in the Verge and by night in
# the arena after a fight; the cold over the crowd's heads.
cd "$(dirname "$0")"
VFX="$(pwd)"
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-abc6bbe020c7fe287
(cd "$WT/godot" && dotnet build 2>&1 | grep -E " error |Build succeeded" | head -3)
python shot.py loot_day2 --quick warden --zone verge --time day --tier 2 --give "oathblade:5,dawnpulse:4" --horde "30,6:risen!" --dist 4 --spread 8 --seconds 3.6 --every 0.7 --count 4 --loot --loot-at 3
python shot.py loot_night2 --quick warden --zone arena --people dead --time night --tier 2 --lab --give "oathblade:5,dawnpulse:4" --horde "40,6:risen!" --dist 4 --spread 8 --seconds 3.6 --every 0.7 --count 4 --loot --loot-at 3
python shot.py rise_wall5 --quick arcanist --zone arena --people dead --time night --tier 2 --lab --give "seeking_motes:4,+from_the_ashes:2" --horde "70,8:risen!" --dist 3 --spread 9 --seconds 2.9 --fall-at 3 --until 7
echo done
