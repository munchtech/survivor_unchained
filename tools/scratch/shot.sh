#!/bin/bash
# usage: shot.sh NAME SECONDS [game args...]
GODOT="/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe"
WT="/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a5629aff0f215ea4a/godot"
SP="/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad"
name=$1; secs=$2; shift 2
LOG=$SP/logs/log_$name.txt
mkdir -p $SP/logs
"$GODOT" --path "$WT" --resolution 1920x1080 -- --shot "$name" --seconds "$secs" "$@" > "$LOG" 2>&1
echo "[$name] $(grep -icE "error|exception" "$LOG") errors; $(grep -iE "saved" "$LOG" | head -1)"
grep -iE "error|exception" "$LOG" | grep -v "^\s*at " | sort | uniq -c | head -6
