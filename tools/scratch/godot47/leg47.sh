#!/usr/bin/env bash
# The 4.7.2 upgrade: a copy of the pacing lane's scratch_pacing/leg.sh, its worktree and out folder (godot/.shots/pacing47) changed.
# P2 task 5: one den perf leg of an exported build. usage: leg.sh <exe dir> <tag> [extra game args...]
# env: PERF_FOR (recorded s, default 140), QUIET_WAIT (s to wait for no foreign Godot/Blender, default 1800).
# Foreign Godot/Blender/SurvivorUnchained/dotnet(test/build, not the idle compiler server) processes are logged before, every 10 s
# during, and after; a leg with any is NOT clean (legs.log says CLEAN or DIRTY).
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a73cef575840655d2
D="$1"; TAG="$2"; shift 2
OUT="$WT/godot/.shots/pacing47"; mkdir -p "$OUT"
FOR="${PERF_FOR:-140}"; QW="${QUIET_WAIT:-1800}"
rivals() {
  powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { \$_.Name -match '^(Godot|blender|dotnet|SurvivorUnchained)' -and \$_.CommandLine -notmatch 'VBCSCompiler|MSBuild.dll|--import' } | ForEach-Object { \$c = (\$_.CommandLine -replace '\s+',' '); '{0} {1} {2}' -f \$_.ProcessId, \$_.Name, \$c.Substring(0, [Math]::Min(120, \$c.Length)) }" 2>/dev/null | tr -d '\r'
}
t0=$(date +%s)
while [ -n "$(rivals)" ] && [ $(( $(date +%s) - t0 )) -lt "$QW" ]; do sleep 20; done
until python C:/Users/munch/Desktop/survivorsunchained/tools/turn.py take godot "godot47-up: leg $TAG" --wait 20 --stale-ok >/dev/null; do sleep 10; done
B="$(rivals)"
t0=$(date +%s)
"$D/SurvivorUnchained.exe" --resolution 2560x1440 -- --quick warden --sex female ${ZONE_ARGS:---zone map --dungeon hollow} --seed 1 --auto human \
  --keep-shaders --quality high --perf "$TAG" --perf-warm 15 --perf-for "$FOR" "$@" > "$OUT/$TAG.log" 2>&1 &
pid=$!
DUR=""
while kill -0 $pid 2>/dev/null; do sleep 10; r="$(rivals | grep -v SurvivorUnchained)"; [ -n "$r" ] && DUR="$DUR
[+$(( $(date +%s) - t0 ))s] $r"; done
wait $pid; rc=$?
A="$(rivals)"
python C:/Users/munch/Desktop/survivorsunchained/tools/turn.py give godot "godot47-up: leg $TAG" >/dev/null
cp "$D/perf/$TAG.csv" "$D/perf/$TAG.json" "$OUT/" 2>/dev/null
state=CLEAN; [ -n "$B$A$DUR" ] && state=DIRTY
{ echo "LEG $TAG $state exit $rc wall $(( $(date +%s) - t0 )) s at $(date +%T) exe $D args $*"; echo "BEFORE:"; echo "$B"; echo "DURING:$DUR"; echo "AFTER:"; echo "$A"; } > "$OUT/$TAG.rivals"
echo "LEG $TAG $state exit $rc at $(date +%T) exe $(basename $D) args $*" >> "$OUT/legs.log"
echo "$TAG $state exit $rc; ERROR lines $(grep -c ERROR "$OUT/$TAG.log")"
grep -E "^perf .*(done|hitches)" "$OUT/$TAG.log" | cut -c1-200
