#!/bin/bash
# His skeleton dumped from hero.glb and his clip library rebuilt on it (in a godot turn).
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-ac39445bca5508eaf
G=/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe
L=/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-survivorsunchained/ba85aba8-36f4-4cf9-99c5-4c5ef9e4a65c/scratchpad/b1/clips.log
cd $WT
python /c/Users/munch/Desktop/survivorsunchained/tools/turn.py take godot "hero: skeleton dump + clips" --wait 900
$G --headless --path godot -s res://tools_scenes/anim_skeleton.gd -- $WT/tools/anim/data/hero_skeleton.json res://art/people/hero.glb > /dev/null 2>&1
python -c "import json; d=json.load(open('tools/anim/data/hero_skeleton.json')); print('SKELETON', len(d['bones']), d['model'])"
start=$(date +%s)
python tools/anim/build.py --body hero > $L 2>&1
echo "BUILD exit $? in $(( $(date +%s) - start )) s"
python /c/Users/munch/Desktop/survivorsunchained/tools/turn.py give godot "hero: skeleton dump + clips"
tail -4 $L
grep -c "frames" $L
