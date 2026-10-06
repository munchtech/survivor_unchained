#!/usr/bin/env bash
# The Dig's moments one frame each (--on boss: the tub on its rail, the barrel's fuse, Grimtunnel
# under, the ground going, the crack); the rise's wall on its ring of turned cards; loot's light
# growing out of the ground as a hoard lands.
cd "$(dirname "$0")"
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a191ed81e2df462cf
(cd "$WT/godot" && dotnet build 2>&1 | grep -E " error |Build succeeded" | head -3)
python shot.py dg1 --quick warden --sex female --night dig --stage 1 --auto --on boss --until 40
python shot.py dg3 --quick warden --sex female --night dig --stage 3 --auto --on boss --until 50
python shot.py rise_wall8 --quick arcanist --zone arena --people dead --time night --tier 2 --lab --give "seeking_motes:4,+from_the_ashes:2" --horde "70,8:risen!" --dist 3 --spread 9 --seconds 3.0 --every 0.25 --count 12 --fall-at 3
python shot.py lg_hoard --quick warden --tier 2 --lab --zone arena --people dead --time night --hoard 2 --seconds 0.3 --every 0.1 --count 14
echo done
