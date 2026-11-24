#!/usr/bin/env bash
# frame-pacing-4: one measured Godot run, only when nobody else runs Godot.
# usage: q.sh <tag> <timeout s> <exe> [args...]
# Waits until `turn.py show` has no godot holder and no rival process (Godot/SurvivorUnchained/blender/dotnet test or build),
# takes the turn, runs under timeout, polls every 5 s for a rival or another holder, gives the turn back.
# Log: godot/.shots/pacing4/<tag>.log ; verdict line (CLEAN/DIRTY) appended to godot/.shots/pacing4/runs.log
# env: QUIET_WAIT (s, default 3600), SAMPLER=<exe path substring> starts tools/scratch/pacing4/samp.py on that process.
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a73cef575840655d2
T=C:/Users/munch/Desktop/survivorsunchained/tools/turn.py
TAG="$1"; TMO="$2"; EXE="$3"; shift 3
O=$WT/godot/.shots/pacing4; mkdir -p $O
ME="pacing4: $TAG"
rivals() {
  powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { \$_.Name -match '^(Godot|blender|dotnet|SurvivorUnchained)' -and \$_.CommandLine -notmatch 'VBCSCompiler|MSBuild.dll|build-server' } | ForEach-Object { \$c = (\$_.CommandLine -replace '\s+',' '); '{0} {1} {2}' -f \$_.ProcessId, \$_.Name, \$c.Substring(0, [Math]::Min(110, \$c.Length)) }" 2>/dev/null | tr -d '\r'
}
others() { python $T show 2>/dev/null | grep '^godot:' | sed 's/^godot: //' | tr ';' '\n' | sed 's/^ *//' | grep -v '^free' | grep -v "^$ME" ; }
t0=$(date +%s)
while { [ -n "$(rivals)" ] || [ -n "$(others)" ]; } && [ $(( $(date +%s) - t0 )) -lt "${QUIET_WAIT:-3600}" ]; do sleep 15; done
until python $T take godot "$ME" --wait 20 --stale-ok >/dev/null; do sleep 10; done
B="$(rivals)$(others)"
t1=$(date +%s)
timeout "$TMO" "$EXE" "$@" > "$O/$TAG.log" 2>&1 &
pid=$!
if [ -n "$SAMPLER" ]; then ( sleep "${SAMPLER_DELAY:-1}"; python $WT/tools/scratch/pacing4/samp.py "$SAMPLER" "$O/$TAG.samp" ${SAMPLER_FOR:-60} > "$O/$TAG.samp.out" 2>&1 ) & fi
DUR=""
while kill -0 $pid 2>/dev/null; do sleep 5; r="$(rivals | grep -v "SurvivorUnchained\|$(basename "$EXE")")$(others)"; [ -n "$r" ] && DUR="$DUR [+$(( $(date +%s) - t1 ))s] $r"; done
wait $pid; rc=$?
wait
python $T give godot "$ME" >/dev/null
state=CLEAN; [ -n "$B$DUR" ] && state=DIRTY
echo "RUN $TAG $state rc $rc wall $(( $(date +%s) - t1 )) s waited $(( t1 - t0 )) s at $(date +%T) :: $(basename "$EXE") $* :: before[$B] during[$DUR]" >> $O/runs.log
echo "$TAG $state rc $rc waited $(( t1 - t0 )) s"
grep -a "Godot Engine\|fx warm-up" "$O/$TAG.log" | cut -c1-420
