#!/usr/bin/env bash
# The new tub run past her (--tubs) by day and in the Dig; Grimtunnel sunk with his mound; the
# rise's wall deeper in colour; loot's light growing as a hoard lands.
cd "$(dirname "$0")"
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a191ed81e2df462cf
(cd "$WT/godot" && dotnet build 2>&1 | grep -E " error |Build succeeded" | head -3)
python shot.py tb_day --quick warden --zone verge --time day --tier 2 --lab --tubs --on boss --until 7
python shot.py tb_dig --quick warden --sex female --night dig --stage 1 --lab --tubs --on boss --until 7
python shot.py dg3b --quick warden --sex female --night dig --stage 3 --auto --on boss --until 22
python shot.py rise_wall9 --quick arcanist --zone arena --people dead --time night --tier 2 --lab --give "seeking_motes:4,+from_the_ashes:2" --horde "70,8:risen!" --dist 3 --spread 9 --seconds 3.0 --every 0.25 --count 12 --fall-at 3
python shot.py lg_hoard --quick warden --tier 2 --lab --zone arena --people dead --time night --hoard 2 --seconds 1.4 --every 0.1 --count 14
echo done
