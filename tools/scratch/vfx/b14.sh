#!/usr/bin/env bash
# The tub heaped and lit; Grimtunnel's mound in the Dig's own dirt; the rise's wall deeper still.
cd "$(dirname "$0")"
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a191ed81e2df462cf
(cd "$WT/godot" && dotnet build 2>&1 | grep -E " error |Build succeeded" | head -3)
python shot.py tc_day --quick warden --zone verge --time day --tier 2 --lab --tubs --on boss --until 5
python shot.py tc_dig --quick warden --sex female --night dig --stage 1 --lab --tubs --on boss --until 5
python shot.py dg3c --quick warden --sex female --night dig --stage 3 --auto --on boss --until 14
python shot.py rise_wall10 --quick arcanist --zone arena --people dead --time night --tier 2 --lab --give "seeking_motes:4,+from_the_ashes:2" --horde "70,8:risen!" --dist 3 --spread 9 --seconds 3.0 --every 0.25 --count 12 --fall-at 3
echo done
