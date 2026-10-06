#!/usr/bin/env bash
# First run of the new skills lead: the Dig's marks at 0.28, the five-blade chakram, and the
# three greys (Umbral Bolt, Moonbrand) and Cinderfall's cream, as they are now.
cd "$(dirname "$0")"
VFX="$(pwd)"
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-abc6bbe020c7fe287
GODOT=/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe
(cd "$WT/godot" && dotnet build 2>&1 | grep -E " error |Build succeeded" | head -3)
python shot.py dig5 --zone arena --people lamplings --seed 739 --tier 2 --minute 25 --give "oathblade:6,seeking_motes:5,cinderfall:5" --auto --seconds 5 --every 1.5 --count 10
python shot.py rise_wall --quick arcanist --zone arena --people dead --time night --tier 2 --lab --give "seeking_motes:4,+from_the_ashes:2" --horde "70,8:risen!" --dist 3 --spread 9 --seconds 2.9 --fall-at 3 --until 7
python sweep.py b1 gale_chakram umbral_bolt moonbrand cinderfall --horde 40 --dist 5 --spread 7 --every 0.05 --count 28 --start 3.2
python sweep.py b1x iron_palms firepot grave_tether gravecall spirit_herd thornbloom blightfield --horde 40 --dist 5 --spread 7 --every 0.1 --count 16 --start 3.2
echo done
