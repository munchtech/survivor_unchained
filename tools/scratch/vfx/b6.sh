#!/usr/bin/env bash
# Loot's light alone (no crowd, no skills) by day in the Verge and by night in the arena, to judge
# the columns cleanly and find what the pale discs by day are; the cold in ice blue.
cd "$(dirname "$0")"
VFX="$(pwd)"
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-abc6bbe020c7fe287
(cd "$WT/godot" && dotnet build 2>&1 | grep -E " error |Build succeeded" | head -3)
python shot.py loot_lab_day --quick warden --zone verge --time day --tier 2 --lab --seconds 3.8 --every 0.6 --count 3 --loot --loot-at 3
python shot.py loot_lab_night --quick warden --zone arena --people dead --time night --tier 2 --lab --seconds 3.8 --every 0.6 --count 3 --loot --loot-at 3
python shot.py rise_wall6 --quick arcanist --zone arena --people dead --time night --tier 2 --lab --give "seeking_motes:4,+from_the_ashes:2" --horde "70,8:risen!" --dist 3 --spread 9 --seconds 2.9 --fall-at 3 --until 7
echo done
