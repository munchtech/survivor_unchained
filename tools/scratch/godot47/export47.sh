#!/usr/bin/env bash
# The 4.7.2 upgrade: export "Windows Demo (proof)" (release template, features demo+perf, shader baker on) into
# release/godot/<name> with the engine given (as the pacing lane's export_next.sh; windowed: the shader baker bakes only with a window).
# usage: export47.sh <name> [godot console exe]   (default 4.7.2)
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a73cef575840655d2
GODOT="${2:-/c/Users/munch/Desktop/Godot_v4.7.2-stable_mono_win64/Godot_v4.7.2-stable_mono_win64_console.exe}"
N="$1"; D="$WT/release/godot/$N"
until python C:/Users/munch/Desktop/survivorsunchained/tools/turn.py take godot "godot47-up: export $N" --wait 20 --stale-ok >/dev/null; do sleep 10; done
rm -rf "$D"; mkdir -p "$D"
cd "$WT/godot"
t0=$(date +%s)
"$GODOT" --path . --export-release "Windows Demo (proof)" "$D/SurvivorUnchained.exe" > "$WT/release/godot/$N.log" 2>&1
python C:/Users/munch/Desktop/survivorsunchained/tools/turn.py give godot "godot47-up: export $N" >/dev/null
L="$WT/release/godot/$N.log"
echo "export $N: $(( $(date +%s) - t0 )) s engine $(basename "$GODOT"); build failures $(grep -c 'Failed to build' "$L"); baking $(grep -c -i 'Baking shaders' "$L"); ERROR lines $(grep -c ERROR "$L")"
ls -la "$D" | head
