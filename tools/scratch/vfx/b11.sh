#!/usr/bin/env bash
# Loot's light: a Legendary's fall (its light down the screen onto it, the pillar standing up out
# of it) and the lesser lights growing up out of the ground as they land. (--loot's first drop
# is 1.5 s after --loot-at.)
cd "$(dirname "$0")"
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a191ed81e2df462cf
(cd "$WT/godot" && dotnet build 2>&1 | grep -E " error |Build succeeded" | head -3)
P="--quick warden --tier 2 --lab"
DAY="--zone verge --time day"
NIGHT="--zone arena --people dead --time night"
python shot.py ld_fall_day $P $DAY --loot legendary --loot-at 3 --seconds 4.45 --every 0.06 --count 20
python shot.py ld_fall_night $P $NIGHT --loot legendary --loot-at 3 --seconds 4.45 --every 0.06 --count 20
python shot.py ld_ring_day $P $DAY --loot --loot-at 3 --seconds 4.45 --every 0.1 --count 10
python shot.py ld_day $P $DAY --loot --seconds 8 --every 1.5 --count 1
echo done
