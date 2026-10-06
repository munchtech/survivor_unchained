#!/usr/bin/env bash
# The rise again (flat flames along the running front; the watch dial held in the air), and the
# crowd's glare round her (lights faded near her, the champion's fall to three metres, the dry
# dead's dust grey).
cd "$(dirname "$0")"
VFX="$(pwd)"
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a94ac6b67f1279213
GODOT=/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe
"$GODOT" --headless --path "$WT/godot" --import > "$VFX/import13.log" 2>&1
(cd "$WT/godot" && dotnet build 2>&1 | grep -E " error |Build succeeded" | head -3)
python shot.py rise_ember --quick arcanist --zone arena --people dead --time night --tier 2 --lab --give "seeking_motes:4,+from_the_ashes:2" --horde "70,8:risen!" --dist 3 --spread 9 --seconds 2.9 --fall-at 3 --until 7
python shot.py rise_notyet --quick warden --zone arena --people dead --time night --tier 2 --lab --give "oathblade:4" --horde "70,8:risen!" --dist 3 --spread 9 --seconds 2.9 --fall-at 3 --until 7
python sweep.py r2 seeking_motes judgement_disc cinderfall umbral_bolt moonbrand
echo done
