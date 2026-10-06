#!/usr/bin/env bash
# Hallowed Ground's ring of runes in the air; Grave Tether's coil; burning ground standing in flame
# (Firepot, Pyre of Faith); the chakram's worn face and the tub's spoil in the Dig.
cd "$(dirname "$0")"
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a191ed81e2df462cf
(cd "$WT/godot" && dotnet build 2>&1 | grep -E " error |Build succeeded" | head -3)
python sweep.py sw2 hallowed_ring grave_tether firepot "hallowed_ring:4@pyre_of_faith" --count 12 --every 0.15
python shot.py te_dig --quick stalker --sex female --night dig --stage 1 --lab --give "gale_chakram:4" --tubs --on boss --until 9
echo done
