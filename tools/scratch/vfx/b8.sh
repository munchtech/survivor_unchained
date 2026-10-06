#!/usr/bin/env bash
# Before: the inherited loot light at 1920x1080, by day and by night, with the ground labels and the
# edge's pointer; the Dig's looks and the rise (never seen: the last import crashed).
cd "$(dirname "$0")"
VFX="$(pwd)"
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a191ed81e2df462cf
GODOT=/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe
"$GODOT" --headless --path "$WT/godot" --import > "$VFX/import_b8.log" 2>&1
echo "import exit $?"
"$GODOT" --headless --path "$WT/godot" --import > "$VFX/import_b8b.log" 2>&1
echo "import again exit $?"
(cd "$WT/godot" && dotnet build 2>&1 | grep -E " error |Build succeeded" | head -3)
python shot.py lb_day --quick warden --zone verge --time day --tier 2 --lab --loot --seconds 8 --every 1.5 --count 2
python shot.py lb_night --quick warden --zone arena --people dead --time night --tier 2 --lab --loot --seconds 8 --every 1.5 --count 2
python shot.py lb_tiers_day --quick warden --zone verge --time day --tier 2 --lab --loot-tiers --loot-at 2 --seconds 6 --every 1 --count 2
python shot.py lb_tiers_night --quick warden --zone arena --people dead --time night --tier 2 --lab --loot-tiers --loot-at 2 --seconds 6 --every 1 --count 2
python shot.py lb_far --quick warden --zone verge --time day --tier 2 --lab --loot legendary --far --seconds 4 --every 1.5 --count 2
python shot.py lb_far_night --quick warden --zone arena --people dead --time night --tier 2 --lab --loot legendary --far --seconds 4 --every 1.5 --count 2
python shot.py lb_hoard --quick warden --zone verge --time day --tier 2 --lab --hoard 3 --seconds 8 --every 1.5 --count 2
python shot.py dig_tubs --quick warden --sex female --night dig --stage 1 --auto --seconds 6 --every 0.9 --count 12
python shot.py dig_boss --quick warden --sex female --night dig --stage 3 --auto --seconds 5 --every 1.1 --count 16
python shot.py rise_wall7 --quick arcanist --zone arena --people dead --time night --tier 2 --lab --give "seeking_motes:4,+from_the_ashes:2" --horde "70,8:risen!" --dist 3 --spread 9 --seconds 3.0 --every 0.3 --count 12 --fall-at 3
echo done
