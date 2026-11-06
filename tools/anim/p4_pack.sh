#!/usr/bin/env bash
# P4 clips packed for the game: godot/art/people/body_p1/p4/*.json (tools/anim/p4.py build) -> body_p1/p4_clips.res
# (godot/tools_scenes/P4Pack.cs). Takes and gives back the godot turn. Extra args pass to Godot.
set -u
W="$(cd "$(dirname "$0")/../.." && pwd)"
G="C:/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe"
T="python C:/Users/munch/Desktop/survivorsunchained/tools/turn.py"
(cd "$W/godot" && dotnet build -v q -nologo) || exit 1
$T take godot "P4: clip pack" --wait 90 || exit 1
LOG="$W/tools/body/out/p4_pack.log"; mkdir -p "$(dirname "$LOG")"
"$G" --headless --path "$W/godot" -s res://tools_scenes/p4_pack.gd -- "$@" > "$LOG" 2>&1; rc=$?
grep "p4-pack\|ERROR" "$LOG"
$T give godot "P4: clip pack"
exit $rc
