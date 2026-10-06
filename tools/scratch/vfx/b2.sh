#!/usr/bin/env bash
# The second look: the chakram as steel, the dust of the dry dead, the moon's colours, the coal's
# trail, the chi palm, the procedural wall of flame, and the Dig's ground in the danger language.
cd "$(dirname "$0")"
VFX="$(pwd)"
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-abc6bbe020c7fe287
GODOT=/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe
"$GODOT" --headless --path "$WT/godot" --import > "$VFX/import_b3.log" 2>&1
echo "import exit $?"
(cd "$WT/godot" && dotnet build 2>&1 | grep -E " error |Build succeeded" | head -3)
python shot.py rise_wall2 --quick arcanist --zone arena --people dead --time night --tier 2 --lab --give "seeking_motes:4,+from_the_ashes:2" --horde "70,8:risen!" --dist 3 --spread 9 --seconds 2.9 --fall-at 3 --until 7
python sweep.py b2 gale_chakram umbral_bolt moonbrand cinderfall iron_palms spirit_herd thornbloom gravecall blightfield firepot grave_tether seeking_motes --horde 40 --dist 5 --spread 7 --every 0.05 --count 28 --start 3.2
python shot.py dig6 --zone arena --people lamplings --seed 739 --tier 2 --minute 25 --give "oathblade:6,seeking_motes:5,cinderfall:5" --auto --seconds 5 --every 1.5 --count 10
echo done
