#!/usr/bin/env bash
# The Godot slice's toolchain, for a fresh Linux container or machine:
# Godot 4.5.1 (.NET build), the .NET 8 SDK, and Mesa's software Vulkan
# (lavapipe) with Xvfb, so the full renderer runs headless for screenshots.
#
#   tools/godot/setup.sh [dir]      (default: ~/.cache/godot-bin)
#
# Prints the Godot binary's path; tools/godot/run.sh finds it there.
set -euo pipefail
DIR="${1:-$HOME/.cache/godot-bin}"
VER=4.5.1
mkdir -p "$DIR"
if ! command -v dotnet >/dev/null; then apt-get install -y -q dotnet-sdk-8.0 >/dev/null; fi
if [ ! -f /usr/share/vulkan/icd.d/lvp_icd.json ]; then apt-get install -y -q mesa-vulkan-drivers >/dev/null; fi
command -v xvfb-run >/dev/null || apt-get install -y -q xvfb >/dev/null
BIN="$DIR/Godot_v${VER}-stable_mono_linux_x86_64/Godot_v${VER}-stable_mono_linux.x86_64"
if [ ! -x "$BIN" ]; then
  curl -sL -o "$DIR/godot.zip" "https://github.com/godotengine/godot-builds/releases/download/${VER}-stable/Godot_v${VER}-stable_mono_linux_x86_64.zip"
  (cd "$DIR" && unzip -oq godot.zip && rm godot.zip)
fi
echo "$BIN"
