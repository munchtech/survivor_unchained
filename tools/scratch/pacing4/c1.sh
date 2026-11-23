#!/usr/bin/env bash
# frame-pacing-4 chain 1: the start check (zone map, den, level 9) on exports, with the sampler. usage: c1.sh <leg>...
# legs: s47 (next5 + sampler), d47 (next5 --generate-spirv-debug-info = re-spirv off), b47 (next5 plain), s45 (next4 + sampler), b45
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a73cef575840655d2
N5=$WT/release/godot/next5/SurvivorUnchained.exe
N4=/c/Users/munch/Desktop/survivorsunchained/release/godot/next4/SurvivorUnchained.exe
GA="--quick warden --sex female --zone map --dungeon hollow --veteran 9 --move-new --move-ab"
Q=$WT/tools/scratch/pacing4/q.sh
for leg in "$@"; do
  tag="${leg%%:*}"; kind="${leg##*:}"
  case "$kind" in
    s47) SAMPLER='next5\SurvivorUnchained.exe' SAMPLER_DELAY=0 SAMPLER_FOR=70 bash $Q $tag 75 $N5 -- $GA ;;
    d47) bash $Q $tag 100 $N5 --generate-spirv-debug-info -- $GA ;;
    ds47) SAMPLER='next5\SurvivorUnchained.exe' SAMPLER_DELAY=0 SAMPLER_FOR=70 bash $Q $tag 75 $N5 --generate-spirv-debug-info -- $GA ;;
    b47) bash $Q $tag 75 $N5 -- $GA ;;
    s45) SAMPLER='next4\SurvivorUnchained.exe' SAMPLER_DELAY=0 SAMPLER_FOR=70 bash $Q $tag 75 $N4 -- $GA ;;
    b45) bash $Q $tag 75 $N4 -- $GA ;;
  esac
  echo "   caches after $tag: pipelines $(stat -c %s "$APPDATA/Godot/app_userdata/Survivor Unchained/vulkan/pipelines.forward_plus.nvidia_geforce_rtx_5080.cache") bytes $(stat -c %y "$APPDATA/Godot/app_userdata/Survivor Unchained/vulkan/pipelines.forward_plus.nvidia_geforce_rtx_5080.cache" | cut -c12-19); shader_cache files $(find "$APPDATA/Godot/app_userdata/Survivor Unchained/shader_cache" -type f | wc -l)"
  [ -f $WT/godot/.shots/pacing4/$tag.samp.out ] && cat $WT/godot/.shots/pacing4/$tag.samp.out
done
