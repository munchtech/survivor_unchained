#!/bin/bash
# armor 5: build, import, pack her clips (and his), ArmsDump, then armscheck --sockets --keep. Usage: pack.sh <logdir>
W=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/armor-5
G=/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe
T=/c/Users/munch/Desktop/survivorsunchained/tools/turn.py
L=$1; mkdir -p $L; cd $W
(cd godot && dotnet build > $L/dotnet_build.log 2>&1; echo "dotnet build $?")
python $T take godot "armor5: pack + arms dump" --wait 600 --stale-ok --root "$W" > $L/turn.log 2>&1 || { echo "turn refused"; exit 1; }
"$G" --headless --path "$W/godot" --import > $L/import.log 2>&1; echo "import $?"
python tools/anim/build.py > $L/build_her.log 2>&1; echo "build her $?"
# (no hero pack: owner, 19 Oct)
"$G" --headless --path "$W/godot" -s res://tools_scenes/arms_dump.gd > $L/dump.log 2>&1; echo "dump $?"
python $T give godot "armor5: pack + arms dump" --root "$W" >> $L/turn.log 2>&1
git checkout -- godot/project.godot 2>/dev/null
git diff --name-only -- '*.import' | while read f; do git checkout -- "$f"; done
git status --short | grep -v '^??' 
python tools/anim/armscheck.py --sockets --keep --jobs 4 > $L/sockets.log 2>&1; echo "sockets $?"
echo PACK DONE
