#!/usr/bin/env bash
# After: loot's light remade as light held upright on the screen (loot_beam.gdshader), by day and by
# night, with the ground labels and the edge's pointer; a Legendary's light falling onto it.
cd "$(dirname "$0")"
VFX="$(pwd)"
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a191ed81e2df462cf
(cd "$WT/godot" && dotnet build 2>&1 | grep -E " error |Build succeeded" | head -3)
P="--quick warden --tier 2 --lab"
DAY="--zone verge --time day"
NIGHT="--zone arena --people dead --time night"
python shot.py la_day $P $DAY --loot --seconds 8 --every 1.5 --count 2
python shot.py la_night $P $NIGHT --loot --seconds 8 --every 1.5 --count 2
python shot.py la_tiers_day $P $DAY --loot-tiers --loot-at 3 --seconds 2.9 --every 0.12 --count 10
python shot.py la_tiers_night $P $NIGHT --loot-tiers --loot-at 3 --seconds 2.9 --every 0.12 --count 10
python shot.py la_far $P $DAY --loot legendary --far --seconds 4 --every 1.5 --count 2
python shot.py la_far_night $P $NIGHT --loot legendary --far --seconds 4 --every 1.5 --count 2
python shot.py la_hoard $P $DAY --hoard 3 --seconds 8 --every 1.5 --count 2
python shot.py la_hoard_night $P $NIGHT --hoard 3 --seconds 8 --every 1.5 --count 2
python shot.py la_crowd $P $NIGHT --loot-tiers --loot-at 3 --horde "50:risen" --dist 4 --spread 8 --seconds 5 --every 1 --count 2
echo done
