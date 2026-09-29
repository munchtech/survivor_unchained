#!/usr/bin/env bash
# Run the Godot slice with the full (Vulkan, Forward+) renderer, headless:
# a virtual display and Mesa's software Vulkan. Arguments after the first
# `--` go to the slice (godot/src/Slice.cs: --shot, --seconds, --at ...).
#
#   tools/godot/run.sh [godot args] -- [slice args]
#
# GODOT=path/to/binary overrides where Godot is (tools/godot/setup.sh).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
GODOT="${GODOT:-$HOME/.cache/godot-bin/Godot_v4.5.1-stable_mono_linux_x86_64/Godot_v4.5.1-stable_mono_linux.x86_64}"
export GODOT_NUPKGS="$(dirname "$GODOT")/GodotSharp/Tools/nupkgs"
export VK_ICD_FILENAMES="${VK_ICD_FILENAMES:-/usr/share/vulkan/icd.d/lvp_icd.json}"
cd "$ROOT/godot"
"$GODOT" --headless --path . --import >/dev/null 2>&1 || true  # incremental: only what changed
dotnet build -v q -nologo SurvivorUnchained.csproj >/dev/null
exec xvfb-run -a -s "-screen 0 1920x1080x24" "$GODOT" --path . --rendering-driver vulkan --audio-driver Dummy "$@"
