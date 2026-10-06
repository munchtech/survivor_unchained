#!/usr/bin/env bash
# Loot's light by day and by night in a fight's aftermath; the rise's cold and taller wall; the
# grounds dimmed in their colour; Dawnpulse without its disc; the herd's echoes.
cd "$(dirname "$0")"
VFX="$(pwd)"
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-abc6bbe020c7fe287
GODOT=/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe
"$GODOT" --headless --path "$WT/godot" --import > "$VFX/import_b5.log" 2>&1
echo "import exit $?"
(cd "$WT/godot" && dotnet build 2>&1 | grep -E " error |Build succeeded" | head -3)
python shot.py loot_day --quick warden --zone arena --people dead --time day --tier 2 --give "oathblade:5,dawnpulse:4" --horde "40,6:risen!" --dist 4 --spread 8 --auto --seconds 6.4 --every 0.7 --count 5 --loot --loot-at 6
python shot.py loot_night --quick warden --zone arena --people dead --time night --tier 2 --give "oathblade:5,dawnpulse:4" --horde "40,6:risen!" --dist 4 --spread 8 --auto --seconds 6.4 --every 0.7 --count 5 --loot --loot-at 6
python shot.py rise_wall4 --quick arcanist --zone arena --people dead --time night --tier 2 --lab --give "seeking_motes:4,+from_the_ashes:2" --horde "70,8:risen!" --dist 3 --spread 9 --seconds 2.9 --fall-at 3 --until 7
python sweep.py b4 spirit_herd dawnpulse iron_palms gale_chakram --horde 40 --dist 5 --spread 7 --every 0.05 --count 28 --start 3.2
python sweep.py b4z thornbloom blightfield hallowed_ring --horde 40 --dist 5 --spread 7 --every 0.15 --count 16 --start 0.6
echo done
