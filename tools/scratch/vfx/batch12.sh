#!/usr/bin/env bash
# The rise with its painted marks, the two runs batch 11 lost to a full disk, and the
# experience director's status read (their branch's vat.gdshaderinc swapped in, then put back).
cd "$(dirname "$0")"
VFX="$(pwd)"
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a94ac6b67f1279213
GODOT=/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe
"$GODOT" --headless --path "$WT/godot" --import > "$VFX/import12.log" 2>&1
(cd "$WT/godot" && dotnet build 2>&1 | grep -E " error |Build succeeded" | head -3)
python shot.py rise_ember --quick arcanist --zone arena --people dead --time night --tier 2 --lab --give "seeking_motes:4,+from_the_ashes:2" --horde "70,8:risen!" --dist 3 --spread 9 --seconds 2.9 --fall-at 3 --until 7
python shot.py rise_notyet --quick warden --zone arena --people dead --time night --tier 2 --lab --give "oathblade:4" --horde "70,8:risen!" --dist 3 --spread 9 --seconds 2.9 --fall-at 3 --until 7
python shot.py kerch3 --zone arena --people kerchiefs --tier 2 --minute 25 --give "oathblade:6,seeking_motes:5,cinderfall:5,arcweb:4" --auto --seconds 5 --every 1.5 --count 10
python shot.py dead3 --zone arena --people dead --tier 3 --minute 25 --give "oathblade:6,hoarfrost:6,seeking_motes:5" --auto --seconds 5 --every 1.5 --count 10
python shot.py dig4 --zone arena --people lamplings --seed 739 --tier 2 --minute 25 --give "oathblade:6,seeking_motes:5,cinderfall:5" --auto --seconds 5 --every 1.5 --count 10
cp "$WT/godot/shaders/vat.gdshaderinc" "$VFX/vat_mine.gdshaderinc"
cp "$VFX/vat_status.gdshaderinc" "$WT/godot/shaders/vat.gdshaderinc"
python sweep.py st1 hoarfrost cinderfall
cp "$VFX/vat_mine.gdshaderinc" "$WT/godot/shaders/vat.gdshaderinc"
echo done
