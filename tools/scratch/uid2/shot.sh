#!/bin/bash
# usage: shot.sh NAME SECONDS [game args...]   (the UI design lead's; the scratchpad is shared)
GODOT="/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe"
WT="/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-ac76f400913a109cd/godot"
SP="/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/uid2"
name=$1; secs=$2; shift 2
LOG=$SP/logs/log_$name.txt
mkdir -p $SP/logs
"$GODOT" --path "$WT" --resolution 1920x1080 -- --shot "$name" --seconds "$secs" --navcheck "$@" > "$LOG" 2>&1
echo "[$name] $(grep -iE "error|exception" "$LOG" | grep -vcE "RID allocations|RenderingServer::get_singleton") errors; $(grep -iE "^saved" "$LOG" | head -1 | sed 's#.*/##')"
grep -iE "error|exception" "$LOG" | grep -vE "RID allocations|RenderingServer::get_singleton|^\s*at " | sort | uniq -c | head -6
grep "^nav " "$LOG" | head -12
