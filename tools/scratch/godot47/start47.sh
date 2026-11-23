#!/bin/bash
# The 4.7.2 upgrade: start check of an export at level 9 (as scratch_coord16/start_check.sh; its own PID only, under timeout).
# usage: start47.sh <name> [exe dir]   (default exe dir: this worktree's release/godot/<name>)
N=${1:-next5}; DIR="${2:-/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a73cef575840655d2/release/godot/$N}"
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a73cef575840655d2
O=$WT/godot/.shots/godot47up; mkdir -p $O
until python C:/Users/munch/Desktop/survivorsunchained/tools/turn.py take godot "godot47-up: start $N" --wait 20 --stale-ok >/dev/null; do sleep 10; done
timeout 60 "$DIR/SurvivorUnchained.exe" -- --quick warden --sex female --zone map --dungeon hollow --veteran 9 --move-new --move-ab > $O/start_$N.log 2>&1
rc=$?
python C:/Users/munch/Desktop/survivorsunchained/tools/turn.py give godot "godot47-up: start $N" >/dev/null
echo "$N rc $rc ; ERROR lines $(grep -c ERROR $O/start_$N.log) ; not exit-leak: $(grep ERROR $O/start_$N.log | grep -v -c 'Unreferenced static string\|leaked\|RID\|still in use\|ObjectDB')"
grep -i "veteran\|fx warm-up\|Godot Engine" $O/start_$N.log | cut -c1-300 | head -4
grep -E "ERROR|SHADER" $O/start_$N.log | grep -v 'Unreferenced static string\|leaked\|RID\|still in use\|ObjectDB' | cut -c1-300 | head -8
