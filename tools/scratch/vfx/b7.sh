#!/usr/bin/env bash
# Loot's light with the NaN at its rim fixed; the Dig's new looks (the tubs, Grimtunnel under the
# ground, his pits and crack, Snib's barrel); the rise without the milky frost.
cd "$(dirname "$0")"
VFX="$(pwd)"
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-abc6bbe020c7fe287
GODOT=/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe
# Twice: after a merge brings new assets the first headless import segfaults (every frame black).
"$GODOT" --headless --path "$WT/godot" --import > "$VFX/import_b7.log" 2>&1
echo "import exit $?"
"$GODOT" --headless --path "$WT/godot" --import > "$VFX/import_b7b.log" 2>&1
echo "import again exit $?"
(cd "$WT/godot" && dotnet build 2>&1 | grep -E " error |Build succeeded" | head -3)
python shot.py loot_lab_day2 --quick warden --zone verge --time day --tier 2 --lab --seconds 3.8 --every 0.6 --count 2 --loot --loot-at 3
python shot.py loot_lab_night2 --quick warden --zone arena --people dead --time night --tier 2 --lab --seconds 3.8 --every 0.6 --count 2 --loot --loot-at 3
python shot.py dig_tubs --quick warden --sex female --night dig --stage 1 --auto --seconds 6 --every 0.9 --count 16
python shot.py dig_boss --quick warden --sex female --night dig --stage 3 --auto --seconds 5 --every 1.1 --count 24
python shot.py rise_wall7 --quick arcanist --zone arena --people dead --time night --tier 2 --lab --give "seeking_motes:4,+from_the_ashes:2" --horde "70,8:risen!" --dist 3 --spread 9 --seconds 2.9 --fall-at 3 --until 7
echo done
