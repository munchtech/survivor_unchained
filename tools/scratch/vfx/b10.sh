#!/usr/bin/env bash
# Loot's light, second pass: deeper by day; each light grows out of the ground as it lands; a
# Legendary's light falls down the screen onto it and its pillar stands up out of that.
cd "$(dirname "$0")"
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a191ed81e2df462cf
(cd "$WT/godot" && dotnet build 2>&1 | grep -E " error |Build succeeded" | head -3)
P="--quick warden --tier 2 --lab"
DAY="--zone verge --time day"
NIGHT="--zone arena --people dead --time night"
python shot.py lc_day $P $DAY --loot --seconds 8 --every 1.5 --count 2
python shot.py lc_night $P $NIGHT --loot --seconds 8 --every 1.5 --count 1
python shot.py lc_fall_day $P $DAY --loot legendary --loot-at 3 --seconds 2.9 --every 0.07 --count 18
python shot.py lc_fall_night $P $NIGHT --loot legendary --loot-at 3 --seconds 2.9 --every 0.07 --count 18
python shot.py lc_ring_day $P $DAY --loot --loot-at 3 --seconds 2.9 --every 0.1 --count 14
echo done
