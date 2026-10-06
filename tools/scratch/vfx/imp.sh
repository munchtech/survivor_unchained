#!/usr/bin/env bash
# Build and import this worktree twice (the first import leaves a few gltf deps unresolved).
cd "$(dirname "$0")"
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a560452c597415545
GODOT=/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe
(cd "$WT/godot" && dotnet build 2>&1 | grep -E " error |Build succeeded" | head -5)
"$GODOT" --headless --path "$WT/godot" --import > import_1.log 2>&1
echo "import 1 exit $?"
"$GODOT" --headless --path "$WT/godot" --import > import_2.log 2>&1
echo "import 2 exit $?"
grep -iE "error" import_2.log | head -10
