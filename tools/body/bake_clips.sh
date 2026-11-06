#!/usr/bin/env bash
# The clip bridge: every A clip baked onto B skeleton (godot/tools_scenes/P1BakeRun.cs) -> godot/art/people/body_p1/{clips,her_clips}.res, a_skeleton.json.
# Takes and gives back the godot turn. Extra args pass to Godot (e.g. --p1-bake-only idle_reaver_town: a check, nothing written).
set -u
W="$(cd "$(dirname "$0")/../.." && pwd)"
G="C:/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe"
T="python C:/Users/munch/Desktop/survivorsunchained/tools/turn.py"
(cd "$W/godot" && dotnet build -v q -nologo) || exit 1
$T take godot "P1 R2 native: clip bake" --wait 90 || exit 1
LOG="$W/tools/body/out/bake_clips.log"; mkdir -p "$(dirname "$LOG")"
"$G" --headless --path "$W/godot" -s res://tools_scenes/p1_bake.gd -- "$@" > "$LOG" 2>&1; rc=$?
grep "p1-bake\|ERROR" "$LOG"
$T give godot "P1 R2 native: clip bake"
exit $rc
