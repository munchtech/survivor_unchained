#!/usr/bin/env bash
# Round 3 after merging the integration branch: the Dig again (what are the pale discs over the
# lamplings?), the rise's wall at its real height, and the reworked skills.
cd "$(dirname "$0")"
VFX="$(pwd)"
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-abc6bbe020c7fe287
GODOT=/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe
"$GODOT" --headless --path "$WT/godot" --import > "$VFX/import_b4.log" 2>&1
echo "import exit $?"
(cd "$WT/godot" && dotnet build 2>&1 | grep -E " error |Build succeeded" | head -3)
python shot.py dig7 --zone arena --people lamplings --seed 739 --tier 2 --minute 25 --give "oathblade:6,seeking_motes:5,cinderfall:5" --auto --seconds 5 --every 1.5 --count 10
python shot.py rise_wall3 --quick arcanist --zone arena --people dead --time night --tier 2 --lab --give "seeking_motes:4,+from_the_ashes:2" --horde "70,8:risen!" --dist 3 --spread 9 --seconds 2.9 --fall-at 3 --until 7
python sweep.py b3 gale_chakram moonbrand umbral_bolt iron_palms spirit_herd dawnpulse --horde 40 --dist 5 --spread 7 --every 0.05 --count 28 --start 3.2
python sweep.py b3z thornbloom blightfield gravecall hallowed_ring --horde 40 --dist 5 --spread 7 --every 0.15 --count 16 --start 0.6
echo done
