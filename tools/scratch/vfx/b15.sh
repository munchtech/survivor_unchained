#!/usr/bin/env bash
# The tub in the Dig's dark; Grimtunnel's mound in the Dig's clay; and a sweep of the skills still
# below the bar (the warden's white cog, Iron Palms, Moonbrand, Firepot, Grave Tether, Hallowed Ground).
cd "$(dirname "$0")"
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a191ed81e2df462cf
(cd "$WT/godot" && dotnet build 2>&1 | grep -E " error |Build succeeded" | head -3)
python shot.py td_dig --quick warden --sex female --night dig --stage 1 --lab --tubs --on boss --until 9
python shot.py td_day --quick warden --zone verge --time day --tier 2 --lab --tubs --on boss --until 5
python shot.py dg3d --quick warden --sex female --night dig --stage 3 --auto --on boss --until 14
python sweep.py sw1 judgement_disc iron_palms moonbrand firepot grave_tether hallowed_ring --count 12 --every 0.15
echo done
